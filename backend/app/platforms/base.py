"""Platform adapter contract.

An adapter's only job is to fetch data that the platform's official API
actually exposes, and to report which fields were available. It must never
invent, infer, or estimate a metric.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import settings
from app.core.errors import PlatformAPIError

# Fields SocialScope AI would like to report. An adapter declares which of these
# the platform API can supply; the rest are surfaced as "unavailable".
TARGET_FIELDS = (
    "views",
    "likes",
    "comments",
    "shares",
    "caption",
    "published_at",
    "author",
    "thumbnail",
    "tags",
    "duration",
    "subscribers",
)


@dataclass
class CollectedData:
    """Normalized result of one successful collection."""

    platform: str
    content: dict[str, Any] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)
    available_fields: list[str] = field(default_factory=list)
    unavailable_fields: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)


class PlatformAdapter(ABC):
    """Base class for all platform adapters."""

    key: str = ""
    label: str = ""
    credential_env_var: str = ""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    @property
    def http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=settings.request_timeout_seconds,
                follow_redirects=True,
                headers={"User-Agent": "SocialScopeAI/1.0 (+DAE academic project)"},
            )
        return self._client

    def close(self) -> None:
        if self._client is not None and self._owns_client:
            self._client.close()
            self._client = None

    # -- API helpers ------------------------------------------------------
    def api_get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """GET a JSON API endpoint and translate failures into friendly errors."""
        try:
            response = self.http.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise PlatformAPIError(self.label, "request timed out") from exc
        except httpx.HTTPError as exc:
            raise PlatformAPIError(self.label, "network error") from exc

        if response.status_code == 429:
            from app.core.errors import RateLimitError

            raise RateLimitError(
                f"{self.label} API request limit reached. Please wait and try again."
            )
        if response.status_code in (401, 403):
            raise PlatformAPIError(
                self.label, "the request was rejected — check the API key, permissions and quota"
            )
        if response.status_code == 404:
            raise PlatformAPIError(
                self.label, "the content is private, deleted, or not accessible with this API"
            )
        if response.status_code >= 500:
            raise PlatformAPIError(self.label, f"upstream error {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise PlatformAPIError(self.label, "the API returned an unreadable response") from exc

        error = payload.get("error")
        if error:
            reason = error.get("message") or error.get("status") or "unknown API error"
            raise PlatformAPIError(self.label, str(reason))
        return payload

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether live collection is possible with the current environment."""

    @abstractmethod
    def collect(self, url: str) -> CollectedData:
        """Fetch all officially available public data for ``url``."""


def availability(available: list[str], extra_notes: list[str] | None = None) -> tuple[list[str], list[str]]:
    """Split TARGET_FIELDS into available/unavailable lists."""
    available_set = set(available)
    present = [f for f in TARGET_FIELDS if f in available_set]
    missing = [f for f in TARGET_FIELDS if f not in available_set]
    return present, missing
