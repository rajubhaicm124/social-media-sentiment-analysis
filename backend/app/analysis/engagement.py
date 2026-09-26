"""Engagement metric calculation.

Engagement rate is only computed when every input it needs was actually
supplied by the platform API. When views or shares are missing, the metric is
reported as unavailable instead of being derived from a substitute value.
"""

from __future__ import annotations

from typing import Any

UNAVAILABLE = "Data unavailable through the current platform API."


def _non_negative(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def compute_engagement(content: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return an engagement breakdown with explicit availability flags."""
    views = _non_negative(content.get("views"))
    likes = _non_negative(content.get("likes"))
    comments = _non_negative(content.get("comment_count"))
    shares = _non_negative(content.get("shares"))
    subscribers = _non_negative(content.get("subscribers"))

    interactions: list[str] = []
    if likes is not None:
        interactions.append("likes")
    if comments is not None:
        interactions.append("comments")
    if shares is not None:
        interactions.append("shares")

    total_interactions = (
        sum(v for v in (likes, comments, shares) if v is not None) if interactions else None
    )

    engagement_rate: float | None = None
    notes: list[str] = []
    if views and views > 0 and total_interactions is not None:
        engagement_rate = round(total_interactions / views * 100, 4)
        notes.append(
            f"Engagement rate = ({' + '.join(interactions)}) / views x 100. "
            "Likes and comments are included; shares are included only when the API returns them."
        )
    else:
        if views is None:
            notes.append(UNAVAILABLE + " View count was not returned for this content.")
        elif views == 0:
            notes.append("View count is zero, so an engagement rate cannot be calculated.")
        if not interactions:
            notes.append(UNAVAILABLE + " No interaction metrics were returned for this content.")

    interactions_per_comment: float | None = None
    analyzed = len([r for r in records if r.get("record_type") == "comment"])
    if analyzed and likes is not None:
        interactions_per_comment = round(likes / analyzed, 4)

    unavailable: list[str] = []
    for name, value in (
        ("views", views),
        ("likes", likes),
        ("comments", comments),
        ("shares", shares),
    ):
        if value is None:
            unavailable.append(name)

    return {
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "subscribers": subscribers,
        "total_interactions": total_interactions,
        "engagement_rate": engagement_rate,
        "engagement_rate_available": engagement_rate is not None,
        "interactions_included": interactions,
        "likes_per_analyzed_comment": interactions_per_comment,
        "analyzed_comments": analyzed,
        "unavailable_fields": unavailable,
        "notes": notes,
    }


def comment_engagement(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-comment engagement summary used by the engagement page."""
    liked = [r for r in records if isinstance(r.get("like_count"), (int, float))]
    values = [float(r["like_count"]) for r in liked]
    total = sum(values) if values else 0.0
    return {
        "comments_with_like_data": len(liked),
        "total_comment_likes": int(total),
        "avg_likes_per_comment": round(total / len(liked), 3) if liked else None,
        "likes_available": bool(liked),
    }
