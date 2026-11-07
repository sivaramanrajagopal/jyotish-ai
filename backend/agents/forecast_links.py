"""Forecast and Gochar on House Links — house status for any date, no scores.

Which houses are live comes from House Links (dasha lords + Jupiter/Saturn).
Planet rows carry the classical Gochara result from the natal Moon.
"""

from __future__ import annotations

from datetime import date

from agents.house_connections.activation import compute_activation, ordinal
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.yogas import detect_yogas
from agents.transit_score_agent import (
    GOCHARA_AUSPICIOUS,
    compact_gochara_summary,
    score_all_houses,
)

GOCHARA_RESULT = {
    "favourable": ("Favourable", "சாதகம்"),
    "blocked": ("Blocked by Vedha", "வேதையால் தடை"),
    "unfavourable": ("Unfavourable", "பாதகம்"),
}


def gochara_result(planet: str, pos_from_moon: int, vedha: bool) -> str:
    if pos_from_moon not in GOCHARA_AUSPICIOUS.get(planet, set()):
        return "unfavourable"
    return "blocked" if vedha else "favourable"


def _planet_rows(scores: dict, md: str, bh: str) -> list[dict]:
    rows = []
    for d in scores.get("transit_analysis") or []:
        planet = d.get("planet", "")
        key = gochara_result(planet, int(d.get("pos_from_moon") or 0), bool(d.get("vedha_blocked")))
        en, ta = GOCHARA_RESULT[key]
        rows.append({
            "planet": planet,
            "sign_en": d.get("transit_sign_en", ""),
            "sign_ta": d.get("transit_sign", ""),
            "degree": d.get("transit_degree"),
            "nakshatra": d.get("nakshatra", ""),
            "pada": d.get("pada"),
            "retrograde": bool(d.get("retrograde")) and planet not in ("Sun", "Moon", "Rahu", "Ketu"),
            "pos_from_moon": d.get("pos_from_moon"),
            "result": {"key": key, "en": en, "ta": ta},
            "vedha_by": (d.get("vedha_by") or "") if key == "blocked" else "",
            "role": "maha" if planet == md else "bhukti" if planet == bh else "",
        })
    return rows


def forecast_links(chart: dict, transit_date: str | None, transit_time: str | None) -> dict:
    scores = score_all_houses(chart, transit_date, transit_time, chart.get("dasha"))
    when = date.fromisoformat(scores["transit_date"])
    houses_map = analyze_all_houses(chart)
    yogas = detect_yogas(houses_map, chart)
    resolved_time = (scores.get("transit_moment") or {}).get("time") or transit_time
    activation = compute_activation(chart, houses_map, yogas, when, resolved_time)

    period = activation.get("period") or {}
    md = (period.get("mahadasha") or {}).get("planet", "")
    bh = (period.get("bhukti") or {}).get("planet", "")
    sav = scores.get("houses") or {}

    houses = []
    for row in activation["rows"]:
        h = row["house"]
        hs = sav.get(h) or {}
        houses.append({
            **row,
            "name": hs.get("name", ""),
            "transit_in": hs.get("transit_in", []),
            "transit_aspecting": hs.get("transit_aspecting", []),
        })

    by_status: dict[str, list[int]] = {"live": [], "waiting": [], "sky": [], "quiet": []}
    for row in houses:
        by_status[row["status"]["key"]].append(row["house"])

    return {
        "as_of": activation["as_of"],
        "transit_date": scores["transit_date"],
        "transit_moment": scores.get("transit_moment"),
        "lagna_en": scores.get("lagna_en", ""),
        "natal_moon_en": scores.get("natal_moon_en", ""),
        "period": activation.get("period"),
        "relation": activation.get("relation"),
        "moon_today": activation.get("today"),
        "now": activation.get("now", []),
        "by_status": by_status,
        "houses": houses,
        "planets": _planet_rows(scores, md, bh),
        "_scores": scores,
    }


def public(result: dict) -> dict:
    return {k: v for k, v in result.items() if not k.startswith("_")}


