"""URL validation and platform detection."""

from __future__ import annotations

import pytest

from app.core.errors import InvalidURLError, UnsupportedPlatformError
from app.platforms.detector import (
    describe_platform,
    detect_platform,
    extract_facebook_id,
    extract_instagram_shortcode,
    extract_youtube_id,
)
from app.core.urls import parse_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s", "youtube"),
        ("https://youtu.be/dQw4w9WgXcQ", "youtube"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "youtube"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("youtube.com/watch?v=dQw4w9WgXcQ", "youtube"),
        ("https://www.facebook.com/1234567890/posts/987654321", "facebook"),
        ("https://fb.watch/abcdef/", "facebook"),
        ("https://m.facebook.com/story.php?story_fbid=1234567890", "facebook"),
        ("https://www.instagram.com/p/C1AbCdEfGhI/", "instagram"),
        ("https://www.instagram.com/reel/C1AbCdEfGhI/", "instagram"),
        ("https://www.instagram.com/tv/C1AbCdEfGhI/", "instagram"),
    ],
)
def test_detects_supported_platforms(url: str, expected: str) -> None:
    assert detect_platform(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://twitter.com/user/status/1",
        "https://tiktok.com/@user",
        "https://www.linkedin.com/feed/update/1",
        "https://evil.com/youtube.com/watch?v=x",
        "https://notyoutube.com/watch?v=x",
    ],
)
def test_rejects_unsupported_hosts(url: str) -> None:
    with pytest.raises(UnsupportedPlatformError):
        detect_platform(url)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "not a url at all",
        "javascript:alert(1)",
        "data:text/html,<h1>x</h1>",
        "file:///etc/passwd",
        "http://localhost:8000",
        "http://127.0.0.1",
    ],
)
def test_rejects_malformed_or_unsafe_urls(url: str) -> None:
    with pytest.raises((InvalidURLError, UnsupportedPlatformError)):
        detect_platform(url)


def test_parses_youtube_id_variants() -> None:
    assert extract_youtube_id(parse_url("https://youtu.be/dQw4w9WgXcQ")) == "dQw4w9WgXcQ"
    assert extract_youtube_id(parse_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")) == "dQw4w9WgXcQ"
    assert extract_youtube_id(parse_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")) == "dQw4w9WgXcQ"
    # A channel URL has no single video id.
    assert extract_youtube_id(parse_url("https://www.youtube.com/@somechannel")) is None


def test_parses_instagram_shortcode() -> None:
    assert extract_instagram_shortcode(parse_url("https://www.instagram.com/p/C1AbCdEfGhI/")) == "C1AbCdEfGhI"
    assert extract_instagram_shortcode(parse_url("https://instagram.com/reel/AbCdEfGhIjK/")) == "AbCdEfGhIjK"
    assert extract_instagram_shortcode(parse_url("https://www.instagram.com/someuser/")) is None


def test_parses_facebook_id() -> None:
    assert extract_facebook_id(parse_url("https://www.facebook.com/1234567890/posts/987654321")) == "987654321"
    assert extract_facebook_id(parse_url("https://www.facebook.com/watch/?v=1234567890")) == "1234567890"


def test_platform_descriptions_expose_limitations() -> None:
    for key in ("youtube", "facebook", "instagram"):
        described = describe_platform(key)
        assert described["label"]
        assert described["credential_env_var"]
        assert described["limitations"], "every platform must document its API limitations"
        assert described["url_examples"]


def test_youtube_documents_missing_share_count() -> None:
    limitations = " ".join(describe_platform("youtube")["limitations"]).lower()
    assert "share" in limitations
