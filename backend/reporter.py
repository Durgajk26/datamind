"""
PDF Report Generator
---------------------
Creates a professional PDF report with AI insights and charts.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_report(filename: str, insights: dict,
                    anomalies: list, profile: dict) -> bytes:
    """
    Generate a full PDF analysis report.
    Returns PDF as bytes for download.
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=26, textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6, alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#666"),
        spaceAfter=20, alignment=TA_CENTER
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a1a2e"),
        spaceBefore=16, spaceAfter=8
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#333"),
        spaceAfter=6, leading=16
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#333"),
        leftIndent=20, spaceAfter=4, leading=15
    )

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("DataMind", title_style))
    story.append(Paragraph("AI-Powered Data Analysis Report", subtitle_style))
    story.append(Paragraph(
        f"File: {filename}  •  Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=colors.HexColor("#6366f1")))
    story.append(Spacer(1, 16))

    # ── Dataset Overview ──────────────────────────────────────────────────────
    story.append(Paragraph("Dataset Overview", h2_style))
    story.append(Paragraph(
        insights.get("dataset_description", ""), body_style
    ))

    # Stats table
    rows = int(profile.get("shape", {}).get("rows", 0))
    cols = int(profile.get("shape", {}).get("columns", 0))
    missing = sum(profile.get("missing_values", {}).values())

    data = [
        ["Metric",          "Value"],
        ["Total Rows",      f"{rows:,}"],
        ["Total Columns",   str(cols)],
        ["Missing Values",  str(missing)],
        ["Numeric Columns", str(len(profile.get("numeric_columns", [])))],
        ["Text Columns",    str(len(profile.get("categorical_columns", [])))],
    ]

    t = Table(data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#6366f1")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f8f8ff"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd")),
        ("PADDING",     (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # ── Key Insights ──────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#ddd")))
    story.append(Paragraph("Key AI Insights", h2_style))
    for insight in insights.get("key_insights", []):
        story.append(Paragraph(f"• {insight}", bullet_style))
    story.append(Spacer(1, 12))

    # ── Data Quality ──────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#ddd")))
    story.append(Paragraph("Data Quality", h2_style))
    dq = insights.get("data_quality", {})
    story.append(Paragraph(
        f"Quality Score: {dq.get('score', 'N/A')}/100", body_style
    ))
    for issue in dq.get("issues", []):
        story.append(Paragraph(f"⚠ {issue}", bullet_style))
    for strength in dq.get("strengths", []):
        story.append(Paragraph(f"✓ {strength}", bullet_style))
    story.append(Spacer(1, 12))

    # ── Anomalies ─────────────────────────────────────────────────────────────
    if anomalies:
        story.append(HRFlowable(width="100%", thickness=0.5,
                                 color=colors.HexColor("#ddd")))
        story.append(Paragraph("Anomaly Detection", h2_style))
        for a in anomalies[:5]:
            story.append(Paragraph(
                f"• {a['column']}: {a['outlier_count']} outliers "
                f"({a['outlier_pct']}%) — range [{a['lower_bound']} "
                f"to {a['upper_bound']}]",
                bullet_style
            ))
        story.append(Spacer(1, 12))

    # ── Business Implications ─────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#ddd")))
    story.append(Paragraph("Business Implications", h2_style))
    story.append(Paragraph(
        insights.get("business_implications", ""), body_style
    ))
    story.append(Spacer(1, 12))

    # ── Questions to Explore ──────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#ddd")))
    story.append(Paragraph("Recommended Questions to Explore", h2_style))
    for q in insights.get("interesting_questions", []):
        story.append(Paragraph(f"• {q}", bullet_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()