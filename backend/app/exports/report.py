"""Analysis report generation: styled HTML and PDF.

The report contains the overview, engagement and sentiment statistics, keyword
tables, data-derived observations, and an explicit data-limitations section.
All numbers come from the stored analysis — nothing is generated client-side.
"""

from __future__ import annotations

import html
import io
from typing import Any

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover
    REPORTLAB_AVAILABLE = False

BRAND = "#4F7CFF"
BRAND_DARK = "#1B2A4A"
MUTED = "#5A6478"


def _fmt(value: Any, suffix: str = "") -> str:
    if value is None:
        return "Data unavailable through the current platform API."
    if isinstance(value, float):
        text = f"{value:,.2f}".rstrip("0").rstrip(".")
    elif isinstance(value, int):
        text = f"{value:,}"
    else:
        text = str(value)
    return f"{text}{suffix}"


def _build_sections(context: dict[str, Any]) -> dict[str, Any]:
    engagement = context.get("engagement", {})
    summary = context.get("sentiment_summary", {})
    stats = context.get("statistics", {})
    content = context.get("content", {})

    overview = [
        ("Platform", context.get("platform")),
        ("Data mode", "DEMO DATA (synthetic, not live)" if context.get("data_mode") == "demo" else "Live platform API"),
        ("Source URL", context.get("source_url")),
        ("Analysis date", context.get("created_at")),
        ("Content title", content.get("title") or (content.get("caption") or "")[:120]),
        (
            "Author / channel",
            content.get("channel_name") or content.get("page_name") or content.get("username"),
        ),
        ("Published at", content.get("published_at")),
        ("Sentiment engine", context.get("sentiment_method")),
        ("Analysed by", context.get("user_name") or "—"),
        ("Total text records", context.get("total_records")),
        ("Records removed by cleaning", context.get("removed_records")),
    ]

    engagement_rows = [
        ("Views", engagement.get("views"), "views"),
        ("Likes", engagement.get("likes"), "likes"),
        ("Comments", engagement.get("comments"), "comments"),
        ("Shares", engagement.get("shares"), "shares"),
        ("Total interactions", engagement.get("total_interactions"), ""),
        ("Engagement rate (%)", engagement.get("engagement_rate"), ""),
    ]

    sentiment_rows = [
        ("Positive records", summary.get("positive"), f"{_fmt(summary.get('positive_pct'))}% of analysed records"),
        ("Neutral records", summary.get("neutral"), f"{_fmt(summary.get('neutral_pct'))}% of analysed records"),
        ("Negative records", summary.get("negative"), f"{_fmt(summary.get('negative_pct'))}% of analysed records"),
        ("Average compound score", summary.get("avg_compound"), "VADER compound, mean"),
        ("Average polarity", summary.get("avg_polarity"), "TextBlob polarity"),
        ("Average subjectivity", summary.get("avg_subjectivity"), "TextBlob subjectivity"),
    ]

    descriptive = stats.get("descriptive", {})
    descriptive_rows = [
        (label, values.get("mean"), values.get("median"), values.get("std_dev"), values.get("min"), values.get("max"))
        for label, values in descriptive.items()
        if values.get("count")
    ]

    correlations = (stats.get("correlations", {}) or {}).get("pairs", [])

    return {
        "overview": overview,
        "engagement_rows": engagement_rows,
        "sentiment_rows": sentiment_rows,
        "descriptive_rows": descriptive_rows,
        "correlations": correlations[:8],
        "keywords": context.get("keywords", [])[:20],
        "hashtags": context.get("hashtags", [])[:20],
        "insights": context.get("insights", []),
        "limitations": context.get("limitations", []),
        "notes": context.get("notes", []),
    }


# ---------------------------------------------------------------- HTML ----
def generate_html(context: dict[str, Any]) -> bytes:
    sections = _build_sections(context)
    banner = (
        '<div class="banner">DEMO DATA &mdash; This dataset is included for demonstration purposes '
        "and is not live social-media data.</div>"
        if context.get("data_mode") == "demo"
        else ""
    )

    def table(headers: list[str], rows: list[tuple[Any, ...]]) -> str:
        head = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(_fmt(cell))}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    insights_html = "".join(
        f"<li><strong>{html.escape(str(i.get('title')))}</strong> &mdash; {html.escape(str(i.get('text')))}</li>"
        for i in sections["insights"]
    )
    limitations_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in sections["limitations"])
    notes_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in sections["notes"])

    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>SocialScope AI &mdash; Analysis Report</title>
