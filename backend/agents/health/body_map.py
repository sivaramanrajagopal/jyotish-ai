"""D3 house → body part mapping (from d3-calculator / Tamil drekkana tradition)."""

from __future__ import annotations

# Drekkana section from degree in sign (0–30)
def drekkana_section(degree_in_sign: float) -> str:
    d = float(degree_in_sign) % 30.0
    if d <= 10.0:
        return "first"
    if d <= 20.0:
        return "second"
    return "third"


def drekkana_section_label(section: str, lang: str = "en") -> str:
    if lang == "ta":
        return {
            "first": "முதல் திரேக்கானம் (0–10°)",
            "second": "இரண்டாம் திரேக்கானம் (10–20°)",
            "third": "மூன்றாம் திரேக்கானம் (20–30°)",
        }.get(section, "")
    return {
        "first": "1st Drekkana (0–10°)",
        "second": "2nd Drekkana (10–20°)",
        "third": "3rd Drekkana (20–30°)",
    }.get(section, "")


# Kalapurusha: D3 house N → rasi N body parts (1=Aries … 12=Pisces)
BODY_PARTS: dict[int, dict[str, dict[str, str]]] = {
    1: {
        "first": {"ta": "தலை", "en": "Head"},
        "second": {"ta": "இடது மார்பு", "en": "Left chest"},
        "third": {"ta": "வலது முழங்கால்", "en": "Right knee"},
    },
    2: {
        "first": {"ta": "வலது கண்", "en": "Right eye"},
        "second": {"ta": "இடது விலா", "en": "Left ribs"},
        "third": {"ta": "வலது கண்ணுக்கால", "en": "Right ankle"},
    },
    3: {
        "first": {"ta": "வலது காது", "en": "Right ear"},
        "second": {"ta": "இடது கை", "en": "Left hand"},
        "third": {"ta": "பாதம்", "en": "Feet"},
    },
    4: {
        "first": {"ta": "வலது நாசி", "en": "Right nostril"},
        "second": {"ta": "இடது தோள்ப்பட்டை", "en": "Left shoulder"},
        "third": {"ta": "இடது கண்ணுக்கால", "en": "Left ankle"},
    },
    5: {
        "first": {"ta": "வலது கன்னம்", "en": "Right cheek"},
        "second": {"ta": "கழுத்து", "en": "Neck"},
        "third": {"ta": "இடது முழங்கால்", "en": "Left knee"},
    },
    6: {
        "first": {"ta": "வலது தாடை", "en": "Right jaw"},
        "second": {"ta": "வலது தோள்பட்டை", "en": "Right shoulder"},
        "third": {"ta": "இடது தொடை", "en": "Left thigh"},
    },
    7: {
        "first": {"ta": "முகம்", "en": "Face"},
        "second": {"ta": "வலது கை", "en": "Right hand"},
        "third": {"ta": "இடது விறைப்பை", "en": "Left spleen"},
    },
    8: {
        "first": {"ta": "இடது தாடை", "en": "Left jaw"},
        "second": {"ta": "வலது விலா", "en": "Right ribs"},
        "third": {"ta": "இடது பக்க இனப்பெருக்க உறுப்பு", "en": "Left reproductive area"},
    },
    9: {
        "first": {"ta": "இடது கன்னம்", "en": "Left cheek"},
        "second": {"ta": "வலது மார்பு", "en": "Right chest"},
        "third": {"ta": "இனப்பெருக்க உறுப்பு மேல் பகுதி", "en": "Upper reproductive area"},
    },
    10: {
        "first": {"ta": "இடது நாசி", "en": "Left nostril"},
        "second": {"ta": "வலது பக்க வயிறு", "en": "Right abdomen"},
        "third": {"ta": "வலது பக்க இனப்பெருக்க உறுப்பு", "en": "Right reproductive area"},
    },
    11: {
        "first": {"ta": "இடது காது", "en": "Left ear"},
        "second": {"ta": "தொப்புள்", "en": "Navel / abdomen centre"},
        "third": {"ta": "வலது விரைப்பை", "en": "Right spleen"},
    },
    12: {
        "first": {"ta": "இடது கண்", "en": "Left eye"},
        "second": {"ta": "இடது பக்க வயிறு", "en": "Left abdomen"},
        "third": {"ta": "வலது தொடை", "en": "Right thigh"},
    },
}

# SVG zone id for body silhouette highlighting
BODY_PART_ZONE: dict[str, str] = {
    "Head": "head",
    "Right eye": "head",
    "Left eye": "head",
    "Face": "head",
    "Right cheek": "head",
    "Left cheek": "head",
    "Right jaw": "head",
    "Left jaw": "head",
    "Right ear": "head",
    "Left ear": "head",
    "Right nostril": "head",
    "Left nostril": "head",
    "Neck": "neck",
    "Left chest": "chest",
    "Right chest": "chest",
    "Left ribs": "torso",
    "Right ribs": "torso",
    "Left shoulder": "arms",
    "Right shoulder": "arms",
    "Left hand": "arms",
    "Right hand": "arms",
    "Right abdomen": "abdomen",
    "Left abdomen": "abdomen",
    "Navel / abdomen centre": "abdomen",
    "Left spleen": "abdomen",
    "Right spleen": "abdomen",
    "Left thigh": "legs",
    "Right thigh": "legs",
    "Left knee": "legs",
    "Right knee": "legs",
    "Left ankle": "legs",
    "Right ankle": "legs",
    "Feet": "legs",
    "Left reproductive area": "pelvis",
    "Right reproductive area": "pelvis",
    "Upper reproductive area": "pelvis",
}


def body_part_for_d3_house(d3_house: int, degree_in_sign: float) -> dict[str, str]:
    """Map D3 whole-sign house + D1 degree drekkana slice → body part labels."""
    house = ((int(d3_house) - 1) % 12) + 1
    section = drekkana_section(degree_in_sign)
    part = BODY_PARTS.get(house, {}).get(section, {"ta": "—", "en": "—"})
    zone = BODY_PART_ZONE.get(part["en"], "torso")
    return {
        "ta": part["ta"],
        "en": part["en"],
        "zone": zone,
        "section": section,
        "d3_house_for_map": house,
    }
