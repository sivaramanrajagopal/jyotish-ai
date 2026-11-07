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


def in_khara_drekkana(longitude: float, mudakku: dict) -> bool:
    """True only while the planet is in the 10° 22nd-drekkana slice."""
    lon = float(longitude) % 360.0
    sign_idx = int(lon / 30) % 12
    deg = lon % 30
    return (
        sign_idx == mudakku["sign_idx"]
        and mudakku["degree_lo"] <= deg < mudakku["degree_hi"]
    )


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
    tz_name: str = "Asia/Kolkata",
) -> dict:
    if ref_dt is None:
        ref_dt = datetime.datetime.now(datetime.timezone.utc)
    jd = _jd(ref_dt)

    soonya_rasis = profile["soonya_rasis"]
    chandrashtama_idx = profile["chandrashtama_sign_idx"]
    mudakku = profile["mudakku"]
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
        in_mudakku = in_khara_drekkana(p_lon, mudakku)

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
        "transit_date": _jd_to_local(jd, tz_name).date().isoformat(),
        "planets": status,
    }


def _moon_sign_at(jd: float) -> int:
    lon, _ = _lon_at(jd, "Moon")
    return int(lon / 30) % 12


def _crossing_jd(jd_a: float, jd_b: float, value_at) -> float:
    """First moment in (jd_a, jd_b], to the minute, where value_at differs from its value at jd_a."""
    start = value_at(jd_a)
    lo, hi = jd_a, jd_b
    while hi - lo > 1.0 / 1440:
        mid = (lo + hi) / 2
        if value_at(mid) == start:
            lo = mid
        else:
            hi = mid
    return hi


def _sign_change_jd(jd_a: float, jd_b: float) -> float:
    """First moment in (jd_a, jd_b] where the Moon's sign differs from its sign at jd_a."""
    return _crossing_jd(jd_a, jd_b, _moon_sign_at)


def _nak_at(jd: float, planet_name: str) -> int:
    lon, _ = _lon_at(jd, planet_name)
    return int(lon / _NAK_SPAN) % 27


def _jd_to_local(jd: float, tz_name: str) -> datetime.datetime:
    from zoneinfo import ZoneInfo
    y, m, d, h = swe.revjul(jd)
    utc = datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=h)
    try:
        return utc.astimezone(ZoneInfo(tz_name)).replace(second=0, microsecond=0)
    except Exception:
        return utc.replace(second=0, microsecond=0)


def find_chandrashtama_windows(
    sign_idx: int, ref_jd: float, days_ahead: int, tz_name: str = "Asia/Kolkata",
) -> list[dict]:
    """Moon-in-the-8th-from-natal-Moon spans, from exact sign entry to exact exit."""
    step = 0.25
    spans: list[tuple[float, float]] = []
    start = None
    if _moon_sign_at(ref_jd) == sign_idx:
        back = ref_jd
        while _moon_sign_at(back - step) == sign_idx:
            back -= step
        start = _sign_change_jd(back - step, back)
    jd = ref_jd
    end_jd = ref_jd + days_ahead
    while jd < end_jd:
        nxt = jd + step
        a, b = _moon_sign_at(jd), _moon_sign_at(nxt)
        if a != b:
            t = _sign_change_jd(jd, nxt)
            if b == sign_idx:
                start = t
            elif a == sign_idx and start is not None:
                spans.append((start, t))
                start = None
        jd = nxt
    if start is not None:
        nxt = start
        while _moon_sign_at(nxt) == sign_idx:
            nxt += step
        spans.append((start, _sign_change_jd(nxt - step, nxt)))

    out = []
    for s, e in spans:
        s_dt, e_dt = _jd_to_local(s, tz_name), _jd_to_local(e, tz_name)
        out.append({
            "start_date": s_dt.date().isoformat(),
            "end_date": e_dt.date().isoformat(),
            "start_time": s_dt.isoformat(),
            "end_time": e_dt.isoformat(),
            "days_away": max(0, int(s - ref_jd)),
            "duration_days": round(e - s, 1),
            "active_now": s <= ref_jd < e,
        })
    return out


