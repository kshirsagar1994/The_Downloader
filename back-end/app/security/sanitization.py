import re
import unicodedata

RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filename(name: str, default_name: str = "media_download") -> str:
    """
    Sanitizes user-provided or extracted media titles for cross-platform filesystem safety.
    Prevents path traversal, null-byte injection, and reserved OS filenames.
    """
    if not name or not isinstance(name, str):
        return default_name

    # Normalize unicode characters
    normalized = unicodedata.normalize("NFKD", name)

    # Replace forbidden path, shell metacharacters, and control characters with an underscore
    sanitized = re.sub(r'[\/\\:\*\?"<>\|\x00-\x1f;&\$`\(\)\{\}]', '_', normalized)

    # Remove repeated underscores / whitespace
    sanitized = re.sub(r'[\s_]+', '_', sanitized)

    # Strip leading/trailing dots and underscores
    sanitized = sanitized.strip('._ ')

    if not sanitized:
        sanitized = default_name

    # Check for reserved Windows filenames
    base_name = sanitized.split(".")[0].upper()
    if base_name in RESERVED_WINDOWS_NAMES:
        sanitized = f"file_{sanitized}"

    # Enforce safe byte length limit (max 200 bytes for filename base)
    encoded = sanitized.encode("utf-8")
    if len(encoded) > 200:
        sanitized = encoded[:200].decode("utf-8", "ignore")

    return sanitized


def sanitize_extension(ext: str, default_ext: str = "mp4") -> str:
    """Sanitizes file extension."""
    if not ext:
        return default_ext
    clean = re.sub(r"[^a-zA-Z0-9]", "", ext.lower().strip("."))
    return clean if clean else default_ext
