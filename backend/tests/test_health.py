"""Health D3 analysis tests."""

from agents.health.body_map import BODY_PARTS, body_part_for_house, drekkana_section
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
    assert drekkana_section(10.0) == "second"
    assert drekkana_section(20.0) == "third"


def test_d3_sign_decan_rules():
    assert d1_to_d3_sign_index(0, 5.0) == 0   # Aries 1st decan → Aries
    assert d1_to_d3_sign_index(0, 15.0) == 4  # Aries 2nd decan → Leo (5th)
    assert d1_to_d3_sign_index(0, 25.0) == 8  # Aries 3rd decan → Sag (9th)


def test_body_part_mapping_house1():
    part = body_part_for_house(1, 5.0)
    assert part["en"] == "Head"
    assert part["ta"] == "தலை"


def test_body_map_follows_classical_order():
    # Brihat Jataka 5.25, houses 1, 2, 3, 4, 5, 6, 7 per decan (right side for 2–6).
    def column(section):
        return [BODY_PARTS[h][section]["en"] for h in range(1, 8)]

    assert column("first") == [
        "Head", "Right eye", "Right ear", "Right nostril", "Right cheek", "Right jaw", "Mouth",
    ]
    assert column("second") == [
        "Neck", "Right shoulder", "Right arm", "Right flank", "Right heart region",
        "Right belly", "Navel",
    ]
    assert column("third") == [
        "Bladder / lower pelvis", "Right genitals / anus", "Right testicle", "Right thigh",
        "Right knee", "Right calf", "Feet",
    ]
    # Houses 2–6 are the right side, 8–12 the mirrored left side.
    for h in range(2, 7):
        for s in ("first", "second", "third"):
            right, left = BODY_PARTS[h][s]["en"], BODY_PARTS[14 - h][s]["en"]
            assert right.startswith("Right") and left == right.replace("Right", "Left")


def test_lagna_body_uses_lagna_decan():
    chart = _chart()
    deg = float(chart["ascendant"]["degree_in_sign"])
    expected = {"first": "Head", "second": "Neck", "third": "Bladder / lower pelvis"}[drekkana_section(deg)]
    assert compute_health_analysis(chart)["summary"]["lagna_body_en"] == expected


def test_rising_decan_sets_section_for_every_house():
    chart = _chart()
    out = compute_health_analysis(chart)
    lagna_section = drekkana_section(float(chart["ascendant"]["degree_in_sign"]))
    assert {r["drekkana_section"] for r in out["planet_rows"]} == {lagna_section}
    for row in out["planet_rows"]:
        assert row["body_part_en"] == BODY_PARTS[row["d1_house"]][lagna_section]["en"]


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
    assert out["factor_groups"]["d3_natal"] is not None
    assert out["transit_today"]
    assert out["summary"]["maha_dasa"]
    assert out["summary"]["bhukti"]
    assert out["summary"]["transit_date"]
    assert all("house_d1" in t for t in out["transit_today"])
    assert all("house_d3" in t for t in out["transit_today"])
    top = out["body_regions"][0]
    assert top.get("rationale_en")
    assert out["summary"].get("focus_rationale_en")


def test_health_narrator_context():
    ctx = health_context_for_narrator(_chart())
    assert "Health awareness" in ctx
    assert "DISCLAIMER" in ctx
    assert "D3" in ctx
