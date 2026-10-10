import re
from typing import Any

from fastapi import status


def sanitize_error_details(details: Any) -> Any:
    """Removes cookies, authorization tokens, passwords, and secrets from error details."""
    if details is None:
        return None
    text = str(details)
    # Redact cookie strings
    text = re.sub(r'(?:cookies?|cookie_content)=["\']?[^\s"\'&]+', "cookie=[REDACTED]", text, flags=re.IGNORECASE)
    # Redact tokens
    text = re.sub(r'(?:po_token|token|pot|visitor_data)=["\']?[^\s"\'&]+', "token=[REDACTED]", text, flags=re.IGNORECASE)
    # Redact passwords in URLs (http://user:pass@host)
    text = re.sub(r'(://[^:\s]+:)[^@\s]+(@)', r"\1[REDACTED]\2", text)
    # Redact bearer headers
    text = re.sub(r'(?:bearer\s+[a-zA-Z0-9_\-\.]+)', "Bearer [REDACTED]", text, flags=re.IGNORECASE)
    # Truncate overly verbose traces to avoid leaking internal server layout
    if len(text) > 400:
        text = text[:400] + "..."
    return text


class DownloaderException(Exception):
    """Base exception for media downloader operations with structured error metadata."""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_DOWNLOAD_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        retryable: bool = False,
        user_action: str | None = None,
        details: Any | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.retryable = retryable
        self.user_action = user_action or "Please verify the URL or try again later."
        self.details = sanitize_error_details(details)


# =========================================================================
# Canonical Phase 4 Error Taxonomy
# =========================================================================

class BotVerificationRequiredError(DownloaderException):
    """YouTube challenged the request with BotGuard or bot verification."""

    def __init__(
        self,
        message: str = "YouTube requires additional verification for this request.",
        user_action: str = "Check the server's authorized authentication and token-provider configuration.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="BOT_VERIFICATION_REQUIRED",
            status_code=status.HTTP_403_FORBIDDEN,
            retryable=False,
            user_action=user_action,
            details=details,
        )


class AuthenticationRequiredError(DownloaderException):
    """Media requires account authentication, membership, or age verification."""

    def __init__(
        self,
        message: str = "This media requires authentication, membership, or a signed-in account to access.",
        user_action: str = "Provide valid authentication cookies with access to this content.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_REQUIRED",
            status_code=status.HTTP_403_FORBIDDEN,
            retryable=False,
            user_action=user_action,
            details=details,
        )


class POTokenConfigurationError(DownloaderException):
    """PO Token Provider is misconfigured, unreachable, or failed to generate token."""

    def __init__(
        self,
        message: str = "YouTube requested a Proof-of-Origin token that could not be generated.",
        user_action: str = "Verify the PO Token Provider service is running and accessible.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="PO_TOKEN_CONFIGURATION_ERROR",
            status_code=status.HTTP_502_BAD_GATEWAY,
            retryable=True,
            user_action=user_action,
            details=details,
        )


class ExtractorOrVersionError(DownloaderException):
    """URL unsupported, or yt-dlp extractor / JS challenge solver issue."""

    def __init__(
        self,
        message: str = "That URL is not supported or media could not be parsed.",
        user_action: str = "Verify the URL is valid or check yt-dlp version and JavaScript runtime.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="EXTRACTOR_OR_VERSION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            retryable=False,
            user_action=user_action,
            details=details,
        )


class VideoUnavailableError(DownloaderException):
    """Target media was removed, deleted, private, or does not exist."""

    def __init__(
        self,
        message: str = "The requested media was not found or is unavailable.",
        user_action: str = "Verify that the media exists, is public, and is available in the server's region.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="VIDEO_UNAVAILABLE",
            status_code=status.HTTP_404_NOT_FOUND,
            retryable=False,
            user_action=user_action,
            details=details,
        )


class NetworkTimeoutError(DownloaderException):
    """Connection or socket timed out while reaching the source."""

    def __init__(
        self,
        message: str = "A temporary network timeout occurred while connecting to the media source.",
        user_action: str = "The media source timed out. Please try again in a few moments.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="NETWORK_TIMEOUT",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            retryable=True,
            user_action=user_action,
            details=details,
        )


class RateLimitedError(DownloaderException):
    """Upstream service or server rate limit reached."""

    def __init__(
        self,
        message: str = "Too many requests. Upstream platform or server rate limit exceeded.",
        user_action: str = "Please wait a moment before trying again.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            retryable=True,
            user_action=user_action,
            details=details,
        )


class ServerConfigurationError(DownloaderException):
    """Server-side configuration or package dependency missing."""

    def __init__(
        self,
        message: str = "Server configuration error encountered during media processing.",
        user_action: str = "Verify server dependencies (such as FFmpeg) and environment settings.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="SERVER_CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=False,
            user_action=user_action,
            details=details,
        )


