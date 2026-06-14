"""
chart_store.py — server-side natal chart persistence (Steps 4–6).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)

try:
    from supabase_client import get_supabase
    _SB = True
except Exception:
    _SB = False


def save_natal_chart(user_id: str, chart: dict, birth_form: Optional[dict] = None) -> None:
    """Upsert full chart JSON for an authenticated user."""
    if not _SB:
        return
    try:
        sb = get_supabase()
        asc = chart.get("ascendant") or {}
        db_row: dict[str, Any] = {
            "user_id": user_id,
            "sun_sign": chart["planet_positions"]["Sun"]["sign"],
            "moon_sign": chart["planet_positions"]["Moon"]["sign"],
            "ascendant": asc.get("sign") if isinstance(asc, dict) else str(asc),
            "planet_positions": chart["planet_positions"],
            "yogas": chart.get("yogas", []),
            "ayanamsa": chart.get("ayanamsa", "Lahiri"),
            "ayanamsa_value": chart.get("ayanamsa_value"),
            "moon_nakshatra_index": chart.get("moon_nakshatra_index"),
            "moon_rasi_index": chart.get("moon_rasi_index"),
            "chart_data": chart,
        }
        if birth_form:
            db_row["birth_form"] = birth_form
        sb.table("natal_charts").upsert(db_row, on_conflict="user_id").execute()
    except Exception as exc:
        logger.exception("Failed to save natal chart for %s: %s", user_id, exc)


def load_natal_chart(user_id: str) -> Optional[dict]:
    """Load full chart from Supabase; returns None if not found."""
    if not _SB:
        return None
    try:
        sb = get_supabase()
        result = (
            sb.table("natal_charts")
            .select("chart_data, planet_positions, yogas, ayanamsa, ayanamsa_value, "
                    "moon_nakshatra_index, moon_rasi_index, ascendant, birth_form")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if not result or not result.data:
            return None

        row = result.data
        chart = None
        if row.get("chart_data"):
            chart = row["chart_data"]
        elif row.get("planet_positions"):
            # Legacy rows without chart_data — minimal reconstruction
            asc_sign = row.get("ascendant") or "Aries"
            chart = {
                "planet_positions": row["planet_positions"],
                "yogas": row.get("yogas") or [],
                "ayanamsa": row.get("ayanamsa") or "Lahiri",
                "ayanamsa_value": row.get("ayanamsa_value"),
                "moon_nakshatra_index": row.get("moon_nakshatra_index"),
                "moon_rasi_index": row.get("moon_rasi_index"),
                "ascendant": {"sign": asc_sign},
                "birth_data": (row.get("birth_form") or {}),
            }

        if not chart:
            return None

        from chart_utils import ensure_dasha

        had_dasha = bool((chart.get("dasha") or {}).get("mahadasha", {}).get("planet"))
        chart = ensure_dasha(chart)
        if not had_dasha and chart.get("dasha_available"):
            save_natal_chart(user_id, chart)
        return chart
    except Exception as exc:
        logger.exception("Failed to load natal chart for %s: %s", user_id, exc)
        return None


def resolve_natal_chart(
    client_chart: Optional[dict],
    auth_user_id: Optional[str],
    sanitise_fn,
) -> dict:
    """
    Prefer server-stored chart for authenticated users.
    Anonymous users must send natal_chart in the request body.
    """
    from security import validate_client_natal_chart

    from chart_utils import ensure_dasha

    if auth_user_id:
        stored = load_natal_chart(auth_user_id)
        if stored:
            return ensure_dasha(validate_client_natal_chart(stored, sanitise_fn))
        if client_chart:
            return ensure_dasha(validate_client_natal_chart(client_chart, sanitise_fn))
        raise HTTPException(
            status_code=404,
            detail="No saved chart. Calculate your birth chart on Home first.",
        )

    if not client_chart:
        raise HTTPException(status_code=400, detail="natal_chart is required.")
    return ensure_dasha(validate_client_natal_chart(client_chart, sanitise_fn))
