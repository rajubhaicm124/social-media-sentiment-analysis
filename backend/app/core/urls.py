"""URL validation helpers shared by the API layer and platform detector."""

from __future__ import annotations

import re
from urllib.parse import urlparse, unquote

ALLOWED_SCHEMES = {"http", "https"}

# Reject obvious non-web schemes (javascript:, data:, file:) before parsing.
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")

ALLOWED_HOST_SUFFIXES = {
    "youtube": ("youtube.com", "youtu.be", "m.youtube.com", "music.youtube.com", "youtube-nocookie.com"),
    "facebook": ("facebook.com", "fb.watch", "fb.com", "m.facebook.com", "web.facebook.com", "fb.watch"),
    "instagram": ("instagram.com", "instagr.am", "ddinstagram.com"),
}


def clean_url(raw: str) -> str:
    """Trim whitespace, strip stray quotes, and add a scheme when missing."""
    if not isinstance(raw, str):
        raise ValueError("URL must be a string")
    value = raw.strip().strip("<>\"'")
    if not value:
        raise ValueError("URL is empty")
    if value.startswith("//"):
        value = f"https:{value}"
    elif not _SCHEME_RE.match(value):
        value = f"https://{value}"
    return value


def parse_url(raw: str):
    """Return a parsed URL or raise ``ValueError`` for anything unsafe."""
    candidate = clean_url(raw)
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError("Only http and https URLs are supported")
    host = (parsed.hostname or "").lower()
    if not host or "." not in host:
        raise ValueError("URL does not contain a valid hostname")
    if host in {"localhost", "127.0.0.1"}:
        raise ValueError("Local addresses are not supported")
    return parsed


def host_matches(host: str, platform: str) -> bool:
    host = host.lower()
    return any(host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_HOST_SUFFIXES[platform])


def normalize_host(host: str) -> str:
    return unquote(host or "").lower()
