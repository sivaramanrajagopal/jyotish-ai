"""House Connections — canonical fixture tests."""

from agents.house_connections_agent import (
    compute_house_connections,
    house_connections_context_for_narrator,
)
from agents.house_connections.core import analyze_all_houses, houses_from_own, position_type_from_own
from agents.house_connections.yogas import detect_yogas
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


def test_houses_from_own_same_house():
    assert houses_from_own(5, 5) == 12


def test_houses_from_own_11th_lord_in_6th_is_8th_dusthana():
    """H11 lord in H6 = 8th from own (not 7th kendra)."""
    assert houses_from_own(11, 6) == 8
    assert position_type_from_own(8) == "dusthana_from_own"


def test_analyze_all_houses_shape():
    houses = analyze_all_houses(_chart())
    assert len(houses) == 12
    assert houses[1]["lord"]
    assert houses[10]["theme_en"] == "Career & status"
    assert "strength" in houses[7]


def test_house_connections_full_structure():
    out = compute_house_connections(_chart())
    assert out["disclaimer"]["en"]
    assert len(out["houses"]) == 12
    assert len(out["edges"]) > 0
    assert len(out["predictions"]) == 12
    assert out["graph"]["nodes"]
    assert out["summary"]["maha_dasa"]


def test_predictions_have_blessers():
    out = compute_house_connections(_chart())
    for pred in out["predictions"]:
        assert pred["structure"]["lord"]
        assert "inference_en" in pred
        assert pred["house"] >= 1


def test_yogas_detected():
    houses = analyze_all_houses(_chart())
    yogas = detect_yogas(houses, _chart())
    assert isinstance(yogas, list)


def test_narrator_context():
    ctx = house_connections_context_for_narrator(_chart())
    assert "HOUSE CONNECTIONS" in ctx
    assert "H10" in ctx or "Career" in ctx