class UnknownDownloadError(DownloaderException):
    """Catch-all for unclassified download and extraction exceptions."""

    def __init__(
        self,
        message: str = "An unexpected error occurred during media download or extraction.",
        user_action: str = "Please verify the link and try again, or try another format.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="UNKNOWN_DOWNLOAD_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=False,
            user_action=user_action,
            details=details,
        )


# =========================================================================
# Legacy Aliases & Specialized Exceptions for Backward Compatibility
# =========================================================================

class UnsupportedUrlError(ExtractorOrVersionError):
    def __init__(self, message: str = "That URL is not currently supported.", details: Any | None = None):
        super().__init__(message=message, details=details)
        self.code = "UNSUPPORTED_URL"
        self.status_code = status.HTTP_400_BAD_REQUEST


class PrivateContentError(AuthenticationRequiredError):
    def __init__(
        self,
        message: str = "This media requires authentication or is private and cannot be accessed.",
        details: Any | None = None,
    ):
        super().__init__(message=message, details=details)
        self.code = "PRIVATE_CONTENT"


class RateLimitExceededError(RateLimitedError):
    def __init__(self, message: str = "Too many requests. Please try again later.", details: Any | None = None):
        super().__init__(message=message, details=details)


class ExtractionFailedError(ExtractorOrVersionError):
    def __init__(self, message: str = "We couldn't extract media information from this URL.", details: Any | None = None):
        super().__init__(message=message, details=details)
        self.code = "EXTRACTION_FAILED"


class FormatUnavailableError(DownloaderException):
    def __init__(self, message: str = "The selected format is not available."):
        super().__init__(
            message=message,
            code="FORMAT_UNAVAILABLE",
            status_code=status.HTTP_400_BAD_REQUEST,
            retryable=False,
            user_action="Select an alternative resolution or format for this media.",
        )


class ProcessingFailedError(UnknownDownloadError):
    def __init__(self, message: str = "Media processing failed.", details: Any | None = None):
        super().__init__(message=message, details=details)
        self.code = "PROCESSING_FAILED"


class FileTooLargeError(DownloaderException):
    def __init__(self, message: str = "This file exceeds the allowed download size limit."):
        super().__init__(
            message=message,
            code="FILE_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            retryable=False,
            user_action="Choose a lower resolution or shorter media clip.",
        )


class OperationTimeoutError(NetworkTimeoutError):
    def __init__(self, message: str = "The operation took too long and timed out."):
        super().__init__(message=message)
        self.code = "TIMEOUT"


class SSRFValidationError(DownloaderException):
    def __init__(self, message: str = "Access to local/private network resources is strictly prohibited."):
        super().__init__(
            message=message,
            code="SSRF_BLOCKED",
            status_code=status.HTTP_403_FORBIDDEN,
            retryable=False,
            user_action="Only public web addresses can be accessed.",
        )


class JobNotFoundError(DownloaderException):
    def __init__(self, message: str = "Requested download job was not found or has expired."):
        super().__init__(
            message=message,
            code="JOB_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            retryable=False,
            user_action="Start a new download task.",
        )


class YouTubeBotCheckError(BotVerificationRequiredError):
    def __init__(
        self,
        message: str = (
            "YouTube temporarily challenged this request with bot verification on this server. "
            "To resolve on cloud hosts, configure YOUTUBE_COOKIES, PO_TOKEN_PROVIDER_URL, or a residential PROXY."
        ),
        details: Any | None = None,
        user_action: str = "Configure authorized cookies, a PO Token provider, or an authorized proxy.",
    ):
        super().__init__(message=message, user_action=user_action, details=details)


class POTokenError(POTokenConfigurationError):
    def __init__(
        self,
        message: str = "PO Token provider was unable to generate a valid token for this media request.",
        details: Any | None = None,
    ):
        super().__init__(message=message, details=details)


class LoginRequiredError(AuthenticationRequiredError):
    def __init__(
        self,
        message: str = "This media requires a signed-in account or membership to access.",
        details: Any | None = None,
    ):
        super().__init__(message=message, details=details)
        self.code = "LOGIN_REQUIRED"


class AgeRestrictedError(AuthenticationRequiredError):
    def __init__(
        self,
        message: str = "This content is age-restricted and requires account authentication.",
        details: Any | None = None,
    ):
        super().__init__(message=message, details=details)
        self.code = "AGE_RESTRICTED"


class NetworkError(NetworkTimeoutError):
    def __init__(
        self,
        message: str = "A temporary network error occurred while connecting to the media source.",
        details: Any | None = None,
    ):
        super().__init__(message=message, details=details)
        self.code = "NETWORK_ERROR"


class FFmpegError(ServerConfigurationError):
    def __init__(
        self,
        message: str = "Media transcoding or stream merging failed.",
        details: Any | None = None,
    ):
        super().__init__(message=message, details=details)
        self.code = "FFMPEG_ERROR"
