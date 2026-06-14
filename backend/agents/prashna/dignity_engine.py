"""Dignity and strength evaluation for Prashna — English signs + degree-aware."""

from __future__ import annotations

from agents.natal_agent import DEBILITATION, EXALTATION, SIGNS, SIGN_LORDS
from agents.prashna.constants import DIGNITY_STRENGTH

# Traditional friendships (English sign lords)
FRIENDSHIPS: dict[str, dict[str, list[str]]] = {
    "Sun":     {"friends": ["Moon", "Mars", "Jupiter"],    "enemies": ["Venus", "Saturn"]},
    "Moon":    {"friends": ["Sun", "Mercury"],            "enemies": []},
    "Mars":    {"friends": ["Sun", "Moon", "Jupiter"],     "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"],              "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"],        "enemies": ["Mercury", "Venus"]},
    "Venus":   {"friends": ["Mercury", "Saturn"],         "enemies": ["Sun", "Moon"]},
    "Saturn":  {"friends": ["Mercury", "Venus"],          "enemies": ["Sun", "Moon", "Mars"]},
}

OWN_SIGNS: dict[str, list[str]] = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

DEEP_ORB = 5.0  # degrees from exact exaltation / debilitation point


def _degree_distance(deg: float, target: float) -> float:
    return min(abs(deg - target), 30 - abs(deg - target))


def _dignity_score(state: str, deep: bool = False) -> float:
    base = {
        "Exalted": 100, "Own Sign": 90, "Friend": 70,
        "Neutral": 50, "Enemy": 30, "Debilitated": 10, "N/A": 50,
    }.get(state, 50)
    if deep and state == "Exalted":
        return min(100, base + 5)
    if deep and state == "Debilitated":
        return max(5, base - 5)
    return base


def planetary_state(planet: str, sign: str, degree_in_sign: float | None = None) -> tuple[str, bool]:
    """
    Return (dignity_state, is_deep) using sign + optional degree within sign.
    Deep = within DEEP_ORB of classical exact exaltation/debilitation degree.
    """
    if planet in ("Rahu", "Ketu", "Ascendant"):
        return "N/A", False

    sign_idx = SIGNS.index(sign) if sign in SIGNS else -1

    if planet in EXALTATION:
        ex_sign, ex_deg = EXALTATION[planet]
        deb_sign, deb_deg = DEBILITATION[planet]

        if sign_idx == ex_sign:
            deep = (
                degree_in_sign is not None
                and _degree_distance(degree_in_sign, ex_deg) <= DEEP_ORB
            )
            return "Exalted", deep

        if sign_idx == deb_sign:
            deep = (
                degree_in_sign is not None
                and _degree_distance(degree_in_sign, deb_deg) <= DEEP_ORB
            )
            return "Debilitated", deep

    if sign in OWN_SIGNS.get(planet, []):
        return "Own Sign", False

    sign_lord = SIGN_LORDS.get(sign, "")
    rel = FRIENDSHIPS.get(planet, {})
    if sign_lord in rel.get("friends", []):
        return "Friend", False
    if sign_lord in rel.get("enemies", []):
        return "Enemy", False
    return "Neutral", False


def planetary_dignity(
    planet: str,
    sign: str,
    degree_in_sign: float | None = None,
) -> dict:
    state, deep = planetary_state(planet, sign, degree_in_sign)
    strength = DIGNITY_STRENGTH.get(state, "neutral")
    score = _dignity_score(state, deep)

    explanations = {
        "Exalted": f"{planet} is exalted in {sign} — strong natural expression.",
        "Own Sign": f"{planet} is in own sign {sign} — stable and empowered.",
        "Friend": f"{planet} is in a friendly sign ({sign}) — moderately supportive.",
        "Neutral": f"{planet} is in neutral dignity in {sign}.",
        "Enemy": f"{planet} is in an enemy sign ({sign}) — some friction indicated.",
        "Debilitated": f"{planet} is debilitated in {sign} — weakened expression.",
        "N/A": f"{planet} dignity not evaluated in {sign}.",
    }
    explanation = explanations.get(state, "")
    if deep and state == "Exalted":
        explanation += f" Near exact exaltation degree — peak strength."
    elif deep and state == "Debilitated":
        explanation += f" Near exact debilitation degree — especially weakened."

    return {
        "planet": planet,
        "sign": sign,
        "degree_in_sign": degree_in_sign,
        "state": state,
        "deep": deep,
        "strength": strength,
        "score": score,
        "explanation": explanation,
    }


def strength_label(strength: str) -> str:
    return {"strong": "Strong", "neutral": "Neutral", "weak": "Weak"}.get(strength, "Neutral")
