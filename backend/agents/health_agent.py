"""
health_agent.py — D3 Drekkana body map + Dasa/Bhukti + transit health awareness.
"""

from __future__ import annotations

import datetime

from agents.bhavat_bhavam.slices import compute_health_bhavat_bhavam
from agents.health.body_map import body_part_for_d3_house
from agents.health.d3 import build_drekkana_from_natal
from agents.health.warnings import (
    apply_dasa_scores,
    apply_transit_scores,
    build_body_regions,
    build_factor_groups,
    enrich_body_regions_rationale,
    build_planet_rows,
    build_transit_today,
    flatten_warnings_for_chat,
)
from agents.natal_agent import calculate_natal_chart
from dasha_core import find_current_dasha_bhukti

DISCLAIMER_EN = (
    "For informational and awareness purposes only. Not medical diagnosis, "
    "treatment, or advice. Consult a qualified physician for any health concerns."
)
DISCLAIMER_TA = (
    "தகவல் மற்றும் விழிப்புணர்வுக்காக மட்டும். மருத்துவ நோயறிதல், சிகிச்சை "
    "அல்லது ஆலோசனை அல்ல. ஆரோக்கிய கவலைகளுக்கு மருத்துவரை அணுகவும்."
)


def _transit_positions_for_today(natal_chart: dict) -> dict:
    bd = natal_chart.get("birth_data") or {}
    lat = bd.get("lat")
    lon = bd.get("lon")
    tz = bd.get("timezone") or "Asia/Kolkata"
    if lat is None or lon is None:
        return {}
    today = datetime.date.today().isoformat()
    try:
        transit = calculate_natal_chart(today, "12:00", float(lat), float(lon), tz)
        return transit.get("planet_positions") or {}
    except Exception:
        return {}


def compute_health_analysis(natal_chart: dict) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    bd = natal_chart.get("birth_data") or {}
    d1_asc_idx = asc.get("sign_index", 0)

    if not bd.get("dob"):
        raise ValueError("birth_data.dob required for health timing.")

    d3_asc, d3_pos = build_drekkana_from_natal(natal_chart)
    d3_asc_idx = d3_asc.get("sign_index", 0)

    asc_deg = float(asc.get("degree_in_sign", 0))
    lagna_body = body_part_for_d3_house(1, asc_deg)

    rows = build_planet_rows(
        d1_asc_idx=d1_asc_idx,
        d1_positions=pp,
        d3_asc_idx=d3_asc_idx,
        d3_positions=d3_pos,
    )

    from agents.health.warnings import _zone_scores_from_rows
    zone_scores = _zone_scores_from_rows(rows)

    moon_lon = (pp.get("Moon") or {}).get("longitude", 0.0)
    _, cur_d, _, cur_b = find_current_dasha_bhukti(moon_lon, bd["dob"])
    maha = cur_d["planet"]
    bhukti = cur_b["planet"]

    dasa_items = apply_dasa_scores(
        zone_scores, rows,
        maha=maha, bhukti=bhukti,
        d1_asc_idx=d1_asc_idx,
        d3_asc_idx=d3_asc_idx,
    )

    transit_pp = _transit_positions_for_today(natal_chart)
    transit_items = apply_transit_scores(
        zone_scores, rows,
        transit_positions=transit_pp,
        d3_positions=d3_pos,
        d3_asc_idx=d3_asc_idx,
        d1_asc_idx=d1_asc_idx,
    )

    body_regions = build_body_regions(zone_scores)
    factor_groups = build_factor_groups(
        rows,
        dasa_items=dasa_items,
        transit_items=transit_items,
        maha=maha,
        bhukti=bhukti,
    )
    body_regions = enrich_body_regions_rationale(
        body_regions,
        rows,
        factor_groups.get("d3_natal") or [],
        transit_items,
    )
    warnings = flatten_warnings_for_chat(factor_groups)
    transit_today = build_transit_today(
        transit_pp,
        d1_asc_idx=d1_asc_idx,
        d3_asc_idx=d3_asc_idx,
    )

    top_region = body_regions[0] if body_regions else {}
    top_factor = (factor_groups.get("d3_natal") or [None])[0]
    overall = top_factor["risk"] if top_factor else (body_regions[0]["risk"] if body_regions else "low")
    transit_date = datetime.date.today().isoformat()
    bhavat_bhavam = compute_health_bhavat_bhavam(natal_chart, maha=maha, bhukti=bhukti)

    return {
        "disclaimer": {"en": DISCLAIMER_EN, "ta": DISCLAIMER_TA},
        "summary": {
            "overall_risk": overall,
            "d3_lagna": d3_asc.get("sign"),
            "d3_lagna_ta": _sign_ta(d3_asc.get("sign", "")),
            "lagna_body_en": lagna_body["en"],
            "lagna_body_ta": lagna_body["ta"],
            "maha_dasa": maha,
            "bhukti": bhukti,
            "dasa_period": f"{cur_b['start'].strftime('%Y-%m-%d')} → {cur_b['end'].strftime('%Y-%m-%d')}",
            "warning_count": len(factor_groups.get("d3_natal", []))
                + len(factor_groups.get("dasa", []))
                + len(factor_groups.get("transit", [])),
            "transit_date": transit_date,
            "top_zone_en": top_factor["body_part_en"] if top_factor else "",
            "top_zone_ta": top_factor["body_part_ta"] if top_factor else "",
            "focus_zone_en": top_region.get("label_en", ""),
            "focus_zone_ta": top_region.get("label_ta", ""),
            "focus_rationale_en": top_region.get("rationale_en", ""),
            "focus_rationale_ta": top_region.get("rationale_ta", ""),
        },
        "current_dasa": {
            "maha_dasa": maha,
            "bukti": bhukti,
            "start": cur_b["start"].strftime("%Y-%m-%d"),
            "end": cur_b["end"].strftime("%Y-%m-%d"),
        },
        "drekkana_ascendant": d3_asc,
        "drekkana_positions": d3_pos,
        "planet_rows": rows,
        "body_regions": body_regions,
        "factor_groups": factor_groups,
        "warnings": warnings,
        "transit_today": transit_today,
        "transit_snapshot": transit_today,
        "hero": {
            "headline_en": _hero_en(maha, bhukti, overall, top_factor),
            "headline_ta": _hero_ta(maha, bhukti, overall, top_factor),
        },
        "bhavat_bhavam": bhavat_bhavam,
    }


