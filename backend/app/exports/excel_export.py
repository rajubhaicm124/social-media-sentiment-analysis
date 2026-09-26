"""Multi-sheet Excel (XLSX) export.

Sheets follow the DAE project brief:

    1. Summary            5. Engagement Analysis
    2. Raw Data           6. Keywords
    3. Clean Data         7. Hashtags
    4. Sentiment Analysis 8. VADER vs TextBlob

Styling: frozen headers, autofilters, sized columns, number and date formats.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    OPENPYXL_AVAILABLE = True
except Exception:  # pragma: no cover
    OPENPYXL_AVAILABLE = False

HEADER_FILL = PatternFill("solid", fgColor="1B2A4A")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14, color="1B2A4A")
NOTE_FONT = Font(italic=True, size=9, color="8A94A6")
THIN = Side(style="thin", color="D8DEE9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CLEAN_COLUMNS = [
    ("record_type", "Record Type", None),
    ("comment_id", "Comment ID", None),
    ("author_name", "Author", None),
    ("parent_id", "Parent ID", None),
    ("raw_text", "Original Text", 60),
    ("clean_text", "Cleaned Text", 60),
    ("published_at", "Published At", 22),
    ("language", "Language", 10),
    ("word_count", "Words", 8),
    ("char_count", "Characters", 11),
    ("like_count", "Likes", 9),
    ("reply_count", "Replies", 9),
    ("sentiment", "Sentiment", 12),
    ("compound", "Compound", 12),
    ("positive", "Positive", 10),
    ("negative", "Negative", 10),
    ("neutral", "Neutral", 10),
    ("polarity", "Polarity", 10),
    ("subjectivity", "Subjectivity", 12),
    ("emotion", "Emotion", 12),
    ("hashtags", "Hashtags", 24),
    ("keywords", "Keywords", 34),
    ("is_outlier", "Outlier", 9),
    ("flags", "Flags", 16),
]

SENTIMENT_COLUMNS = [
    ("comment_id", "Comment ID", None),
    ("author_name", "Author", None),
    ("raw_text", "Text", 70),
    ("sentiment", "Final Sentiment", 15),
    ("final_score", "Final Score", 12),
    ("vader_compound", "VADER Compound", 15),
    ("vader_pos", "VADER Pos", 11),
    ("vader_neg", "VADER Neg", 11),
    ("vader_neu", "VADER Neu", 11),
    ("textblob_polarity", "TextBlob Polarity", 16),
    ("textblob_subjectivity", "TextBlob Subjectivity", 19),
    ("confidence", "Confidence", 11),
    ("emotion", "Emotion", 12),
]

ENGAGEMENT_COLUMNS = [
    ("metric", "Metric", 26),
    ("value", "Value", 18),
    ("available", "Available via API", 17),
    ("note", "Note", 70),
]

RAW_COLUMNS = [
    ("comment_id", "Comment ID", None),
    ("author_name", "Author", None),
    ("raw_text", "Original Text", 70),
    ("published_at", "Published At", 22),
    ("like_count", "Likes", 9),
    ("reply_count", "Replies", 9),
]


def _style_header(
    sheet, row: int, columns: list[tuple[str, str, int | None]], freeze: bool = True
) -> None:
    for index, (_, title, _) in enumerate(columns, start=1):
        cell = sheet.cell(row=row, column=index, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center", horizontal="left", wrap_text=True)
        cell.border = BORDER
    if freeze:
        sheet.freeze_panes = sheet.cell(row=row + 1, column=1)
    sheet.auto_filter.ref = f"A{row}:{get_column_letter(len(columns))}{row}"


def _set_widths(sheet, columns: list[tuple[str, str, int | None]]) -> None:
    for index, (_, title, width) in enumerate(columns, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width or max(12, len(title) + 4)


def _write_table(
    sheet,
    title: str,
    columns: list[tuple[str, str, int | None]],
    rows: list[dict[str, Any]],
    note: str | None = None,
    start_row: int = 1,
    freeze: bool = True,
) -> None:
    """Write a titled, styled table. ``start_row`` allows stacking blocks."""
    sheet.cell(row=start_row, column=1, value=title).font = TITLE_FONT
    row_index = start_row + 1
    if note:
        sheet.cell(row=row_index, column=1, value=note).font = NOTE_FONT
        row_index += 1
    row_index += 1  # spacer row

    header_row = row_index
    _style_header(sheet, header_row, columns, freeze=freeze)
    _set_widths(sheet, columns)

    for record in rows:
        row_index += 1
        for index, (key, _, _) in enumerate(columns, start=1):
            value = record.get(key)
            cell = sheet.cell(row=row_index, column=index)
            if isinstance(value, (list, tuple, dict)):
                cell.value = ", ".join(str(v) for v in value) if not isinstance(value, dict) else str(value)
            elif isinstance(value, bool):
                cell.value = "yes" if value else "no"
            else:
                cell.value = value
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cell.number_format = "0.####"

    if rows:
        sheet.auto_filter.ref = f"A{header_row}:{get_column_letter(len(columns))}{row_index}"
    return row_index


def _kpis(analysis_context: dict[str, Any]) -> list[dict[str, Any]]:
    engagement = analysis_context.get("engagement", {})
    summary = analysis_context.get("sentiment_summary", {})
    stats = analysis_context.get("statistics", {})
    return [
        {"metric": "Total text records", "value": analysis_context.get("total_records", 0), "available": True, "note": "Cleaned and analysable records"},
        {"metric": "Records removed", "value": analysis_context.get("removed_records", 0), "available": True, "note": "Empty, duplicate or spam-like rows dropped by the cleaning pipeline"},
        {"metric": "Views", "value": engagement.get("views"), "available": engagement.get("views") is not None, "note": "Platform API view count"},
        {"metric": "Likes", "value": engagement.get("likes"), "available": engagement.get("likes") is not None, "note": "Platform API like count"},
        {"metric": "Comments", "value": engagement.get("comments"), "available": engagement.get("comments") is not None, "note": "Platform API comment count"},
        {"metric": "Shares", "value": engagement.get("shares"), "available": engagement.get("shares") is not None, "note": "Data unavailable through the current platform API." if engagement.get("shares") is None else "Platform API share count"},
        {"metric": "Engagement rate (%)", "value": engagement.get("engagement_rate"), "available": engagement.get("engagement_rate") is not None, "note": "(interactions) / views x 100 — interactions included: " + (", ".join(engagement.get("interactions_included", [])) or "none")},
        {"metric": "Positive %", "value": summary.get("positive_pct"), "available": True, "note": f"Sentiment engine: {analysis_context.get('sentiment_method')}"},
        {"metric": "Neutral %", "value": summary.get("neutral_pct"), "available": True, "note": "VADER compound between -0.05 and 0.05"},
        {"metric": "Negative %", "value": summary.get("negative_pct"), "available": True, "note": "VADER compound <= -0.05"},
        {"metric": "Average compound score", "value": summary.get("avg_compound"), "available": True, "note": "Mean VADER compound across analysed records"},
        {"metric": "Average polarity (TextBlob)", "value": summary.get("avg_polarity"), "available": True, "note": "TextBlob polarity, or an estimate if TextBlob is unavailable"},
        {"metric": "Average subjectivity (TextBlob)", "value": summary.get("avg_subjectivity"), "available": True, "note": "TextBlob subjectivity, or an estimate if TextBlob is unavailable"},
        {"metric": "Average comment length (chars)", "value": stats.get("comment_length", {}).get("characters", {}).get("mean"), "available": True, "note": "Mean character count of cleaned text"},
        {"metric": "Analysis time (seconds)", "value": analysis_context.get("analysis_seconds"), "available": True, "note": "Server-side pipeline duration"},
    ]


def _sentiment_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        engines = record.get("engines") or {}
        vader = engines.get("vader") or {}
        textblob = engines.get("textblob") or {}
        rows.append(
            {
                "comment_id": record.get("comment_id"),
                "author_name": record.get("author_name"),
                "raw_text": record.get("raw_text"),
                "sentiment": record.get("sentiment"),
                "final_score": record.get("final_score"),
                "vader_compound": vader.get("compound", record.get("compound")),
                "vader_pos": vader.get("positive", record.get("positive")),
                "vader_neg": vader.get("negative", record.get("negative")),
                "vader_neu": vader.get("neutral", record.get("neutral")),
                "textblob_polarity": textblob.get("polarity", record.get("polarity")),
                "textblob_subjectivity": textblob.get("subjectivity", record.get("subjectivity")),
                "confidence": record.get("confidence"),
                "emotion": record.get("emotion"),
            }
        )
    return rows


def generate_excel(
    records: list[dict[str, Any]], raw_records: list[dict[str, Any]], context: dict[str, Any]
) -> bytes:
    if not OPENPYXL_AVAILABLE:  # pragma: no cover
        raise RuntimeError("openpyxl is required for Excel export")

    workbook = Workbook()

    # -- 1. Summary --------------------------------------------------------
    sheet = workbook.active
    sheet.title = "Summary"
    banner = context.get("banner")
    sheet["A1"] = "SocialScope AI — Analysis Summary"
    sheet["A1"].font = TITLE_FONT
    row = 2
    meta_rows = [
        ("Platform", context.get("platform")),
        ("Source URL", context.get("source_url")),
        ("Data mode", "DEMO DATA (synthetic)" if context.get("data_mode") == "demo" else "Live platform API"),
        ("Analysis date", context.get("created_at")),
        ("Content title", context.get("content", {}).get("title")),
        ("Author / channel", context.get("content", {}).get("channel_name") or context.get("content", {}).get("page_name") or context.get("content", {}).get("username")),
        ("Published at", context.get("content", {}).get("published_at")),
        ("Sentiment engine", context.get("sentiment_method")),
        ("Analysed by", context.get("user_name") or "—"),
    ]
    for label, value in meta_rows:
        sheet.cell(row=row, column=1, value=label).font = Font(bold=True)
        sheet.cell(row=row, column=2, value=str(value) if value is not None else "")
        row += 1
    if banner:
        sheet.cell(row=row + 1, column=1, value=banner).font = Font(bold=True, color="B00020")
    kpi_start = row + 3
    _write_table(
        sheet,
        "KPI Summary",
        ENGAGEMENT_COLUMNS,
        _kpis(context),
        note="Empty 'Value' cells with 'no' in the available column are metrics the platform API did not provide.",
        start_row=kpi_start,
        freeze=False,
    )
    _set_widths(sheet, ENGAGEMENT_COLUMNS)

    # -- 2. Raw Data -------------------------------------------------------
    raw_sheet = workbook.create_sheet("Raw Data")
    raw_rows = [
        {
            "comment_id": r.get("comment_id"),
            "author_name": r.get("author_name"),
            "raw_text": r.get("raw_text"),
            "published_at": r.get("published_at"),
            "like_count": r.get("like_count"),
            "reply_count": r.get("reply_count"),
        }
        for r in raw_records
    ]
    _write_table(
        raw_sheet,
        "Raw Data (as returned by the platform API)",
        RAW_COLUMNS,
        raw_rows,
        note="Preserved before any cleaning step.",
    )

    # -- 3. Clean Data -----------------------------------------------------
    clean_sheet = workbook.create_sheet("Clean Data")
    _write_table(
        clean_sheet,
        "Clean Data (deduplicated, de-spammed, normalized)",
        CLEAN_COLUMNS,
        records,
        note=context.get("cleaning_note"),
    )

    # -- 4. Sentiment Analysis --------------------------------------------
    sentiment_sheet = workbook.create_sheet("Sentiment Analysis")
    _write_table(
        sentiment_sheet,
        "Sentiment Analysis — VADER vs TextBlob",
        SENTIMENT_COLUMNS,
        _sentiment_rows(records),
        note=context.get("sentiment_note"),
    )

    # -- 5. Engagement Analysis -------------------------------------------
    engagement_sheet = workbook.create_sheet("Engagement Analysis")
    correlations = (context.get("statistics", {}).get("correlations", {}) or {}).get("pairs", [])
    _write_table(
        engagement_sheet,
        "Engagement Analysis",
        ENGAGEMENT_COLUMNS,
        _kpis(context)
        + [
            {
                "metric": f"Correlation: {p['x']} vs {p['y']}",
                "value": p["coefficient"],
                "available": True,
                "note": f"{p['strength']} {p['direction']} relationship (Pearson r)",
            }
            for p in correlations
        ],
    )

    # -- 6. Keywords -------------------------------------------------------
    keyword_sheet = workbook.create_sheet("Keywords")
    keyword_rows = [
        {"rank": i + 1, "word": k["word"], "count": k["count"], "tfidf": k["tfidf"], "document_frequency": k["document_frequency"]}
        for i, k in enumerate(context.get("keywords", []))
    ]
    _write_table(
        keyword_sheet,
        "Keyword Frequency",
        [
            ("rank", "Rank", 8),
            ("word", "Keyword", 24),
            ("count", "Frequency", 12),
            ("tfidf", "TF-IDF Score", 14),
            ("document_frequency", "Document Frequency", 18),
        ],
        keyword_rows,
        note="Stopwords and numeric tokens removed; TF-IDF scaled by document frequency.",
    )

    # -- 7. Hashtags -------------------------------------------------------
    hashtag_sheet = workbook.create_sheet("Hashtags")
    hashtag_rows = [
        {"rank": i + 1, "hashtag": h["hashtag"], "count": h["count"], "avg_sentiment": h["avg_sentiment"], "sentiment": h["sentiment"]}
        for i, h in enumerate(context.get("hashtags", []))
    ]
    _write_table(
        hashtag_sheet,
        "Hashtag Analysis",
        [
            ("rank", "Rank", 8),
            ("hashtag", "Hashtag", 26),
            ("count", "Frequency", 12),
            ("avg_sentiment", "Avg Sentiment", 14),
            ("sentiment", "Sentiment", 12),
        ],
        hashtag_rows,
        note="Hashtags are extracted from analysed text. Sentiment is the mean compound score of records using the hashtag.",
    )

    # -- 8. Data limitations ----------------------------------------------
    limits_sheet = workbook.create_sheet("Data Limitations")
    row = 1
    limits_sheet["A1"] = "Data Limitations and Methodology Notes"
    limits_sheet["A1"].font = TITLE_FONT
    for index, item in enumerate(context.get("limitations", []), start=1):
        limits_sheet.cell(row=row + index, column=1, value=f"{index}.")
        limits_sheet.cell(row=row + index, column=2, value=item).alignment = Alignment(wrap_text=True)
    limits_sheet.column_dimensions["A"].width = 6
    limits_sheet.column_dimensions["B"].width = 110

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")
