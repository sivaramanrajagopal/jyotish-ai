"""
dasha_agent.py
==============
Vimshottari Mahadasha / Antardasha (Bhukti) for personal natal charts.

Calculation lives in dasha_core.py (shared with Mundane Astrology dashboard).
"""

from __future__ import annotations

import datetime
from typing import Optional

from dasha_core import (
    DASA_DURATIONS,
    NAKSHATRA_LORDS,
    find_current_dasha_bhukti,
    fmt_period,
    fmt_period_day,
    format_bhukti_table,
    get_nakshatra,
    get_relationship,
)

# Re-export for tests / backwards compatibility
_get_nakshatra = get_nakshatra

PERSONAL_DASHA_FOCUS = {
    "Sun":     "Identity, authority, vitality, and father figures",
    "Moon":    "Emotions, mind, home, and mother",
    "Mercury": "Communication, learning, business, and skills",
    "Venus":   "Relationships, comfort, creativity, and finances",
    "Mars":    "Energy, courage, property, and competition",
    "Jupiter": "Wisdom, growth, children, and fortune",
    "Saturn":  "Discipline, karma, delays, and long-term results",
    "Rahu":    "Ambition, foreign influence, and unconventional paths",
    "Ketu":    "Spirituality, detachment, and past-karma resolution",
}

PERSONAL_BHUKTI_TRIGGER = {
    "Sun":     "Leadership roles, health focus, recognition",
    "Moon":    "Emotional shifts, travel, public visibility",
    "Mercury": "Contracts, studies, communication projects",
    "Venus":   "Marriage, romance, luxury purchases, arts",
    "Mars":    "Property, surgery, sports, conflicts",
    "Jupiter": "Education, children, legal matters, expansion",
    "Saturn":  "Hard work, responsibility, structural changes",
    "Rahu":    "Sudden opportunities, foreign connections, tech",
    "Ketu":    "Letting go, spiritual pursuits, isolation",
}


def get_personal_dasha(
    moon_longitude: float,
    birth_date: str,
    current_dt: Optional[datetime.datetime] = None,
) -> dict:
    """
    Compute Vimshottari dasha for a native.

    Args:
        moon_longitude: Sidereal Moon longitude at birth (0–360)
        birth_date:     Date of birth 'YYYY-MM-DD'
        current_dt:     Reference datetime (defaults to UTC now, naive)

    Returns:
        Structured dasha dict consumed by chat, forecast, and natal chart APIs.
    """
    if current_dt is None:
        current_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    moon_long = float(moon_longitude) % 360
    nak, pada, nak_idx = get_nakshatra(moon_long)
    birth_lord = NAKSHATRA_LORDS[nak_idx]
    portion_done = (moon_long % (360.0 / 27)) / (360.0 / 27)
    balance_years = round(DASA_DURATIONS[birth_lord] * (1.0 - portion_done), 2)

    dashas, cur_dasha, bhuktis, cur_bhukti = find_current_dasha_bhukti(
        moon_long, birth_date, current_dt
    )

    antardasha_sequence = [
        {
            "planet": b["planet"],
            "start": fmt_period_day(b["start"]),
            "end": fmt_period_day(b["end"]),
            "years": b["years"],
        }
        for b in bhuktis
    ]

    upcoming: list[dict] = []
    in_current = False
    for b in bhuktis:
        if in_current:
            upcoming.append({
                "planet": b["planet"],
                "start": fmt_period(b["start"]),
                "end": fmt_period(b["end"]),
            })
            if len(upcoming) == 3:
                break
        if b is cur_bhukti:
            in_current = True

    next_dashas: list[dict] = []
    in_cur_d = False
    for d in dashas:
        if in_cur_d:
            next_dashas.append({
                "planet": d["planet"],
                "start": fmt_period(d["start"]),
                "end": fmt_period(d["end"]),
                "years": d["years"],
            })
            if len(next_dashas) == 5:
                break
        if d is cur_dasha:
            in_cur_d = True

    remaining_dasha_y = round(max(0, (cur_dasha["end"] - current_dt).days) / 365.25, 1)
    remaining_bhukti_m = round(max(0, (cur_bhukti["end"] - current_dt).days) / 30.44, 1)

    result = {
        "nakshatra": nak,
        "pada": pada,
        "birth_nakshatra_lord": birth_lord,
        "balance_at_birth_years": balance_years,
        "mahadasha": {
            "planet": cur_dasha["planet"],
            "start": fmt_period(cur_dasha["start"]),
            "end": fmt_period(cur_dasha["end"]),
            "years": cur_dasha["years"],
            "focus": PERSONAL_DASHA_FOCUS.get(cur_dasha["planet"], ""),
            "remaining_years": remaining_dasha_y,
        },
        "bhukti": {
            "planet": cur_bhukti["planet"],
            "start": fmt_period(cur_bhukti["start"]),
            "end": fmt_period(cur_bhukti["end"]),
            "trigger": PERSONAL_BHUKTI_TRIGGER.get(cur_bhukti["planet"], ""),
            "remaining_months": remaining_bhukti_m,
        },
        "relationship": get_relationship(cur_dasha["planet"], cur_bhukti["planet"]),
        "antardasha_sequence": antardasha_sequence,
        "upcoming_bhuktis": upcoming,
        "next_dashas": next_dashas,
    }
    result["bhukti_table_markdown"] = format_bhukti_table(result)
    return result
