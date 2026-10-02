import asyncio
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from app.config import get_settings
from app.core.errors import ProcessingFailedError
from app.core.logging import logger
from app.schemas.job import JobProgressEvent
from app.security.sanitization import sanitize_filename
from app.security.ssrf import validate_url_ssrf
from app.services.ffmpeg_service import FFmpegService

settings = get_settings()


class PlaylistService:
    """Handles playlist and multi-item batch downloading, item selection, and ZIP packaging."""

    @classmethod
    async def download_playlist(
        cls,
        url: str,
        job_dir: Path,
        selected_indices: list[int] | None = None,
        format_id: str | None = None,
        progress_callback: Callable[[JobProgressEvent], None] | None = None,
    ) -> Path:
        """
        Downloads selected items from a playlist.
        Bundles multi-item downloads into a clean ZIP archive for simple browser saving.
        """
        validated_url = validate_url_ssrf(url)
        job_dir.mkdir(parents=True, exist_ok=True)

        selected_format = format_id or "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        ffmpeg_bin = FFmpegService.get_ffmpeg_path()

        out_template = str(job_dir / "%(playlist_index|00)s-%(title).150B.%(ext)s")

        # Build playlist_items option if indices specified (1-based for yt-dlp)
        playlist_items_spec: str | None = None
        if selected_indices is not None and len(selected_indices) > 0:
            # Enforce max playlist bounds
            bounded = selected_indices[:settings.MAX_PLAYLIST_ITEMS]
            # Convert 0-indexed to 1-indexed
            one_indexed = [str(idx + 1) for idx in bounded]
            playlist_items_spec = ",".join(one_indexed)
        else:
            playlist_items_spec = f"1-{settings.MAX_PLAYLIST_ITEMS}"

        current_item_index = 1
        total_items_in_batch = len(selected_indices) if selected_indices else settings.MAX_PLAYLIST_ITEMS

        def _progress_hook(d: dict[str, Any]) -> None:
            if not progress_callback:
                return

            status = d.get("status", "downloading")
            downloaded = d.get("downloaded_bytes") or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed = d.get("speed") or 0.0
            eta = d.get("eta") or 0

            # Calculate item percentage
            item_percent = (downloaded / total * 100.0) if total > 0 else 0.0
            # Calculate aggregate progress
            aggregate_percent = min(
                95.0,
                ((current_item_index - 1) / max(1, total_items_in_batch)) * 100.0 + (item_percent / max(1, total_items_in_batch))
            )

            filename = Path(d.get("filename", "playlist_item.mp4")).name

            event = JobProgressEvent(
                job_id=job_dir.name,
                status="DOWNLOADING" if status == "downloading" else "PROCESSING",
                progress=aggregate_percent,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=speed,
                eta=eta,
                stage_message=f"Downloading batch item {current_item_index} of {total_items_in_batch}...",
                filename=sanitize_filename(filename),
            )
            progress_callback(event)

        ydl_opts: dict[str, Any] = {
            "format": selected_format,
            "outtmpl": out_template,
            "merge_output_format": "mp4",
            "ffmpeg_location": ffmpeg_bin,
            "playlist_items": playlist_items_spec,
            "progress_hooks": [_progress_hook],
            "quiet": True,
            "no_warnings": True,
            "max_filesize": settings.MAX_FILE_SIZE_MB * 1024 * 1024,
            "socket_timeout": 30,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "ios"],
                    "player_skip": ["webpage", "configs"],
                }
            },
        }

        logger.info(
            f"Starting playlist download for {validated_url} (items: {playlist_items_spec}) in {job_dir.name}"
        )

        try:
            await asyncio.to_thread(cls._run_ydl_download, validated_url, ydl_opts)
        except Exception as exc:
            logger.error(f"Playlist download exception: {exc}")
            raise ProcessingFailedError(f"Playlist processing failed: {exc}") from exc

        # Find produced files
        downloaded_files = [
            f for f in job_dir.iterdir()
            if f.is_file() and not f.name.endswith(".part") and not f.name.endswith(".ytdl") and not f.name.endswith(".zip")
        ]

        if not downloaded_files:
            raise ProcessingFailedError("Playlist download finished but no valid media items were extracted.")

        # If multiple files produced, package into a single clean ZIP archive
        if len(downloaded_files) > 1:
            zip_path = job_dir / "playlist_bundle.zip"
            logger.info(f"Packaging {len(downloaded_files)} playlist items into ZIP -> {zip_path.name}")

            with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
                for f in downloaded_files:
                    archive.write(str(f), arcname=sanitize_filename(f.name))
                    f.unlink(missing_ok=True)

            return zip_path

        # If only 1 file was selected/downloaded, return direct file
        return downloaded_files[0]

    @staticmethod
    def _run_ydl_download(url: str, options: dict[str, Any]) -> None:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
