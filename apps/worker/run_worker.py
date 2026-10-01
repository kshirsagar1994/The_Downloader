"""Standalone worker runner process."""
import asyncio
import sys
from pathlib import Path

# Add api directory to sys.path
api_root = (Path(__file__).resolve().parent.parent / "api").resolve()
sys.path.insert(0, str(api_root))

from app.config import get_settings
from app.core.logging import logger
from app.services.queue_service import queue_service

settings = get_settings()


async def main():
    logger.info(f"Starting Standalone Media Worker in {settings.APP_ENV} mode...")
    logger.info(f"Storage path: {settings.storage_path}")

    # Check Redis connectivity
    r = await queue_service.get_redis()
    if r:
        logger.info("Connected to Redis queue.")
    else:
        logger.info("Running with internal memory queue bridge.")

    logger.info("Worker is active and listening for background download tasks.")
    # Keep process alive
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker terminated by signal.")
