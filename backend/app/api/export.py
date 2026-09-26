"""Export endpoints: CSV, Excel workbook, and HTML/PDF report."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app import repository
from app.core.errors import NotFoundError, SocialScopeError
from app.database import get_db
from app.exports import csv_export, excel_export, report
from app.models import Analysis
from app.platforms.demo import DEMO_BANNER

router = APIRouter(tags=["exports"])


def _load(db: Session, analysis_id: str) -> Analysis:
    analysis = repository.get_analysis(db, analysis_id)
    if not analysis:
        raise NotFoundError()
    return analysis


def _context(analysis: Analysis, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Assemble the export context from stored analysis data only."""
    raw = analysis.raw_payload or {}
    metrics = analysis.metrics or {}
    sentiment_status = metrics.get("sentiment_status", {})
    return {
        "analysis_id": analysis.public_id,
        "source_url": analysis.source_url,
        "platform": analysis.platform,
        "data_mode": analysis.data_mode,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "content": raw.get("content", {}),
        "engagement": metrics.get("engagement", {}),
        "sentiment_summary": metrics.get("sentiment_summary", {}),
        "sentiment_status": sentiment_status,
        "sentiment_method": analysis.sentiment_method,
        "user_name": analysis.user_name,
        "total_records": analysis.total_records,
        "removed_records": analysis.removed_records,
        "analysis_seconds": analysis.analysis_seconds,
        "statistics": analysis.statistics or {},
        "keywords": analysis.keywords or [],
        "hashtags": analysis.hashtags or [],
        "insights": analysis.insights or [],
        "limitations": analysis.limitations or [],
        "notes": raw.get("notes", []),
        "unavailable_fields": analysis.unavailable_fields or [],
        "banner": DEMO_BANNER if analysis.data_mode == "demo" else None,
        "cleaning_note": _cleaning_note(raw.get("cleaning_report", {})),
        "sentiment_note": _sentiment_note(sentiment_status),
    }


def _cleaning_note(report_data: dict[str, Any]) -> str:
    if not report_data:
        return ""
    return (
        f"{report_data.get('input_count', 0)} record(s) collected; "
        f"{report_data.get('removed_empty', 0)} empty, "
        f"{report_data.get('removed_duplicate', 0)} duplicate and "
        f"{report_data.get('removed_spam', 0)} spam-like removed; "
        f"{report_data.get('output_count', 0)} analysable record(s) remain."
    )


def _sentiment_note(status: dict[str, Any]) -> str:
    engine = status.get("primary_engine", "unknown")
    blob = "available" if status.get("textblob_available") else "not installed (values estimated)"
    return (
        f"Primary engine: {engine}. TextBlob: {blob}. "
        "Positive when compound >= 0.05, negative when compound <= -0.05, otherwise neutral."
    )


def _download(content: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/analysis/{analysis_id}/export/csv")
def export_csv(
    analysis_id: str,
    dataset: str = Query(default="clean", pattern="^(clean|raw)$"),
    db: Session = Depends(get_db),
) -> Response:
    """Download the dataset as CSV. ``dataset=raw`` returns pre-cleaning records."""
    analysis = _load(db, analysis_id)
    records = repository.all_records(db, analysis)
    if dataset == "raw":
        records = repository.raw_records(db, analysis)
    context = _context(analysis, records)
    content = csv_export.generate_csv(records, context)
    repository.record_export(db, analysis, "csv", f"socialscope_{analysis.public_id}_{dataset}.csv", len(content))
    return _download(
        content, "text/csv; charset=utf-8", f"socialscope_{analysis.platform}_{analysis.public_id}_{dataset}.csv"
    )


@router.get("/analysis/{analysis_id}/export/excel")
def export_excel(analysis_id: str, db: Session = Depends(get_db)) -> Response:
    """Download the multi-sheet formatted workbook."""
    analysis = _load(db, analysis_id)
    records = repository.all_records(db, analysis)
    context = _context(analysis, records)
    try:
        content = excel_export.generate_excel(records, repository.raw_records(db, analysis), context)
    except RuntimeError as exc:
        raise SocialScopeError(
            "Excel export is unavailable because openpyxl is not installed. "
            "Run: pip install -r requirements.txt",
            code="export_dependency_missing",
            status_code=503,
        ) from exc
    repository.record_export(db, analysis, "excel", f"socialscope_{analysis.public_id}.xlsx", len(content))
    return _download(
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        f"socialscope_{analysis.platform}_{analysis.public_id}.xlsx",
    )


@router.get("/analysis/{analysis_id}/export/report")
def export_report(
    analysis_id: str,
    format: str = Query(default="html", pattern="^(html|pdf)$"),
    db: Session = Depends(get_db),
) -> Response:
    """Download the analysis report as styled HTML or PDF."""
    analysis = _load(db, analysis_id)
    records = repository.all_records(db, analysis)
    context = _context(analysis, records)

    if format == "pdf":
        try:
            content = report.generate_pdf(context)
        except RuntimeError as exc:
            raise SocialScopeError(
                "PDF export is unavailable because reportlab is not installed. "
                "Run: pip install -r requirements.txt",
                code="export_dependency_missing",
                status_code=503,
            ) from exc
        media_type = "application/pdf"
        extension = "pdf"
    else:
        content = report.generate_html(context)
        media_type = "text/html; charset=utf-8"
        extension = "html"

    repository.record_export(db, analysis, extension, f"socialscope_{analysis.public_id}.{extension}", len(content))
    return _download(
        content, media_type, f"socialscope_report_{analysis.platform}_{analysis.public_id}.{extension}"
    )
