"""Obstruction dosha transit scan + live status (ported from obstruction_dosha.py)."""

from __future__ import annotations

import datetime

import ephemeris as swe
from agents.dosha_radar.afflictions import check_combustion, check_critical_obstruction, check_gandanta
from agents.dosha_radar.pushkara import check_pushkara
from agents.tamil_dosha.constants import NAKSHATRA_ORDER, RASI_ENGLISH, RASI_ORDER
from agents.tamil_dosha.utils import nakshatra_index_from_longitude, rasi_index_from_longitude
from ephemeris import (
    FLG_SIDEREAL, FLG_SPEED, JUPITER, MARS, MERCURY, MOON, RAHU_NODE, SATURN, SUN, VENUS,
)

_FLAGS = FLG_SIDEREAL | FLG_SPEED
_NAK_SPAN = 360.0 / 27.0

_PLANET_IDS = {
    "Sun": SUN, "Moon": MOON, "Mars": MARS, "Mercury": MERCURY,
    "Jupiter": JUPITER, "Venus": VENUS, "Saturn": SATURN,
}
_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_NODE_COMBUST = {
    "combust": False, "deep": False, "orb": 0.0,
    "cross_sign": False, "would_combust": False, "na": True,
}
_NO_DOSHA = {
    "critical": False, "mild": False, "severity": "none",
    "has_divine_protection": False, "in_soonya": False,
    "visha_gati_note": "", "visha_gati_note_ta": "",
}

TARA_NAMES: dict[int, tuple[str, str, str]] = {
    1: ("Janma", "neutral", "Birth star — sensitive period"),
    2: ("Sampat", "favorable", "Wealth & prosperity"),
    3: ("Vipat", "unfavorable", "Danger & loss — avoid major moves"),
    4: ("Kshema", "favorable", "Well-being & safety"),
    5: ("Pratyak", "unfavorable", "Obstacles — delay launches"),
    6: ("Sadhaka", "favorable", "Achievement — pursue goals"),
    7: ("Vadha", "unfavorable", "Danger (= Vadhai)"),
    8: ("Mitra", "favorable", "Friendly — partnerships"),
    9: ("Parama Mitra", "favorable", "Most auspicious — major decisions"),
}
_FAVORABLE_TARAS = {2, 4, 6, 8, 9}


def _iso_date(dt: datetime.datetime | datetime.date | str | None) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt[:10]
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d")
    return dt.isoformat()


def get_vadhai_vainasikam(janma_nak_idx: int) -> dict:
    vadhai_idx = (int(janma_nak_idx) + 6) % 27
    vainasikam_idx = (int(janma_nak_idx) + 21) % 27
    return {
        "vadhai_idx": vadhai_idx,
        "vadhai_name": NAKSHATRA_ORDER[vadhai_idx],
        "vainasikam_idx": vainasikam_idx,
        "vainasikam_name": NAKSHATRA_ORDER[vainasikam_idx],
    }


def get_chandrashtama_sign(natal_moon_sign_idx: int) -> int:
    return (int(natal_moon_sign_idx) + 7) % 12


def get_mudakku_rasi(lagna_longitude: float) -> dict:
    lagna_sign = int(float(lagna_longitude) / 30) % 12
    lagna_deg = float(lagna_longitude) % 30
    lagna_drek = int(lagna_deg / 10)
    total_drek = lagna_sign * 3 + lagna_drek
    khara_pos = (total_drek + 21) % 36
    sign_idx = khara_pos // 3
    drek_within = khara_pos % 3
    degree_lo = drek_within * 10
    return {
        "sign_idx": sign_idx,
        "sign_name": RASI_ORDER[sign_idx],
        "sign_english": RASI_ENGLISH[sign_idx],
        "degree_lo": degree_lo,
        "degree_hi": degree_lo + 10,
        "drekkana_num": drek_within + 1,
    }


def get_tara(transit_nak_idx: int, janma_nak_idx: int) -> dict:
    distance = (int(transit_nak_idx) - int(janma_nak_idx)) % 27
    tara_num = (distance % 9) + 1
    name, nature, tip = TARA_NAMES[tara_num]
    return {
        "tara_num": tara_num,
        "tara_name": name,
        "tara_nature": nature,
        "tara_tip": tip,
    }


