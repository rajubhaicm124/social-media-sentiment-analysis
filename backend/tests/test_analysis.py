"""Sentiment scoring, statistics, and engagement calculations."""

from __future__ import annotations

import pytest

from app.analysis import engagement as engagement_mod
from app.analysis import sentiment as sentiment_mod
from app.analysis import statistics as stats_mod


def _record(text: str, **overrides):
    base = {
        "record_type": "comment",
        "comment_id": f"c{abs(hash(text)) % 10_000}",
        "raw_text": text,
        "clean_text": text,
        "word_count": len(text.split()),
        "char_count": len(text),
        "published_at": "2026-01-02T03:04:05+00:00",
        "like_count": 5,
        "reply_count": 0,
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------- sentiment

def test_classification_thresholds() -> None:
    assert sentiment_mod.classify(0.5) == "positive"
    assert sentiment_mod.classify(0.05) == "positive"
    assert sentiment_mod.classify(0.0) == "neutral"
    assert sentiment_mod.classify(-0.05) == "negative"
    assert sentiment_mod.classify(-0.9) == "negative"
    assert sentiment_mod.classify(None) == "neutral"


def test_scores_positive_text() -> None:
    result = sentiment_mod.score_text("This is an amazing, brilliant, wonderful video!")
    assert result["sentiment"] == "positive"
    assert result["compound"] > 0
    assert 0.0 <= result["confidence"] <= 1.0


def test_scores_negative_text() -> None:
    result = sentiment_mod.score_text("This is awful, terrible and a complete waste of time.")
    assert result["sentiment"] == "negative"
    assert result["compound"] < 0


def test_scores_neutral_text() -> None:
    result = sentiment_mod.score_text("It is a video. It was released on Tuesday.")
    assert result["sentiment"] == "neutral"


def test_every_score_exposes_both_engines() -> None:
    result = sentiment_mod.score_text("Pretty good, thanks.")
    engines = result["engines"]
    assert "vader" in engines and "textblob" in engines
    assert "polarity" in engines["textblob"]
    assert "subjectivity" in engines["textblob"]
    assert engines["primary"] in {"vader", "lexicon"}


def test_empty_text_is_handled() -> None:
    result = sentiment_mod.score_text("")
    assert result["sentiment"] == "neutral"
    assert result["compound"] == 0


def test_analyze_records_summarizes_distribution() -> None:
    records = [
        _record("amazing brilliant wonderful"),
        _record("awful terrible horrible"),
        _record("it is a video on tuesday"),
    ]
    result = sentiment_mod.analyze_records(records)
    assert result["summary"]["total"] == 3
    assert (
        result["summary"]["positive"]
        + result["summary"]["neutral"]
        + result["summary"]["negative"]
        == 3
    )
    assert abs(sum(result["summary"][f"{k}_pct"] for k in ("positive", "neutral", "negative")) - 100) < 0.1
    assert len(result["comparison"]) == 3


def test_summary_handles_empty_input() -> None:
    summary = sentiment_mod.summarize([])
    assert summary["total"] == 0
    assert summary["positive_pct"] == 0.0


def test_engine_status_reports_reality() -> None:
    status = sentiment_mod.engine_status()
    assert status["primary_engine"] in {"vader", "lexicon"}
    assert isinstance(status["vader_available"], bool)
    assert isinstance(status["textblob_available"], bool)
    assert status["positive_threshold"] == 0.05


def test_emotion_detection() -> None:
    assert sentiment_mod.detect_emotion(0.8, "I love this") == "joy"
    assert sentiment_mod.detect_emotion(-0.8, "I hate this") == "anger"


# -------------------------------------------------------------- statistics

def test_describe_computes_full_summary() -> None:
    stats = stats_mod.describe([1, 2, 3, 4, 5])
    assert stats["count"] == 5
    assert stats["mean"] == 3.0
    assert stats["median"] == 3.0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["std_dev"] == pytest.approx(1.5811, abs=1e-3)
    assert stats["variance"] == pytest.approx(2.5, abs=1e-6)
    assert stats["q1"] == 2.0
    assert stats["q3"] == 4.0
    assert stats["range"] == 4.0


def test_describe_on_empty_is_all_none() -> None:
    stats = stats_mod.describe([])
    assert stats["count"] == 0
    assert stats["mean"] is None


def test_describe_ignores_non_numeric() -> None:
    assert stats_mod.describe([1, "x", None, 3])["count"] == 2


def test_percentile_interpolates() -> None:
    assert stats_mod.percentile([1, 2, 3, 4], 50) == 2.5
    assert stats_mod.percentile([], 50) == 0.0


def test_pearson_correlation() -> None:
    assert stats_mod.pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert stats_mod.pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)
    # Too few points to be meaningful.
    assert stats_mod.pearson([1], [2]) is None
    # No variance in one series.
    assert stats_mod.pearson([1, 1, 1], [1, 2, 3]) is None


