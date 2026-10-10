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
    APP_VERSION: str = "1.0.3"

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

    # YouTube PO Token Provider & Authentication
    PO_TOKEN_PROVIDER_URL: str | None = None
    YOUTUBE_PO_TOKEN: str | None = None
    YOUTUBE_VISITOR_DATA: str | None = None
    YOUTUBE_COOKIES: str | None = None
    YOUTUBE_COOKIES_FILE: str | None = None
    COOKIES_FILE: str | None = None
    YOUTUBE_CLIENTS: str | None = None
    YT_DLP_UPDATE_CHANNEL: str = "stable"
    # Path to bgutil-ytdlp-pot-provider server directory for script-mode PO token generation
    BGUTIL_SCRIPT_HOME: str | None = None

    # Proxy Configuration (Residential / Datacenter Bypass)
    YOUTUBE_PROXY_URL: str | None = None
    YOUTUBE_PROXY: str | None = None
    HTTP_PROXY: str | None = None
    HTTPS_PROXY: str | None = None

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

    @property
    def resolved_po_token_provider_url(self) -> str | None:
        """
        Validates and returns the PO Token Provider URL.
        Prevents SSRF by enforcing valid http/https schemes and valid hostnames.
        Supports hostport inputs from cloud orchestrators (e.g. Render 'fromService: hostport').
        Auto-detects container daemon at http://127.0.0.1:4416 if /opt/bgutil-pot/server is present.
        """
        candidate = self.PO_TOKEN_PROVIDER_URL
        if not candidate or not candidate.strip():
            # If internal container background provider exists, auto-default to it
            import os
            if os.path.isdir("/opt/bgutil-pot/server"):
                return "http://127.0.0.1:4416"
            return None
        raw_url = candidate.strip().rstrip("/")
        if "://" not in raw_url:
            raw_url = f"http://{raw_url}"
        from urllib.parse import urlparse
        try:
            parsed = urlparse(raw_url)
            if parsed.scheme.lower() not in ("http", "https"):
                return None
            if not parsed.hostname:
                return None
            return raw_url
        except (ValueError, TypeError, AttributeError):
            return None

    @property
    def resolved_proxy(self) -> str | None:
        """
        Resolves configured proxy with scheme validation (http, https, socks5, socks5h).
        Prioritizes YOUTUBE_PROXY_URL, then YOUTUBE_PROXY, HTTPS_PROXY, HTTP_PROXY.
        """
        candidate = (
            (self.YOUTUBE_PROXY_URL and self.YOUTUBE_PROXY_URL.strip())
            or (self.YOUTUBE_PROXY and self.YOUTUBE_PROXY.strip())
            or (self.HTTPS_PROXY and self.HTTPS_PROXY.strip())
            or (self.HTTP_PROXY and self.HTTP_PROXY.strip())
        )
        if not candidate:
            return None

        from urllib.parse import urlparse
        try:
            parsed = urlparse(candidate)
            if parsed.scheme.lower() in ("http", "https", "socks5", "socks5h"):
                return candidate
        except (ValueError, TypeError, AttributeError):
            return None
        return None

    @property
    def resolved_youtube_clients(self) -> list[str]:
        raw_clients: list[str] = []
        if self.YOUTUBE_CLIENTS:
            raw_clients = [c.strip() for c in self.YOUTUBE_CLIENTS.split(",") if c.strip()]

        if not raw_clients:
            raw_clients = ["android", "visionos", "web", "mweb"]

        # If user has configured authenticated cookies, keep configured client order
        if self.resolved_cookiefile:
            return raw_clients

        # On cloud servers without cookies, always prioritize bot-challenge-free clients
        # (android, visionos, ios, tv_downgraded) ahead of web/mweb
        bot_free = [c for c in raw_clients if c in ("android", "visionos", "ios", "tv_downgraded")]
        other = [c for c in raw_clients if c not in ("android", "visionos", "ios", "tv_downgraded")]

        if not bot_free:
            bot_free = ["android", "visionos"]

        return bot_free + other

    @property
    def resolved_cookiefile(self) -> str | None:
        """
        Safely locates or constructs a restricted Netscape-format cookie file.
        Supports:
        1. YOUTUBE_COOKIES_FILE or COOKIES_FILE on disk.
        2. YOUTUBE_COOKIES env var (auto-detects base64 or raw string).
        3. Local default ./cookies.txt if present.
        """
        # 1. Dedicated file path configuration
        candidate_file = self.YOUTUBE_COOKIES_FILE or self.COOKIES_FILE
        if candidate_file:
            path = Path(candidate_file).resolve()
            if path.exists() and path.is_file():
                return str(path)

        # 2. String/Base64 environment variable
        if self.YOUTUBE_COOKIES and self.YOUTUBE_COOKIES.strip():
            raw_content = self.YOUTUBE_COOKIES.strip()
            # Attempt base64 decode if applicable
            cookie_text: str
            import base64
            import binascii
            try:
                decoded_bytes = base64.b64decode(raw_content, validate=True)
                cookie_text = decoded_bytes.decode("utf-8")
            except (binascii.Error, ValueError, UnicodeDecodeError):
                cookie_text = raw_content

            # Write to access-restricted temporary cookie file
            cookie_path = self.storage_path / ".auth_cookies.txt"
            cookie_path.write_text(cookie_text, encoding="utf-8")
            try:
                # Restrict file permissions to owner read/write (POSIX 0600)
                cookie_path.chmod(0o600)
            except (OSError, NotImplementedError):
                pass
            return str(cookie_path)

        # 3. Default fallback
        default_cookie = Path("./cookies.txt")
        if default_cookie.exists():
            return str(default_cookie.resolve())
        return None

    def cleanup_temp_cookies(self) -> None:
        """Safely cleans up temporary cookie artifacts from disk."""
        try:
            cookie_path = self.storage_path / ".auth_cookies.txt"
            if cookie_path.exists():
                cookie_path.unlink(missing_ok=True)
        except OSError:
            pass


@lru_cache
def get_settings() -> Settings:
    return Settings()
