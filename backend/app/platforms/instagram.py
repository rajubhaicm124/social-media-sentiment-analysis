"""Instagram (Meta Graph API) adapter.

Instagram media insights require a professional (Business/Creator) account
linked to a Facebook Page. The Graph API cannot resolve an arbitrary public
post shortcode, so this adapter reports that limitation explicitly and
requires the media identifier to belong to the authorised account.
"""

from __future__ import annotations

import re
from typing import Any

from app.config import settings
from app.core.errors import (
    MissingCredentialsError,
    NoDataError,
    PlatformAPIError,
)
from app.core.urls import parse_url
from app.platforms.base import CollectedData, PlatformAdapter, availability
from app.platforms.detector import extract_instagram_shortcode
from app.platforms.meta import graph_url, meta_token

COMMENT_FIELDS = "id,text,timestamp,username,like_count,media{id}"
HASHTAG_RE = re.compile(r"#(\w+)")


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class InstagramAdapter(PlatformAdapter):
    key = "instagram"
    label = "Instagram"
    credential_env_var = "INSTAGRAM_ACCESS_TOKEN"

    def is_configured(self) -> bool:
        return bool(settings.instagram_access_token or settings.facebook_access_token)

    def collect(self, url: str) -> CollectedData:
        token = meta_token(settings.instagram_access_token)
        if not token:
            raise MissingCredentialsError("Instagram", self.credential_env_var)

        try:
            parsed = parse_url(url)
        except ValueError as exc:
            from app.core.errors import InvalidURLError

            raise InvalidURLError(str(exc)) from exc

        shortcode = extract_instagram_shortcode(parsed)
        if not shortcode:
            raise PlatformAPIError(
                "Instagram",
                "a post, reel or TV shortcode could not be read from this link",
            )

        media = self._resolve_media(shortcode, token)
        comments, truncated = self._fetch_comments(media["id"], token)
        insights = self._fetch_insights(media["id"], token)

        caption = media.get("caption") or ""
        content = {
            "content_id": media["id"],
            "media_id": media["id"],
            "shortcode": shortcode,
            "username": media.get("username") or media.get("owner"),
            "author_name": media.get("username") or media.get("owner"),
            "caption": caption,
            "description": caption,
            "published_at": media.get("timestamp"),
            "media_type": media.get("media_type"),
            "thumbnail_url": media.get("media_url") or media.get("thumbnail_url"),
            "permalink": media.get("permalink"),
            "views": to_int(insights.get("views")),
            "reach": to_int(insights.get("reach")),
            "impressions": to_int(insights.get("impressions")),
            "likes": to_int(media.get("like_count")),
            "comment_count": to_int(media.get("comments_count")),
            # The Graph API does not expose a public share count for media.
            "shares": None,
            "hashtags": HASHTAG_RE.findall(caption),
        }

        records: list[dict[str, Any]] = []
        if caption.strip():
            records.append(
                {
                    "record_type": "caption",
                    "comment_id": f"caption:{media['id']}",
                    "author_id": media.get("owner"),
                    "author_name": media.get("username") or media.get("owner"),
                    "raw_text": caption,
                    "published_at": content["published_at"],
                    "like_count": None,
                    "reply_count": None,
                }
            )
        records.extend(comments)

        available = ["caption", "published_at", "author"]
        if content["thumbnail_url"]:
            available.append("thumbnail")
        for name in ("views", "likes", "comments"):
            if content.get(name) is not None:
                available.append(name)
        present, missing = availability(available)

        notes = [
            "Instagram insights require a professional account linked to a Facebook Page.",
            "Share count is not exposed by the Instagram Graph API and is reported as unavailable.",
        ]
        if truncated:
            notes.append("Only the first page of comments was retrieved within the configured limit.")
        if not records:
            raise NoDataError(
                "No public comments were available for this media. The Graph API returns comments "
                "only for media owned by the authorised professional account."
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
                "media_id": media["id"],
                "endpoints": [f"GET /{media['id']}?fields=comments", f"GET /{media['id']}/insights"],
                "data_mode": "live",
            },
        )

    # -- internals --------------------------------------------------------
    def _resolve_media(self, shortcode: str, token: str) -> dict[str, Any]:
        """Resolve the shortcode to a media id owned by the authorised account.

        The Graph API exposes ``GET /{ig-user-id}/media`` for the authorised
        account, so the shortcode is matched against that list. If the media is
        not owned by the account, the limitation is reported instead of guessed.
        """
        account_id = settings.instagram_account_id or self._lookup_ig_user(token)
        if not account_id:
            raise PlatformAPIError(
                "Instagram",
                "no Instagram professional account is linked to this access token; "
                "set INSTAGRAM_ACCOUNT_ID in backend/.env",
            )

        payload = self.api_get(
            graph_url(f"{account_id}/media"),
            params={
                "fields": "id,caption,media_type,media_url,permalink,timestamp,username,like_count,comments_count,owner",
                "username": True,
                "limit": 100,
                "access_token": token,
            },
        )
        items = payload.get("data", []) or []
        if not items:
            raise NoDataError(
                "The authorised Instagram account has no public media to analyse. "
                "The Instagram Graph API only exposes media owned by the linked professional account."
            )
        for item in items:
            permalink = item.get("permalink") or ""
            if f"/{shortcode}/" in permalink or permalink.rstrip("/").endswith(f"/{shortcode}"):
                return item
        raise PlatformAPIError(
            "Instagram",
            f"media '{shortcode}' is not owned by the authorised account, so the Instagram "
            "Graph API cannot return it",
        )

    def _lookup_ig_user(self, token: str) -> str | None:
        try:
            payload = self.api_get(
                graph_url("me/accounts"),
                params={"fields": "instagram_business_account{id,username}", "access_token": token},
            )
        except PlatformAPIError:
            return None
        for page in payload.get("data", []) or []:
            ig = page.get("instagram_business_account")
            if isinstance(ig, dict) and ig.get("id"):
                return ig["id"]
        return None

    def _fetch_insights(self, media_id: str, token: str) -> dict[str, Any]:
        """Media insights are optional; unavailable metrics simply stay None."""
        try:
            payload = self.api_get(
                graph_url(f"{media_id}/insights"),
                params={"metric": "reach,views,impressions", "access_token": token},
            )
        except PlatformAPIError:
            return {}
        metrics = {
            item.get("name"): item.get("values", [{}])[0].get("value")
            for item in payload.get("data", []) or []
        }
        return {k: v for k, v in metrics.items() if v is not None}

    def _fetch_comments(self, media_id: str, token: str) -> tuple[list[dict[str, Any]], bool]:
        payload = self.api_get(
            graph_url(f"{media_id}/comments"),
            params={"fields": COMMENT_FIELDS, "limit": 100, "access_token": token},
        )
        records: list[dict[str, Any]] = []
        for item in payload.get("data", []) or []:
            records.append(
                {
                    "record_type": "comment",
                    "comment_id": item.get("id"),
                    "parent_id": None,
                    "author_id": item.get("username"),
                    "author_name": item.get("username"),
                    "raw_text": item.get("text", "") or "",
                    "published_at": item.get("timestamp"),
                    "like_count": to_int(item.get("like_count")),
                    "reply_count": None,
                }
            )
        cursors = ((payload.get("paging") or {}).get("next") or {}).get("cursors")
        return records, bool(cursors)
