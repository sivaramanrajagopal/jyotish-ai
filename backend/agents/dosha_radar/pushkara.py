"""Pushkara Navamsa — 24 classical zones (ported from natal_protection.py)."""

from __future__ import annotations

import datetime

import ephemeris as swe
from ephemeris import (
    FLG_SIDEREAL, FLG_SPEED, JUPITER, MARS, MERCURY,
    MOON, RAHU_NODE, SATURN, SUN, VENUS,
)

_FLAGS = FLG_SIDEREAL | FLG_SPEED

_PLANET_IDS = {
    "Sun": SUN, "Moon": MOON, "Mars": MARS, "Mercury": MERCURY,
    "Jupiter": JUPITER, "Venus": VENUS, "Saturn": SATURN,
}

SCAN_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

_PUSHKARA_ZONES = [
    {"start": 20.00, "end": 23.33, "sign": "Aries", "nakshatra": "Bharani", "pada": 3, "nak_lord": "Venus"},
    {"start": 26.67, "end": 30.00, "sign": "Aries", "nakshatra": "Krittika", "pada": 1, "nak_lord": "Sun"},
    {"start": 140.00, "end": 143.33, "sign": "Leo", "nakshatra": "Purva Phalguni", "pada": 3, "nak_lord": "Venus"},
    {"start": 146.67, "end": 150.00, "sign": "Leo", "nakshatra": "Uttara Phalguni", "pada": 1, "nak_lord": "Sun"},
    {"start": 260.00, "end": 263.33, "sign": "Sagittarius", "nakshatra": "Purva Ashadha", "pada": 3, "nak_lord": "Venus"},
    {"start": 266.67, "end": 270.00, "sign": "Sagittarius", "nakshatra": "Uttara Ashadha", "pada": 1, "nak_lord": "Sun"},
    {"start": 36.67, "end": 40.00, "sign": "Taurus", "nakshatra": "Krittika", "pada": 4, "nak_lord": "Sun"},
    {"start": 43.33, "end": 46.67, "sign": "Taurus", "nakshatra": "Rohini", "pada": 2, "nak_lord": "Moon"},
    {"start": 156.67, "end": 160.00, "sign": "Virgo", "nakshatra": "Uttara Phalguni", "pada": 4, "nak_lord": "Sun"},
    {"start": 163.33, "end": 166.67, "sign": "Virgo", "nakshatra": "Hasta", "pada": 2, "nak_lord": "Moon"},
    {"start": 276.67, "end": 280.00, "sign": "Capricorn", "nakshatra": "Uttara Ashadha", "pada": 4, "nak_lord": "Sun"},
    {"start": 283.33, "end": 286.67, "sign": "Capricorn", "nakshatra": "Shravana", "pada": 2, "nak_lord": "Moon"},
    {"start": 76.67, "end": 80.00, "sign": "Gemini", "nakshatra": "Ardra", "pada": 4, "nak_lord": "Rahu"},
    {"start": 83.33, "end": 86.67, "sign": "Gemini", "nakshatra": "Punarvasu", "pada": 2, "nak_lord": "Jupiter"},
    {"start": 196.67, "end": 200.00, "sign": "Libra", "nakshatra": "Swati", "pada": 4, "nak_lord": "Rahu"},
    {"start": 203.33, "end": 206.67, "sign": "Libra", "nakshatra": "Vishakha", "pada": 2, "nak_lord": "Jupiter"},
    {"start": 316.67, "end": 320.00, "sign": "Aquarius", "nakshatra": "Shatabhisha", "pada": 4, "nak_lord": "Rahu"},
    {"start": 323.33, "end": 326.67, "sign": "Aquarius", "nakshatra": "Purva Bhadrapada", "pada": 2, "nak_lord": "Jupiter"},
    {"start": 90.00, "end": 93.33, "sign": "Cancer", "nakshatra": "Punarvasu", "pada": 4, "nak_lord": "Jupiter"},
    {"start": 96.67, "end": 100.00, "sign": "Cancer", "nakshatra": "Pushya", "pada": 2, "nak_lord": "Saturn"},
    {"start": 210.00, "end": 213.33, "sign": "Scorpio", "nakshatra": "Vishakha", "pada": 4, "nak_lord": "Jupiter"},
    {"start": 216.67, "end": 220.00, "sign": "Scorpio", "nakshatra": "Anuradha", "pada": 2, "nak_lord": "Saturn"},
    {"start": 330.00, "end": 333.33, "sign": "Pisces", "nakshatra": "Purva Bhadrapada", "pada": 4, "nak_lord": "Jupiter"},
    {"start": 336.67, "end": 340.00, "sign": "Pisces", "nakshatra": "Uttara Bhadrapada", "pada": 2, "nak_lord": "Saturn"},
]


