import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.main import app

settings = get_settings()


@pytest.mark.asyncio
async def test_health_routes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # /api/health
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["api"] == "ok"
        assert data["yt_dlp"] == "ok"

        # /api/health/yt-dlp
        res_yt = await client.get("/api/health/yt-dlp")
        assert res_yt.status_code == 200
        assert res_yt.json()["status"] == "ok"

        # /api/health/ffmpeg
        res_ff = await client.get("/api/health/ffmpeg")
        assert res_ff.status_code == 200
        assert "status" in res_ff.json()


@pytest.mark.asyncio
async def test_extract_endpoint_ssrf_blocked():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/extract", json={"url": "http://127.0.0.1:8000/secret"})
        assert res.status_code == 403
        data = res.json()
        assert data["success"] is False
        assert data["error_code"] == "SSRF_BLOCKED"


@pytest.mark.asyncio
async def test_jobs_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create Job
        create_res = await client.post(
            "/api/jobs",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "media_type": "video",
                "format_id": "best",
            },
        )
        assert create_res.status_code == 200
        create_data = create_res.json()
        assert create_data["success"] is True
        job_id = create_data["job_id"]

        # Get Job Status
        status_res = await client.get(f"/api/jobs/{job_id}")
        assert status_res.status_code == 200
        assert status_res.json()["status"] in ("QUEUED", "ANALYZING", "DOWNLOADING", "COMPLETED", "FAILED")

        # Cancel Job
        cancel_res = await client.post(f"/api/jobs/{job_id}/cancel")
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_admin_metrics_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # No Token -> 401
        res_no_auth = await client.get("/api/admin/metrics")
        assert res_no_auth.status_code == 401

        # Invalid Token -> 403
        res_bad_auth = await client.get(
            "/api/admin/metrics", headers={"x-admin-token": "wrong-secret-token"}
        )
        assert res_bad_auth.status_code == 403

        # Valid Token -> 200
        res_ok = await client.get(
            "/api/admin/metrics", headers={"x-admin-token": settings.ADMIN_SECRET_KEY}
        )
        assert res_ok.status_code == 200
        data = res_ok.json()
        assert data["status"] == "online"
        assert "storage" in data
