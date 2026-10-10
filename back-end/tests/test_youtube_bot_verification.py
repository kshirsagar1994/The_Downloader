import base64
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import yt_dlp
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.core.errors import (
    AuthenticationRequiredError,
    BotVerificationRequiredError,
    NetworkTimeoutError,
    POTokenConfigurationError,
    ServerConfigurationError,
    VideoUnavailableError,
)
from app.core.logging import SensitiveDataFilter
from app.main import app
from app.services.error_classifier import classify_ytdlp_error
from app.services.pot_provider_service import POTProviderService
from app.services.ytdlp_service import YtDlpService

# =========================================================================
# 1. Normal Supported Video Download (Mocked yt-dlp)
# =========================================================================

@pytest.mark.asyncio
async def test_normal_video_extraction_mocked():
    sample_metadata = {
        "id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "duration": 213,
        "uploader": "RickAstleyVEVO",
        "extractor_key": "Youtube",
        "formats": [
            {
                "format_id": "18",
                "ext": "mp4",
                "width": 640,
                "height": 360,
                "vcodec": "avc1.42001E",
                "acodec": "mp4a.40.2",
            }
        ],
    }

    with patch.object(YtDlpService, "_run_extraction", return_value=sample_metadata):
        result = await YtDlpService.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.title == "Rick Astley - Never Gonna Give You Up"
        assert result.platform == "Youtube"
        assert len(result.video_formats) >= 1


# =========================================================================
# 2. Missing Optional Cookie Configuration
# =========================================================================

def test_missing_optional_cookie_configuration(tmp_path: Path):
    s = Settings(
        DOWNLOAD_DIR=str(tmp_path),
        YOUTUBE_COOKIES=None,
        YOUTUBE_COOKIES_FILE=None,
        COOKIES_FILE=None,
    )
    assert s.resolved_cookiefile is None


# =========================================================================
# 3. Base64 and File Cookie Configuration
# =========================================================================

def test_base64_and_file_cookie_configuration(tmp_path: Path):
    # Test base64 decoding
    raw_netscape = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t2147483647\tSID\tsecret_cookie_val"
    b64_netscape = base64.b64encode(raw_netscape.encode("utf-8")).decode("utf-8")

    s_b64 = Settings(
        DOWNLOAD_DIR=str(tmp_path / "b64"),
        YOUTUBE_COOKIES=b64_netscape,
    )
    cookie_file = s_b64.resolved_cookiefile
    assert cookie_file is not None
    assert Path(cookie_file).exists()
    assert "secret_cookie_val" in Path(cookie_file).read_text(encoding="utf-8")

    # Test file path configuration
    custom_file = tmp_path / "custom_cookies.txt"
    custom_file.write_text(raw_netscape, encoding="utf-8")
    s_file = Settings(
        DOWNLOAD_DIR=str(tmp_path / "file"),
        YOUTUBE_COOKIES_FILE=str(custom_file),
    )
    assert s_file.resolved_cookiefile == str(custom_file.resolve())


# =========================================================================
# 4. Invalid or Expired Cookies Detection
# =========================================================================

