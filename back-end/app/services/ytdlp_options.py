import copy
from typing import Any

from app.config import get_settings

settings = get_settings()


def build_base_ydl_opts(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Builds a secure, optimized base dictionary of yt-dlp options.
    Automatically configures:
    1. YouTube player clients (android, android_creator, tv_embedded, ios, web)
    2. Dynamic BgUtils PO Token Provider (youtubepot-bgutilhttp:base_url) if configured
    3. Cookiefile if configured
    4. Timeouts, geo-bypass, safety limits
    """
    extractor_args: dict[str, dict[str, Any]] = {
        "youtube": {
            "player_client": ["android", "android_creator", "tv_embedded", "ios", "web"],
        }
    }

    # Add PO Token Provider configuration if URL is configured
    provider_url = settings.resolved_po_token_provider_url
    if provider_url:
        extractor_args["youtubepot-bgutilhttp"] = {
            "base_url": provider_url,
        }

    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "socket_timeout": 20,
        "geo_bypass": True,
        "extractor_args": extractor_args,
    }

    if settings.resolved_cookiefile:
        opts["cookiefile"] = settings.resolved_cookiefile

    if overrides:
        # Deep merge/update overrides
        for k, v in overrides.items():
            if k == "extractor_args" and isinstance(v, dict):
                merged_args = copy.deepcopy(extractor_args)
                for ek, ev in v.items():
                    if ek in merged_args and isinstance(ev, dict):
                        merged_args[ek].update(ev)
                    else:
                        merged_args[ek] = ev
                opts["extractor_args"] = merged_args
            else:
                opts[k] = v

    return opts


def get_youtube_fallback_clients() -> list[list[str]]:
    """
    Returns the ordered list of player client fallback combinations
    to attempt if extraction fails.
    """
    return [
        ["android"],
        ["android_creator"],
        ["tv_embedded"],
        ["ios", "android"],
        ["mweb"],
        ["tv"],
        ["web"],
    ]
