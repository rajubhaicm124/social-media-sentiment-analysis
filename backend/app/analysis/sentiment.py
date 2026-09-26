"""Sentiment analysis using VADER (primary) and TextBlob (comparison).

Both engines are optional dependencies at runtime. Whichever engine is actually
available is recorded in the output so the UI can state the method used instead
of implying a model that did not run.

Classification thresholds follow the conventional VADER cut-offs:

    compound >= 0.05  -> positive
    compound <= -0.05 -> negative
    otherwise          -> neutral
"""

from __future__ import annotations

from typing import Any

from app.config import settings

POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05

# --- VADER -----------------------------------------------------------------
try:  # pragma: no cover - import guard
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    _VADER = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except Exception:  # pragma: no cover
    _VADER = None
    VADER_AVAILABLE = False

# --- TextBlob --------------------------------------------------------------
try:  # pragma: no cover - import guard
    from textblob import TextBlob as _TextBlob

    TEXTBLOB_AVAILABLE = True
except Exception:  # pragma: no cover
    _TextBlob = None
    TEXTBLOB_AVAILABLE = False


def classify(compound: float | None) -> str:
    if compound is None:
        return "neutral"
    if compound >= POSITIVE_THRESHOLD:
        return "positive"
    if compound <= NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def vader_scores(text: str) -> dict[str, Any] | None:
    """Return VADER pos/neg/neu/compound scores, or ``None`` if unavailable."""
    if not VADER_AVAILABLE or not (text or "").strip():
        return None
    scores = _VADER.polarity_scores(text)
    return {
        "positive": round(float(scores["pos"]), 6),
        "negative": round(float(scores["neg"]), 6),
        "neutral": round(float(scores["neu"]), 6),
        "compound": round(float(scores["compound"]), 6),
    }


def textblob_scores(text: str) -> dict[str, Any] | None:
    """Return TextBlob polarity/subjectivity, or ``None`` if unavailable."""
    if not TEXTBLOB_AVAILABLE or not (text or "").strip():
        return None
    try:
        blob = _TextBlob(text)
        return {
            "polarity": round(float(blob.sentiment.polarity), 6),
            "subjectivity": round(float(blob.sentiment.subjectivity), 6),
        }
    except Exception:
        # TextBlob needs NLTK corpora that may be absent on a fresh machine.
        return None


def lexicon_fallback(text: str) -> dict[str, Any]:
    """Dependency-free polarity estimate used only if VADER is missing."""
    from app.analysis.cleaning import content_tokens

    tokens = set(content_tokens(text))
    if not tokens:
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}
    positive_hits = len(tokens & _POSITIVE_WORDS)
    negative_hits = len(tokens & _NEGATIVE_WORDS)
    total = positive_hits + negative_hits
    if total == 0:
        return {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "compound": 0.0}
    compound = (positive_hits - negative_hits) / total
    return {
        "positive": round(positive_hits / (total + 1), 6),
        "negative": round(negative_hits / (total + 1), 6),
        "neutral": round(1 / (total + 1), 6),
        "compound": round(compound, 6),
    }


_POSITIVE_WORDS = frozenset(
    """amazing awesome beautiful best brilliant brilliant clean delightful excellent fantastic
    good great happy helpful incredible love loved lovely nice perfect superb thanks thank wonderful
    worth genius impressive fun cool enjoyable useful solid smooth clear favorite fav brilliant
    quality reliable recommend recommended brilliant""".split()
)
_NEGATIVE_WORDS = frozenset(
    """awful bad boring broken buggy cheap confusing crash crashed disappointing dislike
    disappointed garbage hate hated horrible poor slow terrible ugly useless waste worst wrong
    buggy laggy freeze frozen fail failed failing""".split()
)


def _subjectivity_estimate(text: str) -> float:
    """Fallback subjectivity when TextBlob/NLTK data is unavailable."""
    from app.analysis.cleaning import tokenize

    tokens = tokenize(text)
    if not tokens:
        return 0.0
    subjective = len(set(tokens) & (_POSITIVE_WORDS | _NEGATIVE_WORDS))
    return round(min(1.0, subjective / len(tokens) * 3), 4)


def engine_status() -> dict[str, Any]:
    """Describe which sentiment engines are active in this deployment."""
    backend = settings.sentiment_backend.lower()
    if backend == "vader" and not VADER_AVAILABLE:
        engine = "lexicon"
    elif backend == "lexicon":
        engine = "lexicon"
    else:
        engine = "vader" if VADER_AVAILABLE else "lexicon"
    return {
        "primary_engine": engine,
        "vader_available": VADER_AVAILABLE,
        "textblob_available": TEXTBLOB_AVAILABLE,
        "positive_threshold": POSITIVE_THRESHOLD,
        "negative_threshold": NEGATIVE_THRESHOLD,
        "description": (
            "VADER (valence-aware rule-based) with TextBlob polarity/subjectivity comparison"
            if VADER_AVAILABLE
            else "Dependency-free lexicon fallback; install vaderSentiment for VADER scores"
        ),
    }


