"""
dasha_agent.py
==============
Personal Vimshottari Dasha agent for Jyotish AI.
Wraps the existing dasha_logic.py engine for individual natal charts.

Usage:
    from agents.dasha_agent import get_personal_dasha
    dasha = get_personal_dasha(moon_longitude=319.96, dob="1990-06-15")
"""

from __future__ import annotations

import datetime
from typing import Optional

from agents.dasha_logic import (
    _generate_dashas,
    _generate_bhuktis,
    _get_nakshatra,
    get_relationship,
    DASHA_FOCUS,
    BHUKTI_TRIGGER,
    DASA_DURATIONS,
)


def get_personal_dasha(
    moon_longitude: float,
    dob: str,
    current_dt: Optional[datetime.datetime] = None,
) -> dict:
    """
    Compute current Mahadasha + Bhukti for a personal natal chart.

    Args:
        moon_longitude: Sidereal Moon longitude from natal_agent (Lahiri)
        dob:            Date of birth 'YYYY-MM-DD'
        current_dt:     Date to evaluate (defaults to today)

    Returns:
        {
          nakshatra, pada,
          mahadasha: {planet, start, end, years, focus, remaining_years},
          bhukti:    {planet, start, end, trigger, remaining_months},
          antardasha_sequence: [{planet, start, end}, ...] all 9 bhuktis,
          upcoming_bhuktis: next 3 after current,
          next_dashas: next 5 mahadashas,
          relationship: "Friend"|"Enemy"|"Neutral"|"Same",
        }
    """
    if current_dt is None:
        current_dt = datetime.datetime.utcnow()

    nak, pada, _ = _get_nakshatra(moon_longitude)
    dashas = _generate_dashas(moon_longitude, dob)

    # Current Mahadasha
    cur_dasha = next(
        (d for d in dashas if d["start"] <= current_dt < d["end"]),
        dashas[-1],
    )

    # All Bhuktis for current Mahadasha
    bhuktis = _generate_bhuktis(cur_dasha)

    # Current Bhukti
    cur_bhukti = next(
        (b for b in bhuktis if b["start"] <= current_dt < b["end"]),
        bhuktis[-1],
    )

    # Upcoming 3 bhuktis after current
    upcoming: list[dict] = []
    in_current = False
    for b in bhuktis:
        if in_current:
            upcoming.append(b)
            if len(upcoming) == 3:
                break
        if b is cur_bhukti:
            in_current = True

    # Next 5 mahadashas
    next_dashas: list[dict] = []
    in_cur_d = False
    for d in dashas:
        if in_cur_d:
            next_dashas.append(d)
            if len(next_dashas) == 5:
                break
        if d is cur_dasha:
            in_cur_d = True

    remaining_dasha_y  = round((cur_dasha["end"]  - current_dt).days / 365.25, 1)
    remaining_bhukti_m = round((cur_bhukti["end"] - current_dt).days / 30.44,  1)

    def _fmt(dt: datetime.datetime) -> str:
        return dt.strftime("%b %Y")

    return {
        "nakshatra": nak,
        "pada":      pada,
        "mahadasha": {
            "planet":          cur_dasha["planet"],
            "start":           _fmt(cur_dasha["start"]),
            "end":             _fmt(cur_dasha["end"]),
            "years":           cur_dasha["years"],
            "focus":           DASHA_FOCUS.get(cur_dasha["planet"], ""),
            "remaining_years": remaining_dasha_y,
        },
        "bhukti": {
            "planet":           cur_bhukti["planet"],
            "start":            _fmt(cur_bhukti["start"]),
            "end":              _fmt(cur_bhukti["end"]),
            "trigger":          BHUKTI_TRIGGER.get(cur_bhukti["planet"], ""),
            "remaining_months": remaining_bhukti_m,
        },
        "antardasha_sequence": [
            {"planet": b["planet"], "start": _fmt(b["start"]), "end": _fmt(b["end"])}
            for b in bhuktis
        ],
        "upcoming_bhuktis": [
            {"planet": b["planet"], "start": _fmt(b["start"]), "end": _fmt(b["end"])}
            for b in upcoming
        ],
        "next_dashas": [
            {"planet": d["planet"], "start": _fmt(d["start"]),
             "end": _fmt(d["end"]), "years": d["years"]}
            for d in next_dashas
        ],
        "relationship": get_relationship(cur_dasha["planet"], cur_bhukti["planet"]),
    }
