"""Planets occupying the relevant Prashna house."""

from __future__ import annotations

from agents.prashna.constants import PLANET_OCCUPANT_POSITIVE, PLANET_OCCUPANT_CAUTION
from agents.prashna.dignity_engine import planetary_dignity


def analyze_occupants(chart: dict, house_num: int, occupants: list[str]) -> list[dict]:
    results = []
    for planet in occupants:
        data = chart["planet_positions"][planet]
        dignity = planetary_dignity(planet, data["sign"])
        positive = PLANET_OCCUPANT_POSITIVE.get(planet)
        caution = PLANET_OCCUPANT_CAUTION.get(planet)

        if planet in ("Jupiter", "Venus", "Mercury") and dignity["strength"] != "weak":
            polarity = "positive"
            desc = positive or f"{planet} in house {house_num} is generally supportive."
        elif planet in ("Saturn", "Mars", "Rahu", "Ketu"):
            polarity = "negative" if dignity["strength"] == "weak" else "neutral"
            desc = caution or f"{planet} in house {house_num} adds complexity."
        elif dignity["strength"] == "strong":
            polarity = "positive"
            desc = positive or f"{planet} is well-placed in house {house_num}."
        elif dignity["strength"] == "weak":
            polarity = "negative"
            desc = caution or f"{planet} is weakened in house {house_num}."
        else:
            polarity = "neutral"
            desc = f"{planet} occupies house {house_num} with mixed indications."

        results.append({
            "planet": planet,
            "house": house_num,
            "sign": data["sign"],
            "dignity": dignity["state"],
            "polarity": polarity,
            "description": desc,
            "category": "occupant",
        })
    return results
