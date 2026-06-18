"""Profession probability tags — adapted from profession_predictor_v2."""

from __future__ import annotations

from collections import defaultdict

from agents.natal_agent import SIGN_LORDS, SIGNS
from agents.career.atmakaraka import whole_sign_house

PROFESSION_CATEGORIES: dict[str, dict] = {
    "Technology / IT": {
        "description": "Software, engineering, data, tech leadership",
        "primary": ["Mercury", "Rahu", "Saturn", "Mars"],
        "secondary": ["Jupiter", "Venus"],
        "signs": ["Gemini", "Virgo", "Aquarius", "Scorpio"],
        "houses": [3, 5, 6, 9, 10, 11],
    },
    "Business / Leadership": {
        "description": "CEO, management, entrepreneurship",
        "primary": ["Sun", "Mercury", "Jupiter"],
        "secondary": ["Venus", "Mars"],
        "signs": ["Leo", "Sagittarius", "Capricorn"],
        "houses": [1, 2, 7, 10, 11],
    },
    "Finance / Banking": {
        "description": "Finance, investment, accounting",
        "primary": ["Venus", "Jupiter", "Mercury"],
        "secondary": ["Moon"],
        "signs": ["Taurus", "Libra", "Sagittarius"],
        "houses": [2, 5, 9, 10, 11],
    },
    "Government / Public Service": {
        "description": "Administration, politics, civil service",
        "primary": ["Sun", "Saturn", "Jupiter"],
        "secondary": ["Mars", "Rahu"],
        "signs": ["Leo", "Capricorn", "Sagittarius"],
        "houses": [1, 6, 9, 10],
    },
    "Medicine / Healthcare": {
        "description": "Doctor, nursing, healing professions",
        "primary": ["Moon", "Ketu", "Mars"],
        "secondary": ["Jupiter", "Venus"],
        "signs": ["Cancer", "Scorpio", "Pisces", "Virgo"],
        "houses": [6, 8, 10, 12],
    },
    "Teaching / Research": {
        "description": "Education, academia, training",
        "primary": ["Jupiter", "Mercury"],
        "secondary": ["Moon"],
        "signs": ["Sagittarius", "Pisces", "Gemini"],
        "houses": [4, 5, 9, 10],
    },
    "Arts / Media": {
        "description": "Creative arts, entertainment, journalism",
        "primary": ["Venus", "Moon", "Mercury"],
        "secondary": ["Rahu"],
        "signs": ["Taurus", "Libra", "Pisces", "Cancer"],
        "houses": [3, 5, 10, 11],
    },
    "Law / Judiciary": {
        "description": "Legal practice, judiciary",
        "primary": ["Jupiter", "Saturn", "Sun"],
        "secondary": ["Mercury"],
        "signs": ["Sagittarius", "Capricorn", "Libra"],
        "houses": [6, 7, 9, 10],
    },
    "Sales / Communication": {
        "description": "Sales, marketing, PR, consulting",
        "primary": ["Mercury", "Venus", "Moon"],
        "secondary": ["Jupiter"],
        "signs": ["Gemini", "Virgo", "Libra"],
        "houses": [2, 3, 7, 10, 11],
    },
    "Sports / Defense": {
        "description": "Athletics, military, police",
        "primary": ["Mars", "Sun"],
        "secondary": ["Saturn", "Ketu"],
        "signs": ["Aries", "Scorpio", "Leo"],
        "houses": [1, 3, 6, 10],
    },
}


CAREER_PLANETS = frozenset({
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
})


def _planets_in_house(pp: dict, asc_idx: int, house: int) -> list[str]:
    out = []
    for planet, pdata in pp.items():
        if planet not in CAREER_PLANETS:
            continue
        if whole_sign_house(pdata.get("sign_index", 0), asc_idx) == house:
            out.append(planet)
    return sorted(out)


def predict_professions(
    planet_positions: dict,
    asc_sign_index: int,
    tenth_lord: str,
) -> list[dict]:
    tenth_idx = (asc_sign_index + 9) % 12
    tenth_sign = SIGNS[tenth_idx]
    in_10 = _planets_in_house(planet_positions, asc_sign_index, 10)
    lord_pdata = planet_positions.get(tenth_lord) or {}
    lord_sign = lord_pdata.get("sign", "")
    lord_house = whole_sign_house(lord_pdata.get("sign_index", 0), asc_sign_index) if lord_pdata else None

    conjunct_lord = [
        p for p, pdata in planet_positions.items()
        if p != tenth_lord and pdata.get("sign") == lord_sign
        and p in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    ]

    scores: dict[str, dict] = defaultdict(lambda: {"score": 0.0, "reasons": []})

    for name, ind in PROFESSION_CATEGORIES.items():
        score = 0.0
        reasons: list[str] = []
        for p in in_10:
            if p in ind["primary"]:
                score += 30
                reasons.append(f"{p} in D1 H10")
            elif p in ind["secondary"]:
                score += 15
                reasons.append(f"{p} in D1 H10 (secondary)")
        if tenth_sign in ind["signs"]:
            score += 20
            reasons.append(f"10th in {tenth_sign}")
        if tenth_lord in ind["primary"]:
            score += 25
            reasons.append(f"{tenth_lord} is 10th lord")
        elif tenth_lord in ind["secondary"]:
            score += 15
        if lord_sign in ind["signs"]:
            score += 20
            reasons.append(f"10th lord in {lord_sign}")
        for p in conjunct_lord:
            if p in ind["primary"]:
                score += 25
                reasons.append(f"{p} with 10th lord")
            elif p in ind["secondary"]:
                score += 15
        if lord_house and lord_house in ind["houses"]:
            score += 10
            reasons.append(f"10th lord in H{lord_house}")
        scores[name]["score"] = min(score, 100.0)
        scores[name]["reasons"] = reasons[:3]

    ranked = sorted(
        (
            {
                "name": name,
                "description": PROFESSION_CATEGORIES[name]["description"],
                "probability": round(data["score"], 1),
                "reasons": data["reasons"],
            }
            for name, data in scores.items()
        ),
        key=lambda x: -x["probability"],
    )
    return ranked
