from pathlib import Path
from unittest.mock import patch

import pytest

from app.schemas.job import JobProgressEvent
from app.services.video_service import VideoService


@pytest.fixture
def temp_job_dir(tmp_path: Path):
    job_dir = tmp_path / "test_video_job"
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


@pytest.mark.asyncio
async def test_video_download_progress_hook(temp_job_dir: Path):
    recorded_events: list[JobProgressEvent] = []

    def on_progress(event: JobProgressEvent):
        recorded_events.append(event)

    # Simulate fake output file created by yt-dlp
    fake_video = temp_job_dir / "Test_Video.mp4"
    fake_video.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1024)

    with patch.object(VideoService, "_run_ydl_download") as mock_ydl:
        def fake_download_trigger(url, opts):
            # Trigger progress hook manually to verify mapping
            hook = opts["progress_hooks"][0]
            hook({
                "status": "downloading",
                "downloaded_bytes": 5242880,
                "total_bytes": 10485760,
                "speed": 1048576.0,
                "eta": 5,
                "filename": str(fake_video),
            })
            # Trigger postprocessor hook
            pp_hook = opts["postprocessor_hooks"][0]
            pp_hook({
                "postprocessor": "Merger",
                "status": "started",
            })

        mock_ydl.side_effect = fake_download_trigger

        result_file = await VideoService.download_video(
            url="https://example.com/watch?v=123",
            job_dir=temp_job_dir,
            format_id="bestvideo+bestaudio/best",
            progress_callback=on_progress,
        )

        assert result_file.exists()
        assert result_file.name == "Test_Video.mp4"
        assert len(recorded_events) >= 2
        assert recorded_events[0].status == "DOWNLOADING"
        assert recorded_events[0].progress == 50.0
        assert recorded_events[0].speed == 1048576.0
        assert recorded_events[1].status == "PROCESSING"
