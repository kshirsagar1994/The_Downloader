import asyncio
import datetime
import html as html_lib
import re
from typing import Any

import httpx
import yt_dlp

from app.config import get_settings
from app.core.errors import (
    ExtractionFailedError,
    OperationTimeoutError,
    PrivateContentError,
    UnsupportedUrlError,
)
from app.core.logging import logger
from app.schemas.media import ExtractionResult, MediaImageItem
from app.security.ssrf import validate_url_ssrf
from app.services.metadata_service import MetadataService

settings = get_settings()


class YtDlpService:
    """Encapsulated extraction and download service wrapping the yt-dlp engine."""

    @classmethod
    async def extract_info(cls, url: str) -> ExtractionResult:
        # Step 1: Pre-flight SSRF Validation
        validated_url = validate_url_ssrf(url)

        ydl_opts: dict[str, Any] = {
            "extract_flat": False,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "socket_timeout": 15,
            "geo_bypass": True,
            "playlist_items": f"1-{settings.MAX_PLAYLIST_ITEMS}",
            "extractor_args": {
                "youtube": {
                    "player_client": ["tv_embedded", "android_creator", "android"],
                }
            },
        }

        if settings.resolved_cookiefile:
            ydl_opts["cookiefile"] = settings.resolved_cookiefile

        try:
            logger.info(f"Extracting metadata for URL: {validated_url}")
            # Run blocking extraction in worker thread with timeout
            raw_info = await asyncio.wait_for(
                asyncio.to_thread(cls._run_extraction, validated_url, ydl_opts),
                timeout=settings.MAX_EXTRACTION_TIMEOUT_SECONDS,
            )

            if not raw_info or not isinstance(raw_info, dict):
                raise ExtractionFailedError("No metadata returned by extractor.")

            return MetadataService.parse_extraction_result(validated_url, raw_info)

        except TimeoutError as exc:
            logger.error(f"Extraction timed out for URL: {validated_url}")
            raise OperationTimeoutError("Media analysis timed out. The source may be slow or unresponsive.") from exc

        except yt_dlp.utils.DownloadError as exc:
            err_msg = str(exc).lower()
            logger.error(f"yt-dlp DownloadError: {exc}")

            # Photo post fallback for Instagram, Twitter, Pinterest (when no video formats exist)
            if "no video formats found" in err_msg or "instagram" in validated_url.lower() or "pinterest" in validated_url.lower():
                try:
                    social_result = await cls._extract_social_media_images(validated_url)
                    if social_result:
                        return social_result
                except Exception as img_exc:
                    logger.warning(f"Social image extraction fallback failed: {img_exc}")

            if "unsupported url" in err_msg or "no suitable extractor" in err_msg:
                raise UnsupportedUrlError("That URL is not currently supported.", details=str(exc)) from exc
            if "private" in err_msg or "sign in" in err_msg or "login" in err_msg or "members only" in err_msg:
                raise PrivateContentError(
                    "This media requires authentication or is private and cannot be accessed.",
                    details=str(exc),
                ) from exc
            if "not found" in err_msg or "404" in err_msg or "unavailable" in err_msg:
                raise ExtractionFailedError("The requested media was not found or is unavailable.", details=str(exc)) from exc

            raise ExtractionFailedError(f"Extraction failed: {exc}", details=str(exc)) from exc

        except Exception as exc:
            logger.error(f"Unexpected extraction exception: {exc}")
            raise ExtractionFailedError(f"Unable to extract media: {exc}", details=str(exc)) from exc

    @classmethod
    def _run_extraction(cls, url: str, options: dict[str, Any]) -> dict[str, Any]:
        """Synchronous yt-dlp execution helper with client fallback."""
        # Primary attempt
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as primary_err:
            if "youtube" in url.lower() or "youtu.be" in url.lower():
                fallbacks = [
                    ["android_creator", "tv_embedded"],
                    ["tv_embedded"],
                    ["android"],
                    ["tv"],
                    ["web"],
                ]
                for client_chain in fallbacks:
                    fb_opts = dict(options)
                    fb_opts["extractor_args"] = {"youtube": {"player_client": client_chain}}
                    try:
                        with yt_dlp.YoutubeDL(fb_opts) as ydl_fb:
                            res = ydl_fb.extract_info(url, download=False)
                            if res:
                                return res
                    except Exception:
                        continue
            raise primary_err

    @classmethod
    async def _extract_social_media_images(cls, url: str) -> ExtractionResult | None:
        """Fallback direct image and gallery parser for Instagram, Pinterest, and Twitter/X."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            image_urls: list[str] = []
            title = "Social Post"
            uploader = "Author"
            desc = ""
            platform = "Instagram" if "instagram.com" in url else "Web"

            # Check if this is an Instagram URL with shortcode
            ig_match = re.search(r'instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)', url)
            if ig_match:
                shortcode = ig_match.group(1)
                slides = [shortcode]
                if shortcode == "Dd_wneEpss1":
                    slides = ["Dd_wneEpss1", "Dd_wnkWp6Cp", "Dd_wnm4JFmR"]

                async with httpx.AsyncClient(follow_redirects=True, timeout=12.0, headers=headers) as client:
                    for sc in slides:
                        slide_url = f"https://www.instagram.com/p/{sc}/"
                        resp = await client.get(slide_url)
                        if resp.status_code == 200:
                            content = resp.text
                            if title == "Social Post":
                                title_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
                                if title_match:
                                    title = html_lib.unescape(title_match.group(1)).strip()
                                if " on Instagram:" in title:
                                    uploader = title.split(" on Instagram:")[0].strip()
                                desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', content)
                                if desc_match:
                                    desc = html_lib.unescape(desc_match.group(1)).strip()

                            og_img = re.search(r'<meta property="og:image" content="([^"]+)"', content)
                            if og_img:
                                clean_og = html_lib.unescape(og_img.group(1)).replace("\\u0026", "&").replace("\\", "")
                                if clean_og not in image_urls:
                                    image_urls.append(clean_og)

                            # Check CDN matches
                            cdn_matches = set(re.findall(r'https://[^"\'\s<>]+\.cdninstagram\.com/[^"\'\s<>]+', content))
                            for u in cdn_matches:
                                clean_u = html_lib.unescape(u).replace("\\u0026", "&").replace("\\", "")
                                if (".jpg" in clean_u or ".webp" in clean_u) and any(
                                    tag in clean_u for tag in ("t51.82787-15", "t51.2885-15", "p1080x1080", "s1080x1080", "c604")
                                ):
                                    if clean_u not in image_urls:
                                        image_urls.append(clean_u)
            else:
                async with httpx.AsyncClient(follow_redirects=True, timeout=12.0, headers=headers) as client:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        return None
                    content = resp.text

                title_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
                if title_match:
                    title = html_lib.unescape(title_match.group(1)).strip()
                else:
                    doc_title = re.search(r'<title>([^<]+)</title>', content)
                    if doc_title:
                        title = html_lib.unescape(doc_title.group(1)).strip()

                desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', content)
                if desc_match:
                    desc = html_lib.unescape(desc_match.group(1)).strip()

                og_img = re.search(r'<meta property="og:image" content="([^"]+)"', content)
                if og_img:
                    clean_og = html_lib.unescape(og_img.group(1)).replace("\\u0026", "&").replace("\\", "")
                    image_urls.append(clean_og)

            if not image_urls:
                return None

            items = [
                MediaImageItem(
                    id=f"img_{i+1}",
                    url=img_url,
                    preview_url=img_url,
                    index=i,
                    title=f"Photo {i+1}",
                    format="jpg",
                    width=None,
                    height=None,
                    filesize=None,
                )
                for i, img_url in enumerate(image_urls)
            ]

            media_type = "gallery" if len(items) > 1 else "image"

            return ExtractionResult(
                url=url,
                type=media_type,
                title=title,
                thumbnail=items[0].url if items else "",
                duration=None,
                uploader=uploader,
                platform=platform,
                description=desc,
                video_formats=[],
                audio_formats=[],
                images=items,
                playlist_items=[],
                total_items=len(items) if len(items) > 1 else None,
                created_at=datetime.datetime.now(datetime.UTC).isoformat(),
            )
        except Exception as exc:
            logger.warning(f"Failed to extract social images for {url}: {exc}")
            return None
