"""Health D3 analysis tests."""

from agents.health.body_map import body_part_for_d3_house, drekkana_section
from agents.health.d3 import build_drekkana_from_natal, d1_to_d3_sign_index
from agents.health_agent import compute_health_analysis, health_context_for_narrator
from agents.natal_agent import calculate_natal_chart

CHENNAI = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}


def _chart():
    c = calculate_natal_chart(
        CHENNAI["dob"], CHENNAI["tob"],
        CHENNAI["lat"], CHENNAI["lon"], CHENNAI["tz"],
    )
    c["birth_data"] = {
        "dob": CHENNAI["dob"],
        "timezone": CHENNAI["tz"],
        "lat": CHENNAI["lat"],
        "lon": CHENNAI["lon"],
    }
    return c


def test_drekkana_section_boundaries():
    assert drekkana_section(5.0) == "first"
    assert drekkana_section(15.0) == "second"
    assert drekkana_section(25.0) == "third"


def test_d3_sign_decan_rules():
    assert d1_to_d3_sign_index(0, 5.0) == 0   # Aries 1st decan → Aries
    assert d1_to_d3_sign_index(0, 15.0) == 4  # Aries 2nd decan → Leo (5th)
    assert d1_to_d3_sign_index(0, 25.0) == 8  # Aries 3rd decan → Sag (9th)


def test_body_part_mapping_house1():
    part = body_part_for_d3_house(1, 5.0)
    assert part["en"] == "Head"
    assert part["ta"] == "தலை"


def test_drekkana_positions_shape():
    chart = _chart()
    asc, pos = build_drekkana_from_natal(chart)
    assert "sign_index" in asc
    assert "Sun" in pos
    assert "house" in pos["Sun"]
    assert "d1_degree_in_sign" in pos["Sun"]


def test_health_analysis_structure():
    out = compute_health_analysis(_chart())
    assert out["disclaimer"]["en"]
    assert out["disclaimer"]["ta"]
    assert out["drekkana_positions"]
    assert out["planet_rows"]
    assert out["body_regions"]
    assert out["warnings"] is not None
    assert out["summary"]["maha_dasa"]
    assert out["summary"]["bhukti"]


def test_health_narrator_context():
    ctx = health_context_for_narrator(_chart())
    assert "Health awareness" in ctx
    assert "DISCLAIMER" in ctx
    assert "D3" in ctx
