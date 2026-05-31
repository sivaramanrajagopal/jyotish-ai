"""
orchestrator.py
===============
Assembles the full astrological context for a forecast:
  1. Natal chart data (passed in from caller)
  2. Current Vimshottari Dasha
  3. Today's Panchangam
  4. Key interpretive metadata

Output is a structured dict passed directly to narrator.py.
"""

from __future__ import annotations

import datetime
from typing import Optional

from agents.dasha_agent import get_personal_dasha
from agents.panchangam_agent import calculate_panchangam, LOCATIONS
from agents.tara_engine import compute_all as compute_personal_panchangam


# ── Readable planet descriptions ─────────────────────────────────────────────

PLANET_NATURE = {
    "Sun":     "soul, authority, father, government",
    "Moon":    "mind, emotions, mother, public",
    "Mars":    "energy, courage, siblings, property",
    "Mercury": "intellect, communication, business",
    "Jupiter": "wisdom, expansion, children, dharma",
    "Venus":   "love, beauty, luxury, relationships",
    "Saturn":  "discipline, karma, delays, longevity",
    "Rahu":    "material ambition, foreign matters, illusion",
    "Ketu":    "spirituality, liberation, past life",
}

HOUSE_MEANINGS = {
    1:  "self, personality, body",
    2:  "wealth, family, speech",
    3:  "courage, siblings, communication",
    4:  "home, mother, happiness",
    5:  "children, intelligence, creativity",
    6:  "enemies, health, service",
    7:  "marriage, partnerships, public",
    8:  "transformation, longevity, hidden matters",
    9:  "luck, dharma, higher learning, father",
    10: "career, status, public life",
    11: "gains, social network, elder siblings",
    12: "expenses, foreign lands, liberation",
}

SIGN_ELEMENT = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

SIGN_QUALITY = {
    "Aries": "Movable", "Cancer": "Movable", "Libra": "Movable", "Capricorn": "Movable",
    "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Dual", "Virgo": "Dual", "Sagittarius": "Dual", "Pisces": "Dual",
}


def _describe_planet(name: str, pos: dict) -> str:
    """One-line planet summary for the prompt."""
    retro = " (retrograde)" if pos.get("retrograde") else ""
    vargo = " [Vargottama]" if pos.get("vargottama") else ""
    return (
        f"{name} in {pos['sign']} (House {pos['house']}, "
        f"{pos['nakshatra']} pada {pos['pada']}, "
        f"{pos['degree_in_sign']:.1f}°){retro}{vargo}"
    )


