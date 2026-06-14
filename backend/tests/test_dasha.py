"""Dasha engine tests — no network required."""

import datetime

from agents.dasha_agent import get_personal_dasha, _get_nakshatra
from agents.natal_agent import calculate_natal_chart


def test_get_nakshatra_pushya():
    # Pushya is index 7; ~100° sidereal falls in Pushya
    nak, pada, idx = _get_nakshatra(100.0)
    assert nak == "Pushya"
    assert pada >= 1
    assert idx == 7


def test_personal_dasha_structure():
    result = get_personal_dasha(100.0, "1990-06-15")
    md = result["mahadasha"]
    bh = result["bhukti"]
    assert md["planet"] in {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"}
    assert bh["planet"] in {"Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"}
    assert md["start"]
    assert md["end"]
    assert isinstance(md["remaining_years"], (int, float))
    assert len(result["antardasha_sequence"]) == 9
    assert result["relationship"] in {"Same", "Friend", "Enemy", "Neutral"}
    assert result["balance_at_birth_years"] > 0


def test_dasha_from_natal_chart():
    chart = calculate_natal_chart(
        "1990-06-15", "14:30", 13.0827, 80.2707, "Asia/Kolkata",
    )
    moon_lon = chart["planet_positions"]["Moon"]["longitude"]
    dasha = get_personal_dasha(moon_lon, "1990-06-15")
    assert dasha["nakshatra"] == chart["planet_positions"]["Moon"]["nakshatra"]
    assert dasha["mahadasha"]["planet"]


def test_current_dasha_covers_reference_date():
    ref = datetime.datetime(2026, 6, 6)
    result = get_personal_dasha(100.0, "1990-06-15", current_dt=ref)
    md = result["mahadasha"]
    bh = result["bhukti"]
    assert md["remaining_years"] >= 0
    assert bh["remaining_months"] >= 0
