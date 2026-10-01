"""Standalone sweeper daemon process."""
import asyncio
import sys
from pathlib import Path

# Add api directory to sys.path
api_root = (Path(__file__).resolve().parent.parent / "api").resolve()
sys.path.insert(0, str(api_root))

from app.core.logging import logger
from app.workers.sweeper_worker import SweeperWorker


async def main():
    logger.info("Starting Storage Sweeper Worker...")
    await SweeperWorker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sweeper terminated by signal.")
