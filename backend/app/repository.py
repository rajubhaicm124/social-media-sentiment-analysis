"""Persistence layer: convert pipeline payloads to and from the database."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Analysis, Report, SocialRecord


def save_analysis(db: Session, payload: dict[str, Any]) -> Analysis:
    """Persist a completed analysis and its cleaned records."""
    content = payload.get("content", {})
    summary = payload.get("sentiment_summary", {})
    engagement = payload.get("engagement", {})

    analysis = Analysis(
        public_id=payload["public_id"],
        source_url=payload["source_url"],
        platform=payload["platform"],
        data_mode=payload.get("data_mode", "live"),
        status=payload.get("status", "completed"),
        content_id=content.get("content_id"),
        channel_id=content.get("channel_id"),
        author_name=content.get("channel_name") or content.get("page_name") or content.get("username"),
        title=content.get("title") or (content.get("caption") or "")[:120] or None,
        content_type=content.get("content_type") or content.get("media_type"),
        published_at=content.get("published_at"),
        thumbnail_url=content.get("thumbnail_url"),
        available_fields=payload.get("available_fields", []),
        unavailable_fields=payload.get("unavailable_fields", []),
        views=engagement.get("views"),
        likes=engagement.get("likes"),
        comment_count=engagement.get("comments"),
        shares=engagement.get("shares"),
        subscribers=engagement.get("subscribers"),
        total_records=payload.get("total_records", 0),
        removed_records=payload.get("removed_records", 0),
        engagement_rate=engagement.get("engagement_rate"),
        positive_pct=summary.get("positive_pct"),
        neutral_pct=summary.get("neutral_pct"),
        negative_pct=summary.get("negative_pct"),
        avg_sentiment=summary.get("avg_compound"),
        analysis_seconds=payload.get("analysis_seconds", 0.0),
        sentiment_method=payload.get("sentiment_method"),
        raw_payload={
            "content": content,
            "raw_records": payload.get("raw_records", []),
            "cleaning_report": payload.get("cleaning_report", {}),
            "provenance": payload.get("provenance", {}),
            "notes": payload.get("notes", []),
        },
        metrics={
            "engagement": engagement,
            "comment_engagement": payload.get("comment_engagement", {}),
            "sentiment_summary": summary,
            "sentiment_comparison": payload.get("sentiment_comparison", []),
            "sentiment_status": payload.get("sentiment_status", {}),
        },
        charts=payload.get("charts", {}),
        statistics=payload.get("statistics", {}),
        trends=payload.get("trends", {}),
        keywords=payload.get("keywords", []),
        hashtags=payload.get("hashtags", []),
        insights=payload.get("insights", []),
        limitations=payload.get("limitations", []),
        user_name=payload.get("user_name"),
    )
    db.add(analysis)
    db.flush()

    for record in payload.get("records", []):
        db.add(
            SocialRecord(
                analysis_id=analysis.id,
                record_type=record.get("record_type", "comment"),
                comment_id=record.get("comment_id"),
                author_id=record.get("author_id"),
                author_name=record.get("author_name"),
                parent_id=record.get("parent_id"),
                raw_text=record.get("raw_text", ""),
                clean_text=record.get("clean_text", ""),
                word_count=record.get("word_count", 0),
                char_count=record.get("char_count", 0),
                language=record.get("language"),
                published_at=record.get("published_at"),
                like_count=record.get("like_count"),
                reply_count=record.get("reply_count"),
                sentiment=record.get("sentiment", "neutral"),
                compound=record.get("compound"),
                positive_score=record.get("positive"),
                negative_score=record.get("negative"),
                neutral_score=record.get("neutral"),
                polarity=record.get("polarity"),
                subjectivity=record.get("subjectivity"),
                final_score=record.get("final_score"),
                confidence=record.get("confidence"),
                engines=record.get("engines"),
                hashtags=record.get("hashtags", []),
                mentions=record.get("mentions", []),
                keywords=record.get("keywords", []),
                emotion=record.get("emotion"),
                is_duplicate=bool(record.get("is_duplicate")),
                is_spam=bool(record.get("is_spam")),
                is_outlier=bool(record.get("is_outlier")),
                flags=record.get("flags", []),
            )
        )

    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis(db: Session, public_id: str) -> Analysis | None:
    return db.execute(
        select(Analysis).where(Analysis.public_id == public_id)
    ).scalar_one_or_none()


def delete_analysis(db: Session, public_id: str) -> bool:
    analysis = get_analysis(db, public_id)
    if not analysis:
        return False
    db.execute(delete(SocialRecord).where(SocialRecord.analysis_id == analysis.id))
    db.execute(delete(Report).where(Report.analysis_id == analysis.id))
    db.delete(analysis)
    db.commit()
    return True


def record_export(db: Session, analysis: Analysis, report_type: str, filename: str, size: int) -> None:
    db.add(
        Report(
            analysis_id=analysis.id,
            report_type=report_type,
            filename=filename,
            byte_size=size,
        )
    )
    db.commit()


def list_history(
    db: Session,
    user_name: str | None = None,
    platform: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    stmt = select(Analysis).order_by(Analysis.created_at.desc()).limit(limit)
    if user_name:
        stmt = stmt.where(Analysis.user_name == user_name)
    if platform:
        stmt = stmt.where(Analysis.platform == platform)
    rows = db.execute(stmt).scalars().all()
    return [history_row(row) for row in rows]


def history_row(analysis: Analysis) -> dict[str, Any]:
    return {
        "analysis_id": analysis.public_id,
        "url": analysis.source_url,
        "platform": analysis.platform,
        "title": analysis.title,
        "author": analysis.author_name,
        "data_mode": analysis.data_mode,
        "status": analysis.status,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "total_records": analysis.total_records,
        "removed_records": analysis.removed_records,
        "views": analysis.views,
        "likes": analysis.likes,
        "comment_count": analysis.comment_count,
        "shares": analysis.shares,
        "engagement_rate": analysis.engagement_rate,
        "positive_pct": analysis.positive_pct,
        "neutral_pct": analysis.neutral_pct,
        "negative_pct": analysis.negative_pct,
        "avg_sentiment": analysis.avg_sentiment,
        "sentiment_method": analysis.sentiment_method,
        "analysis_seconds": analysis.analysis_seconds,
        "user_name": analysis.user_name,
    }


def user_stats(db: Session, user_name: str | None) -> dict[str, Any]:
    """Profile aggregates for the dashboard."""
    stmt = select(Analysis)
    if user_name:
        stmt = stmt.where(Analysis.user_name == user_name)
    rows = db.execute(stmt.order_by(Analysis.created_at.desc())).scalars().all()

    total_records = sum(r.total_records or 0 for r in rows)
    sentiments = [r.avg_sentiment for r in rows if r.avg_sentiment is not None]
    platform_counts: dict[str, int] = {}
    for row in rows:
        platform_counts[row.platform] = platform_counts.get(row.platform, 0) + 1

    favorite = max(platform_counts, key=platform_counts.get) if platform_counts else None
    last = rows[0] if rows else None

    return {
        "user_name": user_name,
        "total_analyses": len(rows),
        "total_records_analyzed": total_records,
        "total_comments_analyzed": total_records,
        "average_sentiment": round(sum(sentiments) / len(sentiments), 4) if sentiments else None,
        "favorite_platform": favorite,
        "platform_breakdown": platform_counts,
        "last_analysis": history_row(last) if last else None,
        "first_analysis_at": rows[-1].created_at.isoformat() if rows else None,
    }


def all_records(db: Session, analysis: Analysis) -> list[dict[str, Any]]:
    rows = db.execute(
        select(SocialRecord)
        .where(SocialRecord.analysis_id == analysis.id)
        .order_by(SocialRecord.id)
    ).scalars().all()
    return [serialize_record(row) for row in rows]


def serialize_record(record: SocialRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "record_type": record.record_type,
        "comment_id": record.comment_id,
        "author_id": record.author_id,
        "author_name": record.author_name,
        "parent_id": record.parent_id,
        "raw_text": record.raw_text,
        "clean_text": record.clean_text,
        "word_count": record.word_count,
        "char_count": record.char_count,
        "language": record.language,
        "published_at": record.published_at,
        "like_count": record.like_count,
        "reply_count": record.reply_count,
        "sentiment": record.sentiment,
        "compound": record.compound,
        "positive": record.positive_score,
        "negative": record.negative_score,
        "neutral": record.neutral_score,
        "polarity": record.polarity,
        "subjectivity": record.subjectivity,
        "final_score": record.final_score,
        "confidence": record.confidence,
        "engines": record.engines or {},
        "hashtags": record.hashtags or [],
        "mentions": record.mentions or [],
        "keywords": record.keywords or [],
        "emotion": record.emotion,
        "is_duplicate": record.is_duplicate,
        "is_spam": record.is_spam,
        "is_outlier": record.is_outlier,
        "flags": record.flags or [],
    }


def raw_records(db: Session, analysis: Analysis) -> list[dict[str, Any]]:
    return analysis.raw_payload.get("raw_records", []) or []


def records_count(db: Session, analysis_id: int) -> int:
    return db.execute(
        select(func.count()).select_from(SocialRecord).where(SocialRecord.analysis_id == analysis_id)
    ).scalar_one()


def dumps(value: Any) -> str:
    return json.dumps(value, default=str)
