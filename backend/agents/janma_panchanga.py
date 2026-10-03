"""
Janma panchanga from the natal longitudes already on the chart.

Tithi, nitya yoga, and karana use the birth Sun and Moon (Lahiri), not noon.
Vaara is the civil weekday of the birth date.
Karana lord, deity, and animal are a fixed Tamil practice table, not a
second calculation. The wallpaper line is a reminder, not a predicted result.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from agents.panchangam_agent import (
    TITHIS,
    YOGAS,
    VAARAM_LORDS,
    VAARAM_NAMES,
    _karanam_index_and_name,
)

# Tamil panchangam practice: karana nathan (planet), deity, and animal.
# Names match panchangam_agent (Garija = கரசை / Karajai).
KARANA_PRACTICE: dict[str, dict[str, str]] = {
    "Bava": {
        "name_ta": "பவம்",
        "kind": "movable",
        "lord": "Mars",
        "lord_ta": "செவ்வாய்",
        "deity": "Indra",
        "deity_ta": "இந்திரன்",
        "animal": "Lion",
        "animal_ta": "சிங்கம்",
    },
    "Balava": {
        "name_ta": "பாலவம்",
        "kind": "movable",
        "lord": "Rahu",
        "lord_ta": "ராகு",
        "deity": "Prajapati",
        "deity_ta": "பிரஜாபதி",
        "animal": "Tiger",
        "animal_ta": "புலி",
    },
    "Kaulava": {
        "name_ta": "கௌலவம்",
        "kind": "movable",
        "lord": "Saturn",
        "lord_ta": "சனி",
        "deity": "Mitra",
        "deity_ta": "மித்திரன்",
        "animal": "Boar",
        "animal_ta": "பன்றி",
    },
    "Taitila": {
        "name_ta": "தைதுலை",
        "kind": "movable",
        "lord": "Venus",
        "lord_ta": "சுக்கிரன்",
        "deity": "Pitris",
        "deity_ta": "பித்ருக்கள்",
        "animal": "Donkey",
        "animal_ta": "கழுதை",
    },
    "Garija": {
        "name_ta": "கரசை",
        "alias": "Karajai",
        "kind": "movable",
        "lord": "Moon",
        "lord_ta": "சந்திரன்",
        "deity": "Bhumadevi",
        "deity_ta": "பூமாதேவி",
        "animal": "Elephant",
        "animal_ta": "யானை",
    },
    "Vanija": {
        "name_ta": "வணிசை",
        "kind": "movable",
        "lord": "Sun",
        "lord_ta": "சூரியன்",
        "deity": "Sri",
        "deity_ta": "ஸ்ரீ தேவி",
        "animal": "Bull",
        "animal_ta": "காளை",
    },
    "Vishti": {
        "name_ta": "பத்திரை",
        "alias": "Bhadra",
        "kind": "movable",
        "lord": "Ketu",
        "lord_ta": "கேது",
        "deity": "Yama",
        "deity_ta": "யமன்",
        "animal": "Rooster",
        "animal_ta": "சேவல்",
    },
    "Shakuni": {
        "name_ta": "சகுனி",
        "kind": "fixed",
        "lord": "Saturn",
        "lord_ta": "சனி",
        "deity": "Vishnu",
        "deity_ta": "விஷ்ணு",
        "animal": "Crow",
        "animal_ta": "காகம்",
    },
    "Chatushpada": {
        "name_ta": "சதுஷ்பாதம்",
        "kind": "fixed",
        "lord": "Jupiter",
        "lord_ta": "குரு",
        "deity": "Manibhadra",
        "deity_ta": "மணிபத்ரன்",
        "animal": "Dog",
        "animal_ta": "நாய்",
    },
    "Naga": {
        "name_ta": "நாகவம்",
        "kind": "fixed",
        "lord": "Rahu",
        "lord_ta": "ராகு",
        "deity": "Naga",
        "deity_ta": "சர்ப்பம்",
        "animal": "Snake",
        "animal_ta": "பாம்பு",
    },
    "Kimstughna": {
        "name_ta": "கிம்ஸ்துக்னம்",
        "kind": "fixed",
        "lord": "Mercury",
        "lord_ta": "புதன்",
        "deity": "Vayu",
        "deity_ta": "வாயு",
        "animal": "Worm",
        "animal_ta": "புழு",
    },
}


def practice_line(animal: str, animal_ta: str) -> dict[str, str]:
    return {
        "en": (
            f"Keep a picture of the {animal.lower()} where you see it often, "
            "as a phone or desktop wallpaper. A simple practice for this karana, "
            "not a promise of results."
        ),
        "ta": f"{animal_ta} படத்தை திரை அல்லது கணினி பின்னணியில் வையுங்கள். இது ஒரு எளிய பழக்கம்.",
    }


def karana_record(name: str) -> dict[str, Any]:
    row = KARANA_PRACTICE[name]
    out = {
        "name": name,
        "name_ta": row["name_ta"],
        "alias": row.get("alias") or "",
        "kind": row["kind"],
        "lord": row["lord"],
        "lord_ta": row["lord_ta"],
        "deity": row["deity"],
        "deity_ta": row["deity_ta"],
        "animal": row["animal"],
        "animal_ta": row["animal_ta"],
        "practice": practice_line(row["animal"], row["animal_ta"]),
    }
    return out


def all_karanas() -> list[dict[str, Any]]:
    return [karana_record(name) for name in KARANA_PRACTICE]


def build_janma_panchanga(chart: dict) -> dict[str, Any]:
    """Essential birth panchanga from natal Sun/Moon longitudes and the birth date."""
    pp = chart.get("planet_positions") or {}
    sun = float((pp.get("Sun") or {}).get("longitude") or 0.0)
    moon_row = pp.get("Moon") or {}
    moon = float(moon_row.get("longitude") or 0.0)
    bd = chart.get("birth_data") or {}

    diff = (moon - sun) % 360.0
    tithi_idx = int(diff / 12.0) % 30
    karan_raw = int(diff / 6.0) % 60
    _, karan_name = _karanam_index_and_name(karan_raw)
    yoga_idx = int(((moon + sun) % 360.0) / (360.0 / 27.0)) % 27

    dob = bd.get("dob") or ""
    weekday = 0
    if dob:
        weekday = datetime.strptime(dob[:10], "%Y-%m-%d").weekday()

    karana = karana_record(karan_name)
    approximate = bool(bd.get("birth_time_approximate"))

    return {
        "vaara": {
            "name": VAARAM_NAMES[weekday],
            "lord": VAARAM_LORDS[weekday],
        },
        "tithi": {
            "name": TITHIS[tithi_idx],
            "paksha": "Shukla" if tithi_idx < 15 else "Krishna",
            "index": (tithi_idx % 15) + 1,
        },
        "nakshatra": {
            "name": moon_row.get("nakshatra") or "",
            "pada": moon_row.get("pada"),
            "lord": moon_row.get("nakshatra_lord") or "",
        },
        "yoga": {
            "name": YOGAS[yoga_idx],
        },
        "karana": karana,
        "karanas": all_karanas(),
        "time_is_noon": approximate,
        "note": (
            "Tithi, yoga, and karana are taken at 12:00 noon because the birth time "
            "was marked unknown. They can fall in the next half of the tithi."
            if approximate else
            "Tithi, yoga, and karana are taken at the birth time."
        ),
    }
