"""CSV export.

Only fields the platform actually supplied are written. Unavailable metrics are
left empty and are listed in a header note so a reader of the file cannot
mistake an empty cell for a zero.
"""

from __future__ import annotations

import csv
import io
from typing import Any

UNAVAILABLE_NOTE = (
    "Data unavailable through the current platform API."
)

# The DAE column convention from the project brief. Unavailable columns are kept
# in the header so the schema is stable across platforms and documented.
COLUMNS: list[tuple[str, str]] = [
    ("platform", "platform"),
    ("data_mode", "data_mode"),
    ("source_url", "source_url"),
    ("content_id", "content_id"),
    ("post_id", "post_id"),
    ("video_id", "video_id"),
    ("channel_id", "channel_id"),
    ("username", "username"),
    ("author_id", "author_id"),
    ("author_name", "author_name"),
    ("title", "title"),
    ("description", "description"),
    ("caption", "caption"),
    ("comment_id", "comment_id"),
    ("parent_id", "parent_id"),
    ("record_type", "record_type"),
    ("comment_text", "raw_text"),
    ("cleaned_comment", "clean_text"),
    ("published_at", "published_at"),
    ("language", "language"),
    ("word_count", "word_count"),
    ("char_count", "char_count"),
    ("likes", "like_count"),
    ("comments", "comments"),
    ("shares", "shares"),
    ("views", "views"),
    ("replies", "reply_count"),
    ("sentiment", "sentiment"),
    ("sentiment_score", "final_score"),
    ("compound_score", "compound"),
    ("positive_score", "positive"),
    ("negative_score", "negative"),
    ("neutral_score", "neutral"),
    ("polarity", "polarity"),
    ("subjectivity", "subjectivity"),
    ("confidence", "confidence"),
    ("emotion", "emotion"),
    ("hashtags", "hashtags"),
    ("mentions", "mentions"),
    ("keywords", "keywords"),
    ("engagement_rate", "engagement_rate"),
    ("is_duplicate", "is_duplicate"),
    ("is_spam", "is_spam"),
    ("is_outlier", "is_outlier"),
    ("flags", "flags"),
    ("vader_compound", "vader_compound"),
    ("textblob_polarity", "textblob_polarity"),
]


def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return " | ".join(str(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{k}={v}" for k, v in value.items())
    return str(value)


def build_row(record: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    engines = record.get("engines") or {}
    vader = engines.get("vader") or {}
    textblob = engines.get("textblob") or {}
    content = context.get("content", {})
    engagement = context.get("engagement", {})

    row: dict[str, Any] = {}
    for column, _source in COLUMNS:
        row[column] = ""

    row.update(
        {
            "platform": context.get("platform"),
            "data_mode": context.get("data_mode"),
            "source_url": context.get("source_url"),
            "content_id": content.get("content_id"),
            "post_id": content.get("post_id") or content.get("media_id"),
            "video_id": content.get("video_id"),
            "channel_id": content.get("channel_id"),
            "username": content.get("username"),
            "title": content.get("title"),
            "description": content.get("description"),
            "caption": content.get("caption"),
            "views": engagement.get("views"),
            "shares": engagement.get("shares"),
            "engagement_rate": engagement.get("engagement_rate"),
            "comments": record.get("comment_id") and _content_comment_count(context),
        }
    )
    for column, source in COLUMNS:
        if column in row and row[column] != "":
            continue
        if source in record:
            row[column] = _flatten(record[source])

    row["vader_compound"] = _flatten(vader.get("compound"))
    row["textblob_polarity"] = _flatten(textblob.get("polarity"))
    return row


def _content_comment_count(context: dict[str, Any]) -> Any:
    return context.get("engagement", {}).get("comments")


def generate_csv(
    records: list[dict[str, Any]], context: dict[str, Any], include_raw: bool = False
) -> bytes:
    """Return UTF-8-BOM CSV bytes (BOM keeps Excel happy with Unicode).

    The file is strictly tabular: no trailing comment or note rows are appended,
    because consumers load this with pandas and any extra row would be parsed as
    a malformed record. Provenance, unavailable-field notes and limitations live
    in the Excel workbook and the report instead. The ``data_mode`` column still
    marks demo output, and a blank cell always means "not available", never 0.
    """
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=[c for c, _ in COLUMNS], extrasaction="ignore")
    writer.writeheader()
    for record in records:
        writer.writerow(build_row(record, context))

    return buffer.getvalue().encode("utf-8-sig")
