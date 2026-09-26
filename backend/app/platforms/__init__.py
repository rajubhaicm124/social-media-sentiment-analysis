"""Platform adapter registry.

Adding a platform means: create a module with a :class:`PlatformAdapter`
subclass, add an entry to :data:`PLATFORM_SPECS` in ``detector.py``, and
register it here. No other layer changes.
"""

from __future__ import annotations

from app.platforms.base import CollectedData, PlatformAdapter
from app.platforms.detector import PLATFORM_SPECS, describe_platform, detect_platform
from app.platforms.facebook import FacebookAdapter
from app.platforms.instagram import InstagramAdapter
from app.platforms.youtube import YouTubeAdapter

ADAPTERS: dict[str, type[PlatformAdapter]] = {
    "youtube": YouTubeAdapter,
    "facebook": FacebookAdapter,
    "instagram": InstagramAdapter,
}

SUPPORTED_PLATFORMS = tuple(ADAPTERS)


def get_adapter(platform: str) -> PlatformAdapter:
    try:
        return ADAPTERS[platform]()
    except KeyError as exc:
        raise ValueError(f"Unsupported platform: {platform}") from exc


def collect(platform: str, url: str) -> CollectedData:
    adapter = get_adapter(platform)
    try:
        return adapter.collect(url)
    finally:
        adapter.close()


__all__ = [
    "ADAPTERS",
    "SUPPORTED_PLATFORMS",
    "PLATFORM_SPECS",
    "CollectedData",
    "PlatformAdapter",
    "collect",
    "describe_platform",
    "detect_platform",
    "get_adapter",
]
