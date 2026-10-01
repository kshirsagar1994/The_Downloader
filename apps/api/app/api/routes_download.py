import mimetypes
import urllib.parse
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.config import get_settings
from app.core.errors import JobNotFoundError
from app.core.rate_limit import limiter
from app.security.sanitization import sanitize_filename

router = APIRouter(prefix="/api/download", tags=["File Delivery"])
settings = get_settings()

MIME_OVERRIDE_MAP = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".opus": "audio/opus",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".zip": "application/zip",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


@router.get("/{job_id}")
async def download_media_file(job_id: str, request: Request):
    """
    Delivers the processed media file to the browser.
    Ensures zero internal filesystem path exposure, strict Content-Disposition headers,
    accurate MIME types, and Content-Length.
    """
    client_ip = limiter.get_client_ip(request)
    limiter.check(f"download:{client_ip}", max_requests=settings.RATE_LIMIT_DOWNLOAD_PER_MIN)

    # Sanitize job_id to prevent path traversal
    clean_job_id = Path(job_id).name
    job_dir = settings.storage_path / clean_job_id

    if not job_dir.exists() or not job_dir.is_dir():
        raise JobNotFoundError(f"Download artifact for job {clean_job_id} not found or expired.")

    # Find the deliverable file in the job directory (exclude temp parts or lock files)
    deliverable_files = [
        f for f in job_dir.iterdir()
        if f.is_file() and not f.name.startswith(".") and not f.name.endswith(".part") and not f.name.endswith(".ytdl")
    ]

    if not deliverable_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file is still generating or was cleaned up.",
        )

    # Pick final deliverable
    target_file = deliverable_files[0]
    safe_name = sanitize_filename(target_file.name)
    file_size = target_file.stat().st_size

    # Determine MIME Type
    ext = target_file.suffix.lower()
    media_type = MIME_OVERRIDE_MAP.get(ext)
    if not media_type:
        guessed_type, _ = mimetypes.guess_type(target_file.name)
        media_type = guessed_type or "application/octet-stream"

    # RFC 5987 / RFC 6266 Header Encoding
    ascii_fallback = safe_name.encode("ascii", "ignore").decode("ascii") or "download"
    encoded_utf8_filename = urllib.parse.quote(safe_name)

    content_disposition = (
        f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_utf8_filename}'
    )

    return FileResponse(
        path=str(target_file.resolve()),
        filename=safe_name,
        media_type=media_type,
        headers={
            "Content-Disposition": content_disposition,
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        },
    )
