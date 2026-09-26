"""Descriptive statistics, correlation, and time-series aggregation.

Implemented in pure Python/NumPy-free style so the analysis stage has no heavy
runtime requirement, while producing the exact figures a DAE report needs.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from typing import Any, Iterable, Sequence

from app.analysis.cleaning import content_tokens


def _numbers(values: Iterable[Any]) -> list[float]:
    return [float(v) for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def mode(values: Sequence[float]) -> float | None:
    if not values:
        return None
    counter = Counter(values)
    top = counter.most_common(1)[0]
    return top[0] if top[1] > 1 else None


def variance(values: Sequence[float], sample: bool = True) -> float:
    n = len(values)
    if n < (2 if sample else 1):
        return 0.0
    avg = mean(values)
    return sum((v - avg) ** 2 for v in values) / (n - 1 if sample else n)


def stdev(values: Sequence[float]) -> float:
    return math.sqrt(variance(values))


def percentile(values: Sequence[float], pct: float) -> float:
    """Linear-interpolation percentile, ``pct`` in 0..100."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * (pct / 100)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[int(position)]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def describe(values: Iterable[Any]) -> dict[str, Any]:
    """Full descriptive summary for one numeric field."""
    data = _numbers(values)
    if not data:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "mode": None,
            "min": None,
            "max": None,
            "std_dev": None,
            "variance": None,
            "q1": None,
            "q3": None,
            "range": None,
            "sum": 0,
        }
    return {
        "count": len(data),
        "mean": round(mean(data), 4),
        "median": round(median(data), 4),
        "mode": mode(data),
        "min": round(min(data), 4),
        "max": round(max(data), 4),
        "std_dev": round(stdev(data), 4),
        "variance": round(variance(data), 4),
        "q1": round(percentile(data, 25), 4),
        "q3": round(percentile(data, 75), 4),
        "range": round(max(data) - min(data), 4),
        "sum": round(sum(data), 4),
    }


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    """Pearson correlation coefficient, or ``None`` when undefined."""
    pairs = [(x, y) for x, y in zip(xs, ys) if isinstance(x, (int, float)) and isinstance(y, (int, float))]
    if len(pairs) < 3:
        return None
    x_vals = [p[0] for p in pairs]
    y_vals = [p[1] for p in pairs]
    mx, my = mean(x_vals), mean(y_vals)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = math.sqrt(sum((x - mx) ** 2 for x in x_vals) * sum((y - my) ** 2 for y in y_vals))
    if den == 0:
        return None
    return round(num / den, 4)


def _strength(value: float | None) -> str:
    if value is None:
        return "n/a"
    magnitude = abs(value)
    if magnitude >= 0.7:
        return "strong"
    if magnitude >= 0.4:
        return "moderate"
    if magnitude >= 0.2:
        return "weak"
    return "negligible"


def correlation_matrix(
    records: list[dict[str, Any]], fields: list[tuple[str, str]]
) -> dict[str, Any]:
    """Correlation matrix plus a flat list of significant relationships."""
    matrix: list[list[float | None]] = []
    lookup: dict[str, list[float]] = {}
    for key, _ in fields:
        lookup[key] = _numbers(r.get(key) for r in records)

    for key_x, _ in fields:
        row: list[float | None] = []
        for key_y, _ in fields:
            if key_x == key_y:
                row.append(1.0)
            else:
                row.append(pearson(lookup[key_x], lookup[key_y]))
        matrix.append(row)

    pairs: list[dict[str, Any]] = []
    for i, (key_x, label_x) in enumerate(fields):
        for j in range(i + 1, len(fields)):
            key_y, label_y = fields[j]
            value = matrix[i][j]
            if value is None:
                continue
            pairs.append(
                {
                    "x": label_x,
                    "y": label_y,
                    "coefficient": value,
                    "strength": _strength(value),
                    "direction": "positive" if value >= 0 else "negative",
                }
            )
    pairs.sort(key=lambda p: abs(p["coefficient"]), reverse=True)

    return {
        "fields": [label for _, label in fields],
        "keys": [key for key, _ in fields],
        "matrix": matrix,
        "pairs": pairs,
    }


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def time_series(records: list[dict[str, Any]], granularity: str = "day") -> dict[str, Any]:
    """Aggregate comment volume and sentiment over time."""
    buckets: dict[str, dict[str, Any]] = {}

    for record in records:
        moment = _parse(record.get("published_at"))
        if not moment:
            continue
        if granularity == "hour":
            key = moment.strftime("%Y-%m-%d %H:00")
        elif granularity == "week":
            year, week, _ = moment.isocalendar()
            key = f"{year}-W{week:02d}"
        else:
            key = moment.strftime("%Y-%m-%d")

        bucket = buckets.setdefault(
            key,
            {"period": key, "count": 0, "positive": 0, "neutral": 0, "negative": 0, "compound_sum": 0.0},
        )
        bucket["count"] += 1
        sentiment = record.get("sentiment", "neutral")
        bucket[sentiment] = bucket.get(sentiment, 0) + 1
        bucket["compound_sum"] += float(record.get("compound") or 0.0)

    series = sorted(buckets.values(), key=lambda b: b["period"])
    for bucket in series:
        bucket["avg_sentiment"] = round(bucket["compound_sum"] / bucket["count"], 4) if bucket["count"] else 0.0
        del bucket["compound_sum"]

    return {
        "granularity": granularity,
        "available": bool(series),
        "points": series,
        "peak_period": max(series, key=lambda b: b["count"])["period"] if series else None,
        "peak_count": max((b["count"] for b in series), default=0),
    }