def check_pushkara(planet_lon: float) -> dict:
    lon = float(planet_lon) % 360.0
    for z in _PUSHKARA_ZONES:
        if z["start"] <= lon < z["end"]:
            zone = (
                f"{z['sign']} {z['start']:.2f}°–{z['end']:.2f}° "
                f"({z['nakshatra']} Pada {z['pada']})"
            )
            return {
                "pushkara": True,
                "zone": zone,
                "zone_en": zone,
                "zone_ta": zone,
                "sign": z["sign"],
                "nakshatra": z["nakshatra"],
                "pada": z["pada"],
                "nak_lord": z["nak_lord"],
            }
    return {
        "pushkara": False, "zone": "", "zone_en": "", "zone_ta": "",
        "sign": "", "nakshatra": "", "pada": 0, "nak_lord": "",
    }


def _lon_at(jd: float, planet_name: str) -> float:
    if planet_name == "Rahu":
        xx, _ = swe.calc_ut(jd, RAHU_NODE, _FLAGS)
        return xx[0] % 360
    if planet_name == "Ketu":
        xx, _ = swe.calc_ut(jd, RAHU_NODE, _FLAGS)
        return (xx[0] + 180.0) % 360
    pid = _PLANET_IDS.get(planet_name)
    if pid is None:
        return 0.0
    xx, _ = swe.calc_ut(jd, pid, _FLAGS)
    return xx[0] % 360


def scan_pushkara_transit(
    planet_name: str,
    reference_dt: datetime.datetime | None = None,
    days_ahead: int = 180,
) -> dict:
    if reference_dt is None:
        reference_dt = datetime.datetime.now(datetime.timezone.utc)
    ref_jd = swe.julday(
        reference_dt.year, reference_dt.month, reference_dt.day,
        reference_dt.hour + reference_dt.minute / 60.0,
    )

    def _pk_at(jd: float) -> dict:
        return check_pushkara(_lon_at(jd, planet_name))

    current = _pk_at(ref_jd)
    currently_in = current.get("pushkara", False)
    exits_in_days = None
    next_entry_days = next_entry_date = next_entry_zone = None

    if currently_in:
        for d in range(1, days_ahead + 1):
            if not _pk_at(ref_jd + d).get("pushkara"):
                exits_in_days = d
                break
        scan_from = (exits_in_days + 1) if exits_in_days is not None else days_ahead + 1
    else:
        scan_from = 1

    for d in range(scan_from, days_ahead + 1):
        p = _pk_at(ref_jd + d)
        if p.get("pushkara"):
            next_entry_days = d
            next_entry_date = (reference_dt + datetime.timedelta(days=d)).strftime("%Y-%m-%d")
            next_entry_zone = p.get("zone", "")
            break

    return {
        "planet": planet_name,
        "currently_pushkara": currently_in,
        "current_zone": current.get("zone", "") if currently_in else "",
        "exits_in_days": exits_in_days,
        "next_entry_days": next_entry_days,
        "next_entry_date": next_entry_date,
        "next_entry_zone": next_entry_zone,
    }


def scan_all_pushkara_transits(
    reference_dt: datetime.datetime | None = None,
    days_ahead: int = 180,
) -> list[dict]:
    return [
        scan_pushkara_transit(p, reference_dt=reference_dt, days_ahead=days_ahead)
        for p in SCAN_PLANETS
    ]
