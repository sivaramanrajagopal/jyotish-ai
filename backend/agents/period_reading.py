"""Plain reading of the current mahadasha and bhukti.

Ties four scores the chart already has:
  Avastha  — whether the period lords can deliver now
  Shadbala — how much strength each lord holds
  BAV      — whether the sign a lord occupies supports that lord
  SAV      — whether the houses that lord rules can receive the result
"""

from __future__ import annotations

from agents.ashtakavarga_agent import calculate_ashtakavarga
from agents.avastha_agent import compute_avastha_analysis
from agents.natal_agent import SIGN_LORDS, SIGNS
from agents.shadbala_agent import compute_shadbala_for_chart

SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
BAV_KEY = {name: name.upper() for name in SEVEN}

DOMAIN = {
    "Sun": "Self, authority, and vitality",
    "Moon": "Mind, mother, and emotional comfort",
    "Mars": "Effort, courage, and siblings",
    "Mercury": "Speech, skill, and trade",
    "Jupiter": "Wisdom, children, and guidance",
    "Venus": "Comfort, marriage, and the arts",
    "Saturn": "Work, endurance, and delay",
    "Rahu": "The house it occupies, and unusual desire",
    "Ketu": "The house it occupies, and release",
}

HOUSE_THEME = {
    1: "the self",
    2: "family and savings",
    3: "courage and siblings",
    4: "home and comfort",
    5: "children and learning",
    6: "work, debt, and health",
    7: "marriage and partners",
    8: "sudden change",
    9: "fortune and guidance",
    10: "career and status",
    11: "gains",
    12: "expenses and endings",
}

STHULA = {
    "Deepta": "bright",
    "Sthamitha": "steady",
    "Muditha": "pleased",
    "Santha": "calm",
    "Sakta": "constrained",
    "Heenasakstha": "weakened",
    "Deena": "distressed",
    "Peethya": "unstable",
    "Peeda": "pressured",
    "Vikala": "combust",
    "Kala": "debilitated",
}

SUKSHMA = {
    "Prakasha": "fully lit",
    "Aasthani": "settled",
    "Bhoji": "enjoying",
    "Aagamana": "arriving",
    "Nritya": "active",
    "Aagama": "coming in",
    "Netrapani": "watching",
    "Kauthuka": "curious",
    "Upaveshana": "seated",
    "Gamana": "moving",
    "Sayana": "resting",
    "Nidra": "asleep",
}

LEAD = {
    "Peak Fructification": "Both lords are in good condition. This period can show results when effort is applied.",
    "Progressive Growth": "This period moves steadily. Plan the work and follow through.",
    "Inertia / Delays": "This period is slow. Results need more effort, and maintenance suits it better than a new launch.",
    "High Friction": "This period is blocked. Keep the stakes low and use it for review.",
}

SAV_WORD = {
    "Strong": "fertile",
    "Good": "able to receive results",
    "Average": "ordinary",
    "Weak": "thin",
}


def _min_text(value: float) -> str:
    number = float(value)
    if number == int(number):
        return str(int(number))
    return f"{number:.1f}"


def strength_phrase(row: dict | None) -> str | None:
    if not row:
        return None
    held = f"{row['rupas']:.2f} / {_min_text(row['minimum'])}"
    ratio = float(row["ratio"])
    if not row["meets_minimum"]:
        band = "short of the strength it needs"
    elif ratio >= 1.3:
        band = "well above the strength it needs"
    elif ratio >= 1.1:
        band = "above the strength it needs"
    elif ratio < 1.05:
        band = "meets the strength it needs, with nothing to spare"
    else:
        band = "just past the strength it needs"
    return f"{held} — {band}"


def condition_phrase(row: dict | None) -> str | None:
    if not row:
        return None
    net = float(row["manifestation"]["net"])
    if net >= 80:
        pace = "awake and able"
    elif net >= 50:
        pace = "workable"
    elif net >= 25:
        pace = "slow"
    else:
        pace = "blocked"
    sthula = STHULA.get(row["sthula"]["name"], row["sthula"]["name"])
    sukshma = SUKSHMA.get(row["sukshma"]["name"], row["sukshma"]["name"])
    return f"{net:.0f}% — {pace} ({sthula}, {sukshma})"


