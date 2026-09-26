"""Insight generation.

Every sentence is generated from a calculated value. If a required field was
not supplied by the platform API, no claim is made about it.
"""

from __future__ import annotations

from typing import Any


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1f}%"


def build_insights(
    content: dict[str, Any],
    records: list[dict[str, Any]],
    sentiment_summary: dict[str, Any],
    engagement: dict[str, Any],
    statistics: dict[str, Any],
    text_assets: dict[str, Any],
    cleaning_report: dict[str, Any],
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    total = sentiment_summary.get("total", 0)

    if total:
        dominant = max(
            ("positive", "neutral", "negative"),
            key=lambda k: sentiment_summary.get(k, 0),
        )
        share = sentiment_summary.get(f"{dominant}_pct", 0.0)
        insights.append(
            {
                "title": "Dominant sentiment",
                "text": f"{dominant.capitalize()} comments represent {_pct(share)} of the "
                f"{total} analysed text records.",
                "kind": "sentiment",
            }
        )

        if sentiment_summary.get("avg_compound") is not None:
            compound = sentiment_summary["avg_compound"]
            direction = "positive" if compound > 0 else "negative" if compound < 0 else "neutral"
            insights.append(
                {
                    "title": "Average sentiment score",
                    "text": f"The mean compound sentiment score is {compound:.3f} "
                    f"({direction} overall tone across the analysed records).",
                    "kind": "sentiment",
                }
            )

    keywords = text_assets.get("keywords", [])
    if keywords:
        top = ", ".join(f"{row['word']} ({row['count']})" for row in keywords[:5])
        insights.append(
            {
                "title": "Most frequent keywords",
                "text": f"The most frequently used words are {top}.",
                "kind": "keywords",
            }
        )

    hashtags = text_assets.get("hashtags", [])
    if hashtags:
        top_tags = ", ".join(f"#{row['hashtag']} ({row['count']})" for row in hashtags[:5])
        insights.append(
            {
                "title": "Most used hashtags",
                "text": f"The most used hashtags are {top_tags}.",
                "kind": "hashtags",
            }
        )

    engagement_rate = engagement.get("engagement_rate")
    if engagement_rate is not None:
        included = engagement.get("interactions_included", [])
        formula = f"({' + '.join(included)}) / views x 100" if included else ""
        insights.append(
            {
                "title": "Engagement",
                "text": f"Engagement rate is {engagement_rate:.2f}%, calculated as {formula}.",
                "kind": "engagement",
            }
        )
    else:
        insights.append(
            {
                "title": "Engagement",
                "text": "Engagement rate could not be calculated because the platform API did not "
                "return all required inputs. No substitute value has been estimated.",
                "kind": "engagement",
            }
        )

    pairs = statistics.get("correlations", {}).get("pairs", [])
    if pairs:
        strongest = pairs[0]
        insights.append(
            {
                "title": "Strongest relationship",
                "text": f"{strongest['x']} and {strongest['y']} show a {strongest['strength']} "
                f"{strongest['direction']} correlation (r = {strongest['coefficient']}).",
                "kind": "correlation",
            }
        )

    hourly = statistics.get("hourly", {})
    if hourly.get("peak_hour"):
        insights.append(
            {
                "title": "Peak activity",
                "text": f"The highest comment activity occurred around {hourly['peak_hour']} "
                "(in the timezone of the timestamps returned by the platform).",
                "kind": "timing",
            }
        )

    comment_length = statistics.get("comment_length", {}).get("characters", {})
    if comment_length.get("mean"):
        insights.append(
            {
                "title": "Comment length",
                "text": f"The average analysed text record is {comment_length['mean']:.0f} characters "
                f"long (median {comment_length.get('median', 0):.0f}).",
                "kind": "length",
            }
        )

    removed = cleaning_report.get("input_count", 0) - cleaning_report.get("output_count", 0)
    if removed:
        insights.append(
            {
                "title": "Data cleaning",
                "text": f"{cleaning_report.get('input_count', 0)} collected record(s) were reduced to "
                f"{cleaning_report.get('output_count', 0)} analysable record(s); {removed} were removed as "
                "empty, duplicate or spam-like.",
                "kind": "data_quality",
            }
        )

    languages = {r.get("language") for r in records if r.get("language")}
    languages.discard("und")
    if len(languages) > 1:
        insights.append(
            {
                "title": "Languages detected",
                "text": f"The analysed records span {len(languages)} detected languages "
                f"({', '.join(sorted(languages))}). Language detection is heuristic.",
                "kind": "language",
            }
        )

    if content.get("published_at"):
        insights.append(
            {
                "title": "Content",
                "text": f"The analysed content was published on {content['published_at']}.",
                "kind": "content",
            }
        )

    return insights


def build_limitations(
    content: dict[str, Any],
    unavailable_fields: list[str],
    platform_notes: list[str],
    data_mode: str,
    sentiment_status: dict[str, Any],
) -> list[str]:
    limitations = list(platform_notes)

    if unavailable_fields:
        limitations.append(
            "The following requested fields were not returned by the platform API and are reported as "
            f"unavailable: {', '.join(unavailable_fields)}."
        )
    else:
        limitations.append("All requested metric fields were available for this content.")

    limitations.append(
        "Sentiment is a lexicon-based estimate produced by "
        f"{sentiment_status.get('primary_engine', 'unknown')}, not a human judgement. Sarcasm, emojis, "
        "code-switching and very short comments reduce accuracy."
    )

    if not sentiment_status.get("textblob_available"):
        limitations.append(
            "TextBlob was not available in this environment, so polarity and subjectivity were "
            "estimated rather than calculated by TextBlob."
        )

    if data_mode == "demo":
        limitations.insert(
            0,
            "DEMO DATA — this dataset is bundled for demonstration purposes and is not live "
            "social-media data.",
        )

    limitations.append(
        "Comment coverage depends on the platform's own moderation: removed, blocked and "
        "creator-hidden comments are not accessible through any permitted method."
    )

    # The demo banner can arrive both from the adapter notes and the mode check.
    seen: set[str] = set()
    deduped: list[str] = []
    for item in limitations:
        normalized = item.strip().lower().rstrip(".")
        # Collapse near-duplicate notices (e.g. two demo banner wordings).
        prefix = "demo data" if normalized.startswith("demo data") else normalized
        if prefix in seen:
            continue
        seen.add(prefix)
        deduped.append(item)
    return deduped