def assemble_context(
    natal_chart: dict,
    location: str = "Chennai",
    target_date: Optional[str] = None,
) -> dict:
    """
    Build the full forecast context.

    Args:
        natal_chart:  Full response from /natal-chart endpoint.
        location:     Location name for Panchangam lookup (must be in LOCATIONS).
        target_date:  YYYY-MM-DD (defaults to today).

    Returns:
        Rich context dict ready for narrator.py.
    """
    if target_date is None:
        target_date = datetime.date.today().isoformat()

    # ── 1. Natal chart basics ────────────────────────────────────────────────
    planets  = natal_chart.get("planet_positions", {})
    asc      = natal_chart.get("ascendant", {})
    yogas    = natal_chart.get("yogas", [])
    birth    = natal_chart.get("birth_data", {})
    navamsa  = natal_chart.get("navamsa_positions", {})

    ascendant_sign = asc.get("sign", "")
    moon_sign      = planets.get("Moon", {}).get("sign", "")
    sun_sign       = planets.get("Sun", {}).get("sign", "")
    moon_lon       = planets.get("Moon", {}).get("longitude", 0.0)

    # Planet lines
    planet_lines = [
        _describe_planet(name, data)
        for name, data in planets.items()
        if isinstance(data, dict)
    ]

    # Yoga names
    yoga_names = [y["name"] for y in yogas if isinstance(y, dict)]

    # Key house lords (for career/relationship analysis)
    house_lords: dict[int, str] = {}
    for name, data in planets.items():
        if isinstance(data, dict) and "house" in data:
            h = data["house"]
            if isinstance(h, int):
                house_lords[h] = name

    # ── 2. Vimshottari Dasha ────────────────────────────────────────────────
    dob = birth.get("dob", "")
    dasha = {}
    if dob and moon_lon:
        try:
            dasha = get_personal_dasha(moon_lon, dob)
        except Exception as e:
            print(f"[orchestrator] dasha error: {e}")

    # ── 3. Panchangam ────────────────────────────────────────────────────────
    panchangam = {}
    if location in LOCATIONS:
        try:
            panchangam = calculate_panchangam(target_date, location)
        except Exception as e:
            print(f"[orchestrator] panchangam error: {e}")
    else:
        # Try first available location
        try:
            first_loc = next(iter(LOCATIONS))
            panchangam = calculate_panchangam(target_date, first_loc)
            location = first_loc
        except Exception as e:
            print(f"[orchestrator] panchangam fallback error: {e}")

    # ── 4. Personal Panchangam (Tara Balam + Chandra Ashtama) ───────────────
    personal_panch: dict = {}
    nak_idx  = natal_chart.get("moon_nakshatra_index")
    rasi_idx = natal_chart.get("moon_rasi_index")
    if nak_idx is not None and rasi_idx is not None:
        try:
            import datetime as _dt
            from zoneinfo import ZoneInfo
            td    = _dt.date.fromisoformat(target_date)
            tz_id = natal_chart.get("birth_data", {}).get("timezone", "Asia/Kolkata")
            dt    = _dt.datetime(td.year, td.month, td.day, 12, 0, 0,
                                 tzinfo=ZoneInfo(tz_id))
            raw = compute_personal_panchangam(int(nak_idx), int(rasi_idx), dt, tz_id)
            tara   = raw.get("tara", {})
            ashtama = raw.get("chandra_ashtama", {})
            cb     = raw.get("chandrabalam", {})

            def _fmt_dt(v):
                if v is None:
                    return None
                if hasattr(v, "strftime"):
                    return v.strftime("%-d %b %Y %H:%M %Z")
                return str(v)

            personal_panch = {
                "natal_nak_name":       raw.get("natal_nak_name", ""),
                "today_moon_nak":       raw.get("today_moon_nak", ""),
                "today_moon_rasi":      raw.get("today_moon_rasi", ""),
                "tara_name":            tara.get("name", ""),
                "tara_nature":          tara.get("nature", ""),
                "tara_meaning":         tara.get("meaning", ""),
                "tara_position":        tara.get("position", ""),
                "ashtama_active":       ashtama.get("is_active", False),
                "ashtama_rasi":         ashtama.get("ashtama_rasi_name", ""),
                "ashtama_end":          _fmt_dt(ashtama.get("end")),
                "next_ashtama_start":   _fmt_dt(ashtama.get("next_ashtama_start")),
                "chandrabalam_good":    cb.get("good", False),
                "chandrabalam_house":   cb.get("house_from_natal", ""),
            }
        except Exception as e:
            print(f"[orchestrator] personal panchangam error: {e}")

    # ── 5. Assemble ──────────────────────────────────────────────────────────
    return {
        "date":          target_date,
        "location":      location,

        # Natal identity
        "native": {
            "name":           birth.get("name", "the native"),
            "dob":            dob,
            "ascendant_sign": ascendant_sign,
            "moon_sign":      moon_sign,
            "sun_sign":       sun_sign,
            "ascendant_nakshatra": asc.get("nakshatra", ""),
            "moon_nakshatra":      planets.get("Moon", {}).get("nakshatra", ""),
            "ascendant_element":   SIGN_ELEMENT.get(ascendant_sign, ""),
            "ascendant_quality":   SIGN_QUALITY.get(ascendant_sign, ""),
        },

        # Planet snapshot
        "planets":  planet_lines,
        "yogas":    yoga_names,

        # Navamsa highlights
        "navamsa_ascendant": natal_chart.get("navamsa_ascendant", {}).get("sign", ""),

        # Dasha
        "dasha": {
            "mahadasha":       dasha.get("mahadasha", {}),
            "bhukti":          dasha.get("bhukti", {}),
            "relationship":    dasha.get("relationship", ""),
            "upcoming_bhuktis": dasha.get("upcoming_bhuktis", []),
        },

        # Personal Panchangam (Tara Balam + Ashtama)
        "personal_panchangam": personal_panch,

        # Today's Panchangam
        "panchangam": {
            "vaaram":    panchangam.get("vaaram_name", ""),
            "vaaram_lord": panchangam.get("vaaram_lord", ""),
            "tithi":     panchangam.get("tithi_name", ""),
            "tithi_paksha": panchangam.get("tithi_paksha", ""),
            "nakshatra": panchangam.get("nakshatra_name", ""),
            "nakshatra_lord": panchangam.get("nakshatra_lord", ""),
            "yogam":     panchangam.get("yogam_name", ""),
            "karanam":   panchangam.get("karanam_name", ""),
            "rahu_kalam_start": panchangam.get("rahu_kalam_start", ""),
            "rahu_kalam_end":   panchangam.get("rahu_kalam_end", ""),
        },
    }
