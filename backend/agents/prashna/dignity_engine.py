"""Dignity and strength evaluation for Prashna."""

from __future__ import annotations

from agents.transit_score_agent import _planetary_state, _dignity_score
from agents.prashna.constants import DIGNITY_STRENGTH


def planetary_dignity(planet: str, sign: str) -> dict:
    state = _planetary_state(planet, sign)
    strength = DIGNITY_STRENGTH.get(state, "neutral")
    score = _dignity_score(state)
    explanations = {
        "Exalted": f"{planet} is exalted in {sign} — strong natural expression.",
        "Own Sign": f"{planet} is in own sign {sign} — stable and empowered.",
        "Friend": f"{planet} is in a friendly sign ({sign}) — moderately supportive.",
        "Neutral": f"{planet} is in neutral dignity in {sign}.",
        "Enemy": f"{planet} is in an enemy sign ({sign}) — some friction indicated.",
        "Debilitated": f"{planet} is debilitated in {sign} — weakened expression.",
        "N/A": f"{planet} dignity not evaluated in {sign}.",
    }
    return {
        "planet": planet,
        "sign": sign,
        "state": state,
        "strength": strength,
        "score": score,
        "explanation": explanations.get(state, ""),
    }


def strength_label(strength: str) -> str:
    return {"strong": "Strong", "neutral": "Neutral", "weak": "Weak"}.get(strength, "Neutral")