def bav_phrase(points: int | None, sign: str) -> str | None:
    if points is None:
        return None
    if points >= 5:
        ground = "supportive ground"
    elif points == 4:
        ground = "ordinary ground"
    else:
        ground = "thin ground"
    return f"Sits in {sign} with {points} points, {ground}."


def _sav_word(label: str) -> str:
    return SAV_WORD.get(label, label.lower())


def houses_ruled(planet: str, lagna_index: int) -> list[int]:
    owned = []
    for house in range(1, 13):
        sign = SIGNS[(lagna_index + house - 1) % 12]
        if SIGN_LORDS.get(sign) == planet:
            owned.append(house)
    return owned


def _house_line(house: int, points: int, label: str) -> str:
    theme = HOUSE_THEME.get(house, "that life area")
    return f"house {house} ({theme}), {_sav_word(label)} at {points}"


def compose_period_reading(
    chart: dict,
    shadbala: dict,
    avastha: dict,
    ashtakavarga: dict,
) -> dict:
    dasha = chart.get("dasha") or {}
    maha = ((dasha.get("mahadasha") or {}).get("planet")
            or (avastha.get("summary") or {}).get("current_dasa"))
    bhukti = ((dasha.get("bhukti") or {}).get("planet")
              or (avastha.get("summary") or {}).get("current_bhukti"))
    synergy = avastha.get("dasa_bhukti") or {}
    klass = synergy.get("manifestationClass") or ""

    by_strength = {row["planet"]: row for row in shadbala.get("planets") or []}
    by_state = {row["planet"]: row for row in avastha.get("planets") or []}
    positions = chart.get("planet_positions") or {}
    asc = chart.get("ascendant") or {}
    lagna_index = SIGNS.index(asc["sign"]) if asc.get("sign") in SIGNS else 0
    sav_by_house = {
        item["house"]: item for item in (ashtakavarga.get("sav") or {}).get("by_house") or []
    }
    bav = ashtakavarga.get("bav") or {}

    lords = []
    for role, planet in (("Mahadasha", maha), ("Bhukti", bhukti)):
        if not planet:
            continue
        state = by_state.get(planet) or {}
        placed = positions.get(planet) or {}
        sign = placed.get("sign") or state.get("sign") or ""
        sign_index = placed.get("sign_index")
        if sign_index is None and sign in SIGNS:
            sign_index = SIGNS.index(sign)

        strength = strength_phrase(by_strength.get(planet))
        if planet not in SEVEN:
            strength = "Read through condition and the house it occupies."

        points = None
        if planet in SEVEN and sign_index is not None:
            sign_wise = (bav.get(BAV_KEY[planet]) or {}).get("sign_wise") or []
            if 0 <= int(sign_index) < len(sign_wise):
                points = int(sign_wise[int(sign_index)])

        if planet in SEVEN:
            ground_bits = []
            seat = bav_phrase(points, sign)
            if seat:
                ground_bits.append(seat)
            owned = []
            for house in houses_ruled(planet, lagna_index):
                item = sav_by_house.get(house)
                if item:
                    owned.append(_house_line(house, item["sav_points"], item["label"]))
            if owned:
                joined = owned[0] if len(owned) == 1 else ", and ".join(
                    [", ".join(owned[:-1]), owned[-1]]
                )
                ground_bits.append(f"Rules {joined}.")
            ground = " ".join(ground_bits)
        else:
            house = placed.get("house")
            item = sav_by_house.get(house) if house else None
            if item:
                ground = "Occupies " + _house_line(house, item["sav_points"], item["label"]) + "."
            else:
                ground = ""

        lords.append({
            "role": role,
            "planet": planet,
            "domain": DOMAIN.get(planet, ""),
            "strength": strength,
            "condition": condition_phrase(state) if state else None,
            "ground": ground,
        })

    return {
        "mahadasha": maha,
        "bhukti": bhukti,
        "period_label": f"{maha} mahadasha, {bhukti} bhukti" if maha and bhukti else "",
        "lead": LEAD.get(klass, ""),
        "period_class": klass,
        "lords": lords,
        "note": (
            "Condition says whether this period can deliver. "
            "Strength says how much each lord has to give. "
            "Points say whether the sign and the houses can receive the result."
        ),
    }


def compute_period_reading(chart: dict) -> dict:
    return compose_period_reading(
        chart,
        compute_shadbala_for_chart(chart),
        compute_avastha_analysis(chart),
        calculate_ashtakavarga(chart),
    )
