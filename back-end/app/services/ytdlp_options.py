import copy
import os
from typing import Any

from app.config import get_settings

settings = get_settings()


def build_base_ydl_opts(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Builds a secure, optimized base dictionary of yt-dlp options.
    Automatically configures:
    1. YouTube player clients (visionos, android, web when PO token provider available)
    2. Dynamic BgUtils PO Token Provider (HTTP server or local script mode)
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

    # Add PO Token Provider configuration if URL is configured (HTTP server mode)
    provider_url = settings.resolved_po_token_provider_url
    if provider_url:
        extractor_args["youtubepot-bgutilhttp"] = {
            "base_url": provider_url,
        }

    # Configure bgutil script-mode PO token generation (local Node.js execution)
    bgutil_home = _resolve_bgutil_script_home()
    if bgutil_home:
        extractor_args["youtubepot-bgutilscript"] = {
            "server_home": bgutil_home,
        }

    import shutil

    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "socket_timeout": 20,
        "geo_bypass": True,
        "extractor_args": extractor_args,
    }

    # Enable JavaScript runtime for YouTube player signature challenges
    js_runtime: dict[str, Any] = {}
    if shutil.which("node"):
        js_runtime["node"] = {}
    elif shutil.which("deno"):
        js_runtime["deno"] = {}
    elif shutil.which("bun"):
        js_runtime["bun"] = {}

    if js_runtime:
        opts["js_runtimes"] = js_runtime

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


def _resolve_bgutil_script_home() -> str | None:
    """
    Resolves the bgutil-ytdlp-pot-provider server home directory.
    Checks in order:
    1. BGUTIL_SCRIPT_HOME environment/config setting
    2. Default Docker build path /opt/bgutil-pot/server
    3. Home directory ~/bgutil-ytdlp-pot-provider/server
    Returns None if no valid installation is found.
    """
    # 1. Explicit configuration
    if settings.BGUTIL_SCRIPT_HOME and settings.BGUTIL_SCRIPT_HOME.strip():
        candidate = settings.BGUTIL_SCRIPT_HOME.strip()
        if os.path.isdir(candidate):
            return candidate

    # 2. Default Docker build path (set in Dockerfile.api)
    docker_path = "/opt/bgutil-pot/server"
    if os.path.isdir(docker_path):
        return docker_path

    # 3. Home directory fallback
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if home:
        home_path = os.path.join(home, "bgutil-ytdlp-pot-provider", "server")
        if os.path.isdir(home_path):
            return home_path

    return None


def get_youtube_fallback_clients() -> list[list[str]]:
    """
    Returns the ordered list of player client fallback combinations
    to attempt if extraction fails. Prioritizes clients that do not require
    unsupported GVS PO tokens.
    """
    return [
        ["visionos"],
        ["android"],
        ["visionos", "android"],
        ["ios"],
        ["tv_embedded"],
        ["mweb"],
        ["web"],
    ]
