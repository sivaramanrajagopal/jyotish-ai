"""
Shared helpers for chart caching and score formatting.
"""

from __future__ import annotations

from fastapi import HTTPException


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


def is_chart_stale(natal_chart: dict) -> bool:
    """Charts saved before the Lahiri ayanamsa fix may use wrong sidereal positions."""
    if not natal_chart:
        return True
    ayan = natal_chart.get("ayanamsa_value")
    if ayan is None:
        return True
    try:
        return natal_chart.get("ayanamsa") == "Lahiri" and float(ayan) > 24.0
    except (TypeError, ValueError):
        return True


def assert_chart_not_stale(natal_chart: dict) -> None:
    if is_chart_stale(natal_chart):
        raise HTTPException(
            status_code=409,
            detail=(
                "Your chart was saved before a calculation update. "
                "Please recalculate on Home to refresh Lahiri positions."
            ),
        )


def ensure_dasha(natal_chart: dict) -> dict:
    """Compute Vimshottari dasha if missing from a saved chart."""
    dasha = natal_chart.get("dasha") or {}
    if dasha.get("mahadasha", {}).get("planet"):
        natal_chart["dasha_available"] = True
        return natal_chart
    try:
        from agents.dasha_agent import get_personal_dasha
        moon_lon = natal_chart["planet_positions"]["Moon"]["longitude"]
        dob = natal_chart.get("birth_data", {}).get("dob", "")
        if moon_lon is not None and dob:
            natal_chart["dasha"] = get_personal_dasha(moon_lon, dob)
            natal_chart["dasha_available"] = bool(
                natal_chart["dasha"].get("mahadasha", {}).get("planet")
            )
    except Exception:
        natal_chart.setdefault("dasha", {})
        natal_chart["dasha_available"] = False
    return natal_chart
