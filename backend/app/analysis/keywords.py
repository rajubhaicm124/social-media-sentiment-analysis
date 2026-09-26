"""Keyword, hashtag, and n-gram extraction."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.analysis.cleaning import STOPWORDS, content_tokens, tokenize

MIN_TOKEN_LENGTH = 3
TOP_LIMIT = 30


def extract_keywords(records: list[dict[str, Any]], limit: int = TOP_LIMIT) -> list[dict[str, Any]]:
    """Unigram frequency with document frequency for the TF-IDF-style score."""
    counter: Counter[str] = Counter()
    document_frequency: Counter[str] = Counter()
    total = 0

    for record in records:
        tokens = [t for t in content_tokens(record.get("clean_text", "")) if len(t) >= MIN_TOKEN_LENGTH]
        unique = set(tokens)
        counter.update(tokens)
        document_frequency.update(unique)
        total += len(tokens)

    if not counter:
        return []

    import math

    rows: list[dict[str, Any]] = []
    for word, count in counter.most_common(limit):
        tf = count / total
        idf = math.log((1 + len(records)) / (1 + document_frequency[word])) + 1
        rows.append(
            {
                "word": word,
                "count": count,
                "tfidf": round(tf * idf, 6),
                "document_frequency": document_frequency[word],
            }
        )
    return rows


def extract_bigrams(records: list[dict[str, Any]], limit: int = 15) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for record in records:
        tokens = content_tokens(record.get("clean_text", ""))
        for first, second in zip(tokens, tokens[1:]):
            counter[f"{first} {second}"] += 1
    return [
        {"phrase": phrase, "count": count}
        for phrase, count in counter.most_common(limit)
        if count > 1
    ]


def extract_hashtags(records: list[dict[str, Any]], limit: int = TOP_LIMIT) -> list[dict[str, Any]]:
    """Hashtag frequency plus the average sentiment of posts that used them."""
    counter: Counter[str] = Counter()
    sentiment_sums: dict[str, list[float]] = {}
    case_map: dict[str, str] = {}

    for record in records:
        for tag in record.get("hashtags", []) or []:
            key = tag.lower()
            case_map.setdefault(key, tag)
            counter[key] += 1
            sentiment_sums.setdefault(key, []).append(float(record.get("compound") or 0.0))

    rows: list[dict[str, Any]] = []
    for tag, count in counter.most_common(limit):
        scores = sentiment_sums.get(tag, [])
        average = round(sum(scores) / len(scores), 4) if scores else 0.0
        rows.append(
            {
                "hashtag": case_map.get(tag, tag),
                "count": count,
                "avg_sentiment": average,
                "sentiment": (
                    "positive" if average >= 0.05 else "negative" if average <= -0.05 else "neutral"
                ),
            }
        )
    return rows


def top_comments(
    records: list[dict[str, Any]], limit: int = 5
) -> dict[str, list[dict[str, Any]]]:
    """Most liked / most positive / most negative comments."""

    def pack(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "comment_id": record.get("comment_id"),
            "text": (record.get("raw_text") or "")[:280],
            "author_name": record.get("author_name"),
            "like_count": record.get("like_count"),
            "published_at": record.get("published_at"),
            "sentiment": record.get("sentiment"),
            "compound": record.get("compound"),
        }

    liked = [r for r in records if isinstance(r.get("like_count"), (int, float))]
    most_liked = sorted(liked, key=lambda r: r["like_count"], reverse=True)[:limit]

    positive = [r for r in records if r.get("sentiment") == "positive"]
    negative = [r for r in records if r.get("sentiment") == "negative"]

    return {
        "most_liked": [pack(r) for r in most_liked],
        "most_positive": [pack(r) for r in sorted(positive, key=lambda r: r.get("compound", 0), reverse=True)[:limit]],
        "most_negative": [pack(r) for r in sorted(negative, key=lambda r: r.get("compound", 0))[:limit]],
    }


def word_cloud_terms(keywords: list[dict[str, Any]], limit: int = 40) -> list[dict[str, Any]]:
    return [
        {"text": row["word"], "value": row["count"]}
        for row in keywords[:limit]
    ]


def build_text_assets(records: list[dict[str, Any]]) -> dict[str, Any]:
    keywords = extract_keywords(records)
    hashtags = extract_hashtags(records)
    for record in records:
        record["keywords"] = [row["word"] for row in keywords if row["word"] in set(content_tokens(record.get("clean_text", "")))][:8]
    return {
        "keywords": keywords,
        "hashtags": hashtags,
        "bigrams": extract_bigrams(records),
        "cloud": word_cloud_terms(keywords),
        "top_comments": top_comments(records),
    }
