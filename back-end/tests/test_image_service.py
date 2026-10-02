import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.media import MediaImageItem
from app.services.image_service import ImageService
from app.storage.workspace import WorkspaceManager


@pytest.fixture
def temp_job_dir(tmp_path: Path):
    job_dir = tmp_path / "test_job_workspace"
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def test_workspace_manager():
    jid, path = WorkspaceManager.create_job_workspace()
    assert path.exists()
    assert jid in str(path)

    # Test retrieval
    retrieved = WorkspaceManager.get_job_workspace(jid)
    assert retrieved == path

    # Test cleanup
    WorkspaceManager.cleanup_workspace(jid)
    assert not path.exists()


@pytest.mark.asyncio
async def test_image_gallery_zip_packaging(temp_job_dir: Path):
    images = [
        MediaImageItem(
            id="img_0",
            url="https://images.unsplash.com/photo-1.jpg",
            preview_url="https://images.unsplash.com/photo-1.jpg",
            title="Sunrise Landscape",
            format="jpg",
            index=0,
        ),
        MediaImageItem(
            id="img_1",
            url="https://images.unsplash.com/photo-2.png",
            preview_url="https://images.unsplash.com/photo-2.png",
            title="Mountain View",
            format="png",
            index=1,
        ),
    ]

    # Mock HTTP responses for the image downloads
    mock_resp_1 = AsyncMock()
    mock_resp_1.status_code = 200
    mock_resp_1.headers = {"content-type": "image/jpeg"}
    mock_resp_1.content = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # JPEG magic bytes

    mock_resp_2 = AsyncMock()
    mock_resp_2.status_code = 200
    mock_resp_2.headers = {"content-type": "image/png"}
    mock_resp_2.content = b"\x89PNG\r\n\x1a\n"  # PNG magic bytes

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = [mock_resp_1, mock_resp_2]

        zip_file = await ImageService.download_image_gallery(
            images=images,
            job_dir=temp_job_dir,
            zip_name="holiday_photos.zip",
        )

        assert zip_file.exists()
        assert zip_file.name == "holiday_photos.zip"

        # Inspect ZIP archive structure
        with zipfile.ZipFile(str(zip_file), "r") as archive:
            namelist = archive.namelist()
            assert len(namelist) == 2
            assert any("01-Sunrise_Landscape.jpg" in name for name in namelist)
            assert any("02-Mountain_View.png" in name for name in namelist)


@pytest.mark.asyncio
async def test_single_image_download(temp_job_dir: Path):
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "image/webp"}
    mock_resp.content = b"RIFF....WEBP"

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        img_path = await ImageService.download_single_image(
            url="https://example.com/art.webp",
            job_dir=temp_job_dir,
            custom_name="Digital Artwork",
        )

        assert img_path.exists()
        assert img_path.name == "Digital_Artwork.webp"
        assert img_path.read_bytes() == b"RIFF....WEBP"
