import asyncio

from app.config import get_settings
from app.core.errors import (
    AuthenticationRequiredError,
    BotVerificationRequiredError,
    DownloaderException,
    ExtractorOrVersionError,
    NetworkTimeoutError,
    POTokenConfigurationError,
    RateLimitedError,
    ServerConfigurationError,
    UnknownDownloadError,
    VideoUnavailableError,
)
from app.core.logging import logger


def classify_ytdlp_error(exc: Exception, url: str) -> DownloaderException:
    """
    Centralized, deterministic error classifier mapping yt-dlp exceptions,
    HTTP status codes, and extractor diagnostics to the canonical error taxonomy.
    Ensures zero sensitive credentials leak in error messages or details.
    """
    if isinstance(exc, DownloaderException):
        return exc

    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return NetworkTimeoutError(
            message="Media analysis or download timed out. The upstream server was unresponsive.",
            user_action="The operation timed out. Please retry in a few moments.",
            details=str(exc),
        )

    err_str = str(exc)
    err_msg = err_str.lower()
    settings = get_settings()

    # 1. YouTube Bot Verification & BotGuard Challenges
    if any(k in err_msg for k in ("confirm you’re not a bot", "confirm you're not a bot", "bot verification", "botguard", "automated queries", "captcha")):
        has_cookies = bool(settings.resolved_cookiefile)
        has_pot = bool(settings.resolved_po_token_provider_url or settings.YOUTUBE_PO_TOKEN)
        has_proxy = bool(settings.resolved_proxy)

        if has_cookies:
            msg = (
                "YouTube challenged this request with bot verification. "
                "The configured authentication cookies may have expired or need renewal."
            )
            action = "Update YOUTUBE_COOKIES with fresh cookies exported from an authorized session."
        elif has_pot:
            msg = (
                "YouTube challenged this request with bot verification. "
                "The PO Token Provider may need a refresh or the host IP is restricted."
            )
            action = "Verify PO_TOKEN_PROVIDER_URL health and ensure the token cache is active."
        elif has_proxy:
            msg = (
                "YouTube challenged this request with bot verification. "
                "The configured proxy address may be restricted by YouTube."
            )
            action = "Verify that YOUTUBE_PROXY is an authorized, operational proxy."
        else:
            msg = (
                "YouTube temporarily challenged this request with bot verification on this server. "
                "To resolve on cloud hosts, configure YOUTUBE_COOKIES, PO_TOKEN_PROVIDER_URL, or a residential PROXY."
            )
            action = "Configure authorized YouTube cookies (YOUTUBE_COOKIES) or PO_TOKEN_PROVIDER_URL in server settings."

        logger.warning(f"[ErrorClassifier] YouTube bot check triggered for {url}. Details: {exc}")
        return BotVerificationRequiredError(message=msg, user_action=action, details=err_str)

    # 2. Proof-of-Origin (PO Token) generation failures
    if any(k in err_msg for k in ("po_token", "pot-provider", "get_pot", "bgutil", "pot provider")):
        logger.warning(f"[ErrorClassifier] PO Token generation failure: {exc}")
        return POTokenConfigurationError(
            message="YouTube requested a Proof-of-Origin token that could not be generated.",
            user_action="Check the PO Token Provider service connectivity and configuration.",
            details=err_str,
        )

    # 3. Authentication & Account Access Required
    if any(k in err_msg for k in ("sign in", "login", "members only", "premium", "join this channel", "account required")):
        return AuthenticationRequiredError(
            message="This media requires a signed-in account or channel membership to access.",
            user_action="Configure authorized cookies with account access to view this content.",
            details=err_str,
        )

    if any(k in err_msg for k in ("age", "confirm your age")):
        return AuthenticationRequiredError(
            message="This content is age-restricted and requires account authentication.",
            user_action="Configure authorized cookies for an age-verified account.",
            details=err_str,
        )

    if "private" in err_msg:
        return AuthenticationRequiredError(
            message="This media is private and cannot be accessed without account authorization.",
            user_action="Verify permissions or supply authorized cookies.",
            details=err_str,
        )

    # 4. Server Configuration (FFmpeg / system binary missing)
    if "ffmpeg" in err_msg and any(k in err_msg for k in ("not found", "missing", "no such file")):
        return ServerConfigurationError(
            message="Media processing failed because FFmpeg is not available on this server.",
            user_action="Ensure FFmpeg is installed and accessible on PATH.",
            details=err_str,
        )

    # 5. Media Not Found / Unavailable
    if any(k in err_msg for k in ("not found", "404", "unavailable", "does not exist", "video has been removed", "deleted", "copyright")):
        return VideoUnavailableError(
            message="The requested media was not found or is no longer available.",
            user_action="Verify that the URL is correct, public, and not region-blocked.",
            details=err_str,
        )

    # 6. Rate Limits & 429
    if any(k in err_msg for k in ("429", "too many requests", "rate limit")):
        return RateLimitedError(
            message="The media source or server has rate-limited requests.",
            user_action="Wait a few minutes before retrying your download.",
            details=err_str,
        )

    # 7. Network & Connection Timeouts
    if any(k in err_msg for k in ("timed out", "connection refused", "network is unreachable", "connection reset", "socket timeout", "temporary failure in name resolution")):
        return NetworkTimeoutError(
            message="A temporary network error occurred while connecting to the source.",
            user_action="Check your connection or wait a moment for the source to respond.",
            details=err_str,
        )

    # 8. Unsupported URL or Extractor/Parser issues
    if any(k in err_msg for k in ("unsupported url", "no suitable extractor")):
        return ExtractorOrVersionError(
            message="That URL is not currently supported.",
            user_action="Verify that the link is supported (e.g. YouTube, Instagram, TikTok, X, etc.).",
            details=err_str,
        )

    # 9. Generic Fallback
    logger.error(f"[ErrorClassifier] Unclassified download error: {exc}")
    return UnknownDownloadError(
        message=f"Extraction or download failed: {exc}",
        user_action="Please verify the URL or try downloading an alternative format.",
        details=err_str,
    )
