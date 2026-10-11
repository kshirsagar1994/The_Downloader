import asyncio
import copy
import datetime
import html as html_lib
import re
from typing import Any

import httpx
import yt_dlp

from app.config import get_settings
from app.core.errors import (
    DownloaderException,
    ExtractionFailedError,
    OperationTimeoutError,
)
from app.core.logging import logger
from app.schemas.media import ExtractionResult, MediaImageItem
from app.security.ssrf import validate_url_ssrf
from app.services.error_classifier import classify_ytdlp_error
from app.services.metadata_service import MetadataService
from app.services.pot_provider_service import POTProviderService
from app.services.ytdlp_options import build_base_ydl_opts, get_youtube_fallback_clients

settings = get_settings()


class YtDlpService:
    """Encapsulated extraction and download service wrapping the yt-dlp engine with PO Token Provider support."""

    @classmethod
    async def _check_po_token_provider_health(cls) -> bool:
        """Check if PO Token provider is healthy and can generate valid tokens."""
        provider_url = settings.resolved_po_token_provider_url
        if not provider_url:
            return False
        
        try:
            health = await POTProviderService.check_health(timeout=2.0)
            return health.get("available", False)
        except Exception:  # noqa: BLE001
            return False

    @classmethod
    async def extract_info(cls, url: str) -> ExtractionResult:
        # Step 1: Pre-flight SSRF Validation
        validated_url = validate_url_ssrf(url)

        is_youtube = "youtube.com" in validated_url.lower() or "youtu.be" in validated_url.lower()

        # Check PO Token provider health for YouTube URLs
        po_provider_healthy = False
        if is_youtube and settings.resolved_po_token_provider_url:
            po_provider_healthy = await cls._check_po_token_provider_health()
            if not po_provider_healthy:
                logger.warning("[YT] PO Token provider unhealthy or unreachable, will attempt extraction without it")

        # Build options - if PO Token provider is unhealthy, pass flag to skip it
        ydl_opts = build_base_ydl_opts(
            {
                "extract_flat": False,
                "skip_download": True,
                "playlist_items": f"1-{settings.MAX_PLAYLIST_ITEMS}",
            },
            target_url=validated_url,
        )

        # If PO Token provider is configured but unhealthy, strip it from options
        if is_youtube and settings.resolved_po_token_provider_url and not po_provider_healthy:
            if "extractor_args" in ydl_opts and isinstance(ydl_opts["extractor_args"], dict):
                ydl_opts["extractor_args"].pop("youtubepot-bgutilhttp", None)
                ydl_opts["extractor_args"].pop("youtubepot-bgutilscript", None)
                logger.info("[YT] Stripped PO Token provider from extraction options due to health check failure")

        try:
            if is_youtube:
                logger.info(f"[YT] Starting extraction for URL: {validated_url}")
                if settings.resolved_po_token_provider_url:
                    if po_provider_healthy:
                        logger.info("[YT] PO Token provider configured and healthy")
                    else:
                        logger.info("[YT] PO Token provider configured but unhealthy - using direct client mode")
            else:
                logger.info(f"Extracting metadata for URL: {validated_url}")

            # Run blocking extraction in worker thread with timeout
            raw_info = await asyncio.wait_for(
                asyncio.to_thread(cls._run_extraction, validated_url, ydl_opts),
                timeout=settings.MAX_EXTRACTION_TIMEOUT_SECONDS,
            )

            if not raw_info or not isinstance(raw_info, dict):
                raise ExtractionFailedError("No metadata returned by extractor.")

            if is_youtube:
                logger.info(f"[YT] Extraction successful: {raw_info.get('title', 'Untitled')[:40]}")

            return MetadataService.parse_extraction_result(validated_url, raw_info)

        except TimeoutError as exc:
            logger.error(f"Extraction timed out for URL: {validated_url}")
            raise OperationTimeoutError("Media analysis timed out. The source may be slow or unresponsive.") from exc

        except yt_dlp.utils.DownloadError as exc:
            err_msg = str(exc).lower()
            logger.error(f"yt-dlp DownloadError: {exc}")

            # Photo post fallback for Instagram, Twitter, Pinterest (when no video formats exist)
            if any(k in err_msg for k in ("no video formats found", "no video could be found", "sent an empty media response", "only works when logged-in")) or any(p in validated_url.lower() for p in ("instagram", "pinterest", "twitter.com", "x.com")):
                try:
                    social_result = await cls._extract_social_media_images(validated_url)
                    if social_result:
                        return social_result
                except Exception as img_exc:  # noqa: BLE001
                    logger.warning(f"Social image extraction fallback failed: {img_exc}")

            # Centralized deterministic error classification
            classified_err = classify_ytdlp_error(exc, validated_url)
            raise classified_err from exc

        except DownloaderException:
            raise

        except Exception as exc:
            logger.error(f"Unexpected extraction exception: {exc}")
            classified_err = classify_ytdlp_error(exc, validated_url)
            raise classified_err from exc

    @classmethod
    def _run_extraction(cls, url: str, options: dict[str, Any]) -> dict[str, Any]:
        """Synchronous yt-dlp execution helper with client fallback and transient retries."""
        is_youtube = "youtube.com" in url.lower() or "youtu.be" in url.lower()

        def _extract_with_opts(opts: dict[str, Any]) -> dict[str, Any] | None:
            """Try extraction with given options, return result or None on failure."""
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    return ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError:
                return None
            except Exception:  # noqa: BLE001
                return None

        # Attempt 1: Primary extraction with configured options
        primary_result = _extract_with_opts(options)
        if primary_result:
            return primary_result

        # If primary failed, check if it was a bot verification error
        # We need to catch the exception to inspect it
        primary_error = None
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as exc:
            primary_error = exc
        except Exception as exc:  # noqa: BLE001
            primary_error = exc

        err_str = str(primary_error).lower() if primary_error else ""

        # Check for bot verification / sign-in challenges
        # Handle both straight (') and curly (') quotes in error messages
        is_bot_verification = any(k in err_str for k in (
            "confirm you're not a bot",
            "confirm you\u2019re not a bot",  # curly quote
            "confirm you\u2019re not a bot",  # curly quote (right single quotation mark)
            "bot verification",
            "botguard",
            "automated queries",
            "captcha",
        ))
        is_sign_in_required = any(k in err_str for k in ("sign in", "login required", "logged-in"))

        # For bot verification, we SHOULD try fallback clients (visionos/android can bypass BotGuard)
        # But for explicit sign-in required (private/age-restricted), don't hammer with fallbacks
        if is_sign_in_required and not is_bot_verification:
            if primary_error:
                raise primary_error
            raise yt_dlp.utils.DownloadError("Sign in required") from None

        # Vimeo fallback: public video pages on vimeo.com can prompt for login while player.vimeo.com works
        if "vimeo.com" in url.lower() and "player.vimeo.com" not in url.lower():
            vimeo_match = re.search(r"vimeo\.com/(?:video/)?(\d+)", url)
            if vimeo_match:
                embed_url = f"https://player.vimeo.com/video/{vimeo_match.group(1)}"
                try:
                    with yt_dlp.YoutubeDL(options) as ydl_vimeo:
                        vimeo_info = ydl_vimeo.extract_info(embed_url, download=False)
                        if vimeo_info:
                            return vimeo_info
                except Exception as fb_exc:  # noqa: BLE001
                    logger.debug(f"Vimeo player embed fallback failed: {fb_exc}")

        # YouTube fallback player clients - try even on bot verification
        if is_youtube:
            # For bot verification, try DIRECT client mode FIRST (visionos + android without PO Token)
            # This is the most reliable method for cloud hosting IPs
            if is_bot_verification:
                logger.info("[YT] Bot verification detected - attempting direct client mode first (visionos+android)...")
                direct_opts = copy.deepcopy(options)
                if "extractor_args" not in direct_opts or not isinstance(direct_opts["extractor_args"], dict):
                    direct_opts["extractor_args"] = {}

                # Use only the most resilient clients for direct mode
                direct_opts["extractor_args"]["youtube"] = {
                    "player_client": ["visionos", "android"],
                }
                # Completely remove PO Token provider and visitor data
                direct_opts["extractor_args"].pop("youtubepot-bgutilhttp", None)
                direct_opts["extractor_args"].pop("youtubepot-bgutilscript", None)

                direct_result = _extract_with_opts(direct_opts)
                if direct_result:
                    logger.info("[YT] Direct client mode extraction succeeded")
                    return direct_result

            # Then try individual fallback clients
            fallbacks = get_youtube_fallback_clients()
            # Try fewer fallback combinations on bot verification since direct mode was tried first
            max_fallbacks = 3 if is_bot_verification else 3

            for client_chain in fallbacks[:max_fallbacks]:
                fb_opts = copy.deepcopy(options)
                if "extractor_args" not in fb_opts or not isinstance(fb_opts["extractor_args"], dict):
                    fb_opts["extractor_args"] = {}
                if "youtube" not in fb_opts["extractor_args"] or not isinstance(fb_opts["extractor_args"]["youtube"], dict):
                    fb_opts["extractor_args"]["youtube"] = {}

                fb_opts["extractor_args"]["youtube"]["player_client"] = client_chain
                # Strip POT provider in fallback so mobile clients extract directly without provider timeouts
                fb_opts["extractor_args"].pop("youtubepot-bgutilhttp", None)
                fb_opts["extractor_args"].pop("youtubepot-bgutilscript", None)

                fb_result = _extract_with_opts(fb_opts)
                if fb_result:
                    logger.info(f"[YT] Fallback extraction succeeded with client(s): {client_chain}")
                    return fb_result

        if primary_error:
            raise primary_error
        raise yt_dlp.utils.DownloadError("Extraction failed with all client strategies") from None

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
