"""
avastha_agent.py — Sthula / Sukshma planetary state scoring from a natal chart.

Enriches natal planets with dignity, combustion, Athi Vega, and birth Nazhikai
after sunrise, then applies the pure scoring engine in agents.avastha.calc.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import ephemeris as swe
from agents.avastha.calc import (
    PLANET_INDEX,
    evaluate_dasa_bhukti_synergy,
    score_planet,
)
from agents.avastha.remedies import get_remedies_for_planet, is_functional_benefic
from agents.dosha_radar.afflictions import check_combustion
from agents.natal_agent import SIGNS
from agents.prashna.dignity_engine import planetary_state
from dasha_core import find_current_dasha_bhukti, get_nakshatra

PLANET_ORDER = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]

# Classical mean daily motions (°/day) for Athi Vega detection
MEAN_DAILY_MOTION: dict[str, float] = {
    "Sun": 0.9856,
    "Moon": 13.1764,
    "Mars": 0.5240,
    "Mercury": 1.3830,
    "Jupiter": 0.0831,
    "Venus": 1.2070,
    "Saturn": 0.0335,
    "Rahu": 0.0529,
    "Ketu": 0.0529,
}

# (sign, deg_from, deg_to) — inclusive start, exclusive end except 30°
MOOLATRIKONA: dict[str, tuple[str, float, float]] = {
    "Sun": ("Leo", 0.0, 20.0),
    "Moon": ("Taurus", 4.0, 30.0),
    "Mars": ("Aries", 0.0, 12.0),
    "Mercury": ("Virgo", 16.0, 20.0),
    "Jupiter": ("Sagittarius", 0.0, 10.0),
    "Venus": ("Libra", 0.0, 15.0),
    "Saturn": ("Aquarius", 0.0, 20.0),
}

NATURAL_BENEFIC_LORDS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})

_PLANET_SWE_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}


def _to_jd(dt: datetime) -> float:
    utc = dt.astimezone(ZoneInfo("UTC"))
    hour_ut = utc.hour + utc.minute / 60 + utc.second / 3600
    return swe.julday(utc.year, utc.month, utc.day, hour_ut)


def _from_jd(jd: float, tz: ZoneInfo) -> datetime:
    y, m, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    second = int(((h - hour) * 60 - minute) * 60)
    dt_utc = datetime(y, m, d, hour, minute, second, tzinfo=ZoneInfo("UTC"))
    return dt_utc.astimezone(tz)


def _sunrise_on_local_date(local_date: datetime, lat: float, lon: float, tz: ZoneInfo) -> datetime | None:
    """Sunrise for the local calendar day of local_date."""
    local_midnight = datetime(
        local_date.year, local_date.month, local_date.day, 0, 0, 0, tzinfo=tz,
    )
    jd_midnight = _to_jd(local_midnight)
    geopos = (lon, lat, 0.0)
    ret_r, tret_r = swe.rise_trans(jd_midnight, swe.SUN, 1, geopos, 0.0, 0.0)
    if ret_r != 0:
        return None
    return _from_jd(tret_r[0], tz)


def birth_nazhikai_after_sunrise(
    dob: str, tob: str, lat: float, lon: float, timezone: str,
) -> dict:
    """
    Nazhikai after sunrise (1 Nazhika = 24 minutes).
    If birth is before that day's sunrise, count from the previous sunrise.
    """
    tz = ZoneInfo(timezone)
    birth_dt = datetime.strptime(f"{dob} {tob}:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
    sunrise = _sunrise_on_local_date(birth_dt, lat, lon, tz)
    if sunrise is None:
        return {
            "nazhikai": 0.0,
            "naazhigai": None,
            "vinazhigai": None,
            "sunrise_local": None,
            "minutes_after_sunrise": 0.0,
            "note": "Sunrise unavailable; nazhikai defaulted to 0.",
        }
    if birth_dt < sunrise:
        prev = birth_dt - timedelta(days=1)
        sunrise = _sunrise_on_local_date(prev, lat, lon, tz) or sunrise

    total_seconds = max(0.0, (birth_dt - sunrise).total_seconds())
    minutes = total_seconds / 60.0
    # 1 naazhigai = 24 minutes. 1 vinazhigai = 24 seconds (60 in a naazhigai).
    naazhigai = int(total_seconds // (24 * 60))
    vinazhigai = int(round((total_seconds % (24 * 60)) / 24.0))
    if vinazhigai >= 60:
        naazhigai += 1
        vinazhigai = 0
    return {
        "nazhikai": round(minutes / 24.0, 4),
        "naazhigai": naazhigai,
        "vinazhigai": vinazhigai,
        "sunrise_local": sunrise.isoformat(),
        "minutes_after_sunrise": round(minutes, 2),
        "note": None,
    }


def _is_moolatrikona(planet: str, sign: str, degree_in_sign: float) -> bool:
    spec = MOOLATRIKONA.get(planet)
    if not spec:
        return False
    mt_sign, lo, hi = spec
    if sign != mt_sign:
        return False
    deg = float(degree_in_sign)
    return lo <= deg < hi or (hi == 30.0 and deg >= lo and deg <= 30.0)


def classify_sign_dignity(planet: str, sign: str, degree_in_sign: float) -> str:
    """Map engine dignity → prompt SignDignity labels (with Moolatrikona / Benefic)."""
    if planet in ("Rahu", "Ketu"):
        return "Neutral"

    if _is_moolatrikona(planet, sign, degree_in_sign):
        return "Moolatrikona"

    state, _ = planetary_state(planet, sign, degree_in_sign)
    if state == "Debilitated":
        return "Debilitated"
    if state == "Exalted":
        return "Exalted"
    if state == "Own Sign":
        return "Own"
    if state == "Friend":
        return "Friendly"
    if state == "Enemy":
        return "Inimical"

    # Neutral: Benefic if sign lord is a natural benefic
    from agents.natal_agent import SIGN_LORDS
    lord = SIGN_LORDS.get(sign, "")
    if lord in NATURAL_BENEFIC_LORDS:
        return "Benefic"
    return "Neutral"


def _planet_speeds(jd: float) -> dict[str, float]:
    """Absolute sidereal daily motion °/day for Athi Vega."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    speeds: dict[str, float] = {}
    for name, pid in _PLANET_SWE_IDS.items():
        xx, _ = swe.calc_ut(jd, pid, flags)
        speeds[name] = abs(float(xx[3]))
    # Mean node speed for Rahu; Ketu same magnitude
    from ephemeris import RAHU_NODE
    xx, _ = swe.calc_ut(jd, RAHU_NODE, flags)
    node_spd = abs(float(xx[3]))
    speeds["Rahu"] = node_spd
    speeds["Ketu"] = node_spd
    return speeds