def comment_length_stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = _numbers(r.get("char_count") for r in records)
    words = _numbers(r.get("word_count") for r in records)
    histogram: list[dict[str, Any]] = []
    if lengths:
        buckets = [
            ("1-10", 0, 10),
            ("11-25", 10, 25),
            ("26-50", 25, 50),
            ("51-100", 50, 100),
            ("101-200", 100, 200),
            ("200+", 200, float("inf")),
        ]
        for label, low, high in buckets:
            histogram.append(
                {
                    "label": label,
                    "count": sum(1 for value in lengths if low < value <= high),
                }
            )
    return {
        "characters": describe(lengths),
        "words": describe(words),
        "histogram": histogram,
    }


def hourly_activity(records: list[dict[str, Any]]) -> dict[str, Any]:
    hours: list[int] = []
    for record in records:
        moment = _parse(record.get("published_at"))
        if moment:
            hours.append(moment.hour)
    distribution = [{"hour": f"{h:02d}:00", "count": 0} for h in range(24)]
    for hour in hours:
        distribution[hour]["count"] += 1
    peak = max(distribution, key=lambda d: d["count"]) if hours else None
    return {
        "distribution": distribution,
        "peak_hour": peak["hour"] if peak and peak["count"] else None,
        "available": bool(hours),
    }


def daily_keywords(records: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    """Top keywords within the positive and negative subsets."""
    def top_for(subset: list[dict[str, Any]]) -> list[str]:
        counter: Counter[str] = Counter()
        for record in subset:
            counter.update(content_tokens(record.get("clean_text", "")))
        return [word for word, _ in counter.most_common(limit)]

    return [
        {
            "sentiment": "positive",
            "keywords": top_for([r for r in records if r.get("sentiment") == "positive"]),
        },
        {
            "sentiment": "negative",
            "keywords": top_for([r for r in records if r.get("sentiment") == "negative"]),
        },
    ]


def build_statistics(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Assemble every statistical output the dashboard needs."""
    sentiment_rows = [r for r in records if r.get("record_type") == "comment"] or records

    numeric_fields = [
        ("compound", "Sentiment (compound)"),
        ("polarity", "Polarity (TextBlob)"),
        ("subjectivity", "Subjectivity (TextBlob)"),
        ("like_count", "Likes"),
        ("word_count", "Word count"),
        ("char_count", "Character count"),
    ]
    descriptive = {
        label: describe(r.get(key) for r in records)
        for key, label in numeric_fields
    }

    correlations = correlation_matrix(
        sentiment_rows,
        [
            ("like_count", "Likes"),
            ("word_count", "Length"),
            ("compound", "Sentiment"),
            ("subjectivity", "Subjectivity"),
        ],
    )

    return {
        "descriptive": descriptive,
        "correlations": correlations,
        "comment_length": comment_length_stats(records),
        "hourly": hourly_activity(records),
        "sentiment_keywords": daily_keywords(sentiment_rows),
    }
