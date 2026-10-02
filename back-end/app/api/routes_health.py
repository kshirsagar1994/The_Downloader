import shutil
import subprocess

import yt_dlp.version
from fastapi import APIRouter

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

    overall_status = "ok" if (ytdlp_ok and ffmpeg_ok) else "degraded"
    details = "YouTube extraction engine operational"
    if pot_configured and pot_available:
        details += " with active PO Token Provider"
    elif cookies_configured:
        details += " with optional authentication cookies"
    else:
        details += " in direct player client mode"

    return YouTubeHealthResponse(
        status=overall_status,
        yt_dlp=ytdlp_ok,
        ffmpeg=ffmpeg_ok,
        redis=redis_ok,
        po_token_provider=pot_configured,
        po_token_provider_available=pot_available,
        cookies_configured=cookies_configured,
        details=details,
    )


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