def score_text(text: str) -> dict[str, Any]:
    """Score one text and return every field the dataset and UI need."""
    primary = vader_scores(text) if VADER_AVAILABLE else None
    if primary is None:
        primary = lexicon_fallback(text)
        used = "lexicon"
    else:
        used = "vader"

    comparison = textblob_scores(text)
    if comparison is None:
        comparison = {
            "polarity": primary["compound"],
            "subjectivity": _subjectivity_estimate(text),
        }
        comparison_source = "estimated"
    else:
        comparison_source = "textblob"

    compound = primary["compound"]
    sentiment = classify(compound)
    # Confidence reflects distance from the neutral band, not statistical truth.
    confidence = round(min(1.0, abs(compound)), 4)

    return {
        "sentiment": sentiment,
        "compound": compound,
        "positive": primary["positive"],
        "negative": primary["negative"],
        "neutral": primary["neutral"],
        "polarity": comparison["polarity"],
        "subjectivity": comparison["subjectivity"],
        "final_score": compound,
        "confidence": confidence,
        "engines": {
            "primary": used,
            "vader": primary,
            "textblob": comparison,
            "textblob_source": comparison_source,
        },
    }


def analyze_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Score every record and summarize the distribution."""
    scored: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []

    for record in records:
        result = score_text(record.get("clean_text") or record.get("raw_text") or "")
        enriched = {**record, **result}
        enriched["keywords"] = record.get("keywords", [])
        enriched["emotion"] = detect_emotion(result["compound"], record.get("raw_text", ""))
        scored.append(enriched)

        vader = result["engines"]["vader"] or {}
        comparison_rows.append(
            {
                "comment_id": record.get("comment_id"),
                "text": (record.get("raw_text") or "")[:160],
                "vader_compound": vader.get("compound"),
                "textblob_polarity": result["engines"]["textblob"]["polarity"],
                "textblob_subjectivity": result["engines"]["textblob"]["subjectivity"],
                "sentiment": result["sentiment"],
            }
        )

    summary = summarize(scored)
    return {"records": scored, "summary": summary, "comparison": comparison_rows}


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    if not total:
        return {
            "total": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "positive_pct": 0.0,
            "neutral_pct": 0.0,
            "negative_pct": 0.0,
            "avg_compound": 0.0,
            "avg_polarity": 0.0,
            "avg_subjectivity": 0.0,
            "distribution": [],
        }

    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for record in records:
        counts[record.get("sentiment", "neutral")] = counts.get(record.get("sentiment", "neutral"), 0) + 1

    def mean(field: str) -> float:
        values = [r[field] for r in records if isinstance(r.get(field), (int, float))]
        return round(sum(values) / len(values), 6) if values else 0.0

    return {
        "total": total,
        **counts,
        "positive_pct": round(counts["positive"] / total * 100, 2),
        "neutral_pct": round(counts["neutral"] / total * 100, 2),
        "negative_pct": round(counts["negative"] / total * 100, 2),
        "avg_compound": mean("compound"),
        "avg_polarity": mean("polarity"),
        "avg_subjectivity": mean("subjectivity"),
        "distribution": [
            {"name": "Positive", "key": "positive", "value": counts["positive"]},
            {"name": "Neutral", "key": "neutral", "value": counts["neutral"]},
            {"name": "Negative", "key": "negative", "value": counts["negative"]},
        ],
    }


_EMOTION_CUES = {
    "joy": ("love", "amazing", "awesome", "great", "excellent", "happy", "brilliant", "wonderful"),
    "anger": ("hate", "awful", "terrible", "worst", "furious", "annoying", "useless", "garbage"),
    "sadness": ("sad", "sorry", "unfortunate", "disappointed", "missing", "lost", "cry"),
    "surprise": ("wow", "unbelievable", "did not expect", "shocking", "incredible", "no way"),
}


def detect_emotion(compound: float | None, text: str) -> str:
    """Coarse emotion tag from lexical cues plus overall valence."""
    lowered = (text or "").lower()
    for emotion, cues in _EMOTION_CUES.items():
        if any(cue in lowered for cue in cues):
            return emotion
    if compound is None:
        return "neutral"
    if compound >= 0.3:
        return "joy"
    if compound <= -0.3:
        return "anger"
    return "neutral"