def test_correlation_matrix_shape_and_labels() -> None:
    records = [_record("good great nice", like_count=i) for i in range(6)]
    matrix = stats_mod.correlation_matrix(
        records, [("like_count", "Likes"), ("compound", "Sentiment")]
    )
    assert matrix["fields"] == ["Likes", "Sentiment"]
    assert len(matrix["matrix"]) == 2
    assert all(len(row) == 2 for row in matrix["matrix"])
    # Diagonal is always 1.
    assert matrix["matrix"][0][0] == 1.0
    assert matrix["matrix"][1][1] == 1.0


def test_time_series_buckets_by_day() -> None:
    records = [
        _record("one", published_at="2026-01-01T01:00:00+00:00"),
        _record("two", published_at="2026-01-01T05:00:00+00:00"),
        _record("three", published_at="2026-01-02T01:00:00+00:00"),
    ]
    series = stats_mod.time_series(records, "day")
    assert series["available"] is True
    assert [p["period"] for p in series["points"]] == ["2026-01-01", "2026-01-02"]
    assert series["points"][0]["count"] == 2
    assert series["peak_period"] == "2026-01-01"
    assert series["peak_count"] == 2


def test_time_series_without_timestamps() -> None:
    series = stats_mod.time_series([_record("x", published_at=None)], "day")
    assert series["available"] is False
    assert series["points"] == []


def test_comment_length_histogram() -> None:
    records = [_record("a" * n) for n in (5, 15, 30, 60, 120, 300)]
    histogram = stats_mod.comment_length_stats(records)["histogram"]
    assert sum(bucket["count"] for bucket in histogram) == 6


def test_build_statistics_returns_expected_sections() -> None:
    records = [_record("good great nice words", like_count=i, compound=i / 10) for i in range(8)]
    result = stats_mod.build_statistics(records)
    for key in ("descriptive", "correlations", "comment_length", "hourly", "sentiment_keywords"):
        assert key in result
    assert result["descriptive"]["Sentiment (compound)"]["count"] == 8


# --------------------------------------------------------------- engagement

def test_engagement_rate_uses_available_interactions() -> None:
    result = engagement_mod.compute_engagement(
        {"views": 1000, "likes": 50, "comment_count": 30, "shares": None}, []
    )
    assert result["engagement_rate"] == pytest.approx(8.0)
    assert result["engagement_rate_available"] is True
    assert result["interactions_included"] == ["likes", "comments"]
    assert "shares" in result["unavailable_fields"]


def test_engagement_rate_includes_shares_when_present() -> None:
    result = engagement_mod.compute_engagement(
        {"views": 1000, "likes": 50, "comment_count": 30, "shares": 20}, []
    )
    assert result["total_interactions"] == 100
    assert result["engagement_rate"] == pytest.approx(10.0)


def test_engagement_rate_unavailable_without_views() -> None:
    result = engagement_mod.compute_engagement(
        {"views": None, "likes": 50, "comment_count": 30}, []
    )
    assert result["engagement_rate"] is None
    assert result["engagement_rate_available"] is False
    assert result["views"] is None
    assert any("unavailable" in note.lower() for note in result["notes"])


def test_engagement_rate_unavailable_without_interactions() -> None:
    result = engagement_mod.compute_engagement({"views": 5000, "likes": None, "comment_count": None}, [])
    assert result["engagement_rate"] is None
    assert result["total_interactions"] is None


def test_zero_views_does_not_divide_by_zero() -> None:
    result = engagement_mod.compute_engagement({"views": 0, "likes": 5, "comment_count": 1}, [])
    assert result["engagement_rate"] is None


def test_never_invents_missing_metrics() -> None:
    result = engagement_mod.compute_engagement({"views": 100, "likes": None, "comment_count": None, "shares": None}, [])
    assert result["likes"] is None
    assert result["comments"] is None
    assert result["shares"] is None
