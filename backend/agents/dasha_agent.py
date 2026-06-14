"""
dasha_agent.py
==============
Vimshottari Mahadasha / Antardasha (Bhukti) for personal natal charts.

Uses sidereal Moon longitude at birth + date of birth to compute:
  - Balance of dasha at birth (from Moon's nakshatra position)
  - Current Mahadasha and Bhukti
  - Full antardasha sequence within current Mahadasha
  - Upcoming bhuktis and next mahadashas
"""

from __future__ import annotations

import datetime
from collections import OrderedDict
from typing import Optional

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3

DASA_DURATIONS: OrderedDict[str, int] = OrderedDict([
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
])

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

PLANET_FRIENDSHIPS: dict[str, dict[str, set[str]]] = {
    "Sun":     {"friends": {"Moon", "Mars", "Jupiter"},          "enemies": {"Venus", "Saturn", "Rahu", "Ketu"}},
    "Moon":    {"friends": {"Sun", "Mercury"},                  "enemies": {"Rahu", "Ketu"}},
    "Mercury": {"friends": {"Sun", "Venus"},                    "enemies": {"Moon"}},
    "Venus":   {"friends": {"Mercury", "Saturn"},               "enemies": {"Sun", "Moon", "Rahu", "Ketu"}},
    "Mars":    {"friends": {"Sun", "Moon", "Jupiter"},           "enemies": {"Mercury", "Rahu", "Ketu"}},
    "Jupiter": {"friends": {"Sun", "Moon", "Mars"},              "enemies": {"Mercury", "Venus", "Rahu", "Ketu"}},
    "Saturn":  {"friends": {"Mercury", "Venus", "Rahu", "Ketu"},  "enemies": {"Sun", "Moon", "Mars"}},
    "Rahu":    {"friends": {"Venus", "Saturn"},                 "enemies": {"Sun", "Moon", "Mars"}},
    "Ketu":    {"friends": {"Mars", "Jupiter"},                 "enemies": {"Sun", "Moon", "Venus"}},
}

_NAK_LEN = 360.0 / 27


def _get_nakshatra(longitude: float) -> tuple[str, int, int]:
    idx = int((longitude % 360) / _NAK_LEN)
    idx = min(idx, 26)
    pada = int(((longitude % _NAK_LEN) / (_NAK_LEN / 4))) + 1
    return NAKSHATRAS[idx], min(pada, 4), idx


def _get_relationship(dasha_lord: str, bhukti_lord: str) -> str:
    if dasha_lord == bhukti_lord:
        return "Same"
    rel = PLANET_FRIENDSHIPS.get(dasha_lord, {})
    if bhukti_lord in rel.get("friends", set()):
        return "Friend"
    if bhukti_lord in rel.get("enemies", set()):
        return "Enemy"
    return "Neutral"


def _fmt_period(dt: datetime.datetime) -> str:
    return dt.strftime("%b %Y")


def _fmt_period_day(dt: datetime.datetime) -> str:
    return dt.strftime("%d %b %Y")


def _generate_dashas(moon_long: float, birth_date_str: str) -> list[dict]:
    _, _, idx = _get_nakshatra(moon_long)
    portion_done = (moon_long % _NAK_LEN) / _NAK_LEN
    start_lord = NAKSHATRA_LORDS[idx]
    lords = list(DASA_DURATIONS.keys())
    start_i = lords.index(start_lord)

    birth_dt = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d")
    dashas: list[dict] = []
    current = birth_dt

    for i in range(3 * len(lords)):
        j = (start_i + i) % len(lords)
        planet = lords[j]
        full = float(DASA_DURATIONS[planet])
        years = full * (1.0 - portion_done) if i == 0 else full
        end = current + datetime.timedelta(days=years * 365.25)
        dashas.append({
            "planet": planet,
            "start": current,
            "end": end,
            "years": round(years, 2),
        })
        current = end

    return dashas


def _generate_bhuktis(dasha: dict) -> list[dict]:
    lords = list(DASA_DURATIONS.keys())
    m_lord = dasha["planet"]
    m_years = dasha["years"]
    start_i = lords.index(m_lord)
    current = dasha["start"]
    bhuktis: list[dict] = []

    for i in range(len(lords)):
        b_lord = lords[(start_i + i) % len(lords)]
        b_years = (DASA_DURATIONS[b_lord] / 120.0) * m_years
        end = current + datetime.timedelta(days=b_years * 365.25)
        bhuktis.append({
            "planet": b_lord,
            "start": current,
            "end": end,
            "years": round(b_years, 3),
        })
        current = end

    return bhuktis


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
        current_dt:     Reference datetime (defaults to UTC now)

    Returns:
        Structured dasha dict consumed by chat, forecast, and natal chart APIs.
    """
    if current_dt is None:
        current_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    moon_long = float(moon_longitude) % 360
    nak, pada, nak_idx = _get_nakshatra(moon_long)
    birth_lord = NAKSHATRA_LORDS[nak_idx]
    portion_done = (moon_long % _NAK_LEN) / _NAK_LEN
    balance_years = round(DASA_DURATIONS[birth_lord] * (1.0 - portion_done), 2)

    dashas = _generate_dashas(moon_long, birth_date)

    cur_dasha = next(
        (d for d in dashas if d["start"] <= current_dt < d["end"]),
        dashas[-1],
    )

    bhuktis = _generate_bhuktis(cur_dasha)
    cur_bhukti = next(
        (b for b in bhuktis if b["start"] <= current_dt < b["end"]),
        bhuktis[-1],
    )

    antardasha_sequence = [
        {
            "planet": b["planet"],
            "start": _fmt_period_day(b["start"]),
            "end": _fmt_period_day(b["end"]),
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
                "start": _fmt_period(b["start"]),
                "end": _fmt_period(b["end"]),
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
                "start": _fmt_period(d["start"]),
                "end": _fmt_period(d["end"]),
                "years": d["years"],
            })
            if len(next_dashas) == 5:
                break
        if d is cur_dasha:
            in_cur_d = True

    remaining_dasha_y = round(max(0, (cur_dasha["end"] - current_dt).days) / 365.25, 1)
    remaining_bhukti_m = round(max(0, (cur_bhukti["end"] - current_dt).days) / 30.44, 1)

    return {
        "nakshatra": nak,
        "pada": pada,
        "birth_nakshatra_lord": birth_lord,
        "balance_at_birth_years": balance_years,
        "mahadasha": {
            "planet": cur_dasha["planet"],
            "start": _fmt_period(cur_dasha["start"]),
            "end": _fmt_period(cur_dasha["end"]),
            "years": cur_dasha["years"],
            "focus": PERSONAL_DASHA_FOCUS.get(cur_dasha["planet"], ""),
            "remaining_years": remaining_dasha_y,
        },
        "bhukti": {
            "planet": cur_bhukti["planet"],
            "start": _fmt_period(cur_bhukti["start"]),
            "end": _fmt_period(cur_bhukti["end"]),
            "trigger": PERSONAL_BHUKTI_TRIGGER.get(cur_bhukti["planet"], ""),
            "remaining_months": remaining_bhukti_m,
        },
        "relationship": _get_relationship(cur_dasha["planet"], cur_bhukti["planet"]),
        "antardasha_sequence": antardasha_sequence,
        "upcoming_bhuktis": upcoming,
        "next_dashas": next_dashas,
    }
