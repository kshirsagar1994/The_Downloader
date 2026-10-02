import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from app.config import get_settings
from app.core.errors import ExtractionFailedError, ProcessingFailedError
from app.core.logging import logger
from app.schemas.job import JobProgressEvent
from app.security.sanitization import sanitize_extension, sanitize_filename
from app.security.ssrf import validate_url_ssrf
from app.services.ffmpeg_service import FFmpegService

settings = get_settings()


class AudioService:
    """Handles audio extraction, format transcoding (MP3/M4A/Opus/WAV), and bitrate optimization."""

    @classmethod
    async def download_audio(
        cls,
        url: str,
        job_dir: Path,
        target_format: str = "mp3",
        bitrate: str = "320k",
        progress_callback: Callable[[JobProgressEvent], None] | None = None,
    ) -> Path:
        """
        Extracts source audio stream and converts to target format (MP3, M4A, Opus, WAV) with specified bitrate.
        """
        validated_url = validate_url_ssrf(url)
        job_dir.mkdir(parents=True, exist_ok=True)

        clean_ext = sanitize_extension(target_format, "mp3")
        clean_bitrate = bitrate.rstrip("k").strip() if bitrate else "320"
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
                percent = min(90.0, (downloaded / total) * 90.0)

            filename = Path(d.get("filename", "audio.mp3")).name

            event = JobProgressEvent(
                job_id=job_dir.name,
                status="DOWNLOADING" if status == "downloading" else "PROCESSING",
                progress=percent,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=speed,
                eta=eta,
                stage_message="Extracting source audio stream..." if status == "downloading" else f"Transcoding to {clean_ext.upper()} ({clean_bitrate} kbps)...",
                filename=sanitize_filename(filename),
            )
            progress_callback(event)

        def _postprocessor_hook(d: dict[str, Any]) -> None:
            if not progress_callback:
                return

            pp_name = d.get("postprocessor", "FFmpeg")
            status = d.get("status")

            event = JobProgressEvent(
                job_id=job_dir.name,
                status="PROCESSING",
                progress=95.0 if status == "started" else 99.0,
                downloaded_bytes=0,
                total_bytes=0,
                speed=0.0,
                eta=0,
                stage_message=f"Transcoding audio with {pp_name} ({clean_ext.upper()})...",
                filename=f"audio.{clean_ext}",
            )
            progress_callback(event)

        ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "ffmpeg_location": ffmpeg_bin,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": clean_ext,
                    "preferredquality": clean_bitrate,
                }
            ],
            "progress_hooks": [_progress_hook],
            "postprocessor_hooks": [_postprocessor_hook],
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "socket_timeout": 30,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios"],
                    "player_skip": ["webpage", "configs"],
                }
            },
        }

        logger.info(
            f"Starting audio extraction for {validated_url} ({clean_ext} @ {clean_bitrate}k) in {job_dir.name}"
        )

        try:
            await asyncio.to_thread(cls._run_ydl_download, validated_url, ydl_opts)
        except yt_dlp.utils.DownloadError as exc:
            logger.error(f"yt-dlp Audio DownloadError: {exc}")
            raise ExtractionFailedError(f"Audio extraction failed: {exc}") from exc
        except Exception as exc:
            logger.error(f"Audio download exception: {exc}")
            raise ProcessingFailedError(f"Audio processing failed: {exc}") from exc

        # Find final audio output file
        candidates = [
            f for f in job_dir.iterdir()
            if f.is_file() and not f.name.endswith(".part") and not f.name.endswith(".ytdl")
        ]

        if not candidates:
            raise ProcessingFailedError("Audio conversion completed but output file is missing.")

        output_file = candidates[0]
        logger.info(f"Audio extraction complete: {output_file.name} ({output_file.stat().st_size} bytes)")
        return output_file

    @staticmethod
    def _run_ydl_download(url: str, options: dict[str, Any]) -> None:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
