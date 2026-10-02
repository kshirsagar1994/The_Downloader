import pytest

from app.services.format_service import FormatService
from app.services.metadata_service import MetadataService
from app.services.ytdlp_service import YtDlpService

SAMPLE_YTDLP_DUMP = {
    "id": "sample_123",
    "title": "Super Sample Video 4K",
    "thumbnail": "https://example.com/thumb.jpg",
    "duration": 245,
    "uploader": "Awesome Creator",
    "extractor_key": "Youtube",
    "description": "Test description",
    "formats": [
        {
            "format_id": "137",
            "vcodec": "avc1.640028",
            "acodec": "none",
            "width": 1920,
            "height": 1080,
            "ext": "mp4",
            "filesize": 52428800,
            "fps": 30,
        },
        {
            "format_id": "313",
            "vcodec": "vp9",
            "acodec": "none",
            "width": 3840,
            "height": 2160,
            "ext": "webm",
            "filesize": 157286400,
            "fps": 60,
        },
        {
            "format_id": "140",
            "vcodec": "none",
            "acodec": "mp4a.40.2",
            "ext": "m4a",
            "abr": 128,
            "filesize": 4194304,
        },
    ],
    "thumbnails": [
        {"url": "https://example.com/thumb_low.jpg", "width": 120, "height": 90},
        {"url": "https://example.com/thumb_max.jpg", "width": 1920, "height": 1080},
    ],
}


def test_format_service_parsing():
    videos, audios = FormatService.parse_formats(SAMPLE_YTDLP_DUMP)
    assert len(videos) >= 3  # Best Quality + 4K + 1080p
    assert videos[0].is_best is True
    assert "Best" in videos[0].label
    assert videos[1].quality == "2160p"
    assert videos[2].quality == "1080p"

    assert len(audios) >= 1
    assert audios[0].quality == "128k"


def test_metadata_service_parsing():
    result = MetadataService.parse_extraction_result(
        "https://example.com/watch?v=sample_123",
        SAMPLE_YTDLP_DUMP,
    )
    assert result.title == "Super Sample Video 4K"
    assert result.duration == 245
    assert result.uploader == "Awesome Creator"
    assert result.platform == "Youtube"
    assert len(result.video_formats) >= 3
    assert len(result.images) >= 2


def test_gallery_extraction():
    gallery_dump = {
        "_type": "multi_video",
        "title": "Post Images",
        "entries": [
            {"url": "https://example.com/1.jpg", "thumbnail": "https://example.com/1.jpg", "width": 1080, "height": 1080, "ext": "jpg"},
            {"url": "https://example.com/2.png", "thumbnail": "https://example.com/2.png", "width": 1920, "height": 1080, "ext": "png"},
        ],
    }
    result = MetadataService.parse_extraction_result("https://example.com/p/123", gallery_dump)
    assert result.type == "gallery"
    assert len(result.images) == 2
    assert result.images[0].format == "jpg"
    assert result.images[1].format == "png"


@pytest.mark.asyncio
async def test_ytdlp_service_ssrf_integration():
    with pytest.raises(Exception) as exc_info:
        await YtDlpService.extract_info("http://127.0.0.1:8000/private")
    assert "SSRF_BLOCKED" in str(exc_info.value) or "loopback" in str(exc_info.value)