def _jd(dt: datetime.datetime) -> float:
    return swe.julday(
        dt.year, dt.month, dt.day,
        dt.hour + dt.minute / 60.0 + dt.second / 3600.0,
    )


def _lon_at(jd: float, planet_name: str) -> tuple[float, bool]:
    if planet_name == "Rahu":
        xx, _ = swe.calc_ut(jd, RAHU_NODE, _FLAGS)
        return xx[0] % 360, xx[3] < 0
    if planet_name == "Ketu":
        xx, _ = swe.calc_ut(jd, RAHU_NODE, _FLAGS)
        lon = (xx[0] + 180.0) % 360
        return lon, xx[3] < 0
    pid = _PLANET_IDS[planet_name]
    xx, _ = swe.calc_ut(jd, pid, _FLAGS)
    return xx[0] % 360, xx[3] < 0


def build_obstruction_profile(natal_chart: dict, tamil_doshas: dict) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    moon = pp.get("Moon") or {}
    thithi = tamil_doshas.get("thithi_soonyam") or {}
    red = tamil_doshas.get("red_zones") or {}

    lagna_idx = asc.get("sign_index")
    if lagna_idx is None:
        lagna_idx = rasi_index_from_longitude(asc.get("longitude", 0))
    lagna_lon = float(asc.get("longitude", lagna_idx * 30))

    moon_nak_idx = nakshatra_index_from_longitude(moon.get("longitude", 0))
    moon_sign_idx = moon.get("sign_index", rasi_index_from_longitude(moon.get("longitude", 0)))
    vv = get_vadhai_vainasikam(moon_nak_idx)
    mudakku = get_mudakku_rasi(lagna_lon)
    soonya_rasis = [r["index"] for r in thithi.get("dagdha_rasis") or []]

    return {
        "soonya_rasis": soonya_rasis,
        "soonya_signs": [RASI_ORDER[i] for i in soonya_rasis],
        "soonya_signs_english": [RASI_ENGLISH[i] for i in soonya_rasis],
        "tithi_name": thithi.get("tithi_name"),
        "paksha": thithi.get("paksha"),
        "moon_nak_name": moon.get("nakshatra") or NAKSHATRA_ORDER[moon_nak_idx],
        "moon_nak_idx": moon_nak_idx,
        "vadhai_nak_idx": red.get("vadhai", {}).get("index", vv["vadhai_idx"]),
        "vadhai_nak_name": red.get("vadhai", {}).get("name", vv["vadhai_name"]),
        "vainasikam_nak_idx": red.get("vainasikam", {}).get("index", vv["vainasikam_idx"]),
        "vainasikam_nak_name": red.get("vainasikam", {}).get("name", vv["vainasikam_name"]),
        "chandrashtama_sign_idx": get_chandrashtama_sign(moon_sign_idx),
        "chandrashtama_sign": RASI_ORDER[get_chandrashtama_sign(moon_sign_idx)],
        "chandrashtama_english": RASI_ENGLISH[get_chandrashtama_sign(moon_sign_idx)],
        "mudakku": mudakku,
        "mudakku_house": (mudakku["sign_idx"] - lagna_idx) % 12 + 1,
        "lagna_sign_idx": lagna_idx,
        "janma_nak_idx": moon_nak_idx,
    }


