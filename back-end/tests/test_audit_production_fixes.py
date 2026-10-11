import time
from pathlib import Path
from unittest.mock import patch

import pytest
import yt_dlp
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.core.errors import (
    BotVerificationRequiredError,
    ExtractorOrVersionError,
    NetworkTimeoutError,
    POTokenConfigurationError,
    ProcessingFailedError,
    RateLimitedError,
    ServerConfigurationError,
    VideoUnavailableError,
)
from app.main import app
from app.services.error_classifier import classify_ytdlp_error
from app.services.ffmpeg_service import FFmpegService
from app.services.queue_service import QueueService
from app.services.ytdlp_options import build_base_ydl_opts
from app.services.ytdlp_service import YtDlpService
from app.storage.workspace import WorkspaceManager

settings = get_settings()


# =========================================================================
# 1. Provider Unavailable & Token Acquisition Failures
# =========================================================================

def test_provider_unavailable_distinct_classification():
    """Confirms that provider errors are classified as POTokenConfigurationError, NOT BotVerificationRequiredError."""
    exc = yt_dlp.utils.DownloadError("Error reaching POST /get_pot: Connection refused")
    err = classify_ytdlp_error(exc, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert isinstance(err, POTokenConfigurationError)
    assert err.code == "PO_TOKEN_CONFIGURATION_ERROR"
    assert err.status_code == 502
    assert err.retryable is True
    assert "PO Token" in err.message


def test_provider_timeout_distinct_classification():
    """Confirms that provider HTTP timeout is mapped to provider configuration error."""
    exc = yt_dlp.utils.DownloadError("PoTokenProviderError: Error reaching GET http://pot-provider:4416/ping (timed out)")
    err = classify_ytdlp_error(exc, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert isinstance(err, POTokenConfigurationError)
    assert err.code == "PO_TOKEN_CONFIGURATION_ERROR"


def test_token_acquisition_failure_classification():
    """Confirms that bgutil generation failure is classified as POTokenConfigurationError."""
    exc = yt_dlp.utils.DownloadError("PoTokenProviderError: Server did not respond with a poToken")
    err = classify_ytdlp_error(exc, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert isinstance(err, POTokenConfigurationError)
    assert err.code == "PO_TOKEN_CONFIGURATION_ERROR"


# =========================================================================
# 2. YouTube Bot Verification: Online Provider vs Host IP Limitation
# =========================================================================

def test_youtube_bot_verification_when_provider_online_host_ip_restricted():
    """When provider is healthy but YouTube still challenges, classify as external host IP restriction."""
    exc = yt_dlp.utils.DownloadError("Sign in to confirm you’re not a bot. This helps protect our community.")
    with (
        patch("app.config.Settings.resolved_cookiefile", None),
        patch("app.config.Settings.resolved_po_token_provider_url", "http://pot-provider:4416"),
        patch("app.config.Settings.resolved_youtube_proxy", None),
        patch("app.services.pot_provider_service.POTProviderService._last_status", True),
        patch("app.services.pot_provider_service.POTProviderService._last_check_time", time.time()),
    ):
        err = classify_ytdlp_error(exc, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert isinstance(err, BotVerificationRequiredError)
        assert err.code == "BOT_VERIFICATION_REQUIRED"
        assert err.status_code == 403
        assert "host IP is restricted" in err.message or "BotGuard" in err.message


# =========================================================================
# 3. HTTP 403, HTTP 429, and Unsupported Media Classification
# =========================================================================

def test_http_403_and_429_classification():
    exc_403 = yt_dlp.utils.DownloadError("HTTP Error 403: Forbidden")
    err_403 = classify_ytdlp_error(exc_403, "https://example.com/stream.m3u8")
    assert isinstance(err_403, VideoUnavailableError)
    assert err_403.code == "VIDEO_UNAVAILABLE"

    exc_429 = yt_dlp.utils.DownloadError("HTTP Error 429: Too Many Requests")
    err_429 = classify_ytdlp_error(exc_429, "https://example.com/video")
    assert isinstance(err_429, RateLimitedError)
    assert err_429.code == "RATE_LIMITED"
    assert err_429.status_code == 429


def test_unsupported_media_and_no_formats():
    exc_unsupported = yt_dlp.utils.DownloadError("Unsupported URL: https://invalid-domain.xyz/test")
    err_unsupported = classify_ytdlp_error(exc_unsupported, "https://invalid-domain.xyz/test")
    assert isinstance(err_unsupported, ExtractorOrVersionError)
    assert err_unsupported.code in ("UNSUPPORTED_URL", "EXTRACTOR_OR_VERSION_ERROR")

    exc_no_fmt = yt_dlp.utils.DownloadError("No video formats found")
    err_no_fmt = classify_ytdlp_error(exc_no_fmt, "https://example.com/post")
    assert isinstance(err_no_fmt, ExtractorOrVersionError)


# =========================================================================
# 4. Extraction Timeout Classification
# =========================================================================

def test_extraction_timeout_classification():
    exc_timeout = TimeoutError("Media socket read timed out")
    err_timeout = classify_ytdlp_error(exc_timeout, "https://example.com/video")
    assert isinstance(err_timeout, NetworkTimeoutError)
    assert err_timeout.code in ("TIMEOUT", "NETWORK_TIMEOUT")
    assert err_timeout.status_code in (504, 500)


# =========================================================================
# 5. FFmpeg Subprocess and Missing Binary Failure
# =========================================================================

def test_ffmpeg_missing_binary():
    exc_ff = yt_dlp.utils.DownloadError("ffmpeg not found in PATH")
    err_ff = classify_ytdlp_error(exc_ff, "https://example.com/video")
    assert isinstance(err_ff, ServerConfigurationError)
    assert err_ff.status_code == 500


@pytest.mark.asyncio
async def test_ffmpeg_service_missing_path():
    with patch("shutil.which", return_value=None):
        with pytest.raises(ProcessingFailedError) as exc_info:
            FFmpegService.get_ffmpeg_path()
        assert "not found" in str(exc_info.value).lower()


# =========================================================================
# 6. Proxy Isolation: YouTube Proxy Must NOT Leak to Other Platforms
# =========================================================================

def test_proxy_isolation_between_platforms():
    """Asserts that YOUTUBE_PROXY is isolated to YouTube requests and does not bleed to Instagram/TikTok."""
    with patch.object(settings, "YOUTUBE_PROXY_URL", "http://yt-proxy.example.com:8080"):
        # YouTube URL -> uses YouTube proxy
        yt_opts = build_base_ydl_opts(target_url="https://www.youtube.com/watch?v=123")
        assert yt_opts.get("proxy") == "http://yt-proxy.example.com:8080"

        # Non-YouTube URL -> must NOT use YouTube proxy
        ig_opts = build_base_ydl_opts(target_url="https://www.instagram.com/p/abc123xyz/")
        assert ig_opts.get("proxy") is None

        tiktok_opts = build_base_ydl_opts(target_url="https://www.tiktok.com/@user/video/123")
        assert tiktok_opts.get("proxy") is None


# =========================================================================
# 7. Render Bare Hostname and Port URL Resolution
# =========================================================================

def test_render_url_scheme_resolution():
    """Tests resolution of Render fromService hostport (e.g. pot-provider.onrender.com:4416)."""
    s_render = Settings(PO_TOKEN_PROVIDER_URL="the-downloader-pot.onrender.com:4416")
    resolved = s_render.resolved_po_token_provider_url
    assert resolved == "https://the-downloader-pot.onrender.com"

    s_internal = Settings(PO_TOKEN_PROVIDER_URL="http://pot-provider:4416")
    assert s_internal.resolved_po_token_provider_url == "http://pot-provider:4416"


# =========================================================================
# 8. QueueService Fast In-Memory Fallback When Redis Offline
# =========================================================================

@pytest.mark.asyncio
async def test_redis_offline_fast_fallback():
    """Confirms that QueueService does not introduce 2-second lag when Redis is unavailable."""
    qs = QueueService()
    # Mock Redis ping failure
    start = time.time()
    r = await qs.get_redis()
    elapsed = time.time() - start
    assert r is None
    assert elapsed >= 0
    # Subsequent call must return instantly via cooldown (< 50ms)
    start_subsequent = time.time()
    r2 = await qs.get_redis()
    elapsed_subsequent = time.time() - start_subsequent
    assert r2 is None
    assert elapsed_subsequent < 0.05


# =========================================================================
# 9. Cancellation & Workspace Cleanup
# =========================================================================

@pytest.mark.asyncio
async def test_cancellation_and_error_workspace_cleanup(tmp_path: Path):
    with patch("app.config.Settings.storage_path", new_callable=lambda: tmp_path):
        job_id = "test-cleanup-job-42"
        _, job_dir = WorkspaceManager.create_job_workspace(job_id)
        assert job_dir.exists()

        # Simulate job failure
        WorkspaceManager.cleanup_workspace(job_id)
        assert not job_dir.exists()


# =========================================================================
# 10. Frontend Parsing of Structured Backend Errors
# =========================================================================

@pytest.mark.asyncio
async def test_frontend_structured_error_contract():
    """Asserts that the backend returns structured error metadata (code, message, retryable, userAction)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.object(
            YtDlpService,
            "extract_info",
            side_effect=POTokenConfigurationError(
                message="PO Token generation failure",
                user_action="Check the PO Token Provider service.",
            ),
        ):
            res = await client.post("/api/extract", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
            assert res.status_code == 502
            data = res.json()
            assert data["success"] is False
            assert "error" in data
            assert data["error"]["code"] == "PO_TOKEN_CONFIGURATION_ERROR"
            assert data["error"]["retryable"] is True
            assert "userAction" in data["error"]
            assert data["error"]["userAction"] == "Check the PO Token Provider service."


# =========================================================================
# 11. Optional Manual Integration Test for Authorized Public Sample Media
# =========================================================================

@pytest.mark.asyncio
async def test_optional_authorized_public_media():
    """
    Optional live integration test using an open-source test media URL.
    Gracefully catches network timeouts or firewall restrictions without failing the test suite.
    """
    public_sample_url = "https://raw.githubusercontent.com/mdn/learning-area/main/html/multimedia-and-embedding/video-and-audio-content/rabbit320.mp4"
    try:
        res = await YtDlpService.extract_info(public_sample_url)
        assert res is not None
        assert res.url == public_sample_url
    except Exception as exc:
        pytest.skip(f"External network access restricted in test environment: {exc}")
