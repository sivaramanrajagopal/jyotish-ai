"""
panchangam_agent.py
====================
Production-grade Vedic Panchangam engine using pyswisseph + Lahiri ayanamsa.

Calculates for any date + location:
  - Vaaram (weekday + lord)
  - Tithi (lunar day, paksha, end time, next tithi)
  - Nakshatra (Moon's asterism, lord, pada, end time, next)
  - Yogam (Sun+Moon sum asterism, end time, next)
  - Karanam (half-tithi, end time, next)
  - Rahu Kalam, Gulikai Kalam, Yamaganda timings

Usage:
    from agents.panchangam_agent import calculate_panchangam
    result = calculate_panchangam("2026-05-30", "Chennai")
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import ephemeris as swe

# ─────────────────────────────────────────────
# Constants & lookup tables
# ─────────────────────────────────────────────

LOCATIONS: dict[str, dict] = {
    "Chennai":    {"lat": 13.0827,  "lon": 80.2707, "tz": "Asia/Kolkata"},
    "Bangalore":  {"lat": 12.9716,  "lon": 77.5946, "tz": "Asia/Kolkata"},
    "Mumbai":     {"lat": 19.0760,  "lon": 72.8777, "tz": "Asia/Kolkata"},
    "Delhi":      {"lat": 28.6139,  "lon": 77.2090, "tz": "Asia/Kolkata"},
    "Hyderabad":  {"lat": 17.3850,  "lon": 78.4867, "tz": "Asia/Kolkata"},
    "Coimbatore": {"lat": 11.0168,  "lon": 76.9558, "tz": "Asia/Kolkata"},
    "Erlangen":   {"lat": 49.5897,  "lon": 11.0078, "tz": "Europe/Berlin"},
}

TITHIS = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
    "Purnima",          # index 14 = Shukla Purnima
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
    "Amavasya",         # index 29
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
]

YOGAS = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

# 7 movable + 4 fixed karanams
MOVABLE_KARANAMS = ["Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija", "Vishti"]
FIXED_KARANAMS = ["Kimstughna", "Shakuni", "Chatushpada", "Naga"]

VAARAM_NAMES = ["Somavaram", "Mangalavaram", "Budhavaram", "Guruvaram",
                "Shukravaram", "Shanivaram", "Bhanuavaram"]
VAARAM_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]

# Slot indices (1-based, day divided into 8 equal parts sunrise→sunset)
# Weekday: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
#
# Rahu Kalam standard times (fixed 6AM–6PM reference → actual slot):
#   Sun=8 (4:30–6PM), Mon=2 (7:30–9AM), Tue=7 (3–4:30PM),
#   Wed=5 (12–1:30PM), Thu=6 (1:30–3PM), Fri=4 (10:30AM–12PM), Sat=3 (9–10:30AM)
RAHU_SLOTS    = [2, 7, 5, 6, 4, 3, 8]
GULIKAI_SLOTS = [6, 5, 4, 3, 2, 1, 7]
YAMAGAN_SLOTS = [4, 3, 2, 1, 7, 6, 5]

# ─────────────────────────────────────────────
# Julian Day helpers (Lahiri via ephemeris wrappers)
# ─────────────────────────────────────────────

def _to_jd(dt: datetime) -> float:
    """Convert a timezone-aware datetime to Julian Day (UT)."""
    # swe.julday expects UT
    utc = dt.astimezone(ZoneInfo("UTC"))
    hour_ut = utc.hour + utc.minute / 60 + utc.second / 3600
    return swe.julday(utc.year, utc.month, utc.day, hour_ut)


def _from_jd(jd: float, tz: ZoneInfo) -> datetime:
    """Convert Julian Day (UT) to timezone-aware local datetime."""
    y, m, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    second = int(((h - hour) * 60 - minute) * 60)
    dt_utc = datetime(y, m, d, hour, minute, second, tzinfo=ZoneInfo("UTC"))
    return dt_utc.astimezone(tz)


# ─────────────────────────────────────────────
# Sidereal longitude helpers
# ─────────────────────────────────────────────

def _moon_lon(jd: float) -> float:
    """Sidereal Moon longitude (Lahiri) in degrees [0, 360)."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    xx, _ = swe.calc_ut(jd, swe.MOON, flags)
    return xx[0] % 360


