"""Chart facts for each house lord, as the classical rules need them.

Benefic and malefic follow BPHS here and only here; other tabs keep their own lists.
- Jupiter and Venus are benefics.
- The Moon is a benefic when waxing (Shukla paksha) and a malefic when waning.
- Mercury is a benefic unless it shares a sign with a malefic.
- Sun, Mars, Saturn, Rahu and Ketu are malefics.

Conjunction is sharing a sign. Aspects are whole-sign graha drishti from
_planet_aspects (7th for all; Mars 4/8, Jupiter 5/9, Saturn 3/10, Rahu/Ketu 3/11).
"""

from __future__ import annotations

from agents.bhavat_bhavam.core import PLANETS, lord_of_house, sign_of_house, whole_sign_house
from agents.dosha_radar.afflictions import check_combustion
from agents.prashna.dignity_engine import planetary_state
from agents.transit_score_agent import _planet_aspects

ALWAYS_BENEFIC = frozenset({"Jupiter", "Venus"})
ALWAYS_MALEFIC = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})

# BPHS 24.147-148: full strength gives the full result, half gives half, weak gives a quarter.
# Read from Shadbala: at or above the required minimum is full; within 80% of it is half.
HALF_STRENGTH_RATIO = 0.8


def moon_is_waxing(positions: dict) -> bool:
    sun = positions.get("Sun", {}).get("longitude")
    moon = positions.get("Moon", {}).get("longitude")
    if sun is None or moon is None:
        return True
    return (float(moon) - float(sun)) % 360 < 180


def planet_natures(positions: dict) -> dict[str, str]:
    """'benefic' or 'malefic' for each of the nine planets in this chart."""
    natures = {p: "malefic" for p in ALWAYS_MALEFIC}
    natures.update({p: "benefic" for p in ALWAYS_BENEFIC})
    natures["Moon"] = "benefic" if moon_is_waxing(positions) else "malefic"
    mercury_sign = positions.get("Mercury", {}).get("sign_index")
    joined_by_malefic = any(
        natures[p] == "malefic" and positions.get(p, {}).get("sign_index") == mercury_sign
        for p in PLANETS
        if p != "Mercury"
    )
    natures["Mercury"] = "malefic" if joined_by_malefic else "benefic"
    return natures


def strength_label(shadbala: dict | None, planet: str) -> str | None:
    if not shadbala:
        return None
    row = next((r for r in shadbala.get("planets", []) if r.get("planet") == planet), None)
    if not row or row.get("ratio") is None:
        return None
    ratio = float(row["ratio"])
    if ratio >= 1.0:
        return "full"
    if ratio >= HALF_STRENGTH_RATIO:
        return "half"
    return "quarter"


def _house_of(positions: dict, planet: str, asc_index: int) -> int | None:
    idx = positions.get(planet, {}).get("sign_index")
    return None if idx is None else whole_sign_house(idx, asc_index)


def lord_facts(chart: dict, shadbala: dict | None = None) -> list[dict]:
    """One fact row per house: its lord, where the lord sits, and what touches the lord."""
    positions = chart.get("planet_positions") or {}
    asc_index = int((chart.get("ascendant") or {})["sign_index"])
    natures = planet_natures(positions)
    houses = {p: _house_of(positions, p, asc_index) for p in PLANETS}
    sun_lon = positions.get("Sun", {}).get("longitude")

    rows = []
    for house in range(1, 13):
        lord = lord_of_house(asc_index, house)
        pdata = positions.get(lord) or {}
        lord_house = houses.get(lord)
        if lord_house is None:
            continue
        joined = [p for p in PLANETS if p != lord and houses.get(p) == lord_house]
        aspected_by = [
            p for p in PLANETS
            if p != lord and houses.get(p) is not None and lord_house in _planet_aspects(p, houses[p])
        ]
        dignity, _ = planetary_state(lord, pdata.get("sign", ""), pdata.get("degree_in_sign"))
        combust = False
        if sun_lon is not None and pdata.get("longitude") is not None:
            combust = check_combustion(
                float(sun_lon), float(pdata["longitude"]), lord, bool(pdata.get("retrograde")),
            )["combust"]

        strength = strength_label(shadbala, lord)
        benefic_joined = [p for p in joined if natures[p] == "benefic"]
        malefic_joined = [p for p in joined if natures[p] == "malefic"]
        benefic_aspects = [p for p in aspected_by if natures[p] == "benefic"]
        malefic_aspects = [p for p in aspected_by if natures[p] == "malefic"]
        rows.append({
            "house": house,
            "house_sign": sign_of_house(asc_index, house),
            "lord": lord,
            "lord_house": lord_house,
            "lord_sign": pdata.get("sign"),
            "lord_nature": natures[lord],
            "dignity": dignity,
            "retrograde": bool(pdata.get("retrograde")),
            "combust": combust,
            "joined_by": joined,
            "aspected_by": aspected_by,
            "benefic_joined": benefic_joined,
            "malefic_joined": malefic_joined,
            "benefic_aspects": benefic_aspects,
            "malefic_aspects": malefic_aspects,
            "strength": strength,
            "checks": {
                "lord_nature": natures[lord],
                # None when Shadbala is unavailable, so strength-based variants fall back.
                "lord_strong": None if strength is None else strength == "full",
                "jupiter_conjunct": "Jupiter" in joined,
                "benefic_conjunct": bool(benefic_joined),
                "malefic_conjunct": bool(malefic_joined),
                "benefic_aspect": bool(benefic_aspects),
                "malefic_aspect": bool(malefic_aspects),
                "benefic_aspect_or_conjunct": bool(benefic_joined or benefic_aspects),
                "malefic_aspect_or_conjunct": bool(malefic_joined or malefic_aspects),
                "exalted_or_own": dignity in ("Exalted", "Own Sign"),
                "debilitated": dignity == "Debilitated",
            },
        })
    return rows
