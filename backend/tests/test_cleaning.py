"""Data cleaning and normalization."""

from __future__ import annotations

from app.analysis.cleaning import (
    clean_records,
    clean_text_for_nlp,
    detect_language,
    extract_hashtags,
    extract_mentions,
    looks_like_spam,
    normalize_timestamp,
    normalize_whitespace,
    to_int,
)


def _record(**overrides):
    base = {
        "record_type": "comment",
        "comment_id": "c1",
        "author_id": "a1",
        "author_name": "Author",
        "raw_text": "This is a great video, thanks!",
        "published_at": "2026-01-02T03:04:05Z",
        "like_count": 12,
        "reply_count": None,
    }
    base.update(overrides)
    return base


def test_removes_empty_and_whitespace_records() -> None:
    result = clean_records([_record(), _record(comment_id="c2", raw_text="   ")])
    assert result["report"]["removed_empty"] == 1
    assert result["report"]["output_count"] == 1


def test_removes_duplicate_ids() -> None:
    result = clean_records([_record(), _record(raw_text="Different text entirely")])
    assert result["report"]["removed_duplicate"] == 1
    assert result["report"]["output_count"] == 1


def test_removes_duplicate_text_with_different_ids() -> None:
    result = clean_records([_record(), _record(comment_id="c2")])
    assert result["report"]["removed_duplicate"] == 1


def test_removes_spam() -> None:
    spam = _record(comment_id="spam", raw_text="FREE crypto giveaway http://a.example http://b.example")
    result = clean_records([_record(), spam])
    assert result["report"]["removed_spam"] == 1
    assert result["report"]["output_count"] == 1


def test_counts_are_consistent() -> None:
    records = [
        _record(),
        _record(comment_id="c2", raw_text="Second genuinely different comment here"),
        _record(comment_id="c3", raw_text="  "),
        _record(comment_id="c4", raw_text="   ".join([]) or "!"),
    ]
    report = clean_records(records)["report"]
    assert report["input_count"] == report["output_count"] + (
        report["removed_empty"] + report["removed_duplicate"] + report["removed_spam"]
    )


def test_normalizes_text_for_nlp() -> None:
    cleaned = clean_text_for_nlp("Check this out!!! https://example.com/x @someone #cool <b>bold</b>")
    assert "http" not in cleaned
    assert "<b>" not in cleaned
    assert "bold" in cleaned  # HTML is unwrapped, not deleted
    assert "someone" in cleaned  # mention marker removed, word kept
    assert "cool" in cleaned  # hashtag marker removed, word kept
    assert "  " not in cleaned


def test_removes_zero_width_and_repeated_chars() -> None:
    assert clean_text_for_nlp("he\u200bllo") == "hello"
    assert clean_text_for_nlp("sooooooooo good") == "soo good"


def test_normalize_timestamp_formats() -> None:
    expected = "2026-01-02T03:04:05+00:00"
    assert normalize_timestamp("2026-01-02T03:04:05Z") == expected
    assert normalize_timestamp("2026-01-02 03:04:05") == expected
    assert normalize_timestamp("2026-01-02") == "2026-01-02T00:00:00+00:00"
    assert normalize_timestamp("not a date") is None
    assert normalize_timestamp(None) is None
    assert normalize_timestamp("") is None


def test_to_int_handles_compact_and_invalid() -> None:
    assert to_int("1,234") == 1234
    assert to_int("1.2K") == 1200
    assert to_int("3M") == 3_000_000
    assert to_int(7) == 7
    assert to_int("abc") is None
    assert to_int(None) is None
    assert to_int(True) is None  # booleans are not counts


def test_extract_hashtags_and_mentions() -> None:
    assert extract_hashtags("look #One and #one and #two") == ["One", "two"]
    assert extract_mentions("hi @alice and @bob and @alice") == ["alice", "bob"]


def test_language_heuristic() -> None:
    assert detect_language("This is a normal english sentence about things") == "en"
    assert detect_language("") == "und"
    assert detect_language("esto es muy bueno y no es terrible") in {"en", "es"}


def test_spam_detection_edge_cases() -> None:
    assert looks_like_spam("") is True
    assert looks_like_spam("a") is True
    assert looks_like_spam("http://only-a-link.example") is True
    assert looks_like_spam("Great video, check http://x.example for more") is False


def test_whitespace_normalization() -> None:
    assert normalize_whitespace("  a   b \n c  ") == "a b c"


def test_report_lists_every_stage() -> None:
    report = clean_records([_record()])["report"]
    assert len(report["steps"]) == 7
    assert all(step["step"] and step["detail"] for step in report["steps"])


def test_output_records_have_required_fields() -> None:
    cleaned = clean_records([_record()])["records"][0]
    for field in (
        "raw_text",
        "clean_text",
        "word_count",
        "char_count",
        "language",
        "published_at",
        "hashtags",
        "mentions",
        "flags",
    ):
        assert field in cleaned
