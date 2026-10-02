from pydantic import BaseModel


class ComponentHealth(BaseModel):
    status: str  # ok, degraded, error, missing, disabled
    version: str | None = None
    details: str | None = None


class SystemHealthResponse(BaseModel):
    api: str = "ok"
    redis: str = "ok"
    worker: str = "ok"
    yt_dlp: str = "ok"
    ffmpeg: str = "ok"
    po_token_provider: str = "ok"
    version: str
    environment: str
    components: dict[str, ComponentHealth] = {}


class YouTubeHealthResponse(BaseModel):
    status: str  # ok, degraded
    yt_dlp: bool = True
    ffmpeg: bool = True
    redis: bool = True
    po_token_provider: bool = False
    po_token_provider_available: bool = False
    cookies_configured: bool = False
    details: str | None = None
