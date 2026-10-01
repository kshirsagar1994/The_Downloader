import asyncio

from app.config import get_settings
from app.core.errors import DownloaderException
from app.core.logging import logger
from app.storage.cleanup import CleanupService

settings = get_settings()


class SweeperWorker:
    """Periodic daemon running background cleanup tasks."""

    _running: bool = False

    @classmethod
    async def run(cls) -> None:
        cls._running = True
        logger.info(
            f"SweeperWorker started. Running every {settings.CLEANUP_INTERVAL_SECONDS}s (Expiry: {settings.DOWNLOAD_EXPIRY_SECONDS}s)."
        )
        while cls._running:
            try:
                CleanupService.sweep_expired_jobs()
            except (OSError, DownloaderException) as exc:
                logger.error(f"Error during storage sweeping: {exc}")

            await asyncio.sleep(settings.CLEANUP_INTERVAL_SECONDS)

    @classmethod
    def stop(cls) -> None:
        cls._running = False
