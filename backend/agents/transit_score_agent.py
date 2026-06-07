"""
transit_score_agent.py
======================
Deterministic Vedic transit scoring engine following Parasara's Gochara rules.

References: Brihat Parashara Hora Shastra — Chapter on Gochara (Transit)

CORRECT APPROACH:
  - Transits are evaluated from the NATAL MOON SIGN (Chandra Rasi), not Lagna
  - Each planet has specific auspicious positions counted from natal Moon
  - Vedha (obstruction): another planet at the Vedha point cancels the benefit
  - Sun–Saturn and Moon–Mercury are exempt from mutual Vedha
  - House scores = 60% natal lord strength + 40% Gochara result
  - "Transit Activity" shows only planets DIRECTLY in or DIRECTLY aspecting a house

Main entry point:
    score_all_houses(natal_chart: dict, transit_date: str | None) -> dict
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from pathlib import Path
from typing import Optional

import ephemeris as swe
from ephemeris import RAHU_NODE
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ─────────────────────────────────────────────────────────────────────────────
# Vedic constants
# ─────────────────────────────────────────────────────────────────────────────

RASIS = ["Mesha","Rishaba","Mithuna","Kataka","Simha","Kanni",
         "Thula","Vrischika","Dhanus","Makara","Kumbha","Meena"]

RASIS_EN = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
            "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

SIGN_LORDS = {
    "Mesha":"Mars", "Rishaba":"Venus", "Mithuna":"Mercury",
    "Kataka":"Moon","Simha":"Sun",    "Kanni":"Mercury",
    "Thula":"Venus","Vrischika":"Mars","Dhanus":"Jupiter",
    "Makara":"Saturn","Kumbha":"Saturn","Meena":"Jupiter",
}

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta","Shatabhisha",
    "Purva Bhadrapada","Uttara Bhadrapada","Revati",
]
_NK = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
NAK_TO_LORD = {n: _NK[i % 9] for i, n in enumerate(NAKSHATRAS)}

PLANETARY_STATES = {
    "Sun":    {"exalted":"Mesha",   "debilitated":"Thula",    "own":["Simha"]},
    "Moon":   {"exalted":"Rishaba", "debilitated":"Vrischika","own":["Kataka"]},
    "Mars":   {"exalted":"Makara",  "debilitated":"Kataka",   "own":["Mesha","Vrischika"]},
    "Mercury":{"exalted":"Kanni",   "debilitated":"Meena",    "own":["Mithuna","Kanni"]},
    "Jupiter":{"exalted":"Kataka",  "debilitated":"Makara",   "own":["Dhanus","Meena"]},
    "Venus":  {"exalted":"Meena",   "debilitated":"Kanni",    "own":["Rishaba","Thula"]},
    "Saturn": {"exalted":"Thula",   "debilitated":"Mesha",    "own":["Makara","Kumbha"]},
}

FRIENDSHIPS = {
    "Sun":    {"friends":["Moon","Mars","Jupiter"],    "enemies":["Venus","Saturn"]},
    "Moon":   {"friends":["Sun","Mercury"],            "enemies":[]},
    "Mars":   {"friends":["Sun","Moon","Jupiter"],     "enemies":["Mercury"]},
    "Mercury":{"friends":["Sun","Venus"],              "enemies":["Moon"]},
    "Jupiter":{"friends":["Sun","Moon","Mars"],        "enemies":["Mercury","Venus"]},
    "Venus":  {"friends":["Mercury","Saturn"],         "enemies":["Sun","Moon"]},
    "Saturn": {"friends":["Mercury","Venus"],          "enemies":["Sun","Moon","Mars"]},
}

PLANETARY_NATURE = {
    "Sun":"malefic","Moon":"benefic","Mars":"malefic","Mercury":"neutral",
    "Jupiter":"benefic","Venus":"benefic","Saturn":"malefic",
    "Rahu":"malefic","Ketu":"malefic",
}

HOUSE_CLASSIFICATIONS = {
    "kendra":[1,4,7,10],"trikona":[1,5,9],
    "upachaya":[3,6,10,11],"dusthana":[6,8,12],
}

HOUSE_SIGNIFICATIONS = {
    1: {"area":"Self & Personality",         "themes":["health","appearance","vitality","overall well-being"]},
    2: {"area":"Wealth & Family",            "themes":["finances","family","speech","food","assets"]},
    3: {"area":"Courage & Skills",           "themes":["communication","short travels","siblings","skills","courage"]},
    4: {"area":"Home & Happiness",           "themes":["property","vehicles","mother","happiness","education"]},
    5: {"area":"Creativity & Children",      "themes":["creativity","children","romance","speculation","intellect"]},
    6: {"area":"Health & Competition",       "themes":["disease","debts","enemies","competition","service"]},
    7: {"area":"Partnership & Marriage",     "themes":["spouse","business partnerships","public relations"]},
    8: {"area":"Transformation & Longevity","themes":["sudden events","inheritance","occult","research","longevity"]},
    9: {"area":"Fortune & Wisdom",           "themes":["luck","father","dharma","long travels","spirituality"]},
    10:{"area":"Career & Status",            "themes":["profession","reputation","authority","government","karma"]},
    11:{"area":"Gains & Friendships",        "themes":["income","friends","aspirations","elder siblings","profits"]},
    12:{"area":"Spirituality & Liberation",  "themes":["expenses","foreign lands","isolation","spirituality","losses"]},
}

HOUSE_EXPLANATIONS = {
    1: {"name":"Self & Personality",         "simple":"your health, vitality, and how others see you"},
    2: {"name":"Wealth & Family",            "simple":"your finances, family bonds, and speech"},
    3: {"name":"Courage & Skills",           "simple":"your communication, courage, and siblings"},
    4: {"name":"Home & Happiness",           "simple":"your home, mother, and inner peace"},
    5: {"name":"Creativity & Children",      "simple":"your intelligence, creativity, and children"},
    6: {"name":"Health & Competition",       "simple":"your health challenges, daily work, and obstacles"},
    7: {"name":"Partnership & Marriage",     "simple":"your marriage, business partners, and relationships"},
    8: {"name":"Transformation & Longevity","simple":"sudden changes, inheritance, and hidden matters"},
    9: {"name":"Fortune & Wisdom",           "simple":"your luck, father, and higher learning"},
    10:{"name":"Career & Status",            "simple":"your career, reputation, and public life"},
    11:{"name":"Gains & Friendships",        "simple":"your income, friends, and wishes fulfilled"},
    12:{"name":"Spirituality & Liberation",  "simple":"expenses, foreign lands, and spiritual liberation"},
}

# Natural significators (Karakas) for each house
HOUSE_KARAKAS = {
    1: ["Sun"],
    2: ["Jupiter","Mercury"],
    3: ["Mars"],
    4: ["Moon"],
    5: ["Jupiter"],
    6: ["Mars","Saturn"],
    7: ["Venus"],
    8: ["Saturn"],
    9: ["Jupiter","Sun"],
    10:["Mercury","Sun","Jupiter","Saturn"],
    11:["Jupiter"],
    12:["Saturn","Ketu"],
}

# ─────────────────────────────────────────────────────────────────────────────
# PARASARA GOCHARA RULES (from natal Moon sign)
# Position 1 = natal Moon's sign, 2 = next sign, etc.
# ─────────────────────────────────────────────────────────────────────────────

GOCHARA_AUSPICIOUS: dict[str, set[int]] = {
    "Sun":     {3, 6, 10, 11},
    "Moon":    {1, 3, 6, 7, 10, 11},
    "Mars":    {3, 6, 11},
    "Mercury": {2, 4, 6, 8, 10, 11},
    "Jupiter": {2, 5, 7, 9, 11},
    "Venus":   {1, 2, 3, 4, 5, 8, 9, 11, 12},
    "Saturn":  {3, 6, 11},
    "Rahu":    {3, 6, 11},
    "Ketu":    {3, 6, 11},
}

# Vedha (obstruction) table: {planet: {auspicious_pos: vedha_pos}}
# If another planet occupies vedha_pos, the auspiciousness is cancelled.
VEDHA_POINTS: dict[str, dict[int, int]] = {
    "Sun":     {3: 9,  6: 12, 10:  4, 11:  5},
    "Moon":    {1: 5,  3:  9,  6: 12,  7:  2, 10: 4, 11: 8},
    "Mars":    {3: 12, 6:  9, 11:  5},
    "Mercury": {2: 5,  4:  3,  6:  9,  8:  1, 10: 8, 11: 8},
    "Jupiter": {2: 12, 5:  4,  7:  3,  9: 10, 11: 8},
    "Venus":   {1: 8,  2:  7,  3:  1,  4: 10,  5: 9, 8: 5, 9: 11, 11: 6, 12: 3},
    "Saturn":  {3: 12, 6:  9, 11:  5},
    "Rahu":    {3: 9,  6: 12, 11:  5},
    "Ketu":    {3: 9,  6: 12, 11:  5},
}

# Sun–Saturn and Moon–Mercury are exempt from mutual Vedha (BPHS rule)
VEDHA_EXEMPT: set[frozenset] = {
    frozenset({"Sun", "Saturn"}),
    frozenset({"Moon", "Mercury"}),
}

# ─────────────────────────────────────────────────────────────────────────────
# Ephemeris helpers
# ─────────────────────────────────────────────────────────────────────────────

def _init_swe():
    swe.use_lahiri()


def _get_chart_info(longitude: float, speed: Optional[float] = None) -> dict:
    pada = int(((longitude % (360 / 27)) / (360 / 27 / 4)) + 1)
    return {
        "longitude": longitude,
        "retrograde": (speed < 0) if speed is not None else None,
        "rasi": RASIS[int(longitude // 30)],
        "rasi_en": RASIS_EN[int(longitude // 30)],
        "nakshatra": NAKSHATRAS[int((longitude % 360) // (360 / 27))],
        "pada": pada,
    }


def _get_planet_positions(jd: float, lat: float, lon: float) -> tuple[dict, float]:
    _init_swe()
    FLAGS = swe.FLG_SIDEREAL | swe.FLG_SPEED
    swe.set_topo(lon, lat, 0)
    results = {}

    for pid in range(0, 10):
        name = swe.get_planet_name(pid)
        lonlat = swe.calc_ut(jd, pid, FLAGS)[0]
        results[name] = _get_chart_info(lonlat[0], lonlat[3])

    rahu = swe.calc_ut(jd, RAHU_NODE, FLAGS)[0]
    results["Rahu"] = _get_chart_info(rahu[0], rahu[3])
    results["Rahu"]["retrograde"] = True
    ketu_lon = (rahu[0] + 180.0) % 360.0
    results["Ketu"] = _get_chart_info(ketu_lon, rahu[3])
    results["Ketu"]["retrograde"] = True

    _, ascmc = swe.houses_ex(jd, lat, lon, b"P", flags=FLAGS)
    results["Ascendant"] = _get_chart_info(ascmc[0])

    return results, ascmc[0]


def _house_from_lon(longitude: float, asc_deg: float) -> int:
    return (int(longitude // 30) - int(asc_deg // 30)) % 12 + 1


def _planet_house_ownership(lagna_sign: str, planet: str) -> list[int]:
    try:
        li = RASIS.index(lagna_sign)
    except ValueError:
        return []
    return [(i - li) % 12 + 1 for i, s in enumerate(RASIS) if SIGN_LORDS.get(s) == planet]


def _nth_house_from(from_house: int, n: int) -> int:
    return ((from_house + n - 2) % 12) + 1


def _planet_aspects(planet: str, from_house: int) -> list[int]:
    """Direct aspects only — 7th for all, plus special aspects for Mars/Jupiter/Saturn."""
    asp = {_nth_house_from(from_house, 7)}
    if planet == "Mars":
        asp |= {_nth_house_from(from_house, 4), _nth_house_from(from_house, 8)}
    elif planet == "Jupiter":
        asp |= {_nth_house_from(from_house, 5), _nth_house_from(from_house, 9)}
    elif planet == "Saturn":
        asp |= {_nth_house_from(from_house, 3), _nth_house_from(from_house, 10)}
    return sorted(asp)


def _planetary_state(planet: str, sign: str) -> str:
    if planet in ("Rahu", "Ketu", "Ascendant"):
        return "N/A"
    s = PLANETARY_STATES.get(planet, {})
    if sign == s.get("exalted"):      return "Exalted"
    if sign == s.get("debilitated"):  return "Debilitated"
    if sign in s.get("own", []):      return "Own Sign"
    sl = SIGN_LORDS.get(sign, "")
    f  = FRIENDSHIPS.get(planet, {})
    if sl in f.get("friends", []):    return "Friend"
    if sl in f.get("enemies", []):    return "Enemy"
    return "Neutral"


# ─────────────────────────────────────────────────────────────────────────────
# Natal connection analysis (for house lord strength)
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_connections(data: dict, asc_deg: float) -> list[dict]:
    lagna_sign = data["Ascendant"]["rasi"]
    result = []
    for planet in ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]:
        if planet not in data:
            continue
        p   = data[planet]
        lon = p["longitude"]
        sig = p["rasi"]
        nak = p["nakshatra"]
        house = _house_from_lon(lon, asc_deg)
        asp   = _planet_aspects(planet, house)
        owns  = _planet_house_ownership(lagna_sign, planet)
        state = _planetary_state(planet, sig)

        result.append({
            "Planet":       planet,
            "Placed_House": house,
            "Sign":         sig,
            "State":        state,
            "Degree":       round(lon % 30, 2),
            "Retrograde":   "R" if p["retrograde"] else "-",
            "Planet_Owns":  owns,
            "Nakshatra":    nak,
            "Pada":         p["pada"],
            "Aspects":      asp,
            "Total_Connections": len({house} | set(owns) | set(asp)),
        })
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Natal house lord strength (from Lagna) — unchanged, this is correct
# ─────────────────────────────────────────────────────────────────────────────

def _dignity_score(state: str) -> float:
    return {"Exalted":100,"Own Sign":90,"Friend":70,"Neutral":50,"Enemy":30,"Debilitated":10,"N/A":50}.get(state, 50)


def _house_quality_score(house: int) -> float:
    hc = HOUSE_CLASSIFICATIONS
    if house in hc["kendra"] and house in hc["trikona"]: return 100
    if house in hc["trikona"]:  return 90
    if house in hc["kendra"]:   return 80
    if house in hc["upachaya"]: return 70
    if house in hc["dusthana"]: return 30
    return 50


def _natal_house_strength(house_num: int, lord_data: dict,
                           planets_in: list, planets_asp: list,
                           houses_from_own: int) -> float:
    pos_s = {12:100,4:90,7:90,10:90,5:95,9:95,3:75,11:75,2:50,6:40,8:30}
    lp = pos_s.get(houses_from_own, 50)
    ld = _dignity_score(lord_data["State"])

    ben = sum(1 for p in planets_in + planets_asp if PLANETARY_NATURE.get(p) == "benefic")
    mal = sum(1 for p in planets_in + planets_asp if PLANETARY_NATURE.get(p) == "malefic")
    bs  = min(100, ben * 30)
    mp  = min(50,  mal * 12)

    hc = HOUSE_CLASSIFICATIONS
    hn = 60
    if house_num in hc["kendra"]:   hn = 85
    if house_num in hc["trikona"]:  hn = 90
    if house_num in hc["dusthana"]: hn = 45
    if house_num in hc["upachaya"]: hn = 75

    return max(0, min(100, lp*0.35 + ld*0.25 + bs*0.20 - mp*0.15 + hn*0.15))


def _analyze_house_lords(natal_data: dict, conns: list[dict], asc_deg: float) -> dict:
    lagna_sign = natal_data["Ascendant"]["rasi"]
    try:
        li = RASIS.index(lagna_sign)
    except ValueError:
        return {}

    out = {}
    for h in range(1, 13):
        hs_idx  = (li + h - 1) % 12
        hs      = RASIS[hs_idx]
        lord    = SIGN_LORDS[hs]
        ld      = next((c for c in conns if c["Planet"] == lord), None)
        if not ld:
            continue
        lh      = ld["Placed_House"]
        hfo     = ((lh - h) % 12) or 12
        p_in    = [c["Planet"] for c in conns if c["Placed_House"] == h]
        p_asp   = [c["Planet"] for c in conns if h in c["Aspects"]]
        ns      = _natal_house_strength(h, ld, p_in, p_asp, hfo)

        out[h] = {
            "house_sign":          hs,
            "house_sign_en":       RASIS_EN[hs_idx],
            "lord":                lord,
            "lord_placed_in_house": lh,
            "lord_placed_in_sign": ld["Sign"],
            "lord_dignity":        ld["State"],
            "lord_degree":         ld["Degree"],
            "lord_retrograde":     ld["Retrograde"] == "R",
            "lord_nakshatra":      ld["Nakshatra"],
            "lord_pada":           ld["Pada"],
            "houses_from_own":     hfo,
            "planets_in_house":    p_in,
            "planets_aspecting":   p_asp,
            "natal_strength":      round(ns, 1),
        }
    return out


# ─────────────────────────────────────────────────────────────────────────────
# PARASARA GOCHARA SCORING
# ─────────────────────────────────────────────────────────────────────────────

def _pos_from_moon(transit_lon: float, natal_moon_lon: float) -> int:
    """
    Calculate position of a transit planet counted from natal Moon sign.
    Returns 1–12 (1 = same sign as natal Moon).
    """
    natal_moon_sign_idx   = int(natal_moon_lon // 30)
    transit_sign_idx      = int(transit_lon // 30)
    return (transit_sign_idx - natal_moon_sign_idx) % 12 + 1


def _gochara_score(planet: str,
                   pos: int,
                   all_positions: dict[str, int]) -> tuple[float, bool, str]:
    """
    Returns (score 0–100, vedha_blocked bool, blocking_planet str).

    Rules (BPHS Gochara):
    - Planet in auspicious position from natal Moon AND no Vedha → score 80–95
    - Planet in auspicious position but Vedha active            → score 40–50
    - Planet in inauspicious position                           → score 15–40
    """
    auspicious = GOCHARA_AUSPICIOUS.get(planet, set())

    # Base score for inauspicious position (gradated by house)
    # 8th from Moon (Ashtama) is worst; 4th, 5th, 7th, 12th also bad
    inauspicious_scores = {
        8: 10,   # Ashtama — worst
        4: 20,
        5: 25,
        7: 25,
        12: 25,
        1: 30,   # Janma — bad for most planets
        2: 35,
        10: 40,  # 10th is mixed (upachaya but counted inauspicious for some)
        9: 35,
        11: 35,  # should not be here for most planets — but fallback
        3: 35,
        6: 35,
    }

    if pos not in auspicious:
        return inauspicious_scores.get(pos, 30), False, ""

    # Auspicious position — check Vedha
    vedha_pos = VEDHA_POINTS.get(planet, {}).get(pos)
    if vedha_pos:
        for other, other_pos in all_positions.items():
            if other == planet:
                continue
            if frozenset({planet, other}) in VEDHA_EXEMPT:
                continue
            if other_pos == vedha_pos:
                return 45.0, True, other  # Vedha cancels the benefit

    # Auspicious, no Vedha
    # Grade the auspicious score by how strong the position is
    top_positions = {
        "Sun":     {11: 95, 3: 80, 6: 80, 10: 80},
        "Moon":    {11: 95, 6: 85, 10: 85, 7: 80, 3: 80, 1: 70},
        "Mars":    {11: 95, 3: 80, 6: 80},
        "Mercury": {11: 90, 6: 85, 10: 85, 2: 75, 4: 75, 8: 70},
        "Jupiter": {11: 95, 2: 85, 5: 85, 7: 85, 9: 85},
        "Venus":   {11: 90, 4: 85, 5: 85, 1: 80, 2: 80, 3: 80, 8: 75, 9: 75, 12: 70},
        "Saturn":  {11: 95, 3: 80, 6: 80},
        "Rahu":    {11: 90, 3: 75, 6: 75},
        "Ketu":    {11: 90, 3: 75, 6: 75},
    }
    return top_positions.get(planet, {}).get(pos, 80), False, ""


def _gochara_result_label(score: float, vedha: bool) -> str:
    if vedha:
        return "Vedha (blocked)"
    if score >= 80:
        return "Auspicious"
    if score >= 50:
        return "Mixed"
    return "Inauspicious"


def _rag(score: float) -> dict:
    if score >= 68:
        return {"status":"GREEN", "emoji":"🟢", "label":"Favourable",  "colour":"#27ae60"}
    if score >= 40:
        return {"status":"AMBER", "emoji":"🟡", "label":"Mixed",       "colour":"#f39c12"}
    return     {"status":"RED",   "emoji":"🔴", "label":"Challenging", "colour":"#e74c3c"}


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
    Score all 12 houses using Parasara's Gochara rules.

    Blend:
        60% natal house lord strength (from Lagna — permanent strength)
        40% Gochara transit score     (from natal Moon — current timing)

    Parameters
    ----------
    natal_chart  : the /natal-chart response (must contain birth_data)
    transit_date : YYYY-MM-DD; defaults to today

    Returns
    -------
    dict: houses, overall_health, transit_analysis (per planet), house_rankings
    """
    if transit_date is None:
        transit_date = datetime.date.today().isoformat()

    ck = _cache_key(natal_chart, transit_date)
    if ck in _score_cache:
        return _score_cache[ck]

    bd     = natal_chart.get("birth_data", {})
    dob    = bd.get("dob", "")
    tob    = bd.get("tob", "")
    lat    = float(bd.get("lat", 13.08))
    lon    = float(bd.get("lon", 80.27))
    # Derive UTC offset from timezone string (more accurate than hardcoded 5.5)
    tz_str = bd.get("timezone", "Asia/Kolkata")
    try:
        from zoneinfo import ZoneInfo
        _tz  = ZoneInfo(tz_str)
        _ref = datetime.datetime(2000, 1, 1, 12, 0, tzinfo=_tz)
        tz_off = _ref.utcoffset().total_seconds() / 3600  # type: ignore
    except Exception:
        tz_off = float(bd.get("tz_offset", 5.5))

    # ── Natal chart ────────────────────────────────────────────────────────
    dob_dt   = datetime.datetime.strptime(dob, "%Y-%m-%d")
    tob_dt   = datetime.datetime.strptime(tob[:5], "%H:%M")
    local_dt = datetime.datetime(dob_dt.year, dob_dt.month, dob_dt.day,
                                 tob_dt.hour, tob_dt.minute)
    utc_dt   = local_dt - datetime.timedelta(hours=tz_off)
    natal_jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                          utc_dt.hour + utc_dt.minute / 60.0)

    natal_data, natal_asc_deg = _get_planet_positions(natal_jd, lat, lon)
    natal_conns               = _analyze_connections(natal_data, natal_asc_deg)
    natal_dict                = {c["Planet"]: c for c in natal_conns}
    house_lord_data           = _analyze_house_lords(natal_data, natal_conns, natal_asc_deg)

    # Natal Moon longitude — Gochara reference point
    natal_moon_lon = natal_data["Moon"]["longitude"]
    natal_moon_sign = natal_data["Moon"]["rasi"]
    natal_moon_sign_en = natal_data["Moon"]["rasi_en"]

    # ── Transit positions ──────────────────────────────────────────────────
    td_dt      = datetime.datetime.strptime(transit_date, "%Y-%m-%d")
    transit_jd = swe.julday(td_dt.year, td_dt.month, td_dt.day, 12.0)
    transit_data, _ = _get_planet_positions(transit_jd, lat, lon)

    # ── Gochara: position of each transit planet from natal Moon ───────────
    planets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]

    positions_from_moon: dict[str, int] = {}
    for p in planets:
        if p in transit_data:
            positions_from_moon[p] = _pos_from_moon(
                transit_data[p]["longitude"], natal_moon_lon
            )

    # ── Per-planet Gochara scores ──────────────────────────────────────────
    gochara_scores:  dict[str, float] = {}
    gochara_details: dict[str, dict]  = {}

    for p in planets:
        if p not in positions_from_moon:
            continue
        pos   = positions_from_moon[p]
        score, vedha, vedha_by = _gochara_score(p, pos, positions_from_moon)
        gochara_scores[p]  = score
        gochara_details[p] = {
            "planet":          p,
            "transit_sign":    transit_data[p]["rasi"],
            "transit_sign_en": transit_data[p]["rasi_en"],
            "transit_degree":  round(transit_data[p]["longitude"] % 30, 2),
            "nakshatra":       transit_data[p]["nakshatra"],
            "pada":            transit_data[p]["pada"],
            "pos_from_moon":   pos,
            "retrograde":      transit_data[p]["retrograde"],
            "auspicious":      pos in GOCHARA_AUSPICIOUS.get(p, set()),
            "vedha_blocked":   vedha,
            "vedha_by":        vedha_by,
            "score":           round(score, 1),
            "rag":             _rag(score),
            "result":          _gochara_result_label(score, vedha),
        }

    # ── Gochara transit score per house ────────────────────────────────────
    # For each house:
    #   1. Gochara of the house lord (most important — 50%)
    #   2. Gochara of planets DIRECTLY in that house (40%)
    #   3. Gochara of natural Karaka(s) for that house (10%)
    gochara_house_scores: dict[int, float] = {}

    for h in range(1, 13):
        hl_data = house_lord_data.get(h, {})
        lord    = hl_data.get("lord", "")

        # 1. House lord gochara
        lord_gochara = gochara_scores.get(lord, 50.0)

        # 2. Planets physically transiting this house right now
        # (planet's current sign = the house's sign from lagna)
        lagna_sign = natal_data["Ascendant"]["rasi"]
        lagna_idx  = RASIS.index(lagna_sign)
        house_sign = RASIS[(lagna_idx + h - 1) % 12]

        planets_in_house = [
            p for p in planets
            if p in transit_data and transit_data[p]["rasi"] == house_sign
        ]

        if planets_in_house:
            in_house_score = sum(gochara_scores.get(p, 50) for p in planets_in_house) / len(planets_in_house)
        else:
            in_house_score = 50.0  # neutral — no planet transiting

        # 3. Natural karaka gochara
        karakas = HOUSE_KARAKAS.get(h, [])
        if karakas:
            karaka_score = sum(gochara_scores.get(k, 50) for k in karakas) / len(karakas)
        else:
            karaka_score = 50.0

        gochara_house_scores[h] = round(
            lord_gochara * 0.50 + in_house_score * 0.35 + karaka_score * 0.15, 1
        )

    # ── SAV refinement ────────────────────────────────────────────────────────
    # Silently load SAV to refine transit scores (Ashtakavarga bindus per house)
    try:
        from agents.ashtakavarga_agent import sav_for_transit_scoring
        sav_house = sav_for_transit_scoring(natal_chart)
    except Exception:
        sav_house = [28] * 12   # neutral default

    # ── Blended final house scores ─────────────────────────────────────────
    # 55% natal house lord strength + 35% Gochara + 10% SAV normalised
    houses_out: dict[int, dict] = {}

    for h in range(1, 13):
        hl        = house_lord_data.get(h, {})
        natal_s   = hl.get("natal_strength", 50.0)
        transit_s = gochara_house_scores.get(h, 50.0)
        # SAV normalised: 337 total / 12 houses ≈ 28 average
        # Map to 0-100 scale: sav_pts / 56 * 100 (56 = max theoretical per house)
        sav_pts   = sav_house[h - 1] if h <= len(sav_house) else 28
        sav_norm  = round(min(100, (sav_pts / 42) * 100), 1)   # 42 = practical max
        blended   = round(natal_s * 0.55 + transit_s * 0.35 + sav_norm * 0.10, 1)

        # "Transit Activity" — ONLY planets directly in or directly aspecting house
        house_sign  = RASIS[(RASIS.index(natal_data["Ascendant"]["rasi"]) + h - 1) % 12]
        direct_in   = [p for p in planets if p in transit_data
                       and transit_data[p]["rasi"] == house_sign]
        direct_asp  = [p for p in planets if p in transit_data
                       and h in _planet_aspects(p, _house_from_lon(transit_data[p]["longitude"], natal_asc_deg))
                       and transit_data[p]["rasi"] != house_sign]
        transit_activity = direct_in + direct_asp

        houses_out[h] = {
            "house_num":          h,
            "area":               HOUSE_SIGNIFICATIONS[h]["area"],
            "name":               HOUSE_EXPLANATIONS[h]["name"],
            "simple":             HOUSE_EXPLANATIONS[h]["simple"],
            "themes":             HOUSE_SIGNIFICATIONS[h]["themes"],
            "score":              blended,
            "natal_score":        natal_s,
            "transit_score":      transit_s,
            "rag":                _rag(blended),
            "lord":               hl.get("lord", ""),
            "lord_placed_house":  hl.get("lord_placed_in_house", ""),
            "lord_dignity":       hl.get("lord_dignity", ""),
            "lord_retrograde":    hl.get("lord_retrograde", False),
            "planets_in_house":   hl.get("planets_in_house", []),    # natal planets
            "planets_aspecting":  hl.get("planets_aspecting", []),   # natal aspects
            "transit_planets":    transit_activity,                   # direct transit only
            "house_sign":         hl.get("house_sign", ""),
            "house_sign_en":      hl.get("house_sign_en", ""),
            # Lord gochara detail for narrator context
            "lord_gochara_pos":    positions_from_moon.get(hl.get("lord",""), ""),
            "lord_gochara_result": _gochara_result_label(
                gochara_scores.get(hl.get("lord",""), 50),
                gochara_details.get(hl.get("lord",""), {}).get("vedha_blocked", False)
            ),
            # Ashtakavarga
            "sav_points":   sav_pts,
            "sav_label":    "Strong" if sav_pts >= 30 else "Good" if sav_pts >= 25 else "Average" if sav_pts >= 20 else "Weak",
        }

    # ── Overall Gochara health ─────────────────────────────────────────────
    all_scores = [d["score"] for d in gochara_details.values()]
    avg  = round(sum(all_scores) / len(all_scores), 1) if all_scores else 50.0
    overall = {
        "average_score": avg,
        "rag":           _rag(avg),
        "green_count":   sum(1 for s in all_scores if s >= 68),
        "amber_count":   sum(1 for s in all_scores if 40 <= s < 68),
        "red_count":     sum(1 for s in all_scores if s < 40),
        "total_planets": len(all_scores),
    }

    # ── House ranking by blended score ────────────────────────────────────
    ranked = sorted(houses_out.values(), key=lambda x: x["score"], reverse=True)

    result = {
        "houses":           houses_out,
        "overall_health":   overall,
        "transit_analysis": list(gochara_details.values()),
        "house_rankings":   ranked,
        "transit_date":     transit_date,
        "lagna":            natal_data["Ascendant"]["rasi"],
        "lagna_en":         RASIS_EN[RASIS.index(natal_data["Ascendant"]["rasi"])],
        "natal_moon":       natal_moon_sign,
        "natal_moon_en":    natal_moon_sign_en,
        "gochara_note":     "Transits evaluated from natal Moon sign per Parasara Gochara rules. Vedha checked.",
    }

    _score_cache[ck] = result
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Context builder for narrator
# ─────────────────────────────────────────────────────────────────────────────

