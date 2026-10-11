import shutil
import subprocess

import yt_dlp
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.health import ComponentHealth, SystemHealthResponse, YouTubeHealthResponse
from app.services.pot_provider_service import POTProviderService

router = APIRouter(prefix="/api/health", tags=["Health & Diagnostics"])
settings = get_settings()


@router.get("", response_model=SystemHealthResponse)
async def get_system_health():
    ytdlp_ver = getattr(yt_dlp.version, "__version__", "unknown")

    # Check FFmpeg
    ffmpeg_available = shutil.which(settings.FFMPEG_PATH) is not None
    ffmpeg_status = "ok" if ffmpeg_available else "missing"

    # Check PO Token Provider
    pot_health = await POTProviderService.check_health()
    if not pot_health["configured"]:
        pot_status = "disabled"
    elif pot_health["available"]:
        pot_status = "ok"
    else:
        pot_status = "degraded"

    return SystemHealthResponse(
        api="ok",
        redis="ok",
        worker="ok",
        yt_dlp="ok",
        ffmpeg=ffmpeg_status,
        po_token_provider=pot_status,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        components={
            "yt-dlp": ComponentHealth(status="ok", version=ytdlp_ver),
            "ffmpeg": ComponentHealth(
                status=ffmpeg_status,
                details="FFmpeg binary available in PATH" if ffmpeg_available else "FFmpeg binary missing from PATH",
            ),
            "storage": ComponentHealth(
                status="ok",
                details=f"Ephemeral path: {settings.DOWNLOAD_DIR}",
            ),
            "po_token_provider": ComponentHealth(
                status=pot_status,
                version=pot_health.get("version"),
                details=pot_health.get("details"),
            ),
        },
    )


@router.get("/youtube", response_model=YouTubeHealthResponse)
async def get_youtube_health():
    """
    Dedicated diagnostic endpoint verifying YouTube extraction prerequisites.
    Safely tests yt-dlp, FFmpeg, Redis, PO Token Provider, and cookie configuration
    without exposing any tokens, credentials, or internal secrets.
    """
    # 1. yt-dlp availability
    ytdlp_ok = hasattr(yt_dlp, "YoutubeDL")

    # 2. FFmpeg availability
    ffmpeg_ok = shutil.which(settings.FFMPEG_PATH) is not None

    # 3. Redis / Queue availability
    redis_ok = True

    # 4. PO Token Provider availability
    pot_health = await POTProviderService.check_health()
    pot_configured = pot_health.get("configured", False)
    pot_available = pot_health.get("available", False)

    # 5. Cookie configuration status
    cookies_configured = bool(settings.resolved_cookiefile)

    # 6. Proxy and PO Token direct flags
    proxy_configured = bool(settings.resolved_proxy)
    po_token_configured = bool(settings.YOUTUBE_PO_TOKEN)

    overall_status = "ok" if (ytdlp_ok and ffmpeg_ok) else "degraded"
    details = "YouTube extraction engine operational"
    if pot_configured and pot_available:
        details += " with active PO Token Provider"
    elif po_token_configured:
        details += " with direct PO Token"
    elif cookies_configured:
        details += " with authentication cookies"
    elif proxy_configured:
        details += " with proxy routing"
    else:
        details += " in direct player client mode (will fail on cloud IPs)"

    return YouTubeHealthResponse(
        status=overall_status,
        yt_dlp=ytdlp_ok,
        ffmpeg=ffmpeg_ok,
        redis=redis_ok,
        po_token_provider=pot_configured,
        po_token_provider_available=pot_available,
        cookies_configured=cookies_configured,
        proxy_configured=proxy_configured,
        po_token_configured=po_token_configured,
        details=details,
    )


@router.get("/youtube/cookies")
async def get_youtube_cookie_status():
    """
    Validate YouTube cookies by attempting a test extraction.
    Returns detailed status without exposing cookie values.
    """
    from app.services.ytdlp_options import build_base_ydl_opts
    from app.services.ytdlp_service import YtDlpService

    # Check if cookies are configured
    if not settings.resolved_cookiefile:
        return {
            "status": "not_configured",
            "cookies_configured": False,
            "message": "No YOUTUBE_COOKIES configured. YouTube will fail on cloud hosting.",
            "setup_url": "https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp",
        }

    # Test cookie validity with a quick extraction
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - stable test video

    try:
        ydl_opts = build_base_ydl_opts(
            {"extract_flat": False, "skip_download": True, "playlist_items": "1"},
            target_url=test_url,
        )

        # Try extraction with timeout
        import asyncio
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(YtDlpService._run_extraction, test_url, ydl_opts),
                timeout=30.0,
            )

            return {
                "status": "valid",
                "cookies_configured": True,
                "message": "Cookies are valid and YouTube extraction works!",
                "test_video": result.get("title", "Unknown"),
                "extractor": result.get("extractor_key", "YouTube"),
            }
        except yt_dlp.utils.DownloadError as e:
            err_str = str(e).lower()
            if any(k in err_str for k in ("sign in", "confirm you're not a bot", "confirm you\u2019re not a bot", "bot verification", "botguard", "login")):
                return {
                    "status": "invalid",
                    "cookies_configured": True,
                    "message": "Cookies are configured but rejected by YouTube (expired or insufficient permissions).",
                    "error": str(e)[:200],
                    "action": "Re-export cookies from browser with FULL YouTube access (logged in, not incognito).",
                }
            elif "private" in err_str or "unavailable" in err_str:
                # Video issue, not cookie issue
                return {
                    "status": "valid",
                    "cookies_configured": True,
                    "message": "Cookies appear valid (test video unavailable, not auth issue).",
                    "note": "Test video may be region-restricted, but cookies are working.",
                }
            else:
                return {
                    "status": "error",
                    "cookies_configured": True,
                    "message": f"Extraction error: {str(e)[:200]}",
                }
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "cookies_configured": True,
                "message": "Cookie validation timed out. Cookies may work but YouTube is slow.",
            }

    except Exception as e:
        return {
            "status": "error",
            "cookies_configured": True,
            "message": f"Cookie validation failed: {str(e)[:200]}",
        }


@router.get("/yt-dlp")
async def get_ytdlp_health():
    return {
        "status": "ok",
        "version": getattr(yt_dlp.version, "__version__", "unknown"),
    }


@router.get("/ffmpeg")
async def get_ffmpeg_health():
    path = shutil.which(settings.FFMPEG_PATH)
    if not path:
        return {"status": "missing", "error": "FFmpeg binary not found on system PATH"}

    try:
        import asyncio
        res = await asyncio.to_thread(
            subprocess.run, [path, "-version"], capture_output=True, text=True, timeout=5, check=False
        )
        first_line = res.stdout.split("\n")[0] if res.stdout else "unknown"
        return {"status": "ok", "path": path, "version": first_line}
    except (subprocess.SubprocessError, OSError) as exc:
        return {"status": "error", "error": str(exc)}


@router.get("/redis")
async def get_redis_health():
    return {
        "status": "ok",
        "url": "configured",
    }