def _house_line(row: dict) -> str:
    parts = [f"{row['status']['en']}"]
    reasons = [r.get("en") or r.get("text") or "" for r in row["dasha"]["reasons"]]
    reasons = [r for r in reasons if r]
    if reasons:
        parts.append("dasha: " + "; ".join(reasons[:2]))
    lines = [ln["en"] for ln in row["transit"]["lines"]]
    if lines:
        parts.append("transit: " + "; ".join(lines))
    return f"H{row['house']} {row['theme_en']} — " + " · ".join(parts)


def daily_context(result: dict) -> str:
    """Prompt block for the daily reading."""
    p = result.get("period") or {}
    md, bh = p.get("mahadasha") or {}, p.get("bhukti") or {}
    by = result["by_status"]
    rows = {r["house"]: r for r in result["houses"]}
    lines = [
        f"=== HOUSE LINKS — {result['transit_date']} ===",
        f"Dasha: {md.get('planet', '')} Mahadasha (to {md.get('end', '')}) / "
        f"{bh.get('planet', '')} Bhukti (to {bh.get('end', '')}).",
    ]
    if result.get("relation"):
        lines.append(result["relation"]["en"])
    lines.append("Live now (dasha on and Jupiter + Saturn both touch it):")
    lines += [f"  {_house_line(rows[h])}" for h in by["live"]] or ["  none"]
    lines.append("Dasha on, transit not now:")
    lines += [f"  {_house_line(rows[h])}" for h in by["waiting"]] or ["  none"]
    if by["sky"]:
        lines.append("Transit only (no dasha support, so effects stay light): "
                     + ", ".join(f"H{h} {rows[h]['theme_en']}" for h in by["sky"]))
    if result.get("moon_today"):
        lines.append(result["moon_today"]["en"])
    lines.append("")
    lines.append(compact_gochara_summary(result["_scores"], _dasha_shape(result)))
    return "\n".join(lines)


def house_context(result: dict, house: int) -> str:
    """Prompt block for one house insight."""
    row = next(r for r in result["houses"] if r["house"] == house)
    pl = {r["planet"]: r for r in result["planets"]}
    lines = [
        f"HOUSE {house}: {row['theme_en']} ({row['sign']} sign, lord {row['lord']} in the {ordinal(row['lord_house'])})",
        f"Status on {result['transit_date']}: {row['status']['en']}",
    ]
    for r in row["dasha"]["reasons"]:
        text = r.get("en") or r.get("text")
        if text:
            lines.append(f"  dasha: {text}")
    for ln in row["transit"]["lines"]:
        lines.append(f"  transit: {ln['en']}")
    if row.get("transit_in"):
        lines.append("Planets passing through: " + ", ".join(row["transit_in"]))
    if row.get("transit_aspecting"):
        lines.append("Planets aspecting: " + ", ".join(row["transit_aspecting"]))
    lord = pl.get(row["lord"])
    if lord:
        lines.append(
            f"House lord {row['lord']} in Gochara: {lord['sign_en']}, "
            f"{ordinal(lord['pos_from_moon'])} from the natal Moon, {lord['result']['en'].lower()}"
        )
    for name in row.get("transit_in", []) + row.get("transit_aspecting", []):
        prow = pl.get(name)
        if prow and name != row["lord"]:
            lines.append(f"  {name}: {ordinal(prow['pos_from_moon'])} from Moon, {prow['result']['en'].lower()}")
    if row["transit"].get("sav_points") is not None:
        lines.append(f"Ashtakavarga: {row['transit']['sav_points']} bindus ({row['transit']['sav_label']})")
    if row["fruit"].get("en"):
        lines.append(f"Natal promise: {row['fruit']['en']}")
    for link in row.get("links", []):
        lines.append(f"  link: {link['en']}")
    lines.append(f"Natal Moon: {result['natal_moon_en']} (Gochara reference)")
    return "\n".join(lines)


def _dasha_shape(result: dict) -> dict:
    p = result.get("period") or {}
    return {
        "mahadasha": {"planet": (p.get("mahadasha") or {}).get("planet", "")},
        "bhukti": {"planet": (p.get("bhukti") or {}).get("planet", "")},
    }
