"""Bhavat Bhavam agent — compute + chat narrator context."""

from __future__ import annotations

from agents.bhavat_bhavam.slices import (
    compute_career_bhavat_bhavam,
    compute_health_bhavat_bhavam,
    DISCLAIMER_EN,
)
from dasha_core import find_current_dasha_bhukti


def _dasa_lords(natal_chart: dict) -> tuple[str, str]:
    bd = natal_chart.get("birth_data") or {}
    pp = natal_chart.get("planet_positions") or {}
    if not bd.get("dob"):
        return "", ""
    moon_lon = (pp.get("Moon") or {}).get("longitude", 0.0)
    _, cur_d, _, cur_b = find_current_dasha_bhukti(moon_lon, bd["dob"])
    return cur_d["planet"], cur_b["planet"]


def compute_bhavat_bhavam(natal_chart: dict) -> dict:
    maha, bhukti = _dasa_lords(natal_chart)
    health = compute_health_bhavat_bhavam(natal_chart, maha=maha, bhukti=bhukti)
    career = compute_career_bhavat_bhavam(natal_chart, maha=maha, bhukti=bhukti)
    return {
        "health": health,
        "career": career,
        "maha_dasa": maha,
        "bhukti": bhukti,
    }


def bhavat_bhavam_context_for_narrator(natal_chart: dict) -> str:
    try:
        data = compute_bhavat_bhavam(natal_chart)
    except Exception:
        return ""

    lines = [
        "=== Bhavat Bhavam (D1 whole-sign) ===",
        f"DISCLAIMER: {DISCLAIMER_EN}",
        f"Dasa: {data['maha_dasa']}–{data['bhukti']}",
    ]

    for section_key, label in (("health", "Health"), ("career", "Career")):
        section = data.get(section_key) or {}
        links = section.get("links") or []
        if not links:
            continue
        lines.append(f"{label} links:")
        for lk in links[:4]:
            lines.append(
                f"• H{lk['primary_house']}→H{lk['bb_house']} "
                f"({lk['signal']}): {lk['insight_en']}"
            )

    if len(lines) <= 3:
        return ""
    return "\n".join(lines)
