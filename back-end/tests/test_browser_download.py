from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app

settings = get_settings()


@pytest.fixture
def temp_job_storage(tmp_path: Path):
    storage = tmp_path / "browser_download_storage"
    storage.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.mark.asyncio
async def test_download_endpoint_mp4(temp_job_storage: Path):
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_job_storage):
        job_id = "job_mp4_test_01"
        job_dir = temp_job_storage / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        video_file = job_dir / "Amazing_4K_Video.mp4"
        sample_data = b"\x00\x00\x00\x18ftypmp42" + b"VIDEO_BYTES_HERE" * 100
        video_file.write_bytes(sample_data)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(f"/api/download/{job_id}")
            assert res.status_code == 200
            assert res.headers["content-type"] == "video/mp4"
            assert res.headers["content-length"] == str(len(sample_data))
            assert "Amazing_4K_Video.mp4" in res.headers["content-disposition"]
            assert "attachment;" in res.headers["content-disposition"]
            assert res.headers["x-content-type-options"] == "nosniff"

            # Assert no internal filesystem path leakage
            assert "file:///" not in res.headers["content-disposition"]
            assert str(temp_job_storage) not in res.headers["content-disposition"]
            assert res.content == sample_data


@pytest.mark.asyncio
async def test_download_endpoint_zip_archive(temp_job_storage: Path):
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_job_storage):
        job_id = "job_zip_test_02"
        job_dir = temp_job_storage / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        zip_file = job_dir / "Gallery_Photos.zip"
        sample_zip = b"PK\x03\x04" + b"ZIP_PAYLOAD" * 50
        zip_file.write_bytes(sample_zip)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(f"/api/download/{job_id}")
            assert res.status_code == 200
            assert res.headers["content-type"] == "application/zip"
            assert "Gallery_Photos.zip" in res.headers["content-disposition"]
            assert res.content == sample_zip


@pytest.mark.asyncio
async def test_download_endpoint_utf8_filename(temp_job_storage: Path):
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_job_storage):
        job_id = "job_utf8_test_03"
        job_dir = temp_job_storage / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        special_file = job_dir / "Musica_Espanola_2026.mp3"
        special_file.write_bytes(b"ID3" + b"AUDIO_DATA" * 50)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(f"/api/download/{job_id}")
            assert res.status_code == 200
            assert res.headers["content-type"] == "audio/mpeg"
            assert "filename*=UTF-8''" in res.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_endpoint_missing_job_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/download/non-existent-uuid-job")
        assert res.status_code == 404
        assert res.json()["success"] is False
        assert res.json()["error_code"] == "JOB_NOT_FOUND"
