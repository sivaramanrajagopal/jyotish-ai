"""Drishti (aspects) to Prashna houses."""

from __future__ import annotations

from agents.transit_score_agent import _planet_aspects
from agents.prashna.constants import PLANET_ASPECT_SUPPORT, PLANET_ASPECT_CHALLENGE


SUPPORTIVE_PLANETS = {"Jupiter", "Venus", "Mercury", "Moon"}
CHALLENGING_PLANETS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}


def aspects_to_house(chart: dict, target_house: int) -> list[dict]:
    """Planets directly aspecting target_house from their placement."""
    results = []
    for planet, data in chart["planet_positions"].items():
        from_house = data["house"]
        aspected = _planet_aspects(planet, from_house)
        if target_house not in aspected:
            continue
        if planet in SUPPORTIVE_PLANETS:
            polarity = "positive"
            desc = PLANET_ASPECT_SUPPORT.get(
                planet,
                f"{planet} aspects house {target_house} — potentially supportive.",
            )
        elif planet in {"Saturn", "Mars"}:
            polarity = "negative"
            desc = PLANET_ASPECT_CHALLENGE.get(
                planet,
                f"{planet} aspects house {target_house} — caution indicated.",
            )
        elif planet in {"Rahu", "Ketu"}:
            polarity = "neutral"
            desc = PLANET_ASPECT_CHALLENGE.get(
                planet,
                f"{planet} influences house {target_house} — unconventional effects possible.",
            )
        else:
            polarity = "neutral"
            desc = f"{planet} aspects house {target_house} — mixed influence."

        results.append({
            "planet": planet,
            "from_house": from_house,
            "target_house": target_house,
            "polarity": polarity,
            "description": desc,
            "category": "aspect",
        })
    return results
