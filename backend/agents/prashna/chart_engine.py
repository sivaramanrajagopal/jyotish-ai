"""Cast Prashna chart at the exact moment of the question."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from agents.natal_agent import calculate_natal_chart
from agents.panchangam_agent import LOCATIONS
from agents.prashna.constants import SIGN_LORDS


def resolve_prashna_location(
    lat: float | None,
    lon: float | None,
    place: str | None,
) -> tuple[float, float, str]:
    """Return lat, lon, place_label for the Prashna moment."""
    if lat is not None and lon is not None:
        label = (place or "").strip() or f"{lat:.4f}, {lon:.4f}"
        return float(lat), float(lon), label

    text = (place or "").strip()
    for key, info in LOCATIONS.items():
        if text and (key.lower() in text.lower() or text.lower() in key.lower()):
            return info["lat"], info["lon"], key

    if text in LOCATIONS:
        info = LOCATIONS[text]
        return info["lat"], info["lon"], text

    default = LOCATIONS["Chennai"]
    return default["lat"], default["lon"], "Chennai (default)"


def cast_prashna_chart(
    timestamp_iso: str,
    timezone: str,
    lat: float,
    lon: float,
) -> dict:
    """
    Build a horary chart using Swiss Ephemeris at question time.
    Reuses natal_agent.calculate_natal_chart — same astronomy, Prashna lagna.
    """
    tz = ZoneInfo(timezone)
    dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.astimezone(tz)

    dob = dt.strftime("%Y-%m-%d")
    tob = dt.strftime("%H:%M")

    chart = calculate_natal_chart(dob, tob, lat, lon, timezone)
    chart["prashna_moment"] = {
        "iso": dt.isoformat(),
        "date": dob,
        "time": tob,
        "timezone": timezone,
        "lat": lat,
        "lon": lon,
    }
    return chart


def house_sign(chart: dict, house_num: int) -> str:
    """Whole-sign house sign (1-based house)."""
    asc_idx = chart["ascendant"]["sign_index"]
    return chart["house_signs"][house_num - 1]


def house_lord(chart: dict, house_num: int) -> str:
    return SIGN_LORDS[house_sign(chart, house_num)]


def lord_house(chart: dict, planet: str) -> int:
    return chart["planet_positions"][planet]["house"]


def planets_in_house(chart: dict, house_num: int) -> list[str]:
    return [
        name for name, data in chart["planet_positions"].items()
        if data["house"] == house_num
    ]