def compute_live_transit_status(
    natal_chart: dict,
    profile: dict,
    ref_dt: datetime.datetime | None = None,
) -> dict:
    if ref_dt is None:
        ref_dt = datetime.datetime.now(datetime.timezone.utc)
    jd = _jd(ref_dt)

    soonya_rasis = profile["soonya_rasis"]
    chandrashtama_idx = profile["chandrashtama_sign_idx"]
    mudakku_sign_idx = profile["mudakku"]["sign_idx"]
    vadhai_nak_idx = profile["vadhai_nak_idx"]
    vainasikam_nak_idx = profile["vainasikam_nak_idx"]
    lagna_sign_idx = profile["lagna_sign_idx"]
    janma_nak_idx = profile["janma_nak_idx"]

    sun_xx, _ = swe.calc_ut(jd, SUN, _FLAGS)
    sun_lon = sun_xx[0]

    status: dict[str, dict] = {}
    scan_planets = list(_PLANET_IDS.keys()) + ["Rahu", "Ketu"]

    for p_name in scan_planets:
        p_lon, p_retro = _lon_at(jd, p_name)
        p_sign = int(p_lon / 30)
        p_nak = int(p_lon / _NAK_SPAN) % 27

        combust = (
            check_combustion(sun_lon, p_lon, p_name, p_retro)
            if p_name not in ("Sun", "Rahu", "Ketu")
            else _NODE_COMBUST if p_name != "Sun" else _NODE_COMBUST
        )
        if p_name == "Sun":
            combust = _NODE_COMBUST

        gandanta = check_gandanta(p_lon)
        pushkara = check_pushkara(p_lon)

        in_soonya = p_sign in soonya_rasis
        in_chandrashtama = p_name == "Moon" and p_sign == chandrashtama_idx
        in_mudakku = p_sign == mudakku_sign_idx

        red_zone_raw = None
        if p_nak == vainasikam_nak_idx:
            red_zone_raw = "Vainasikam"
        elif p_nak == vadhai_nak_idx:
            red_zone_raw = "Vadhai"
        red_zone = "Transformational" if (red_zone_raw and pushkara.get("pushkara")) else red_zone_raw

        crit = (
            check_critical_obstruction(
                {"sign_idx": p_sign, "combust": combust, "gandanta": gandanta, "pushkara": pushkara},
                soonya_rasis,
            )
            if p_name not in ("Rahu", "Ketu")
            else _NO_DOSHA.copy()
        )

        status[p_name] = {
            "sign_idx": p_sign,
            "sign": RASI_ORDER[p_sign],
            "sign_english": RASI_ENGLISH[p_sign],
            "nak_name": NAKSHATRA_ORDER[p_nak],
            "house_num": (p_sign - lagna_sign_idx) % 12 + 1,
            "in_soonya": in_soonya,
            "in_chandrashtama": in_chandrashtama,
            "in_mudakku": in_mudakku,
            "red_zone": red_zone,
            "red_zone_raw": red_zone_raw,
            "combust": combust,
            "gandanta": gandanta,
            "pushkara": pushkara,
            "critical_obstruction": crit,
            "tara": get_tara(p_nak, janma_nak_idx),
        }

    return {
        "transit_date": _iso_date(ref_dt),
        "planets": status,
    }


