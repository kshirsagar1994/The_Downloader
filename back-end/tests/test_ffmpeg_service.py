import asyncio
import subprocess
from pathlib import Path

import pytest

from app.core.errors import ProcessingFailedError
from app.services.ffmpeg_service import FFmpegService


@pytest.fixture
def temp_media_dir(tmp_path: Path):
    media_dir = tmp_path / "test_ffmpeg_media"
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir


@pytest.mark.asyncio
async def test_ffmpeg_binary_availability():
    ffmpeg_path = FFmpegService.get_ffmpeg_path()
    assert Path(ffmpeg_path).exists() or ffmpeg_path == "ffmpeg"
    ffprobe_path = FFmpegService.get_ffprobe_path()
    assert Path(ffprobe_path).exists() or ffprobe_path == "ffprobe"


@pytest.mark.asyncio
async def test_ffmpeg_merge_and_probe(temp_media_dir: Path):
    ffmpeg = FFmpegService.get_ffmpeg_path()

    # Generate 1-second synthetic video stream (lavfi testsrc)
    video_path = temp_media_dir / "raw_video.mp4"
    await asyncio.to_thread(
        subprocess.run,
        [ffmpeg, "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30", "-c:v", "libx264", str(video_path)],
        check=True,
        capture_output=True,
    )

    # Generate 1-second synthetic audio stream (lavfi sine)
    audio_path = temp_media_dir / "raw_audio.m4a"
    await asyncio.to_thread(
        subprocess.run,
        [ffmpeg, "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1", "-c:a", "aac", str(audio_path)],
        check=True,
        capture_output=True,
    )

    # Test Merging
    merged_output = temp_media_dir / "merged_final.mp4"
    result_path = await FFmpegService.merge_video_audio(video_path, audio_path, merged_output)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    # Test Probing
    probe_info = await FFmpegService.probe_media(result_path)
    assert "streams" in probe_info
    stream_types = [s.get("codec_type") for s in probe_info["streams"]]
    assert "video" in stream_types
    assert "audio" in stream_types


@pytest.mark.asyncio
async def test_ffmpeg_audio_extraction(temp_media_dir: Path):
    ffmpeg = FFmpegService.get_ffmpeg_path()

    # Generate synthetic video with audio
    source_media = temp_media_dir / "source.mp4"
    await asyncio.to_thread(
        subprocess.run,
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264", "-c:a", "aac",
            str(source_media),
        ],
        check=True,
        capture_output=True,
    )

    # Extract MP3 (320k)
    mp3_output = temp_media_dir / "output.mp3"
    await FFmpegService.extract_audio(source_media, mp3_output, target_format="mp3", bitrate="320k")
    assert mp3_output.exists()
    assert mp3_output.stat().st_size > 0

    # Extract WAV (Lossless PCM)
    wav_output = temp_media_dir / "output.wav"
    await FFmpegService.extract_audio(source_media, wav_output, target_format="wav")
    assert wav_output.exists()
    assert wav_output.stat().st_size > 0


@pytest.mark.asyncio
async def test_ffmpeg_invalid_input_error(temp_media_dir: Path):
    non_existent = temp_media_dir / "missing.mp4"
    output = temp_media_dir / "wont_work.mp3"

    with pytest.raises(ProcessingFailedError):
        await FFmpegService.extract_audio(non_existent, output)
