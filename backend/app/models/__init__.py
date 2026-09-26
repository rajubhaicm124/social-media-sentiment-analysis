"""SQLAlchemy ORM models.

Only aggregate analysis metadata and platform-permitted public fields are
persisted. No credentials, tokens, or private user data are stored.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Analysis(Base):
    """One analysis run for one URL (or one demo dataset)."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)

    # -- provenance -------------------------------------------------------
    source_url: Mapped[str] = mapped_column(String(1024))
    platform: Mapped[str] = mapped_column(String(32), index=True)
    data_mode: Mapped[str] = mapped_column(String(16), default="live")  # live | demo
    status: Mapped[str] = mapped_column(String(24), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # -- subject ----------------------------------------------------------
    content_id: Mapped[str | None] = mapped_column(String(191), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(191), nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    published_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # -- availability flags (never fabricate a metric) --------------------
    available_fields: Mapped[list] = mapped_column(JSON, default=list)
    unavailable_fields: Mapped[list] = mapped_column(JSON, default=list)

    # -- metrics (NULL means "not provided by the platform API") ----------
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subscribers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # -- computed analysis ------------------------------------------------
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    removed_records: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    positive_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    neutral_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    negative_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_sentiment: Mapped[float | None] = mapped_column(Float, nullable=True)
    analysis_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_method: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # -- flexible payloads ------------------------------------------------
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    charts: Mapped[dict] = mapped_column(JSON, default=dict)
    statistics: Mapped[dict] = mapped_column(JSON, default=dict)
    trends: Mapped[dict] = mapped_column(JSON, default=dict)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    insights: Mapped[list] = mapped_column(JSON, default=list)
    limitations: Mapped[list] = mapped_column(JSON, default=list)

    user_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    records: Mapped[list["SocialRecord"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class SocialRecord(Base):
    """A single normalized text record: one comment, caption, or post body."""

    __tablename__ = "social_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )

    record_type: Mapped[str] = mapped_column(String(32), default="comment")
    comment_id: Mapped[str | None] = mapped_column(String(191), nullable=True)
    author_id: Mapped[str | None] = mapped_column(String(191), nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(String(191), nullable=True)

    raw_text: Mapped[str] = mapped_column(Text, default="")
    clean_text: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)

    published_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    like_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reply_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # sentiment
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral", index=True)
    compound: Mapped[float | None] = mapped_column(Float, nullable=True)
    positive_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    negative_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    neutral_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    polarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    subjectivity: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    engines: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # cleaning / NLP extras
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    mentions: Mapped[list] = mapped_column(JSON, default=list)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    emotion: Mapped[str | None] = mapped_column(String(24), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False)
    flags: Mapped[list] = mapped_column(JSON, default=list)

    analysis: Mapped[Analysis] = relationship(back_populates="records")


class Report(Base):
    """Metadata for a generated export artefact."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    report_type: Mapped[str] = mapped_column(String(24))  # csv | excel | pdf
    filename: Mapped[str] = mapped_column(String(255))
    byte_size: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    analysis: Mapped[Analysis] = relationship(back_populates="reports")


__all__ = ["Analysis", "SocialRecord", "Report", "utcnow"]