def scan_all_dosha_transits(
    profile: dict,
    ref_dt: datetime.datetime,
    days_ahead: int = 90,
) -> dict:
    chandrashtama_sign_idx = profile["chandrashtama_sign_idx"]
    vadhai_nak_idx = profile["vadhai_nak_idx"]
    vainasikam_nak_idx = profile["vainasikam_nak_idx"]
    soonya_rasis = profile["soonya_rasis"]
    janma_nak_idx = profile["janma_nak_idx"]

    ref_jd = _jd(ref_dt)
    prev_nak: dict[str, int] = {}
    seed_jd = ref_jd - 1
    for p_name in _PLANET_IDS:
        lon, _ = _lon_at(seed_jd, p_name)
        prev_nak[p_name] = int(lon / _NAK_SPAN) % 27
    rahu_lon, _ = _lon_at(seed_jd, "Rahu")
    prev_nak["Rahu"] = int(rahu_lon / _NAK_SPAN) % 27
    prev_nak["Ketu"] = int(((rahu_lon + 180) % 360) / _NAK_SPAN) % 27

    chandrashtama_windows: list[dict] = []
    red_zone_entries: list[dict] = []
    critical_windows: list[dict] = []
    tara_windows: list[dict] = []

    in_chandra = False
    chandra_start_day = 0
    prev_moon_tara = 0

    for d in range(days_ahead + 1):
        jd = ref_jd + d
        day_date = ref_dt + datetime.timedelta(days=d)

        sun_xx, _ = swe.calc_ut(jd, SUN, _FLAGS)
        sun_lon = sun_xx[0]

        for p_name in _PLANET_IDS:
            p_lon, p_retro = _lon_at(jd, p_name)
            curr_nak = int(p_lon / _NAK_SPAN) % 27
            curr_sign = int(p_lon / 30)

            if p_name == "Moon":
                moon_tara = get_tara(curr_nak, janma_nak_idx)
                if moon_tara["tara_num"] != prev_moon_tara:
                    if moon_tara["tara_num"] in _FAVORABLE_TARAS:
                        tara_windows.append({
                            "tara_num": moon_tara["tara_num"],
                            "tara_name": moon_tara["tara_name"],
                            "tara_nature": moon_tara["tara_nature"],
                            "nak_name": NAKSHATRA_ORDER[curr_nak],
                            "entry_date": _iso_date(day_date),
                            "days_away": d,
                        })
                    prev_moon_tara = moon_tara["tara_num"]

                if curr_sign == chandrashtama_sign_idx:
                    if not in_chandra:
                        in_chandra = True
                        chandra_start_day = d
                elif in_chandra:
                    in_chandra = False
                    chandrashtama_windows.append({
                        "start_date": _iso_date(ref_dt + datetime.timedelta(days=chandra_start_day)),
                        "end_date": _iso_date(day_date),
                        "days_away": chandra_start_day,
                        "duration_days": d - chandra_start_day,
                    })

            if curr_nak != prev_nak[p_name]:
                for nak_idx, nak_type in (
                    (vadhai_nak_idx, "Vadhai"),
                    (vainasikam_nak_idx, "Vainasikam"),
                ):
                    if curr_nak == nak_idx:
                        pk = check_pushkara(p_lon)
                        red_zone_entries.append({
                            "planet": p_name,
                            "type": nak_type,
                            "nak_name": NAKSHATRA_ORDER[nak_idx],
                            "entry_date": _iso_date(day_date),
                            "days_away": d,
                            "severity": "CRITICAL" if nak_type == "Vainasikam" else "WARNING",
                            "has_pushkara": pk.get("pushkara", False),
                            "pushkara_zone": pk.get("zone", ""),
                        })
            prev_nak[p_name] = curr_nak

            if p_name in _MALEFICS and curr_sign in soonya_rasis:
                combust = check_combustion(sun_lon, p_lon, p_name, p_retro)
                gandanta = check_gandanta(p_lon)
                pushkara = check_pushkara(p_lon)
                is_hard = combust.get("deep") or gandanta.get("gandanta")
                if is_hard:
                    prev_lon, _ = _lon_at(jd - 1, p_name) if d > 0 else (p_lon, p_retro)
                    prev_sign = int(prev_lon / 30)
                    if d == 0 or prev_sign != curr_sign:
                        aff_type = (
                            "Deep Combust + Gandanta"
                            if combust.get("deep") and gandanta.get("gandanta")
                            else ("Gandanta" if gandanta.get("gandanta") else "Deep Combust")
                        )
                        critical_windows.append({
                            "planet": p_name,
                            "soonya_sign": RASI_ORDER[curr_sign],
                            "affliction_type": aff_type,
                            "has_divine": pushkara.get("pushkara", False),
                            "date": _iso_date(day_date),
                            "days_away": d,
                        })

        for node_name in ("Rahu", "Ketu"):
            node_lon, _ = _lon_at(jd, node_name)
            curr_nak = int(node_lon / _NAK_SPAN) % 27
            if curr_nak != prev_nak[node_name]:
                for nak_idx, nak_type in (
                    (vadhai_nak_idx, "Vadhai"),
                    (vainasikam_nak_idx, "Vainasikam"),
                ):
                    if curr_nak == nak_idx:
                        pk = check_pushkara(node_lon)
                        red_zone_entries.append({
                            "planet": node_name,
                            "type": nak_type,
                            "nak_name": NAKSHATRA_ORDER[nak_idx],
                            "entry_date": _iso_date(day_date),
                            "days_away": d,
                            "severity": "CRITICAL",
                            "has_pushkara": pk.get("pushkara", False),
                            "pushkara_zone": pk.get("zone", ""),
                        })
            prev_nak[node_name] = curr_nak

    if in_chandra:
        chandrashtama_windows.append({
            "start_date": _iso_date(ref_dt + datetime.timedelta(days=chandra_start_day)),
            "end_date": _iso_date(ref_dt + datetime.timedelta(days=days_ahead)),
            "days_away": chandra_start_day,
            "duration_days": days_ahead - chandra_start_day,
        })

    red_zone_entries.sort(key=lambda x: x["days_away"])
    critical_windows.sort(key=lambda x: x["days_away"])
    tara_windows.sort(key=lambda x: x["days_away"])

    return {
        "days_ahead": days_ahead,
        "chandrashtama_windows": chandrashtama_windows,
        "red_zone_entries": red_zone_entries,
        "critical_windows": critical_windows,
        "tara_windows": tara_windows,
    }