def _sun_lon(jd: float) -> float:
    """Sidereal Sun longitude (Lahiri) in degrees [0, 360)."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    xx, _ = swe.calc_ut(jd, swe.SUN, flags)
    return xx[0] % 360


def _moon_sun_diff(jd: float) -> float:
    """Moon - Sun sidereal longitude difference, normalised to [0, 360)."""
    return (_moon_lon(jd) - _sun_lon(jd)) % 360


def _moon_sun_sum(jd: float) -> float:
    """(Moon + Sun) sidereal longitude sum, normalised to [0, 360)."""
    return (_moon_lon(jd) + _sun_lon(jd)) % 360


# ─────────────────────────────────────────────
# Binary search for exact end time
# ─────────────────────────────────────────────

def _binary_search_end(
    value_fn,
    current_index: int,
    arc_size: float,
    jd_start: float,
    jd_end_limit: float,
    tolerance_jd: float = 1 / 86400,  # 1-second precision
) -> float | None:
    """
    Find the JD when value_fn(jd) / arc_size changes from current_index
    to current_index + 1.  Returns None if change not found within limit.
    """
    target = (current_index + 1) * arc_size   # degrees at boundary

    def exceeds(jd: float) -> bool:
        return value_fn(jd) >= target

    # Quick check: does it change at all before limit?
    if not exceeds(jd_end_limit):
        return None

    lo, hi = jd_start, jd_end_limit
    while (hi - lo) > tolerance_jd:
        mid = (lo + hi) / 2
        if exceeds(mid):
            hi = mid
        else:
            lo = mid
    return hi


# ─────────────────────────────────────────────
# Sunrise via swe.rise_trans
# ─────────────────────────────────────────────

def _get_sunrise_sunset(
    jd_noon: float, lat: float, lon: float, tz: ZoneInfo
) -> tuple[datetime | None, datetime | None]:
    """
    Compute sunrise and sunset for the calendar day containing jd_noon.
    Uses swe.rise_trans with atmospheric refraction (standard).

    IMPORTANT: searches from LOCAL midnight, not UT midnight.
    For India (UTC+5:30), UT midnight = 5:30 AM IST, leaving only ~22 min
    before sunrise — too tight a window for swe.rise_trans accuracy.
    Using local midnight gives a proper ~6-hour window.
    """
    geopos = (lon, lat, 0.0)

    # Derive the local calendar date from jd_noon, then get local midnight
    local_dt = _from_jd(jd_noon, tz)
    local_midnight = datetime(
        local_dt.year, local_dt.month, local_dt.day,
        0, 0, 0, tzinfo=tz
    )
    jd_local_midnight = _to_jd(local_midnight)   # UT of local midnight

    # swe.rise_trans flags: 1 = CALC_RISE, 2 = CALC_SET
    RISE = 1
    SET  = 2

    ret_r, tret_r = swe.rise_trans(jd_local_midnight, swe.SUN, RISE, geopos, 0.0, 0.0)
    ret_s, tret_s = swe.rise_trans(jd_local_midnight, swe.SUN, SET,  geopos, 0.0, 0.0)

    sunrise = _from_jd(tret_r[0], tz) if ret_r == 0 else None
    sunset  = _from_jd(tret_s[0], tz) if ret_s == 0 else None
    return sunrise, sunset


# ─────────────────────────────────────────────
# Kalam helpers (Rahu, Gulikai, Yamaganda)
# ─────────────────────────────────────────────

def _kalam_times(
    sunrise: datetime, sunset: datetime, slot_1based: int
) -> tuple[datetime, datetime]:
    """Return start/end of an 8-part daytime kalam slot (1-indexed)."""
    day_seconds = (sunset - sunrise).total_seconds()
    slot_secs   = day_seconds / 8
    start = sunrise + timedelta(seconds=slot_secs * (slot_1based - 1))
    end   = start   + timedelta(seconds=slot_secs)
    return start, end


# ─────────────────────────────────────────────
# Karanam index helper
# ─────────────────────────────────────────────

def _karanam_index_and_name(k_raw: int) -> tuple[int, str]:
    """
    Raw karanam index (0-based half-tithi position within the month).
    Fixed karanams: index 0 = Kimstughna (first half of Shukla Pratipada),
                    index 57/58/59 = Shakuni/Chatushpada/Naga.
    Movable: indices 1–56 cycle through the 7 movable karanams.
    Returns (1-based index into combined list, name).
    """
    if k_raw == 0:
        return 1, FIXED_KARANAMS[0]   # Kimstughna
    elif k_raw >= 57:
        fixed_idx = k_raw - 57        # 0, 1, 2
        if fixed_idx < 3:
            return fixed_idx + 2, FIXED_KARANAMS[fixed_idx + 1]
        else:
            return 11, FIXED_KARANAMS[3]
    else:
        mov_idx = (k_raw - 1) % 7
        return mov_idx + 1, MOVABLE_KARANAMS[mov_idx]  # 1-based movable


# ─────────────────────────────────────────────
# Main calculation function
# ─────────────────────────────────────────────

def calculate_panchangam(date_str: str, location: str) -> dict:
    """
    Calculate full Panchangam for a given date and location.

    Args:
        date_str: ISO date string 'YYYY-MM-DD'
        location: Key from LOCATIONS dict (e.g. 'Chennai')

    Returns:
        Dict with all Panchangam fields, ready for Supabase insert.
    """
    if location not in LOCATIONS:
        raise ValueError(f"Unknown location '{location}'. "
                         f"Valid: {list(LOCATIONS.keys())}")

    loc    = LOCATIONS[location]
    tz     = ZoneInfo(loc["tz"])
    lat    = loc["lat"]
    lon    = loc["lon"]

    # Parse date, get local noon as anchor
    d = date.fromisoformat(date_str)
    local_noon  = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=tz)
    jd_noon     = _to_jd(local_noon)

    # Limit binary searches to end of local day
    local_eod   = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=tz)
    jd_eod      = _to_jd(local_eod)

    # Start of day JD (midnight local)
    local_sod   = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
    jd_sod      = _to_jd(local_sod)

    # ── Sunrise / Sunset ──────────────────────────────────────
    sunrise, sunset = _get_sunrise_sunset(jd_noon, lat, lon, tz)

    # ── Vaaram ───────────────────────────────────────────────
    weekday = d.weekday()  # Mon=0 … Sun=6
    vaaram_name  = VAARAM_NAMES[weekday]
    vaaram_lord  = VAARAM_LORDS[weekday]

    # ── Tithi ────────────────────────────────────────────────
    diff_noon = _moon_sun_diff(jd_noon)
    tithi_raw  = int(diff_noon / 12)       # 0–29
    tithi_idx  = tithi_raw                  # 0-based
    tithi_name = TITHIS[tithi_idx]
    tithi_paksha = "Shukla" if tithi_idx < 15 else "Krishna"
    tithi_1based = (tithi_idx % 15) + 1    # 1–15

    tithi_end_jd = _binary_search_end(
        _moon_sun_diff, tithi_idx, 12.0, jd_sod, jd_eod
    )
    tithi_end_dt  = _from_jd(tithi_end_jd, tz) if tithi_end_jd else None
    next_tithi_idx = (tithi_idx + 1) % 30
    next_tithi_name = TITHIS[next_tithi_idx]

    # Next tithi's end (look 36 hours ahead)
    jd_36h = jd_sod + 1.5
    next_tithi_end_jd = _binary_search_end(
        _moon_sun_diff, next_tithi_idx, 12.0,
        tithi_end_jd if tithi_end_jd else jd_eod, jd_36h
    ) if tithi_end_jd else None
    next_tithi_end_dt = _from_jd(next_tithi_end_jd, tz) if next_tithi_end_jd else None

    # ── Nakshatra ────────────────────────────────────────────
    moon_noon   = _moon_lon(jd_noon)
    naks_raw    = moon_noon / (360 / 27)   # 0.0 – 26.999
    naks_idx    = int(naks_raw)             # 0-based (0=Ashwini)
    naks_name   = NAKSHATRAS[naks_idx]
    naks_lord   = NAKSHATRA_LORDS[naks_idx]
    naks_pada   = int((naks_raw - naks_idx) * 4) + 1  # 1–4

    naks_end_jd = _binary_search_end(
        _moon_lon, naks_idx, 360 / 27, jd_sod, jd_eod
    )
    naks_end_dt  = _from_jd(naks_end_jd, tz) if naks_end_jd else None
    next_naks_idx  = (naks_idx + 1) % 27
    next_naks_name = NAKSHATRAS[next_naks_idx]

    next_naks_end_jd = _binary_search_end(
        _moon_lon, next_naks_idx, 360 / 27,
        naks_end_jd if naks_end_jd else jd_eod, jd_eod + 1.0
    ) if naks_end_jd else None
    next_naks_end_dt = _from_jd(next_naks_end_jd, tz) if next_naks_end_jd else None

    # ── Yogam ────────────────────────────────────────────────
    sum_noon  = _moon_sun_sum(jd_noon)
    yoga_raw  = sum_noon / (360 / 27)
    yoga_idx  = int(yoga_raw)   # 0-based
    yoga_name = YOGAS[yoga_idx]

    yoga_end_jd = _binary_search_end(
        _moon_sun_sum, yoga_idx, 360 / 27, jd_sod, jd_eod
    )
    yoga_end_dt  = _from_jd(yoga_end_jd, tz) if yoga_end_jd else None
    next_yoga_idx  = (yoga_idx + 1) % 27
    next_yoga_name = YOGAS[next_yoga_idx]

    next_yoga_end_jd = _binary_search_end(
        _moon_sun_sum, next_yoga_idx, 360 / 27,
        yoga_end_jd if yoga_end_jd else jd_eod, jd_eod + 1.0
    ) if yoga_end_jd else None
    next_yoga_end_dt = _from_jd(next_yoga_end_jd, tz) if next_yoga_end_jd else None

    # ── Karanam ──────────────────────────────────────────────
    # Each karanam = 6° of Moon-Sun diff → half a tithi
    karan_raw_f = diff_noon / 6          # float position in month (0–59.9)
    karan_raw   = int(karan_raw_f)        # 0-based raw index
    karan_1based, karan_name = _karanam_index_and_name(karan_raw)

    karan_end_jd = _binary_search_end(
        _moon_sun_diff, karan_raw, 6.0, jd_sod, jd_eod
    )
    karan_end_dt  = _from_jd(karan_end_jd, tz) if karan_end_jd else None
    next_karan_raw = karan_raw + 1
    next_karan_1based, next_karan_name = _karanam_index_and_name(next_karan_raw % 60)

    next_karan_end_jd = _binary_search_end(
        _moon_sun_diff, next_karan_raw % 60, 6.0,
        karan_end_jd if karan_end_jd else jd_eod, jd_eod + 1.0
    ) if karan_end_jd else None
    next_karan_end_dt = _from_jd(next_karan_end_jd, tz) if next_karan_end_jd else None

    # ── Kalam timings ────────────────────────────────────────
    rahu_start = rahu_end = gulikai_start = gulikai_end = None
    yama_start = yama_end = None

    if sunrise and sunset:
        rahu_s, rahu_e = _kalam_times(sunrise, sunset, RAHU_SLOTS[weekday])
        guli_s, guli_e = _kalam_times(sunrise, sunset, GULIKAI_SLOTS[weekday])
        yama_s, yama_e = _kalam_times(sunrise, sunset, YAMAGAN_SLOTS[weekday])
        rahu_start, rahu_end = rahu_s, rahu_e
        gulikai_start, gulikai_end = guli_s, guli_e
        yama_start, yama_end = yama_s, yama_e

    # ── Ayanamsa value ───────────────────────────────────────
    ayanamsa_val = swe.get_ayanamsa_ut(jd_noon)

    # ── Assemble result ──────────────────────────────────────
    def _fmt(dt: datetime | None) -> str | None:
        return dt.isoformat() if dt else None

    return {
        # Identity
        "date":           date_str,
        "location_name":  location,
        "lat":            lat,
        "lon":            lon,
        "timezone":       loc["tz"],
        "ayanamsa":       "Lahiri",
        "ayanamsa_value": round(ayanamsa_val, 6),

        # Sun
        "sunrise": _fmt(sunrise),
        "sunset":  _fmt(sunset),

        # Vaaram
        "vaaram_name":  vaaram_name,
        "vaaram_lord":  vaaram_lord,

        # Tithi
        "tithi_name":       tithi_name,
        "tithi_paksha":     tithi_paksha,
        "tithi_index":      tithi_1based,
        "tithi_end_time":   _fmt(tithi_end_dt),
        "next_tithi_name":  next_tithi_name,
        "next_tithi_end":   _fmt(next_tithi_end_dt),

        # Nakshatra
        "nakshatra_name":      naks_name,
        "nakshatra_lord":      naks_lord,
        "nakshatra_index":     naks_idx + 1,
        "nakshatra_pada":      naks_pada,
        "nakshatra_end_time":  _fmt(naks_end_dt),
        "next_nakshatra_name": next_naks_name,
        "next_nakshatra_end":  _fmt(next_naks_end_dt),

        # Yogam
        "yogam_name":      yoga_name,
        "yogam_index":     yoga_idx + 1,
        "yogam_end_time":  _fmt(yoga_end_dt),
        "next_yogam_name": next_yoga_name,
        "next_yogam_end":  _fmt(next_yoga_end_dt),

        # Karanam
        "karanam_name":      karan_name,
        "karanam_index":     karan_1based,
        "karanam_end_time":  _fmt(karan_end_dt),
        "next_karanam_name": next_karan_name,
        "next_karanam_end":  _fmt(next_karan_end_dt),

        # Kalam
        "rahu_kalam_start":    _fmt(rahu_start),
        "rahu_kalam_end":      _fmt(rahu_end),
        "gulikai_kalam_start": _fmt(gulikai_start),
        "gulikai_kalam_end":   _fmt(gulikai_end),
        "yamaganda_start":     _fmt(yama_start),
        "yamaganda_end":       _fmt(yama_end),

        "validated":     False,
        "calculated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
    }


# ─────────────────────────────────────────────
# Formatted validation output
# ─────────────────────────────────────────────

def format_validation_output(p: dict) -> str:
    """Human-readable output for Prokerala comparison."""

    def _local(iso: str | None) -> str:
        if not iso:
            return "—"
        try:
            from dateutil.parser import parse as _parse
            from zoneinfo import ZoneInfo
            dt = _parse(iso).astimezone(ZoneInfo("Asia/Kolkata"))
        except Exception:
            return iso
        return dt.strftime("%I:%M %p IST")

    lines = [
        f"╔══════════════════════════════════════════════╗",
        f"  Panchangam  {p['date']}  {p['location_name']}",
        f"  Ayanamsa: {p.get('ayanamsa', 'Lahiri')} {float(p['ayanamsa_value']):.4f}°" if p.get('ayanamsa_value') else f"  Ayanamsa: {p.get('ayanamsa', 'Lahiri')} (from cache)",
        f"╚══════════════════════════════════════════════╝",
        f"",
        f"🌅 Sunrise   : {_local(p['sunrise'])}",
        f"🌇 Sunset    : {_local(p['sunset'])}",
        f"",
        f"📅 Vaaram    : {p['vaaram_name']} (lord: {p['vaaram_lord']})",
        f"",
        f"🌑 Tithi     : {p['tithi_paksha']} {p['tithi_name']} (#{p['tithi_index']})",
        f"   Ends      : {_local(p['tithi_end_time'])}",
        f"   Next      : {p['next_tithi_name']}",
        f"",
        f"⭐ Nakshatra : {p['nakshatra_name']} pada {p['nakshatra_pada']} "
        f"(lord: {p['nakshatra_lord']}, #{p['nakshatra_index']})",
        f"   Ends      : {_local(p['nakshatra_end_time'])}",
        f"   Next      : {p['next_nakshatra_name']}",
        f"",
        f"☯  Yogam     : {p['yogam_name']} (#{p['yogam_index']})",
        f"   Ends      : {_local(p['yogam_end_time'])}",
        f"   Next      : {p['next_yogam_name']}",
        f"",
        f"⚖  Karanam   : {p['karanam_name']} (#{p['karanam_index']})",
        f"   Ends      : {_local(p['karanam_end_time'])}",
        f"   Next      : {p['next_karanam_name']}",
        f"",
        f"🔴 Rahu Kalam: {_local(p['rahu_kalam_start'])} – {_local(p['rahu_kalam_end'])}",
        f"🟡 Gulikai   : {_local(p['gulikai_kalam_start'])} – {_local(p['gulikai_kalam_end'])}",
        f"🟠 Yamaganda : {_local(p['yamaganda_start'])} – {_local(p['yamaganda_end'])}",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Quick standalone test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    from datetime import date as _date
    today = _date.today().isoformat()
    print(f"\nCalculating Panchangam for {today} at Chennai...\n")
    result = calculate_panchangam(today, "Chennai")
    print(format_validation_output(result))
