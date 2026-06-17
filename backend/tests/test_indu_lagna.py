"""Indu Lagna — canonical fixture and reference parity tests."""

import datetime

from agents.indu_lagna_agent import (
    calculate_indu_lagna_index,
    compute_indu_lagna,
)
from agents.natal_agent import calculate_natal_chart

CHENNAI_1978 = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}


def _chennai_chart() -> dict:
    chart = calculate_natal_chart(
        CHENNAI_1978["dob"],
        CHENNAI_1978["tob"],
        CHENNAI_1978["lat"],
        CHENNAI_1978["lon"],
        CHENNAI_1978["tz"],
    )
    chart["birth_data"] = {
        "dob": CHENNAI_1978["dob"],
        "timezone": CHENNAI_1978["tz"],
    }
    return chart


def test_indu_lagna_index_canonical():
    assert calculate_indu_lagna_index(10, 11) == 4


def test_indu_lagna_natal_canonical():
    out = compute_indu_lagna(_chennai_chart(), transit_years=2)
    il = out["indu_lagna"]
    assert il["name"] == "Simha"
    assert il["english"] == "Leo"
    assert il["lord"] == "Sun"
    assert il["house_from_lagna"] == 7
    assert sorted(out["fortune_planets"]) == ["Mercury", "Saturn", "Sun"]
    natal_names = sorted(p["planet"] for p in out["natal"]["planets_in_indu_lagna"])
    assert natal_names == ["Mercury", "Saturn"]


def test_natal_judgment_canonical():
    out = compute_indu_lagna(_chennai_chart(), transit_years=2)
    j = out["natal_judgment"]
    assert j["verdict"] in ("supportive", "mixed", "challenging")
    assert j["lord"]["planet"] == "Sun"
    assert j["lord"]["dignity"] in {
        "Exalted", "Own Sign", "Friend", "Neutral", "Enemy", "Debilitated", "N/A",
    }
    occ_planets = {o["planet"] for o in j["occupants"]}
    assert occ_planets == {"Mercury", "Saturn"}
    saturn = next(o for o in j["occupants"] if o["planet"] == "Saturn")
    assert saturn["tone"] == "mixed"
    assert "Lagna lord" in saturn["note"]
    assert j["lagna_lord"] == "Saturn"
    assert out["summary"]["natal_verdict"] == j["verdict"]


def test_dasa_bhukti_matches_standard_vimshottari():
    """Fortune Dasa/Bhukti uses dasha_core (same as Dasha Roadmap)."""
    from dasha_core import generate_dashas, generate_bhuktis

    chart = _chennai_chart()
    moon_lon = chart["planet_positions"]["Moon"]["longitude"]
    fortune = {"Sun", "Mercury", "Saturn"}

    out = compute_indu_lagna(chart, transit_years=1)
    timeline = out["dasa_bhukti_periods"]
    assert len(timeline) == 36
    assert timeline[0] == {
        "maha_dasa": "Mercury",
        "bukti": "Mercury",
        "start": "1978-09-18",
        "end": "1979-10-09",
        "activation_tier": "primary",
        "label": "Mercury–Mercury Dasa/Bhukti",
    }

    # Cross-check a few windows against dasha_core directly
    expected: list[dict] = []
    birth_dt = datetime.datetime(1978, 9, 18)
    cutoff = birth_dt + datetime.timedelta(days=90 * 365.25)
    for dasa in generate_dashas(moon_lon, "1978-09-18"):
        if dasa["start"] >= cutoff:
            break
        for b in generate_bhuktis(dasa):
            if b["end"] <= birth_dt or b["start"] >= cutoff:
                continue
            if dasa["planet"] in fortune or b["planet"] in fortune:
                expected.append({
                    "maha_dasa": dasa["planet"],
                    "bukti": b["planet"],
                    "start": b["start"].strftime("%Y-%m-%d"),
                    "end": b["end"].strftime("%Y-%m-%d"),
                })
    assert [(p["maha_dasa"], p["bukti"], p["start"], p["end"]) for p in timeline] == [
        (e["maha_dasa"], e["bukti"], e["start"], e["end"]) for e in expected
    ]

    moon_mercury = next(
        p for p in timeline if p["maha_dasa"] == "Moon" and p["bukti"] == "Mercury"
    )
    assert moon_mercury == {
        "maha_dasa": "Moon",
        "bukti": "Mercury",
        "start": "2025-01-06",
        "end": "2026-06-08",
        "activation_tier": "primary",
        "label": "Moon–Mercury Dasa/Bhukti",
    }


def test_tiered_transits_structure():
    out = compute_indu_lagna(_chennai_chart(), transit_years=3)
    for t in out["slow_transits"]:
        assert t["planet"] in {"Jupiter", "Saturn"}
        assert t["activation_tier"] == "secondary"
        assert t["target"] in {"Indu Lagna", "Indu lord (Sun) sign"}
    for t in out["fast_transits"]:
        assert t["planet"] in {"Sun", "Mercury", "Moon"}
        assert t["activation_tier"] == "minor"
    assert out["transit_periods"] == out["slow_transits"] + out["fast_transits"]


def test_hero_block_present():
    out = compute_indu_lagna(_chennai_chart(), transit_years=3)
    assert "headline" in out["hero"]
    assert out["hero"]["natal_promise"] in ("Supportive", "Mixed", "Challenging")
    assert out["interpretation"]["disclaimer"]


def test_narrator_context_includes_judgment():
    from agents.indu_lagna_agent import indu_context_for_narrator

    ctx = indu_context_for_narrator(_chennai_chart())
    assert "Natal promise" in ctx
    assert "Indu Lagna" in ctx
    assert "stability" in ctx.lower()
