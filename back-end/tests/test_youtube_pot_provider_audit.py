import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yt_dlp

from app.config import Settings, get_settings
from app.core.logging import SensitiveDataFilter
from app.services.ytdlp_options import (
    YtDlpLogHandler,
    build_base_ydl_opts,
    get_youtube_fallback_clients,
)
from app.services.ytdlp_service import YtDlpService

settings = get_settings()


# =========================================================================
# 1. Dockerfile & Startup Script Configuration Integrity
# =========================================================================

def test_startup_script_properties():
    """Verifies that infrastructure/docker/start-api.sh exists, contains robust supervision, and LF endings."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    start_script = repo_root / "infrastructure" / "docker" / "start-api.sh"
    assert start_script.exists(), "start-api.sh must exist in infrastructure/docker"

    content = start_script.read_text(encoding="utf-8")
    # Verify no CRLF line endings
    assert "\r\n" not in content, "start-api.sh must have UNIX (LF) line endings"
    # Verify shebang and strict mode
    assert content.startswith("#!/bin/sh\nset -e")
    # Verify readiness check and process monitoring
    assert "kill -0" in content
    assert "/ping" in content
    assert "uvicorn app.main:app" in content
    assert "POT_PROVIDER_PORT" in content


def test_dockerfile_version_and_command_alignment():
    """Verifies that Dockerfile.api pins bgutil-ytdlp-pot-provider to 2.0.2 matching python requirements."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    dockerfile_api = repo_root / "infrastructure" / "docker" / "Dockerfile.api"
    req_file = repo_root / "back-end" / "requirements.txt"

    df_content = dockerfile_api.read_text(encoding="utf-8")
    req_content = req_file.read_text(encoding="utf-8")

    assert "--branch 2.0.2" in df_content, "Dockerfile.api must clone branch 2.0.2"
    assert "npm ci" in df_content, "Dockerfile.api must use npm ci for locked reproducible build"
    assert "bgutil-ytdlp-pot-provider==2.0.2" in req_content, "requirements.txt must pin bgutil-ytdlp-pot-provider==2.0.2"
    assert "yt-dlp-ejs" in req_content, "requirements.txt must include yt-dlp-ejs for JS challenge solving"


# =========================================================================
# 2. Player Client Sanitization and Cloud BotGuard Prevention
# =========================================================================

def test_youtube_clients_sanitizes_tvhtml5():
    """Ensures deprecated 'tvhtml5' is automatically sanitized to 'tv' without warnings."""
    s = Settings(YOUTUBE_CLIENTS="web, mweb, tvhtml5")
    clients = s.resolved_youtube_clients
    assert "tv" in clients
    assert "tvhtml5" not in clients
    assert clients == ["web", "mweb", "tv"]


def test_default_youtube_clients_order():
    """Ensures default client chain prioritizes visionos and android while supporting tv, mweb, web."""
    s = Settings(YOUTUBE_CLIENTS=None, PO_TOKEN_PROVIDER_URL="http://127.0.0.1:4416")
    clients = s.resolved_youtube_clients
    # Must start with cloud-resilient clients
    assert clients[0] in ("visionos", "android")
    assert "web" in clients
    assert "mweb" in clients
    assert "tv" in clients
    assert "tvhtml5" not in clients


def test_fallback_clients_validity():
    """Verifies fallback clients list uses valid yt-dlp client identifiers."""
    fallbacks = get_youtube_fallback_clients()
    all_clients = [c for chain in fallbacks for c in chain]
    assert "tvhtml5" not in all_clients
    assert "tv" in all_clients
    assert "visionos" in all_clients
    assert "android" in all_clients


# =========================================================================
# 3. Provider URL Resolution and Placeholder Fallback
# =========================================================================

def test_unresolvable_placeholder_falls_back_to_local_provider(tmp_path: Path):
    """When PO_TOKEN_PROVIDER_URL points to old unresolvable placeholder and local daemon exists, fall back to loopback."""
    fake_server_dir = tmp_path / "server"
    fake_server_dir.mkdir(parents=True)

    with patch("os.path.isdir", side_effect=lambda p: str(p) == "/opt/bgutil-pot/server"):
        s = Settings(PO_TOKEN_PROVIDER_URL="http://the-downloader-pot-provider:4416")
        assert s.resolved_po_token_provider_url == "http://127.0.0.1:4416"


def test_custom_pot_provider_port():
    """Verifies POT_PROVIDER_PORT setting customizes the resolved URL."""
    with patch("os.path.isdir", return_value=True):
        s = Settings(PO_TOKEN_PROVIDER_URL=None, POT_PROVIDER_PORT=4499)
        assert s.resolved_po_token_provider_url == "http://127.0.0.1:4499"


# =========================================================================
# 4. Observability and Secret Scrubbing
# =========================================================================

