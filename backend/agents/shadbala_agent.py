"""Shadbala from a stored natal chart."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from agents.shadbala.calc import _jd, compute_shadbala


def compute_shadbala_for_chart(chart: dict) -> dict:
    birth_data = chart.get("birth_data") or {}
    dob = birth_data.get("dob")
    tob = birth_data.get("tob") or "12:00"
    lat = birth_data.get("lat")
    lon = birth_data.get("lon")
    timezone = birth_data.get("timezone") or "Asia/Kolkata"
    if not dob or lat is None or lon is None:
        raise ValueError("Birth date and place are required for Shadbala.")
    if len(str(tob)) == 5:
        tob = f"{tob}:00"
    birth = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(timezone))
    result = compute_shadbala(_jd(birth), float(lat), float(lon), birth)
    if birth_data.get("birth_time_approximate"):
        result["time_note"] = (
            "Birth time was taken as 12:00 noon, so Dig Bala, hora, and day/night strength follow noon."
        )
    return result
