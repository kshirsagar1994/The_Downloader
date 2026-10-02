from typing import Any
from pydantic import BaseModel, field_validator


class CreateJobRequest(BaseModel):
    url: str
    media_type: str  # video, audio, image, gallery, playlist
    format_id: str | None = None
    audio_bitrate: str | None = "320k"
    selected_image_indices: list[int] | None = None
    selected_playlist_indices: list[int] | None = None
    target_extension: str | None = None


class CreateJobResponse(BaseModel):
    success: bool = True
    job_id: str
    status: str = "QUEUED"
    message: str = "Job created and queued for background processing."


class JobProgressEvent(BaseModel):
    job_id: str
    status: str  # QUEUED, ANALYZING, DOWNLOADING, PROCESSING, PACKAGING, COMPLETED, FAILED, CANCELLED, EXPIRED
    progress: float = 0.0  # 0.0 to 100.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # bytes / sec
    eta: int = 0  # seconds
    stage_message: str = "Initializing..."
    filename: str | None = None
    mime_type: str | None = None
    download_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None

    @field_validator("downloaded_bytes", "total_bytes", "eta", mode="before")
    @classmethod
    def coerce_to_int(cls, v: Any) -> int:
        if v is None:
            return 0
        if isinstance(v, (float, int, str)):
            try:
                return int(round(float(v)))
            except (ValueError, TypeError):
                return 0
        return 0

    @field_validator("progress", "speed", mode="before")
    @classmethod
    def coerce_to_float(cls, v: Any) -> float:
        if v is None:
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0
