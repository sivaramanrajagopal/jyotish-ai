"""Dasa life-area activation chain tests."""

import pytest

from agents.house_connections.dasa_activation import (
    build_activation_chain,
    compute_dasa_life_areas,
)
from agents.natal_agent import calculate_natal_chart
from agents.bhavat_bhavam.core import lord_of_house, whole_sign_house

CHENNAI = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}


@pytest.fixture
def chart():
    return calculate_natal_chart(
        CHENNAI["dob"], CHENNAI["tob"],
        CHENNAI["lat"], CHENNAI["lon"], CHENNAI["tz"],
    )


def test_seven_steps_for_moon_dasha(chart):
    chain = build_activation_chain("Moon", chart, period="mahadasha")
    assert len(chain["steps"]) == 7
    assert chain["steps"][0]["key"] == "dasa_seat"
    assert chain["steps"][-1]["key"] == "dasa_seat_anchor"


def test_moon_dasha_activation_houses(chart):
    """Moon in Revati → Mercury link; Moon rules 6th; Jupiter in 6th spreads 2 & 11."""
    asc = chart["ascendant"]["sign_index"]
    moon_h = whole_sign_house(chart["planet_positions"]["Moon"]["sign_index"], asc)
    chain = build_activation_chain("Moon", chart, period="mahadasha")

    assert moon_h == 2
    assert chart["planet_positions"]["Moon"]["nakshatra"] == "Revati"
    assert chain["nakshatra_lord"] == "Mercury"

    focus = set(chain["focus_houses"])
    # H2 seat, H5/H8 Mercury, H7 Mercury seat, H6 Moon, H2/H11 Jupiter spread
    assert 2 in focus
    assert 5 in focus
    assert 6 in focus
    assert 7 in focus
    assert 8 in focus
    assert 11 in focus
    assert focus == {2, 5, 6, 7, 8, 11}


def test_step5_occupant_spread_from_dasa_owned_houses(chart):
    asc = chart["ascendant"]["sign_index"]
    moon_owned = [h for h in range(1, 13) if lord_of_house(asc, h) == "Moon"]
    assert moon_owned == [6]

    chain = build_activation_chain("Moon", chart, period="mahadasha")
    step5 = next(s for s in chain["steps"] if s["key"] == "occupant_spread")
    assert 2 in step5["houses_all"]
    assert 11 in step5["houses_all"]
    assert "Jupiter" in step5["detail_en"]


def test_combined_maha_bhukti_union(chart):
    out = compute_dasa_life_areas(chart, "Moon", "Mercury")
    maha_focus = set(out["mahadasha"]["focus_houses"])
    bhukti_focus = set(out["antardasha"]["focus_houses"])
    combined = set(out["combined"]["focus_houses"])
    assert combined == maha_focus | bhukti_focus


def test_background_houses_are_complement(chart):
    chain = build_activation_chain("Saturn", chart, period="mahadasha")
    focus = set(chain["focus_houses"])
    bg = set(chain["background_houses"])
    assert focus | bg == set(range(1, 13))
    assert not focus & bg
