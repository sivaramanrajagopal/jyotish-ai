"""House Links upcoming: next bhuktis, their houses, double-transit windows, sign changes."""

from datetime import date

from agents.house_connections.core import analyze_all_houses
from agents.house_connections.upcoming import compute_upcoming, sign_changes, sky_segments
from agents.natal_agent import calculate_natal_chart

AS_OF = date(2026, 11, 6)


def _upcoming() -> dict:
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    return compute_upcoming(chart, analyze_all_houses(chart), AS_OF)


def test_next_three_bhuktis_cross_into_mars_mahadasha():
    periods = _upcoming()["periods"]
    assert [(p["mahadasha"], p["bhukti"]) for p in periods] == [
        ("Moon", "Venus"), ("Moon", "Sun"), ("Mars", "Mars"),
    ]
    assert periods[0]["start"] == "7 Jan 2027"


def test_venus_bhukti_houses_and_relation():
    venus = _upcoming()["periods"][0]
    assert [h["house"] for h in venus["houses"]] == [4, 9]
    assert venus["relation"]["tone"] == "uneasy"  # Venus in the 9th is the 8th from the Moon in the 2nd


def test_double_transit_window_on_the_4th():
    venus = _upcoming()["periods"][0]
    fourth = next(h for h in venus["houses"] if h["house"] == 4)
    # Jupiter in Virgo (8th) aspects the 4th; Saturn in Pisces (2nd) aspects the 4th.
    assert fourth["windows"][0]["start"] == "27 Nov 2027"


def test_retrograde_reentry_is_its_own_sign_change():
    changes = sign_changes(sky_segments(AS_OF, date(2027, 3, 1)), 10)
    jupiter = [c for c in changes if c["planet"] == "Jupiter"]
    assert jupiter and jupiter[0]["sign"] == "Cancer" and jupiter[0]["house"] == 6


def test_no_dob_returns_none():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {}
    assert compute_upcoming(chart, analyze_all_houses(chart), AS_OF) is None
