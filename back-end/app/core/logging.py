import logging
import re
import sys
from typing import ClassVar


class SensitiveDataFilter(logging.Filter):
    """Redacts sensitive credentials, cookies, tokens, and proxy passwords from log records."""

    _PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        # Redact cookie strings and Netscape cookies
        (re.compile(r'(?:cookies?|cookie_content)=["\']?[^\s"\'&]+', re.IGNORECASE), "cookie=[REDACTED]"),
        (re.compile(r'(?:\.youtube\.com|\.google\.com)\s+(?:TRUE|FALSE)\s+\S+\s+(?:TRUE|FALSE)\s+\d+\s+\S+\s+\S+', re.IGNORECASE), "[NETSCAPE_COOKIE_REDACTED]"),
        # Redact po_token / pot / visitor_data
        (re.compile(r'(?:po_token|pot|visitor_data)=["\']?[^\s"\'&]+', re.IGNORECASE), "po_token=[REDACTED]"),
        (re.compile(r'Generated POT:\s*[^\s"\'<>]+', re.IGNORECASE), "Generated POT: [REDACTED]"),
        (re.compile(r'web\.player\+[a-zA-Z0-9_\-\.]+', re.IGNORECASE), "web.player+[REDACTED]"),
        # Redact signed media URLs (e.g. googlevideo, cloudfront)
        (re.compile(r'https?://[^\s"\'<>]*(?:googlevideo\.com|cloudfront\.net|akamaized\.net)/[^\s"\'<>]+', re.IGNORECASE), "[SIGNED_MEDIA_URL_REDACTED]"),
        # Redact signature parameters in URLs or logs
        (re.compile(r'(?:[?&])(?:sig|signature)=[^\s"\'&]+', re.IGNORECASE), "&sig=[REDACTED]"),
        # Redact Authorization / Bearer tokens
        (re.compile(r'(?:bearer\s+[a-zA-Z0-9_\-\.]+)', re.IGNORECASE), "Bearer [REDACTED]"),
        # Redact passwords embedded in URLs: http://user:pass@host
        (re.compile(r'(://[^:\s]+:)[^@\s]+(@)', re.IGNORECASE), r"\1[REDACTED]\2"),
        # Redact passwords in query parameters
        (re.compile(r'(?:password|passwd|secret|api_key|token)=["\']?[^\s"\'&]+', re.IGNORECASE), "secret=[REDACTED]"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self._PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


def setup_logger(name: str = "media_downloader") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(SensitiveDataFilter())
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger()
