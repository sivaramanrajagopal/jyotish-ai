"""Prashna horary analysis tests — uses real Swiss Ephemeris."""

from agents.prashna.analyzer import analyze_prashna
from agents.prashna.constants import CATEGORY_HOUSE
from agents.prashna.verdict_engine import compute_verdict


def test_category_house_mapping():
    assert CATEGORY_HOUSE["career"] == 10
    assert CATEGORY_HOUSE["marriage"] == 7
    assert CATEGORY_HOUSE["general"] == 11


def test_analyze_prashna_structure():
    result = analyze_prashna(
        question="Will I get the promotion this quarter?",
        category="career",
        timestamp_iso="2026-06-06T14:30:00",
        timezone="Asia/Kolkata",
        lat=13.0827,
        lon=80.2707,
        place="Chennai",
    )
    assert result["question"]["category"] == "career"
    assert result["chart"]["ascendant"]["sign"]
    assert result["verdict"]["result"] in {
        "likely_yes", "likely_no", "delayed", "obstructed", "unclear", "possible_delayed",
    }
    assert result["testimonies"]["counts"]["total"] >= 3
    assert result["interpretation"]["summary"]
    assert result["disclaimer"]
    assert "Moon" not in result["analysis"]["moon"]["moon_sign"]  # real sign name


def test_analyze_prashna_real_moon_sign():
    result = analyze_prashna(
        question="Is travel abroad favourable now?",
        category="travel",
        timestamp_iso="2026-06-06T12:00:00",
        timezone="Asia/Kolkata",
    )
    moon_sign = result["analysis"]["moon"]["moon_sign"]
    assert moon_sign in {
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    }


def test_verdict_likely_yes():
    testimonies = {
        "counts": {"positive": 5, "negative": 1, "neutral": 2, "total": 8},
        "positive": [], "negative": [], "neutral": [],
    }
    v = compute_verdict(testimonies, "supportive")
    assert v["result"] == "likely_yes"


def test_verdict_unclear():
    testimonies = {
        "counts": {"positive": 1, "negative": 0, "neutral": 1, "total": 2},
        "positive": [], "negative": [], "neutral": [],
    }
    v = compute_verdict(testimonies, "neutral")
    assert v["result"] == "unclear"
