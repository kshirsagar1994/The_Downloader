from pathlib import Path
from unittest.mock import patch

import pytest

from app.schemas.job import JobProgressEvent
from app.services.audio_service import AudioService


@pytest.fixture
def temp_job_dir(tmp_path: Path):
    job_dir = tmp_path / "test_audio_job"
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


@pytest.mark.asyncio
async def test_audio_download_progress_hook(temp_job_dir: Path):
    recorded_events: list[JobProgressEvent] = []

    def on_progress(event: JobProgressEvent):
        recorded_events.append(event)

    # Simulate fake output file created by yt-dlp
    fake_audio = temp_job_dir / "Test_Audio.mp3"
    fake_audio.write_bytes(b"ID3\x03\x00\x00\x00" + b"\x00" * 1024)

    with patch.object(AudioService, "_run_ydl_download") as mock_ydl:
        def fake_download_trigger(url, opts):
            # Trigger progress hook manually
            hook = opts["progress_hooks"][0]
            hook({
                "status": "downloading",
                "downloaded_bytes": 1048576,
                "total_bytes": 2097152,
                "speed": 524288.0,
                "eta": 2,
                "filename": str(fake_audio),
            })
            # Trigger postprocessor hook
            pp_hook = opts["postprocessor_hooks"][0]
            pp_hook({
                "postprocessor": "FFmpegExtractAudio",
                "status": "started",
            })

        mock_ydl.side_effect = fake_download_trigger

        result_file = await AudioService.download_audio(
            url="https://example.com/watch?v=audio123",
            job_dir=temp_job_dir,
            target_format="mp3",
            bitrate="320k",
            progress_callback=on_progress,
        )

        assert result_file.exists()
        assert result_file.name == "Test_Audio.mp3"
        assert len(recorded_events) >= 2
        assert recorded_events[0].status == "DOWNLOADING"
        assert recorded_events[0].progress == 45.0
        assert recorded_events[1].status == "PROCESSING"
