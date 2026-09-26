"""Platform detection from a public social-media URL.

Supports YouTube, Facebook and Instagram. Additional platforms only need a new
entry in :data:`PLATFORM_SPECS` plus an adapter module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs

from app.core.errors import InvalidURLError, UnsupportedPlatformError
from app.core.urls import host_matches, parse_url

YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
INSTAGRAM_SHORTCODE_RE = re.compile(r"^[A-Za-z0-9_-]{5,64}$")
FACEBOOK_POST_ID_RE = re.compile(r"(?:posts|permalink|story\.php)[^0-9]{0,40}(\d{6,25})")


@dataclass(frozen=True)
class PlatformSpec:
    key: str
    label: str
    env_var: str
    url_examples: tuple[str, ...]
    documented_limitations: tuple[str, ...]


PLATFORM_SPECS: dict[str, PlatformSpec] = {
    "youtube": PlatformSpec(
        key="youtube",
        label="YouTube",
        env_var="YOUTUBE_API_KEY",
        url_examples=(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        ),
        documented_limitations=(
            "Share count is not exposed by the YouTube Data API v3 and is reported as unavailable.",
            "The comment API returns public comments only; removed, held-for-review and "
            "creator-hidden comments are not accessible.",
            "Comment pages are capped by the API quota cost, so very large comment "
            "sections are sampled rather than exhaustively downloaded.",
            "Channel subscriber counts are only returned for the authenticated owner's channel.",
            "Video tags are not returned by the Data API v3 for most videos.",
        ),
    ),
    "facebook": PlatformSpec(
        key="facebook",
        label="Facebook",
        env_var="FACEBOOK_ACCESS_TOKEN",
        url_examples=(
            "https://www.facebook.com/1234567890/posts/1234567890",
            "https://www.facebook.com/watch/?v=1234567890",
        ),
        documented_limitations=(
            "A Facebook Page access token with the required permissions is mandatory; "
            "public posts from personal profiles cannot be read through the Graph API.",
            "The Graph API returns Page and post insights only for content owned by the token's Page.",
            "Reaction breakdowns and post insights are only available for Page-owned content.",
            "Comment moderation status and private content are never exposed.",
        ),
    ),
    "instagram": PlatformSpec(
        key="instagram",
        label="Instagram",
        env_var="INSTAGRAM_ACCESS_TOKEN",
        url_examples=(
            "https://www.instagram.com/p/C1AbCdEfGhI/",
            "https://www.instagram.com/reel/C1AbCdEfGhI/",
        ),
        documented_limitations=(
            "Instagram Graph API media insights require a professional (Business or Creator) "
            "account linked to a Facebook Page.",
            "The Graph API cannot resolve an arbitrary public post by its shortcode; a media "
            "ID and an authorised account are required.",
            "Hashtag and mention impressions are restricted to the owning account.",
            "Comment text is only available for media owned by the authorised professional account.",
        ),
    ),
}

# Meta Graph API is shared by the Facebook and Instagram adapters.
META_SHARED_TOKEN_ENV = ("FACEBOOK_ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN")


def detect_platform(raw_url: str) -> str:
    """Return ``'youtube'`` | ``'facebook'`` | ``'instagram'``.

    Raises :class:`InvalidURLError` for malformed input and
    :class:`UnsupportedPlatformError` for valid URLs on unsupported hosts.
    """
    try:
        parsed = parse_url(raw_url)
    except ValueError as exc:
        raise InvalidURLError(f"{exc}. Please enter a valid YouTube, Facebook or Instagram URL.") from exc

    host = (parsed.hostname or "").lower()
    for key in ("youtube", "facebook", "instagram"):
        if host_matches(host, key):
            return key
    raise UnsupportedPlatformError(
        f"Unsupported social-media URL ({host}). SocialScope AI currently supports "
        "YouTube, Facebook and Instagram."
    )


def extract_youtube_id(parsed) -> str | None:
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    if host.endswith("youtu.be"):
        candidate = path.lstrip("/").split("/")[0]
        return candidate if YOUTUBE_ID_RE.match(candidate) else None
    if "shorts" in path or "embed" in path or "live" in path:
        candidate = path.strip("/").split("/")
        if len(candidate) >= 2 and YOUTUBE_ID_RE.match(candidate[1]):
            return candidate[1]
    values = parse_qs(parsed.query or "").get("v", [])
    if values and YOUTUBE_ID_RE.match(values[0]):
        return values[0]
    if path.rstrip("/").split("/")[-1:] and YOUTUBE_ID_RE.match(path.rstrip("/").split("/")[-1]):
        return path.rstrip("/").split("/")[-1]
    return None


def extract_instagram_shortcode(parsed) -> str | None:
    parts = [p for p in (parsed.path or "").split("/") if p]
    if not parts:
        return None
    kind, value = parts[0].lower(), parts[1] if len(parts) > 1 else None
    if kind in {"p", "reel", "reels", "tv", "share"} and value:
        candidate = value.split("?")[0]
        return candidate if INSTAGRAM_SHORTCODE_RE.match(candidate) else None
    return None


def extract_facebook_id(parsed) -> str | None:
    path = parsed.path or ""
    match = FACEBOOK_POST_ID_RE.search(path)
    if match:
        return match.group(1)
    query = parse_qs(parsed.query or "")
    for key in ("v", "story_fbid", "post_id"):
        values = query.get(key, [])
        if values and values[0].isdigit():
            return values[0]
    parts = [p for p in path.split("/") if p]
    for part in parts:
        if part.isdigit() and len(part) >= 6:
            return part
    return parts[0] if parts else None


def describe_platform(key: str) -> dict:
    spec = PLATFORM_SPECS[key]
    return {
        "key": spec.key,
        "label": spec.label,
        "credential_env_var": spec.env_var,
        "url_examples": list(spec.url_examples),
        "limitations": list(spec.documented_limitations),
    }
