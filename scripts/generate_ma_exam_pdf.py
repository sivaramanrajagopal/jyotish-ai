#!/usr/bin/env python3
"""
Generate MA Exam submission PDF with South Indian D1 charts and event transit charts.
Uses jyotish-ai backend (Lahiri sidereal, whole-sign houses).
"""

from __future__ import annotations

import datetime
import os
import sys
from pathlib import Path

# Backend on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import swisseph as swe
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable

from agents.natal_agent import calculate_natal_chart, SIGNS
from chart_utils import ensure_dasha
from dasha_core import generate_dashas, generate_bhuktis, find_current_dasha_bhukti

swe.set_sid_mode(swe.SIDM_LAHIRI)

SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]
PLANET_SHORT = {
    "Sun": "Su", "Moon": "Mo", "Mercury": "Me", "Venus": "Ve", "Mars": "Ma",
    "Jupiter": "Ju", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
}

LOCATIONS = {
    "Dharmapuri": (12.127, 78.158),
    "Coimbatore": (11.0168, 76.9558),
    "Chennai": (13.0827, 80.2707),
    "Sankarapuram": (12.183, 78.583),
}

# Fixed South Indian 4×4 grid (sign indices)
_SI_GRID = [
    [11, 0, 1, 2],
    [10, -1, -1, 3],
    [9, -1, -1, 4],
    [8, 7, 6, 5],
]


def _parse_time(tob: str) -> str:
    """Normalize HH:MM for natal_agent."""
    parts = tob.strip().upper().replace(".", ":").split(":")
    h = int(parts[0])
    if "PM" in tob.upper() and h < 12:
        h += 12
    if "AM" in tob.upper() and h == 12:
        h = 0
    m = int(parts[1]) if len(parts) > 1 else 0
    return f"{h:02d}:{m:02d}"


