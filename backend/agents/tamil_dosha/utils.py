"""Shared longitude / rasi / nakshatra helpers for Tamil dosha modules."""

from __future__ import annotations

import math

from .constants import NAKSHATRA_LORDS, NAKSHATRA_ORDER, RASI_ENGLISH, RASI_ORDER, SIGN_LORDS

_NAK_ARC = 360.0 / 27
_PADA_ARC = _NAK_ARC / 4


def rasi_index_from_longitude(lon_deg: float) -> int:
    return int(float(lon_deg) / 30) % 12


def nakshatra_index_from_longitude(lon_deg: float) -> int:
    return int((float(lon_deg) % 360) / _NAK_ARC) % 27


def nakshatra_pada_from_longitude(lon_deg: float) -> int:
    rem = float(lon_deg) % _NAK_ARC
    return min(int(rem / _PADA_ARC) + 1, 4)


def house_from_rasi(rasi_index: int, lagna_rasi_index: int) -> int:
    return (int(rasi_index) - int(lagna_rasi_index)) % 12 + 1


def rasi_of_nakshatra_pada(nakshatra_index: int, pada: int) -> int:
    lon = (int(nakshatra_index) * _NAK_ARC + (int(pada) - 1) * _PADA_ARC) % 360
    return rasi_index_from_longitude(lon)


def rasi_label(rasi_index: int) -> dict:
    idx = int(rasi_index) % 12
    return {
        "index": idx,
        "name": RASI_ORDER[idx],
        "english": RASI_ENGLISH[idx],
    }


def nakshatra_label(nak_index: int) -> dict:
    idx = int(nak_index) % 27
    return {
        "index": idx,
        "name": NAKSHATRA_ORDER[idx],
        "lord": NAKSHATRA_LORDS[idx],
    }


def tithi_index_from_longitudes(moon_lon: float, sun_lon: float) -> tuple[int, str, str]:
    """Return (tithi_index 0–14, name, paksha). 0 = Purnima/Amavasya."""
    angle_diff = (float(moon_lon) - float(sun_lon)) % 360
    tithi_number = int(math.ceil(angle_diff / 12.0))
    if tithi_number == 0:
        tithi_number = 30
    paksha = "Shukla" if tithi_number <= 15 else "Krishna"
    if tithi_number in (15, 30):
        return 0, "Purnima/Amavasya", paksha
    idx = ((tithi_number - 1) % 15) + 1
    from .constants import TITHI_NAMES
    return idx, TITHI_NAMES.get(idx, f"Tithi {idx}"), paksha


def graha_at_longitude(lon_deg: float) -> dict:
    lon = float(lon_deg) % 360
    nak_idx = nakshatra_index_from_longitude(lon)
    rasi_idx = rasi_index_from_longitude(lon)
    return {
        "longitude": round(lon, 4),
        "nakshatra_index": nak_idx,
        "nakshatra": NAKSHATRA_ORDER[nak_idx],
        "nakshatra_lord": NAKSHATRA_LORDS[nak_idx],
        "rasi_index": rasi_idx,
        "rasi": RASI_ORDER[rasi_idx],
        "rasi_lord": SIGN_LORDS[rasi_idx],
    }
