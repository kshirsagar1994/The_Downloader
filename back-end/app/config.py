from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment and defaults."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core
    APP_ENV: str = "development"
    DEBUG: bool = True
    APP_TITLE: str = "Universal Media Downloader API"
    APP_VERSION: str = "1.0.0"

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "*"

    # Redis Queue & PubSub
    REDIS_URL: str = "redis://localhost:6379/0"

    # Executable Paths
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    YTDLP_PATH: str = "yt-dlp"

    # Storage Paths
    DOWNLOAD_DIR: str = "./tmp/media-downloader"
    DOWNLOAD_EXPIRY_SECONDS: int = 3600
    CLEANUP_INTERVAL_SECONDS: int = 60

    # Rate Limiting & Safety Limits
    RATE_LIMIT_EXTRACT_PER_MIN: int = 20
    RATE_LIMIT_JOBS_PER_MIN: int = 10
    RATE_LIMIT_DOWNLOAD_PER_MIN: int = 30
    MAX_FILE_SIZE_MB: int = 5000
    MAX_PLAYLIST_ITEMS: int = 50
    MAX_CONCURRENT_JOBS_PER_IP: int = 3
    MAX_JOB_DURATION_SECONDS: int = 900
    MAX_EXTRACTION_TIMEOUT_SECONDS: int = 20

    # Admin Portal
    ADMIN_SECRET_KEY: str = "change-this-to-a-secure-random-token-in-production"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def storage_path(self) -> Path:
        p = Path(self.DOWNLOAD_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()
