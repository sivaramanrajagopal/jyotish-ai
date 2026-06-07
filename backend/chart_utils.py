"""
Shared helpers for chart caching and score formatting.
"""

from __future__ import annotations


def round_score(value) -> int:
    """Round a 0–100 score to the nearest integer for display and prompts."""
    if value is None:
        return 0
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0


def chart_fingerprint(natal_chart: dict) -> str:
    """
    Fingerprint planet signs + ayanamsa so cache invalidates after recalculation.
    """
    pp = natal_chart.get("planet_positions") or {}
    asc = natal_chart.get("ascendant") or {}
    asc_sign = asc.get("sign", "") if isinstance(asc, dict) else str(asc)

    parts = [asc_sign]
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        pos = pp.get(planet) or {}
        parts.append(pos.get("sign", "") if isinstance(pos, dict) else "")

    ayan = natal_chart.get("ayanamsa_value")
    ayan_str = f"{ayan:.4f}" if isinstance(ayan, (int, float)) else str(ayan or "")
    parts.append(ayan_str)
    return "|".join(parts)
