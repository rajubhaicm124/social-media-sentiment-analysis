"""Analysis endpoints: detect, analyze, demo, and read back results."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.analysis import pipeline
from app.config import settings
from app.core.errors import NotFoundError, SocialScopeError
from app.core.ratelimit import limiter
from app.database import get_db
from app.platforms import collect, describe_platform, detect_platform
from app.platforms.base import CollectedData
from app.platforms.demo import DEMO_BANNER, build_demo
from app import repository
from app.schemas import AnalyzeRequest, DemoRequest, DetectRequest

logger = logging.getLogger("socialscope.analysis")
router = APIRouter(tags=["analysis"])

DEMO_CONTEXT_NOTE = (
    "Demo Mode uses a bundled synthetic dataset. It is stored and exported as "
    "clearly labelled demo data, never as live social-media data."
)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "anonymous"


@router.get("/platforms")
def list_platforms() -> dict[str, Any]:
    """Supported platforms and whether live credentials are configured."""
    credentials = settings.platform_credentials()
    return {
        "platforms": [
            {
                **describe_platform(key),
                "configured": credentials.get(key, False),
                "credential_env_var": describe_platform(key)["credential_env_var"],
            }
            for key in ("youtube", "facebook", "instagram")
        ],
        "demo_mode_enabled": settings.enable_demo_mode,
    }


@router.post("/detect")
def detect(payload: DetectRequest) -> dict[str, Any]:
    """Validate a URL and report the detected platform."""
    platform = detect_platform(payload.url)
    spec = describe_platform(platform)
    return {
        "url": payload.url,
        "platform": platform,
        "platform_label": spec["label"],
        "detected": True,
        "configured": settings.platform_credentials().get(platform, False),
        "message": f"Platform detected successfully — {spec['label']}",
    }


def _analyze_collected(
    collected: CollectedData,
    source_url: str,
    data_mode: str,
    user_name: str | None,
    db: Session,
) -> dict[str, Any]:
    payload = pipeline.run_pipeline(
        collected, source_url=source_url, data_mode=data_mode, user_name=user_name
    )
    analysis = repository.save_analysis(db, payload)
    pipeline.persist_raw_snapshot(payload)
    return _serialize_analysis(db, analysis)


def _run(platform: str, url: str, data_mode: str, user_name: str | None, db: Session) -> dict[str, Any]:
    collected = collect(platform, url)
    return _analyze_collected(collected, url, data_mode, user_name, db)


@router.post("/analyze")
def analyze(payload: AnalyzeRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Detect the platform from the URL, collect available data, and analyse it."""
    limiter.check(_client_key(request))
    platform = detect_platform(payload.url)
    return _run(platform, payload.url, "live", payload.user_name, db)


