import asyncio
import traceback
from pathlib import Path

from app.config import get_settings
from app.core.errors import DownloaderException
from app.core.logging import logger
from app.schemas.job import CreateJobRequest, JobProgressEvent
from app.services.audio_service import AudioService
from app.services.image_service import ImageService
from app.services.playlist_service import PlaylistService
from app.services.queue_service import queue_service
from app.services.video_service import VideoService
from app.services.ytdlp_service import YtDlpService
from app.storage.workspace import WorkspaceManager

settings = get_settings()


class JobWorker:
    """Orchestrates job lifecycle, worker execution, and status synchronization."""

    @classmethod
    async def process_job(cls, job_id: str, request: CreateJobRequest) -> None:
        """Asynchronous execution task for processing media downloads."""
        _, job_dir = WorkspaceManager.create_job_workspace(job_id)

        # Initial Status
        event = JobProgressEvent(
            job_id=job_id,
            status="ANALYZING",
            progress=5.0,
            stage_message="Analyzing media parameters...",
            filename="media_download",
        )
        await queue_service.save_job_state(event)

        loop = asyncio.get_running_loop()

        def _on_progress(update_event: JobProgressEvent) -> None:
            # Propagate progress safely across worker threads into running event loop
            try:
                asyncio.run_coroutine_threadsafe(queue_service.save_job_state(update_event), loop)
            except Exception as e:
                logger.debug(f"Progress dispatch error: {e}")

        try:
            output_file: Path

            # Check if cancelled before starting heavy workload
            current_job = await queue_service.get_job_state(job_id)
            if current_job and current_job.status == "CANCELLED":
                logger.info(f"Job {job_id} was cancelled before worker execution.")
                return

            media_type = request.media_type.lower()
            if media_type == "video":
                output_file = await VideoService.download_video(
                    url=request.url,
                    job_dir=job_dir,
                    format_id=request.format_id,
                    progress_callback=_on_progress,
                )

            elif media_type == "audio":
                output_file = await AudioService.download_audio(
                    url=request.url,
                    job_dir=job_dir,
                    target_format=request.target_extension or "mp3",
                    bitrate=request.audio_bitrate or "320k",
                    progress_callback=_on_progress,
                )

            elif media_type in ("image", "gallery"):
                # If images array not in request, extract metadata first
                meta = await YtDlpService.extract_info(request.url)
                if not meta.images:
                    raise DownloaderException("No downloadable images found at this URL.")

                if media_type == "gallery" or len(meta.images) > 1:
                    output_file = await ImageService.download_image_gallery(
                        images=meta.images,
                        job_dir=job_dir,
                        zip_name=f"{meta.title or 'images'}.zip",
                        selected_indices=request.selected_image_indices,
                    )
                else:
                    output_file = await ImageService.download_single_image(
                        url=meta.images[0].url,
                        job_dir=job_dir,
                        custom_name=meta.title,
                    )

            elif media_type == "playlist":
                output_file = await PlaylistService.download_playlist(
                    url=request.url,
                    job_dir=job_dir,
                    selected_indices=request.selected_playlist_indices,
                    format_id=request.format_id,
                    progress_callback=_on_progress,
                )

            else:
                # Default to video
                output_file = await VideoService.download_video(
                    url=request.url,
                    job_dir=job_dir,
                    format_id=request.format_id,
                    progress_callback=_on_progress,
                )

            # Check if cancelled during download
            current_job = await queue_service.get_job_state(job_id)
            if current_job and current_job.status == "CANCELLED":
                logger.info(f"Job {job_id} was cancelled during processing.")
                return

            # Job Completed Successfully
            file_size = output_file.stat().st_size if output_file and output_file.exists() else 0
            completed_event = JobProgressEvent(
                job_id=job_id,
                status="COMPLETED",
                progress=100.0,
                downloaded_bytes=file_size,
                total_bytes=file_size,
                speed=0.0,
                eta=0,
                stage_message="Download ready!",
                filename=output_file.name if output_file else "download",
                download_url=f"/api/download/{job_id}",
            )
            await queue_service.save_job_state(completed_event)
            logger.info(f"Job {job_id} COMPLETED -> {output_file.name if output_file else 'file'} ({file_size} bytes)")

        except DownloaderException as exc:
            current_job = await queue_service.get_job_state(job_id)
            if current_job and current_job.status == "CANCELLED":
                logger.info(f"Job {job_id} was cancelled; skipping error handler.")
                return

            logger.error(f"Job {job_id} failed with domain error: {exc.message}")
            failed_event = JobProgressEvent(
                job_id=job_id,
                status="FAILED",
                progress=0.0,
                stage_message="Failed",
                error_code=exc.code,
                error_message=exc.message,
            )
            await queue_service.save_job_state(failed_event)

        except Exception as exc:  # noqa: BLE001
            current_job = await queue_service.get_job_state(job_id)
            if current_job and current_job.status == "CANCELLED":
                logger.info(f"Job {job_id} was cancelled; skipping unexpected error handler.")
                return

            logger.error(f"Job {job_id} unexpected failure: {exc}\n{traceback.format_exc()}")
            failed_event = JobProgressEvent(
                job_id=job_id,
                status="FAILED",
                progress=0.0,
                stage_message="Failed",
                error_code="PROCESSING_ERROR",
                error_message=str(exc),
            )
            await queue_service.save_job_state(failed_event)
