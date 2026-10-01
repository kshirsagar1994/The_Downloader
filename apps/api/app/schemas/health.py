
from pydantic import BaseModel


class ComponentHealth(BaseModel):
    status: str  # ok, degraded, error
    version: str | None = None
    details: str | None = None


class SystemHealthResponse(BaseModel):
    api: str = "ok"
    redis: str = "ok"
    worker: str = "ok"
    yt_dlp: str = "ok"
    ffmpeg: str = "ok"
    version: str
    environment: str
    components: dict[str, ComponentHealth] = {}
