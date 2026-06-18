"""Combustion and Gandanta checks for Dosha Radar."""

from __future__ import annotations

COMBUSTION_ORB = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
}

_GANDANTA_JUNCTIONS = [(0.0, "Pisces/Aries"), (120.0, "Cancer/Leo"), (240.0, "Scorpio/Sagittarius")]
_GANDANTA_ORB = 10.0 / 3.0


def _angular_distance(a: float, b: float) -> float:
    diff = abs(float(a) - float(b)) % 360
    return diff if diff <= 180 else 360 - diff


def check_combustion(
    sun_deg: float, planet_deg: float, planet_name: str, is_retrograde: bool,
) -> dict:
    if planet_name == "Sun":
        return {"combust": False, "deep": False, "orb": 0.0, "cross_sign": False}

    orb_limit = COMBUSTION_ORB.get(planet_name, 14.0)
    if planet_name == "Mercury" and is_retrograde:
        orb_limit = 12.0

    dist = _angular_distance(sun_deg, planet_deg)
    sun_sign = int(sun_deg / 30) % 12
    planet_sign = int(planet_deg / 30) % 12
    cross_sign = sun_sign != planet_sign

    if cross_sign:
        return {
            "combust": False, "deep": False, "orb": round(dist, 2),
            "cross_sign": True, "would_combust": dist <= orb_limit,
        }

    return {
        "combust": dist <= orb_limit,
        "deep": dist <= 3.0,
        "orb": round(dist, 2),
        "cross_sign": False,
        "would_combust": False,
    }


def check_gandanta(planet_deg: float) -> dict:
    lon = float(planet_deg) % 360
    best_orb = 999.0
    best_jct = ""
    for jct_deg, jct_name in _GANDANTA_JUNCTIONS:
        dist = min(abs(lon - jct_deg), abs(lon - jct_deg + 360), abs(lon - jct_deg - 360))
        if dist < best_orb:
            best_orb = dist
            best_jct = jct_name
    return {
        "gandanta": best_orb <= _GANDANTA_ORB,
        "junction": best_jct,
        "orb": round(best_orb, 2),
    }


def check_critical_obstruction(
    planet_data: dict,
    soonya_rasis: list[int],
) -> dict:
    combust = planet_data.get("combust", {})
    gandanta = planet_data.get("gandanta", {})
    pushkara = planet_data.get("pushkara", {})

    has_deep = combust.get("deep", False)
    has_combust = combust.get("combust", False)
    has_gandanta = gandanta.get("gandanta", False)
    in_soonya = int(planet_data.get("sign_idx", -1)) in soonya_rasis
    has_pushkara = pushkara.get("pushkara", False)

    is_hard = has_deep or has_gandanta
    is_critical = is_hard and in_soonya
    is_mild = has_combust and (not has_deep) and in_soonya

    severity = "none"
    visha_gati_note = ""
    visha_gati_note_ta = ""
    has_divine = False

    if is_critical:
        if has_pushkara:
            severity = "critical_divine"
            has_divine = True
            visha_gati_note = (
                "Visha Gati (poisonous movement) — Pushkara Navamsa active. "
                "Initial struggle; divine grace may restore unexpectedly."
            )
            visha_gati_note_ta = (
                "விஷ கதி — புஷ்கர நவாம்சம் செயலில். "
                "ஆரம்ப சிரமம்; தெய்வ அருள் குணமடையல் கொடுக்கலாம்."
            )
        else:
            severity = "critical"
            visha_gati_note = "Visha Gati — no Pushkara protection. Proceed with caution."
            visha_gati_note_ta = "விஷ கதி — புஷ்கர பாதுகாப்பு இல்லை. கவனமாக செயல்படவும்."
    elif is_mild:
        if has_pushkara:
            severity = "mild_divine"
            has_divine = True
            visha_gati_note = "Mild obstruction partially relieved by Pushkara."
            visha_gati_note_ta = "மிதமான தடை — புஷ்கரம் பகுதியாக நிவர்த்தி."
        else:
            severity = "mild"
            visha_gati_note = "Mild obstruction in Soonya Rasi."
            visha_gati_note_ta = "சூன்ய ராசியில் மிதமான தடை."

    return {
        "critical": is_critical,
        "mild": is_mild,
        "severity": severity,
        "has_divine_protection": has_divine,
        "in_soonya": in_soonya,
        "visha_gati_note": visha_gati_note,
        "visha_gati_note_ta": visha_gati_note_ta,
    }