def test_invalid_or_expired_cookies_detection():
    exc = yt_dlp.utils.DownloadError("Sign in to confirm you’re not a bot. This helps protect our community.")
    with patch("app.config.Settings.resolved_cookiefile", "/tmp/cookies.txt"):
        err = classify_ytdlp_error(exc, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert isinstance(err, BotVerificationRequiredError)
        assert err.code == "BOT_VERIFICATION_REQUIRED"
        assert "authentication cookies may have expired" in err.message.lower()
        assert err.retryable is False


# =========================================================================
# 5. Missing or Incompatible PO Token Provider
# =========================================================================

def test_missing_or_incompatible_po_token_provider():
    # Dangerous or invalid schemas must be rejected
    s_invalid = Settings(PO_TOKEN_PROVIDER_URL="gopher://127.0.0.1:4416")
    assert s_invalid.resolved_po_token_provider_url is None

    s_file = Settings(PO_TOKEN_PROVIDER_URL="file:///etc/passwd")
    assert s_file.resolved_po_token_provider_url is None

    s_valid = Settings(PO_TOKEN_PROVIDER_URL="http://pot-provider:4416/")
    assert s_valid.resolved_po_token_provider_url == "http://pot-provider:4416"


# =========================================================================
# 6. Provider Timeout or Connection Failure
# =========================================================================

@pytest.mark.asyncio
async def test_provider_timeout_or_connection_failure():
    with (
        patch("app.config.Settings.resolved_po_token_provider_url", "http://pot-provider:4416"),
        patch("httpx.AsyncClient.get", side_effect=Exception("Connection timed out")),
    ):
        POTProviderService._last_check_time = 0  # Force refresh
        health = await POTProviderService.check_health(timeout=1.0)
        assert health["configured"] is True
        assert health["available"] is False
        assert "unreachable" in health["details"].lower() or "offline" in health["details"].lower()

    # yt-dlp error when provider fails
    exc = yt_dlp.utils.DownloadError("Error reaching POST /get_pot: Connection refused")
    classified = classify_ytdlp_error(exc, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert isinstance(classified, POTokenConfigurationError)
    assert classified.code == "PO_TOKEN_CONFIGURATION_ERROR"
    assert classified.retryable is True


# =========================================================================
# 7. YouTube Bot Verification Classification
# =========================================================================

def test_youtube_bot_verification_error_classification():
    exc = yt_dlp.utils.DownloadError("Sign in to confirm you’re not a bot. This helps protect our community.")
    with (
        patch("app.config.Settings.resolved_cookiefile", None),
        patch("app.config.Settings.resolved_po_token_provider_url", None),
        patch("app.config.Settings.resolved_proxy", None),
    ):
        err = classify_ytdlp_error(exc, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert isinstance(err, BotVerificationRequiredError)
        assert err.code == "BOT_VERIFICATION_REQUIRED"
        assert err.status_code == 403
        assert err.retryable is False
        assert "YOUTUBE_COOKIES" in err.message or "PO_TOKEN_PROVIDER_URL" in err.message


# =========================================================================
# 8. Unavailable or Private Videos
# =========================================================================

def test_unavailable_or_private_videos():
    exc_404 = yt_dlp.utils.DownloadError("ERROR: Video unavailable. This video has been removed by the uploader")
    err_404 = classify_ytdlp_error(exc_404, "https://www.youtube.com/watch?v=deleted_123")
    assert isinstance(err_404, VideoUnavailableError)
    assert err_404.code == "VIDEO_UNAVAILABLE"
    assert err_404.status_code == 404

    exc_priv = yt_dlp.utils.DownloadError("ERROR: Private video. Sign in if you've been granted access to this video")
    err_priv = classify_ytdlp_error(exc_priv, "https://www.youtube.com/watch?v=private_123")
    assert isinstance(err_priv, AuthenticationRequiredError)
    assert err_priv.code == "AUTHENTICATION_REQUIRED"
    assert err_priv.status_code == 403


# =========================================================================
# 9. FFmpeg Missing or Unavailable
# =========================================================================

def test_ffmpeg_missing_or_unavailable():
    exc_ff = yt_dlp.utils.DownloadError("ffmpeg not found. Please install or provide path to ffmpeg")
    err_ff = classify_ytdlp_error(exc_ff, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert isinstance(err_ff, ServerConfigurationError)
    assert err_ff.code == "SERVER_CONFIGURATION_ERROR"
    assert err_ff.status_code == 500


# =========================================================================
# 10. Network Timeout & Limited Retries
# =========================================================================

def test_network_timeout_and_limited_retries():
    # TimeoutError
    err_timeout = classify_ytdlp_error(TimeoutError("Socket read timed out"), "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert isinstance(err_timeout, NetworkTimeoutError)
    assert err_timeout.code == "NETWORK_TIMEOUT"
    assert err_timeout.status_code == 504
    assert err_timeout.retryable is True

    # Ensure _run_extraction does NOT loop 9 times on bot verification
    call_count = 0

    class MockYDL:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def extract_info(self, url, download=False):
            nonlocal call_count
            call_count += 1
            raise yt_dlp.utils.DownloadError("Sign in to confirm you're not a bot.")

    with patch("yt_dlp.YoutubeDL", side_effect=MockYDL):
        with pytest.raises(yt_dlp.utils.DownloadError):
            YtDlpService._run_extraction("https://www.youtube.com/watch?v=test", {})

        # Must exit immediately after primary attempt without hammering fallbacks
        assert call_count == 1


# =========================================================================
# 11. Secret Redaction in Logs and API Responses
# =========================================================================

def test_secret_redaction_in_logs():
    filter_instance = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Using po_token=abc123secret and cookie=SESSION_SECRET_99 and proxy=http://user:secretpass@proxy.com:8080",
        args=(),
        exc_info=None,
    )
    filter_instance.filter(record)
    assert "abc123secret" not in record.msg
    assert "SESSION_SECRET_99" not in record.msg
    assert "secretpass" not in record.msg
    assert "[REDACTED]" in record.msg


@pytest.mark.asyncio
async def test_secret_redaction_in_api_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger an exception with sensitive details
        with patch.object(
            YtDlpService,
            "extract_info",
            side_effect=BotVerificationRequiredError(
                message="YouTube challenged bot verification.",
                details="Failed with po_token=SECRET_TOKEN_XYZ and cookie=MY_COOKIE_123 and http://admin:pass123@proxy.com",
            ),
        ):
            res = await client.post("/api/extract", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
            assert res.status_code == 403
            data = res.json()
            assert data["success"] is False
            assert data["error"]["code"] == "BOT_VERIFICATION_REQUIRED"
            assert "SECRET_TOKEN_XYZ" not in str(data)
            assert "MY_COOKIE_123" not in str(data)
            assert "pass123" not in str(data)


# =========================================================================
# 12. Cleanup of Temporary Auth Files
# =========================================================================

def test_cleanup_of_temporary_auth_files(tmp_path: Path):
    s = Settings(
        DOWNLOAD_DIR=str(tmp_path),
        YOUTUBE_COOKIES="sample cookie text",
    )
    created_path = s.resolved_cookiefile
    assert created_path is not None
    assert Path(created_path).exists()

    s.cleanup_temp_cookies()
    assert not Path(created_path).exists()
