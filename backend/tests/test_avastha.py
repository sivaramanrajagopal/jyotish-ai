"""Unit tests for Sthula / Sukshma Avastha scoring (soft-penalty model)."""

from __future__ import annotations

import math

from agents.avastha.remedies import (
    get_remedies_for_planet,
    is_functional_benefic,
)
from agents.avastha.calc import (
    STHULA_CAPACITY,
    SUKSHMA_EFFICIENCY,
    apply_capacity_penalties,
    average_pair,
    classify_manifestation,
    evaluate_dasa_bhukti_synergy,
    eval_sthula_avastha,
    eval_sukshma_avastha,
    manifestation_index,
    score_planet,
)
from agents.avastha_agent import (
    birth_nazhikai_after_sunrise,
    classify_sign_dignity,
    compute_avastha_analysis,
)
from agents.natal_agent import calculate_natal_chart


def test_sthula_combust_hard_override():
    name, reason, athi, retro = eval_sthula_avastha(
        sign_dignity="Exalted",
        is_retrograde=False,
        is_combust=True,
        is_accelerated=True,
        degree_in_rasi=10.0,
    )
    assert name == "Vikala"
    assert athi == 0.0 and retro == 0.0
    assert "Combust" in reason


def test_sthula_soft_athi_preserves_exaltation():
    name, reason, athi, retro = eval_sthula_avastha(
        sign_dignity="Exalted",
        is_retrograde=False,
        is_combust=False,
        is_accelerated=True,
        degree_in_rasi=8.0,
        planet_name="Jupiter",
    )
    assert name == "Deepta"
    assert athi == 15.0
    assert retro == 0.0
    assert "Athi Vega" in reason


def test_sthula_retro_strong_dignity_keeps_label():
    name, reason, athi, retro = eval_sthula_avastha(
        sign_dignity="Own",
        is_retrograde=True,
        is_combust=False,
        is_accelerated=False,
        degree_in_rasi=10.0,
        planet_name="Venus",
    )
    assert name == "Sthamitha"
    assert retro == 10.0


def test_sthula_retro_weak_dignity_sakta():
    name, _, athi, retro = eval_sthula_avastha(
        sign_dignity="Friendly",
        is_retrograde=True,
        is_combust=False,
        is_accelerated=False,
        degree_in_rasi=10.0,
        planet_name="Mars",
    )
    assert name == "Sakta"
    assert retro == 0.0  # encoded in Sakta capacity


def test_sthula_nodes_skip_retro_penalty():
    name, reason, athi, retro = eval_sthula_avastha(
        sign_dignity="Neutral",
        is_retrograde=True,
        is_combust=False,
        is_accelerated=False,
        degree_in_rasi=3.0,
        planet_name="Rahu",
    )
    assert name == "Heenasakstha"
    assert retro == 0.0
    assert "Retrograde" not in reason


def test_sthula_last_degree_and_debilitated():
    assert eval_sthula_avastha(
        sign_dignity="Debilitated", is_retrograde=True, is_combust=False,
        is_accelerated=False, degree_in_rasi=29.5, planet_name="Sun",
    )[0] == "Kala"
    assert eval_sthula_avastha(
        sign_dignity="Own", is_retrograde=False, is_combust=False,
        is_accelerated=False, degree_in_rasi=29.0, planet_name="Sun",
    )[0] == "Peethya"


def test_capacity_penalties_floor():
    assert apply_capacity_penalties(90, 15, 10) == 65
    assert apply_capacity_penalties(20, 15, 10) == 15  # floor


def test_sukshma_known_remainder():
    name, br = eval_sukshma_avastha(
        planet_index=1,
        nakshatra_index=1,
        degree_in_rasi=10.0,
        janma_nakshatra_index=5,
        lagna_rasi_index=3,
        birth_nazhikai_after_sunrise=2.0,
    )
    assert br["step1"] == 1
    assert br["step2"] == 10
    assert br["step3"] == 20
    assert br["remainder"] == 8
    assert name == "Aagama"


def test_sukshma_remainder_zero_maps_to_nidra():
    name, br = eval_sukshma_avastha(
        planet_index=2,
        nakshatra_index=3,
        degree_in_rasi=2.0,
        janma_nakshatra_index=0,
        lagna_rasi_index=0,
        birth_nazhikai_after_sunrise=0.0,
    )
    assert br["remainder"] == 0
    assert br["avastha_index"] == 12
    assert name == "Nidra"


def test_manifestation_geometric_mean():
    assert manifestation_index(90, 80) == round(math.sqrt(90 * 80), 2)
    assert manifestation_index(60, 60) == 60.0
    assert average_pair(39.0, 60.0) == 49.5
    assert classify_manifestation(80) == "Immediate & High Manifestation"
    assert classify_manifestation(79.9) == "Conditional / Strategic Manifestation"


def test_score_planet_exalted_with_athi():
    row = score_planet(
        planet_name="Jupiter",
        planet_index=5,
        rasi_index=4,
        nakshatra_index=8,
        degree_in_rasi=8.845,
        is_retrograde=False,
        is_combust=False,
        is_accelerated=True,
        sign_dignity="Exalted",
        janma_nakshatra_index=27,
        lagna_rasi_index=11,
        birth_nazhikai_after_sunrise=29.0507,
    )
    assert row["sthula"]["name"] == "Deepta"
    assert row["sthula"]["base_capacity"] == 90.0
    assert row["sthula"]["athi_vega_penalty"] == 15.0
    assert row["sthula"]["capacity"] == 75.0  # 90-15
    assert row["sukshma"]["name"] == "Nidra"
    assert row["manifestation"]["net"] == round(math.sqrt(75 * 15), 2)


