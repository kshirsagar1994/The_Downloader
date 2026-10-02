import pytest

from app.core.errors import SSRFValidationError
from app.security.ssrf import validate_url_ssrf


def test_ssrf_blocks_loopback_and_private_ips():
    blocked_urls = [
        "http://127.0.0.1/test",
        "http://127.0.0.2:8080",
        "http://localhost:8000/api",
        "http://10.0.0.1/secret",
        "http://172.16.0.1/admin",
        "http://192.168.1.100/router",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0/",
        "http://[::1]/",
    ]

    for url in blocked_urls:
        with pytest.raises(SSRFValidationError):
            validate_url_ssrf(url)


def test_ssrf_blocks_invalid_schemes():
    invalid_schemes = [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "gopher://example.com/",
        "data:text/plain;base64,SGVsbG8=",
        "javascript:alert(1)",
    ]

    for url in invalid_schemes:
        with pytest.raises(SSRFValidationError):
            validate_url_ssrf(url)


def test_ssrf_allows_public_https_url():
    public_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = validate_url_ssrf(public_url)
    assert result == public_url