@router.post("/analyze/youtube")
def analyze_youtube(payload: AnalyzeRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    limiter.check(_client_key(request))
    detected = detect_platform(payload.url)
    if detected != "youtube":
        raise SocialScopeError(
            f"This URL was detected as {detected}, not YouTube. Use /api/analyze for automatic detection.",
            code="platform_mismatch",
            status_code=422,
        )
    return _run("youtube", payload.url, "live", payload.user_name, db)


@router.post("/analyze/facebook")
def analyze_facebook(payload: AnalyzeRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    limiter.check(_client_key(request))
    detected = detect_platform(payload.url)
    if detected != "facebook":
        raise SocialScopeError(
            f"This URL was detected as {detected}, not Facebook. Use /api/analyze for automatic detection.",
            code="platform_mismatch",
            status_code=422,
        )
    return _run("facebook", payload.url, "live", payload.user_name, db)


@router.post("/analyze/instagram")
def analyze_instagram(payload: AnalyzeRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    limiter.check(_client_key(request))
    detected = detect_platform(payload.url)
    if detected != "instagram":
        raise SocialScopeError(
            f"This URL was detected as {detected}, not Instagram. Use /api/analyze for automatic detection.",
            code="platform_mismatch",
            status_code=422,
        )
    return _run("instagram", payload.url, "live", payload.user_name, db)


@router.post("/demo")
def demo(payload: DemoRequest, request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Run the pipeline against a bundled, clearly labelled synthetic dataset."""
    if not settings.enable_demo_mode:
        raise SocialScopeError(
            "Demo mode is disabled on this deployment.", code="demo_disabled", status_code=403
        )
    limiter.check(_client_key(request))

    data = build_demo(payload.platform)
    collected = CollectedData(
        platform=data["platform"],
        content=data["content"],
        records=data["records"],
        available_fields=data["available_fields"],
        unavailable_fields=data["unavailable_fields"],
        notes=data["notes"],
        provenance=data["provenance"],
    )
    result = _analyze_collected(
        collected,
        source_url=f"demo://{payload.platform}/sample",
        data_mode="demo",
        user_name=payload.user_name,
        db=db,
    )
    result["demo_notice"] = DEMO_BANNER
    return result


@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Full analysis payload including records, charts, statistics and insights."""
    analysis = repository.get_analysis(db, analysis_id)
    if not analysis:
        raise NotFoundError()
    records = repository.all_records(db, analysis)
    return _serialize_analysis(db, analysis, records=records)


@router.get("/analysis/{analysis_id}/comments")
def get_comments(
    analysis_id: str,
    search: str | None = None,
    sentiment: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_likes: int | None = None,
    sort: str = "published_at",
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Searchable, sortable, filterable, paginated record table."""
    analysis = repository.get_analysis(db, analysis_id)
    if not analysis:
        raise NotFoundError()

    rows = repository.all_records(db, analysis)
    rows = [r for r in rows if r["record_type"] == "comment"] or rows

    if search:
        needle = search.lower()
        rows = [
            r
            for r in rows
            if needle in (r.get("raw_text") or "").lower()
            or needle in (r.get("author_name") or "").lower()
            or needle in " ".join(r.get("keywords") or []).lower()
            or needle in " ".join(r.get("hashtags") or []).lower()
        ]
    if sentiment and sentiment != "all":
        rows = [r for r in rows if r.get("sentiment") == sentiment]
    if date_from:
        rows = [r for r in rows if (r.get("published_at") or "") >= date_from]
    if date_to:
        rows = [r for r in rows if (r.get("published_at") or "") <= date_to]
    if min_likes is not None:
        rows = [r for r in rows if (r.get("like_count") or 0) >= min_likes]

    reverse = order == "desc"
    if sort == "likes":
        rows.sort(key=lambda r: r.get("like_count") or 0, reverse=reverse)
    elif sort == "sentiment":
        rows.sort(key=lambda r: r.get("compound") or 0, reverse=reverse)
    elif sort == "length":
        rows.sort(key=lambda r: r.get("char_count") or 0, reverse=reverse)
    else:
        rows.sort(key=lambda r: r.get("published_at") or "", reverse=reverse)

    total = len(rows)
    start = (page - 1) * page_size
    return {
        "analysis_id": analysis_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
        "records": rows[start : start + page_size],
    }


@router.get("/analysis/{analysis_id}/sentiment")
def get_sentiment(analysis_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Sentiment summary, distribution, and the VADER vs TextBlob comparison."""
    analysis = repository.get_analysis(db, analysis_id)
    if not analysis:
        raise NotFoundError()
    metrics = analysis.metrics or {}
    return {
        "analysis_id": analysis_id,
        "summary": metrics.get("sentiment_summary", {}),
        "status": metrics.get("sentiment_status", {}),
        "comparison": metrics.get("sentiment_comparison", []),
        "method": analysis.sentiment_method,
    }


@router.get("/analysis/{analysis_id}/engagement")
def get_engagement(analysis_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Engagement metrics with explicit availability for each field."""
    analysis = repository.get_analysis(db, analysis_id)
    if not analysis:
        raise NotFoundError()
    metrics = analysis.metrics or {}
    stats = analysis.statistics or {}
    return {
        "analysis_id": analysis_id,
        "engagement": metrics.get("engagement", {}),
        "comment_engagement": metrics.get("comment_engagement", {}),
        "correlations": stats.get("correlations", {}),
        "unavailable_fields": analysis.unavailable_fields or [],
    }


def _serialize_analysis(
    db: Session,
    analysis: Any,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble the API response for an analysis."""
    if records is None:
        records = repository.all_records(db, analysis)

    raw = analysis.raw_payload or {}
    metrics = analysis.metrics or {}
    return {
        "analysis_id": analysis.public_id,
        "source_url": analysis.source_url,
        "platform": analysis.platform,
        "data_mode": analysis.data_mode,
        "status": analysis.status,
        "user_name": analysis.user_name,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "content": raw.get("content", {}),
        "provenance": raw.get("provenance", {}),
        "notes": raw.get("notes", []),
        "cleaning_report": raw.get("cleaning_report", {}),
        "available_fields": analysis.available_fields or [],
        "unavailable_fields": analysis.unavailable_fields or [],
        "total_records": analysis.total_records,
        "removed_records": analysis.removed_records,
        "analysis_seconds": analysis.analysis_seconds,
        "sentiment_summary": metrics.get("sentiment_summary", {}),
        "sentiment_status": metrics.get("sentiment_status", {}),
        "sentiment_method": analysis.sentiment_method,
        "sentiment_comparison": metrics.get("sentiment_comparison", []),
        "engagement": metrics.get("engagement", {}),
        "comment_engagement": metrics.get("comment_engagement", {}),
        "statistics": analysis.statistics or {},
        "trends": analysis.trends or {},
        "charts": analysis.charts or {},
        "keywords": analysis.keywords or [],
        "hashtags": analysis.hashtags or [],
        "insights": analysis.insights or [],
        "limitations": analysis.limitations or [],
        "records": records,
    }