def build_house_context(scores: dict, house_num: int) -> str:
    h   = scores["houses"].get(house_num, {})
    oh  = scores["overall_health"]
    ta  = [d for d in scores["transit_analysis"]
           if d["planet"] == h.get("lord") or
              d["planet"] in h.get("transit_planets", [])]

    lines = [
        f"HOUSE {house_num}: {h.get('name')} ({h.get('simple')})",
        f"House sign: {h.get('house_sign_en')}",
        f"Blended score: {h.get('score')}/100  [{h.get('rag', {}).get('label')}]",
        f"  └ Natal strength: {h.get('natal_score')}/100",
        f"  └ Gochara score:  {h.get('transit_score')}/100",
        "",
        f"Natal house lord: {h.get('lord')} in H{h.get('lord_placed_house')} ({h.get('lord_dignity')}"
        + (", Retrograde" if h.get("lord_retrograde") else "") + ")",
        f"Lord Gochara (from natal Moon): position {h.get('lord_gochara_pos')} from Moon → {h.get('lord_gochara_result')}",
    ]

    if h.get("planets_in_house"):
        lines.append(f"Natal planets in this house: {', '.join(h['planets_in_house'])}")
    if h.get("planets_aspecting"):
        lines.append(f"Natal planets aspecting: {', '.join(h['planets_aspecting'])}")

    if h.get("transit_planets"):
        lines.append(f"Current direct transits (in house or aspecting): {', '.join(h['transit_planets'])}")
        for p in h["transit_planets"]:
            d = next((x for x in scores["transit_analysis"] if x["planet"] == p), None)
            if d:
                lines.append(
                    f"  {p}: {d['transit_sign_en']} {d['transit_degree']:.1f}°  "
                    f"pos {d['pos_from_moon']} from natal Moon → {d['result']} (score {d['score']})"
                )
    else:
        lines.append("No planets directly transiting or aspecting this house right now.")

    lines += [
        "",
        f"Natal Moon sign: {scores.get('natal_moon_en')} (Gochara reference)",
        f"Overall transit health today: {oh['average_score']}/100 [{oh['rag']['label']}]",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Dasha-Transit Correlation
# The most powerful timing signal: Dasha lord in auspicious Gochara position
# ─────────────────────────────────────────────────────────────────────────────

def dasha_transit_correlation(scores: dict, dasha: dict) -> dict:
    """
    Correlate current Dasha/Bhukti lords with their Gochara positions.

    When the Dasha lord is in an auspicious Gochara position from natal Moon,
    the Dasha period activates strongly and positively (Parasara timing rule).
    When the Dasha lord is in an inauspicious position, the period is subdued
    or brings obstacles even if the natal chart is strong.

    Returns a dict with scores, labels and a plain-English summary.
    """
    md_planet = (dasha.get("mahadasha") or {}).get("planet", "")
    bh_planet = (dasha.get("bhukti")    or {}).get("planet", "")

    ta_map = {d["planet"]: d for d in scores.get("transit_analysis", [])}

    def _detail(planet: str) -> dict:
        d = ta_map.get(planet, {})
        return {
            "planet":       planet,
            "score":        d.get("score", 50.0),
            "pos":          d.get("pos_from_moon", "?"),
            "result":       d.get("result", "Unknown"),
            "vedha":        d.get("vedha_blocked", False),
            "vedha_by":     d.get("vedha_by", ""),
            "transit_sign": d.get("transit_sign_en", ""),
            "rag":          d.get("rag", _rag(50)),
        }

    md = _detail(md_planet)
    bh = _detail(bh_planet)

    # Weighted average: Mahadasha lord carries more weight
    avg_score = round(md["score"] * 0.60 + bh["score"] * 0.40, 1)
    corr_rag  = _rag(avg_score)

    # Human-readable summary
    def _planet_phrase(d: dict, role: str) -> str:
        planet = d["planet"]
        if not planet:
            return ""
        sign   = d["transit_sign"]
        pos    = d["pos"]
        result = d["result"]
        if d["vedha"]:
            return (f"{planet} ({role}) is at position {pos} from natal Moon — "
                    f"auspicious in {sign} but blocked by Vedha from {d['vedha_by']}.")
        if result == "Auspicious":
            return (f"{planet} ({role}) is at position {pos} from natal Moon in {sign} — "
                    f"auspicious Gochara, activating the {role.lower()} period strongly.")
        else:
            return (f"{planet} ({role}) is at position {pos} from natal Moon in {sign} — "
                    f"{result.lower()} Gochara, dampening the {role.lower()} period results.")

    phrases = [p for p in [
        _planet_phrase(md, "Mahadasha lord"),
        _planet_phrase(bh, "Bhukti lord"),
    ] if p]

    if avg_score >= 68:
        overall = "Both Dasha lords are well-placed in transit — a strongly activated period."
    elif avg_score >= 45:
        overall = "Mixed Dasha-transit correlation — partial activation of the period."
    else:
        overall = "Dasha lords are poorly placed in transit — the period is subdued. Exercise patience."

    return {
        "mahadasha":       md,
        "bhukti":          bh,
        "correlation_score": avg_score,
        "rag":             corr_rag,
        "summary":         " ".join(phrases),
        "overall":         overall,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Compact Gochara summary for chat system prompt injection
# ─────────────────────────────────────────────────────────────────────────────

def compact_gochara_summary(scores: dict, dasha: dict) -> str:
    """
    Returns a compact multi-line block suitable for injecting into the
    chat system prompt.  Designed to be concise — ~600 tokens max.
    """
    oh   = scores["overall_health"]
    dtc  = dasha_transit_correlation(scores, dasha)
    moon = scores.get("natal_moon_en", "?")
    date = scores.get("transit_date", "today")

    lines = [
        f"=== GOCHARA TRANSIT SCORES — {date} (ref: {moon} natal Moon) ===",
        f"Overall transit health: {oh['average_score']}/100 [{oh['rag']['label']}]  "
        f"({oh['green_count']}🟢 {oh['amber_count']}🟡 {oh['red_count']}🔴)",
        "",
        f"DASHA-TRANSIT CORRELATION ({dtc['rag']['label']} — {dtc['correlation_score']}/100):",
        dtc["summary"],
        dtc["overall"],
        "",
        "12-HOUSE SCORES (natal strength 60% + Gochara 40%):",
    ]

    for h in range(1, 13):
        hd = scores["houses"].get(h, {})
        lord = hd.get("lord", "?")
        lpos = hd.get("lord_gochara_pos", "?")
        lres = hd.get("lord_gochara_result", "?")
        rag  = hd.get("rag", {}).get("emoji", "")
        tp   = ", ".join(hd.get("transit_planets", [])) or "none"
        lines.append(
            f"  H{h:02d} {hd.get('name',''):<28} {rag} {hd.get('score',0):5.1f}  "
            f"lord={lord} pos{lpos}→{lres}  direct_transit=[{tp}]"
        )

    lines += [
        "",
        "Use these scores + Gochara positions to give SPECIFIC, TIMELY answers.",
        "When asked about a life area, cite the house score, lord position, and Dasha correlation.",
    ]

    return "\n".join(lines)
