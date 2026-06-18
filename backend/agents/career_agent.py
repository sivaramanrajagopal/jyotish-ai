"""
career_agent.py — D1 + D10 career prediction (10 rules, profession tags, Dasa timing).
"""

from __future__ import annotations

import datetime

from agents.career.atmakaraka import classical_karakas, evaluate_atmakaraka_d10
from agents.career.d10 import build_dasamsa_from_natal
from agents.career.profession import predict_professions
from agents.career.rules import evaluate_pdf10_rules
from agents.career.timing import build_career_timing
from agents.natal_agent import SIGN_LORDS, SIGNS
from dasha_core import find_current_dasha_bhukti

CAREER_PLANETS = frozenset({
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
})


def _tenth_lord(asc_sign_index: int) -> str:
    tenth_idx = (int(asc_sign_index) + 9) % 12
    return SIGN_LORDS[SIGNS[tenth_idx]]


def _strength_label(rules_matched: int, top_prob: float) -> str:
    if rules_matched >= 7 and top_prob >= 60:
        return "Strong"
    if rules_matched >= 5 or top_prob >= 45:
        return "Good"
    if rules_matched >= 3 or top_prob >= 30:
        return "Moderate"
    return "Developing"


def compute_career_prediction(natal_chart: dict, *, timing_years: int = 90) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    bd = natal_chart.get("birth_data") or {}
    asc_idx = asc.get("sign_index")
    if asc_idx is None:
        raise ValueError("Chart must include ascendant sign_index.")

    dasamsa_asc, dasamsa_pos = build_dasamsa_from_natal(natal_chart)
    tenth_lord = _tenth_lord(asc_idx)
    karakas = classical_karakas(pp)
    ak_eval = evaluate_atmakaraka_d10(pp, dasamsa_pos, dasamsa_asc)

    birth_date = bd.get("dob")
    if not birth_date:
        raise ValueError("birth_data.dob required for career timing.")

    moon_lon = (pp.get("Moon") or {}).get("longitude", 0.0)
    timing = build_career_timing(
        moon_lon,
        birth_date,
        tenth_lord=tenth_lord,
        atmakaraka=karakas["atmakaraka"],
        amatyakaraka=karakas["amatyakaraka"],
        years=timing_years,
    )
    dasha_links_10th = any(p["tenth_lord_link"] for p in timing)

    rules = evaluate_pdf10_rules(
        asc_sign_index=asc_idx,
        planet_positions=pp,
        dasamsa_positions=dasamsa_pos,
        dasamsa_ascendant=dasamsa_asc,
        tenth_lord=tenth_lord,
        ak_eval=ak_eval,
        dasha_links_10th=dasha_links_10th,
    )
    matched = sum(1 for r in rules if r["matched"])

    professions = predict_professions(pp, asc_idx, tenth_lord)
    top_prob = professions[0]["probability"] if professions else 0.0
    strength = _strength_label(matched, top_prob)

    today = datetime.date.today().isoformat()
    current_timing = [p for p in timing if p["start"] <= today <= p["end"]]
    upcoming_timing = [p for p in timing if p["start"] > today][:10]

    _, cur_d, _, cur_b = find_current_dasha_bhukti(moon_lon, birth_date)

    headline = "No active career Dasa link today."
    if current_timing:
        headline = f"Career timing active: {current_timing[0]['label']} ({', '.join(current_timing[0]['links'])})"
    elif upcoming_timing:
        headline = f"Next career window: {upcoming_timing[0]['label']} from {upcoming_timing[0]['start']}"

    return {
        "summary": {
            "rules_matched": matched,
            "rules_total": 10,
            "career_strength": strength,
            "tenth_lord": tenth_lord,
            "tenth_house_sign": SIGNS[(asc_idx + 9) % 12],
            "atmakaraka": karakas["atmakaraka"],
            "amatyakaraka": karakas["amatyakaraka"],
            "top_profession": professions[0]["name"] if professions else "",
            "top_probability": top_prob,
        },
        "profession_tags": professions[:5],
        "rules": rules,
        "karakas": {**karakas, "ak_d10": ak_eval},
        "dasamsa_ascendant": dasamsa_asc,
        "dasamsa_positions": dasamsa_pos,
        "current_dasa": {
            "maha_dasa": cur_d["planet"],
            "bukti": cur_b["planet"],
            "start": cur_b["start"].strftime("%Y-%m-%d"),
            "end": cur_b["end"].strftime("%Y-%m-%d"),
        },
        "timing": {
            "current": current_timing,
            "upcoming": upcoming_timing,
            "all": timing,
        },
        "hero": {"headline": headline, "career_strength": strength},
        "interpretation": {
            "note": (
                "Career analysis uses D1 + D10 (Dasamsa), ten Parashari rules, profession "
                "significators, and Vimshottari periods linked to 10th lord / AK / AmK."
            ),
        },
    }


def career_context_for_narrator(natal_chart: dict) -> str:
    try:
        data = compute_career_prediction(natal_chart)
    except Exception:
        return ""

    s = data["summary"]
    lines = [
        "=== Career (D1 + D10) ===",
        f"Strength: {s['career_strength']} · Rules {s['rules_matched']}/{s['rules_total']}",
        f"D1 10th lord: {s['tenth_lord']} · 10th sign: {s['tenth_house_sign']}",
        f"AK: {s['atmakaraka']} · AmK: {s['amatyakaraka']}",
        f"Top profession: {s['top_profession']} ({s['top_probability']}%)",
    ]
    matched = [r["label"] for r in data["rules"] if r["matched"]]
    if matched:
        lines.append("Rules matched: " + "; ".join(matched[:6]))
    if data["hero"].get("headline"):
        lines.append(data["hero"]["headline"])
    tags = ", ".join(f"{p['name']} {p['probability']}%" for p in data["profession_tags"][:3])
    if tags:
        lines.append(f"Profession tags: {tags}")
    return "\n".join(lines)
