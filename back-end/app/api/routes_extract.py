from fastapi import APIRouter, Request

from app.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.media import ExtractRequest, ExtractResponse
from app.services.ytdlp_service import YtDlpService

router = APIRouter(prefix="/api/extract", tags=["Media Extraction"])
settings = get_settings()


@router.post("", response_model=ExtractResponse)
async def extract_media(payload: ExtractRequest, request: Request):
    # Apply Rate Limiting
    client_ip = limiter.get_client_ip(request)
    limiter.check(f"extract:{client_ip}", max_requests=settings.RATE_LIMIT_EXTRACT_PER_MIN)

    # Perform real extraction via yt-dlp service
    extraction_result = await YtDlpService.extract_info(payload.url)

    return ExtractResponse(
        success=True,
        media=extraction_result,
    )
