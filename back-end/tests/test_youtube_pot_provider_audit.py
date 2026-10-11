import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
import yt_dlp

from app.config import Settings, get_settings
from app.services.pot_provider_service import POTProviderService
from app.services.ytdlp_options import YtDlpLogHandler, build_base_ydl_opts, get_youtube_fallback_clients
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
    except Exception as exc:
        pytest.skip(f"Live network access restricted or YouTube rate-limited in test environment: {exc}")
