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


def expected_lahiri(dob: str) -> float | None:
    """Approximate Lahiri ayanamsa for a YYYY-MM-DD date (within 0.005° for 1900–2060)."""
    try:
        y, m, d = (int(x) for x in str(dob)[:10].split("-"))
    except (TypeError, ValueError):
        return None
    return 23.8531 + 0.013969 * (y + (m - 1) / 12 + (d - 1) / 365.25 - 2000)


def is_chart_stale(natal_chart: dict) -> bool:
    """
    Charts saved before the Lahiri ayanamsa fix carry Fagan–Bradley values labelled
    Lahiri (about 0.88° higher). Compare against the Lahiri value for the birth date.
    """
    if not natal_chart:
        return True
    ayan = natal_chart.get("ayanamsa_value")
    if ayan is None:
        return True
    try:
        ayan = float(ayan)
    except (TypeError, ValueError):
        return True
    if natal_chart.get("ayanamsa") != "Lahiri":
        return False
    expected = expected_lahiri((natal_chart.get("birth_data") or {}).get("dob"))
    if expected is None:
        return ayan > 24.0
    return abs(ayan - expected) > 0.3


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
    """Recompute Vimshottari dasha as of now; a saved chart's running periods go stale."""
    return refresh_dasha(natal_chart, force=True)


def refresh_dasha(natal_chart: dict, *, force: bool = True) -> dict:
    """
    Recompute Vimshottari dasha from Moon longitude + DOB.
    force=True (default): always refresh — use before chat/forecast for accurate dates.
    force=False: skip if mahadasha already present (legacy ensure_dasha behaviour).
    """
    dasha = natal_chart.get("dasha") or {}
    if not force and dasha.get("mahadasha", {}).get("planet") and dasha.get("timeline"):
        if dasha.get("antardasha_sequence") and not dasha.get("bhukti_table_markdown"):
            try:
                from dasha_core import format_bhukti_table, format_mahadasha_timeline_table, format_full_dasha_cycle_markdown
                dasha["bhukti_table_markdown"] = format_bhukti_table(dasha)
                dasha["mahadasha_timeline_markdown"] = format_mahadasha_timeline_table(dasha)
                dasha["full_dasha_cycle_markdown"] = format_full_dasha_cycle_markdown(dasha)
                natal_chart["dasha"] = dasha
            except Exception:
                pass
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
        natal_chart["dasha_available"] = bool(
            (natal_chart.get("dasha") or {}).get("mahadasha", {}).get("planet")
        )
    return natal_chart
