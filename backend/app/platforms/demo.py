"""Bundled synthetic demo datasets.

These records are **generated locally, not collected from any platform**. They
exist so the dashboard, charts and exports can be exercised before API keys are
configured. Every analysis produced from them is stored with
``data_mode='demo'`` and labelled as demo data in the API, the UI and the
exports.

Generation is seeded, so the same demo analysis is produced on every machine and
the reported statistics are reproducible.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any

DEMO_BANNER = (
    "DEMO DATA — This dataset is included for demonstration purposes and is not "
    "live social-media data."
)

# (text, sentiment, likes_range) — sentiment labels are part of the generated
# ground truth and are only used to shape the synthetic distribution; the
# pipeline still scores every record independently.
_POSITIVE = [
    "This is genuinely the best explanation I have seen on the topic, thank you!",
    "Amazing work, the editing quality has improved so much since last year.",
    "The presenter is so clear and confident, I learned more in ten minutes than all semester.",
    "Love the practical examples, that finally made it click for me.",
    "Great content as always, subscribed on day one.",
    "This video helped me solve a problem I have had for weeks, incredibly useful.",
    "Fantastic breakdown, very easy to follow and well paced.",
    "The audio quality is excellent and the editing is professional.",
    "I appreciate the honest discussion instead of just hype, really refreshing.",
    "Brilliant idea, never thought about the problem that way before.",
    "Excellent tips, already applied two of them to my own channel.",
    "Such a wholesome video, this made my day a lot better.",
    "Very well researched, the sources at the end are a nice touch.",
    "Superb production value, you can tell a lot of care went into this.",
    "Really good episode, the guest answered every question thoughtfully.",
    "This is a masterpiece of educational content, fantastic job everyone involved.",
    "Very impressed with how much effort went into the research for this.",
    "Perfect length, not too short and not dragging, exactly right.",
    "Highly recommend this to anyone starting out, it is a solid foundation.",
    "The visualisations make a complex idea so easy to grasp, wonderful work.",
    "Lovely community we have here, thank you for keeping it welcoming.",
    "Incredible turnaround on the channel, keep it up!",
]

_NEUTRAL = [
    "Is there a playlist for this series somewhere?",
    "What software did you use for the transition at 4:12?",
    "Does this approach work for older hardware as well?",
    "I tried this last week, the results were roughly what I expected.",
    "Which chapter covers the second part of the topic?",
    "Can you explain the difference between the two versions shown here?",
    "The timestamp in the description seems outdated, just so you know.",
    "I am a bit confused about the third step, could you clarify?",
    "This came out right as I finished my own project on the same topic.",
    "How many episodes are planned for this series?",
    "What microphone are you recording with?",
    "I have a similar setup but I get slightly different numbers, why?",
    "Does this apply to the mobile version of the app as well?",
    "Is there a written version of this available anywhere?",
    "The first half was slower than usual but it made sense in the end.",
    "Just wanted to say I found this through the related videos sidebar.",
    "Which country is the data in the chart collected from?",
    "I have watched this twice now and still learned something new.",
    "Does the free tier include the export feature?",
    "What would you do differently starting from zero experience?",
    "Sure, here is the dataset link in case anyone needs it.",
    "The audio was a bit quiet on my headphones, but otherwise great.",
]

_NEGATIVE = [
    "This is disappointing, the explanation skips the hardest part entirely.",
    "Honestly not useful at all, it feels like it was not researched properly.",
    "The audio quality is terrible and hard to listen to.",
    "Why is the pacing so rushed? Very frustrating to follow.",
    "Bad edit at the halfway mark, it cuts off mid sentence.",
    "This take is wrong, the actual fix is much simpler than described here.",
    "Waste of ten minutes, nothing new in this one.",
    "The clickbait title is misleading, the content does not match it.",
    "I disagree with the conclusion, the data does not support it.",
    "Terrible thumbnail, almost clicked away before starting.",
    "Very shallow treatment of a topic that deserves much more depth.",
    "The presenter keeps mispronouncing the names, it is distracting.",
    "Boring stretch in the middle, it drags badly.",
    "The download link in the description is dead, that is sloppy.",
    "Disagree with the tone, it comes across as arrogant and dismissive.",
    "This feels rushed just to hit the algorithm, quality has dropped a lot.",
    "Wrong information about the pricing, be careful with this one.",
    "Awful experience, the app crashed every single time I tried it.",
    "The comment section is full of spam links, disappointing.",
    "Simply not worth your time, there are far better resources on this.",
]

_AUTHORS = [
    "Aarav Mehta", "Lena Fischer", "Kofi Mensah", "Sofia Rossi", "Daniel Okafor",
    "Yuki Tanaka", "Priya Nair", "Marco Silva", "Emma Laurent", "Noah Berg",
    "Zara Ahmed", "Lucas Moreau", "Hana Kim", "Diego Alvarez", "Ingrid Hansen",
    "Tomas Novak", "Amara Diallo", "Ravi Kapoor", "Chloe Dubois", "Omar Haddad",
]


_QUALIFIERS = [
    "Clear the last three videos helped me a lot.",
    "I shared this with my whole team already.",
    "The pacing in the second half was much better than the first.",
    "Been following this channel for about two years now.",
    "This is the third time I have come back to rewatch it.",
    "The examples are from real projects, not toy scenarios.",
    "Honestly the section on edge cases was the best part.",
    "I tried this approach last quarter with similar results.",
    "Subscribed, notified and bookmarked in one go.",
    "Worth mentioning the audio is much clearer than before.",
    "Even my non-technical friends found it easy to follow.",
    "The summary at the end saved me a lot of time.",
    "I had been doing this the hard way for months.",
    "Would love a follow-up covering the advanced version.",
    "The timestamps in the description are really useful.",
    "This finally answered a question I had for ages.",
    "Compared to other videos on this, this one is thorough.",
    "Genuinely one of the best explanations I have come across.",
    "Not the strongest upload, but still worth watching.",
    "The visual style suits the topic really well.",
]

_HASHTAG_POOL = [
    "datapipeline", "analytics", "datascience", "engineering", "community",
    "workshops", "learningtogether", "design", "studio", "bts", "creators",
    "python", "sql", "cloud", "devrel", "beginners", "deepdive",
]


def _pick_comments(rng: random.Random, sentiment: str) -> str:
    """Build a varied comment from a main clause plus an optional qualifier.

    Combining fragments keeps the corpus mostly unique, which is what a real
    comment section looks like. A pool of a few dozen fixed sentences would
    instead be dominated by exact duplicates that the cleaning pipeline would
    (correctly) remove.
    """
    pool = {"positive": _POSITIVE, "neutral": _NEUTRAL, "negative": _NEGATIVE}[sentiment]
    text = rng.choice(pool)
    if rng.random() < 0.55:
        text = f"{text} {rng.choice(_QUALIFIERS)}"
    return text


def _timestamp(rng: random.Random, published: datetime, spread_hours: int) -> str:
    """Exponentially-distributed comment timing after publication."""
    mean_minutes = max(2.0, spread_hours * 60 / 3)
    offset = timedelta(minutes=rng.expovariate(1 / mean_minutes))
    moment = published + offset
    if moment > datetime.now(timezone.utc):
        moment = datetime.now(timezone.utc) - timedelta(minutes=rng.randint(1, 600))
    return moment.replace(microsecond=0).isoformat()


def _make_records(
    rng: random.Random,
    count: int,
    published: datetime,
    spread_hours: int,
    comment_field: str,
    ratio: tuple[float, float, float] = (0.52, 0.28, 0.20),
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index in range(count):
        draw = rng.random()
        if draw < ratio[0]:
            sentiment = "positive"
        elif draw < ratio[0] + ratio[1]:
            sentiment = "neutral"
        else:
            sentiment = "negative"

        text = _pick_comments(rng, sentiment)
        if rng.random() < 0.22:
            text = f"{text} #{rng.choice(_HASHTAG_POOL)}"
        if rng.random() < 0.10:
            text = f"{text} @{rng.choice(_AUTHORS).split()[0].lower()}"

        likes = None
        if rng.random() < 0.72:
            base = {"positive": (2, 240), "neutral": (0, 60), "negative": (0, 30)}[sentiment]
            likes = int(rng.triangular(base[0], base[1], base[1] / 3))

        records.append(
            {
                "record_type": "comment",
                "comment_id": f"demo_{comment_field}_{index:04d}",
                "parent_id": None,
                "author_id": f"demo_user_{index % len(_AUTHORS):02d}",
                "author_name": _AUTHORS[index % len(_AUTHORS)],
                "raw_text": text,
                "published_at": _timestamp(rng, published, spread_hours),
                "like_count": likes,
                "reply_count": int(rng.triangular(0, 6, 1)) if rng.random() < 0.25 else None,
            }
        )
    return records


def _caption(platform: str, rng: random.Random) -> str:
    if platform == "youtube":
        return (
            "How we rebuilt our entire data pipeline in 90 days — the full walkthrough, "
            "including the mistakes we made. Chapters, sources and the spreadsheet template "
            "are all linked below. #datapipeline #analytics #datascience #engineering"
        )
    if platform == "facebook":
        return (
            "We are opening four new community workshop slots this month. Everyone who has "
            "attended before knows how welcoming these sessions are. Register through the link "
            "in the comments. #community #workshops #learningtogether"
        )
    return (
            "Behind the scenes of the studio build — three weeks of work in thirty seconds. "
            "Save this for later and follow for the full series. #design #studio #bts #creators"
        )


def build_demo(platform: str) -> dict[str, Any]:
    """Return a ``CollectedData``-shaped dict of synthetic records."""
    rng = random.Random({"youtube": 20260101, "facebook": 20260202, "instagram": 20260303}[platform])
    now = datetime.now(timezone.utc).replace(microsecond=0)
    published = now - timedelta(days=rng.randint(3, 12), hours=rng.randint(0, 20))

    if platform == "youtube":
        content = {
            "content_id": "DEMO_dQw4w9WgXcQ",
            "video_id": "DEMO_dQw4w9WgXcQ",
            "channel_id": "DEMO_UCdemoChannel0001",
            "channel_name": "DataScope Lab (Demo)",
            "title": "Rebuilding a Data Pipeline in 90 Days (Demo Sample)",
            "description": _caption("youtube", rng),
            "published_at": published.isoformat(),
            "category_id": "28",
            "language": "en",
            "thumbnail_url": None,
            "duration_seconds": 1_482,
            "duration": "24:42",
            "views": 1_284_500,
            "likes": 96_120,
            "comment_count": 2_186,
            "shares": None,
            "tags": ["datapipeline", "analytics", "datascience"],
            "hashtags": ["datapipeline", "analytics", "datascience", "engineering"],
        }
        records = _make_records(rng, 220, published, 72, "yt")
        available = ["views", "likes", "comments", "caption", "published_at", "author", "duration", "tags"]
        unavailable = ["shares", "subscribers", "thumbnail"]
    elif platform == "facebook":
        content = {
            "content_id": "DEMO_900000000000001",
            "post_id": "DEMO_900000000000001",
            "page_id": "DEMO_PAGE_0001",
            "page_name": "Community Learning Hub (Demo)",
            "author_name": "Community Learning Hub (Demo)",
            "title": "Community workshop slots open (Demo Sample)",
            "description": _caption("facebook", rng),
            "caption": _caption("facebook", rng),
            "published_at": published.isoformat(),
            "content_type": "post",
            "thumbnail_url": None,
            "permalink": None,
            "views": 41_300,
            "likes": 3_180,
            "reactions": 3_180,
            "comment_count": 486,
            "shares": 214,
        }
        records = _make_records(rng, 170, published, 96, "fb", ratio=(0.44, 0.31, 0.25))
        available = ["views", "likes", "comments", "shares", "caption", "published_at", "author"]
        unavailable = ["subscribers", "tags", "duration", "thumbnail"]
    else:
        content = {
            "content_id": "DEMO_17890000000000000",
            "media_id": "DEMO_17890000000000000",
            "shortcode": "DEMOpost01",
            "username": "studio.by.demo",
            "author_name": "studio.by.demo",
            "caption": _caption("instagram", rng),
            "description": _caption("instagram", rng),
            "published_at": published.isoformat(),
            "media_type": "REELS",
            "thumbnail_url": None,
            "permalink": None,
            "views": 318_900,
            "reach": 284_400,
            "impressions": 402_100,
            "likes": 27_640,
            "comment_count": 1_042,
            "shares": None,
            "hashtags": ["design", "studio", "bts", "creators"],
        }
        records = _make_records(rng, 190, published, 60, "ig", ratio=(0.61, 0.22, 0.17))
        available = ["views", "likes", "comments", "caption", "published_at", "author", "tags"]
        unavailable = ["shares", "subscribers", "duration", "thumbnail"]

    # A caption is analysed as its own text record, mirroring live collection.
    records.insert(
        0,
        {
            "record_type": "caption",
            "comment_id": f"caption:DEMO_{platform}",
            "parent_id": None,
            "author_id": content.get("channel_id") or content.get("page_id") or content.get("username"),
            "author_name": content.get("channel_name") or content.get("page_name") or content.get("username"),
            "raw_text": content.get("description") or content.get("caption") or "",
            "published_at": content.get("published_at"),
            "like_count": None,
            "reply_count": None,
        },
    )

    # Deliberate data-quality noise so the cleaning report is non-trivial.
    records.append({**records[5], "comment_id": f"demo_{platform}_dup_0001"})  # duplicate ID
    duplicate_text = dict(records[12])
    duplicate_text["comment_id"] = f"demo_{platform}_dup_0002"
    records.append(duplicate_text)  # duplicate text
    records.append(
        {
            "record_type": "comment",
            "comment_id": f"demo_{platform}_empty_0001",
            "parent_id": None,
            "author_id": "demo_user_99",
            "author_name": "Demo User",
            "raw_text": "   ",
            "published_at": published.isoformat(),
            "like_count": None,
            "reply_count": None,
        }
    )
    records.append(
        {
            "record_type": "comment",
            "comment_id": f"demo_{platform}_spam_0001",
            "parent_id": None,
            "author_id": "demo_user_spam",
            "author_name": "Demo Spammer",
            "raw_text": "FREE crypto giveaway http://a.example http://b.example click now",
            "published_at": published.isoformat(),
            "like_count": None,
            "reply_count": None,
        }
    )

    return {
        "platform": platform,
        "content": content,
        "records": records,
        "available_fields": available,
        "unavailable_fields": unavailable,
        "notes": [
            DEMO_BANNER,
            f"Synthetic content, comments and engagement totals generated locally for {platform}.",
            "These figures are not real and must not be cited as platform metrics.",
        ],
        "provenance": {
            "api": "Local synthetic generator (no external API called)",
            "generator_seed": {"youtube": 20260101, "facebook": 20260202, "instagram": 20260303}[platform],
            "data_mode": "demo",
        },
    }