<style>
  :root {{ color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Inter, system-ui, sans-serif; margin: 0; padding: 32px;
         background: #f4f6fb; color: #1b2a4a; line-height: 1.6; }}
  .wrap {{ max-width: 1000px; margin: 0 auto; }}
  header {{ background: linear-gradient(135deg, #4f7cff, #8a5cff); color: #fff;
            padding: 32px; border-radius: 20px; box-shadow: 0 12px 30px rgba(31,58,120,.18); }}
  header h1 {{ margin: 0 0 4px; font-size: 30px; }}
  header p {{ margin: 0; opacity: .92; }}
  .banner {{ background: #fff3f4; border-left: 5px solid #e11d48; color: #9f1239;
             padding: 14px 18px; border-radius: 10px; margin: 20px 0; font-weight: 600; }}
  section {{ background: #fff; border-radius: 18px; padding: 24px 26px; margin: 22px 0;
             box-shadow: 0 4px 18px rgba(27,42,74,.07); }}
  h2 {{ margin: 0 0 14px; font-size: 20px; color: {BRAND_DARK};
        border-left: 4px solid {BRAND}; padding-left: 12px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 14px; }}
  th {{ background: {BRAND_DARK}; color: #fff; text-align: left; padding: 10px 12px; font-size: 13px; }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #e6eaf2; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #fafbfe; }}
  ul {{ margin: 6px 0 0; padding-left: 20px; }}
  li {{ margin-bottom: 8px; }}
  footer {{ text-align: center; color: {MUTED}; font-size: 13px; margin: 26px 0 8px; }}
  .tag {{ display: inline-block; background: #eef2ff; color: {BRAND_DARK}; border-radius: 999px;
          padding: 3px 11px; font-size: 12px; margin-right: 6px; }}
  @media print {{ body {{ background: #fff; padding: 0; }}
                  section {{ box-shadow: none; border: 1px solid #e6eaf2; break-inside: avoid; }} }}
</style></head><body><div class="wrap">
<header>
  <h1>SocialScope AI</h1>
  <p>Social Media Sentiment &amp; Analytics Report &mdash; {html.escape(str(context.get('platform', '')))}</p>
  <p style="margin-top:8px">
    <span class="tag" style="background:rgba(255,255,255,.22);color:#fff">{html.escape(str(context.get('sentiment_method') or 'n/a'))}</span>
    <span class="tag" style="background:rgba(255,255,255,.22);color:#fff">{_fmt(context.get('total_records'))} records</span>
    <span class="tag" style="background:rgba(255,255,255,.22);color:#fff">{_fmt(context.get('analysis_seconds'))}s</span>
  </p>
</header>
{banner}
<section><h2>1. Analysis Overview</h2>{table(["Field", "Value"], sections["overview"])}</section>
<section><h2>2. Engagement Statistics</h2>{table(["Metric", "Value"], sections["engagement_rows"])}</section>
<section><h2>3. Sentiment Statistics</h2>{table(["Metric", "Value", "Note"], sections["sentiment_rows"])}</section>
<section><h2>4. Descriptive Statistics</h2>
  {table(["Field", "Mean", "Median", "Std Dev", "Min", "Max"], sections["descriptive_rows"])}</section>
<section><h2>5. Correlations</h2>
  {table(["Relationship", "Pearson r", "Strength", "Direction"],
         [(f"{p['x']} vs {p['y']}", p["coefficient"], p["strength"], p["direction"]) for p in sections["correlations"]]
        or [("No correlation could be calculated from the available fields.", "", "", "")])}</section>
<section><h2>6. Keywords</h2>
  {table(["#", "Keyword", "Frequency", "TF-IDF"],
         [(i + 1, k["word"], k["count"], k["tfidf"]) for i, k in enumerate(sections["keywords"])]
        or [("No keywords were extracted.", "", "", "")])}</section>
<section><h2>7. Hashtags</h2>
  {table(["#", "Hashtag", "Frequency", "Avg Sentiment", "Sentiment"],
         [(i + 1, h["hashtag"], h["count"], h["avg_sentiment"], h["sentiment"]) for i, h in enumerate(sections["hashtags"])]
        or [("No hashtags were found in the analysed text.", "", "", "", "")])}</section>
<section><h2>8. Observations</h2><ul>{insights_html or "<li>No observations could be generated.</li>"}</ul></section>
<section><h2>9. Data Limitations</h2><ul>{limitations_html}</ul></section>
{f'<section><h2>10. Collection Notes</h2><ul>{notes_html}</ul></section>' if sections["notes"] else ''}
<footer>
  Generated by SocialScope AI &mdash; "From Social Data to Smart Insights."<br>
  This report analyses only data available through supported platform APIs and permitted
  public sources. It does not bypass privacy settings, authentication or platform restrictions.
</footer>
</div></body></html>"""

    return body.encode("utf-8")


# ----------------------------------------------------------------- PDF ----
def generate_pdf(context: dict[str, Any]) -> bytes:
    if not REPORTLAB_AVAILABLE:  # pragma: no cover
        raise RuntimeError("reportlab is required for PDF export")

    sections = _build_sections(context)
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title="SocialScope AI — Analysis Report",
        author="SocialScope AI",
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SSTitle", parent=styles["Title"], fontSize=22, textColor=colors.HexColor(BRAND_DARK)
    )
    h1 = ParagraphStyle(
        "SSH1", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor(BRAND_DARK), spaceBefore=10
    )
    body = ParagraphStyle("SSBody", parent=styles["BodyText"], fontSize=9.5, alignment=TA_LEFT)

    def make_table(headers: list[str], rows: list[tuple[Any, ...]], widths=None) -> Table:
        data = [[Paragraph(f"<b>{html.escape(str(h))}</b>", body) for h in headers]]
        for row in rows:
            data.append([Paragraph(html.escape(_fmt(cell)), body) for cell in row])
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_DARK)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8DEE9")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    story: list[Any] = [
        Paragraph("SocialScope AI", title_style),
        Paragraph("Social Media Sentiment &amp; Analytics Report", body),
        Spacer(1, 10),
    ]

    if context.get("data_mode") == "demo":
        story.append(
            Paragraph(
                "<b>DEMO DATA</b> &mdash; This dataset is included for demonstration purposes "
                "and is not live social-media data.",
                ParagraphStyle("Warn", parent=body, textColor=colors.HexColor("#9F1239")),
            )
        )
        story.append(Spacer(1, 8))

    story += [
        Paragraph("1. Analysis Overview", h1),
        make_table(["Field", "Value"], sections["overview"], widths=[60 * mm, 105 * mm]),
        Paragraph("2. Engagement Statistics", h1),
        make_table(["Metric", "Value"], sections["engagement_rows"], widths=[80 * mm, 85 * mm]),
        Paragraph("3. Sentiment Statistics", h1),
        make_table(["Metric", "Value", "Note"], sections["sentiment_rows"], widths=[55 * mm, 40 * mm, 70 * mm]),
    ]

    if sections["descriptive_rows"]:
        story += [
            Paragraph("4. Descriptive Statistics", h1),
            make_table(
                ["Field", "Mean", "Median", "Std Dev", "Min", "Max"],
                sections["descriptive_rows"],
                widths=[45 * mm, 24 * mm, 24 * mm, 24 * mm, 22 * mm, 26 * mm],
            ),
        ]

    story.append(PageBreak())
    story += [
        Paragraph("5. Correlations", h1),
        make_table(
            ["Relationship", "Pearson r", "Strength", "Direction"],
            [(f"{p['x']} vs {p['y']}", p["coefficient"], p["strength"], p["direction"]) for p in sections["correlations"]]
            or [("No correlation could be calculated from the available fields.", "", "", "")],
            widths=[65 * mm, 28 * mm, 35 * mm, 37 * mm],
        ),
        Paragraph("6. Keywords", h1),
        make_table(
            ["#", "Keyword", "Frequency", "TF-IDF"],
            [(i + 1, k["word"], k["count"], k["tfidf"]) for i, k in enumerate(sections["keywords"])][:20]
            or [("No keywords were extracted.", "", "", "")],
            widths=[14 * mm, 70 * mm, 40 * mm, 41 * mm],
        ),
        Paragraph("7. Hashtags", h1),
        make_table(
            ["#", "Hashtag", "Frequency", "Avg Sentiment", "Sentiment"],
            [(i + 1, h["hashtag"], h["count"], h["avg_sentiment"], h["sentiment"]) for i, h in enumerate(sections["hashtags"])][:20]
            or [("No hashtags were found in the analysed text.", "", "", "", "")],
            widths=[12 * mm, 60 * mm, 32 * mm, 34 * mm, 27 * mm],
        ),
        Paragraph("8. Observations", h1),
    ]
    for insight in sections["insights"] or [{"title": "None", "text": "No observations could be generated."}]:
        story.append(Paragraph(f"<b>{html.escape(str(insight.get('title')))}:</b> {html.escape(str(insight.get('text')))}", body))
        story.append(Spacer(1, 4))

    story.append(Paragraph("9. Data Limitations", h1))
    for item in sections["limitations"]:
        story.append(Paragraph(f"&bull; {html.escape(str(item))}", body))
        story.append(Spacer(1, 3))

    if sections["notes"]:
        story.append(Paragraph("10. Collection Notes", h1))
        for item in sections["notes"]:
            story.append(Paragraph(f"&bull; {html.escape(str(item))}", body))

    def footer(canvas, _doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor(MUTED))
        canvas.drawString(18 * mm, 10 * mm, "SocialScope AI — From Social Data to Smart Insights.")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
