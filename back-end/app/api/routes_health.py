import shutil
import subprocess

import yt_dlp.version
from fastapi import APIRouter

from app.config import get_settings
from app.schemas.health import ComponentHealth, SystemHealthResponse

router = APIRouter(prefix="/api/health", tags=["Health & Diagnostics"])
settings = get_settings()


@router.get("", response_model=SystemHealthResponse)
async def get_system_health():
    ytdlp_ver = getattr(yt_dlp.version, "__version__", "unknown")

    # Check FFmpeg
    ffmpeg_available = shutil.which(settings.FFMPEG_PATH) is not None
    ffmpeg_status = "ok" if ffmpeg_available else "missing"

    return SystemHealthResponse(
        api="ok",
        redis="ok",
        worker="ok",
        yt_dlp="ok",
        ffmpeg=ffmpeg_status,
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
        },
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
        "url": settings.REDIS_URL,
    }
