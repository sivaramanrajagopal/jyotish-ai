"""Smoke tests — no network or OpenAI required."""

from chart_utils import chart_fingerprint, is_chart_stale, round_score
from location_utils import nearest_panchangam_location, resolve_panchangam_location


def test_round_score():
    assert round_score(71.8) == 72
    assert round_score(None) == 0


def test_chart_stale():
    assert is_chart_stale({"ayanamsa": "Lahiri", "ayanamsa_value": 24.5}) is True
    assert is_chart_stale({"ayanamsa": "Lahiri", "ayanamsa_value": 23.85}) is False
    assert is_chart_stale({}) is True


def test_chart_fingerprint_changes_with_ayanamsa():
    a = {"ascendant": {"sign": "Aquarius"}, "planet_positions": {"Sun": {"sign": "Virgo"}}, "ayanamsa_value": 23.9}
    b = {**a, "ayanamsa_value": 24.5}
    assert chart_fingerprint(a) != chart_fingerprint(b)


def test_nearest_panchangam_location():
    assert nearest_panchangam_location(11.0168, 76.9558) == "Coimbatore"
    assert nearest_panchangam_location(19.0760, 72.8777) == "Mumbai"


def test_resolve_panchangam_location_text():
    assert resolve_panchangam_location("Chennai, India") == "Chennai"
    assert resolve_panchangam_location("Unknown Town", lat=12.97, lon=77.59) == "Bangalore"
