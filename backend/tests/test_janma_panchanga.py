"""Janma tithi, yoga, and karana from natal longitudes."""

from agents.janma_panchanga import KARANA_PRACTICE, build_janma_panchanga
from agents.natal_agent import calculate_natal_chart
from agents.panchangam_agent import TITHIS, YOGAS, _karanam_index_and_name


def test_garija_practice_is_elephant():
    row = KARANA_PRACTICE["Garija"]
    assert row["name_ta"] == "கரசை"
    assert row["alias"] == "Karajai"
    assert row["lord"] == "Moon"
    assert row["animal"] == "Elephant"
    assert len(KARANA_PRACTICE) == 11


def test_chennai_birth_matches_sun_moon_gap():
    chart = calculate_natal_chart(
        "1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata",
    )
    sun = chart["planet_positions"]["Sun"]["longitude"]
    moon = chart["planet_positions"]["Moon"]["longitude"]
    diff = (moon - sun) % 360
    tithi_idx = int(diff / 12) % 30
    _, karana = _karanam_index_and_name(int(diff / 6) % 60)
    yoga_idx = int(((moon + sun) % 360) / (360 / 27)) % 27

    out = build_janma_panchanga(chart)
    assert out["vaara"]["name"] == "Somavaram"
    assert out["vaara"]["lord"] == "Moon"
    assert out["tithi"]["name"] == TITHIS[tithi_idx]
    assert out["tithi"]["paksha"] == ("Shukla" if tithi_idx < 15 else "Krishna")
    assert out["yoga"]["name"] == YOGAS[yoga_idx]
    assert out["karana"]["name"] == karana
    assert out["nakshatra"]["name"] == chart["planet_positions"]["Moon"]["nakshatra"]
    assert out["time_is_noon"] is False
    assert len(out["karanas"]) == 11
    assert "wallpaper" in out["karana"]["practice"]["en"]


def test_approximate_time_note():
    chart = calculate_natal_chart(
        "1978-09-18", "12:00", 13.0827, 80.2707, "Asia/Kolkata",
    )
    chart["birth_data"]["birth_time_approximate"] = True
    out = build_janma_panchanga(chart)
    assert out["time_is_noon"] is True
    assert "noon" in out["note"]