def _sign_ta(sign: str) -> str:
    m = {
        "Aries": "மேஷம்", "Taurus": "ரிஷபம்", "Gemini": "மிதுனம்",
        "Cancer": "கடகம்", "Leo": "சிம்மம்", "Virgo": "கன்னி",
        "Libra": "துலாம்", "Scorpio": "விருச்சிகம்", "Sagittarius": "தனுசு",
        "Capricorn": "மகரம்", "Aquarius": "கும்பம்", "Pisces": "மீனம்",
    }
    return m.get(sign, sign)


def _hero_en(maha: str, bhukti: str, risk: str, top_factor: dict | None) -> str:
    zone = f" · focus: {top_factor['body_part_en']}" if top_factor else ""
    return f"Active {maha}–{bhukti} · D3 awareness: {risk}{zone}"


def _hero_ta(maha: str, bhukti: str, risk: str, top_factor: dict | None) -> str:
    risk_ta = {"low": "குறைவு", "moderate": "மிதமான", "high": "அதிக விழிப்பு"}.get(risk, risk)
    zone = f" · {top_factor['body_part_ta']}" if top_factor else ""
    return f"நடப்பு {maha}–{bhukti} · D3 விழிப்பு: {risk_ta}{zone}"


def health_context_for_narrator(natal_chart: dict) -> str:
    try:
        data = compute_health_analysis(natal_chart)
    except Exception:
        return ""

    s = data["summary"]
    fg = data.get("factor_groups") or {}
    lines = [
        "=== Health awareness (D3 Drekkana) ===",
        f"DISCLAIMER: {DISCLAIMER_EN}",
        f"D3 Lagna: {s['d3_lagna']} · Overall: {s['overall_risk']}",
        f"Dasa: {s['maha_dasa']}–{s['bhukti']} ({s['dasa_period']})",
        f"Lagna body part: {s['lagna_body_en']}",
        f"Transits as of: {s.get('transit_date', 'today')}",
    ]
    for f in (fg.get("d3_natal") or [])[:4]:
        reasons = "; ".join(f.get("reasons_en") or [])
        lines.append(f"• D3 {f['body_part_en']}: {reasons}")
    for d in (fg.get("dasa") or [])[:2]:
        lines.append(f"• Dasa: {d['text_en']}")
    for t in (fg.get("transit") or [])[:3]:
        lines.append(f"• Transit: {t['text_en']}")
    return "\n".join(lines)
