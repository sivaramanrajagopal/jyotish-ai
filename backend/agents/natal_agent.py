"""
natal_agent.py
==============
Vedic birth chart (Janma Kundali) engine using pyswisseph + Lahiri ayanamsa.

Computes for any birth date/time/location:
  - Ascendant (Lagna) — sign, degree, nakshatra
  - 9 planets: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
    Each planet: longitude, sign, sign_lord, house, nakshatra, pada,
                 degree_in_sign, retrograde
  - House cusps (Whole Sign system — standard in Vedic)
  - Basic yoga detection: Gaja Kesari, Budha-Aditya, Chandra-Mangala,
    Neecha Bhanga, Vargottama

Usage:
    from agents.natal_agent import calculate_natal_chart
    chart = calculate_natal_chart("1990-06-15", "14:30", 13.0827, 80.2707, "Asia/Kolkata")
"""

from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

import ephemeris as swe
from ephemeris import RAHU_NODE

# ─────────────────────────────────────────────
# Lookup tables
# ─────────────────────────────────────────────

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    "Aries": "Mars",      "Taurus": "Venus",    "Gemini": "Mercury",
    "Cancer": "Moon",     "Leo": "Sun",          "Virgo": "Mercury",
    "Libra": "Venus",     "Scorpio": "Mars",     "Sagittarius": "Jupiter",
    "Capricorn": "Saturn","Aquarius": "Saturn",  "Pisces": "Jupiter",
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
]

# Swiss Ephemeris planet IDs
PLANETS = {
    "Sun":     swe.SUN,
    "Moon":    swe.MOON,
    "Mars":    swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus":   swe.VENUS,
    "Saturn":  swe.SATURN,
    "Rahu":    RAHU_NODE,
}

# Exaltation degrees (sidereal, for neecha bhanga detection)
EXALTATION = {
    "Sun": (0, 10),      # Aries 10°
    "Moon": (1, 3),      # Taurus 3°
    "Mars": (9, 28),     # Capricorn 28°
    "Mercury": (5, 15),  # Virgo 15°
    "Jupiter": (3, 5),   # Cancer 5°
    "Venus": (11, 27),   # Pisces 27°
    "Saturn": (6, 20),   # Libra 20°
}

DEBILITATION = {
    "Sun": (6, 10),      # Libra 10°
    "Moon": (7, 3),      # Scorpio 3°
    "Mars": (3, 28),     # Cancer 28°
    "Mercury": (11, 15), # Pisces 15°
    "Jupiter": (9, 5),   # Capricorn 5°
    "Venus": (5, 27),    # Virgo 27°
    "Saturn": (0, 20),   # Aries 20°
}

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _to_jd(dt: datetime) -> float:
    utc = dt.astimezone(ZoneInfo("UTC"))
    hour_ut = utc.hour + utc.minute / 60 + utc.second / 3600
    return swe.julday(utc.year, utc.month, utc.day, hour_ut)  # noqa: ephemeris wrapper


def _lon_to_sign(lon: float) -> tuple[str, float]:
    """Return (sign_name, degree_within_sign) for a sidereal longitude."""
    sign_idx = int(lon / 30) % 12
    degree_in_sign = lon % 30
    return SIGNS[sign_idx], degree_in_sign


def _lon_to_nakshatra(lon: float) -> tuple[str, str, int]:
    """Return (nakshatra_name, nakshatra_lord, pada) for a sidereal longitude."""
    arc = 360 / 27
    naks_idx = int(lon / arc) % 27
    pada = int(((lon % arc) / (arc / 4))) + 1
    return NAKSHATRAS[naks_idx], NAKSHATRA_LORDS[naks_idx], pada


