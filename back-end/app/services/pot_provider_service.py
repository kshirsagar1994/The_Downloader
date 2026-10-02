import time
from typing import Any

import httpx

from app.config import get_settings
from app.core.logging import logger

settings = get_settings()


class POTProviderService:
    """Service to verify and interface with the BgUtils PO Token Provider."""

    _last_check_time: float = 0
    _last_status: bool = False
    _last_version: str | None = None

    @classmethod
    def get_provider_url(cls) -> str | None:
        """Returns the configured PO token provider URL if set."""
        return settings.resolved_po_token_provider_url

    @classmethod
    async def check_health(cls, timeout: float = 3.0) -> dict[str, Any]:
        """
        Safely probes the PO Token Provider /ping endpoint without exposing secrets or internal URLs.
        Caches result for 15 seconds to avoid flooding the provider.
        """
        provider_url = cls.get_provider_url()
        if not provider_url:
            return {
                "configured": False,
                "available": False,
                "details": "No PO Token Provider URL configured. Running in direct client mode.",
            }

        now = time.time()
        if now - cls._last_check_time < 15.0:
            return {
                "configured": True,
                "available": cls._last_status,
                "version": cls._last_version,
                "details": "Healthy" if cls._last_status else "Provider unreachable",
            }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(f"{provider_url}/ping")
                if resp.status_code == 200:
                    cls._last_status = True
                    cls._last_check_time = now
                    try:
                        data = resp.json()
                        cls._last_version = str(data.get("version", "ok"))
                    except Exception:
                        cls._last_version = "ok"

                    logger.debug("[YT] PO Token Provider is healthy")
                    return {
                        "configured": True,
                        "available": True,
                        "version": cls._last_version,
                        "details": "Provider active and ready",
                    }
                else:
                    cls._last_status = False
                    cls._last_check_time = now
                    logger.warning(f"[YT] PO Token Provider returned HTTP {resp.status_code}")
                    return {
                        "configured": True,
                        "available": False,
                        "details": f"Provider returned HTTP {resp.status_code}",
                    }
        except Exception as exc:
            cls._last_status = False
            cls._last_check_time = now
            logger.warning(f"[YT] Could not connect to PO Token Provider: {exc}")
            return {
                "configured": True,
                "available": False,
                "details": "Provider unreachable or offline",
            }