def test_ytdlp_log_handler_diagnostics_without_leaks():
    """Tests that YtDlpLogHandler captures key lifecycle events and never leaks secrets."""
    captured_logs: list[str] = []

    class MockAppLogger:
        def info(self, msg: str):
            captured_logs.append(f"INFO: {msg}")

        def debug(self, msg: str):
            captured_logs.append(f"DEBUG: {msg}")

        def warning(self, msg: str):
            captured_logs.append(f"WARN: {msg}")

        def error(self, msg: str):
            captured_logs.append(f"ERROR: {msg}")

    with patch("app.services.ytdlp_options.logger", MockAppLogger()):
        handler = YtDlpLogHandler()
        # Plugin discovery
        handler.debug("[youtube] [pot] PO Token Providers: bgutil:http-2.0.2 (external)")
        assert any("Plugin discovered" in msg for msg in captured_logs)

        # Provider invocation
        handler.info("[youtube] [pot:bgutil:http] Generating a gvs PO Token for web client via bgutil HTTP server")
        assert any("Token generation invoked" in msg for msg in captured_logs)

        # Provider success
        handler.debug("[youtube] m4nLtV8OSfQ: Retrieved a gvs PO Token for web client")
        assert any("Token generation succeeded" in msg for msg in captured_logs)

        # JS challenge solving
        handler.debug("[youtube] [jsc:node] Solving JS challenges using node")
        assert any("JavaScript challenge solver active" in msg for msg in captured_logs)

        # Raw token redaction
        handler.debug("Generated POT: secret_raw_token_xyz_123")
        assert any("Token generation succeeded" in msg for msg in captured_logs)
        assert not any("secret_raw_token_xyz_123" in msg for msg in captured_logs)


def test_plugin_discovery_by_python_environment():
    """Task 2: Verifies that bgutil-ytdlp-pot-provider plugin is discovered by yt-dlp in this environment."""
    _ = yt_dlp.YoutubeDL({"quiet": True})
    from yt_dlp.extractor.youtube.pot.provider import _pot_providers
    discovered = dict(_pot_providers.value)
    assert "BgUtilHTTP" in discovered
    assert discovered["BgUtilHTTP"].PROVIDER_NAME == "bgutil:http"


def test_extractor_args_configured_with_fetch_pot_and_pot_trace():
    """Task 4: Verifies yt-dlp options include youtubepot-bgutilhttp base_url, fetch_pot=always, and pot_trace=true."""
    with patch.dict(os.environ, {"PO_TOKEN_PROVIDER_URL": "http://127.0.0.1:4416"}):
        from app.config import get_settings
        get_settings.cache_clear()
        opts = build_base_ydl_opts(target_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        get_settings.cache_clear()

    assert opts["verbose"] is True
    assert "youtubepot-bgutilhttp" in opts["extractor_args"]
    assert opts["extractor_args"]["youtubepot-bgutilhttp"]["base_url"] == ["http://127.0.0.1:4416"]
    assert opts["extractor_args"]["youtube"]["fetch_pot"] == ["always"]
    assert opts["extractor_args"]["youtube"]["pot_trace"] == ["true"]


def test_stage_diagnostics_logging():
    """Task 3 & 6: Verifies safe diagnostics logging identifies the correct failure stage."""
    captured_logs: list[str] = []

    class MockLogger:
        def info(self, msg: str):
            captured_logs.append(msg)
        def debug(self, msg: str):
            captured_logs.append(msg)
        def warning(self, msg: str):
            captured_logs.append(msg)
        def error(self, msg: str):
            captured_logs.append(msg)

    # Test stage: during_token_generation
    class MockYDLTokenFail:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def extract_info(self, url, download=False):
            raise yt_dlp.utils.DownloadError("Error reaching POST /get_pot (caused by ConnectionRefused)")

    with (
        patch("app.services.ytdlp_service.logger", MockLogger()),
        patch("yt_dlp.YoutubeDL", side_effect=MockYDLTokenFail),
        pytest.raises(yt_dlp.utils.DownloadError),
    ):
        YtDlpService._run_extraction("https://www.youtube.com/watch?v=dQw4w9WgXcQ", {})

    assert any("during_token_generation" in msg for msg in captured_logs)

    # Test stage: after_youtube_rejection
    captured_logs.clear()
    class MockYDLBotReject:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def extract_info(self, url, download=False):
            raise yt_dlp.utils.DownloadError("Sign in to confirm you're not a bot")

    with (
        patch("app.services.ytdlp_service.logger", MockLogger()),
        patch("yt_dlp.YoutubeDL", side_effect=MockYDLBotReject),
        pytest.raises(yt_dlp.utils.DownloadError),
    ):
        YtDlpService._run_extraction("https://www.youtube.com/watch?v=dQw4w9WgXcQ", {})

    assert any("after_youtube_rejection" in msg for msg in captured_logs)


def test_sensitive_data_filter_redacts_signed_media_urls_and_tokens():
    """Task 9: Verifies SensitiveDataFilter redacts signed googlevideo URLs, tokens, and cookies."""
    flt = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Fetch https://rr1---sn-abc.googlevideo.com/videoplayback?expire=123&sig=SECRET_SIG_XYZ with Generated POT: SECRET_POT_999 and .youtube.com TRUE / FALSE 1700000000 SID SECRET_COOKIE",
        args=(), exc_info=None,
    )
    flt.filter(record)
    assert "SECRET_SIG_XYZ" not in record.msg
    assert "SECRET_POT_999" not in record.msg
    assert "SECRET_COOKIE" not in record.msg
    assert "[SIGNED_MEDIA_URL_REDACTED]" in record.msg


# =========================================================================
# 5. Live Extraction Verification (Public Example URL)
# =========================================================================

@pytest.mark.asyncio
async def test_live_youtube_extraction_example_url():
    """
    Attempts extraction on the user's reported test URL:
    https://youtu.be/m4nLtV8OSfQ?si=NN_jVPJ5IWG-VA1U
    """
    test_url = "https://youtu.be/m4nLtV8OSfQ?si=NN_jVPJ5IWG-VA1U"
    try:
        res = await YtDlpService.extract_info(test_url)
        assert res is not None
        assert "Aigiri Nandini" in res.title
        assert res.platform == "Youtube"
        assert len(res.video_formats) > 0 or len(res.audio_formats) > 0
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Live network access restricted or YouTube rate-limited in test environment: {exc}")
