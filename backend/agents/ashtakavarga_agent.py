"""
ashtakavarga_agent.py
=====================
Ashtakavarga (BAV + SAV) calculation engine.

Ported from: https://github.com/sivaramanrajagopal/Ashtavargam
  - ashtakavarga_calculator_v2.py  (BAV rules + calculation)
  - calculators/advanced_ashtavarga.py (Trikona + Ekadhipatya Shodhana, Shodhya Pinda)

Entry points:
    calculate_ashtakavarga(natal_chart: dict) -> dict
        Returns BAV per planet (sign-wise + house-wise), SAV, Shodhana, Pinda.

    sav_for_transit_scoring(natal_chart: dict) -> list[int]
        Returns SAV house-wise array [H1..H12] for use in transit scoring.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from chart_utils import chart_fingerprint

load_dotenv(Path(__file__).parent.parent / ".env")

# ─────────────────────────────────────────────────────────────────────────────
# Tamil/South Indian BAV rules (ashtakavarga_calculator_final.py — Ashtavargam)
# ─────────────────────────────────────────────────────────────────────────────

BAV_RULES: dict[str, dict[str, list[int]]] = {
    "SUN": {
        "SUN": [1, 2, 4, 7, 8, 9, 10, 11],
        "MOON": [3, 6, 10, 11],
        "MARS": [1, 2, 4, 7, 8, 9, 10, 11],
        "MERCURY": [3, 5, 6, 9, 10, 11, 12],
        "JUPITER": [5, 6, 9, 11],
        "VENUS": [6, 7, 12],
        "SATURN": [1, 2, 4, 7, 8, 9, 10, 11],
        "ASCENDANT": [3, 4, 6, 10, 11, 12],
    },
    "MOON": {
        "SUN": [3, 6, 7, 8, 10, 11],
        "MOON": [1, 3, 6, 7, 10, 11],
        "MARS": [2, 3, 5, 6, 9, 10, 11],
        "MERCURY": [1, 3, 4, 5, 7, 8, 10, 11],
        "JUPITER": [1, 4, 7, 8, 10, 11, 12],
        "VENUS": [3, 4, 5, 7, 9, 10, 11],
        "SATURN": [3, 5, 6, 11],
        "ASCENDANT": [3, 6, 10, 11],
    },
    "MARS": {
        "SUN": [3, 5, 6, 10, 11],
        "MOON": [3, 6, 11],
        "MARS": [1, 2, 4, 7, 8, 10, 11],
        "MERCURY": [3, 5, 6, 11],
        "JUPITER": [6, 10, 11, 12],
        "VENUS": [6, 8, 11, 12],
        "SATURN": [1, 4, 7, 8, 9, 10, 11],
        "ASCENDANT": [1, 3, 6, 10, 11],
    },
    "MERCURY": {
        "SUN": [5, 6, 9, 11, 12],
        "MOON": [2, 4, 6, 8, 10, 11],
        "MARS": [1, 2, 4, 7, 8, 9, 10, 11],
        "MERCURY": [1, 3, 5, 6, 9, 10, 11, 12],
        "JUPITER": [6, 8, 11, 12],
        "VENUS": [1, 2, 3, 4, 5, 8, 9, 11],
        "SATURN": [1, 2, 4, 7, 8, 9, 10, 11],
        "ASCENDANT": [1, 2, 4, 6, 8, 10, 11],
    },
    "JUPITER": {
        "SUN": [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "MOON": [2, 5, 7, 9, 11],
        "MARS": [1, 2, 4, 7, 8, 10, 11],
        "MERCURY": [1, 2, 4, 5, 6, 9, 10, 11],
        "JUPITER": [1, 2, 3, 4, 7, 8, 10, 11],
        "VENUS": [2, 5, 6, 9, 10, 11],
        "SATURN": [3, 5, 6, 12],
        "ASCENDANT": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "VENUS": {
        "SUN": [8, 11, 12],
        "MOON": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "MARS": [3, 5, 6, 9, 11, 12],
        "MERCURY": [3, 5, 6, 9, 11],
        "JUPITER": [5, 8, 9, 10, 11],
        "VENUS": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "SATURN": [3, 4, 5, 8, 9, 10, 11],
        "ASCENDANT": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "SATURN": {
        "SUN": [1, 2, 4, 7, 8, 10, 11],
        "MOON": [3, 6, 11],
        "MARS": [3, 5, 6, 10, 11, 12],
        "MERCURY": [6, 8, 9, 10, 11, 12],
        "JUPITER": [5, 6, 11, 12],
        "VENUS": [6, 11, 12],
        "SATURN": [3, 5, 6, 11],
        "ASCENDANT": [1, 3, 4, 6, 10, 11],
    },
    "ASCENDANT": {
        "SUN": [3, 4, 6, 10, 11, 12],
        "MOON": [3, 6, 10, 11],
        "MARS": [1, 3, 6, 10, 11],
        "MERCURY": [1, 2, 4, 6, 8, 10, 11],
        "JUPITER": [1, 2, 4, 5, 6, 7, 9, 10, 11],
        "VENUS": [1, 2, 3, 4, 5, 8, 9, 11],
        "SATURN": [1, 3, 4, 6, 10, 11],
        "ASCENDANT": [3, 6, 10, 11],
    },
}

BAV_CONTRIBUTORS = [
    "SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "ASCENDANT",
]

# Planets included in SAV (ASCENDANT excluded from SAV sum)
SAV_PLANETS = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]

# Trikona groups for Shodhana (sign numbers 1-12)
TRIKONA_GROUPS = [(1, 5, 9), (2, 6, 10), (3, 7, 11), (4, 8, 12)]

# Ekadhipatya pairs (dual-lord signs)
EKADHIPATYA_PAIRS = [(1, 8), (2, 7), (3, 6), (9, 12), (10, 11)]

RASI_GUNAKARA  = {1:7,2:10,3:8,4:4,5:10,6:5,7:7,8:8,9:9,10:5,11:11,12:12}
GRAHA_GUNAKARA = {"SUN":5,"MOON":5,"MARS":8,"MERCURY":5,"JUPITER":10,"VENUS":7,"SATURN":5}

RASIS_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
            "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# SAV interpretation thresholds
def _sav_label(pts: int) -> str:
    if pts >= 30: return "Strong"
    if pts >= 25: return "Good"
    if pts >= 20: return "Average"
    return "Weak"

def _sav_colour(pts: int) -> str:
    if pts >= 30: return "green"
    if pts >= 25: return "amber"
    if pts >= 20: return "yellow"
    return "red"

# ─────────────────────────────────────────────────────────────────────────────
# Planet position extraction from natal_chart response
# ─────────────────────────────────────────────────────────────────────────────

def _planet_positions_from_natal(natal_chart: dict) -> dict[str, int]:
    """
    Extract planet rasi (sign index 0-11) positions from the natal_chart response.
    Returns dict like {"SUN": 3, "MOON": 7, ..., "ASCENDANT": 1}  (0-based index)
    """
    pp = natal_chart.get("planet_positions", {})
    asc = natal_chart.get("ascendant", {})

    SIGN_MAP = {
        "Aries":0,"Taurus":1,"Gemini":2,"Cancer":3,"Leo":4,"Virgo":5,
        "Libra":6,"Scorpio":7,"Sagittarius":8,"Capricorn":9,"Aquarius":10,"Pisces":11,
    }

    result: dict[str, int] = {}
    name_map = {
        "Sun":"SUN","Moon":"MOON","Mars":"MARS","Mercury":"MERCURY",
        "Jupiter":"JUPITER","Venus":"VENUS","Saturn":"SATURN",
    }
    for eng, bav_key in name_map.items():
        sign = pp.get(eng, {}).get("sign", "")
        if sign in SIGN_MAP:
            result[bav_key] = SIGN_MAP[sign]

    asc_sign = asc.get("sign", "")
    if asc_sign in SIGN_MAP:
        result["ASCENDANT"] = SIGN_MAP[asc_sign]

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Core BAV calculation
# ─────────────────────────────────────────────────────────────────────────────

def _calc_bav_sign_wise(target_planet: str, positions: dict[str, int]) -> list[int]:
    """
    Returns 12-element list: bindu count per sign (index 0=Aries … 11=Pisces).
    Tamil rules; max 8 bindus per rasi (Parasara cap).
    """
    chart = [0] * 12
    rules = BAV_RULES.get(target_planet, {})
    for contributor, house_offsets in rules.items():
        if contributor not in positions:
            continue
        contrib_pos = positions[contributor]   # 0-based sign index
        for offset in house_offsets:
            target_idx = (contrib_pos + offset - 1) % 12
            chart[target_idx] += 1
    return [min(v, 8) for v in chart]


def _sign_to_house_wise(sign_chart: list[int], lagna_sign_idx: int) -> list[int]:
    """
    Convert sign-wise array to house-wise array using lagna sign index (0-based).
    House 1 = lagna sign, House 2 = lagna+1, etc.
    """
    return [sign_chart[(lagna_sign_idx + h) % 12] for h in range(12)]


# ─────────────────────────────────────────────────────────────────────────────
# Shodhana (reduction)
# ─────────────────────────────────────────────────────────────────────────────

def _trikona_shodhana(bav: list[int]) -> list[int]:
    """Apply Trikona shodhana to a sign-wise BAV chart."""
    chart = list(bav)
    for group in TRIKONA_GROUPS:
        idxs = [g - 1 for g in group]
        vals = [chart[i] for i in idxs]
        zeros = sum(1 for v in vals if v == 0)
        if zeros >= 2:
            for i in idxs: chart[i] = 0
        elif zeros >= 1:
            pass  # no reduction
        elif vals[0] == vals[1] == vals[2]:
            for i in idxs: chart[i] = 0
        else:
            mn = min(vals)
            for i in idxs: chart[i] = max(0, chart[i] - mn)
    return chart


def _ekadhipatya_shodhana(bav: list[int], occupancy: dict[int, list[str]]) -> list[int]:
    """Apply Ekadhipatya shodhana to a sign-wise BAV chart."""
    chart = list(bav)
    for sign_a, sign_b in EKADHIPATYA_PAIRS:
        ai, bi = sign_a - 1, sign_b - 1
        av, bv = chart[ai], chart[bi]
        if av == 0 or bv == 0:
            continue
        a_occ = len(occupancy.get(sign_a, [])) > 0
        b_occ = len(occupancy.get(sign_b, [])) > 0
        if a_occ and b_occ:
            continue
        if not a_occ and not b_occ:
            if av == bv:
                chart[ai] = chart[bi] = 0
            else:
                low = min(av, bv)
                chart[ai] = chart[bi] = low
        elif a_occ and not b_occ:
            chart[bi] = av if bv > av else 0
        elif b_occ and not a_occ:
            chart[ai] = bv if av > bv else 0
    return chart


def _shodhya_pinda(reduced_bav: list[int], occupancy: dict[int, list[str]], planet_key: str) -> dict:
    """Compute Shodhya Pinda for one planet's reduced BAV."""
    rasi_p = 0
    graha_p = 0
    for s in range(12):
        sign_num = s + 1
        b = reduced_bav[s]
        rasi_p += b * RASI_GUNAKARA[sign_num]
        for occ in occupancy.get(sign_num, []):
            if occ in GRAHA_GUNAKARA:
                graha_p += b * GRAHA_GUNAKARA[occ]
    total = rasi_p + graha_p
    rem = total % 27
    nak_idx = 26 if rem == 0 else rem - 1
    NAKS = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
            "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
            "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
            "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
            "Purva Bhadrapada","Uttara Bhadrapada","Revati"]
    return {
        "rasi_pinda":   rasi_p,
        "graha_pinda":  graha_p,
        "shodhya_pinda": total,
        "trigger_nakshatra": NAKS[nak_idx],
    }


