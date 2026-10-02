
from pydantic import BaseModel, Field


class MediaFormatOption(BaseModel):
    format_id: str
    label: str
    extension: str
    quality: str | None = None
    resolution: str | None = None
    filesize_approx: int | None = None
    has_video: bool = True
    has_audio: bool = True
    is_best: bool = False
    vcodec: str | None = None
    acodec: str | None = None
    fps: int | None = None


class MediaImageItem(BaseModel):
    id: str
    url: str
    preview_url: str
    title: str | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    filesize: int | None = None
    index: int


class PlaylistItem(BaseModel):
    id: str
    url: str
    title: str
    thumbnail: str | None = None
    duration: int | None = None
    uploader: str | None = None
    index: int


class ExtractRequest(BaseModel):
    url: str = Field(..., description="Target media URL to analyze")


class ExtractionResult(BaseModel):
    url: str
    type: str  # video, audio, image, gallery, playlist
    title: str
    thumbnail: str | None = None
    duration: int | None = None
    uploader: str | None = None
    platform: str | None = None
    description: str | None = None
    video_formats: list[MediaFormatOption] = Field(default_factory=list)
    audio_formats: list[MediaFormatOption] = Field(default_factory=list)
    images: list[MediaImageItem] = Field(default_factory=list)
    playlist_items: list[PlaylistItem] = Field(default_factory=list)
    total_items: int | None = None
    created_at: str


class ExtractResponse(BaseModel):
    success: bool = True
    media: ExtractionResult
