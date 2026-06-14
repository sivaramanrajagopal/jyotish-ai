"""Lagna (Ascendant) analysis for Prashna."""

from __future__ import annotations

from agents.prashna.dignity_engine import planetary_dignity, strength_label


def analyze_lagna(chart: dict) -> dict:
    asc = chart["ascendant"]
    lord = asc["sign_lord"]
    lord_data = chart["planet_positions"][lord]

    dignity = planetary_dignity(lord, lord_data["sign"])
    strength = dignity["strength"]

    return {
        "ascendant_sign": asc["sign"],
        "lagna_lord": lord,
        "lagna_lord_sign": lord_data["sign"],
        "lagna_lord_house": lord_data["house"],
        "dignity": dignity["state"],
        "strength": strength,
        "strength_label": strength_label(strength),
        "explanation": (
            f"Lagna is {asc['sign']} with lord {lord} in {lord_data['sign']} "
            f"(house {lord_data['house']}). Dignity: {dignity['state']}. "
            f"{dignity['explanation']}"
        ),
    }


def lagna_testimonies(lagna: dict) -> list[dict]:
    out = []
    if lagna["strength"] == "strong":
        out.append({
            "type": "lagna",
            "category": "Lagna",
            "polarity": "positive",
            "description": f"Strong Lagna lord ({lagna['lagna_lord']}) — querent has capacity to pursue the matter.",
        })
    elif lagna["strength"] == "weak":
        out.append({
            "type": "lagna",
            "category": "Lagna",
            "polarity": "negative",
            "description": f"Weak Lagna lord ({lagna['lagna_lord']}) — querent may lack full control over the outcome.",
        })
    else:
        out.append({
            "type": "lagna",
            "category": "Lagna",
            "polarity": "neutral",
            "description": f"Moderate Lagna lord strength — mixed personal capacity indicated.",
        })
    return out