def test_dasa_bhukti_uses_average():
    out = evaluate_dasa_bhukti_synergy("Moon", "Ketu", 40.0, 60.0)
    assert out["combinedScore"] == 50.0
    assert out["method"] == "average"
    assert out["manifestationClass"] == "Progressive Growth"


def test_capacity_keys_cover_all_sthula():
    for name in (
        "Deepta", "Sthamitha", "Muditha", "Santha", "Sakta", "Heenasakstha",
        "Deena", "Peethya", "Peeda", "Vikala", "Kala",
    ):
        assert name in STHULA_CAPACITY
        assert STHULA_CAPACITY[name] <= 90


def test_chennai_birth_is_29_naazhigai_3_vinazhigai():
    """18 Sep 1978, 17:35, Chennai. Counted from sunrise, 24 minutes and 24 seconds."""
    result = birth_nazhikai_after_sunrise("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    assert result["naazhigai"] == 29
    assert result["vinazhigai"] == 3
    assert result["nazhikai"] == 29.0507


def test_sign_dignity_labels():
    assert classify_sign_dignity("Sun", "Aries", 10.0) == "Exalted"
    assert classify_sign_dignity("Sun", "Leo", 10.0) == "Moolatrikona"
    assert classify_sign_dignity("Rahu", "Taurus", 5.0) == "Neutral"


def test_full_chart_chennai_native():
    chart = calculate_natal_chart(
        "1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata",
    )
    result = compute_avastha_analysis(chart)
    assert len(result["planets"]) == 9
    by = {p["planet"]: p for p in result["planets"]}

    # Jupiter exalted must NOT be crushed to Peeda
    assert by["Jupiter"]["sthula"]["name"] == "Deepta"
    assert by["Jupiter"]["sthula"]["athi_vega_penalty"] == 15.0
    assert by["Jupiter"]["manifestation"]["net"] > 20

    # Nodes: no retro wipe to Sakta
    assert by["Rahu"]["sthula"]["name"] == "Heenasakstha"
    assert by["Ketu"]["sthula"]["name"] == "Heenasakstha"
    assert by["Rahu"]["sthula"]["retro_penalty"] == 0.0

    # Venus own sign unchanged path
    assert by["Venus"]["sthula"]["name"] == "Sthamitha"

    assert result["dasa_bhukti"]["method"] == "average"
    for p in result["planets"]:
        assert 0 <= p["manifestation"]["net"] <= 100
        assert p["sthula"]["capacity"] >= 15
        assert p["sukshma"]["name"] in SUKSHMA_EFFICIENCY
        assert p["remedy"]["planet"] == p["planet"]
        assert p["remedy"]["branch"] in {
            "peak", "combust_weak", "afflicted", "dormant", "none",
        }


def test_functional_benefic_gem_gate():
    assert is_functional_benefic("Jupiter", 1) is True   # Aries: 9th
    assert is_functional_benefic("Sun", 1) is True       # Aries: 5th
    assert is_functional_benefic("Mars", 1) is False     # Aries: 1st + 8th
    assert is_functional_benefic("Saturn", 2) is True    # Taurus yogakaraka
    assert is_functional_benefic("Saturn", 3) is False   # Gemini: 8th + 9th
    assert is_functional_benefic("Jupiter", 5) is True   # Leo: 5th, natural benefic
    assert is_functional_benefic("Rahu", 1) is False
    assert is_functional_benefic("Ketu", 9) is False


def test_remedy_branches():
    peak = get_remedies_for_planet(
        "Venus", "Sthamitha", "Aagama", 80.0, functional_benefic=True,
    )
    assert peak["branch"] == "peak"
    assert peak["intervention"] is False
    assert peak["items"] == []

    combust = get_remedies_for_planet(
        "Mercury", "Vikala", "Nidra", 30.0, functional_benefic=True,
    )
    assert combust["branch"] == "combust_weak"
    assert [i["kind"] for i in combust["items"]] == ["mantra", "deity"]
    assert "Gemstone avoided" in combust["cautions"][0]

    kala = get_remedies_for_planet(
        "Sun", "Kala", "Sayana", 20.0, functional_benefic=True,
    )
    assert kala["branch"] == "combust_weak"
    assert "gem" not in [i["kind"] for i in kala["items"]]

    afflicted = get_remedies_for_planet(
        "Saturn", "Deena", "Nidra", 40.0, functional_benefic=True,
    )
    assert afflicted["branch"] == "afflicted"
    assert [i["kind"] for i in afflicted["items"]] == ["charity", "fast", "deity"]

    dormant_gem = get_remedies_for_planet(
        "Jupiter", "Deepta", "Sayana", 50.0, functional_benefic=True,
    )
    assert dormant_gem["branch"] == "dormant"
    assert [i["kind"] for i in dormant_gem["items"]] == ["mantra", "charity", "gem"]
    assert dormant_gem["items"][0]["detail"] == "108 times"

    dormant_no_gem = get_remedies_for_planet(
        "Saturn", "Santha", "Nidra", 40.0, functional_benefic=False,
    )
    assert dormant_no_gem["branch"] == "dormant"
    assert "gem" not in [i["kind"] for i in dormant_no_gem["items"]]
    assert "not a functional benefic" in dormant_no_gem["cautions"][0]

    quiet = get_remedies_for_planet(
        "Moon", "Santha", "Upaveshana", 60.0, functional_benefic=True,
    )
    assert quiet["branch"] == "none"
    assert quiet["intervention"] is False
