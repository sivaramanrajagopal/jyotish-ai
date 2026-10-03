"""
Pure Sthula / Sukshma Avastha math and 0–100% condition scoring.

Hard overrides (classical affliction): Combust → Debilitated → last-degree.
Soft modifiers (do not wipe dignity): Athi Vega −15, Retrograde −10 (nodes skip retro).
Net condition = geometric mean √(capacity × efficiency).
Dasa–Bhukti = average of the two lords' nets.
"""

from __future__ import annotations

import math
from typing import Any, Literal, TypedDict

PlanetName = Literal[
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
]

SignDignity = Literal[
    "Exalted", "Moolatrikona", "Own", "Friendly", "Benefic",
    "Neutral", "Inimical", "Debilitated",
]

SthulaName = Literal[
    "Deepta", "Sthamitha", "Muditha", "Santha", "Sakta", "Heenasakstha",
    "Deena", "Peethya", "Peeda", "Vikala", "Kala",
]

SukshmaName = Literal[
    "Sayana", "Upaveshana", "Netrapani", "Prakasha", "Gamana", "Aagamana",
    "Aasthani", "Aagama", "Bhoji", "Nritya", "Kauthuka", "Nidra",
]

ManifestationClass = Literal[
    "Immediate & High Manifestation",
    "Conditional / Strategic Manifestation",
    "Delayed / Sluggish Manifestation",
    "Blocked / Distressed Manifestation",
]

DasaBhuktiClass = Literal[
    "Peak Fructification",
    "Progressive Growth",
    "Inertia / Delays",
    "High Friction",
]

PLANET_INDEX: dict[str, int] = {
    "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4, "Jupiter": 5,
    "Venus": 6, "Saturn": 7, "Rahu": 8, "Ketu": 9,
}

NODE_PLANETS = frozenset({"Rahu", "Ketu"})
STRONG_DIGNITY = frozenset({"Exalted", "Moolatrikona", "Own"})

SUKSHMA_NAMES: dict[int, SukshmaName] = {
    1: "Sayana", 2: "Upaveshana", 3: "Netrapani", 4: "Prakasha",
    5: "Gamana", 6: "Aagamana", 7: "Aasthani", 8: "Aagama",
    9: "Bhoji", 10: "Nritya", 11: "Kauthuka", 12: "Nidra",
}

# Capped capacities — avoid implying a perfect 100% engine
STHULA_CAPACITY: dict[str, float] = {
    "Deepta": 90.0,
    "Sthamitha": 80.0,
    "Muditha": 70.0,
    "Santha": 60.0,
    "Sakta": 55.0,
    "Heenasakstha": 45.0,
    "Deena": 35.0,
    "Peethya": 30.0,
    "Peeda": 25.0,  # retained for legend; soft Athi Vega uses a penalty instead
    "Vikala": 15.0,
    "Kala": 15.0,
}

ATHI_VEGA_PENALTY = 15.0
RETRO_PENALTY = 10.0
CAPACITY_FLOOR = 15.0

SUKSHMA_EFFICIENCY: dict[str, float] = {
    "Prakasha": 100.0,
    "Aasthani": 100.0,
    "Bhoji": 85.0,
    "Aagamana": 85.0,
    "Nritya": 80.0,
    "Aagama": 80.0,
    "Netrapani": 70.0,
    "Kauthuka": 70.0,
    "Upaveshana": 60.0,
    "Gamana": 50.0,
    "Sayana": 30.0,
    "Nidra": 15.0,
}

_DIGNITY_TO_STHULA: dict[str, SthulaName] = {
    "Exalted": "Deepta",
    "Moolatrikona": "Deepta",
    "Own": "Sthamitha",
    "Friendly": "Muditha",
    "Benefic": "Santha",
    "Neutral": "Heenasakstha",
    "Inimical": "Deena",
    "Debilitated": "Kala",
}

_CLASS_OUTCOMES: dict[DasaBhuktiClass, list[str]] = {
    "Peak Fructification": [
        "Both period lords show solid natal condition scores.",
        "Favourable window for decisive action when effort is applied.",
    ],
    "Progressive Growth": [
        "Steady fructification with planning and follow-through.",
        "Prefer structured goals over sudden leaps.",
    ],
    "Inertia / Delays": [
        "Sluggish or late delivery is more likely this period pair.",
        "Favour maintenance over high-stakes launches.",
    ],
    "High Friction": [
        "This lord pair tends toward friction or blocked output.",
        "Keep stakes low; use for review and remedies.",
    ],
}


