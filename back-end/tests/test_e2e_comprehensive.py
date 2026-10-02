import asyncio
import os
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.core.rate_limit import limiter
from app.main import app
from app.schemas.media import MediaImageItem
from app.services.audio_service import AudioService
from app.services.image_service import ImageService
from app.services.playlist_service import PlaylistService
from app.services.video_service import VideoService
from app.services.ytdlp_service import YtDlpService
from app.storage.cleanup import CleanupService

settings = get_settings()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limiter tracking between tests."""
    limiter._requests.clear()
    yield
    limiter._requests.clear()


@pytest.fixture
def temp_workspace(tmp_path: Path):
    ws = tmp_path / "e2e_workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


async def poll_until_job_status(
    client: AsyncClient, job_id: str, target_statuses=("COMPLETED", "FAILED", "CANCELLED"), timeout: float = 3.0
) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        res = await client.get(f"/api/jobs/{job_id}")
        if res.status_code == 200:
            data = res.json()
            if data.get("status") in target_statuses:
                return data
        await asyncio.sleep(0.05)
    res = await client.get(f"/api/jobs/{job_id}")
    return res.json() if res.status_code == 200 else {}


# =========================================================================
# COMPREHENSIVE END-TO-END TEST SUITE
# =========================================================================

@pytest.mark.asyncio
async def test_e2e_valid_video_pipeline(temp_workspace: Path):
    """Test 1: Valid Video URL Extraction -> Job Queue -> Merged MP4 Delivery."""
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_workspace):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async def fake_video_dl(url, job_dir, format_id, progress_callback):
                out = job_dir / "Test_E2E_Video.mp4"
                out.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"VIDEO_DATA" * 50)
                return out

            with patch.object(VideoService, "download_video", side_effect=fake_video_dl):
                create_res = await client.post(
                    "/api/jobs",
                    json={
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "media_type": "video",
                        "format_id": "bestvideo+bestaudio/best",
                    },
                )
                assert create_res.status_code == 200
                job_id = create_res.json()["job_id"]

                status_data = await poll_until_job_status(client, job_id, ("COMPLETED",))
                assert status_data.get("status") == "COMPLETED"

                # 3. File Download
                dl_res = await client.get(f"/api/download/{job_id}")
                assert dl_res.status_code == 200
                assert dl_res.headers["content-type"] == "video/mp4"
                assert "Test_E2E_Video.mp4" in dl_res.headers["content-disposition"]


@pytest.mark.asyncio
async def test_e2e_audio_transcode_pipeline(temp_workspace: Path):
    """Test 2: Audio Extraction & 320kbps MP3 Transcode."""
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_workspace):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async def fake_audio_dl(url, job_dir, target_format, bitrate, progress_callback):
                out = job_dir / f"Extracted_Audio.{target_format}"
                out.write_bytes(b"ID3\x03\x00\x00\x00" + b"MP3_STREAM" * 50)
                return out

            with patch.object(AudioService, "download_audio", side_effect=fake_audio_dl):
                create_res = await client.post(
                    "/api/jobs",
                    json={
                        "url": "https://soundcloud.com/artist/track",
                        "media_type": "audio",
                        "audio_bitrate": "320k",
                        "target_extension": "mp3",
                    },
                )
                assert create_res.status_code == 200
                job_id = create_res.json()["job_id"]

                status_data = await poll_until_job_status(client, job_id, ("COMPLETED",))
                assert status_data.get("status") == "COMPLETED"

                dl_res = await client.get(f"/api/download/{job_id}")
                assert dl_res.status_code == 200
                assert dl_res.headers["content-type"] == "audio/mpeg"


@pytest.mark.asyncio
async def test_e2e_gallery_zip_download(temp_workspace: Path):
    """Test 3: Multi-image Gallery Extraction & ZIP Bundling."""
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_workspace):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async def fake_gallery_dl(images, job_dir, zip_name, selected_indices):
                out = job_dir / zip_name
                out.write_bytes(b"PK\x03\x04" + b"ZIP_CONTENTS" * 20)
                return out

            meta_mock = AsyncMock()
            meta_mock.images = [
                MediaImageItem(id="1", url="https://example.com/1.jpg", preview_url="", index=0),
                MediaImageItem(id="2", url="https://example.com/2.jpg", preview_url="", index=1),
            ]
            meta_mock.title = "Vacation_Gallery"

            with (
                patch.object(ImageService, "download_image_gallery", side_effect=fake_gallery_dl),
                patch.object(YtDlpService, "extract_info", return_value=meta_mock),
            ):
                create_res = await client.post(
                    "/api/jobs",
                    json={
                        "url": "https://instagram.com/p/sample123",
                        "media_type": "gallery",
                        "selected_image_indices": [0, 1],
                    },
                )
                assert create_res.status_code == 200
                job_id = create_res.json()["job_id"]

                status_data = await poll_until_job_status(client, job_id, ("COMPLETED",))
                assert status_data.get("status") == "COMPLETED"

                dl_res = await client.get(f"/api/download/{job_id}")
                assert dl_res.status_code == 200
                assert dl_res.headers["content-type"] == "application/zip"
                assert "Vacation_Gallery.zip" in dl_res.headers["content-disposition"]


@pytest.mark.asyncio
async def test_e2e_playlist_batch_download(temp_workspace: Path):
    """Test 4: Playlist Multi-Item Batch Download."""
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_workspace):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async def fake_playlist_dl(url, job_dir, selected_indices, format_id, progress_callback):
                out = job_dir / "playlist_bundle.zip"
                out.write_bytes(b"PK\x03\x04" + b"PLAYLIST_ZIP" * 20)
                return out

            with patch.object(PlaylistService, "download_playlist", side_effect=fake_playlist_dl):
                create_res = await client.post(
                    "/api/jobs",
                    json={
                        "url": "https://youtube.com/playlist?list=PL12345",
                        "media_type": "playlist",
                        "selected_playlist_indices": [0, 1, 2],
                    },
                )
                assert create_res.status_code == 200
                job_id = create_res.json()["job_id"]

                status_data = await poll_until_job_status(client, job_id, ("COMPLETED",))
                assert status_data.get("status") == "COMPLETED"

                dl_res = await client.get(f"/api/download/{job_id}")
                assert dl_res.status_code == 200
                assert dl_res.headers["content-type"] == "application/zip"


@pytest.mark.asyncio
async def test_e2e_job_cancellation():
    """Test 5: Download Cancellation flow."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Prevent background task from racing/failing immediately by delaying it
        async def slow_video_dl(*args, **kwargs):
            await asyncio.sleep(2.0)

        with patch.object(VideoService, "download_video", side_effect=slow_video_dl):
            create_res = await client.post(
                "/api/jobs",
                json={"url": "https://example.com/long_video", "media_type": "video"},
            )
            job_id = create_res.json()["job_id"]

            cancel_res = await client.post(f"/api/jobs/{job_id}/cancel")
            assert cancel_res.status_code == 200
            assert cancel_res.json()["status"] == "CANCELLED"

            status_res = await client.get(f"/api/jobs/{job_id}")
            assert status_res.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_e2e_storage_sweeper_eviction(temp_workspace: Path):
    """Test 6: Storage Sweeper and Job Expiration."""
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_workspace):
        expired_job = temp_workspace / "old_job_uuid"
        expired_job.mkdir(parents=True, exist_ok=True)
        (expired_job / "file.mp4").write_text("old data")

        # Age the directory
        past = time.time() - 4000
        os.utime(str(expired_job), (past, past))

        evicted = CleanupService.sweep_expired_jobs()
        assert evicted >= 1
        assert not expired_job.exists()


