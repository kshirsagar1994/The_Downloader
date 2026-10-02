import datetime
from typing import Any

from app.schemas.media import ExtractionResult, MediaImageItem, PlaylistItem
from app.services.format_service import FormatService


class MetadataService:
    """Extracts structured metadata, thumbnails, images, and playlist entries."""

    @classmethod
    def parse_extraction_result(cls, url: str, raw_info: dict[str, Any]) -> ExtractionResult:
        is_playlist = "_type" in raw_info and raw_info["_type"] in ("playlist", "multi_video")

        title = raw_info.get("title") or "Untitled Media"
        thumbnail = raw_info.get("thumbnail") or ""
        duration = raw_info.get("duration")
        uploader = raw_info.get("uploader") or raw_info.get("channel") or raw_info.get("creator")
        platform = raw_info.get("extractor_key") or raw_info.get("extractor") or "Web"
        description = raw_info.get("description")

        # Parse Video & Audio formats
        video_formats, audio_formats = FormatService.parse_formats(raw_info)

        # Parse Images / Gallery
        images = cls.extract_images(raw_info)

        # Parse Playlist Items
        playlist_items = cls.extract_playlist_items(raw_info) if is_playlist else []

        # Determine primary media type
        media_type = "video"
        if images and not video_formats:
            media_type = "gallery" if len(images) > 1 else "image"
        elif is_playlist and playlist_items and not (images and len(images) == len(playlist_items)):
            media_type = "playlist"
        elif images and len(images) > 1:
            media_type = "gallery"
        elif audio_formats and not video_formats:
            media_type = "audio"

        return ExtractionResult(
            url=url,
            type=media_type,
            title=title,
            thumbnail=thumbnail,
            duration=int(duration) if duration else None,
            uploader=uploader,
            platform=platform,
            description=description,
            video_formats=video_formats,
            audio_formats=audio_formats,
            images=images,
            playlist_items=playlist_items,
            total_items=len(playlist_items) if is_playlist else None,
            created_at=datetime.datetime.now(datetime.UTC).isoformat(),
        )

    @classmethod
    def extract_images(cls, raw_info: dict[str, Any]) -> list[MediaImageItem]:
        images: list[MediaImageItem] = []
        seen_urls: set[str] = set()

        # Check gallery entries (e.g. Instagram carousel, Reddit gallery, Twitter multi-image)
        entries = raw_info.get("entries", [])
        if entries:
            for idx, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    continue
                img_url = entry.get("url") or entry.get("thumbnail")
                if img_url and img_url not in seen_urls:
                    seen_urls.add(img_url)
                    images.append(
                        MediaImageItem(
                            id=f"img_{idx}",
                            url=img_url,
                            preview_url=entry.get("thumbnail") or img_url,
                            title=entry.get("title") or f"Image #{idx + 1}",
                            width=entry.get("width"),
                            height=entry.get("height"),
                            format=entry.get("ext", "jpg"),
                            filesize=entry.get("filesize"),
                            index=idx,
                        )
                    )

        # Also extract discovered high-resolution thumbnails
        thumbnails = raw_info.get("thumbnails", [])
        if not images and thumbnails:
            # Pick distinct high quality thumbnails
            for idx, thumb in enumerate(thumbnails):
                if not isinstance(thumb, dict):
                    continue
                thumb_url = thumb.get("url")
                if thumb_url and thumb_url not in seen_urls:
                    seen_urls.add(thumb_url)
                    images.append(
                        MediaImageItem(
                            id=f"thumb_{idx}",
                            url=thumb_url,
                            preview_url=thumb_url,
                            title=f"Thumbnail #{idx + 1}",
                            width=thumb.get("width"),
                            height=thumb.get("height"),
                            format="jpg",
                            filesize=thumb.get("filesize"),
                            index=idx,
                        )
                    )

        return images

    @classmethod
    def extract_playlist_items(cls, raw_info: dict[str, Any]) -> list[PlaylistItem]:
        playlist_items: list[PlaylistItem] = []
        entries = raw_info.get("entries", [])

        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            playlist_items.append(
                PlaylistItem(
                    id=str(entry.get("id", f"item_{idx}")),
                    url=entry.get("url") or entry.get("webpage_url") or "",
                    title=entry.get("title") or f"Item #{idx + 1}",
                    thumbnail=entry.get("thumbnail"),
                    duration=int(entry.get("duration")) if entry.get("duration") else None,
                    uploader=entry.get("uploader") or entry.get("channel"),
                    index=idx,
                )
            )

        return playlist_items
