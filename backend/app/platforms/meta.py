"""Meta Graph API helpers shared by the Facebook and Instagram adapters."""

from __future__ import annotations

from typing import Any

from app.config import settings


def graph_base() -> str:
    return f"https://graph.facebook.com/{settings.meta_api_version}"


def graph_url(path: str) -> str:
    return f"{graph_base()}/{path.lstrip('/')}"


def meta_token(preferred: str | None) -> str | None:
    """Return the first configured Meta token (never logged, never returned)."""
    return preferred or settings.facebook_access_token or settings.instagram_access_token


def flatten_meta_error(payload: dict[str, Any]) -> str | None:
    error = payload.get("error")
    if not error:
        return None
    if isinstance(error, dict):
        return str(error.get("message") or error.get("type") or "Meta API error")
    return str(error)


def wrap_media(media: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Graph API media object into SocialScope content fields."""
    return {
        "content_id": media.get("id"),
        "caption": media.get("caption") or media.get("message") or "",
        "published_at": media.get("timestamp") or media.get("created_time"),
        "media_type": media.get("media_type") or media.get("type"),
        "thumbnail_url": media.get("thumbnail_url") or media.get("picture"),
        "permalink": media.get("permalink"),
        "username": (media.get("from") or {}).get("username"),
    }
