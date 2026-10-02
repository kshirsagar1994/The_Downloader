import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.pot_provider_service import POTProviderService
from app.services.ytdlp_options import build_base_ydl_opts, get_youtube_fallback_clients


@pytest.mark.asyncio
async def test_youtube_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health/youtube")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "yt_dlp" in data
        assert "ffmpeg" in data
        assert "po_token_provider" in data
        assert "po_token_provider_available" in data
        assert "cookies_configured" in data
        assert data["yt_dlp"] is True
        # Ensure no secrets, raw tokens or credentials are in response
        assert "po_token" not in data  # No raw po_token value
        assert "cookie" not in data  # No raw cookies
        assert "authorization" not in data
        assert "password" not in data


@pytest.mark.asyncio
async def test_pot_provider_service_unconfigured():
    health = await POTProviderService.check_health()
    assert isinstance(health, dict)
    assert "available" in health


def test_ytdlp_options_builder():
    opts = build_base_ydl_opts()
    assert "extractor_args" in opts
    assert "youtube" in opts["extractor_args"]
    assert "player_client" in opts["extractor_args"]["youtube"]
    assert "android" in opts["extractor_args"]["youtube"]["player_client"]


def test_youtube_fallback_clients():
    fallbacks = get_youtube_fallback_clients()
    assert len(fallbacks) >= 5
    assert ["android"] in fallbacks