def _is_accelerated(planet: str, speed: float) -> bool:
    """Athi Vega: daily motion clearly above classical mean (≥ 1.25×)."""
    mean = MEAN_DAILY_MOTION.get(planet)
    if mean is None or mean <= 0:
        return False
    return float(speed) >= mean * 1.25


def compute_avastha_analysis(natal_chart: dict) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    bd = natal_chart.get("birth_data") or {}

    asc_idx0 = asc.get("sign_index")
    if asc_idx0 is None:
        raise ValueError("Chart must include ascendant sign_index.")

    dob = bd.get("dob")
    tob = bd.get("tob")
    lat = bd.get("lat")
    lon = bd.get("lon")
    timezone = bd.get("timezone") or "Asia/Kolkata"
    if not dob or not tob or lat is None or lon is None:
        raise ValueError("birth_data.dob, tob, lat, lon required for Avastha.")

    moon = pp.get("Moon") or {}
    moon_lon = float(moon.get("longitude") or 0.0)
    _, _, moon_nak_0 = get_nakshatra(moon_lon)
    # Prefer chart field when present (0-based)
    if natal_chart.get("moon_nakshatra_index") is not None:
        moon_nak_0 = int(natal_chart["moon_nakshatra_index"])

    janma_nak_1 = moon_nak_0 + 1  # prompt 1–27
    lagna_rasi_1 = int(asc_idx0) + 1  # prompt 1–12

    naz = birth_nazhikai_after_sunrise(dob, tob, float(lat), float(lon), timezone)
    nazhikai = float(naz["nazhikai"])

    tz = ZoneInfo(timezone)
    birth_dt = datetime.strptime(f"{dob} {tob}:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
    jd = _to_jd(birth_dt)
    speeds = _planet_speeds(jd)

    sun_lon = float((pp.get("Sun") or {}).get("longitude") or 0.0)

    planets_out: list[dict] = []
    by_name: dict[str, dict] = {}

    for pname in PLANET_ORDER:
        pdata = pp.get(pname) or {}
        lon = float(pdata.get("longitude") or 0.0)
        sign = pdata.get("sign") or SIGNS[int(pdata.get("sign_index") or 0)]
        deg = float(pdata.get("degree_in_sign") or (lon % 30))
        sign_idx0 = pdata.get("sign_index")
        if sign_idx0 is None:
            sign_idx0 = SIGNS.index(sign) if sign in SIGNS else int(lon // 30) % 12

        _, _, nak_0 = get_nakshatra(lon)
        retro = bool(pdata.get("retrograde"))
        # Nodes are not classically combust; skip Sun-orb check for Rahu/Ketu
        if pname in ("Rahu", "Ketu", "Sun"):
            combust = False
        else:
            combust = check_combustion(sun_lon, lon, pname, retro).get("combust", False)
        speed = speeds.get(pname, 0.0)
        accelerated = _is_accelerated(pname, speed)
        dignity = classify_sign_dignity(pname, sign, deg)

        row = score_planet(
            planet_name=pname,
            planet_index=PLANET_INDEX[pname],
            rasi_index=int(sign_idx0) + 1,
            nakshatra_index=nak_0 + 1,
            degree_in_rasi=deg,
            is_retrograde=retro,
            is_combust=bool(combust),
            is_accelerated=accelerated,
            sign_dignity=dignity,
            janma_nakshatra_index=janma_nak_1,
            lagna_rasi_index=lagna_rasi_1,
            birth_nazhikai_after_sunrise=nazhikai,
        )
        row["sign"] = sign
        row["speed_deg_per_day"] = round(speed, 4)
        functional = is_functional_benefic(pname, lagna_rasi_1)
        row["functional_benefic"] = functional
        row["remedy"] = get_remedies_for_planet(
            pname,
            row["sthula"]["name"],
            row["sukshma"]["name"],
            row["manifestation"]["net"],
            functional_benefic=functional,
        )
        planets_out.append(row)
        by_name[pname] = row

    # Current Dasa–Bhukti from chart.dasha when present, else compute
    dasha = natal_chart.get("dasha") or {}
    maha = ((dasha.get("mahadasha") or {}).get("planet")
            or (dasha.get("maha_dasa") or {}).get("planet"))
    bhukti = ((dasha.get("bhukti") or {}).get("planet")
              or (dasha.get("antardasha") or {}).get("planet"))
    if not maha or not bhukti:
        _, cur_d, _, cur_b = find_current_dasha_bhukti(moon_lon, dob)
        maha = cur_d["planet"]
        bhukti = cur_b["planet"]

    dasa_net = float((by_name.get(maha) or {}).get("manifestation", {}).get("net") or 0)
    bhukti_net = float((by_name.get(bhukti) or {}).get("manifestation", {}).get("net") or 0)
    synergy = evaluate_dasa_bhukti_synergy(maha, bhukti, dasa_net, bhukti_net)

    avg_net = round(sum(p["manifestation"]["net"] for p in planets_out) / len(planets_out), 2)
    peak = max(planets_out, key=lambda p: p["manifestation"]["net"])
    low = min(planets_out, key=lambda p: p["manifestation"]["net"])

    return {
        "summary": {
            "avg_manifestation": avg_net,
            "peak_planet": peak["planet"],
            "peak_net": peak["manifestation"]["net"],
            "lowest_planet": low["planet"],
            "lowest_net": low["manifestation"]["net"],
            "current_dasa": maha,
            "current_bhukti": bhukti,
            "janma_nakshatra_index": janma_nak_1,
            "lagna_rasi_index": lagna_rasi_1,
            "birth_nazhikai_after_sunrise": nazhikai,
            "sunrise_local": naz.get("sunrise_local"),
        },
        "metadata": {
            "janmaNakshatraIndex": janma_nak_1,
            "lagnaRasiIndex": lagna_rasi_1,
            "birthNazhikaiAfterSunrise": nazhikai,
            "sunrise_local": naz.get("sunrise_local"),
            "minutes_after_sunrise": naz.get("minutes_after_sunrise"),
            "nazhikai_note": naz.get("note"),
        },
        "planets": planets_out,
        "dasa_bhukti": synergy,
        "hero": {
            "headline": (
                f"Peak condition: {peak['planet']} at {peak['manifestation']['net']}% "
                f"({peak['sthula']['name']} / {peak['sukshma']['name']}). "
                f"Current Dasa–Bhukti {maha}–{bhukti}: {synergy['combinedScore']}% "
                f"({synergy['manifestationClass']})."
            ),
        },
        "disclaimer": {
            "en": "Analytical aid only — scores quantify classical Sthula/Sukshma planetary states. Not medical, legal, or financial advice.",
            "ta": "பகுப்பாய்வு உதவி மட்டும் — ஸ்தூல/சூக்ஷ்ம அவஸ்தா மதிப்பெண்கள். மருத்துவ/சட்ட/நிதி ஆலோசனை அல்ல.",
        },
        "scoring_legend": {
            "sthula_capacity": {
                "Deepta": 90, "Sthamitha": 80, "Muditha": 70, "Santha": 60,
                "Sakta": 55, "Heenasakstha": 45, "Deena": 35, "Peethya": 30,
                "Peeda": 25, "Vikala": 15, "Kala": 15,
            },
            "soft_penalties": {
                "athi_vega": -15,
                "retrograde": -10,
                "nodes_skip_retro_penalty": True,
                "capacity_floor": 15,
            },
            "net_method": "geometric_mean sqrt(capacity × efficiency)",
            "dasa_bhukti_method": "average of two natal nets",
            "sukshma_efficiency": {
                "Prakasha": 100, "Aasthani": 100, "Bhoji": 85, "Aagamana": 85,
                "Nritya": 80, "Aagama": 80, "Netrapani": 70, "Kauthuka": 70,
                "Upaveshana": 60, "Gamana": 50, "Sayana": 30, "Nidra": 15,
            },
            "sthula_priority": [
                "Combust→Vikala", "Debilitated→Kala", "Degree≥29→Peethya",
                "then dignity (retro→Sakta only if not exalted/MT/own)",
                "soft: Athi Vega −15, Retro −10 (not nodes)",
            ],
        },
    }


def evaluate_synergy_from_analysis(
    analysis: dict, dasa_lord: str, bhukti_lord: str,
) -> dict:
    by_name = {p["planet"]: p for p in analysis.get("planets") or []}
    d = by_name.get(dasa_lord)
    b = by_name.get(bhukti_lord)
    if not d or not b:
        raise ValueError(f"Unknown planet in synergy: {dasa_lord}/{bhukti_lord}")
    return evaluate_dasa_bhukti_synergy(
        dasa_lord,
        bhukti_lord,
        d["manifestation"]["net"],
        b["manifestation"]["net"],
    )
