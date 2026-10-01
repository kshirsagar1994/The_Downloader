import asyncio
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from app.config import get_settings
from app.schemas.job import CreateJobRequest, JobProgressEvent
from app.services.queue_service import QueueService
from app.storage.cleanup import CleanupService
from app.workers.job_worker import JobWorker

settings = get_settings()


@pytest.fixture
def temp_storage(tmp_path: Path):
    storage = tmp_path / "test_ephemeral_storage"
    storage.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.mark.asyncio
async def test_queue_service_pubsub():
    qs = QueueService()
    job_id = "test-job-queue-1"

    ev1 = JobProgressEvent(
        job_id=job_id,
        status="QUEUED",
        progress=0.0,
    )
    await qs.save_job_state(ev1)

    state = await qs.get_job_state(job_id)
    assert state is not None
    assert state.status == "QUEUED"

    # Test subscription streaming
    events_received: list[JobProgressEvent] = []

    async def consume():
        async for e in qs.subscribe_events(job_id):
            events_received.append(e)
            if e.status == "COMPLETED":
                break

    consumer_task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)

    # Emit progress and completion
    ev2 = JobProgressEvent(job_id=job_id, status="DOWNLOADING", progress=50.0)
    await qs.save_job_state(ev2)

    ev3 = JobProgressEvent(job_id=job_id, status="COMPLETED", progress=100.0)
    await qs.save_job_state(ev3)

    await asyncio.wait_for(consumer_task, timeout=2.0)
    assert len(events_received) >= 2
    assert events_received[-1].status == "COMPLETED"


@pytest.mark.asyncio
async def test_job_worker_execution(temp_storage: Path):
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_storage):
        job_id = "worker-test-job-10"

        # Mock VideoService download to create fake video file
        async def fake_download(url, job_dir, format_id, progress_callback):
            out = job_dir / "Done_Video.mp4"
            out.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1024)
            return out

        with patch("app.services.video_service.VideoService.download_video", side_effect=fake_download):
            req = CreateJobRequest(
                url="https://example.com/watch?v=123",
                media_type="video",
                format_id="best",
            )

            await JobWorker.process_job(job_id, req)

            # Assert job state in queue is COMPLETED
            from app.services.queue_service import queue_service
            final_state = await queue_service.get_job_state(job_id)
            assert final_state is not None
            assert final_state.status == "COMPLETED"
            assert final_state.progress == 100.0
            assert final_state.filename == "Done_Video.mp4"


def test_cleanup_service_sweeper(temp_storage: Path):
    with patch("app.config.Settings.storage_path", new_callable=lambda: temp_storage):
        # Create 1 fresh directory and 1 expired directory
        fresh_dir = temp_storage / "fresh_job"
        fresh_dir.mkdir()
        (fresh_dir / "video.mp4").write_text("fresh")

        expired_dir = temp_storage / "expired_job"
        expired_dir.mkdir()
        (expired_dir / "video.mp4").write_text("expired")

        # Age the expired directory by setting its mtime to 2 hours ago
        past_time = time.time() - 7200
        os.utime(str(expired_dir), (past_time, past_time))

        evicted = CleanupService.sweep_expired_jobs()
        assert evicted >= 1
        assert not expired_dir.exists()
        assert fresh_dir.exists()
