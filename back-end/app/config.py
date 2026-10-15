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
    APP_VERSION: str = "1.0.9"

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
    MAX_EXTRACTION_TIMEOUT_SECONDS: int = 45

    # YouTube PO Token Provider & Authentication
    PO_TOKEN_PROVIDER_URL: str | None = None
    POT_PROVIDER_PORT: int = 4416
    POT_PROVIDER_TIMEOUT_SECONDS: float = 5.0
    YOUTUBE_PO_TOKEN: str | None = None
    YOUTUBE_VISITOR_DATA: str | None = None
    YOUTUBE_COOKIES: str | None = None
    YOUTUBE_COOKIES_FILE: str | None = None
    YOUTUBE_CLIENTS: str | None = None
    YT_DLP_UPDATE_CHANNEL: str = "stable"
    # Path to bgutil-ytdlp-pot-provider server directory for script-mode PO token generation
    BGUTIL_SCRIPT_HOME: str | None = None

    # Instagram Authentication
    INSTAGRAM_COOKIES: str | None = None
    INSTAGRAM_COOKIES_FILE: str | None = None

    # TikTok Authentication
    TIKTOK_COOKIES: str | None = None
    TIKTOK_COOKIES_FILE: str | None = None

    # Snapchat Authentication
    SNAPCHAT_COOKIES: str | None = None
    SNAPCHAT_COOKIES_FILE: str | None = None

    # Twitter/X Authentication
    TWITTER_COOKIES: str | None = None
    TWITTER_COOKIES_FILE: str | None = None

    # Generic fallback cookies
    COOKIES_FILE: str | None = None

    # Proxy Configuration (Residential / Datacenter Bypass)
    YOUTUBE_PROXY_URL: str | None = None
    YOUTUBE_PROXY: str | None = None
    INSTAGRAM_PROXY_URL: str | None = None
    TIKTOK_PROXY_URL: str | None = None
    SNAPCHAT_PROXY_URL: str | None = None
    TWITTER_PROXY_URL: str | None = None
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
        Intelligently handles Render edge port routing (.onrender.com -> https).
        Auto-detects container daemon at http://127.0.0.1:4416 if /opt/bgutil-pot/server is present.
        """
        candidate = self.PO_TOKEN_PROVIDER_URL
        if not candidate or not candidate.strip() or candidate.strip().rstrip("/") in (
            "http://the-downloader-pot-provider:4416",
            "the-downloader-pot-provider:4416",
        ):
            # If internal container background provider exists, auto-default to it
            import os
            if os.path.isdir("/opt/bgutil-pot/server"):
                return f"http://127.0.0.1:{self.POT_PROVIDER_PORT}"
            if not candidate or not candidate.strip():
                return None

        raw_url = candidate.strip().rstrip("/")
        # Fix Render hostport edge cases:
        # If pointing to an onrender.com host with port 4416, Render public router does not expose 4416 externally.
        # Render web services over public internet terminate TLS on port 443 with HTTPS.
        if ".onrender.com:4416" in raw_url.lower():
            raw_url = raw_url.replace(":4416", "")
            if raw_url.startswith("http://"):
                raw_url = "https://" + raw_url[7:]
            elif not raw_url.startswith("https://"):
                raw_url = f"https://{raw_url}"
        elif ".onrender.com" in raw_url.lower() and not raw_url.startswith("http"):
            raw_url = f"https://{raw_url}"

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
    def resolved_youtube_proxy(self) -> str | None:
        """
        Resolves proxy specifically for YouTube extraction.
        Prioritizes YOUTUBE_PROXY_URL, then YOUTUBE_PROXY, HTTPS_PROXY, HTTP_PROXY.
        """
        candidate = (
            (self.YOUTUBE_PROXY_URL and self.YOUTUBE_PROXY_URL.strip())
            or (self.YOUTUBE_PROXY and self.YOUTUBE_PROXY.strip())
            or (self.HTTPS_PROXY and self.HTTPS_PROXY.strip())
            or (self.HTTP_PROXY and self.HTTP_PROXY.strip())
        )
        return self._validate_proxy_url(candidate)

    @property
    def resolved_global_proxy(self) -> str | None:
        """
        Resolves general upstream proxy for non-YouTube platforms.
        Does NOT leak YouTube-specific proxy credentials or routes.
        """
        candidate = (
            (self.HTTPS_PROXY and self.HTTPS_PROXY.strip())
            or (self.HTTP_PROXY and self.HTTP_PROXY.strip())
        )
        return self._validate_proxy_url(candidate)

    @property
    def resolved_proxy(self) -> str | None:
        """Backward-compatible proxy alias."""
        return self.resolved_youtube_proxy

    @staticmethod
    def _validate_proxy_url(candidate: str | None) -> str | None:
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
        """
        Returns client preferences matching provider capabilities:
        - Prioritizes visionos and android device clients to eliminate BotGuard challenges on cloud hosting IPs,
          while retaining tv, mweb, and web which leverage the BgUtil PO Token Provider.
        - Automatically translates deprecated/unsupported client names (e.g. 'tvhtml5' -> 'tv').
        - Always respects custom YOUTUBE_CLIENTS if explicitly defined (with tvhtml5 sanitized).
        """
        def _sanitize_clients(clients: list[str]) -> list[str]:
            sanitized: list[str] = []
            for c in clients:
                clean = c.strip()
                if clean.lower() == "tvhtml5":
                    clean = "tv"
                if clean and clean not in sanitized:
                    sanitized.append(clean)
            return sanitized

        if self.YOUTUBE_CLIENTS and self.YOUTUBE_CLIENTS.strip():
            raw_list = [c.strip() for c in self.YOUTUBE_CLIENTS.split(",") if c.strip()]
            return _sanitize_clients(raw_list)

        has_pot = bool(self.resolved_po_token_provider_url or self.YOUTUBE_PO_TOKEN or self.resolved_cookiefile)
        if has_pot:
            # Balanced cloud order: visionos/android bypass datacenter BotGuard; tv/mweb/web use PO Token provider
            return ["visionos", "android", "tv", "mweb", "ios", "web"]
        # Direct client mode without PO Token provider
        return ["visionos", "android", "ios", "tv", "mweb", "web"]

    @property
    def resolved_bgutil_script_home(self) -> str | None:
        """Resolves local script directory for bgutil script-mode PO token generation."""
        if self.BGUTIL_SCRIPT_HOME and self.BGUTIL_SCRIPT_HOME.strip():
            p = Path(self.BGUTIL_SCRIPT_HOME).resolve()
            if p.exists() and p.is_dir():
                return str(p)
        if Path("/opt/bgutil-pot/server").is_dir():
            return "/opt/bgutil-pot/server"
        return None

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

    # -------------------------------------------------------------------------
    # Platform-specific cookie resolution
    # -------------------------------------------------------------------------
    def _resolve_platform_cookiefile(
        self, cookies_env: str | None, cookies_file_env: str | None
    ) -> str | None:
        """Generic cookie resolution for any platform."""
        # 1. Dedicated file path
        candidate_file = cookies_file_env or self.COOKIES_FILE
        if candidate_file:
            path = Path(candidate_file).resolve()
            if path.exists() and path.is_file():
                return str(path)

        # 2. String/Base64 environment variable
        if cookies_env and cookies_env.strip():
            raw_content = cookies_env.strip()
            import base64
            import binascii
            try:
                decoded_bytes = base64.b64decode(raw_content, validate=True)
                cookie_text = decoded_bytes.decode("utf-8")
            except (binascii.Error, ValueError, UnicodeDecodeError):
                cookie_text = raw_content

            cookie_path = self.storage_path / f".auth_cookies_{hash(cookies_env) % 10000}.txt"
            cookie_path.write_text(cookie_text, encoding="utf-8")
            try:
                cookie_path.chmod(0o600)
            except (OSError, NotImplementedError):
                pass
            return str(cookie_path)

        return None

    @property
    def resolved_instagram_cookiefile(self) -> str | None:
        return self._resolve_platform_cookiefile(self.INSTAGRAM_COOKIES, self.INSTAGRAM_COOKIES_FILE)

    @property
    def resolved_tiktok_cookiefile(self) -> str | None:
        return self._resolve_platform_cookiefile(self.TIKTOK_COOKIES, self.TIKTOK_COOKIES_FILE)

    @property
    def resolved_snapchat_cookiefile(self) -> str | None:
        return self._resolve_platform_cookiefile(self.SNAPCHAT_COOKIES, self.SNAPCHAT_COOKIES_FILE)

    @property
    def resolved_twitter_cookiefile(self) -> str | None:
        return self._resolve_platform_cookiefile(self.TWITTER_COOKIES, self.TWITTER_COOKIES_FILE)

    # -------------------------------------------------------------------------
    # Platform-specific proxy resolution
    # -------------------------------------------------------------------------
    @property
    def resolved_instagram_proxy(self) -> str | None:
        candidate = (
            (self.INSTAGRAM_PROXY_URL and self.INSTAGRAM_PROXY_URL.strip())
            or (self.HTTPS_PROXY and self.HTTPS_PROXY.strip())
            or (self.HTTP_PROXY and self.HTTP_PROXY.strip())
        )
        return self._validate_proxy_url(candidate)

    @property
    def resolved_tiktok_proxy(self) -> str | None:
        candidate = (
            (self.TIKTOK_PROXY_URL and self.TIKTOK_PROXY_URL.strip())
            or (self.HTTPS_PROXY and self.HTTPS_PROXY.strip())
            or (self.HTTP_PROXY and self.HTTP_PROXY.strip())
        )
        return self._validate_proxy_url(candidate)

    @property
    def resolved_snapchat_proxy(self) -> str | None:
        candidate = (
            (self.SNAPCHAT_PROXY_URL and self.SNAPCHAT_PROXY_URL.strip())
            or (self.HTTPS_PROXY and self.HTTPS_PROXY.strip())
            or (self.HTTP_PROXY and self.HTTP_PROXY.strip())
        )
        return self._validate_proxy_url(candidate)

    @property
    def resolved_twitter_proxy(self) -> str | None:
        candidate = (
            (self.TWITTER_PROXY_URL and self.TWITTER_PROXY_URL.strip())
            or (self.HTTPS_PROXY and self.HTTPS_PROXY.strip())
            or (self.HTTP_PROXY and self.HTTP_PROXY.strip())
        )
        return self._validate_proxy_url(candidate)

    def cleanup_temp_cookies(self) -> None:
        """Safely cleans up temporary cookie artifacts from disk."""
        try:
            cookie_path = self.storage_path / ".auth_cookies.txt"
            if cookie_path.exists():
                cookie_path.unlink(missing_ok=True)
            # Clean up platform-specific cookies
            for f in self.storage_path.glob(".auth_cookies_*.txt"):
                f.unlink(missing_ok=True)
        except OSError:
            pass


@lru_cache
def get_settings() -> Settings:
    return Settings()
