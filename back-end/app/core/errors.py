from typing import Any

from fastapi import status


class DownloaderException(Exception):
    """Base exception for media downloader operations."""
    def __init__(
        self,
        message: str,
        code: str = "DOWNLOADER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Any | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class UnsupportedUrlError(DownloaderException):
    def __init__(self, message: str = "That URL is not currently supported.", details: Any | None = None):
        super().__init__(
            message=message,
            code="UNSUPPORTED_URL",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class PrivateContentError(DownloaderException):
    def __init__(
        self,
        message: str = "This media requires authentication or is private and cannot be accessed.",
        details: Any | None = None,
    ):
        super().__init__(
            message=message,
            code="PRIVATE_CONTENT",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class RateLimitExceededError(DownloaderException):
    def __init__(self, message: str = "Too many requests. Please try again later.", details: Any | None = None):
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class ExtractionFailedError(DownloaderException):
    def __init__(self, message: str = "We couldn't extract media information from this URL.", details: Any | None = None):
        super().__init__(
            message=message,
            code="EXTRACTION_FAILED",
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


class FormatUnavailableError(DownloaderException):
    def __init__(self, message: str = "The selected format is not available."):
        super().__init__(
            message=message,
            code="FORMAT_UNAVAILABLE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class ProcessingFailedError(DownloaderException):
    def __init__(self, message: str = "Media processing failed."):
        super().__init__(
            message=message,
            code="PROCESSING_FAILED",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class FileTooLargeError(DownloaderException):
    def __init__(self, message: str = "This file exceeds the allowed download size limit."):
        super().__init__(
            message=message,
            code="FILE_TOO_LARGE",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class OperationTimeoutError(DownloaderException):
    def __init__(self, message: str = "The operation took too long and timed out."):
        super().__init__(
            message=message,
            code="TIMEOUT",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


class SSRFValidationError(DownloaderException):
    def __init__(self, message: str = "Access to local/private network resources is strictly prohibited."):
        super().__init__(
            message=message,
            code="SSRF_BLOCKED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class JobNotFoundError(DownloaderException):
    def __init__(self, message: str = "Requested download job was not found or has expired."):
        super().__init__(
            message=message,
            code="JOB_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )
