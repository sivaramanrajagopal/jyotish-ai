"""
indu_lagna_agent.py — Indu Lagna (fortune lagna) and fortune-building periods.

Natal judgment (occupants, lord dignity, aspects) + tiered activation:
  primary   — Dasa/Bhukti of Indu lord or natal occupants
  secondary — Jupiter/Saturn transits over Indu sign or Indu lord's natal sign
  minor     — fast-planet transits (Sun, Mercury, Moon) through Indu sign
"""

from __future__ import annotations

import datetime
from typing import Optional

import ephemeris as swe
from dasha_core import generate_dashas, generate_bhuktis
from agents.prashna.dignity_engine import planetary_state
from agents.tamil_dosha.constants import RASI_ENGLISH, RASI_ORDER, SIGN_LORDS
from agents.transit_score_agent import _planet_aspects

RASI_VALUES = [6, 12, 8, 16, 30, 8, 12, 6, 10, 1, 1, 10]

SLOW_TRANSIT_PLANETS = ("Jupiter", "Saturn")
FAST_TRANSIT_PLANETS = ("Sun", "Mercury", "Moon")

NATURAL_BENEFICS = frozenset({"Jupiter", "Venus"})
NATURAL_MALEFICS = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})

TRANSIT_BODIES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.RAHU_NODE,
}

_FLAGS = swe.FLG_SIDEREAL | swe.FLG_SPEED

_HOUSE_THEMES = {
    1: "self and vitality",
    2: "wealth and family",
    3: "effort and communication",
    4: "home and comfort",
    5: "merit and creativity",
    6: "service and obstacles",
    7: "partnerships and trade",
    8: "shared resources",
    9: "fortune and dharma",
    10: "career and status",
    11: "gains and networks",
    12: "expenses and retreat",
}


def _ninth_sign_index(sign_idx: int) -> int:
    return (int(sign_idx) + 8) % 12


def calculate_indu_lagna_index(asc_sign_index: int, moon_sign_index: int) -> int:
    ninth_asc = _ninth_sign_index(asc_sign_index)
    ninth_moon = _ninth_sign_index(moon_sign_index)
    total = RASI_VALUES[ninth_asc] + RASI_VALUES[ninth_moon]
    remainder = total % 12
    if remainder == 0:
        remainder = 12
    return (int(moon_sign_index) + remainder - 1) % 12


def _sign_label(sign_idx: int) -> dict:
    return {
        "index": sign_idx,
        "name": RASI_ORDER[sign_idx],
        "english": RASI_ENGLISH[sign_idx],
        "lord": SIGN_LORDS[sign_idx],
    }


def _planets_in_sign(planet_positions: dict, sign_idx: int) -> list[str]:
    out: list[str] = []
    for planet, pdata in planet_positions.items():
        if planet in ("Ascendant",):
            continue
        if pdata.get("sign_index") == sign_idx:
            out.append(planet)
    return sorted(out)


def _is_waxing_moon(moon_lon: float, sun_lon: float) -> bool:
    return ((moon_lon - sun_lon) % 360.0) < 180.0


def _sign_malefic_occupants(planet_positions: dict, sign_idx: int) -> set[str]:
    """Malefics sharing the same sign as planet (whole-sign conjunction)."""
    malefics: set[str] = set()
    for planet, pdata in planet_positions.items():
        if planet in ("Ascendant",):
            continue
        if pdata.get("sign_index") == sign_idx and planet in NATURAL_MALEFICS:
            malefics.add(planet)
    return malefics


def _classify_occupant(
    planet: str,
    pdata: dict,
    planet_positions: dict,
    sun_lon: float,
    moon_lon: float,
    *,
    lagna_lord: Optional[str] = None,
) -> dict:
    sign = pdata.get("sign") or RASI_ENGLISH[pdata.get("sign_index", 0)]
    deg = pdata.get("degree_in_sign")
    dignity, _deep = planetary_state(planet, sign, deg)

    if planet in NATURAL_BENEFICS:
        tone = "benefic"
        note = f"Natural benefic in Indu Lagna ({dignity})"
    elif planet == "Mercury":
        sign_idx = pdata.get("sign_index", 0)
        afflicted_by = sorted(_sign_malefic_occupants(planet_positions, sign_idx) - {planet})
        if dignity == "Debilitated" or afflicted_by or pdata.get("retrograde"):
            tone = "mixed"
            parts = []
            if dignity == "Debilitated":
                parts.append("debilitated")
            if afflicted_by:
                parts.append(f"with {', '.join(afflicted_by)}")
            if pdata.get("retrograde"):
                parts.append("retrograde")
            note = f"Mercury afflicted ({', '.join(parts)})" if parts else "Mercury (mixed)"
        else:
            tone = "benefic"
            note = f"Mercury unafflicted ({dignity})"
    elif planet == "Moon":
        if _is_waxing_moon(moon_lon, sun_lon):
            tone = "benefic"
            note = f"Waxing Moon ({dignity})"
        else:
            tone = "mixed"
            note = f"Waning Moon ({dignity})"
    elif planet == "Sun":
        tone = "mixed"
        note = f"Sun as authority graha ({dignity})"
    elif planet in NATURAL_MALEFICS:
        if planet == lagna_lord:
            tone = "mixed"
            note = (
                f"{planet} as Lagna lord in Indu ({dignity}) — personally significant; "
                f"fortune through discipline and H{pdata.get('house', '?')} themes"
            )
        else:
            tone = "challenging"
            note = f"{planet} as malefic occupant ({dignity})"
    else:
        tone = "mixed"
        note = f"{planet} ({dignity})"

    return {
        "planet": planet,
        "tone": tone,
        "note": note,
        "dignity": dignity,
        "house": pdata.get("house"),
        "retrograde": bool(pdata.get("retrograde")),
    }


def _lord_judgment(indu_lord: str, planet_positions: dict) -> dict:
    pdata = planet_positions.get(indu_lord) or {}
    sign = pdata.get("sign") or ""
    deg = pdata.get("degree_in_sign")
    dignity, deep = planetary_state(indu_lord, sign, deg) if sign else ("N/A", False)
    house = pdata.get("house")

    strength_score = {
        "Exalted": 90,
        "Own Sign": 85,
        "Friend": 70,
        "Neutral": 55,
        "Enemy": 40,
        "Debilitated": 25,
        "N/A": 50,
    }.get(dignity, 50)
    if deep and dignity == "Exalted":
        strength_score = 95
    if deep and dignity == "Debilitated":
        strength_score = 20

    return {
        "planet": indu_lord,
        "sign": sign,
        "sign_tamil": RASI_ORDER[pdata.get("sign_index", 0)] if pdata.get("sign_index") is not None else "",
        "house": house,
        "dignity": dignity,
        "deep": deep,
        "strength_score": strength_score,
        "retrograde": bool(pdata.get("retrograde")),
    }


def _aspects_on_indu_house(planet_positions: dict, indu_house: int) -> list[dict]:
    aspects: list[dict] = []
    for planet, pdata in planet_positions.items():
        if planet in ("Ascendant",):
            continue
        from_house = pdata.get("house")
        if not from_house:
            continue
        if indu_house not in _planet_aspects(planet, int(from_house)):
            continue
        if planet in ("Jupiter", "Venus"):
            tone = "benefic"
            weight = 15 if planet == "Jupiter" else 10
        elif planet in NATURAL_MALEFICS:
            tone = "challenging"
            weight = -8 if planet == "Mars" else -5
        else:
            tone = "mixed"
            weight = 0
        aspects.append({
            "planet": planet,
            "from_house": from_house,
            "tone": tone,
            "weight": weight,
            "note": f"{planet} aspects Indu Lagna (H{indu_house}) from H{from_house}",
        })
    aspects.sort(key=lambda a: -a["weight"])
    return aspects


def _natal_judgment(
    indu_idx: int,
    indu_lord: str,
    indu_house: int,
    planets_in_indu: list[str],
    planet_positions: dict,
    *,
    asc_sign_index: int,
) -> dict:
    sun = planet_positions.get("Sun") or {}
    moon = planet_positions.get("Moon") or {}
    sun_lon = float(sun.get("longitude", 0))
    moon_lon = float(moon.get("longitude", 0))

    lagna_lord = SIGN_LORDS[asc_sign_index]

    occupants = [
        _classify_occupant(
            planet, planet_positions[planet], planet_positions, sun_lon, moon_lon,
            lagna_lord=lagna_lord,
        )
        for planet in planets_in_indu
        if planet in planet_positions
    ]
    lord = _lord_judgment(indu_lord, planet_positions)
    aspects = _aspects_on_indu_house(planet_positions, indu_house)

    score = lord["strength_score"]
    for occ in occupants:
        score += {"benefic": 10, "mixed": 0, "challenging": -12}.get(occ["tone"], 0)
        if occ["planet"] == lagna_lord and occ["tone"] == "mixed":
            score += 5
    for asp in aspects:
        score += asp["weight"]

    if not occupants:
        score -= 5

    if score >= 68:
        verdict = "supportive"
        verdict_label = "Supportive"
    elif score >= 42:
        verdict = "mixed"
        verdict_label = "Mixed"
    else:
        verdict = "challenging"
        verdict_label = "Challenging"

    benefic_aspects = [a["planet"] for a in aspects if a["tone"] == "benefic"]
    challenging_aspects = [a["planet"] for a in aspects if a["tone"] == "challenging"]

    return {
        "occupants": occupants,
        "lord": lord,
        "lagna_lord": lagna_lord,
        "aspects": aspects,
        "benefic_aspects": benefic_aspects,
        "challenging_aspects": challenging_aspects,
        "house_theme": _HOUSE_THEMES.get(indu_house, "life area"),
        "verdict": verdict,
        "verdict_label": verdict_label,
        "score": round(score, 1),
        "summary": _judgment_summary(verdict_label, lord, occupants, benefic_aspects),
    }


def _judgment_summary(
    verdict_label: str,
    lord: dict,
    occupants: list[dict],
    benefic_aspects: list[str],
) -> str:
    parts = [f"Natal promise: {verdict_label}."]
    parts.append(
        f"Indu lord {lord['planet']} in {lord['sign'] or '—'} ({lord['dignity']})."
    )
    if occupants:
        tones = ", ".join(f"{o['planet']} ({o['tone']})" for o in occupants)
        parts.append(f"Occupants: {tones}.")
    else:
        parts.append("No planets occupy Indu Lagna.")
    if benefic_aspects:
        parts.append(f"Supportive aspects: {', '.join(benefic_aspects)}.")
    return " ".join(parts)


def _fortune_dasa_periods(
    moon_longitude: float,
    birth_date: str,
    relevant_planets: set[str],
    *,
    years: int = 90,
) -> list[dict]:
    """Filter Vimshottari Dasa/Bhukti (standard order via dasha_core) for fortune grahas."""
    birth_dt = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
    cutoff = birth_dt + datetime.timedelta(days=years * 365.25)
    periods: list[dict] = []

    for dasa in generate_dashas(moon_longitude, birth_date):
        if dasa["start"] >= cutoff:
            break
        maha = dasa["planet"]
        for b in generate_bhuktis(dasa):
            if b["end"] <= birth_dt or b["start"] >= cutoff:
                continue
            bukti = b["planet"]
            if maha in relevant_planets or bukti in relevant_planets:
                periods.append({
                    "maha_dasa": maha,
                    "bukti": bukti,
                    "start": b["start"].strftime("%Y-%m-%d"),
                    "end": b["end"].strftime("%Y-%m-%d"),
                    "activation_tier": "primary",
                    "label": f"{maha}–{bukti} Dasa/Bhukti",
                })
    return periods


def _planet_longitude(jd: float, planet: str) -> float:
    if planet == "Ketu":
        rahu = swe.calc_ut(jd, swe.RAHU_NODE, _FLAGS)[0][0]
        return (rahu + 180.0) % 360.0
    body = TRANSIT_BODIES[planet]
    return swe.calc_ut(jd, body, _FLAGS)[0][0]


def _sign_index_from_longitude(lon: float) -> int:
    return int(lon // 30) % 12


def _jd_at_local_noon(d: datetime.date, tz_name: str) -> float:
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(tz_name)
    dt = datetime.datetime(d.year, d.month, d.day, 12, 0, tzinfo=tz)
    utc = dt.astimezone(datetime.timezone.utc)
    hour = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
    return swe.julday(utc.year, utc.month, utc.day, hour)


def _scan_transits_in_signs(
    targets: list[dict],
    planets: list[str],
    start_date: datetime.date,
    end_date: datetime.date,
    tz_name: str,
    *,
    activation_tier: str,
) -> list[dict]:
    """Whole-sign transit windows; targets = [{index, label}, ...]."""
    windows: list[dict] = []
    today = datetime.date.today()
    target_indices = {t["index"] for t in targets}
    target_by_idx = {t["index"]: t["label"] for t in targets}

    for planet in planets:
        in_sign = False
        period_start: Optional[datetime.date] = None
        active_target_label = ""

        d = start_date
        while d <= end_date:
            jd = _jd_at_local_noon(d, tz_name)
            lon = _planet_longitude(jd, planet)
            sign_idx = _sign_index_from_longitude(lon)
            currently_in = sign_idx in target_indices

            if currently_in and not in_sign:
                period_start = d
                active_target_label = target_by_idx.get(sign_idx, "")
                in_sign = True
            elif currently_in and in_sign:
                pass
            elif not currently_in and in_sign and period_start is not None:
                windows.append({
                    "planet": planet,
                    "target": active_target_label,
                    "start": period_start.isoformat(),
                    "end": (d - datetime.timedelta(days=1)).isoformat(),
                    "duration_days": (d - period_start).days,
                    "currently_active": False,
                    "activation_tier": activation_tier,
                    "label": f"{planet} over {active_target_label}",
                })
                in_sign = False
                period_start = None
                active_target_label = ""
            d += datetime.timedelta(days=1)

        if in_sign and period_start is not None:
            windows.append({
                "planet": planet,
                "target": active_target_label,
                "start": period_start.isoformat(),
                "end": end_date.isoformat(),
                "duration_days": (end_date - period_start).days + 1,
                "currently_active": period_start <= today <= end_date,
                "activation_tier": activation_tier,
                "label": f"{planet} over {active_target_label}",
            })

    windows.sort(key=lambda w: (w["start"], w["planet"]))
    return windows


def _filter_by_date(periods: list[dict], today_str: str, *, active: bool) -> list[dict]:
    if active:
        return [p for p in periods if p["start"] <= today_str <= p["end"]]
    return [p for p in periods if p["start"] > today_str]


def _hero_block(
    primary: list[dict],
    secondary: list[dict],
    today_str: str,
    verdict_label: str,
) -> dict:
    active_primary = _filter_by_date(primary, today_str, active=True)
    active_secondary = _filter_by_date(secondary, today_str, active=True)
    next_primary = _filter_by_date(primary, today_str, active=False)
    next_secondary = _filter_by_date(secondary, today_str, active=False)

    return {
        "natal_promise": verdict_label,
        "active_primary": active_primary[:2],
        "active_secondary": active_secondary[:2],
        "next_primary": next_primary[:1],
        "next_secondary": next_secondary[:1],
        "headline": _hero_headline(active_primary, active_secondary, next_primary, next_secondary),
    }


def _hero_headline(
    active_primary: list[dict],
    active_secondary: list[dict],
    next_primary: list[dict],
    next_secondary: list[dict],
) -> str:
    if active_primary:
        p = active_primary[0]
        return f"Fortune activation active: {p['label']} until {p['end']}"
    if active_secondary:
        s = active_secondary[0]
        return f"Slow transit active: {s['label']} until {s['end']}"
    if next_primary:
        p = next_primary[0]
        return f"Next major window: {p['label']} from {p['start']}"
    if next_secondary:
        s = next_secondary[0]
        return f"Next slow transit: {s['label']} from {s['start']}"
    return "No major fortune activation in the near horizon."


def compute_indu_lagna(
    natal_chart: dict,
    *,
    dasa_years: int = 90,
    transit_years: int = 10,
) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    moon = pp.get("Moon") or {}
    bd = natal_chart.get("birth_data") or {}

    asc_idx = asc.get("sign_index")
    moon_idx = moon.get("sign_index")
    if asc_idx is None or moon_idx is None:
        raise ValueError("Chart must include ascendant and Moon sign_index.")

    indu_idx = calculate_indu_lagna_index(asc_idx, moon_idx)
    indu_lord = SIGN_LORDS[indu_idx]
    planets_in_indu = _planets_in_sign(pp, indu_idx)
    fortune_planets = sorted({indu_lord, *planets_in_indu})
    relevant = set(fortune_planets)

    ninth_asc_idx = _ninth_sign_index(asc_idx)
    ninth_moon_idx = _ninth_sign_index(moon_idx)
    house_from_lagna = (indu_idx - asc_idx) % 12 + 1

    lord_pdata = pp.get(indu_lord) or {}
    lord_sign_idx = lord_pdata.get("sign_index")
    transit_targets = [{"index": indu_idx, "label": "Indu Lagna"}]
    if lord_sign_idx is not None and lord_sign_idx != indu_idx:
        transit_targets.append({
            "index": lord_sign_idx,
            "label": f"Indu lord ({indu_lord}) sign",
        })

    judgment = _natal_judgment(
        indu_idx, indu_lord, house_from_lagna, planets_in_indu, pp,
        asc_sign_index=int(asc_idx),
    )

    birth_date = bd.get("dob")
    if not birth_date:
        raise ValueError("birth_data.dob required for fortune timeline.")
    tz_name = bd.get("timezone") or "Asia/Kolkata"

    moon_lon = moon.get("longitude", 0.0)
    dasa_periods = _fortune_dasa_periods(
        moon_lon, birth_date, relevant, years=dasa_years,
    )

    today = datetime.date.today()
    today_str = today.isoformat()
    transit_start = today
    transit_end = today + datetime.timedelta(days=transit_years * 365)

    slow_transits = _scan_transits_in_signs(
        transit_targets,
        list(SLOW_TRANSIT_PLANETS),
        transit_start,
        transit_end,
        tz_name,
        activation_tier="secondary",
    )
    fast_fortune = [p for p in fortune_planets if p in FAST_TRANSIT_PLANETS]
    fast_transits = _scan_transits_in_signs(
        [{"index": indu_idx, "label": "Indu Lagna"}],
        fast_fortune,
        transit_start,
        transit_end,
        tz_name,
        activation_tier="minor",
    )

    hero = _hero_block(dasa_periods, slow_transits, today_str, judgment["verdict_label"])

    return {
        "indu_lagna": {
            **_sign_label(indu_idx),
            "lord": indu_lord,
            "house_from_lagna": house_from_lagna,
            "ninth_from_lagna": _sign_label(ninth_asc_idx),
            "ninth_from_moon": _sign_label(ninth_moon_idx),
            "rasi_value_sum": {
                "ninth_from_lagna": RASI_VALUES[ninth_asc_idx],
                "ninth_from_moon": RASI_VALUES[ninth_moon_idx],
            },
        },
        "natal_judgment": judgment,
        "natal": {
            "ascendant": _sign_label(asc_idx),
            "moon": _sign_label(moon_idx),
            "planets_in_indu_lagna": [
                {"planet": p, **(pp.get(p) or {})} for p in planets_in_indu
            ],
        },
        "fortune_planets": fortune_planets,
        "dasa_bhukti_periods": dasa_periods,
        "slow_transits": slow_transits,
        "fast_transits": fast_transits,
        "transit_periods": slow_transits + fast_transits,
        "hero": hero,
        "current": {
            "dasa_bhukti": _filter_by_date(dasa_periods, today_str, active=True),
            "slow_transits": _filter_by_date(slow_transits, today_str, active=True),
            "fast_transits": _filter_by_date(fast_transits, today_str, active=True),
        },
        "upcoming": {
            "dasa_bhukti": _filter_by_date(dasa_periods, today_str, active=False)[:8],
            "slow_transits": _filter_by_date(slow_transits, today_str, active=False)[:8],
            "fast_transits": _filter_by_date(fast_transits, today_str, active=False)[:12],
        },
        "summary": {
            "indu_lagna": RASI_ORDER[indu_idx],
            "indu_lord": indu_lord,
            "natal_verdict": judgment["verdict"],
            "natal_verdict_label": judgment["verdict_label"],
            "fortune_planet_count": len(fortune_planets),
            "dasa_period_count": len(dasa_periods),
            "slow_transit_count": len(slow_transits),
            "fast_transit_count": len(fast_transits),
        },
        "interpretation": {
            "themes": [
                "Financial stability and comfortable living more than sudden windfalls",
                "Support from employers, benefactors, clients, or inheritance themes",
                "Ease of accumulation — saving and holding resources",
            ],
            "disclaimer": (
                "Indu Lagna describes fortune potential and timing themes — not guaranteed "
                "riches or lottery-style gains. Combine natal promise with activation windows."
            ),
        },
        "meta": {
            "dasa_horizon_years": dasa_years,
            "transit_horizon_years": transit_years,
            "transit_targets": [t["label"] for t in transit_targets],
            "dasa_bhukti_engine": "dasha_core Vimshottari (standard antardasha order)",
        },
    }


def indu_context_for_narrator(natal_chart: dict) -> str:
    try:
        data = compute_indu_lagna(natal_chart, dasa_years=90, transit_years=5)
    except Exception:
        return ""

    il = data["indu_lagna"]
    j = data["natal_judgment"]
    lines = [
        "=== Indu Lagna (Fortune / Wealth Lagna) ===",
        f"Indu Lagna: {il['english']} ({il['name']}) · lord {il['lord']} · H{il['house_from_lagna']}",
        f"Natal promise: {j['verdict_label']} — {j['summary']}",
        f"Fortune grahas: {', '.join(data['fortune_planets'])}",
    ]

    if j["occupants"]:
        occ = "; ".join(f"{o['planet']} ({o['tone']})" for o in j["occupants"])
        lines.append(f"Occupants: {occ}")
    lines.append(
        f"Indu lord {j['lord']['planet']}: {j['lord']['dignity']} in {j['lord']['sign']} H{j['lord']['house']}"
    )
    if j["benefic_aspects"]:
        lines.append(f"Benefic aspects on Indu: {', '.join(j['benefic_aspects'])}")

    hero = data["hero"]
    if hero.get("headline"):
        lines.append(hero["headline"])

    lines.append(
        "Frame benefits as stability, support, and accumulation ease — not sudden lottery wealth."
    )
    return "\n".join(lines)
