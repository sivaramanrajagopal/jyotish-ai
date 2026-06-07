"""
tara_engine.py
==============
Computes three personal Jyotish indicators for any date/time:

1. Tara Balam
   The 9-Tara system measures the quality of the current Moon nakshatra
   relative to the native's natal (Janma) nakshatra.
   Formula: tara_position = ((today_nak_index - natal_nak_index) % 27) % 9 + 1

2. Chandra Ashtama
   Moon transiting the 8th sign from the natal Moon rasi.
   Ashtama rasi = (natal_rasi_index + 7) % 12
   Returns whether currently active, plus exact start/end timestamps
   for the Moon's ingress/egress of the ashtama sign (using binary search).

3. Chandrabalam
   Moon transiting houses 1,3,6,7,10,11 from natal Moon rasi → good.
   All other houses → weak.
   house_from_natal = ((today_rasi - natal_rasi) % 12) + 1

All computations use pyswisseph with Lahiri ayanamsa.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import ephemeris as swe

# ── Constants ─────────────────────────────────────────────────────────────────

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Tara table: position 1–9
TARA_TABLE = {
    1: {"name": "Janma",       "nature": "neutral",  "colour": "yellow",
        "meaning": "Birth star — mixed results, health focus"},
    2: {"name": "Sampat",      "nature": "benefic",  "colour": "green",
        "meaning": "Wealth star — gains, prosperity"},
    3: {"name": "Vipat",       "nature": "malefic",  "colour": "red",
        "meaning": "Danger star — obstacles, accidents"},
    4: {"name": "Kshema",      "nature": "benefic",  "colour": "green",
        "meaning": "Comfort star — well-being, stability"},
    5: {"name": "Pratyari",    "nature": "malefic",  "colour": "red",
        "meaning": "Enemy star — conflicts, setbacks"},
    6: {"name": "Sadhana",     "nature": "benefic",  "colour": "green",
        "meaning": "Achievement star — success, fulfilment"},
    7: {"name": "Naidhana",    "nature": "malefic",  "colour": "red",
        "meaning": "Death star — loss, danger, avoid major moves"},
    8: {"name": "Mitra",       "nature": "benefic",  "colour": "green",
        "meaning": "Friend star — alliances, support"},
    9: {"name": "Param Mitra", "nature": "benefic",  "colour": "green",
        "meaning": "Best friend star — excellent outcomes"},
}

# Houses from natal Moon that give Chandrabalam
CHANDRABALAM_GOOD_HOUSES = {1, 3, 6, 7, 10, 11}


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _dt_to_jd(dt: datetime) -> float:
    """Convert a timezone-aware datetime to Julian Day (UT)."""
    utc = dt.utctimetuple()
    hour_frac = utc.tm_hour + utc.tm_min / 60.0 + utc.tm_sec / 3600.0
    return swe.julday(utc.tm_year, utc.tm_mon, utc.tm_mday, hour_frac)


def _moon_longitude(jd: float) -> float:
    """Return sidereal Moon longitude (0–360) at given JD."""
    lon, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return lon[0] % 360


def _nak_index(lon: float) -> int:
    """Nakshatra index 0–26 from sidereal longitude."""
    return int(lon / (360 / 27))


def _rasi_index(lon: float) -> int:
    """Rasi index 0–11 from sidereal longitude."""
    return int(lon / 30) % 12


def _nak_pada(lon: float) -> int:
    """Pada 1–4 within current nakshatra."""
    nak_span = 360 / 27          # 13.333...°
    pada_span = nak_span / 4     # 3.333...°
    deg_in_nak = lon % nak_span
    return int(deg_in_nak / pada_span) + 1


# ── Binary search for sign ingress/egress ────────────────────────────────────

def _binary_search_sign_change(
    target_rasi: int,
    jd_start: float,
    jd_end: float,
    entering: bool,
    precision_sec: float = 60,
) -> Optional[float]:
    """
    Binary-search the exact JD when Moon enters (entering=True)
    or exits (entering=False) target_rasi.
    Returns None if no such crossing exists in [jd_start, jd_end].
    """
    precision_jd = precision_sec / 86400.0

    lon_start = _moon_longitude(jd_start)
    lon_end   = _moon_longitude(jd_end)

    rasi_start = _rasi_index(lon_start)
    rasi_end   = _rasi_index(lon_end)

    if entering:
        # We want to find where rasi first becomes target_rasi
        if rasi_start == target_rasi:
            return jd_start          # already in target sign
        if rasi_end != target_rasi:
            return None              # never enters in window
    else:
        # We want to find where rasi stops being target_rasi
        if rasi_start != target_rasi:
            return None              # never in target sign at start
        if rasi_end == target_rasi:
            return jd_end            # still in sign at end

    lo, hi = jd_start, jd_end
    while (hi - lo) > precision_jd:
        mid = (lo + hi) / 2
        rasi_mid = _rasi_index(_moon_longitude(mid))
        if entering:
            if rasi_mid == target_rasi:
                hi = mid
            else:
                lo = mid
        else:
            if rasi_mid == target_rasi:
                lo = mid
            else:
                hi = mid

    return (lo + hi) / 2


def _jd_to_dt(jd: float, tz: ZoneInfo) -> datetime:
    """Convert Julian Day to timezone-aware datetime."""
    y, mo, d, h = swe.revjul(jd)
    hour = int(h)
    minute = int((h - hour) * 60)
    second = int(((h - hour) * 60 - minute) * 60)
    dt_utc = datetime(y, mo, d, hour, minute, second, tzinfo=ZoneInfo("UTC"))
    return dt_utc.astimezone(tz)


# ── Main API ──────────────────────────────────────────────────────────────────

def compute_tara_balam(
    natal_nak_index: int,   # 0–26, from natal Moon longitude
    today_nak_index: int,   # 0–26, from today's Moon longitude
) -> dict:
    """
    Compute Tara Balam.

    Returns:
        {position, name, nature, colour, meaning}
    """
    offset = (today_nak_index - natal_nak_index) % 27
    position = (offset % 9) + 1
    tara = TARA_TABLE[position]
    return {
        "position": position,
        "name":     tara["name"],
        "nature":   tara["nature"],
        "colour":   tara["colour"],
        "meaning":  tara["meaning"],
    }


def compute_chandrabalam(
    natal_rasi_index: int,   # 0–11
    today_rasi_index: int,   # 0–11
) -> dict:
    """
    Compute Chandrabalam — Moon's house from natal Moon rasi.

    Returns:
        {house_from_natal, good: bool}
    """
    house = ((today_rasi_index - natal_rasi_index) % 12) + 1
    return {
        "house_from_natal": house,
        "good": house in CHANDRABALAM_GOOD_HOUSES,
    }


def compute_chandra_ashtama(
    natal_rasi_index: int,
    dt: datetime,
    timezone: str = "Asia/Kolkata",
    search_days: int = 30,
) -> dict:
    """
    Compute Chandra Ashtama status for the given datetime.

    Ashtama rasi = (natal_rasi_index + 7) % 12 (8th sign from natal Moon).
    Searches up to search_days forward to find next ashtama start if not active.

    Returns:
        {
          is_active: bool,
          ashtama_rasi_index: int,
          ashtama_rasi_name: str,
          start: datetime | None,   — ingress time (if active, the entry time)
          end: datetime | None,     — egress time (when Moon leaves ashtama rasi)
          next_ashtama_date: date | None,  — if not active, when next starts
        }
    """
    tz = ZoneInfo(timezone)
    ashtama_rasi = (natal_rasi_index + 7) % 12

    jd_now  = _dt_to_jd(dt)
    lon_now = _moon_longitude(jd_now)
    current_rasi = _rasi_index(lon_now)
    is_active = (current_rasi == ashtama_rasi)

    start_dt: Optional[datetime] = None
    end_dt:   Optional[datetime] = None
    next_date = None

    if is_active:
        # Find when Moon entered this sign (search back up to 3 days)
        jd_back = jd_now - 3
        jd_entry = _binary_search_sign_change(ashtama_rasi, jd_back, jd_now, entering=True)
        if jd_entry:
            start_dt = _jd_to_dt(jd_entry, tz)

        # Find when Moon exits this sign (search forward up to 4 days)
        jd_fwd = jd_now + 4
        jd_exit = _binary_search_sign_change(ashtama_rasi, jd_now, jd_fwd, entering=False)
        if jd_exit:
            end_dt = _jd_to_dt(jd_exit, tz)
            # Now find the *next* occurrence after this one ends
            jd_after_exit = jd_exit + 0.5   # start searching half a day after exit
            jd_limit_next = jd_after_exit + search_days
            step_jd = 0.5
            jd_search = jd_after_exit
            while jd_search < jd_limit_next:
                rasi_here = _rasi_index(_moon_longitude(jd_search))
                if rasi_here == ashtama_rasi:
                    jd_next_entry = _binary_search_sign_change(
                        ashtama_rasi, jd_search - step_jd, jd_search, entering=True
                    )
                    if jd_next_entry:
                        next_date = _jd_to_dt(jd_next_entry, tz)
                    break
                jd_search += step_jd

    else:
        # Find the next ashtama window within search_days
        step_jd = 0.5   # search in 12-hour chunks
        jd_search = jd_now
        jd_limit  = jd_now + search_days

        while jd_search < jd_limit:
            rasi_here = _rasi_index(_moon_longitude(jd_search))
            if rasi_here == ashtama_rasi:
                # found entry — binary-search exact start
                jd_entry = _binary_search_sign_change(
                    ashtama_rasi, jd_search - step_jd, jd_search, entering=True
                )
                if jd_entry:
                    next_date = _jd_to_dt(jd_entry, tz)
                break
            jd_search += step_jd

    return {
        "is_active":           is_active,
        "ashtama_rasi_index":  ashtama_rasi,
        "ashtama_rasi_name":   SIGNS[ashtama_rasi],
        "start":               start_dt,    # current period start (if active)
        "end":                 end_dt,      # current period end (if active)
        "next_ashtama_start":  next_date,   # exact datetime of next occurrence
    }


def compute_all(
    natal_nak_index: int,
    natal_rasi_index: int,
    dt: datetime,
    timezone: str = "Asia/Kolkata",
) -> dict:
    """
    Compute Tara Balam + Chandrabalam + Chandra Ashtama in one call.

    Args:
        natal_nak_index:   0–26 (natal Moon nakshatra index)
        natal_rasi_index:  0–11 (natal Moon rasi index)
        dt:                timezone-aware datetime to evaluate (usually now)
        timezone:          IANA timezone string for output timestamps

    Returns combined dict with all three indicators.
    """
    jd = _dt_to_jd(dt)
    lon = _moon_longitude(jd)

    today_nak_index  = _nak_index(lon)
    today_rasi_index = _rasi_index(lon)
    today_pada       = _nak_pada(lon)

    tara        = compute_tara_balam(natal_nak_index, today_nak_index)
    chandrabalam = compute_chandrabalam(natal_rasi_index, today_rasi_index)
    ashtama     = compute_chandra_ashtama(natal_rasi_index, dt, timezone)

    return {
        # Today's Moon
        "today_moon_longitude":   lon,
        "today_moon_rasi_index":  today_rasi_index,
        "today_moon_rasi":        SIGNS[today_rasi_index],
        "today_moon_nak_index":   today_nak_index,
        "today_moon_nak":         NAKSHATRAS[today_nak_index],
        "today_moon_pada":        today_pada,

        # Natal reference
        "natal_nak_index":        natal_nak_index,
        "natal_nak_name":         NAKSHATRAS[natal_nak_index],
        "natal_rasi_index":       natal_rasi_index,
        "natal_rasi_name":        SIGNS[natal_rasi_index],

        # Tara Balam
        "tara": tara,

        # Chandrabalam
        "chandrabalam": chandrabalam,

        # Chandra Ashtama
        "chandra_ashtama": ashtama,
    }
