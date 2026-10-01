import asyncio
from typing import Any

import yt_dlp

from app.config import get_settings
from app.core.errors import (
    ExtractionFailedError,
    OperationTimeoutError,
    PrivateContentError,
    UnsupportedUrlError,
)
from app.core.logging import logger
from app.schemas.media import ExtractionResult
from app.security.ssrf import validate_url_ssrf
from app.services.metadata_service import MetadataService

settings = get_settings()


class YtDlpService:
    """Encapsulated extraction and download service wrapping the yt-dlp engine."""

    @classmethod
    async def extract_info(cls, url: str) -> ExtractionResult:
        # Step 1: Pre-flight SSRF Validation
        validated_url = validate_url_ssrf(url)

        ydl_opts: dict[str, Any] = {
            "extract_flat": False,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "socket_timeout": 15,
            "playlist_items": f"1-{settings.MAX_PLAYLIST_ITEMS}",
        }

        try:
            logger.info(f"Extracting metadata for URL: {validated_url}")
            # Run blocking extraction in worker thread with timeout
            raw_info = await asyncio.wait_for(
                asyncio.to_thread(cls._run_extraction, validated_url, ydl_opts),
                timeout=settings.MAX_EXTRACTION_TIMEOUT_SECONDS,
            )

            if not raw_info or not isinstance(raw_info, dict):
                raise ExtractionFailedError("No metadata returned by extractor.")

            return MetadataService.parse_extraction_result(validated_url, raw_info)

        except TimeoutError as exc:
            logger.error(f"Extraction timed out for URL: {validated_url}")
            raise OperationTimeoutError("Media analysis timed out. The source may be slow or unresponsive.") from exc

        except yt_dlp.utils.DownloadError as exc:
            err_msg = str(exc).lower()
            logger.error(f"yt-dlp DownloadError: {exc}")

            if "unsupported url" in err_msg or "no suitable extractor" in err_msg:
                raise UnsupportedUrlError(f"That URL is not currently supported: {exc}") from exc
            if "private" in err_msg or "sign in" in err_msg or "login" in err_msg or "members only" in err_msg:
                raise PrivateContentError("This media requires authentication or is private and cannot be accessed.") from exc
            if "not found" in err_msg or "404" in err_msg or "unavailable" in err_msg:
                raise ExtractionFailedError("The requested media was not found or is unavailable.") from exc

            raise ExtractionFailedError(f"Extraction failed: {exc}") from exc

        except Exception as exc:
            logger.error(f"Unexpected extraction exception: {exc}")
            raise ExtractionFailedError(f"Unable to extract media: {exc}") from exc

    @staticmethod
    def _run_extraction(url: str, options: dict[str, Any]) -> dict[str, Any]:
        """Synchronous yt-dlp execution helper."""
        with yt_dlp.YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=False)
