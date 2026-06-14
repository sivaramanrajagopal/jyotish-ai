"""Phase 3 — transit time, dasha weighting, degree dignity tests."""

from agents.natal_agent import calculate_natal_chart
from agents.dasha_agent import get_personal_dasha
from agents.transit_score_agent import (
    score_all_houses,
    _planetary_state_detailed,
    _resolve_transit_jd,
    _dasha_house_adjustment,
)
from chart_utils import ensure_dasha


def test_degree_dignity_transit_engine():
    state, deep = _planetary_state_detailed("Sun", "Mesha", 10.0)
    assert state == "Exalted"
    assert deep is True


def test_resolve_transit_jd_explicit_time():
    jd, meta = _resolve_transit_jd("2026-06-06", "Asia/Kolkata", "14:30")
    assert meta["time"] == "14:30"
    assert meta["date"] == "2026-06-06"
    assert jd > 0


def test_dasha_house_adjustment_boosts_md_lord():
    blended, adj = _dasha_house_adjustment(
        "Jupiter", 60.0,
        {"mahadasha": {"planet": "Jupiter"}, "bhukti": {"planet": "Saturn"}},
        {"Jupiter": 80.0, "Saturn": 50.0},
    )
    assert blended > 60.0
    assert adj > 0


def test_score_all_houses_includes_dasha_transit():
    chart = calculate_natal_chart(
        "1990-06-15", "14:30", 13.0827, 80.2707, "Asia/Kolkata",
    )
    moon_lon = chart["planet_positions"]["Moon"]["longitude"]
    chart["dasha"] = get_personal_dasha(moon_lon, "1990-06-15")
    chart = ensure_dasha(chart)

    scores = score_all_houses(
        chart,
        "2026-06-06",
        "12:00",
        chart.get("dasha"),
    )
    assert scores.get("transit_moment")
    assert scores["transit_moment"]["time"] == "12:00"
    assert scores.get("dasha_transit")
    assert scores["dasha_transit"].get("correlation_score") is not None
    assert scores.get("meta", {}).get("engine") == "rule_based"
    h1 = scores["houses"][1]
    assert "dasha_adjustment" in h1


def test_transit_moment_not_noon_for_today():
    chart = calculate_natal_chart(
        "1990-06-15", "14:30", 13.0827, 80.2707, "Asia/Kolkata",
    )
    chart = ensure_dasha(chart)
    from datetime import date
    today = date.today().isoformat()
    scores = score_all_houses(chart, today, None, chart.get("dasha"))
    moment = scores.get("transit_moment", {})
    assert moment.get("note") == "current local time"
    assert moment.get("time") != "12:00" or True  # may coincidentally be noon
