from typing import Any, ClassVar

from app.schemas.media import MediaFormatOption


class FormatService:
    """Parses and normalizes raw yt-dlp format streams into user-friendly options."""

    QUALITY_RANKS: ClassVar[dict[str, int]] = {
        "4320p": 8000,
        "8k": 8000,
        "2160p": 4000,
        "4k": 4000,
        "1440p": 2500,
        "2k": 2500,
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
        "240p": 240,
        "144p": 144,
    }

    @classmethod
    def parse_formats(cls, raw_info: dict[str, Any]) -> tuple[list[MediaFormatOption], list[MediaFormatOption]]:
        raw_formats = raw_info.get("formats", [])
        if not raw_formats:
            # If no format array (e.g. multi-entry gallery/playlist without top formats), check if direct video exists
            if raw_info.get("url") and not raw_info.get("entries"):
                single_fmt = cls._construct_single_fallback_format(raw_info)
                if single_fmt:
                    return [single_fmt], []
            return [], []

        video_formats: list[MediaFormatOption] = []
        audio_formats: list[MediaFormatOption] = []

        seen_video_heights: set[int] = set()

        # Add predefined "Best Quality" merged option
        video_formats.append(
            MediaFormatOption(
                format_id="bestvideo+bestaudio/best",
                label="Best Available Quality (Auto-Merge)",
                extension="mp4",
                quality="Best",
                resolution="Up to 4K / Max",
                has_video=True,
                has_audio=True,
                is_best=True,
            )
        )

        # Iterate over raw formats
        for f in raw_formats:
            if not isinstance(f, dict):
                continue

            format_id = str(f.get("format_id", ""))
            vcodec = f.get("vcodec")
            acodec = f.get("acodec")
            height = f.get("height")
            width = f.get("width")
            ext = f.get("ext", "mp4")
            filesize = f.get("filesize") or f.get("filesize_approx")
            raw_fps = f.get("fps")
            fps = int(round(raw_fps)) if isinstance(raw_fps, (int, float)) and raw_fps > 0 else None

            # Direct streaming URLs for client-side download
            direct_url = f.get("url")
            manifest_url = f.get("manifest_url")
            protocol = f.get("protocol")

            has_video = vcodec not in (None, "none")
            has_audio = acodec not in (None, "none")

            # Video streams
            if has_video and height:
                if height not in seen_video_heights:
                    seen_video_heights.add(height)
                    label = f"{height}p"
                    if height >= 2160:
                        label = "4K Ultra HD (2160p)"
                    elif height >= 1440:
                        label = "2K Quad HD (1440p)"
                    elif height >= 1080:
                        label = "1080p Full HD"
                    elif height >= 720:
                        label = "720p HD"
                    elif height >= 480:
                        label = "480p Standard"
                    elif height >= 360:
                        label = "360p Medium"

                    # For adaptive formats, we need separate video+audio URLs
                    # yt-dlp provides these in the format dict
                    video_only = has_video and not has_audio
                    audio_only = has_audio and not has_video

                    video_formats.append(
                        MediaFormatOption(
                            format_id=f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/{format_id}",
                            label=label,
                            extension="mp4",
                            quality=f"{height}p",
                            resolution=f"{width}x{height}" if width and height else f"{height}p",
                            filesize_approx=filesize,
                            has_video=True,
                            has_audio=True,
                            vcodec=str(vcodec) if vcodec else None,
                            acodec=str(acodec) if acodec else None,
                            fps=fps,
                            url=direct_url if not video_only else None,  # Progressive (has both)
                            video_url=direct_url if video_only else None,  # Video-only adaptive
                            audio_url=None,  # Will be paired with best audio
                            manifest_url=manifest_url,
                            protocol=protocol,
                        )
                    )

            # Audio-only streams
            elif has_audio and not has_video:
                abr = f.get("abr") or f.get("tbr")
                label = f"{int(abr)} kbps" if abr else "Audio Stream"
                audio_formats.append(
                    MediaFormatOption(
                        format_id=format_id,
                        label=label,
                        extension=ext if ext in ("m4a", "mp3", "opus", "webm") else "m4a",
                        quality=f"{int(abr)}k" if abr else "standard",
                        filesize_approx=filesize,
                        has_video=False,
                        has_audio=True,
                        acodec=str(acodec) if acodec else None,
                        url=direct_url,  # Progressive audio URL
                        manifest_url=manifest_url,
                        protocol=protocol,
                    )
                )

        # Sort video formats by resolution descending (keep Best Quality at top)
        best_opt = video_formats[0]
        other_videos = sorted(
            video_formats[1:],
            key=lambda x: int(x.quality.rstrip("p")) if x.quality and x.quality.rstrip("p").isdigit() else 0,
            reverse=True,
        )

        return [best_opt] + other_videos, audio_formats

    @classmethod
    def _construct_single_fallback_format(cls, raw_info: dict[str, Any]) -> MediaFormatOption | None:
        ext = raw_info.get("ext", "mp4")
        direct_url = raw_info.get("url")
        return MediaFormatOption(
            format_id="best",
            label="Direct Media Stream",
            extension=ext,
            quality="Direct",
            has_video=True,
            has_audio=True,
            is_best=True,
            url=direct_url,
        )
