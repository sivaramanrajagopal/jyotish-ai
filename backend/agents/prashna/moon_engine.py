"""Moon analysis — mandatory in Prashna."""

from __future__ import annotations

from agents.prashna.dignity_engine import planetary_dignity, strength_label
from agents.prashna.constants import DUSTHANA


def _house_relation(moon_house: int, relevant_house: int) -> str:
    diff = (relevant_house - moon_house) % 12
    if diff == 0:
        return "same_house"
    if diff in (3, 6, 9, 4, 8):
        return "supportive_angle"
    if moon_house in DUSTHANA or relevant_house in DUSTHANA:
        return "dusthana"
    return "neutral"


def analyze_moon(chart: dict, relevant_house: int) -> dict:
    moon = chart["planet_positions"]["Moon"]
    dignity = planetary_dignity("Moon", moon["sign"])
    relation = _house_relation(moon["house"], relevant_house)

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
        "dignity": dignity["state"],
        "strength": dignity["strength"],
        "strength_label": strength_label(dignity["strength"]),
        "relation_to_matter": relation,
        "outcome": outcome,
        "explanation": explanation,
    }


def moon_testimonies(moon: dict) -> list[dict]:
    polarity_map = {"supportive": "positive", "obstructive": "negative", "neutral": "neutral"}
    return [{
        "type": "moon",
        "category": "Moon",
        "polarity": polarity_map[moon["outcome"]],
        "description": moon["explanation"],
    }]
