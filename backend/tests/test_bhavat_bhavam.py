"""Bhavat Bhavam tests."""

from agents.bhavat_bhavam.core import bhavat_bhavam_house, evaluate_link
from agents.bhavat_bhavam_agent import (
    bhavat_bhavam_context_for_narrator,
    compute_bhavat_bhavam,
)
from agents.health_agent import compute_health_analysis
from agents.career_agent import compute_career_prediction
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


def test_bhavat_bhavam_mapping():
    assert bhavat_bhavam_house(6) == 11
    assert bhavat_bhavam_house(8) == 3
    assert bhavat_bhavam_house(10) == 7
    assert bhavat_bhavam_house(12) == 11
    assert bhavat_bhavam_house(2) == 3


def test_sivaraman_health_6_to_11():
    chart = _chart()
    asc = chart["ascendant"]["sign_index"]
    link = evaluate_link(
        6,
        asc_sign_index=asc,
        planet_positions=chart["planet_positions"],
        maha="Moon",
        bhukti="Ketu",
        slice_kind="health",
    )
    assert link["bb_house"] == 11
    assert link["primary_active"] is True
    assert "Jupiter" in link["primary_planets"]
    assert link["primary_lord"] == "Moon"


def test_compute_bhavat_bhavam_shape():
    out = compute_bhavat_bhavam(_chart())
    assert out["health"]["slice"] == "health"
    assert out["career"]["slice"] == "career"
    assert out["health"]["active_count"] >= 2
    assert out["career"]["active_count"] >= 1


def test_health_response_includes_bhavam():
    out = compute_health_analysis(_chart())
    bb = out["bhavat_bhavam"]
    assert bb["slice"] == "health"
    assert any(lk["primary_house"] == 6 for lk in bb["links"])


def test_career_response_includes_bhavam():
    out = compute_career_prediction(_chart())
    bb = out["bhavat_bhavam"]
    assert bb["slice"] == "career"
    assert any(lk["primary_house"] == 10 for lk in bb["links"])


def test_narrator_context():
    ctx = bhavat_bhavam_context_for_narrator(_chart())
    assert "Bhavat Bhavam" in ctx
    assert "H6" in ctx or "H6→H11" in ctx or "→H11" in ctx
    assert "DISCLAIMER" in ctx
