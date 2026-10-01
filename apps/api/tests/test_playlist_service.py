import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.schemas.job import JobProgressEvent
from app.services.playlist_service import PlaylistService


@pytest.fixture
def temp_job_dir(tmp_path: Path):
    job_dir = tmp_path / "test_playlist_job"
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


@pytest.mark.asyncio
async def test_playlist_multi_item_zip_bundling(temp_job_dir: Path):
    recorded_events: list[JobProgressEvent] = []

    def on_progress(event: JobProgressEvent):
        recorded_events.append(event)

    # Create two fake items that yt-dlp simulated downloading
    item1 = temp_job_dir / "01-Video_Alpha.mp4"
    item1.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 1024)
    item2 = temp_job_dir / "02-Video_Beta.mp4"
    item2.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 2048)

    with patch.object(PlaylistService, "_run_ydl_download") as mock_ydl:
        def fake_download(url, opts):
            # Verify playlist_items was properly formatted (1-indexed)
            assert opts["playlist_items"] == "1,2"
            # Trigger progress hook
            opts["progress_hooks"][0]({
                "status": "downloading",
                "downloaded_bytes": 1024,
                "total_bytes": 1024,
                "speed": 1000.0,
                "eta": 0,
                "filename": str(item1),
            })

        mock_ydl.side_effect = fake_download

        result_path = await PlaylistService.download_playlist(
            url="https://example.com/playlist?list=PL123",
            job_dir=temp_job_dir,
            selected_indices=[0, 1],
            progress_callback=on_progress,
        )

        assert result_path.exists()
        assert result_path.name == "playlist_bundle.zip"

        with zipfile.ZipFile(str(result_path), "r") as archive:
            namelist = archive.namelist()
            assert len(namelist) == 2
            assert "01-Video_Alpha.mp4" in namelist
            assert "02-Video_Beta.mp4" in namelist


@pytest.mark.asyncio
async def test_playlist_single_item_direct_file(temp_job_dir: Path):
    # Single item downloaded should return direct file rather than zip
    single_item = temp_job_dir / "01-Solo_Video.mp4"
    single_item.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 512)

    with patch.object(PlaylistService, "_run_ydl_download"):
        result_path = await PlaylistService.download_playlist(
            url="https://example.com/playlist?list=PL123",
            job_dir=temp_job_dir,
            selected_indices=[0],
        )

        assert result_path.exists()
        assert result_path.name == "01-Solo_Video.mp4"
