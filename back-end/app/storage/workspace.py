import shutil
import uuid
from pathlib import Path

from app.config import get_settings
from app.core.errors import DownloaderException
from app.core.logging import logger

settings = get_settings()


class WorkspaceManager:
    """Manages ephemeral per-job isolated directories."""

    @classmethod
    def create_job_workspace(cls, job_id: str | None = None) -> tuple[str, Path]:
        """Creates an isolated workspace directory /tmp/media-downloader/{job_id}/."""
        jid = job_id or str(uuid.uuid4())
        job_dir = (settings.storage_path / jid).resolve()
        job_dir.mkdir(parents=True, exist_ok=True)
        return jid, job_dir

    @classmethod
    def get_job_workspace(cls, job_id: str) -> Path:
        """Retrieves and asserts that the workspace directory exists and is strictly contained."""
        # Sanitize job_id to prevent directory traversal
        clean_id = Path(job_id).name
        job_dir = (settings.storage_path / clean_id).resolve()

        # Assert path containment
        if not job_dir.is_relative_to(settings.storage_path):
            raise DownloaderException("Security violation: Path traversal outside storage root detected.")

        return job_dir

    @classmethod
    def cleanup_workspace(cls, job_id: str) -> None:
        """Removes the isolated workspace and all contained artifacts."""
        try:
            job_dir = cls.get_job_workspace(job_id)
            if job_dir.exists() and job_dir.is_dir():
                shutil.rmtree(str(job_dir), ignore_errors=True)
        except (OSError, DownloaderException) as exc:
            logger.warning(f"Could not cleanly remove workspace for job {job_id}: {exc}")
