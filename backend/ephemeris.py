"""
ephemeris.py — thread-safe Lahiri sidereal Swiss Ephemeris helpers.

pyswisseph sidereal mode is process-global; concurrent requests can race if
set_sid_mode() is only called at import time. Always use these wrappers so
Lahiri is set immediately before each calculation.
"""

from __future__ import annotations

import threading

import swisseph as swe

_lock = threading.RLock()

# Re-export common constants
FLG_SIDEREAL = swe.FLG_SIDEREAL
FLG_SPEED = swe.FLG_SPEED
SIDM_LAHIRI = swe.SIDM_LAHIRI
RAHU_NODE = swe.MEAN_NODE  # Vedic mean node; Ketu = Rahu + 180°

SUN = swe.SUN
MOON = swe.MOON
MARS = swe.MARS
MERCURY = swe.MERCURY
JUPITER = swe.JUPITER
VENUS = swe.VENUS
SATURN = swe.SATURN


def use_lahiri() -> None:
    """Set Lahiri ayanamsa (call before raw swe.* if not using wrappers)."""
    with _lock:
        swe.set_sid_mode(swe.SIDM_LAHIRI)


def get_ayanamsa_ut(jd: float) -> float:
    with _lock:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.get_ayanamsa_ut(jd)


def calc_ut(jd: float, body: int, flags: int = 0):
    with _lock:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.calc_ut(jd, body, flags)


def houses_ex(jd: float, lat: float, lon: float, hsys: bytes, flags: int = 0):
    with _lock:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.houses_ex(jd, lat, lon, hsys, flags)


def julday(year: int, month: int, day: float, hour: float = 0.0) -> float:
    return swe.julday(year, month, day, hour)


def revjul(jd: float, cal: int = swe.GREG_CAL):
    return swe.revjul(jd, cal)


def rise_trans(jd: float, body: int, rsmi: int, geopos, atpress: float = 0.0, attemp: float = 0.0):
    with _lock:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.rise_trans(jd, body, rsmi, geopos, atpress, attemp)


def set_topo(lon: float, lat: float, alt: float = 0.0) -> None:
    with _lock:
        swe.set_topo(lon, lat, alt)


def get_planet_name(pid: int) -> str:
    return swe.get_planet_name(pid)
