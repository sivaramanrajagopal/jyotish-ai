"""Core house analysis — lords, strength, position from own."""

from __future__ import annotations

from agents.bhavat_bhavam.core import (
    EXALTATION,
    OWN_SIGNS,
    lord_of_house,
    planets_in_house,
    sign_of_house,
    whole_sign_house,
    _lord_strength_tags,
    _lords_linked,
)
from agents.house_connections.themes import (
    BENEFICS,
    DUSTHANA,
    KENDRA,
    MALEFICS,
    POSITION_TYPE,
    TRIKONA,
    UPACHAYA,
)
from agents.natal_agent import NAKSHATRA_LORDS, NAKSHATRAS, SIGN_LORDS, SIGNS
from agents.transit_score_agent import _planet_aspects


def houses_from_own(house_num: int, lord_house: int) -> int:
    """Inclusive count from owned house (owned = 1st; lord in owned sign = 1)."""
    return ((lord_house - house_num) % 12) + 1


def position_type_from_own(hfo: int) -> str:
    if hfo == 1:
        return "own_house"
    if hfo in (4, 7, 10):
        return "kendra_from_own"
    if hfo in (5, 9):
        return "trikona_from_own"
    if hfo in (6, 8, 12):
        return "dusthana_from_own"
    if hfo in (3, 11):
        return "upachaya_from_own"
    return "neutral_from_own"


def _dignity(planet: str, sign: str) -> str:
    if planet in ("Rahu", "Ketu"):
        return "N/A"
    ex_idx, _ = EXALTATION.get(planet, (-1, 0))
    if ex_idx >= 0 and SIGNS[ex_idx] == sign:
        return "Exalted"
    if sign in OWN_SIGNS.get(planet, []):
        return "Own Sign"
    deb_map = {
        "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
        "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
    }
    if deb_map.get(planet) == sign:
        return "Debilitated"
    return "Neutral"


def _dignity_score(state: str) -> float:
    return {
        "Exalted": 100, "Own Sign": 90, "Friend": 70,
        "Neutral": 50, "Enemy": 30, "Debilitated": 10, "N/A": 50,
    }.get(state, 50)


def _house_strength(
    house_num: int,
    lord: str,
    lord_data: dict,
    hfo: int,
    planets_in: list[str],
    planets_asp: list[str],
    asc_sign_index: int,
    planet_positions: dict,
) -> float:
    pos_s = {
        1: 100, 4: 90, 7: 90, 10: 90,
        5: 95, 9: 95, 3: 75, 11: 75,
        2: 50, 6: 40, 8: 30, 12: 35,
    }
    lp = pos_s.get(hfo, 50)
    ld = _dignity_score(_dignity(lord, lord_data.get("sign", "")))

    ben = sum(1 for p in planets_in + planets_asp if p in BENEFICS)
    mal = sum(1 for p in planets_in + planets_asp if p in MALEFICS)
    bs = min(100, ben * 30)
    mp = min(50, mal * 12)

    hn = 60
    if house_num in KENDRA:
        hn = 85
    if house_num in TRIKONA:
        hn = 90
    if house_num in DUSTHANA:
        hn = 45
    if house_num in UPACHAYA:
        hn = max(hn, 75)

    tags = _lord_strength_tags(lord, planet_positions, asc_sign_index)
    tag_bonus = min(10, len(tags) * 3)

    return round(max(0, min(100, lp * 0.35 + ld * 0.25 + bs * 0.20 - mp * 0.15 + hn * 0.15 + tag_bonus)), 1)


def rag_status(score: float) -> dict:
    if score >= 70:
        return {"status": "strong", "emoji": "🟢", "label_en": "Strong", "label_ta": "வலிமை"}
    if score >= 45:
        return {"status": "moderate", "emoji": "🟡", "label_en": "Moderate", "label_ta": "மிதம்"}
    return {"status": "weak", "emoji": "🔴", "label_en": "Weak", "label_ta": "பலவீனம்"}


def nakshatra_lord_for(planet_data: dict) -> str:
    nak = planet_data.get("nakshatra") or ""
    if nak in NAKSHATRAS:
        return NAKSHATRA_LORDS[NAKSHATRAS.index(nak)]
    return ""


def houses_owned_by(planet: str, asc_sign_index: int) -> list[int]:
    owned: list[int] = []
    for h in range(1, 13):
        if lord_of_house(asc_sign_index, h) == planet:
            owned.append(h)
    return owned


def planets_aspecting_house(
    planet_positions: dict,
    asc_sign_index: int,
    house: int,
) -> list[str]:
    out: list[str] = []
    for planet, pdata in planet_positions.items():
        if planet not in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            continue
        if pdata.get("sign_index") is None:
            continue
        ph = whole_sign_house(pdata["sign_index"], asc_sign_index)
        if house in _planet_aspects(planet, ph):
            out.append(planet)
    return sorted(out)


def analyze_house(
    house_num: int,
    *,
    asc_sign_index: int,
    planet_positions: dict,
) -> dict:
    from agents.house_connections.themes import HOUSE_THEMES

    lord = lord_of_house(asc_sign_index, house_num)
    lord_data = planet_positions.get(lord) or {}
    lord_house = whole_sign_house(lord_data.get("sign_index", 0), asc_sign_index) if lord_data.get("sign_index") is not None else 0
    hfo = houses_from_own(house_num, lord_house) if lord_house else 1
    pos_type = position_type_from_own(hfo)
    pos_info = POSITION_TYPE[pos_type]
    theme = HOUSE_THEMES[house_num]

    planets_in = planets_in_house(planet_positions, asc_sign_index, house_num)
    planets_asp = planets_aspecting_house(planet_positions, asc_sign_index, house_num)
    strength = _house_strength(house_num, lord, lord_data, hfo, planets_in, planets_asp, asc_sign_index, planet_positions)
    rag = rag_status(strength)

    return {
        "house": house_num,
        "sign": sign_of_house(asc_sign_index, house_num),
        "theme_en": theme["en"],
        "theme_ta": theme["ta"],
        "impacts_en": theme["impacts_en"],
        "lord": lord,
        "lord_house": lord_house,
        "lord_sign": lord_data.get("sign", ""),
        "lord_dignity": _dignity(lord, lord_data.get("sign", "")),
        "lord_retrograde": bool(lord_data.get("retrograde")),
        "lord_nakshatra": lord_data.get("nakshatra", ""),
        "lord_pada": lord_data.get("pada"),
        "houses_from_own": hfo,
        "position_type": pos_type,
        "position_en": pos_info["en"],
        "position_ta": pos_info["ta"],
        "position_impact_en": pos_info["impact_en"],
        "position_impact_ta": pos_info["impact_ta"],
        "planets_in_house": planets_in,
        "planets_aspecting": planets_asp,
        "lord_strength_tags": _lord_strength_tags(lord, planet_positions, asc_sign_index),
        "strength": strength,
        "rag": rag,
        "is_dusthana": house_num in DUSTHANA,
    }


def analyze_all_houses(natal_chart: dict) -> dict[int, dict]:
    asc = natal_chart.get("ascendant") or {}
    asc_idx = asc.get("sign_index", 0)
    pp = natal_chart.get("planet_positions") or {}
    return {h: analyze_house(h, asc_sign_index=asc_idx, planet_positions=pp) for h in range(1, 13)}
