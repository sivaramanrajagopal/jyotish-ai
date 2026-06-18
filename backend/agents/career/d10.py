"""D10 (Dasamsa) — Parasara method, aligned with Astro-birthchart-Database."""

from __future__ import annotations

from agents.natal_agent import SIGNS, SIGN_LORDS, _house_number, _lon_to_nakshatra

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]


def d1_longitude_to_d10(longitude: float) -> float:
    longitude = float(longitude) % 360.0
    rasi_index = int(longitude // 30) % 12
    degrees_in_rasi = longitude % 30.0
    part = min(int(degrees_in_rasi / 3.0), 9)
    if rasi_index % 2 == 0:
        d10_rasi_index = (rasi_index + part) % 12
    else:
        start = (rasi_index + 8) % 12
        d10_rasi_index = (start + part) % 12
    d10_degrees = (degrees_in_rasi % 3.0) * 10.0
    return d10_rasi_index * 30.0 + d10_degrees


def build_dasamsa_from_natal(natal_chart: dict) -> tuple[dict, dict]:
    """
    Build dasamsa_ascendant + dasamsa_positions in the same shape as D1/navamsa
    for SouthIndianChart and PlanetTable reuse.
    """
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}

    bodies: dict[str, float] = {}
    for name in PLANETS:
        if name in pp and pp[name].get("longitude") is not None:
            bodies[name] = float(pp[name]["longitude"])
    if asc.get("longitude") is not None:
        bodies["Ascendant"] = float(asc["longitude"])

    d10_lons: dict[str, float] = {
        name: d1_longitude_to_d10(lon) for name, lon in bodies.items()
    }

    asc_d10_lon = d10_lons.get("Ascendant", d1_longitude_to_d10(float(asc.get("longitude", 0))))
    asc_d10_idx = int(asc_d10_lon // 30) % 12
    asc_d10_sign = SIGNS[asc_d10_idx]
    asc_naks, asc_naks_lord, asc_pada = _lon_to_nakshatra(asc_d10_lon)

    dasamsa_ascendant = {
        "sign": asc_d10_sign,
        "sign_index": asc_d10_idx,
        "sign_lord": SIGN_LORDS[asc_d10_sign],
        "longitude": round(asc_d10_lon, 4),
        "degree_in_sign": round(asc_d10_lon % 30, 4),
        "nakshatra": asc_naks,
        "nakshatra_lord": asc_naks_lord,
        "pada": asc_pada,
    }

    dasamsa_positions: dict[str, dict] = {}
    for pname in PLANETS:
        if pname not in pp or pname not in d10_lons:
            continue
        pdata = pp[pname]
        d10_lon = d10_lons[pname]
        sign_idx = int(d10_lon // 30) % 12
        sign = SIGNS[sign_idx]
        naks, naks_lord, pada = _lon_to_nakshatra(d10_lon)
        dasamsa_positions[pname] = {
            "sign": sign,
            "sign_index": sign_idx,
            "sign_lord": SIGN_LORDS[sign],
            "house": _house_number(sign_idx, asc_d10_idx),
            "longitude": round(d10_lon, 4),
            "degree_in_sign": round(d10_lon % 30, 4),
            "nakshatra": naks,
            "nakshatra_lord": naks_lord,
            "pada": pada,
            "retrograde": bool(pdata.get("retrograde")),
        }

    return dasamsa_ascendant, dasamsa_positions