def _transit_positions(date_str: str) -> dict:
    y, m, d = map(int, date_str.split("-"))
    jd = swe.julday(y, m, d, 12.0 - 5.5 / 24)
    ayan = swe.get_ayanamsa_ut(jd)
    out = {}
    bodies = [
        (0, "Sun"), (1, "Moon"), (2, "Mercury"), (3, "Venus"), (4, "Mars"),
        (5, "Jupiter"), (6, "Saturn"), (11, "Rahu"),
    ]
    for pid, name in bodies:
        if pid == 11:
            xx, _ = swe.calc_ut(jd, swe.MEAN_NODE)
        else:
            xx, _ = swe.calc_ut(jd, pid)
        lon = (xx[0] - ayan) % 360
        idx = int(lon // 30) % 12
        out[name] = {"sign": SIGNS[idx], "sign_index": idx, "retrograde": False}
    ketu_idx = (out["Rahu"]["sign_index"] + 6) % 12
    out["Ketu"] = {"sign": SIGNS[ketu_idx], "sign_index": ketu_idx, "retrograde": False}
    return out


def _dasa_on_date(moon_lon: float, dob: str, event_date: str) -> str:
    y, m, d = map(int, event_date.split("-"))
    dt = datetime.datetime(y, m, d)
    dashas = generate_dashas(moon_lon, dob)
    lines = []
    for md in dashas:
        if md["start"] <= dt <= md["end"]:
            lines.append(f"Mahadasha: {md['planet']} ({md['start'].strftime('%d %b %Y')} – {md['end'].strftime('%d %b %Y')})")
            for ad in generate_bhuktis(md):
                if ad["start"] <= dt <= ad["end"]:
                    lines.append(f"Antardasha: {ad['planet']} ({ad['start'].strftime('%d %b %Y')} – {ad['end'].strftime('%d %b %Y')})")
            break
    return "\n".join(lines) if lines else "Dasa not found"


def _transit_house_table(natal_asc_idx: int, trans: dict) -> list[list[str]]:
    rows = [["Planet", "Sign", "House from Lagna"]]
    for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        t = trans[p]
        h = ((t["sign_index"] - natal_asc_idx) % 12) + 1
        rows.append([p, t["sign"], f"H{h}"])
    return rows


class SouthIndianChart(Flowable):
    """Draw South Indian style 4×4 rasi chart."""

    def __init__(self, planet_positions: dict, lagna_sign_index: int,
                 title: str = "D1 Rasi", subtitle: str = "", width: float = 14 * cm):
        super().__init__()
        self.planet_positions = planet_positions
        self.lagna_sign_index = lagna_sign_index
        self.title = title
        self.subtitle = subtitle
        self.width = width
        self.height = width

    def wrap(self, avail_width, avail_height):
        self.width = min(self.width, avail_width)
        self.height = self.width
        return self.width, self.height

    def draw(self):
        c = self.canv
        w = self.width
        cell = w / 4
        sign_planets: dict[int, list[str]] = {i: [] for i in range(12)}
        for pname, pdata in self.planet_positions.items():
            if pname in PLANET_SHORT and isinstance(pdata, dict):
                idx = pdata.get("sign_index", 0)
                short = PLANET_SHORT[pname]
                if pdata.get("retrograde"):
                    short += "R"
                sign_planets[idx].append(short)

        def draw_cell(sign_idx: int, row: int, col: int, is_centre: bool = False):
            x = col * cell
            if is_centre:
                # Centre spans rows 1–2 (0-indexed): cols 1–2, must not overlap row 0
                x = col * cell
                y = w - 3 * cell
                cw, ch = cell * 2, cell * 2
            else:
                y = w - (row + 1) * cell
                cw, ch = cell, cell

            if is_centre:
                c.setFillColor(colors.HexColor("#1e3a5f"))
                c.rect(x, y, cw, ch, fill=1, stroke=1)
                c.setFillColor(colors.HexColor("#fbbf24"))
                c.setFont("Helvetica-Bold", 9)
                c.drawCentredString(x + cw / 2, y + ch / 2 + 8, self.title)
                c.setFillColor(colors.HexColor("#94a3b8"))
                c.setFont("Helvetica", 7)
                if self.subtitle:
                    c.drawCentredString(x + cw / 2, y + ch / 2 - 6, self.subtitle[:48])
                return

            is_lagna = sign_idx == self.lagna_sign_index
            bg = colors.HexColor("#f8fafc")
            if is_lagna:
                bg = colors.HexColor("#dbeafe")
            c.setFillColor(bg)
            c.setStrokeColor(colors.HexColor("#94a3b8"))
            c.rect(x, y, cw, ch, fill=1, stroke=1)

            if is_lagna:
                c.setStrokeColor(colors.HexColor("#dc2626"))
                c.setLineWidth(1.5)
                c.line(x + 2, y + ch - 2, x + cw - 2, y + 2)
                c.setLineWidth(1)

            c.setFillColor(colors.HexColor("#64748b"))
            c.setFont("Helvetica", 6)
            c.drawRightString(x + cw - 3, y + ch - 8, f"{SIGN_ABBR[sign_idx]}")

            if is_lagna:
                c.setFillColor(colors.HexColor("#1d4ed8"))
                c.setFont("Helvetica-Bold", 6)
                c.drawString(x + 3, y + ch - 16, "ASC")

            planets = sign_planets.get(sign_idx, [])
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(colors.HexColor("#1e293b"))
            py = y + ch - 24
            for pl in planets:
                c.drawString(x + 4, py, pl)
                py -= 9

        # Row 0
        for col, si in enumerate(_SI_GRID[0]):
            draw_cell(si, 0, col)
        # Row 1
        draw_cell(_SI_GRID[1][0], 1, 0)
        draw_cell(-1, 1, 1, is_centre=True)
        draw_cell(_SI_GRID[1][3], 1, 3)
        # Row 2
        draw_cell(_SI_GRID[2][0], 2, 0)
        draw_cell(_SI_GRID[2][3], 2, 3)
        # Row 3
        for col, si in enumerate(_SI_GRID[3]):
            draw_cell(si, 3, col)


from ma_exam_cases import CASES


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontSize=22, spaceAfter=12, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor("#475569")),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=16, spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#1e3a5f")),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#334155")),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=14, alignment=TA_JUSTIFY),
        "bullet": ParagraphStyle("bullet", parent=base["Normal"], fontSize=10, leading=13, leftIndent=14, bulletIndent=6),
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, textColor=colors.HexColor("#64748b")),
    }


