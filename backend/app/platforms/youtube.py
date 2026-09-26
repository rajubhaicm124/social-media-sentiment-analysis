"""YouTube Data API v3 adapter.

Only fields documented by the YouTube Data API are collected. Notably, the API
does not expose a share count, so ``shares`` is always reported as unavailable.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.core.errors import InvalidURLError, MissingCredentialsError, NoDataError
from app.core.urls import parse_url
from app.platforms.base import CollectedData, PlatformAdapter, availability
from app.platforms.detector import extract_youtube_id

API_BASE = "https://www.googleapis.com/youtube/v3"
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

VIDEO_PARTS = "snippet,statistics,contentDetails,status"
COMMENT_PARTS = "snippet"


def _iso_to_iso(iso: str) -> str:
    """Convert YouTube's RFC3339 timestamp into a stable ISO-8601 UTC string."""
    if not iso:
        return ""
    if ISO_RE.match(iso):
        cleaned = iso.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(cleaned)
            return parsed.astimezone(timezone.utc).isoformat()
        except ValueError:
            return iso
    return iso


def parse_duration(value: str | None) -> tuple[int | None, str | None]:
    """Parse an ISO-8601 duration such as ``PT4M13S`` into seconds + display."""
    if not value:
        return None, None
    match = re.fullmatch(
        r"P(?:(?P<d>\d+)D)?T?(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?", value
    )
    if not match:
        return None, None
    parts = {k: int(v) for k, v in match.groupdict(default="0").items() if v}
    seconds = parts.get("d", 0) * 86400 + parts.get("h", 0) * 3600 + parts.get("m", 0) * 60 + parts.get("s", 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    display = f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"
    return seconds, display


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class YouTubeAdapter(PlatformAdapter):
    key = "youtube"
    label = "YouTube"
    credential_env_var = "YOUTUBE_API_KEY"

    def is_configured(self) -> bool:
        return bool(settings.youtube_api_key)

    # -- collection -------------------------------------------------------
    def collect(self, url: str) -> CollectedData:
        if not self.is_configured():
            raise MissingCredentialsError("YouTube", self.credential_env_var)

        try:
            parsed = parse_url(url)
        except ValueError as exc:
            raise InvalidURLError(str(exc)) from exc

        video_id = extract_youtube_id(parsed)
        if not video_id:
            raise InvalidURLError(
                "This YouTube link does not point to a single video. SocialScope AI analyses "
                "one video at a time — open a watch, youtu.be or Shorts link and try again."
            )

        video = self._fetch_video(video_id)
        comments, comment_pages, comments_truncated = self._fetch_comments(video_id)

        snippet = video.get("snippet", {}) or {}
        statistics = video.get("statistics", {}) or {}
        content_details = video.get("contentDetails", {}) or {}

        duration_seconds, duration_display = parse_duration(content_details.get("duration"))
        thumbnails = snippet.get("thumbnails", {}) or {}
        thumbnail = (
            thumbnails.get("maxres", {}).get("url")
            or thumbnails.get("standard", {}).get("url")
            or thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url")
        )
        description = snippet.get("description", "") or ""

        content = {
            "content_id": video_id,
            "video_id": video_id,
            "channel_id": snippet.get("channelId"),
            "channel_name": snippet.get("channelTitle"),
            "title": snippet.get("title"),
            "description": description,
            "published_at": _iso_to_iso(snippet.get("publishedAt", "")),
            "category_id": snippet.get("categoryId"),
            "language": (snippet.get("defaultLanguage") or None),
            "thumbnail_url": thumbnail,
            "duration_seconds": duration_seconds,
            "duration": duration_display,
            "views": to_int(statistics.get("viewCount")),
            "likes": to_int(statistics.get("likeCount")),
            "comment_count": to_int(statistics.get("commentCount")),
            # The YouTube Data API v3 exposes no share count.
            "shares": None,
            "embeddable": (video.get("status", {}) or {}).get("embeddable"),
            "made_for_kids": (video.get("status", {}) or {}).get("madeForKids"),
        }

        tags = self._fetch_tags(video_id, description)
        if tags:
            content["tags"] = tags
            content["hashtags"] = [t.lstrip("#") for t in re.findall(r"#\w+", description)]

        records: list[dict[str, Any]] = []
        if description.strip():
            records.append(
                {
                    "record_type": "caption",
                    "comment_id": f"caption:{video_id}",
                    "author_id": snippet.get("channelId"),
                    "author_name": snippet.get("channelTitle"),
                    "raw_text": description,
                    "published_at": content["published_at"],
                    "like_count": None,
                    "reply_count": None,
                }
            )
        records.extend(comments)

        available = ["caption", "published_at", "author", "thumbnail"]
        if content["views"] is not None:
            available.append("views")
        if content["likes"] is not None:
            available.append("likes")
        if content["comment_count"] is not None:
            available.append("comments")
        if duration_seconds is not None:
            available.append("duration")
        if tags:
            available.append("tags")
        if thumbnail:
            available.append("thumbnail")
        present, missing = availability(available)

        notes = [
            "Shares are not exposed by the YouTube Data API v3 and are reported as unavailable.",
            f"{len(comments)} public comment(s) retrieved across {comment_pages} API page(s).",
        ]
        if comments_truncated:
            notes.append(
                "The comment section is larger than the configured page limit, so comments were "
                "sampled. Increase MAX_COMMENT_PAGES to widen the sample (subject to quota)."
            )
        if not records:
            raise NoDataError(
                "No public comments were available for this video. Videos with comments disabled "
                "return an empty commentThreads response from the API."
            )

        return CollectedData(
            platform=self.key,
            content=content,
            records=records,
            available_fields=present,
            unavailable_fields=missing,
            notes=notes,
            provenance={
                "api": "YouTube Data API v3",
                "video_id": video_id,
                "endpoints": [
                    f"GET /videos?part={VIDEO_PARTS}&id={video_id}",
                    f"GET /commentThreads?part={COMMENT_PARTS}&videoId={video_id}&maxResults={settings.comments_per_page}",
                ],
                "data_mode": "live",
            },
        )

    # -- internals --------------------------------------------------------
    def _fetch_video(self, video_id: str) -> dict[str, Any]:
        payload = self.api_get(
            f"{API_BASE}/videos",
            params={
                "part": VIDEO_PARTS,
                "id": video_id,
                "key": settings.youtube_api_key,
                "maxResults": 1,
            },
        )
        items = payload.get("items") or []
        if not items:
            from app.core.errors import PlatformAPIError

            raise PlatformAPIError(
                "YouTube",
                "the video is private, removed, or does not exist",
            )
        return items[0]

    def _fetch_tags(self, video_id: str, description: str) -> list[str]:
        """Read the ``tags`` snippet, falling back to hashtags in the description."""
        payload = self.api_get(
            f"{API_BASE}/videos",
            params={"part": "snippet", "id": video_id, "key": settings.youtube_api_key},
        )
        items = payload.get("items") or []
        tags = ((items[0].get("snippet", {}) or {}).get("tags")) if items else None
        if tags:
            return list(tags)
        return [t for t in re.findall(r"#(\w+)", description or "")]

    def _fetch_comments(
        self, video_id: str
    ) -> tuple[list[dict[str, Any]], int, bool]:
        records: list[dict[str, Any]] = []
        pages = 0
        truncated = False
        token: str | None = None
        max_pages = max(1, settings.max_comment_pages)

        while pages < max_pages:
            params: dict[str, Any] = {
                "part": COMMENT_PARTS,
                "videoId": video_id,
                "maxResults": min(100, settings.comments_per_page),
                "textFormat": "plainText",
                "key": settings.youtube_api_key,
            }
            if token:
                params["pageToken"] = token
            payload = self.api_get(f"{API_BASE}/commentThreads", params=params)
            pages += 1

            for item in payload.get("items", []) or []:
                record = self._thread_to_record(item)
                if record:
                    records.append(record)

            token = payload.get("nextPageToken")
            if not token:
                break
        else:
            truncated = bool(token)

        return records, pages, truncated

    @staticmethod
    def _thread_to_record(item: dict[str, Any]) -> dict[str, Any] | None:
        snippet = ((item.get("snippet") or {}).get("topLevelComment") or {}).get("snippet") or {}
        if not snippet:
            return None
        record: dict[str, Any] = {
            "record_type": "comment",
            "comment_id": snippet.get("commentId") or item.get("id"),
            "parent_id": snippet.get("parentId"),
            "author_id": snippet.get("authorChannelId", {}).get("value")
            if isinstance(snippet.get("authorChannelId"), dict)
            else None,
            "author_name": snippet.get("authorDisplayName"),
            "raw_text": snippet.get("textDisplay", "") or "",
            "published_at": _iso_to_iso(snippet.get("publishedAt", "")),
            # totalReplyCount is exposed; likeCount is only present when the
            # viewer owns the video or when the API grants the 'mine' context.
            "reply_count": snippet.get("totalReplyCount"),
            "like_count": snippet.get("likeCount"),
            "is_author": bool(snippet.get("authorIsChannelOwner")),
        }
        return record
