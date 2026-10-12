import copy
import shutil
from typing import Any

from app.config import get_settings
from app.core.logging import logger

settings = get_settings()


class YtDlpLogHandler:
    """
    Captures yt-dlp internal diagnostics and bridges them into application logs
    without leaking secrets, cookies, or token values.
    """

    def debug(self, msg: str) -> None:
        clean = msg.strip()
        if "Generated POT:" in clean:
            logger.info("[POT Provider] Token generation succeeded (token received)")
            return
        if "[pot] PO Token Providers:" in clean:
            provider_info = clean.split("[pot] PO Token Providers:")[1].strip()
            logger.info(f"[POT Provider] Plugin discovered: {provider_info}")
        elif "[pot] Attempting to fetch a PO Token from" in clean or ("Generating a" in clean and "PO Token" in clean):
            logger.info(f"[POT Provider] Token generation invoked: {clean}")
        elif "Retrieved a" in clean and "PO Token" in clean:
            logger.info(f"[POT Provider] Token generation succeeded: {clean}")
        elif "[pot:bgutil:http]" in clean:
            if "Checking server availability" in clean:
                logger.info("[POT Provider] Probing local provider health endpoint (/ping)")
            elif "Error reaching GET" in clean:
                logger.warning(f"[POT Provider] Health check warning: {clean}")
            else:
                logger.info(f"[POT Provider] {clean}")
        elif "[pot]" in clean:
            if "rejected this request" in clean:
                logger.info(f"[POT Provider] Provider rejected request: {clean}")
            elif "No PO Token providers were able to provide" in clean:
                logger.warning("[POT Provider] No PO token provider was able to provide a valid token")
            else:
                logger.debug(f"[yt-dlp:pot] {clean}")
        elif "Extracting player response for" in clean:
            client_name = clean.split("Extracting player response for")[-1].strip().split()[0]
            logger.info(f"[YT Client] Attempting extraction with player client: {client_name}")
        elif "[jsc:" in clean or "Solving JS challenges" in clean:
            logger.info(f"[YT-JSC] JavaScript challenge solver active: {clean}")
        else:
            logger.debug(f"[yt-dlp:debug] {clean}")

    def info(self, msg: str) -> None:
        clean = msg.strip()
        if "Generating a" in clean and "PO Token" in clean:
            logger.info(f"[POT Provider] Token generation invoked: {clean}")
        elif "Retrieved a" in clean and "PO Token" in clean:
            logger.info(f"[POT Provider] Token generation succeeded: {clean}")
        elif "Extracting player response for" in clean:
            client_name = clean.split("Extracting player response for")[-1].strip().split()[0]
            logger.info(f"[YT Client] Attempting extraction with player client: {client_name}")
        else:
            logger.info(f"[yt-dlp] {clean}")

    def warning(self, msg: str) -> None:
        logger.warning(f"[yt-dlp:warning] {msg.strip()}")

    def error(self, msg: str) -> None:
        logger.error(f"[yt-dlp:error] {msg.strip()}")


def build_base_ydl_opts(
    overrides: dict[str, Any] | None = None,
    target_url: str | None = None,
) -> dict[str, Any]:
    """
    Builds a secure, optimized base dictionary of yt-dlp options.
    Automatically configures:
    1. YouTube player clients matching provider capabilities
    2. Dynamic BgUtils PO Token Provider (HTTP server or local script mode)
    3. Cookiefile if configured
    4. Isolated HTTP/HTTPS/SOCKS Proxy (YouTube proxy restricted to YouTube)
    5. Timeouts, geo-bypass, safety limits
    6. Structured logging with secret scrubbing
    """
    current_settings = get_settings()
    is_youtube = bool(
        target_url and ("youtube.com" in target_url.lower() or "youtu.be" in target_url.lower())
    ) or (target_url is None)

    extractor_args: dict[str, dict[str, Any]] = {}

    if is_youtube:
        youtube_args: dict[str, Any] = {
            "player_client": current_settings.resolved_youtube_clients,
        }

        if current_settings.YOUTUBE_PO_TOKEN and current_settings.YOUTUBE_PO_TOKEN.strip():
            po_token_val = current_settings.YOUTUBE_PO_TOKEN.strip()
            if "+" not in po_token_val and "." not in po_token_val:
                po_token_val = f"web.player+{po_token_val}"
            youtube_args["po_token"] = [po_token_val]

        if current_settings.YOUTUBE_VISITOR_DATA and current_settings.YOUTUBE_VISITOR_DATA.strip():
            youtube_args["visitor_data"] = [current_settings.YOUTUBE_VISITOR_DATA.strip()]

        # Configure PO Token Provider (HTTP mode prioritized, script mode fallback)
        provider_url = current_settings.resolved_po_token_provider_url
        if provider_url:
            extractor_args["youtubepot-bgutilhttp"] = {
                "base_url": [provider_url],
            }
            # When PO Token Provider is active, ensure yt-dlp actively requests tokens
            # rather than skipping them under 'auto' policy:
            youtube_args["fetch_pot"] = ["always"]
            youtube_args["pot_trace"] = ["true"]
        elif current_settings.resolved_bgutil_script_home:
            extractor_args["youtubepot-bgutilscript"] = {
                "server_home": [current_settings.resolved_bgutil_script_home],
            }
            youtube_args["fetch_pot"] = ["always"]
            youtube_args["pot_trace"] = ["true"]

        extractor_args["youtube"] = youtube_args

    opts: dict[str, Any] = {
        "quiet": False,
        "verbose": True,
        "no_warnings": False,
        "ignoreerrors": False,
        "socket_timeout": 20,
        "geo_bypass": True,
        "extractor_args": extractor_args,
        "logger": YtDlpLogHandler(),
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

    if current_settings.resolved_cookiefile:
        opts["cookiefile"] = current_settings.resolved_cookiefile

    # Isolated Proxy Handling: Only assign YouTube proxy to YouTube requests
    if target_url:
        if is_youtube and current_settings.resolved_youtube_proxy:
            opts["proxy"] = current_settings.resolved_youtube_proxy
        elif not is_youtube and current_settings.resolved_global_proxy:
            opts["proxy"] = current_settings.resolved_global_proxy
    elif current_settings.resolved_proxy:
        opts["proxy"] = current_settings.resolved_proxy

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
    to attempt if extraction fails. Prioritizes clients compatible with
    active authentication / token providers.
    """
    return [
        ["visionos"],
        ["android"],
        ["tv"],
        ["mweb"],
        ["web"],
        ["ios"],
    ]
