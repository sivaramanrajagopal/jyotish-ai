"""
Resolve birth place / coordinates to a supported Panchangam city key.
"""

from __future__ import annotations

import math

from agents.panchangam_agent import LOCATIONS


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_panchangam_location(lat: float, lon: float) -> str:
    """Pick the closest supported LOCATIONS city by great-circle distance."""
    best_name = "Chennai"
    best_dist = float("inf")
    for name, info in LOCATIONS.items():
        d = _haversine_km(lat, lon, info["lat"], info["lon"])
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_name


def resolve_panchangam_location(
    place: str,
    lat: float | None = None,
    lon: float | None = None,
) -> str:
    """
    Match place string to LOCATIONS key, or use nearest city when lat/lon known.
    """
    if lat is not None and lon is not None:
        return nearest_panchangam_location(float(lat), float(lon))

    text = (place or "").strip()
    if text in LOCATIONS:
        return text

    lower = text.lower()
    for key in LOCATIONS:
        kl = key.lower()
        if kl in lower or lower in kl:
            return key

    return "Chennai"