def _navamsa_sign_idx(lon: float) -> int:
    """
    Compute D9 Navamsa sign index (0-11) for a sidereal longitude.
    Each rasi (30°) is split into 9 amsas of 3°20' each.
    Starting sign by element:
      Fire (Aries/Leo/Sgr)   → Aries (0)
      Earth (Tau/Vir/Cap)    → Capricorn (9)
      Air (Gem/Lib/Aqr)      → Libra (6)
      Water (Can/Sco/Pis)    → Cancer (3)
    """
    sign_i      = int(lon / 30) % 12
    deg_in_sign = lon % 30
    amsa_idx    = int(deg_in_sign / (30 / 9))          # 0–8
    element     = sign_i % 3                            # 0=fire,1=earth,2=air; water=3 offset
    # Correct element mapping: 0→Aries(0), 1→Capricorn(9), 2→Libra(6), water→Cancer(3)
    # Signs: 0=Ari,1=Tau,2=Gem,3=Can,4=Leo,5=Vir,6=Lib,7=Sco,8=Sgr,9=Cap,10=Aqr,11=Pis
    # Fire: Ari(0),Leo(4),Sgr(8)  → sign_i%4==0
    # Earth:Tau(1),Vir(5),Cap(9)  → sign_i%4==1
    # Air:  Gem(2),Lib(6),Aqr(10) → sign_i%4==2
    # Water:Can(3),Sco(7),Pis(11) → sign_i%4==3
    starts = [0, 9, 6, 3]
    start  = starts[sign_i % 4]
    return (start + amsa_idx) % 12


def _house_number(planet_sign_idx: int, asc_sign_idx: int) -> int:
    """Whole Sign house number (1-based) given planet sign and ascendant sign."""
    return ((planet_sign_idx - asc_sign_idx) % 12) + 1


