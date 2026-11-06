"""Fixes shared by several tabs: stale check, lord placement count, birth offset, fresh dasha."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from agents.natal_agent import calculate_natal_chart
from agents.transit_score_agent import _natal_house_strength, score_all_houses
from chart_utils import ensure_dasha, is_chart_stale
from time_utils import today_in


def _chart(dob, tob, lat, lon, tz):
    chart = calculate_natal_chart(dob, tob, lat, lon, tz)
    chart["birth_data"].update({"dob": dob, "tob": tob, "lat": lat, "lon": lon, "timezone": tz})
    return chart


@pytest.mark.parametrize("dob", ["1943-05-10", "1978-09-18", "2010-08-01", "2016-03-05", "2024-12-31"])
def test_fresh_lahiri_charts_are_not_stale(dob):
    assert not is_chart_stale(_chart(dob, "06:30", 13.08, 80.27, "Asia/Kolkata"))


def test_fagan_value_labelled_lahiri_is_stale():
    chart = _chart("1978-09-18", "17:35", 13.08, 80.27, "Asia/Kolkata")
    chart["ayanamsa_value"] = 24.4430
    assert is_chart_stale(chart)


def test_lord_placement_counts_inclusively():
    lord = {"State": "Neutral", "Deep": False}
    own = _natal_house_strength(5, lord, [], [], 1)
    ninth = _natal_house_strength(5, lord, [], [], 9)
    eighth = _natal_house_strength(5, lord, [], [], 8)
    assert own >= ninth > eighth


@pytest.mark.parametrize("dob,tob,lat,lon,tz", [
    ("1943-05-10", "06:30", 13.08, 80.27, "Asia/Kolkata"),
    ("1985-07-04", "09:15", 40.71, -74.01, "America/New_York"),
    ("1990-07-15", "07:40", 51.51, -0.13, "Europe/London"),
])
def test_transit_scorer_lagna_matches_natal_chart(dob, tob, lat, lon, tz):
    chart = _chart(dob, tob, lat, lon, tz)
    scores = score_all_houses(chart, "2026-01-15", "12:00")
    assert scores["lagna_en"] == chart["ascendant"]["sign"]


def test_saved_dasha_is_recomputed():
    chart = _chart("1978-09-18", "17:35", 13.08, 80.27, "Asia/Kolkata")
    chart["dasha"] = {"mahadasha": {"planet": "Sun"}, "bhukti": {"planet": "Sun"}, "timeline": [{"x": 1}]}
    fresh = ensure_dasha(chart)["dasha"]
    assert fresh["mahadasha"]["planet"] != "Sun" or fresh["bhukti"]["planet"] != "Sun"
    assert fresh.get("antardasha_sequence")


def test_today_in_uses_zone():
    assert today_in("Asia/Kolkata") == datetime.now(ZoneInfo("Asia/Kolkata")).date()
    assert isinstance(today_in("Not/AZone"), date)
