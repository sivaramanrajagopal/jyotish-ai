"""Significator connection: Lagna lord ↔ relevant house lord."""

from __future__ import annotations

from agents.transit_score_agent import _planet_aspects
from agents.prashna.dignity_engine import planetary_dignity


def _connection_strength(lagna_lord: str, matter_lord: str, chart: dict) -> tuple[str, str]:
    ll = chart["planet_positions"][lagna_lord]
    ml = chart["planet_positions"][matter_lord]

    if ll["sign"] == ml["sign"]:
        return "strong", f"{lagna_lord} and {matter_lord} conjoin in {ll['sign']} — strong querent–matter link."

    if ll["house"] == ml["house"]:
        return "strong", f"{lagna_lord} and {matter_lord} share house {ll['house']} — direct connection."

    ll_aspects = set(_planet_aspects(lagna_lord, ll["house"]))
    ml_aspects = set(_planet_aspects(matter_lord, ml["house"]))

    if ml["house"] in ll_aspects or ll["house"] in ml_aspects:
        return "moderate", (
            f"{lagna_lord} (H{ll['house']}) and {matter_lord} (H{ml['house']}) are linked by aspect — "
            "moderate connection between querent and the matter."
        )

    ll_dig = planetary_dignity(lagna_lord, ll["sign"])
    ml_dig = planetary_dignity(matter_lord, ml["sign"])
    if ll_dig["strength"] == "strong" and ml_dig["strength"] == "strong":
        return "moderate", (
            f"Both {lagna_lord} and {matter_lord} are dignified — indirect support despite no tight aspect."
        )

    return "weak", (
        f"Weak link between {lagna_lord} (H{ll['house']}) and {matter_lord} (H{ml['house']}) — "
        "the querent may be disconnected from the outcome."
    )


def analyze_significators(chart: dict, lagna_lord: str, matter_lord: str) -> dict:
    strength, explanation = _connection_strength(lagna_lord, matter_lord, chart)
    return {
        "lagna_lord": lagna_lord,
        "matter_lord": matter_lord,
        "connection": strength,
        "connection_label": {
            "strong": "Strong Connection",
            "moderate": "Moderate Connection",
            "weak": "Weak Connection",
        }.get(strength, "Moderate Connection"),
        "explanation": explanation,
    }


def significator_testimonies(sig: dict) -> list[dict]:
    polarity = {"strong": "positive", "moderate": "neutral", "weak": "negative"}[sig["connection"]]
    return [{
        "type": "significator",
        "category": "Significators",
        "polarity": polarity,
        "description": sig["explanation"],
    }]