def _info_table(case: dict, lagna: str, moon_line: str) -> Table:
    data = [
        ["Field", "Detail"],
        ["Use Case", f"{case['num']} — {case['title']}"],
        ["Gender", case["gender"]],
        ["Birth", f"{case['birth']}, {case['place']}"],
        ["Lagna", lagna],
        ["Moon", moon_line],
        ["Question", case["question"]],
    ]
    if case.get("event_label"):
        data.append(["Event", case["event_label"]])
    t = Table(data, colWidths=[3.2 * cm, 13.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_pdf(output_path: Path) -> None:
    styles = _styles()

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(1.8 * cm, 1.2 * cm, "MA Exam — Life Event Analysis (Parasara Method) · jyotish-ai · Lahiri · Whole-Sign")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="MA Exam — Life Event Analysis",
        author="CosmicDiary / jyotish-ai",
    )
    story = []

    # Cover
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("MA Examination", styles["title"]))
    story.append(Paragraph("Life Event Analysis — Parasara Method", styles["subtitle"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        "10 Use Cases · Natal + Dasa + Gochara Synthesis<br/>"
        "Calculation Engine: jyotish-ai (Lahiri Ayanamsa, Whole-Sign Houses)",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"Compiled: {datetime.date.today().strftime('%d %B %Y')}", styles["subtitle"]))
    story.append(PageBreak())

    # TOC
    story.append(Paragraph("Table of Contents", styles["h1"]))
    for case in CASES:
        ev = f" [{case['event_label']}]" if case.get("event_label") else ""
        story.append(Paragraph(
            f"Use Case {case['num']}: {case['title']}{ev} — {case['gender']}, {case['place']}",
            styles["body"],
        ))
    story.append(PageBreak())

    for case in CASES:
        lat, lon = LOCATIONS[case["place"]]
        tob = _parse_time(case["tob"])
        chart = ensure_dasha(calculate_natal_chart(case["dob"], tob, lat, lon, "Asia/Kolkata"))
        asc = chart["ascendant"]
        moon = chart["planet_positions"]["Moon"]
        moon_line = f"{moon['sign']} H{moon['house']} — {moon['nakshatra']}"
        lagna_line = f"{asc['sign']} ({asc['nakshatra']})"

        story.append(Paragraph(f"Use Case {case['num']} — {case['title']}", styles["h1"]))
        story.append(_info_table(case, lagna_line, moon_line))
        story.append(Spacer(1, 0.4 * cm))

        # D1 chart
        story.append(Paragraph("D1 Rasi Chart (South Indian Style)", styles["h2"]))
        story.append(SouthIndianChart(
            chart["planet_positions"],
            asc["sign_index"],
            title="D1 Rasi",
            subtitle=f"{case['birth']}, {case['place']}",
        ))
        story.append(Spacer(1, 0.3 * cm))

        # Natal analysis
        story.append(Paragraph("Natal Analysis", styles["h2"]))
        for para in case.get("natal_analysis", case.get("natal_points", [])):
            text = para if para.startswith("<") else para
            if not text.startswith("•"):
                story.append(Paragraph(text, styles["body"]))
            else:
                story.append(Paragraph(text, styles["bullet"]))
        story.append(Spacer(1, 0.2 * cm))

        # Drishti (planetary aspects)
        if case.get("aspect_analysis"):
            story.append(Paragraph("Drishti Analysis (Parasara Rules)", styles["h2"]))
            story.append(Paragraph(
                "<i>Traditional whole-sign drishti: all planets aspect the 7th house; "
                "Mars also 4th &amp; 8th; Jupiter 5th &amp; 9th; Saturn 3rd &amp; 10th; "
                "Rahu/Ketu 3rd &amp; 11th.</i>",
                styles["small"],
            ))
            story.append(Spacer(1, 0.1 * cm))
            for para in case["aspect_analysis"]:
                story.append(Paragraph(para, styles["body"]))
                story.append(Spacer(1, 0.1 * cm))
            story.append(Spacer(1, 0.1 * cm))

        # Dasa
        story.append(Paragraph("Dasa Analysis", styles["h2"]))
        moon_lon = moon["longitude"]
        if case.get("event_date"):
            story.append(Paragraph(
                f"<b>Running periods on {case['event_date']}:</b><br/>"
                f"{_dasa_on_date(moon_lon, case['dob'], case['event_date']).replace(chr(10), '<br/>')}",
                styles["body"],
            ))
            story.append(Spacer(1, 0.15 * cm))
        for para in case.get("dasa_analysis", [case.get("dasa_note")] if case.get("dasa_note") else []):
            if para:
                story.append(Paragraph(para, styles["body"]))
                story.append(Spacer(1, 0.1 * cm))
        story.append(Spacer(1, 0.1 * cm))

        # Gochara — event transit chart OR textual gochara analysis
        if case.get("event_date"):
            story.append(Paragraph(f"Gochara Analysis — {case['event_date']}", styles["h2"]))
            for para in case.get("gochara_analysis", [case.get("gochara_note")] if case.get("gochara_note") else []):
                if para:
                    story.append(Paragraph(para, styles["body"]))
                    story.append(Spacer(1, 0.1 * cm))
            trans = _transit_positions(case["event_date"])
            story.append(SouthIndianChart(
                trans,
                asc["sign_index"],
                title="Transit Chart",
                subtitle=case["event_label"],
            ))
            story.append(Spacer(1, 0.2 * cm))
            rows = _transit_house_table(asc["sign_index"], trans)
            tt = Table(rows, colWidths=[3 * cm, 4 * cm, 4 * cm])
            tt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(tt)
        elif case.get("gochara_analysis"):
            story.append(Paragraph("Gochara Analysis", styles["h2"]))
            for para in case["gochara_analysis"]:
                story.append(Paragraph(para, styles["body"]))
                story.append(Spacer(1, 0.1 * cm))

        # Conclusion
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("Conclusion", styles["h2"]))
        conclusion = case.get("conclusion", "")
        if isinstance(conclusion, list):
            for para in conclusion:
                story.append(Paragraph(para, styles["body"]))
                story.append(Spacer(1, 0.1 * cm))
        else:
            story.append(Paragraph(conclusion, styles["body"]))
        story.append(Spacer(1, 0.2 * cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")))
        story.append(PageBreak())

    # Methodology page
    story.append(Paragraph("Methodology Note", styles["h1"]))
    story.append(Paragraph(
        "All charts computed using the jyotish-ai canonical engine: Lahiri sidereal ayanamsa, "
        "whole-sign house system, Vimshottari Dasa from Moon nakshatra. Drishti follows traditional "
        "Parasara rules (7th aspect for all; special aspects for Mars, Jupiter, Saturn, Rahu, Ketu). "
        "South Indian charts show fixed rasi positions. For event cases, transit chart shows planetary "
        "positions on the event date (noon IST) mapped to houses from natal lagna. Analysis follows "
        "Parasara method: Bhava significators → Drishti → Dasa permission → Gochara trigger.",
        styles["body"],
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"PDF written: {output_path}")


if __name__ == "__main__":
    out = ROOT / "docs" / "MA-EXAM-SUBMISSION.pdf"
    build_pdf(out)
