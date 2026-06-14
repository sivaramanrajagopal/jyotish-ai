"""Prashna engine enhancement tests."""

from agents.transit_score_agent import _planet_aspects
from agents.prashna.dignity_engine import planetary_dignity, planetary_state
from agents.prashna.significator_engine import _in_conjunction, CONJUNCTION_ORB
from agents.prashna.moon_engine import moon_nakshatra_testimonies
from agents.prashna.analyzer import analyze_prashna


def test_rahu_ketu_drishti():
    asp = _planet_aspects("Rahu", 1)
    assert 3 in asp
    assert 7 in asp
    assert 11 in asp
    asp_k = _planet_aspects("Ketu", 10)
    assert 12 in asp_k  # 3rd from 10
    assert 4 in asp_k   # 7th from 10
    assert 8 in asp_k   # 11th from 10 ( (10+11-2)%12+1 = 8 )


def test_degree_dignity_deep_exaltation():
    state, deep = planetary_state("Sun", "Aries", 10.0)
    assert state == "Exalted"
    assert deep is True


def test_degree_dignity_exalt_sign_not_deep():
    state, deep = planetary_state("Sun", "Aries", 25.0)
    assert state == "Exalted"
    assert deep is False


def test_planetary_dignity_english_signs():
    d = planetary_dignity("Sun", "Leo")
    assert d["state"] == "Own Sign"
    assert d["strength"] == "strong"


def test_conjunction_orb():
    chart = {
        "planet_positions": {
            "Mercury": {"longitude": 100.0, "sign": "Cancer", "house": 4},
            "Sun": {"longitude": 105.0, "sign": "Cancer", "house": 4},
        }
    }
    assert _in_conjunction(chart, "Mercury", "Sun") is True
    chart["planet_positions"]["Sun"]["longitude"] = 120.0
    assert _in_conjunction(chart, "Mercury", "Sun") is False


def test_moon_nakshatra_testimony_friend():
    moon = {
        "moon_nakshatra": "Pushya",
        "moon_nakshatra_lord": "Saturn",
        "matter_lord": "Mercury",
    }
    items = moon_nakshatra_testimonies(moon)
    assert len(items) == 1
    assert items[0]["type"] == "moon_nakshatra"


def test_analyze_prashna_has_calculation_audit():
    result = analyze_prashna(
        question="Will I get the promotion?",
        category="career",
        question_id="promotion",
        timestamp_iso="2026-06-06T14:30:00",
        timezone="Asia/Kolkata",
    )
    audit = result.get("calculation_audit")
    assert audit is not None
    assert audit["question"]["text"]
    assert audit["moment"]["timestamp_iso"]
    assert audit["lagna"]["lagna_lord"]
    assert audit["matter_house"]["house_num"] == 10
    assert audit["significators"]["querent_lord"]
    assert audit["significators"]["quesited_lord"]
    assert len(audit["planets"]) >= 9
    assert audit["verdict_logic"]["label"]
    assert audit["method"]["engine"] == "Parashara rule-based Prashna"
    assert len(audit["significators"]["checks"]) >= 1


def test_analyze_prashna_has_meta():
    result = analyze_prashna(
        question="Will I get the promotion?",
        category="career",
        question_id="promotion",
        timestamp_iso="2026-06-06T14:30:00",
        timezone="Asia/Kolkata",
    )
    assert result["meta"]["engine"] == "rule_based"
    assert result["meta"]["uses_degrees"] is True
    assert "moon_nakshatra" in result["analysis"]["moon"]


def test_same_lagna_matter_lord_significator():
    result = analyze_prashna(
        question="Will I get the promotion?",
        category="career",
        question_id="promotion",
        timestamp_iso="2026-06-06T14:30:00",
        timezone="Asia/Kolkata",
    )
    sig = result["analysis"]["significators"]
    assert "conjoin" not in sig["explanation"].lower() or sig["lagna_lord"] != sig["matter_lord"]
