"""Export dashboard-ready analytics to Excel and PDF."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _excel_safe(frame: pd.DataFrame) -> pd.DataFrame:
    """Make dataframe values compatible with Excel, including timezone dates."""
    safe = frame.copy()
    for column in safe.columns:
        if isinstance(safe[column].dtype, pd.DatetimeTZDtype):
            safe[column] = safe[column].dt.tz_convert("UTC").dt.tz_localize(None)
    return safe


def build_excel_report(
    events: pd.DataFrame,
    funnel: pd.DataFrame,
    retention: pd.DataFrame,
    ltv: pd.DataFrame,
    anomalies: pd.DataFrame,
) -> bytes:
    """Return a multi-sheet XLSX report as bytes."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for frame, sheet in ((funnel, "Funnel"), (retention, "Retention"), (ltv, "LTV"), (anomalies, "Anomalies"), (events, "Event sample")):
            _excel_safe(frame).to_excel(writer, sheet_name=sheet, index=False)
    return output.getvalue()


def build_pdf_report(
    funnel: pd.DataFrame,
    ab_result: dict,
    anomalies: pd.DataFrame,
    title: str = "Growth Funnel Lab Report",
) -> bytes:
    """Return a compact PDF summary report as bytes."""
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(letter), rightMargin=0.45 * inch, leftMargin=0.45 * inch, topMargin=0.4 * inch, bottomMargin=0.4 * inch)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 0.15 * inch)]
    funnel_row = funnel.iloc[0]
    summary = [
        ["Metric", "Value"],
        ["Landing users", f"{int(funnel_row['landing_users']):,}"],
        ["Signup CVR", f"{funnel_row['landing_to_signup_cvr']:.1%}"],
        ["Activation CVR", f"{funnel_row['signup_to_activation_cvr']:.1%}"],
        ["Subscription CVR", f"{funnel_row['activation_to_subscription_cvr']:.1%}"],
        ["A/B p-value", f"{ab_result['p_value']:.4f}"],
        ["A/B absolute lift", f"{ab_result['absolute_lift']:.1%}"],
    ]
    table = Table(summary, colWidths=[2.2 * inch, 1.4 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))
    anomaly_count = int(anomalies["is_anomaly"].sum()) if "is_anomaly" in anomalies.columns else 0
    story.append(Paragraph(f"Anomaly flags: {anomaly_count}. LTV and retention values are observed metrics; recent cohorts may be incomplete.", styles["BodyText"]))
    document.build(story)
    return output.getvalue()