# ─────────────────────────────────────────────────────────────────────────────
# In-process cache
# ─────────────────────────────────────────────────────────────────────────────

_bav_cache: dict[str, dict] = {}

def _build_matrix_8x8(
    target_planet: str,
    positions: dict[str, int],
    lagna_idx: int,
) -> list[list[int]]:
    """8×12 contribution matrix (contributors × houses) for one BAV planet."""
    rows: list[list[int]] = []
    rules = BAV_RULES.get(target_planet, {})
    for contributor in BAV_CONTRIBUTORS:
        row = [0] * 12
        if contributor not in positions:
            rows.append(row)
            continue
        ref_rasi = positions[contributor] + 1  # 1-based
        benefic = rules.get(contributor, [])
        for house in range(1, 13):
            house_rasi = ((lagna_idx + house - 1) % 12) + 1
            rel = house_rasi - ref_rasi + 1
            if rel <= 0:
                rel += 12
            if rel in benefic:
                row[house - 1] = 1
        rows.append(row)
    return rows


def _natal_key(natal_chart: dict) -> str:
    bd = natal_chart.get("birth_data", {})
    fp = chart_fingerprint(natal_chart)
    return f"tamil-v2|{bd.get('dob')}|{bd.get('tob')}|{bd.get('lat')}|{bd.get('lon')}|{fp}"


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def calculate_ashtakavarga(natal_chart: dict) -> dict:
    """
    Calculate complete Ashtakavarga for a natal chart.

    Returns
    -------
    {
      "bav": {
        "SUN":  {"sign_wise": [int*12], "house_wise": [int*12], "total": int,
                 "trikona_reduced": [...], "ekadhipatya_reduced": [...],
                 "shodhya_pinda": {...}},
        ...
      },
      "sav": {
        "sign_wise":  [int*12],
        "house_wise": [int*12],   ← primary array for transit scoring
        "total":      int,
        "by_house":   [{house, sign, sav_points, label, colour}, ...]
      },
      "lagna_sign_idx": int,
      "lagna_sign":     str,
    }
    """
    key = _natal_key(natal_chart)
    if key in _bav_cache:
        return _bav_cache[key]

    positions = _planet_positions_from_natal(natal_chart)
    if not positions:
        return {}

    lagna_idx = positions.get("ASCENDANT", 0)

    # Build occupancy map (sign_num 1-based → list of planets)
    occupancy: dict[int, list[str]] = {}
    for planet, sign_idx in positions.items():
        sign_num = sign_idx + 1
        occupancy.setdefault(sign_num, []).append(planet)

    bav_out: dict[str, dict] = {}
    matrix_out: dict[str, list[list[int]]] = {}
    sav_sign = [0] * 12

    for planet in ["SUN","MOON","MARS","MERCURY","JUPITER","VENUS","SATURN","ASCENDANT"]:
        sign_wise  = _calc_bav_sign_wise(planet, positions)
        house_wise = _sign_to_house_wise(sign_wise, lagna_idx)
        total      = sum(sign_wise)

        matrix_out[planet] = _build_matrix_8x8(planet, positions, lagna_idx)

        # Shodhana (only for 7 planets, not Ascendant)
        trikona   = _trikona_shodhana(sign_wise) if planet != "ASCENDANT" else sign_wise
        ekadhipatya = _ekadhipatya_shodhana(trikona, occupancy) if planet != "ASCENDANT" else sign_wise
        pinda     = _shodhya_pinda(ekadhipatya, occupancy, planet) if planet != "ASCENDANT" else {}

        bav_out[planet] = {
            "sign_wise":            sign_wise,
            "house_wise":           house_wise,
            "total":                total,
            "trikona_reduced":      trikona,
            "ekadhipatya_reduced":  ekadhipatya,
            "shodhya_pinda":        pinda,
        }

        # Accumulate SAV (7 planets only, not Ascendant)
        if planet in SAV_PLANETS:
            for i in range(12):
                sav_sign[i] += sign_wise[i]

    sav_house = _sign_to_house_wise(sav_sign, lagna_idx)
    sav_house = [min(v, 54) for v in sav_house]

    by_house = [
        {
            "house":      h + 1,
            "sign":       RASIS_EN[(lagna_idx + h) % 12],
            "sav_points": sav_house[h],
            "label":      _sav_label(sav_house[h]),
            "colour":     _sav_colour(sav_house[h]),
        }
        for h in range(12)
    ]

    # Positions for Prokerala grid (1-based rasi numbers)
    planetary_positions = {k: v + 1 for k, v in positions.items()}

    result = {
        "bav":           bav_out,
        "sav": {
            "sign_wise":  sav_sign,
            "house_wise": sav_house,
            "total":      sum(sav_house),
            "by_house":   by_house,
        },
        "matrix_8x8":    matrix_out,
        "planetary_positions": planetary_positions,
        "lagna_sign_idx": lagna_idx,
        "lagna_sign":     RASIS_EN[lagna_idx],
        "rules":          "tamil",
    }

    _bav_cache[key] = result
    return result