class SukshmaBreakdown(TypedDict):
    step1: int
    step2: int
    step3: int
    remainder: int
    avastha_index: int
    formula: str


def eval_sthula_avastha(
    *,
    sign_dignity: SignDignity | str,
    is_retrograde: bool,
    is_combust: bool,
    is_accelerated: bool,
    degree_in_rasi: float,
    planet_name: str | None = None,
) -> tuple[SthulaName, str, float, float]:
    """
    Return (sthula_name, reason, athi_penalty, retro_penalty).

    Hard overrides: combust, debilitated, last degree.
    Athi Vega / retrograde are soft capacity penalties (except nodes skip retro).
    Retrograde on weak dignity (not exalted/MT/own) may label Sakta.
    """
    deg = float(degree_in_rasi)
    is_node = planet_name in NODE_PLANETS
    athi_pen = 0.0
    retro_pen = 0.0

    if is_combust:
        return "Vikala", "Combust — hard affliction", 0.0, 0.0
    if sign_dignity == "Debilitated":
        return "Kala", "Debilitated sign placement", 0.0, 0.0
    if deg >= 29.0:
        # Soft modifiers can still apply on last-degree
        name: SthulaName = "Peethya"
        reason = "Last degree of rasi (≥ 29°)"
        if is_accelerated:
            athi_pen = ATHI_VEGA_PENALTY
            reason += f"; Athi Vega −{ATHI_VEGA_PENALTY:.0f}"
        if is_retrograde and not is_node:
            retro_pen = RETRO_PENALTY
            reason += f"; Retrograde −{RETRO_PENALTY:.0f}"
        return name, reason, athi_pen, retro_pen

    # Dignity base (nodes stay on Neutral → Heenasakstha unless overridden above)
    if is_retrograde and not is_node and sign_dignity not in STRONG_DIGNITY:
        name = "Sakta"
        reason = f"Retrograde on {sign_dignity} dignity"
        retro_pen = 0.0  # Sakta capacity already encodes constraint
    else:
        name = _DIGNITY_TO_STHULA.get(sign_dignity, "Heenasakstha")
        reason = f"Dignity: {sign_dignity}"
        if is_retrograde and not is_node:
            retro_pen = RETRO_PENALTY
            reason += f"; Retrograde −{RETRO_PENALTY:.0f}"

    if is_accelerated:
        athi_pen = ATHI_VEGA_PENALTY
        reason += f"; Athi Vega −{ATHI_VEGA_PENALTY:.0f}"

    return name, reason, athi_pen, retro_pen


def apply_capacity_penalties(
    base_capacity: float,
    athi_penalty: float,
    retro_penalty: float,
) -> float:
    return max(CAPACITY_FLOOR, float(base_capacity) - float(athi_penalty) - float(retro_penalty))


def eval_sukshma_avastha(
    *,
    planet_index: int,
    nakshatra_index: int,
    degree_in_rasi: float,
    janma_nakshatra_index: int,
    lagna_rasi_index: int,
    birth_nazhikai_after_sunrise: float,
) -> tuple[SukshmaName, SukshmaBreakdown]:
    """Sukshma remainder formula (1-based indices). remainder 0 → 12 Nidra."""
    p_idx = int(planet_index)
    n_idx = int(nakshatra_index)
    deg = float(degree_in_rasi)
    janma = int(janma_nakshatra_index)
    lagna = int(lagna_rasi_index)
    nazhikai = float(birth_nazhikai_after_sunrise)

    step1 = p_idx * n_idx
    step2 = math.floor(step1 * deg)
    step3 = step2 + janma + lagna + nazhikai
    step3_int = math.floor(step3)
    remainder = step3_int % 12
    avastha_index = 12 if remainder == 0 else remainder
    name = SUKSHMA_NAMES[avastha_index]

    breakdown: SukshmaBreakdown = {
        "step1": step1,
        "step2": step2,
        "step3": step3_int,
        "remainder": remainder,
        "avastha_index": avastha_index,
        "formula": (
            f"({p_idx}×{n_idx}={step1}) → floor({step1}×{deg:.4f})={step2} → "
            f"{step2}+{janma}+{lagna}+{nazhikai:.4f}={step3_int} → "
            f"{step3_int}%12={remainder} → index {avastha_index} ({name})"
        ),
    }
    return name, breakdown