def _is_retrograde(planet_id: int, jd: float) -> bool:
    """True if planet's speed is negative (retrograde)."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    xx, _ = swe.calc_ut(jd, planet_id, flags)  # Lahiri enforced in ephemeris
    return xx[3] < 0   # xx[3] = speed in longitude


# ─────────────────────────────────────────────
# Yoga detection
# ─────────────────────────────────────────────

def _detect_yogas(positions: dict, asc_sign_idx: int) -> list[dict]:
    """Detect classical Vedic yogas from planet positions."""
    yogas = []

    def house(planet: str) -> int:
        return positions[planet]["house"]

    def sign_idx(planet: str) -> int:
        return SIGNS.index(positions[planet]["sign"])

    # ── Gaja Kesari Yoga ─────────────────────────────────────
    # Jupiter in kendra (1,4,7,10) from Moon
    moon_house = house("Moon")
    jup_house  = house("Jupiter")
    relative   = ((jup_house - moon_house) % 12) + 1
    if relative in [1, 4, 7, 10]:
        yogas.append({
            "name": "Gaja Kesari Yoga",
            "description": "Jupiter in kendra from Moon — bestows wisdom, fame, and prosperity.",
            "planets": ["Jupiter", "Moon"],
        })

    # ── Budha-Aditya Yoga ────────────────────────────────────
    # Sun and Mercury in same sign
    if positions["Sun"]["sign"] == positions["Mercury"]["sign"]:
        yogas.append({
            "name": "Budha-Aditya Yoga",
            "description": "Sun conjunct Mercury — sharp intellect, eloquence, and recognition.",
            "planets": ["Sun", "Mercury"],
        })

    # ── Chandra-Mangala Yoga ─────────────────────────────────
    # Moon and Mars in same sign or mutual aspect (7th from each other)
    moon_si = sign_idx("Moon")
    mars_si  = sign_idx("Mars")
    if moon_si == mars_si or abs(moon_si - mars_si) == 6:
        yogas.append({
            "name": "Chandra-Mangala Yoga",
            "description": "Moon and Mars conjunct or opposed — strong will, entrepreneurial spirit.",
            "planets": ["Moon", "Mars"],
        })

    # ── Vargottama check (planet in same sign in Rasi and Navamsa) ──
    # Uses _navamsa_sign_idx() — Fire/Earth/Air/Water starts [0,9,6,3]
    for planet_name, data in positions.items():
        rasi_sign_i   = int(data["longitude"] / 30) % 12
        navamsa_sign_i = _navamsa_sign_idx(data["longitude"])
        if navamsa_sign_i == rasi_sign_i:
            yogas.append({
                "name": f"Vargottama {planet_name}",
                "description": f"{planet_name} is vargottama (same sign in Rasi and Navamsa) — greatly strengthened.",
                "planets": [planet_name],
            })

    # ── Neecha Bhanga Raja Yoga ──────────────────────────────
    # Debilitated planet's dispositor is in kendra from ascendant or Moon
    for planet_name, (deb_sign_i, _) in DEBILITATION.items():
        if planet_name not in positions:
            continue
        if sign_idx(planet_name) == deb_sign_i:
            dispositor = SIGN_LORDS[SIGNS[deb_sign_i]]
            if dispositor in positions:
                disp_house = house(dispositor)
                if disp_house in [1, 4, 7, 10]:
                    yogas.append({
                        "name": f"Neecha Bhanga Raja Yoga ({planet_name})",
                        "description": (
                            f"Debilitated {planet_name} cancelled by {dispositor} in kendra — "
                            f"difficulty transforms into strength and elevation."
                        ),
                        "planets": [planet_name, dispositor],
                    })

    return yogas


# ─────────────────────────────────────────────
# Main calculation
# ─────────────────────────────────────────────

def calculate_natal_chart(
    dob: str,
    tob: str,
    lat: float,
    lon: float,
    timezone: str,
) -> dict:
    """
    Calculate a complete Vedic natal chart.

    Args:
        dob:      Date of birth 'YYYY-MM-DD'
        tob:      Time of birth 'HH:MM' (24h, local time)
        lat:      Birth latitude
        lon:      Birth longitude
        timezone: Birth timezone (e.g. 'Asia/Kolkata')

    Returns:
        Dict with ascendant, planet_positions, yogas, ayanamsa details.
    """
    tz = ZoneInfo(timezone)

    # Parse birth datetime
    dt_str = f"{dob} {tob}:00"
    birth_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
    jd = _to_jd(birth_dt)

    # Ayanamsa value (Lahiri — set inside ephemeris wrapper)
    ayanamsa_val = swe.get_ayanamsa_ut(jd)

    # ── Ascendant ────────────────────────────────────────────
    flags  = swe.FLG_SIDEREAL
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b"W", flags)
    # ascmc[0] = Ascendant longitude (already sidereal with FLG_SIDEREAL)
    asc_lon = ascmc[0] % 360
    asc_sign, asc_deg = _lon_to_sign(asc_lon)
    asc_sign_idx = SIGNS.index(asc_sign)
    asc_naks, asc_naks_lord, asc_pada = _lon_to_nakshatra(asc_lon)

    # ── Planets ──────────────────────────────────────────────
    planet_positions: dict[str, dict] = {}

    for name, planet_id in PLANETS.items():
        xx, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        p_lon = xx[0] % 360
        retro = xx[3] < 0

        sign, deg_in_sign = _lon_to_sign(p_lon)
        sign_idx_val = SIGNS.index(sign)
        naks, naks_lord, pada = _lon_to_nakshatra(p_lon)
        house_num = _house_number(sign_idx_val, asc_sign_idx)

        planet_positions[name] = {
            "longitude":      round(p_lon, 4),
            "sign":           sign,
            "sign_index":     sign_idx_val,
            "sign_lord":      SIGN_LORDS[sign],
            "house":          house_num,
            "nakshatra":      naks,
            "nakshatra_lord": naks_lord,
            "pada":           pada,
            "degree_in_sign": round(deg_in_sign, 4),
            "retrograde":     retro,
        }

    # ── Ketu (always 180° from Rahu) ─────────────────────────
    rahu_lon  = planet_positions["Rahu"]["longitude"]
    ketu_lon  = (rahu_lon + 180) % 360
    k_sign, k_deg = _lon_to_sign(ketu_lon)
    k_sign_idx = SIGNS.index(k_sign)
    k_naks, k_naks_lord, k_pada = _lon_to_nakshatra(ketu_lon)

    planet_positions["Ketu"] = {
        "longitude":      round(ketu_lon, 4),
        "sign":           k_sign,
        "sign_index":     k_sign_idx,
        "sign_lord":      SIGN_LORDS[k_sign],
        "house":          _house_number(k_sign_idx, asc_sign_idx),
        "nakshatra":      k_naks,
        "nakshatra_lord": k_naks_lord,
        "pada":           k_pada,
        "degree_in_sign": round(ketu_lon % 30, 4),
        "retrograde":     True,   # Ketu always retrograde by convention
    }

    # ── Yogas ────────────────────────────────────────────────
    yogas = _detect_yogas(planet_positions, asc_sign_idx)

    # ── House cusps (Whole Sign) ──────────────────────────────
    house_signs = [SIGNS[(asc_sign_idx + i) % 12] for i in range(12)]

    # ── D9 Navamsa positions ──────────────────────────────────
    asc_nav_idx  = _navamsa_sign_idx(asc_lon)
    navamsa_positions: dict[str, dict] = {}
    for pname, pdata in planet_positions.items():
        nav_idx  = _navamsa_sign_idx(pdata["longitude"])
        nav_sign = SIGNS[nav_idx]
        nav_house = _house_number(nav_idx, asc_nav_idx)
        navamsa_positions[pname] = {
            "sign":       nav_sign,
            "sign_index": nav_idx,
            "sign_lord":  SIGN_LORDS[nav_sign],
            "house":      nav_house,
            "vargottama": nav_idx == SIGNS.index(pdata["sign"]),
        }

    asc_nav_sign = SIGNS[asc_nav_idx]

    # ── Moon indices for Tara / Ashtama engines ───────────────
    moon_lon          = planet_positions["Moon"]["longitude"]
    moon_nak_index    = int(moon_lon / (360 / 27))   # 0–26
    moon_rasi_index   = int(moon_lon / 30) % 12       # 0–11

    return {
        "ascendant": {
            "longitude":      round(asc_lon, 4),
            "sign":           asc_sign,
            "sign_index":     asc_sign_idx,
            "sign_lord":      SIGN_LORDS[asc_sign],
            "degree_in_sign": round(asc_deg, 4),
            "nakshatra":      asc_naks,
            "nakshatra_lord": asc_naks_lord,
            "pada":           asc_pada,
        },
        "navamsa_ascendant": {
            "sign":       asc_nav_sign,
            "sign_index": asc_nav_idx,
            "sign_lord":  SIGN_LORDS[asc_nav_sign],
        },
        "planet_positions": planet_positions,
        "navamsa_positions": navamsa_positions,
        "house_signs":      house_signs,
        "yogas":              yogas,
        "moon_nakshatra_index": moon_nak_index,
        "moon_rasi_index":      moon_rasi_index,
        "ayanamsa":           "Lahiri",
        "ayanamsa_value":     round(ayanamsa_val, 6),
        "birth_data": {
            "dob": dob,
            "tob": tob,
            "lat": lat,
            "lon": lon,
            "timezone": timezone,
        },
    }


# ─────────────────────────────────────────────
# Formatted output for quick inspection
# ─────────────────────────────────────────────

def format_chart_output(chart: dict) -> str:
    asc = chart["ascendant"]
    lines = [
        f"╔══════════════════════════════════════════════╗",
        f"  Janma Kundali  {chart['birth_data']['dob']}  {chart['birth_data']['tob']}",
        f"  Ayanamsa: {chart['ayanamsa']} {chart['ayanamsa_value']:.4f}°",
        f"╚══════════════════════════════════════════════╝",
        f"",
        f"⬆  Ascendant : {asc['sign']} {asc['degree_in_sign']:.2f}°  "
        f"({asc['nakshatra']} pada {asc['pada']})",
        f"",
        f"{'Planet':<10} {'Sign':<14} {'Deg':>6}  {'House':>5}  {'Nakshatra':<20} {'Pada':>4}  {'R':>2}",
        "─" * 72,
    ]
    order = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    for p in order:
        d = chart["planet_positions"][p]
        r = "R" if d["retrograde"] else " "
        lines.append(
            f"{p:<10} {d['sign']:<14} {d['degree_in_sign']:>6.2f}  "
            f"{d['house']:>5}  {d['nakshatra']:<20} {d['pada']:>4}  {r:>2}"
        )
    lines.append("")
    if chart["yogas"]:
        lines.append("✦ Yogas detected:")
        for y in chart["yogas"]:
            lines.append(f"  • {y['name']}: {y['description']}")
    else:
        lines.append("  No major yogas detected.")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Standalone test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Test: Chennai, 1990-06-15 14:30
    chart = calculate_natal_chart(
        dob="1990-06-15",
        tob="14:30",
        lat=13.0827,
        lon=80.2707,
        timezone="Asia/Kolkata",
    )
    print(format_chart_output(chart))
