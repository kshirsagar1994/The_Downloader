import copy
from typing import Any

from app.config import get_settings

settings = get_settings()


def build_base_ydl_opts(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Builds a secure, optimized base dictionary of yt-dlp options.
    Automatically configures:
    1. YouTube player clients (visionos, web, mweb, ios, tv_embedded)
    2. Dynamic BgUtils PO Token Provider (youtubepot-bgutilhttp:base_url) or direct PO tokens
    3. Cookiefile if configured
    4. HTTP/HTTPS/SOCKS Proxy if configured
    5. Timeouts, geo-bypass, safety limits
    """
    youtube_args: dict[str, Any] = {
        "player_client": settings.resolved_youtube_clients,
    }

    if settings.YOUTUBE_PO_TOKEN and settings.YOUTUBE_PO_TOKEN.strip():
        po_token_val = settings.YOUTUBE_PO_TOKEN.strip()
        if "+" not in po_token_val and "." not in po_token_val:
            po_token_val = f"web.player+{po_token_val}"
        youtube_args["po_token"] = [po_token_val]

    if settings.YOUTUBE_VISITOR_DATA and settings.YOUTUBE_VISITOR_DATA.strip():
        youtube_args["visitor_data"] = [settings.YOUTUBE_VISITOR_DATA.strip()]

    extractor_args: dict[str, dict[str, Any]] = {
        "youtube": youtube_args,
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

    if settings.resolved_proxy:
        opts["proxy"] = settings.resolved_proxy

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
        ["visionos"],
        ["ios"],
        ["tv_embedded"],
        ["android_creator"],
        ["mweb"],
        ["web_creator"],
        ["tv_downgraded"],
        ["android"],
        ["web"],
    ]