def scan_all_dosha_transits(
    profile: dict,
    ref_dt: datetime.datetime,
    days_ahead: int = 90,
    tz_name: str = "Asia/Kolkata",
) -> dict:
    chandrashtama_sign_idx = profile["chandrashtama_sign_idx"]
    vadhai_nak_idx = profile["vadhai_nak_idx"]
    vainasikam_nak_idx = profile["vainasikam_nak_idx"]
    soonya_rasis = profile["soonya_rasis"]
    janma_nak_idx = profile["janma_nak_idx"]

    ref_jd = _jd(ref_dt)
    end_jd = ref_jd + days_ahead

    def local_date(jd: float) -> str:
        return _jd_to_local(jd, tz_name).date().isoformat()

    def days_away(jd: float) -> int:
        return max(0, int(jd - ref_jd))

    red_zone_entries: list[dict] = []
    critical_windows: list[dict] = []
    tara_windows: list[dict] = []

    moon_nak = _nak_at(ref_jd, "Moon")
    tara_now = get_tara(moon_nak, janma_nak_idx)
    if tara_now["tara_num"] in _FAVORABLE_TARAS:
        tara_windows.append({
            "tara_num": tara_now["tara_num"],
            "tara_name": tara_now["tara_name"],
            "tara_nature": tara_now["tara_nature"],
            "nak_name": NAKSHATRA_ORDER[moon_nak],
            "entry_date": local_date(ref_jd),
            "days_away": 0,
        })

    # Entries from the last day count as current. The Moon can cross a whole
    # nakshatra (13°20') in under a day, so it is stepped every 2 hours.
    for p_name in (*_PLANET_IDS, "Rahu", "Ketu"):
        step = 1.0 / 12 if p_name == "Moon" else 1.0
        jd = ref_jd - 1
        prev = _nak_at(jd, p_name)
        while jd < end_jd:
            nxt = min(jd + step, end_jd)
            curr = _nak_at(nxt, p_name)
            if curr != prev:
                t = _crossing_jd(jd, nxt, lambda x: _nak_at(x, p_name))
                curr = _nak_at(t, p_name)
                for nak_idx, nak_type in (
                    (vadhai_nak_idx, "Vadhai"),
                    (vainasikam_nak_idx, "Vainasikam"),
                ):
                    if curr == nak_idx:
                        pk = check_pushkara(_lon_at(t, p_name)[0])
                        red_zone_entries.append({
                            "planet": p_name,
                            "type": nak_type,
                            "nak_name": NAKSHATRA_ORDER[nak_idx],
                            "entry_date": local_date(t),
                            "days_away": days_away(t),
                            "severity": "CRITICAL" if nak_type == "Vainasikam" else "WARNING",
                            "has_pushkara": pk.get("pushkara", False),
                            "pushkara_zone": pk.get("zone", ""),
                        })
                if p_name == "Moon" and t > ref_jd:
                    tara = get_tara(curr, janma_nak_idx)
                    if tara["tara_num"] in _FAVORABLE_TARAS:
                        tara_windows.append({
                            "tara_num": tara["tara_num"],
                            "tara_name": tara["tara_name"],
                            "tara_nature": tara["tara_nature"],
                            "nak_name": NAKSHATRA_ORDER[curr],
                            "entry_date": local_date(t),
                            "days_away": days_away(t),
                        })
            prev = curr
            jd = nxt

    # A malefic in a Soonya sign turning deep combust or gandanta opens a window.
    was_hard: dict[str, bool] = {}
    for d in range(days_ahead + 1):
        jd = ref_jd + d
        sun_lon = swe.calc_ut(jd, SUN, _FLAGS)[0][0]
        for p_name in _PLANET_IDS:
            if p_name not in _MALEFICS:
                continue
            p_lon, p_retro = _lon_at(jd, p_name)
            curr_sign = int(p_lon / 30)
            combust = check_combustion(sun_lon, p_lon, p_name, p_retro)
            gandanta = check_gandanta(p_lon)
            is_hard = curr_sign in soonya_rasis and bool(combust.get("deep") or gandanta.get("gandanta"))
            if is_hard and not was_hard.get(p_name):
                aff_type = (
                    "Deep Combust + Gandanta"
                    if combust.get("deep") and gandanta.get("gandanta")
                    else ("Gandanta" if gandanta.get("gandanta") else "Deep Combust")
                )
                critical_windows.append({
                    "planet": p_name,
                    "soonya_sign": RASI_ORDER[curr_sign],
                    "affliction_type": aff_type,
                    "has_divine": check_pushkara(p_lon).get("pushkara", False),
                    "date": local_date(jd),
                    "days_away": d,
                })
            was_hard[p_name] = is_hard

    chandrashtama_windows = find_chandrashtama_windows(
        chandrashtama_sign_idx, ref_jd, days_ahead, tz_name,
    )

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
