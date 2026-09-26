"""The end-to-end analysis pipeline.

    collect -> clean -> sentiment -> statistics -> engagement -> keywords -> insights

The same pipeline is used for live API data and for the labelled demo dataset,
so the UI behaves identically in both cases.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable

from app.analysis import cleaning, engagement as engagement_mod, insights as insights_mod
from app.analysis import keywords as keywords_mod
from app.analysis import sentiment as sentiment_mod
from app.analysis import statistics as stats_mod
from app.config import settings
from app.platforms.base import CollectedData

ProgressCallback = Callable[[str], None]


def _noop(_: str) -> None:
    return None


def run_pipeline(
    collected: CollectedData,
    *,
    source_url: str,
    data_mode: str = "live",
    user_name: str | None = None,
    on_progress: ProgressCallback = _noop,
) -> dict[str, Any]:
    """Transform collected platform data into a complete analysis payload."""
    started = time.perf_counter()

    on_progress("Cleaning dataset")
    clean_result = cleaning.clean_records(collected.records)
    clean_records = clean_result["records"]
    report = clean_result["report"]

    on_progress("Processing comments")
    sentiment_result = sentiment_mod.analyze_records(clean_records)
    scored = sentiment_result["records"]
    summary = sentiment_result["summary"]

    on_progress("Calculating engagement metrics")
    engagement = engagement_mod.compute_engagement(collected.content, scored)
    comment_engagement = engagement_mod.comment_engagement(scored)

    on_progress("Running statistical analysis")
    statistics = stats_mod.build_statistics(scored)

    on_progress("Generating visualizations")
    text_assets = keywords_mod.build_text_assets(scored)
    charts = build_charts(scored, summary, statistics, engagement, text_assets, collected.content)

    sentiment_status = sentiment_mod.engine_status()
    insight_list = insights_mod.build_insights(
        collected.content,
        scored,
        summary,
        engagement,
        statistics,
        text_assets,
        report,
    )
    limitation_list = insights_mod.build_limitations(
        collected.content,
        collected.unavailable_fields,
        collected.notes,
        data_mode,
        sentiment_status,
    )

    elapsed = round(time.perf_counter() - started, 3)

    payload = {
        "public_id": uuid.uuid4().hex[:16],
        "source_url": source_url,
        "platform": collected.platform,
        "data_mode": data_mode,
        "status": "completed",
        "user_name": user_name,
        "content": collected.content,
        "records": scored,
        "cleaning_report": report,
        "raw_records": collected.records,
        "sentiment_summary": summary,
        "sentiment_comparison": sentiment_result["comparison"],
        "sentiment_status": sentiment_status,
        "sentiment_method": sentiment_status["primary_engine"],
        "engagement": engagement,
        "comment_engagement": comment_engagement,
        "statistics": statistics,
        "trends": {
            "daily": stats_mod.time_series(scored, "day"),
            "hourly_of_day": statistics["hourly"],
            "weekly": stats_mod.time_series(scored, "week"),
        },
        "keywords": text_assets["keywords"],
        "hashtags": text_assets["hashtags"],
        "charts": charts,
        "insights": insight_list,
        "limitations": limitation_list,
        "available_fields": collected.available_fields,
        "unavailable_fields": collected.unavailable_fields,
        "notes": collected.notes,
        "provenance": collected.provenance,
        "total_records": len(scored),
        "removed_records": report["input_count"] - report["output_count"],
        "analysis_seconds": elapsed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    on_progress("Preparing downloadable dataset")
    return payload


def build_charts(
    records: list[dict[str, Any]],
    summary: dict[str, Any],
    statistics: dict[str, Any],
    engagement: dict[str, Any],
    text_assets: dict[str, Any],
    content: dict[str, Any],
) -> dict[str, Any]:
    """Pre-computed series so the frontend never has to reshape data itself."""
    trends = stats_mod.time_series(records, "day")

    scatter = [
        {
            "id": record.get("comment_id"),
            "likes": record.get("like_count"),
            "sentiment": record.get("compound"),
            "text": (record.get("raw_text") or "")[:80],
            "sentiment_label": record.get("sentiment"),
        }
        for record in records
        if isinstance(record.get("like_count"), (int, float))
        and isinstance(record.get("compound"), (int, float))
    ]

    return {
        "engagement_bars": {
            "categories": ["Views", "Likes", "Comments", "Shares"],
            "values": [
                engagement.get("views"),
                engagement.get("likes"),
                engagement.get("comments"),
                engagement.get("shares"),
            ],
        },
        "sentiment_donut": summary.get("distribution", []),
        "sentiment_scores": {
            "categories": ["Positive", "Neutral", "Negative", "Avg compound", "Avg polarity", "Avg subjectivity"],
            "values": [
                summary.get("positive", 0),
                summary.get("neutral", 0),
                summary.get("negative", 0),
                summary.get("avg_compound", 0),
                summary.get("avg_polarity", 0),
                summary.get("avg_subjectivity", 0),
            ],
        },
        "sentiment_timeline": {
            "categories": [point["period"] for point in trends["points"]],
            "series": [
                {
                    "name": "Positive",
                    "data": [point.get("positive", 0) for point in trends["points"]],
                },
                {
                    "name": "Neutral",
                    "data": [point.get("neutral", 0) for point in trends["points"]],
                },
                {
                    "name": "Negative",
                    "data": [point.get("negative", 0) for point in trends["points"]],
                },
            ],
            "available": trends["available"],
        },
        "likes_vs_sentiment": scatter,
        "comment_length_histogram": statistics["comment_length"]["histogram"],
        "hourly_activity": statistics["hourly"]["distribution"],
        "keyword_bars": [
            {"name": row["word"], "value": row["count"]} for row in text_assets["keywords"][:15]
        ],
        "hashtag_bars": [
            {"name": row["hashtag"], "value": row["count"]} for row in text_assets["hashtags"][:15]
        ],
        "word_cloud": text_assets["cloud"],
        "top_comments": text_assets["top_comments"],
        "correlation_matrix": statistics["correlations"],
    }


def persist_raw_snapshot(payload: dict[str, Any]) -> str | None:
    """Write the untouched collected payload to ``data/raw`` for auditability."""
    try:
        target = settings.data_dir / "raw" / f"{payload['public_id']}.json"
        snapshot = {
            "public_id": payload["public_id"],
            "source_url": payload["source_url"],
            "platform": payload["platform"],
            "data_mode": payload["data_mode"],
            "collected_at": payload["created_at"],
            "provenance": payload.get("provenance", {}),
            "content": payload.get("content", {}),
            "raw_records": payload.get("raw_records", []),
        }
        target.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")
        return str(target)
    except OSError:
        return None
