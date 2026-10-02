import shutil
import time

from app.config import get_settings
from app.core.logging import logger

settings = get_settings()


class CleanupService:
    """Scans and evicts expired media files and workspaces."""

    @classmethod
    def sweep_expired_jobs(cls) -> int:
        """
        Iterates over the ephemeral storage root and unlinks workspaces
        whose last modification timestamp exceeds DOWNLOAD_EXPIRY_SECONDS.
        """
        storage_root = settings.storage_path
        if not storage_root.exists() or not storage_root.is_dir():
            return 0

        now = time.time()
        expiry_threshold = now - settings.DOWNLOAD_EXPIRY_SECONDS
        evicted_count = 0

        for item in storage_root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                try:
                    mtime = item.stat().st_mtime
                    if mtime < expiry_threshold:
                        logger.info(f"Sweeping expired workspace: {item.name} (age: {int(now - mtime)}s)")
                        shutil.rmtree(str(item), ignore_errors=True)
                        evicted_count += 1
                except (OSError, PermissionError) as exc:
                    logger.warning(f"Error inspecting directory {item.name}: {exc}")

        if evicted_count > 0:
            logger.info(f"Sweeper finished: Evicted {evicted_count} expired job workspaces.")

        return evicted_count
