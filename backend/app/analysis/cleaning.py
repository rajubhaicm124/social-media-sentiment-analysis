"""Data cleaning and normalization pipeline.

Produces two datasets from the collected records:

* **RAW**  — exactly what the platform API returned (preserved untouched).
* **CLEAN** — deduplicated, de-spammed, text-normalized and typed records that
  the statistical and sentiment stages operate on.

Every removal is counted and labelled so the dashboard can show how many rows
the pipeline dropped and why. Nothing is silently discarded.
"""

from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"[@](\w[\w.]*)")
HASHTAG_RE = re.compile(r"#(\w[\w_]*)")
EMOJI_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F1E6-\U0001F1FF" "]"
)
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
CONTROL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
REPEAT_CHAR_RE = re.compile(r"(.)\1{4,}")
ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")

# Tokens that carry no analytical value in a comment corpus.
STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren as at be because been before being
    below between both but by can cannot could couldn did didn do does doesn doing don down during
    each few for from further had hadn has hasn have haven having he her here hers herself him
    himself his how i if in into is isn it its itself let me more most mustn my myself no nor not of
    off on once only or other ought our ours ourselves out over own same shan she should shouldn so
    some such than that the their theirs them themselves then there these they this those through to
    too under until up very was wasn we were weren what when where which while who whom why with won
    would wouldn you your yours yourself yourselves im ive dont thats really just get got like know
    think want going one two also make made much many lot bit thing things people way well back even
    still us
    """.split()
)

SPAM_PATTERNS = (
    re.compile(r"(.)\1{6,}", re.IGNORECASE),          # aaaaaaa
    re.compile(r"\b(viagra|casino|crypto\s*giveaway)\b", re.IGNORECASE),
    re.compile(r"https?://\S+.*https?://\S+", re.IGNORECASE),  # link stuffing
    re.compile(r"^\W*$"),                             # punctuation only
)


def detect_language(text: str) -> str:
    """Very small heuristic language tag.

    Deliberately dependency-free; the UI labels it as a heuristic, not a
    certified language identification result.
    """
    if not text:
        return "und"
    lowered = text.lower()
    markers = {
        "es": (" el ", " la ", " que ", " de ", " muy ", " gracias ", " esto "),
        "fr": (" le ", " la ", " est ", " très ", " merci ", " une "),
        "de": (" der ", " die ", " das ", " und ", " nicht ", " ich "),
        "pt": (" você ", " não ", " muito ", " obrigado ", " esta "),
        "hi": (" है ", " और ", " यह ", " नहीं "),
    }
    padded = f" {lowered} "
    for code, tokens in markers.items():
        if sum(1 for token in tokens if token in padded) >= 2:
            return code
    return "en"


def normalize_whitespace(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def clean_text_for_nlp(text: str) -> str:
    """Aggressive cleaning used only as sentiment input.

    URLs and mentions are removed because they add no sentiment signal and
    would otherwise dominate token-based scoring.
    """
    value = HTML_TAG_RE.sub(" ", text or "")
    value = html.unescape(value)
    value = URL_RE.sub(" ", value)
    value = MENTION_RE.sub(r"\1", value)
    value = HASHTAG_RE.sub(r"\1", value)
    value = EMOJI_RE.sub(" ", value)
    value = ZERO_WIDTH_RE.sub("", value)
    value = CONTROL_RE.sub("", value)
    value = REPEAT_CHAR_RE.sub(r"\1\1", value)
    return normalize_whitespace(value)


def normalize_timestamp(value: Any) -> str | None:
    """Coerce assorted timestamp formats into ISO-8601 UTC, or ``None``."""
    if value in (None, "", 0):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).isoformat()
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return normalize_timestamp(int(text))
    candidate = text.replace("Z", "+00:00")
    for parser in (
        lambda s: datetime.fromisoformat(s),
        lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z"),
        lambda s: datetime.strptime(s, "%Y-%m-%d %H:%M:%S"),
        lambda s: datetime.strptime(s, "%Y-%m-%d"),
    ):
        try:
            parsed = parser(candidate)
        except (ValueError, TypeError):
            continue
        moment = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).isoformat()
    return None


def to_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[,\s]", "", text)
    multiplier = 1
    if text and text[-1] in "KkMm":
        multiplier = {"k": 1_000, "m": 1_000_000}[text[-1].lower()]
        text = text[:-1]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return None


def extract_hashtags(text: str) -> list[str]:
    seen: list[str] = []
    for tag in HASHTAG_RE.findall(text or ""):
        lowered = tag.lower()
        if lowered not in [s.lower() for s in seen]:
            seen.append(tag)
    return seen


def extract_mentions(text: str) -> list[str]:
    return list(dict.fromkeys(MENTION_RE.findall(text or "")))


def looks_like_spam(text: str) -> bool:
    stripped = (text or "").strip()
    if len(stripped) < 2:
        return True
    if URL_RE.search(stripped):
        # A comment that is nothing but a link carries no analysable text.
        remainder = URL_RE.sub("", stripped).strip()
        if not content_tokens(remainder):
            return True
    return any(pattern.search(stripped) for pattern in SPAM_PATTERNS)


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z']{2,}", (text or "").lower())]


def content_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if t not in STOPWORDS and not t.isdigit()]


def clean_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the full cleaning pipeline over collected records."""
    report = {
        "input_count": len(records),
        "removed_empty": 0,
        "removed_duplicate": 0,
        "removed_spam": 0,
        "invalid_dates": 0,
        "output_count": 0,
        "steps": [],
    }
    report["steps"].append({"step": "1. Validate records", "detail": f"{len(records)} record(s) received"})

    seen_ids: set[str] = set()
    seen_texts: dict[str, str] = {}
    cleaned: list[dict[str, Any]] = []

    for record in records:
        raw_text = (record.get("raw_text") or "").strip()
        if not raw_text:
            report["removed_empty"] += 1
            continue

        comment_id = str(record.get("comment_id") or "").strip()
        if comment_id and comment_id in seen_ids:
            report["removed_duplicate"] += 1
            continue

        if looks_like_spam(raw_text):
            report["removed_spam"] += 1
            continue

        # Duplicate text detection: same normalized text within this content.
        fingerprint = clean_text_for_nlp(raw_text).lower()
        if fingerprint and fingerprint in seen_texts:
            report["removed_duplicate"] += 1
            continue

        clean_value = clean_text_for_nlp(raw_text)
        if not clean_value:
            report["removed_empty"] += 1
            continue

        published = normalize_timestamp(record.get("published_at"))
        if record.get("published_at") and not published:
            report["invalid_dates"] += 1

        if comment_id:
            seen_ids.add(comment_id)
        if fingerprint:
            seen_texts[fingerprint] = comment_id or ""

        words = clean_value.split()
        cleaned.append(
            {
                "record_type": record.get("record_type", "comment"),
                "comment_id": comment_id or None,
                "parent_id": str(record.get("parent_id") or "") or None,
                "author_id": str(record.get("author_id") or "") or None,
                "author_name": record.get("author_name") or None,
                "raw_text": raw_text,
                "clean_text": clean_value,
                "word_count": len(words),
                "char_count": len(clean_value),
                "language": detect_language(clean_value),
                "published_at": published,
                "like_count": to_int(record.get("like_count")),
                "reply_count": to_int(record.get("reply_count")),
                "hashtags": extract_hashtags(raw_text),
                "mentions": extract_mentions(raw_text),
                "flags": [],
                "is_duplicate": False,
                "is_spam": False,
            }
        )

    # Outlier detection on comment length (IQR method, numpy-free).
    cleaned = _flag_length_outliers(cleaned, report)

    report["output_count"] = len(cleaned)
    report["steps"].append({"step": "2. Remove empty records", "detail": f"{report['removed_empty']} removed"})
    report["steps"].append({"step": "3. Remove duplicates", "detail": f"{report['removed_duplicate']} removed"})
    report["steps"].append({"step": "4. Filter spam patterns", "detail": f"{report['removed_spam']} removed"})
    report["steps"].append(
        {"step": "5. Normalize text/dates/IDs", "detail": f"{report['invalid_dates']} invalid timestamp(s)"}
    )
    report["steps"].append({"step": "6. Detect length outliers", "detail": f"{report.get('outliers', 0)} flagged"})
    report["steps"].append({"step": "7. Final dataset", "detail": f"{len(cleaned)} record(s) ready"})

    return {"records": cleaned, "report": report}


def _flag_length_outliers(records: list[dict[str, Any]], report: dict[str, Any]) -> list[dict[str, Any]]:
    if len(records) < 4:
        report["outliers"] = 0
        return records
    lengths = sorted(r["word_count"] for r in records)
    median = lengths[len(lengths) // 2]
    lower = lengths[: len(lengths) // 2]
    upper = lengths[(len(lengths) + 1) // 2 :]
    q1 = lower[len(lower) // 2] if lower else median
    q3 = upper[len(upper) // 2] if upper else median
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    count = 0
    for record in records:
        if high > low and (record["word_count"] > high or record["word_count"] < low):
            record["is_outlier"] = True
            record["flags"].append("length_outlier")
            count += 1
    report["outliers"] = count
    return records


def is_image_only(text: str) -> bool:
    """True when a comment carries no analysable words (e.g. an emoji)."""
    return not content_tokens(text) and not EMOJI_RE.search(text or "")
