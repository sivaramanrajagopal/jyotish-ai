"""
transit_score_agent.py
======================
Deterministic Vedic transit scoring engine.

Ported directly from:
  https://huggingface.co/spaces/sivaramrb901/Astrology-House-Connections
  (app.py + house_lord_analysis.py)

Main entry point:
    score_all_houses(natal_chart: dict, transit_date: str | None) -> dict

Input  : the /natal-chart response (contains birth_data.lat/lon/dob/tob/tz_offset)
Output : {
    "houses": {1: {...}, 2: {...}, ... 12: {...}},
    "overall_health": {...},
    "transit_analysis": [...],   # per-planet detail
    "house_rankings": [...],     # sorted by activation
}

Cache: in-process dict keyed by (dob+tob+lat+lon+transit_date).
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Optional

import swisseph as swe
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ─────────────────────────────────────────────────────────────────────────────
# Constants (identical to HF Space)
# ─────────────────────────────────────────────────────────────────────────────

RASIS = ["Mesha", "Rishaba", "Mithuna", "Kataka", "Simha", "Kanni",
         "Thula", "Vrischika", "Dhanus", "Makara", "Kumbha", "Meena"]

RASIS_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

SIGN_LORDS = {
    "Mesha": "Mars",   "Rishaba": "Venus",   "Mithuna": "Mercury",
    "Kataka": "Moon",  "Simha": "Sun",       "Kanni": "Mercury",
    "Thula": "Venus",  "Vrischika": "Mars",   "Dhanus": "Jupiter",
    "Makara": "Saturn","Kumbha": "Saturn",   "Meena": "Jupiter",
}

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati",
]
_NAK_LORDS_CYCLE = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
NAK_TO_LORD = {n: _NAK_LORDS_CYCLE[i % 9] for i, n in enumerate(NAKSHATRAS)}

PLANETARY_STATES = {
    "Sun":     {"exalted": "Mesha",    "debilitated": "Thula",    "own": ["Simha"]},
    "Moon":    {"exalted": "Rishaba",  "debilitated": "Vrischika","own": ["Kataka"]},
    "Mars":    {"exalted": "Makara",   "debilitated": "Kataka",   "own": ["Mesha","Vrischika"]},
    "Mercury": {"exalted": "Kanni",    "debilitated": "Meena",    "own": ["Mithuna","Kanni"]},
    "Jupiter": {"exalted": "Kataka",   "debilitated": "Makara",   "own": ["Dhanus","Meena"]},
    "Venus":   {"exalted": "Meena",    "debilitated": "Kanni",    "own": ["Rishaba","Thula"]},
    "Saturn":  {"exalted": "Thula",    "debilitated": "Mesha",    "own": ["Makara","Kumbha"]},
}

FRIENDSHIPS = {
    "Sun":     {"friends": ["Moon","Mars","Jupiter"],      "enemies": ["Venus","Saturn"]},
    "Moon":    {"friends": ["Sun","Mercury"],              "enemies": []},
    "Mars":    {"friends": ["Sun","Moon","Jupiter"],       "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun","Venus"],                "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun","Moon","Mars"],          "enemies": ["Mercury","Venus"]},
    "Venus":   {"friends": ["Mercury","Saturn"],           "enemies": ["Sun","Moon"]},
    "Saturn":  {"friends": ["Mercury","Venus"],            "enemies": ["Sun","Moon","Mars"]},
}

PLANETARY_NATURE = {
    "Sun":     {"type": "malefic"},
    "Moon":    {"type": "benefic"},
    "Mars":    {"type": "malefic"},
    "Mercury": {"type": "neutral"},
    "Jupiter": {"type": "benefic"},
    "Venus":   {"type": "benefic"},
    "Saturn":  {"type": "malefic"},
    "Rahu":    {"type": "malefic"},
    "Ketu":    {"type": "malefic"},
}

HOUSE_CLASSIFICATIONS = {
    "kendra":   [1, 4, 7, 10],
    "trikona":  [1, 5, 9],
    "upachaya": [3, 6, 10, 11],
    "dusthana": [6, 8, 12],
}

HOUSE_SIGNIFICATIONS = {
    1:  {"area": "Self & Personality",        "themes": ["health","appearance","vitality","overall well-being"]},
    2:  {"area": "Wealth & Family",           "themes": ["finances","family","speech","food","assets"]},
    3:  {"area": "Courage & Skills",          "themes": ["communication","short travels","siblings","skills","courage"]},
    4:  {"area": "Home & Happiness",          "themes": ["property","vehicles","mother","happiness","education"]},
    5:  {"area": "Creativity & Children",     "themes": ["creativity","children","romance","speculation","intellect"]},
    6:  {"area": "Health & Competition",      "themes": ["disease","debts","enemies","competition","service"]},
    7:  {"area": "Partnership & Marriage",    "themes": ["spouse","business partnerships","public relations"]},
    8:  {"area": "Transformation & Longevity","themes": ["sudden events","inheritance","occult","research","longevity"]},
    9:  {"area": "Fortune & Wisdom",          "themes": ["luck","father","dharma","long travels","spirituality"]},
    10: {"area": "Career & Status",           "themes": ["profession","reputation","authority","government","karma"]},
    11: {"area": "Gains & Friendships",       "themes": ["income","friends","aspirations","elder siblings","profits"]},
    12: {"area": "Spirituality & Liberation", "themes": ["expenses","foreign lands","isolation","spirituality","losses"]},
}

HOUSE_EXPLANATIONS = {
    1:  {"name": "Self & Personality",        "simple": "your health, vitality, and how others see you"},
    2:  {"name": "Wealth & Family",           "simple": "your finances, family bonds, and speech"},
    3:  {"name": "Courage & Skills",          "simple": "your communication, courage, and siblings"},
    4:  {"name": "Home & Happiness",          "simple": "your home, mother, and inner peace"},
    5:  {"name": "Creativity & Children",     "simple": "your intelligence, creativity, and children"},
    6:  {"name": "Health & Competition",      "simple": "your health challenges, daily work, and obstacles"},
    7:  {"name": "Partnership & Marriage",    "simple": "your marriage, business partners, and relationships"},
    8:  {"name": "Transformation & Longevity","simple": "sudden changes, inheritance, and hidden matters"},
    9:  {"name": "Fortune & Wisdom",          "simple": "your luck, father, and higher learning"},
    10: {"name": "Career & Status",           "simple": "your career, reputation, and public life"},
    11: {"name": "Gains & Friendships",       "simple": "your income, friends, and wishes fulfilled"},
    12: {"name": "Spirituality & Liberation", "simple": "expenses, foreign lands, and spiritual liberation"},
}

# ─────────────────────────────────────────────────────────────────────────────
# Ephemeris helpers
# ─────────────────────────────────────────────────────────────────────────────

def _init_swe():
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def _get_chart_info(longitude: float, speed: Optional[float] = None) -> dict:
    pada = int(((longitude % (360 / 27)) / (360 / 27 / 4)) + 1)
    return {
        "longitude": longitude,
        "retrograde": (speed < 0) if speed is not None else None,
        "rasi": RASIS[int(longitude // 30)],
        "nakshatra": NAKSHATRAS[int((longitude % 360) // (360 / 27))],
        "pada": pada,
    }


def _get_planet_positions(jd: float, lat: float, lon: float) -> tuple[dict, float]:
    """Return (planet_data_dict, asc_deg)."""
    _init_swe()
    FLAGS = swe.FLG_SIDEREAL | swe.FLG_SPEED
    swe.set_topo(lon, lat, 0)
    results = {}

    for pid in range(0, 10):
        name = swe.get_planet_name(pid)
        lonlat = swe.calc_ut(jd, pid, FLAGS)[0]
        results[name] = _get_chart_info(lonlat[0], lonlat[3])

    rahu = swe.calc_ut(jd, swe.TRUE_NODE, FLAGS)[0]
    results["Rahu"] = _get_chart_info(rahu[0], rahu[3])
    results["Rahu"]["retrograde"] = True
    ketu_lon = (rahu[0] + 180.0) % 360.0
    results["Ketu"] = _get_chart_info(ketu_lon, rahu[3])
    results["Ketu"]["retrograde"] = True

    _, ascmc = swe.houses_ex(jd, lat, lon, b"P", flags=FLAGS)
    results["Ascendant"] = _get_chart_info(ascmc[0])

    return results, ascmc[0]


def _house_from_lon(longitude: float, asc_deg: float) -> int:
    lagna_rasi = int(asc_deg // 30)
    planet_rasi = int(longitude // 30)
    return (planet_rasi - lagna_rasi) % 12 + 1


def _planet_house_ownership(lagna_sign: str, planet_name: str) -> list[int]:
    try:
        lagna_idx = RASIS.index(lagna_sign)
    except ValueError:
        return []
    return [
        (i - lagna_idx) % 12 + 1
        for i, sign in enumerate(RASIS)
        if SIGN_LORDS.get(sign) == planet_name
    ]


def _nth_house_from(from_house: int, n: int) -> int:
    return ((from_house + n - 2) % 12) + 1


def _planet_aspects(planet: str, from_house: int) -> list[int]:
    aspects = {_nth_house_from(from_house, 7)}
    if planet == "Mars":
        aspects |= {_nth_house_from(from_house, 4), _nth_house_from(from_house, 8)}
    elif planet == "Jupiter":
        aspects |= {_nth_house_from(from_house, 5), _nth_house_from(from_house, 9)}
    elif planet == "Saturn":
        aspects |= {_nth_house_from(from_house, 3), _nth_house_from(from_house, 10)}
    return sorted(aspects)


def _planetary_state(planet: str, sign: str) -> str:
    if planet in ("Rahu", "Ketu", "Ascendant"):
        return "N/A"
    states = PLANETARY_STATES.get(planet, {})
    if sign == states.get("exalted"):       return "Exalted"
    if sign == states.get("debilitated"):   return "Debilitated"
    if sign in states.get("own", []):       return "Own Sign"
    sign_lord = SIGN_LORDS.get(sign, "")
    pf = FRIENDSHIPS.get(planet, {})
    if sign_lord in pf.get("friends", []):  return "Friend"
    if sign_lord in pf.get("enemies", []):  return "Enemy"
    return "Neutral"


# ─────────────────────────────────────────────────────────────────────────────
# Core connection analysis (exact port from HF Space)
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_connections(data: dict, asc_deg: float) -> list[dict]:
    lagna_sign = data["Ascendant"]["rasi"]
    planet_connections = []
    planets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

    for planet in planets:
        if planet not in data:
            continue
        pdata   = data[planet]
        lon     = pdata["longitude"]
        sign    = pdata["rasi"]
        nak     = pdata["nakshatra"]
        pada    = pdata["pada"]
        house   = _house_from_lon(lon, asc_deg)
        aspects = _planet_aspects(planet, house)

        nak_lord      = NAK_TO_LORD[nak]
        nak_lord_house = _house_from_lon(data[nak_lord]["longitude"], asc_deg) if nak_lord in data else "-"
        nak_lord_owns  = _planet_house_ownership(lagna_sign, nak_lord)

        sign_lord      = SIGN_LORDS[sign]
        sld            = data.get(sign_lord, {})
        sign_lord_house = _house_from_lon(sld["longitude"], asc_deg) if sld else "-"
        sign_lord_owns  = _planet_house_ownership(lagna_sign, sign_lord)

        planet_owns = _planet_house_ownership(lagna_sign, planet)
        state       = _planetary_state(planet, sign)

        all_houses: set = {house}
        all_houses.update(planet_owns)
        if nak_lord_house != "-":
            all_houses.add(nak_lord_house)
        all_houses.update(nak_lord_owns)
        if sign_lord_house != "-":
            all_houses.add(sign_lord_house)
        all_houses.update(sign_lord_owns)
        all_houses.update(aspects)

        planet_connections.append({
            "Planet":           planet,
            "Placed_House":     house,
            "Sign":             sign,
            "Sign_Lord":        sign_lord,
            "Nakshatra":        nak,
            "Pada":             pada,
            "Nak_Lord":         nak_lord,
            "State":            state,
            "Degree":           round(lon % 30, 2),
            "Retrograde":       "R" if pdata["retrograde"] else "-",
            "Planet_Owns":      planet_owns,
            "Nak_Lord_In":      nak_lord_house,
            "Nak_Lord_Owns":    nak_lord_owns,
            "Aspects":          aspects,
            "All_Connected_Houses": sorted(all_houses),
            "Total_Connections":    len(all_houses),
        })

    return planet_connections


# ─────────────────────────────────────────────────────────────────────────────
# Scoring functions (exact port from HF Space)
# ─────────────────────────────────────────────────────────────────────────────

def _dignity_score(state: str) -> float:
    return {"Exalted": 100, "Own Sign": 90, "Friend": 70,
            "Neutral": 50, "Enemy": 30, "Debilitated": 10, "N/A": 50}.get(state, 50)


def _house_quality_score(house: int) -> float:
    hc = HOUSE_CLASSIFICATIONS
    if house in hc["kendra"] and house in hc["trikona"]: return 100
    if house in hc["trikona"]:  return 90
    if house in hc["kendra"]:   return 80
    if house in hc["upachaya"]: return 70
    if house in hc["dusthana"]: return 30
    return 50


def _transit_score(planet: str, transit_house: int, natal_state: str, retrograde: bool) -> float:
    nature = PLANETARY_NATURE.get(planet, {"type": "neutral"})["type"]
    hs = _house_quality_score(transit_house)
    hc = HOUSE_CLASSIFICATIONS

    if nature == "benefic":
        if transit_house in hc["kendra"] + hc["trikona"]: hs += 10
        elif transit_house in hc["dusthana"]:              hs -= 5
    elif nature == "malefic":
        if transit_house in hc["upachaya"]:  hs += 10
        elif transit_house in hc["dusthana"]: hs += 5
        else:                                 hs -= 10

    ds    = _dignity_score(natal_state)
    retro = 0.9 if retrograde and planet not in ("Rahu", "Ketu") else 1.0
    return max(0, min(100, ((hs * 0.6) + (ds * 0.4)) * retro))


def _rag(score: float) -> dict:
    if score >= 70:
        return {"status": "GREEN",  "emoji": "🟢", "label": "Favourable",   "colour": "#27ae60"}
    if score >= 40:
        return {"status": "AMBER",  "emoji": "🟡", "label": "Mixed",        "colour": "#f39c12"}
    return {"status": "RED",    "emoji": "🔴", "label": "Challenging",  "colour": "#e74c3c"}


def _interpretation(planet: str, transit_house: int, activated_houses: list[int],
                    score: float, rag: dict) -> dict:
    area   = HOUSE_SIGNIFICATIONS[transit_house]["area"]
    themes = ", ".join(HOUSE_SIGNIFICATIONS[transit_house]["themes"][:3])

    if rag["status"] == "GREEN":
        impact = f"{planet} is favourably placed, bringing positive energy to {area}."
        advice = f"Good time to focus on {themes}. Take proactive steps."
    elif rag["status"] == "AMBER":
        impact = f"{planet} brings mixed influences to {area}. A balanced approach is needed."
        advice = f"Be mindful with {themes}. Neither push too hard nor neglect."
    else:
        impact = f"{planet} creates challenges in {area}. Patience and care are required."
        advice = f"Exercise caution with {themes}. Avoid major decisions."

    if len(activated_houses) > 5:
        impact += f" Wide activation across {len(activated_houses)} life areas."

    return {
        "impact": impact,
        "advice": advice,
        "life_areas": [HOUSE_SIGNIFICATIONS[h]["area"] for h in activated_houses[:3]],
    }


# ─────────────────────────────────────────────────────────────────────────────
# House lord analysis (port from house_lord_analysis.py)
# ─────────────────────────────────────────────────────────────────────────────

def _lord_position_type(houses_from_own: int) -> str:
    if houses_from_own == 12:          return "own_house"
    if houses_from_own in (4, 7, 10):  return "kendra_from_own"
    if houses_from_own in (5, 9):      return "trikona_from_own"
    if houses_from_own in (3, 6, 11):  return "upachaya_from_own"
    if houses_from_own in (6, 8, 12):  return "dusthana_from_own"
    return "neutral_from_own"


def _lord_strength(lord_data: dict, houses_from_own: int) -> dict:
    ds = _dignity_score(lord_data["State"])
    pos_scores = {12: 100, 4: 90, 7: 90, 10: 90, 5: 95, 9: 95,
                  3: 75, 11: 75, 2: 50, 6: 40, 8: 30}
    ps    = pos_scores.get(houses_from_own, 50)
    retro = 0.85 if lord_data["Retrograde"] == "R" else 1.0
    bonus = min(20, lord_data["Total_Connections"] * 2)
    return {
        "total":             round(((ds * 0.5) + (ps * 0.4) + bonus) * retro, 1),
        "dignity_component": ds,
        "position_component": ps,
        "connection_bonus":  bonus,
    }


def _house_strength(house_num: int, lord_data: dict, planets_in: list[str],
                    planets_asp: list[str], houses_from_own: int) -> dict:
    pos_scores = {12: 100, 4: 90, 7: 90, 10: 90, 5: 95, 9: 95,
                  3: 75, 11: 75, 2: 50, 6: 40, 8: 30}
    lp = pos_scores.get(houses_from_own, 50)
    ld = _dignity_score(lord_data["State"])

    benefic = sum(1 for p in planets_in + planets_asp
                  if PLANETARY_NATURE.get(p, {}).get("type") == "benefic")
    malefic = sum(1 for p in planets_in + planets_asp
                  if PLANETARY_NATURE.get(p, {}).get("type") == "malefic")
    bs = min(100, benefic * 30)
    mp = min(50,  malefic * 12)

    hc = HOUSE_CLASSIFICATIONS
    hn = 60
    if house_num in hc["kendra"]:   hn = 85
    if house_num in hc["trikona"]:  hn = 90
    if house_num in hc["dusthana"]: hn = 45
    if house_num in hc["upachaya"]: hn = 75

    total = max(0, min(100, lp * 0.35 + ld * 0.25 + bs * 0.20 - mp * 0.15 + hn * 0.15))
    return {"total": round(total, 1), "lord_position": lp, "lord_dignity": ld,
            "benefic_influence": bs, "malefic_influence": mp, "house_nature": hn}


def _analyze_house_lords(natal_data: dict, planet_connections: list[dict], asc_deg: float) -> dict:
    lagna_sign = natal_data["Ascendant"]["rasi"]
    try:
        lagna_idx = RASIS.index(lagna_sign)
    except ValueError:
        return {}

    analysis = {}
    for house_num in range(1, 13):
        house_sign_idx = (lagna_idx + house_num - 1) % 12
        house_sign     = RASIS[house_sign_idx]
        house_lord     = SIGN_LORDS[house_sign]

        lord_data = next((pc for pc in planet_connections if pc["Planet"] == house_lord), None)
        if not lord_data:
            continue

        lord_house    = lord_data["Placed_House"]
        houses_from   = ((lord_house - house_num) % 12) or 12
        position_type = _lord_position_type(houses_from)

        planets_in  = [pc["Planet"] for pc in planet_connections if pc["Placed_House"] == house_num]
        planets_asp = [pc["Planet"] for pc in planet_connections if house_num in pc["Aspects"]]

        ls = _lord_strength(lord_data, houses_from)
        hs = _house_strength(house_num, lord_data, planets_in, planets_asp, houses_from)

        analysis[house_num] = {
            "house_sign":          house_sign,
            "house_sign_en":       RASIS_EN[house_sign_idx],
            "lord":                house_lord,
            "lord_placed_in_house": lord_house,
            "lord_placed_in_sign": lord_data["Sign"],
            "lord_dignity":        lord_data["State"],
            "lord_degree":         lord_data["Degree"],
            "lord_retrograde":     lord_data["Retrograde"] == "R",
            "lord_nakshatra":      lord_data["Nakshatra"],
            "lord_pada":           lord_data["Pada"],
            "houses_from_own":     houses_from,
            "position_type":       position_type,
            "planets_in_house":    planets_in,
            "planets_aspecting":   planets_asp,
            "lord_strength":       ls,
            "house_strength":      hs,
            "rag":                 _rag(hs["total"]),
        }

    return analysis


# ─────────────────────────────────────────────────────────────────────────────
# In-process cache
# ─────────────────────────────────────────────────────────────────────────────

_score_cache: dict[str, dict] = {}


def _cache_key(natal_chart: dict, transit_date: str) -> str:
    bd = natal_chart.get("birth_data", {})
    return f"{bd.get('dob')}|{bd.get('tob')}|{bd.get('lat')}|{bd.get('lon')}|{transit_date}"


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def score_all_houses(natal_chart: dict, transit_date: Optional[str] = None) -> dict:
    """
    Score all 12 houses based on natal chart + today's (or given) transits.

    Parameters
    ----------
    natal_chart : dict
        The /natal-chart response. Must contain `birth_data` with:
        dob (YYYY-MM-DD), tob (HH:MM), lat, lon, tz_offset (float, UTC+).
    transit_date : str | None
        YYYY-MM-DD.  Defaults to today.

    Returns
    -------
    dict with keys: houses, overall_health, transit_analysis, house_rankings
    """
    if transit_date is None:
        transit_date = datetime.date.today().isoformat()

    ck = _cache_key(natal_chart, transit_date)
    if ck in _score_cache:
        return _score_cache[ck]

    bd = natal_chart.get("birth_data", {})
    dob      = bd.get("dob", "")
    tob      = bd.get("tob", "")
    lat      = float(bd.get("lat", 13.08))
    lon      = float(bd.get("lon", 80.27))
    tz_off   = float(bd.get("tz_offset", 5.5))

    # ── Natal chart positions ──────────────────────────────────────────────
    dob_dt  = datetime.datetime.strptime(dob, "%Y-%m-%d")
    tob_dt  = datetime.datetime.strptime(tob[:5], "%H:%M")
    local_dt = datetime.datetime(dob_dt.year, dob_dt.month, dob_dt.day,
                                 tob_dt.hour, tob_dt.minute)
    utc_dt   = local_dt - datetime.timedelta(hours=tz_off)
    natal_jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                          utc_dt.hour + utc_dt.minute / 60.0)

    natal_data, natal_asc_deg = _get_planet_positions(natal_jd, lat, lon)
    natal_connections         = _analyze_connections(natal_data, natal_asc_deg)
    natal_dict                = {pc["Planet"]: pc for pc in natal_connections}

    # ── House lord analysis (natal) ────────────────────────────────────────
    house_lord_analysis = _analyze_house_lords(natal_data, natal_connections, natal_asc_deg)

    # ── Transit positions ──────────────────────────────────────────────────
    td_dt     = datetime.datetime.strptime(transit_date, "%Y-%m-%d")
    transit_jd = swe.julday(td_dt.year, td_dt.month, td_dt.day, 12.0)  # noon UTC
    transit_data, _ = _get_planet_positions(transit_jd, lat, lon)

    # ── Per-planet transit scoring ─────────────────────────────────────────
    detailed: list[dict] = []
    all_scores: list[float] = []
    house_act_count: dict[int, int]     = defaultdict(int)
    house_act_by:    dict[int, list[str]] = defaultdict(list)

    planets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

    for planet in planets:
        if planet not in transit_data or planet not in natal_dict:
            continue

        tp       = transit_data[planet]
        np       = natal_dict[planet]
        t_house  = _house_from_lon(tp["longitude"], natal_asc_deg)
        nak      = tp["nakshatra"]
        pada     = tp["pada"]
        pada_lord = NAK_TO_LORD[nak]

        # activated houses
        activated = {t_house}
        activated.update(_planet_aspects(planet, t_house))
        if pada_lord in natal_dict:
            ld = natal_dict[pada_lord]
            activated.add(ld["Placed_House"])
            activated.update(ld["Planet_Owns"])
        activated_sorted = sorted(activated)

        score = _transit_score(planet, t_house, np["State"], tp["retrograde"])
        all_scores.append(score)
        rag   = _rag(score)
        interp = _interpretation(planet, t_house, activated_sorted, score, rag)

        detailed.append({
            "planet":           planet,
            "natal_house":      np["Placed_House"],
            "transit_house":    t_house,
            "transit_sign":     tp["rasi"],
            "transit_sign_en":  RASIS_EN[RASIS.index(tp["rasi"])],
            "transit_degree":   round(tp["longitude"] % 30, 2),
            "nakshatra":        nak,
            "pada":             pada,
            "pada_lord":        pada_lord,
            "activated_houses": activated_sorted,
            "score":            round(score, 1),
            "rag":              rag,
            "interpretation":   interp,
            "retrograde":       tp["retrograde"],
        })

        for h in activated_sorted:
            house_act_count[h] += 1
            house_act_by[h].append(planet)

    # ── Overall health ─────────────────────────────────────────────────────
    avg = round(sum(all_scores) / len(all_scores), 1) if all_scores else 50.0
    overall = {
        "average_score": avg,
        "rag":           _rag(avg),
        "green_count":   sum(1 for s in all_scores if s >= 70),
        "amber_count":   sum(1 for s in all_scores if 40 <= s < 70),
        "red_count":     sum(1 for s in all_scores if s < 40),
        "total_planets": len(all_scores),
    }

    # ── House activation ranking ───────────────────────────────────────────
    ranked: list[dict] = []
    for house in range(1, 13):
        count   = house_act_count.get(house, 0)
        planets_act = house_act_by.get(house, [])
        qs      = _house_quality_score(house)
        ws      = round((qs * 0.4) + (min(count * 20, 100) * 0.6), 1)
        ranked.append({
            "house":            house,
            "area":             HOUSE_SIGNIFICATIONS[house]["area"],
            "themes":           HOUSE_SIGNIFICATIONS[house]["themes"],
            "activation_count": count,
            "planets":          planets_act,
            "quality_score":    qs,
            "weighted_score":   ws,
            "rag":              _rag(ws),
        })
    ranked.sort(key=lambda x: x["weighted_score"], reverse=True)

    # ── Combine house lord scores + transit activation for final house score
    houses_out: dict[int, dict] = {}
    for h in range(1, 13):
        hl   = house_lord_analysis.get(h, {})
        rank = next((r for r in ranked if r["house"] == h), {})

        # Weighted blend: 60% natal house lord strength, 40% transit activation
        natal_score   = hl.get("house_strength", {}).get("total", 50.0)
        transit_ws    = rank.get("weighted_score", 50.0)
        blended       = round(natal_score * 0.6 + transit_ws * 0.4, 1)

        houses_out[h] = {
            "house_num":          h,
            "area":               HOUSE_SIGNIFICATIONS[h]["area"],
            "name":               HOUSE_EXPLANATIONS[h]["name"],
            "simple":             HOUSE_EXPLANATIONS[h]["simple"],
            "themes":             HOUSE_SIGNIFICATIONS[h]["themes"],
            "score":              blended,
            "natal_score":        natal_score,
            "transit_score":      transit_ws,
            "rag":                _rag(blended),
            "lord":               hl.get("lord", ""),
            "lord_placed_house":  hl.get("lord_placed_in_house", ""),
            "lord_dignity":       hl.get("lord_dignity", ""),
            "lord_retrograde":    hl.get("lord_retrograde", False),
            "planets_in_house":   hl.get("planets_in_house", []),
            "planets_aspecting":  hl.get("planets_aspecting", []),
            "transit_planets":    rank.get("planets", []),
            "activation_count":   rank.get("activation_count", 0),
            "house_sign":         hl.get("house_sign", ""),
            "house_sign_en":      hl.get("house_sign_en", ""),
        }

    result = {
        "houses":           houses_out,
        "overall_health":   overall,
        "transit_analysis": detailed,
        "house_rankings":   ranked,
        "transit_date":     transit_date,
        "lagna":            natal_data["Ascendant"]["rasi"],
        "lagna_en":         RASIS_EN[RASIS.index(natal_data["Ascendant"]["rasi"])],
    }

    _score_cache[ck] = result
    return result


def build_house_context(scores: dict, house_num: int) -> str:
    """
    Build a concise text block for the narrator to use when generating
    the AI interpretation for a specific house.
    """
    h   = scores["houses"].get(house_num, {})
    ta  = [p for p in scores["transit_analysis"] if house_num in p.get("activated_houses", [])]
    oh  = scores["overall_health"]

    lines = [
        f"HOUSE {house_num}: {h.get('name')} ({h.get('simple')})",
        f"Score: {h.get('score')}/100  [{h.get('rag', {}).get('label')}]",
        f"Natal house lord: {h.get('lord')} in H{h.get('lord_placed_house')} "
        f"({h.get('lord_dignity')}{', Retrograde' if h.get('lord_retrograde') else ''})",
        f"House sign: {h.get('house_sign_en')}",
    ]
    if h.get("planets_in_house"):
        lines.append(f"Planets in house: {', '.join(h['planets_in_house'])}")
    if h.get("planets_aspecting"):
        lines.append(f"Planets aspecting: {', '.join(h['planets_aspecting'])}")
    if ta:
        lines.append("Active transits through this house:")
        for p in ta:
            lines.append(
                f"  {p['planet']} in H{p['transit_house']} ({p['transit_sign_en']}) "
                f"score={p['score']} [{p['rag']['label']}] — {p['interpretation']['impact']}"
            )
    lines.append(f"Overall transit health today: {oh['average_score']}/100 [{oh['rag']['label']}]")
    return "\n".join(lines)
