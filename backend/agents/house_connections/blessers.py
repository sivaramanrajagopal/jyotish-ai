"""Blesser planet ranking per house — who can manifest results."""

from __future__ import annotations

from agents.house_connections.core import houses_owned_by, nakshatra_lord_for
from agents.house_connections.themes import BENEFICS
from agents.bhavat_bhavam.core import whole_sign_house, _lords_linked


def rank_blessers(
    house_num: int,
    houses: dict[int, dict],
    edges: list[dict],
    natal_chart: dict,
    maha: str = "",
    bhukti: str = "",
) -> list[dict]:
    asc_idx = (natal_chart.get("ascendant") or {}).get("sign_index", 0)
    pp = natal_chart.get("planet_positions") or {}
    ha = houses[house_num]
    lord = ha["lord"]
    scores: dict[str, float] = {}

    def bump(planet: str, pts: float, reason_en: str, reason_ta: str) -> None:
        if not planet or planet not in pp:
            return
        if planet not in scores:
            scores[planet] = 0.0
        scores[planet] += pts
        reasons = scores.setdefault(f"_reasons_{planet}", [])
        if isinstance(reasons, list):
            reasons.append({"en": reason_en, "ta": reason_ta, "pts": pts})

    # Lord of house
    bump(lord, 8, f"Lord of H{house_num}", f"H{house_num} அதிபதி")

    # Planets in house
    for p in ha["planets_in_house"]:
        bump(p, 5, f"Occupies H{house_num}", f"H{house_num} கிரகம்")

    # Aspecting house
    for p in ha["planets_aspecting"]:
        bump(p, 4, f"Aspects H{house_num}", f"H{house_num} பார்வை")

    # Edge-linked planets
    for e in edges:
        if e["to_house"] != house_num and e["from_house"] != house_num:
            continue
        w = e.get("weight", 1)
        for p in e.get("planets") or []:
            if e.get("supportive", True):
                bump(p, w, e["label_en"], e.get("label_ta", e["label_en"]))
            else:
                bump(p, -1, f"Stress: {e['label_en']}", e.get("label_ta", ""))

    # Pada lords of occupants
    for p in ha["planets_in_house"]:
        pl = nakshatra_lord_for(pp.get(p) or {})
        bump(pl, 3, f"Pada lord of {p} in H{house_num}", f"{p} pada அதிபதி")

    # Benefic dignity boost
    for planet in list(scores.keys()):
        if planet.startswith("_reasons_"):
            continue
        if planet in BENEFICS:
            scores[planet] += 2
        pdata = pp.get(planet) or {}
        sign = pdata.get("sign", "")
        if sign in ("Cancer", "Taurus", "Sagittarius", "Pisces", "Libra"):
            pass  # simplified — dignity already in house strength

    # Dasa activation
    for planet in list(scores.keys()):
        if planet.startswith("_reasons_"):
            continue
        if planet == maha:
            scores[planet] += 6
        elif planet == bhukti:
            scores[planet] += 4

    ranked: list[dict] = []
    for planet, score in scores.items():
        if planet.startswith("_reasons_"):
            continue
        reasons = scores.get(f"_reasons_{planet}", [])
        ranked.append({
            "planet": planet,
            "score": round(score, 1),
            "active_maha": planet == maha,
            "active_bhukti": planet == bhukti,
            "reasons": reasons if isinstance(reasons, list) else [],
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:6]
