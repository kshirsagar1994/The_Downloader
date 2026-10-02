import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from app.config import get_settings
from app.core.errors import ExtractionFailedError, ProcessingFailedError
from app.core.logging import logger
from app.schemas.job import JobProgressEvent
from app.security.sanitization import sanitize_filename
from app.security.ssrf import validate_url_ssrf
from app.services.ffmpeg_service import FFmpegService

settings = get_settings()


class VideoService:
    """Handles video stream downloading, adaptive track merging, and progress tracking."""

    @classmethod
    async def download_video(
        cls,
        url: str,
        job_dir: Path,
        format_id: str | None = None,
        progress_callback: Callable[[JobProgressEvent], None] | None = None,
    ) -> Path:
        """
        Downloads requested video stream(s) using yt-dlp and merges video+audio via FFmpeg if separate.
        Streams progress updates directly through the progress_callback.
        """
        validated_url = validate_url_ssrf(url)
        job_dir.mkdir(parents=True, exist_ok=True)

        selected_format = format_id or "bestvideo+bestaudio/best"
        ffmpeg_bin = FFmpegService.get_ffmpeg_path()

        out_template = str(job_dir / "%(title).180B.%(ext)s")

        def _progress_hook(d: dict[str, Any]) -> None:
            if not progress_callback:
                return

            status = d.get("status")
            downloaded = int(round(float(d.get("downloaded_bytes") or 0)))
            total = int(round(float(d.get("total_bytes") or d.get("total_bytes_estimate") or 0)))
            speed = float(d.get("speed") or 0.0)
            eta = int(round(float(d.get("eta") or 0)))

            percent = 0.0
            if total > 0:
                percent = min(99.0, (downloaded / total) * 100.0)

            filename = Path(d.get("filename", "video.mp4")).name

            event = JobProgressEvent(
                job_id=job_dir.name,
                status="DOWNLOADING" if status == "downloading" else "PROCESSING",
                progress=percent,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=speed,
                eta=eta,
                stage_message="Downloading media stream..." if status == "downloading" else "Finalizing streams...",
                filename=sanitize_filename(filename),
            )
            progress_callback(event)

        def _postprocessor_hook(d: dict[str, Any]) -> None:
            if not progress_callback:
                return

            pp_name = d.get("postprocessor", "")
            status = d.get("status")

            stage_msg = f"Processing with FFmpeg ({pp_name})..." if status == "started" else "Streams merged."
            event = JobProgressEvent(
                job_id=job_dir.name,
                status="PROCESSING",
                progress=95.0 if status == "started" else 99.0,
                downloaded_bytes=0,
                total_bytes=0,
                speed=0.0,
                eta=0,
                stage_message=stage_msg,
                filename="Processing media...",
            )
            progress_callback(event)

        from app.services.ytdlp_options import build_base_ydl_opts

        ydl_opts = build_base_ydl_opts({
            "format": selected_format,
            "outtmpl": out_template,
            "merge_output_format": "mp4",
            "ffmpeg_location": ffmpeg_bin,
            "progress_hooks": [_progress_hook],
            "postprocessor_hooks": [_postprocessor_hook],
            "max_filesize": settings.MAX_FILE_SIZE_MB * 1024 * 1024,
            "concurrent_fragment_downloads": 4,
            "socket_timeout": 30,
        })

        logger.info(f"Starting video download for {validated_url} (format: {selected_format}) in {job_dir.name}")

        try:
            await asyncio.to_thread(cls._run_ydl_download, validated_url, ydl_opts)
        except yt_dlp.utils.DownloadError as exc:
            logger.error(f"yt-dlp Video DownloadError: {exc}")
            raise ExtractionFailedError(f"Video download failed: {exc}") from exc
        except Exception as exc:
            logger.error(f"Video download exception: {exc}")
            raise ProcessingFailedError(f"Download processing failed: {exc}") from exc

        # Find the produced output file
        candidates = [
            f for f in job_dir.iterdir()
            if f.is_file() and not f.name.endswith(".part") and not f.name.endswith(".ytdl")
        ]

        if not candidates:
            raise ProcessingFailedError("Video download completed but no output file was created.")

        output_file = candidates[0]
        logger.info(f"Video download complete: {output_file.name} ({output_file.stat().st_size} bytes)")
        return output_file

    @staticmethod
    def _run_ydl_download(url: str, options: dict[str, Any]) -> None:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
