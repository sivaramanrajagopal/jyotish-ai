"""D3 (Drekkana) — Parasara decan method aligned with d3-calculator repo."""

from __future__ import annotations

from agents.health.body_map import drekkana_section
from agents.natal_agent import SIGNS, SIGN_LORDS, _house_number, _lon_to_nakshatra

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]


def d1_to_d3_sign_index(d1_sign_index: int, degree_in_sign: float) -> int:
    """D3 sign from D1 sign + degree (decan: same / 5th / 9th)."""
    section = drekkana_section(degree_in_sign)
    base = int(d1_sign_index) % 12
    if section == "first":
        return base
    if section == "second":
        return (base + 4) % 12
    return (base + 8) % 12


def d3_degree_in_sign(degree_in_sign: float) -> float:
    d = float(degree_in_sign) % 30.0
    section = drekkana_section(d)
    if section == "first":
        offset = d
    elif section == "second":
        offset = d - 10.0
    else:
        offset = d - 20.0
    return max(0.0, min(30.0, offset * 3.0))


def build_drekkana_from_natal(natal_chart: dict) -> tuple[dict, dict]:
    """Drekkana ascendant + positions — same shape as D10 for SouthIndianChart."""
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}

    asc_idx = asc.get("sign_index", 0)
    asc_deg = float(asc.get("degree_in_sign", asc.get("longitude", 0) % 30))
    d3_asc_idx = d1_to_d3_sign_index(asc_idx, asc_deg)
    d3_asc_deg = d3_degree_in_sign(asc_deg)
    d3_asc_lon = d3_asc_idx * 30.0 + d3_asc_deg
    asc_sign = SIGNS[d3_asc_idx]
    naks, naks_lord, pada = _lon_to_nakshatra(d3_asc_lon)

    drekkana_ascendant = {
        "sign": asc_sign,
        "sign_index": d3_asc_idx,
        "sign_lord": SIGN_LORDS[asc_sign],
        "longitude": round(d3_asc_lon, 4),
        "degree_in_sign": round(d3_asc_deg, 4),
        "nakshatra": naks,
        "nakshatra_lord": naks_lord,
        "pada": pada,
    }

    drekkana_positions: dict[str, dict] = {}
    for pname in PLANETS:
        if pname not in pp:
            continue
        pdata = pp[pname]
        d1_idx = pdata.get("sign_index", 0)
        d1_deg = float(pdata.get("degree_in_sign", 0))
        d3_idx = d1_to_d3_sign_index(d1_idx, d1_deg)
        d3_deg = d3_degree_in_sign(d1_deg)
        d3_lon = d3_idx * 30.0 + d3_deg
        sign = SIGNS[d3_idx]
        naks, naks_lord, pada = _lon_to_nakshatra(d3_lon)
        drekkana_positions[pname] = {
            "sign": sign,
            "sign_index": d3_idx,
            "sign_lord": SIGN_LORDS[sign],
            "house": _house_number(d3_idx, d3_asc_idx),
            "longitude": round(d3_lon, 4),
            "degree_in_sign": round(d3_deg, 4),
            "d1_degree_in_sign": round(d1_deg, 4),
            "nakshatra": naks,
            "nakshatra_lord": naks_lord,
            "pada": pada,
            "retrograde": bool(pdata.get("retrograde")),
        }

    return drekkana_ascendant, drekkana_positions
