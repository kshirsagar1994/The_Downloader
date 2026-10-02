import shutil

import yt_dlp.version
from fastapi import APIRouter, Depends

from app.config import get_settings
from app.security.auth import verify_admin_token

router = APIRouter(prefix="/api/admin", tags=["Admin Portal"], dependencies=[Depends(verify_admin_token)])
settings = get_settings()


@router.get("/metrics")
async def get_admin_metrics():
    # Compute ephemeral storage stats
    storage_path = settings.storage_path
    total_space, used_space, free_space = shutil.disk_usage(str(storage_path))

    job_dirs = list(storage_path.iterdir()) if storage_path.exists() else []

    return {
        "status": "online",
        "engine_version": "v1.0.0",
        "processor_status": "Active & Ready",
        "storage": {
            "total_bytes": total_space,
            "used_bytes": used_space,
            "free_bytes": free_space,
            "active_job_directories": len(job_dirs),
        },
        "limits": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "max_playlist_items": settings.MAX_PLAYLIST_ITEMS,
            "download_expiry_seconds": settings.DOWNLOAD_EXPIRY_SECONDS,
        },
    }
