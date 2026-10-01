import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.core.errors import ProcessingFailedError
from app.core.logging import logger

settings = get_settings()


class FFmpegService:
    """Encapsulated FFmpeg and FFprobe media processing engine."""

    @classmethod
    def get_ffmpeg_path(cls) -> str:
        path = shutil.which(settings.FFMPEG_PATH)
        if not path:
            raise ProcessingFailedError(
                "FFmpeg executable not found. Please verify FFmpeg is installed and in PATH."
            )
        return path

    @classmethod
    def get_ffprobe_path(cls) -> str:
        path = shutil.which(settings.FFPROBE_PATH)
        if not path:
            raise ProcessingFailedError(
                "FFprobe executable not found. Please verify FFprobe is installed and in PATH."
            )
        return path

    @classmethod
    async def merge_video_audio(
        cls,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Losslessly multiplexes separate video and audio streams into a container.
        Uses stream copy (-c copy) when compatible to preserve maximum quality.
        """
        ffmpeg = cls.get_ffmpeg_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            ffmpeg,
            "-y",  # Overwrite output without prompting
            "-i", str(video_path.resolve()),
            "-i", str(audio_path.resolve()),
            "-c:v", "copy",
            "-c:a", "aac",  # Transcode audio to aac if needed for MP4 container compatibility
            "-movflags", "+faststart",  # Optimize for web streaming
            str(output_path.resolve()),
        ]

        logger.info(f"Merging video and audio: {video_path.name} + {audio_path.name} -> {output_path.name}")
        await cls._execute_ffmpeg_cmd(cmd)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ProcessingFailedError(f"Failed to produce merged output file at {output_path.name}")

        return output_path

    @classmethod
    async def extract_audio(
        cls,
        input_path: Path,
        output_path: Path,
        target_format: str = "mp3",
        bitrate: str = "320k",
    ) -> Path:
        """
        Extracts and converts audio stream to target format (MP3, M4A, Opus, WAV) with specified bitrate.
        """
        ffmpeg = cls.get_ffmpeg_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd: list[str] = [
            ffmpeg,
            "-y",
            "-i", str(input_path.resolve()),
            "-vn",  # Strip video
        ]

        # Configure codecs and bitrates per format
        fmt = target_format.lower().strip(".")
        if fmt == "mp3":
            cmd.extend(["-c:a", "libmp3lame", "-b:a", bitrate])
        elif fmt == "m4a":
            cmd.extend(["-c:a", "aac", "-b:a", bitrate])
        elif fmt == "opus":
            cmd.extend(["-c:a", "libopus", "-b:a", bitrate])
        elif fmt == "wav":
            cmd.extend(["-c:a", "pcm_s16le"])  # Lossless 16-bit PCM
        else:
            cmd.extend(["-c:a", "libmp3lame", "-b:a", "320k"])

        cmd.append(str(output_path.resolve()))

        logger.info(f"Extracting audio ({fmt} @ {bitrate}): {input_path.name} -> {output_path.name}")
        await cls._execute_ffmpeg_cmd(cmd)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ProcessingFailedError(f"Failed to produce audio output file at {output_path.name}")

        return output_path

    @classmethod
    async def convert_video(
        cls,
        input_path: Path,
        output_path: Path,
        target_format: str = "mp4",
    ) -> Path:
        """Converts video to standard MP4 container."""
        ffmpeg = cls.get_ffmpeg_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            ffmpeg,
            "-y",
            "-i", str(input_path.resolve()),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path.resolve()),
        ]

        logger.info(f"Converting video to {target_format}: {input_path.name} -> {output_path.name}")
        await cls._execute_ffmpeg_cmd(cmd)

        return output_path

    @classmethod
    async def probe_media(cls, file_path: Path) -> dict[str, Any]:
        """Probes media file metadata, streams, resolution, and codecs via FFprobe."""
        ffprobe = cls.get_ffprobe_path()

        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path.resolve()),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode("utf-8", "ignore")
            raise ProcessingFailedError(f"FFprobe failed for {file_path.name}: {err}")

        try:
            return json.loads(stdout.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ProcessingFailedError(f"Failed to parse FFprobe JSON output: {exc}") from exc

    @classmethod
    async def _execute_ffmpeg_cmd(cls, cmd: list[str]) -> None:
        """Safe non-blocking subprocess runner with timeout and stderr diagnostic collection."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait with a timeout of 10 minutes for heavy transcode
            _stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)

            if proc.returncode != 0:
                err_text = stderr.decode("utf-8", "ignore")
                logger.error(f"FFmpeg execution failed (code {proc.returncode}): {err_text}")
                raise ProcessingFailedError(
                    f"FFmpeg processing failed with exit code {proc.returncode}: {err_text[-300:]}"
                )

        except TimeoutError as exc:
            logger.error("FFmpeg execution timed out.")
            raise ProcessingFailedError("FFmpeg transcode operation timed out.") from exc
        except Exception as exc:
            logger.error(f"FFmpeg subprocess error: {exc}")
            raise ProcessingFailedError(f"FFmpeg error: {exc}") from exc
