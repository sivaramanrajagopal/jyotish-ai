"""Atmakaraka / Amatyakaraka — classical degree-in-sign ranking."""

from __future__ import annotations

GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def degree_in_sign(longitude: float) -> float:
    return float(longitude) % 30.0


def classical_karakas(planet_positions: dict) -> dict:
    ranked: list[tuple[str, float, str]] = []
    for planet in GRAHAS:
        pdata = planet_positions.get(planet) or {}
        lon = pdata.get("longitude")
        if lon is None:
            continue
        ranked.append((planet, degree_in_sign(lon), pdata.get("sign", "")))
    ranked.sort(key=lambda x: (-x[1], x[0]))
    ak = ranked[0][0] if ranked else ""
    amk = ranked[1][0] if len(ranked) > 1 else ""
    return {
        "atmakaraka": ak,
        "amatyakaraka": amk,
        "atmakaraka_degrees": ranked[0][1] if ranked else 0.0,
        "ranked": [{"planet": p, "degrees_in_sign": d, "sign": s} for p, d, s in ranked],
    }


def whole_sign_house(planet_sign_index: int, asc_sign_index: int) -> int:
    return (int(planet_sign_index) - int(asc_sign_index)) % 12 + 1


def evaluate_atmakaraka_d10(
    planet_positions: dict,
    dasamsa_positions: dict,
    dasamsa_ascendant: dict,
) -> dict:
    info = classical_karakas(planet_positions)
    ak = info["atmakaraka"]
    out = {**info, "d10_house": None, "rule_matched": False, "detail": "No Atmakaraka"}
    if not ak or ak not in dasamsa_positions:
        return out
    asc_idx = dasamsa_ascendant.get("sign_index", 0)
    h = whole_sign_house(dasamsa_positions[ak]["sign_index"], asc_idx)
    out["d10_house"] = h
    if h == 10:
        out["rule_matched"] = True
        out["detail"] = f"AK {ak} in D10 10th ({dasamsa_positions[ak]['sign']})"
    elif h in (1, 4, 7, 10):
        out["rule_matched"] = True
        out["detail"] = f"AK {ak} in D10 Kendra H{h} ({dasamsa_positions[ak]['sign']})"
    else:
        out["detail"] = f"AK {ak} in D10 H{h} (not Kendra/10th)"
    return out
