"""Relevant house analysis for Prashna category."""

from __future__ import annotations

from agents.prashna.chart_engine import house_sign, house_lord, planets_in_house
from agents.prashna.dignity_engine import planetary_dignity, strength_label


def analyze_relevant_house(chart: dict, house_num: int, category_label: str) -> dict:
    sign = house_sign(chart, house_num)
    lord = house_lord(chart, house_num)
    lord_data = chart["planet_positions"][lord]
    occupants = planets_in_house(chart, house_num)
    dignity = planetary_dignity(lord, lord_data["sign"], lord_data.get("degree_in_sign"))

    return {
        "house_num": house_num,
        "category_label": category_label,
        "house_sign": sign,
        "house_lord": lord,
        "house_lord_sign": lord_data["sign"],
        "house_lord_house": lord_data["house"],
        "occupants": occupants,
        "lord_dignity": dignity["state"],
        "lord_strength": dignity["strength"],
        "lord_strength_label": strength_label(dignity["strength"]),
        "explanation": (
            f"For {category_label}, house {house_num} ({sign}) is examined. "
            f"Lord {lord} is in {lord_data['sign']} (H{lord_data['house']}), "
            f"dignity {dignity['state']}."
            + (f" Occupants: {', '.join(occupants)}." if occupants else " No planets occupy this house.")
        ),
    }


def house_lord_testimonies(house: dict) -> list[dict]:
    out = []
    if house["lord_strength"] == "strong":
        out.append({
            "type": "house_lord",
            "category": f"House {house['house_num']}",
            "polarity": "positive",
            "description": f"Strong {house['house_lord']} (lord of house {house['house_num']}) supports the matter.",
        })
    elif house["lord_strength"] == "weak":
        out.append({
            "type": "house_lord",
            "category": f"House {house['house_num']}",
            "polarity": "negative",
            "description": f"Weakened {house['house_lord']} may hinder fulfilment of the question.",
        })
    return out