def manifestation_index(capacity: float, efficiency: float) -> float:
    """Geometric mean of capacity and efficiency (softer than product/100)."""
    c = max(0.0, float(capacity))
    e = max(0.0, float(efficiency))
    return round(math.sqrt(c * e), 2)


def average_pair(a: float, b: float) -> float:
    return round((float(a) + float(b)) / 2.0, 2)


def classify_manifestation(net: float) -> ManifestationClass:
    n = float(net)
    if n >= 80:
        return "Immediate & High Manifestation"
    if n >= 50:
        return "Conditional / Strategic Manifestation"
    if n >= 25:
        return "Delayed / Sluggish Manifestation"
    return "Blocked / Distressed Manifestation"


def _dasa_bhukti_class(combined: float) -> DasaBhuktiClass:
    n = float(combined)
    if n >= 80:
        return "Peak Fructification"
    if n >= 50:
        return "Progressive Growth"
    if n >= 25:
        return "Inertia / Delays"
    return "High Friction"


def score_planet(
    *,
    planet_name: PlanetName | str,
    planet_index: int,
    rasi_index: int,
    nakshatra_index: int,
    degree_in_rasi: float,
    is_retrograde: bool,
    is_combust: bool,
    is_accelerated: bool,
    sign_dignity: SignDignity | str,
    janma_nakshatra_index: int,
    lagna_rasi_index: int,
    birth_nazhikai_after_sunrise: float,
) -> dict[str, Any]:
    """Full per-planet Sthula + Sukshma + condition score packet."""
    sthula, sthula_reason, athi_pen, retro_pen = eval_sthula_avastha(
        sign_dignity=sign_dignity,
        is_retrograde=is_retrograde,
        is_combust=is_combust,
        is_accelerated=is_accelerated,
        degree_in_rasi=degree_in_rasi,
        planet_name=planet_name,
    )
    sukshma, breakdown = eval_sukshma_avastha(
        planet_index=planet_index,
        nakshatra_index=nakshatra_index,
        degree_in_rasi=degree_in_rasi,
        janma_nakshatra_index=janma_nakshatra_index,
        lagna_rasi_index=lagna_rasi_index,
        birth_nazhikai_after_sunrise=birth_nazhikai_after_sunrise,
    )
    base_cap = STHULA_CAPACITY[sthula]
    capacity = apply_capacity_penalties(base_cap, athi_pen, retro_pen)
    efficiency = SUKSHMA_EFFICIENCY[sukshma]
    net = manifestation_index(capacity, efficiency)
    m_class = classify_manifestation(net)

    return {
        "planet": planet_name,
        "planet_index": planet_index,
        "rasi_index": rasi_index,
        "nakshatra_index": nakshatra_index,
        "degree_in_rasi": round(float(degree_in_rasi), 4),
        "is_retrograde": bool(is_retrograde),
        "is_combust": bool(is_combust),
        "is_accelerated": bool(is_accelerated),
        "sign_dignity": sign_dignity,
        "sthula": {
            "name": sthula,
            "capacity": capacity,
            "base_capacity": base_cap,
            "athi_vega_penalty": athi_pen,
            "retro_penalty": retro_pen,
            "reason": sthula_reason,
        },
        "sukshma": {
            "name": sukshma,
            "efficiency": efficiency,
            "avastha_index": breakdown["avastha_index"],
            "breakdown": breakdown,
        },
        "manifestation": {
            "net": net,
            "class": m_class,
            "method": "geometric_mean",
        },
    }


def evaluate_dasa_bhukti_synergy(
    dasa_lord: PlanetName | str,
    bhukti_lord: PlanetName | str,
    dasa_net: float,
    bhukti_net: float,
) -> dict[str, Any]:
    combined = average_pair(dasa_net, bhukti_net)
    klass = _dasa_bhukti_class(combined)
    return {
        "dasaLord": dasa_lord,
        "bhuktiLord": bhukti_lord,
        "dasa_net": round(float(dasa_net), 2),
        "bhukti_net": round(float(bhukti_net), 2),
        "combinedScore": combined,
        "method": "average",
        "manifestationClass": klass,
        "objectiveOutcome": _CLASS_OUTCOMES[klass],
    }
