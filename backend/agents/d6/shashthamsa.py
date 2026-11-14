"""D6 (Shashthamsa) — Narasimha Rao / Jagannatha Hora.

Each sign is six 5° slices. Odd signs count from Aries, even signs from Libra —
the same as wrapping whole 5° steps from 0° Aries. Not a BPHS Shodashavarga;
not D60 Shashtyamsa.
"""

from __future__ import annotations

from agents.natal_agent import SIGN_LORDS, SIGNS, _house_number, _lon_to_nakshatra

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]


def d1_longitude_to_d6(longitude: float) -> float:
    """Sidereal D1 longitude → D6 longitude (Rao/JHora, whole-sign varga)."""
    longitude = float(longitude) % 360.0
    d6_rasi = int(longitude / 5.0) % 12
    d6_deg = (longitude % 5.0) * 6.0
    return d6_rasi * 30.0 + d6_deg


def build_shashthamsa_from_natal(natal_chart: dict) -> tuple[dict, dict]:
    """Shashthamsa ascendant + positions — same shape as D3/D10 for SouthIndianChart."""
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}

    bodies: dict[str, float] = {}
    for name in PLANETS:
        if name in pp and pp[name].get("longitude") is not None:
            bodies[name] = float(pp[name]["longitude"])
    if asc.get("longitude") is not None:
        bodies["Ascendant"] = float(asc["longitude"])
    elif asc.get("sign_index") is not None:
        deg = float(asc.get("degree_in_sign", 0))
        bodies["Ascendant"] = int(asc["sign_index"]) % 12 * 30.0 + deg

    d6_lons = {name: d1_longitude_to_d6(lon) for name, lon in bodies.items()}
    asc_d6_lon = d6_lons.get("Ascendant", 0.0)
    asc_d6_idx = int(asc_d6_lon // 30) % 12
    asc_d6_sign = SIGNS[asc_d6_idx]
    naks, naks_lord, pada = _lon_to_nakshatra(asc_d6_lon)

    shashthamsa_ascendant = {
        "sign": asc_d6_sign,
        "sign_index": asc_d6_idx,
        "sign_lord": SIGN_LORDS[asc_d6_sign],
        "longitude": round(asc_d6_lon, 4),
        "degree_in_sign": round(asc_d6_lon % 30, 4),
        "nakshatra": naks,
        "nakshatra_lord": naks_lord,
        "pada": pada,
    }

    shashthamsa_positions: dict[str, dict] = {}
    for pname in PLANETS:
        if pname not in pp or pname not in d6_lons:
            continue
        pdata = pp[pname]
        d6_lon = d6_lons[pname]
        sign_idx = int(d6_lon // 30) % 12
        sign = SIGNS[sign_idx]
        pnaks, pnaks_lord, ppada = _lon_to_nakshatra(d6_lon)
        shashthamsa_positions[pname] = {
            "sign": sign,
            "sign_index": sign_idx,
            "sign_lord": SIGN_LORDS[sign],
            "house": _house_number(sign_idx, asc_d6_idx),
            "longitude": round(d6_lon, 4),
            "degree_in_sign": round(d6_lon % 30, 4),
            "nakshatra": pnaks,
            "nakshatra_lord": pnaks_lord,
            "pada": ppada,
            "retrograde": bool(pdata.get("retrograde")),
        }

    return shashthamsa_ascendant, shashthamsa_positions
