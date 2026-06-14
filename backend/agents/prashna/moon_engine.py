"""Moon analysis — mandatory in Prashna."""

from __future__ import annotations

from agents.prashna.dignity_engine import planetary_dignity, strength_label
from agents.prashna.constants import DUSTHANA, SIGN_LORDS

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


def _house_relation(moon_house: int, relevant_house: int) -> str:
    diff = (relevant_house - moon_house) % 12
    if diff == 0:
        return "same_house"
    if diff in (3, 6, 9, 4, 8):
        return "supportive_angle"
    if moon_house in DUSTHANA or relevant_house in DUSTHANA:
        return "dusthana"
    return "neutral"


def _nakshatra_lord(nakshatra: str) -> str:
    try:
        idx = NAKSHATRAS.index(nakshatra)
        return NAKSHATRA_LORDS[idx]
    except ValueError:
        return ""


def analyze_moon(chart: dict, relevant_house: int) -> dict:
    moon = chart["planet_positions"]["Moon"]
    dignity = planetary_dignity("Moon", moon["sign"], moon.get("degree_in_sign"))
    relation = _house_relation(moon["house"], relevant_house)
    nak = moon.get("nakshatra", "")
    nak_lord = _nakshatra_lord(nak)
    matter_lord = SIGN_LORDS.get(
        chart["house_signs"][relevant_house - 1], ""
    )

    if dignity["strength"] == "strong" and relation in ("same_house", "supportive_angle"):
        outcome = "supportive"
        explanation = (
            f"Moon is strong in {moon['sign']} (H{moon['house']}) and well-connected to "
            f"the matter-house (H{relevant_house}) — emotional and circumstantial flow favours the question."
        )
    elif dignity["strength"] == "weak" or relation == "dusthana":
        outcome = "obstructive"
        explanation = (
            f"Moon in {moon['sign']} (H{moon['house']}) shows friction relative to house {relevant_house}. "
            f"Mind or circumstances may obstruct smooth fulfilment."
        )
    else:
        outcome = "neutral"
        explanation = (
            f"Moon in {moon['sign']} (H{moon['house']}) is moderately placed for house {relevant_house} matters."
        )

    return {
        "moon_sign": moon["sign"],
        "moon_house": moon["house"],
        "moon_nakshatra": nak,
        "moon_nakshatra_lord": nak_lord,
        "moon_pada": moon.get("pada"),
        "dignity": dignity["state"],
        "strength": dignity["strength"],
        "strength_label": strength_label(dignity["strength"]),
        "relation_to_matter": relation,
        "matter_lord": matter_lord,
        "outcome": outcome,
        "explanation": explanation,
    }


def moon_testimonies(moon: dict) -> list[dict]:
    polarity_map = {"supportive": "positive", "obstructive": "negative", "neutral": "neutral"}
    out = [{
        "type": "moon",
        "category": "Moon",
        "polarity": polarity_map[moon["outcome"]],
        "description": moon["explanation"],
    }]
    out.extend(moon_nakshatra_testimonies(moon))
    return out


def moon_nakshatra_testimonies(moon: dict) -> list[dict]:
    """Moon nakshatra lord's relation to matter-house lord — classical Prashna check."""
    nak_lord = moon.get("moon_nakshatra_lord", "")
    matter_lord = moon.get("matter_lord", "")
    nak = moon.get("moon_nakshatra", "")

    if not nak_lord or not matter_lord or not nak:
        return []

    if nak_lord == matter_lord:
        return [{
            "type": "moon_nakshatra",
            "category": "Moon Nakshatra",
            "polarity": "positive",
            "description": (
                f"Moon in {nak} (lord {nak_lord}) aligns with matter-lord {matter_lord} — "
                "circumstances favour the question."
            ),
        }]

    from agents.prashna.dignity_engine import FRIENDSHIPS
    rel = FRIENDSHIPS.get(nak_lord, {})
    if matter_lord in rel.get("friends", []):
        return [{
            "type": "moon_nakshatra",
            "category": "Moon Nakshatra",
            "polarity": "positive",
            "description": (
                f"Moon nakshatra lord {nak_lord} ({nak}) is friendly to matter-lord {matter_lord} — supportive flow."
            ),
        }]
    if matter_lord in rel.get("enemies", []):
        return [{
            "type": "moon_nakshatra",
            "category": "Moon Nakshatra",
            "polarity": "negative",
            "description": (
                f"Moon nakshatra lord {nak_lord} ({nak}) is inimical to matter-lord {matter_lord} — friction indicated."
            ),
        }]

    return [{
        "type": "moon_nakshatra",
        "category": "Moon Nakshatra",
        "polarity": "neutral",
        "description": (
            f"Moon in {nak} (lord {nak_lord}) has neutral relation to matter-lord {matter_lord}."
        ),
    }]
