"""Facebook (Meta Graph API) adapter.

The Graph API can only read posts that belong to a Page the configured access
token controls. Public posts on personal profiles are not readable, and this
adapter reports that honestly instead of substituting other data.
"""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.errors import (
    MissingCredentialsError,
    NoDataError,
    PlatformAPIError,
)
from app.core.urls import parse_url
from app.platforms.base import CollectedData, PlatformAdapter, availability
from app.platforms.detector import extract_facebook_id
from app.platforms.meta import graph_url, meta_token

COMMENT_FIELDS = "id,message,created_time,like_count,from,parent"


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class FacebookAdapter(PlatformAdapter):
    key = "facebook"
    label = "Facebook"
    credential_env_var = "FACEBOOK_ACCESS_TOKEN"

    def is_configured(self) -> bool:
        return bool(settings.facebook_access_token or settings.instagram_access_token)

    def collect(self, url: str) -> CollectedData:
        token = meta_token(settings.facebook_access_token)
        if not token:
            raise MissingCredentialsError("Facebook", self.credential_env_var)

        try:
            parsed = parse_url(url)
        except ValueError as exc:
            from app.core.errors import InvalidURLError

            raise InvalidURLError(str(exc)) from exc

        post_id = extract_facebook_id(parsed)
        if not post_id:
            raise PlatformAPIError(
                "Facebook",
                "a post or Page identifier could not be read from this link",
            )

        post = self._fetch_post(post_id, token)
        comments, truncated = self._fetch_comments(post_id, token)

        page = post.get("from") or {}
        reactions = to_int(post.get("reactions", {}).get("summary", {}).get("total_count"))
        shares = to_int(post.get("shares", {}).get("count"))

        content = {
            "content_id": post_id,
            "post_id": post_id,
            "page_id": page.get("id"),
            "page_name": page.get("name"),
            "author_name": page.get("name"),
            "title": (post.get("message") or post.get("name") or "")[:120] or None,
            "description": post.get("message") or post.get("story") or "",
            "caption": post.get("message") or "",
            "published_at": post.get("created_time"),
            "content_type": post.get("type") or "post",
            "thumbnail_url": post.get("picture"),
            "permalink": post.get("permalink_url"),
            "views": to_int(post.get("video_views")) if post.get("video_views") else None,
            "likes": reactions,
            "reactions": reactions,
            "comment_count": to_int(post.get("comments_count")) if post.get("comments_count") is not None else (len(comments) or None),
            "shares": shares,
        }

        records: list[dict[str, Any]] = []
        if content["caption"].strip():
            records.append(
                {
                    "record_type": "caption",
                    "comment_id": f"caption:{post_id}",
                    "author_id": page.get("id"),
                    "author_name": page.get("name"),
                    "raw_text": content["caption"],
                    "published_at": content["published_at"],
                    "like_count": None,
                    "reply_count": None,
                }
            )
        records.extend(comments)

        available = ["caption", "published_at", "author"]
        if content["thumbnail_url"]:
            available.append("thumbnail")
        for name in ("views", "likes", "comments", "shares"):
            if content.get(name) is not None:
                available.append(name)
        present, missing = availability(available)

        notes = [
            "Facebook Graph API access requires a Page token; posts on personal profiles are not readable.",
            "Reaction counts returned by the API already aggregate the selected reaction types.",
        ]
        if truncated:
            notes.append("Only the first page of comments was retrieved within the configured limit.")
        if not records:
            raise NoDataError(
                "No public comments were available for this post. The Graph API returns comments "
                "only for Page-owned content that the access token can manage."
            )

        return CollectedData(
            platform=self.key,
            content=content,
            records=records,
            available_fields=present,
            unavailable_fields=missing,
            notes=notes,
            provenance={
                "api": f"Meta Graph API {settings.meta_api_version}",
                "post_id": post_id,
                "endpoints": [f"GET /{post_id}", f"GET /{post_id}/comments"],
                "data_mode": "live",
            },
        )

    # -- internals --------------------------------------------------------
    def _fetch_post(self, post_id: str, token: str) -> dict[str, Any]:
        fields = (
            "id,message,story,created_time,from,permalink_url,picture,type,"
            "reactions.limit(0),shares,comments_count,video_views"
        )
        payload = self.api_get(graph_url(post_id), params={"fields": fields, "access_token": token})
        if not payload.get("id"):
            raise PlatformAPIError(
                "Facebook",
                "the post is not accessible with the configured Page token",
            )
        return payload

    def _fetch_comments(self, post_id: str, token: str) -> tuple[list[dict[str, Any]], bool]:
        payload = self.api_get(
            graph_url(f"{post_id}/comments"),
            params={"fields": COMMENT_FIELDS, "limit": 100, "access_token": token},
        )
        records: list[dict[str, Any]] = []
        for item in payload.get("data", []) or []:
            author = item.get("from") or {}
            records.append(
                {
                    "record_type": "comment",
                    "comment_id": item.get("id"),
                    "parent_id": item.get("parent", {}).get("id") if isinstance(item.get("parent"), dict) else item.get("parent"),
                    "author_id": author.get("id"),
                    "author_name": author.get("name"),
                    "raw_text": item.get("message", "") or "",
                    "published_at": item.get("created_time"),
                    "like_count": to_int(item.get("like_count")),
                    "reply_count": None,
                }
            )
        cursors = ((payload.get("paging") or {}).get("next") or {}).get("cursors")
        return records, bool(cursors)
