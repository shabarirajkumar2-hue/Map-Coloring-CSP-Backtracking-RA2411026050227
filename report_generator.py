"""
Report Generator - Generates PDF reports for Map Coloring CSP solutions using ReportLab.
"""

import os
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


COLOR_MAP = {
    "Red":    colors.HexColor("#E74C3C"),
    "Green":  colors.HexColor("#2ECC71"),
    "Blue":   colors.HexColor("#3498DB"),
    "Yellow": colors.HexColor("#F1C40F"),
    "Purple": colors.HexColor("#9B59B6"),
    "Orange": colors.HexColor("#E67E22"),
    "Pink":   colors.HexColor("#FF6B9D"),
    "Cyan":   colors.HexColor("#00BCD4"),
}

DARK_BG   = colors.HexColor("#1A1A2E")
ACCENT    = colors.HexColor("#6C63FF")
LIGHT_BG  = colors.HexColor("#F5F5F5")
TEXT_DARK = colors.HexColor("#2C2C54")


def generate_pdf_report(data: dict) -> bytes:
    """
    Generate a professional PDF report for the CSP map coloring result.
    :param data: dict with keys: username, regions, neighbors, colors_used,
                 solution, confidence_score, complexity_label,
                 constraints_satisfied, total_constraints, backtracks,
                 elapsed_ms, timeline, timestamp
    :return: PDF as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ─── Title Section ────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=22, textColor=ACCENT,
        spaceAfter=4, alignment=TA_CENTER, fontName="Helvetica-Bold"
    )
    subtitle_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=11, textColor=TEXT_DARK,
        alignment=TA_CENTER, spaceAfter=2
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontSize=9, textColor=colors.grey, alignment=TA_CENTER
    )

    elements.append(Paragraph("🗺️ Map Coloring CSP Solver", title_style))
    elements.append(Paragraph("Constraint Satisfaction Problem — Execution Report", subtitle_style))
    elements.append(Paragraph(
        f"Generated: {data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}  |  "
        f"User: {data.get('username', 'N/A')}",
        label_style
    ))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))
    elements.append(Spacer(1, 0.3 * cm))

    # ─── Summary Cards ────────────────────────────────────────────────────────
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=13, textColor=ACCENT,
        spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold"
    )
    normal = ParagraphStyle(
        "Normal2", parent=styles["Normal"],
        fontSize=10, textColor=TEXT_DARK, spaceAfter=4
    )

    elements.append(Paragraph("1. Execution Summary", section_style))

    summary_data = [
        ["Metric", "Value"],
        ["Total Regions", str(len(data.get("regions", [])))],
        ["Colors Available", ", ".join(data.get("colors_used", []))],
        ["Backtracking Steps", str(data.get("backtracks", 0))],
        ["Execution Time", f"{data.get('elapsed_ms', 0)} ms"],
        ["Constraints Satisfied", f"{data.get('constraints_satisfied', 0)} / {data.get('total_constraints', 0)}"],
        ["Confidence Score", f"{data.get('confidence_score', 0)}%"],
        ["Complexity Level", data.get("complexity_label", "—")],
    ]

    summary_table = Table(summary_data, colWidths=[7 * cm, 9 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 11),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("FONTSIZE",   (0, 1), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 0), (-1, 0), [ACCENT]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * cm))

    # ─── Solution Table ───────────────────────────────────────────────────────
    elements.append(Paragraph("2. Coloring Solution", section_style))
    solution = data.get("solution", {})
    if solution:
        sol_data = [["Region", "Assigned Color"]]
        for region, color in solution.items():
            sol_data.append([region, color])

        sol_table = Table(sol_data, colWidths=[8 * cm, 8 * cm])
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), TEXT_DARK),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING",   (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ]
        for i, (region, color) in enumerate(solution.items(), start=1):
            bg = COLOR_MAP.get(color, colors.HexColor("#EEEEEE"))
            style_cmds.append(("BACKGROUND", (1, i), (1, i), bg))
            style_cmds.append(("TEXTCOLOR", (1, i), (1, i), colors.white))
        sol_table.setStyle(TableStyle(style_cmds))
        elements.append(sol_table)
    else:
        elements.append(Paragraph("No solution was found for the given configuration.", normal))
    elements.append(Spacer(1, 0.5 * cm))

    # ─── Adjacency List ───────────────────────────────────────────────────────
    elements.append(Paragraph("3. Adjacency Relationships", section_style))
    neighbors = data.get("neighbors", {})
    if neighbors:
        adj_data = [["Region", "Adjacent Regions"]]
        for region in data.get("regions", []):
            nbrs = neighbors.get(region, [])
            adj_data.append([region, ", ".join(nbrs) if nbrs else "None"])
        adj_table = Table(adj_data, colWidths=[6 * cm, 10 * cm])
        adj_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEXT_DARK),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        elements.append(adj_table)
    elements.append(Spacer(1, 0.5 * cm))

    # ─── Timeline (first 15 steps) ────────────────────────────────────────────
    elements.append(Paragraph("4. Execution Timeline (Key Steps)", section_style))
    timeline = data.get("timeline", [])[:15]
    if timeline:
        tl_data = [["#", "Type", "Description"]]
        for item in timeline:
            tl_data.append([
                str(item.get("step", "")),
                item.get("label", item.get("type", "")),
                item.get("message", "")
            ])
        tl_table = Table(tl_data, colWidths=[1.5 * cm, 4 * cm, 10.5 * cm])
        tl_style = [
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ]
        tl_table.setStyle(TableStyle(tl_style))
        elements.append(tl_table)
        if len(data.get("timeline", [])) > 15:
            elements.append(Paragraph(
                f"  ... and {len(data['timeline']) - 15} more steps.",
                ParagraphStyle("sm", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
            ))
    elements.append(Spacer(1, 0.5 * cm))

    # ─── Footer ───────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Paragraph(
        "Map Coloring CSP Solver — AI Lab Assignment | Algorithm: Backtracking + MRV + LCV",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER, spaceBefore=6)
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