@pytest.mark.asyncio
async def test_e2e_ssrf_malicious_subnets():
    """Test 7: Complete SSRF Defense."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        malicious_urls = [
            "http://127.0.0.1:8000/admin",
            "http://169.254.169.254/metadata",
            "http://10.0.0.1/",
            "http://192.168.1.1/",
            "file:///etc/passwd",
        ]
        for bad_url in malicious_urls:
            res = await client.post("/api/extract", json={"url": bad_url})
            assert res.status_code == 403
            assert res.json()["error_code"] == "SSRF_BLOCKED"


@pytest.mark.asyncio
async def test_e2e_rate_limiting_enforcement():
    """Test 8: Rate Limiting Throttling."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Rapidly exhaust rate limit on /api/jobs (10/min)
        async def dummy_video_dl(*args, **kwargs):
            return Path("dummy.mp4")

        with patch.object(VideoService, "download_video", side_effect=dummy_video_dl):
            for i in range(10):
                res = await client.post(
                    "/api/jobs",
                    json={"url": f"https://example.com/video_{i}", "media_type": "video"},
                )
                assert res.status_code == 200

            # 11th request must be rejected with 429
            blocked_res = await client.post(
                "/api/jobs",
                json={"url": "https://example.com/video_excess", "media_type": "video"},
            )
            assert blocked_res.status_code == 429
            assert blocked_res.json()["error_code"] == "RATE_LIMITED"
