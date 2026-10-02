import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "version" in data


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["api"] == "ok"
        assert data["yt_dlp"] == "ok"


def test_ytdlp_import_and_version():
    import yt_dlp.version
    assert hasattr(yt_dlp.version, "__version__")
    assert yt_dlp.version.__version__ is not None
    print(f"Verified yt-dlp version: {yt_dlp.version.__version__}")


def test_settings_storage_path():
    settings = get_settings()
    assert settings.storage_path.exists()