def sav_for_transit_scoring(natal_chart: dict) -> list[int]:
    """
    Returns SAV house-wise [H1..H12] for use in transit_score_agent.
    High SAV (≥30) boosts transit results; low SAV (<22) dampens them.
    """
    try:
        av = calculate_ashtakavarga(natal_chart)
        return av.get("sav", {}).get("house_wise", [28] * 12)
    except Exception:
        return [28] * 12


def bav_context_for_narrator(natal_chart: dict) -> str:
    """Build compact text block for chat/forecast system prompts."""
    try:
        av = calculate_ashtakavarga(natal_chart)
        sav = av["sav"]["by_house"]
        lines = ["=== ASHTAKAVARGA — SAV House Scores ==="]
        for h in sav:
            lines.append(
                f"  H{h['house']:02d} {h['sign']:<14} SAV={h['sav_points']:2d}  [{h['label']}]"
            )
        strong  = [h for h in sav if h["sav_points"] >= 30]
        weak    = [h for h in sav if h["sav_points"] < 22]
        if strong:
            strong_h = ", ".join(f"H{h['house']}" for h in strong)
            lines.append(f"Strongest houses (SAV≥30): {strong_h}")
        if weak:
            weak_h = ", ".join(f"H{h['house']}" for h in weak)
            lines.append(f"Weakest houses (SAV<22): {weak_h}")
        lines.append("(Higher SAV = better results when planets transit that house)")
        return "\n".join(lines)
    except Exception as e:
        return f"[Ashtakavarga unavailable: {e}]"
