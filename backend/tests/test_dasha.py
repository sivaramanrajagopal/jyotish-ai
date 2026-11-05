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


def test_ensure_dasha_backfill_missing():
    from chart_utils import ensure_dasha

    chart = {
        "planet_positions": {"Moon": {"longitude": 354.14, "sign": "Pisces"}},
        "birth_data": {"dob": "1978-09-18"},
        "dasha": {},
    }
    result = ensure_dasha(chart)
    assert result["dasha_available"] is True
    assert result["dasha"]["mahadasha"]["planet"]


def test_ensure_dasha_skips_when_present():
    from chart_utils import ensure_dasha

    chart = {
        "planet_positions": {"Moon": {"longitude": 100.0}},
        "birth_data": {"dob": "1990-06-15"},
        "dasha": {"mahadasha": {"planet": "Venus"}, "timeline": [{"planet": "Venus"}]},
    }
    result = ensure_dasha(chart)
    assert result["dasha"]["mahadasha"]["planet"] == "Venus"
    assert result["dasha_available"] is True


def test_ensure_dasha_adds_timeline_to_old_chart():
    from chart_utils import ensure_dasha

    chart = {
        "planet_positions": {"Moon": {"longitude": 354.14}},
        "birth_data": {"dob": "1978-09-18"},
        "dasha": {"mahadasha": {"planet": "Venus"}},
    }
    result = ensure_dasha(chart)
    assert len(result["dasha"]["timeline"]) == 9


def test_birth_mahadasha_bhuktis_continue_from_before_birth():
    from dasha_core import generate_bhuktis, generate_dashas

    # Moon 354.14° is Revati (Mercury) with 56% already travelled, so the
    # native is born inside Mercury–Rahu, not at the start of Mercury–Mercury.
    first = generate_dashas(354.14, "1978-09-18")[0]
    bhuktis = generate_bhuktis(first)
    assert first["planet"] == "Mercury"
    assert [b["planet"] for b in bhuktis] == ["Rahu", "Jupiter", "Saturn"]
    assert bhuktis[0]["start"] == datetime.datetime(1978, 9, 18)
    assert bhuktis[-1]["end"] == first["end"]
    assert abs(bhuktis[0]["full_years"] - 18 / 120 * 17) < 1e-9
    assert bhuktis[0]["years"] < bhuktis[0]["full_years"]
    assert abs(bhuktis[1]["years"] - 16 / 120 * 17) < 1e-3


def test_full_timeline_for_chart_a():
    ref = datetime.datetime(2026, 11, 5)
    timeline = get_personal_dasha(354.14, "1978-09-18", current_dt=ref)["timeline"]
    assert [row["planet"] for row in timeline] == [
        "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn",
    ]
    assert timeline[0]["balance"] is True
    assert timeline[0]["start"] == "1978-09-18"
    for prev, nxt in zip(timeline, timeline[1:]):
        assert prev["end"] == nxt["start"]
        assert nxt["bhuktis"][0]["planet"] == nxt["planet"]
        assert nxt["bhuktis"][0]["start"] == nxt["start"]
        assert nxt["bhuktis"][-1]["end"] == nxt["end"]
    moon = next(row for row in timeline if row["planet"] == "Moon")
    assert moon["current"] is True
    current = [b for b in moon["bhuktis"] if b["current"]]
    assert [b["planet"] for b in current] == ["Ketu"]
    assert sum(row["current"] for row in timeline) == 1
