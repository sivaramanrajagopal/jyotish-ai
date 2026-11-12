"""Drekkana body map: house from the D1 lagna + rising decan → Kalapurusha limb."""

from __future__ import annotations

# Drekkana section from degree in sign (0–30); 10° and 20° open the next decan.
def drekkana_section(degree_in_sign: float) -> str:
    d = float(degree_in_sign) % 30.0
    if d < 10.0:
        return "first"
    if d < 20.0:
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


# Kalapurusha limbs by house from the D1 lagna (Brihat Jataka 5.25):
#   1st decan: head, eyes, ears, nose, cheeks, jaws, mouth
#   2nd decan: neck, shoulders, arms, sides, heart, kroda (belly), navel
#   3rd decan: basti, genitals/anus, testicles, thighs, knees, calves, feet
# for houses 1, 2/12, 3/11, 4/10, 5/9, 6/8, 7. The decan rising at the lagna
# picks the column for every house. Houses 2–6 are the right side, 8–12 the left.
BODY_PARTS: dict[int, dict[str, dict[str, str]]] = {
    1: {
        "first": {"ta": "தலை", "en": "Head"},
        "second": {"ta": "கழுத்து", "en": "Neck"},
        "third": {"ta": "சிறுநீர்ப்பை / அடிவயிறு", "en": "Bladder / lower pelvis"},
    },
    2: {
        "first": {"ta": "வலது கண்", "en": "Right eye"},
        "second": {"ta": "வலது தோள்பட்டை", "en": "Right shoulder"},
        "third": {"ta": "வலது பிறப்புறுப்பு / ஆசனவாய்", "en": "Right genitals / anus"},
    },
    3: {
        "first": {"ta": "வலது காது", "en": "Right ear"},
        "second": {"ta": "வலது புஜம்", "en": "Right arm"},
        "third": {"ta": "வலது விரை", "en": "Right testicle"},
    },
    4: {
        "first": {"ta": "வலது நாசி", "en": "Right nostril"},
        "second": {"ta": "வலது விலாப்புறம்", "en": "Right flank"},
        "third": {"ta": "வலது தொடை", "en": "Right thigh"},
    },
    5: {
        "first": {"ta": "வலது கன்னம்", "en": "Right cheek"},
        "second": {"ta": "வலது இதயப் பகுதி", "en": "Right heart region"},
        "third": {"ta": "வலது முழங்கால்", "en": "Right knee"},
    },
    6: {
        "first": {"ta": "வலது தாடை", "en": "Right jaw"},
        "second": {"ta": "வலது பக்க வயிறு", "en": "Right belly"},
        "third": {"ta": "வலது கெண்டைக்கால்", "en": "Right calf"},
    },
    7: {
        "first": {"ta": "வாய்", "en": "Mouth"},
        "second": {"ta": "தொப்புள்", "en": "Navel"},
        "third": {"ta": "பாதம்", "en": "Feet"},
    },
    8: {
        "first": {"ta": "இடது தாடை", "en": "Left jaw"},
        "second": {"ta": "இடது பக்க வயிறு", "en": "Left belly"},
        "third": {"ta": "இடது கெண்டைக்கால்", "en": "Left calf"},
    },
    9: {
        "first": {"ta": "இடது கன்னம்", "en": "Left cheek"},
        "second": {"ta": "இடது இதயப் பகுதி", "en": "Left heart region"},
        "third": {"ta": "இடது முழங்கால்", "en": "Left knee"},
    },
    10: {
        "first": {"ta": "இடது நாசி", "en": "Left nostril"},
        "second": {"ta": "இடது விலாப்புறம்", "en": "Left flank"},
        "third": {"ta": "இடது தொடை", "en": "Left thigh"},
    },
    11: {
        "first": {"ta": "இடது காது", "en": "Left ear"},
        "second": {"ta": "இடது புஜம்", "en": "Left arm"},
        "third": {"ta": "இடது விரை", "en": "Left testicle"},
    },
    12: {
        "first": {"ta": "இடது கண்", "en": "Left eye"},
        "second": {"ta": "இடது தோள்பட்டை", "en": "Left shoulder"},
        "third": {"ta": "இடது பிறப்புறுப்பு / ஆசனவாய்", "en": "Left genitals / anus"},
    },
}

# Earlier Tamil / d3-calculator map: D3 house (1 = D3 lagna) + the planet's own 10° slice.
TAMIL_D3_BODY_PARTS: dict[int, dict[str, dict[str, str]]] = {
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
    "Mouth": "head",
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
    "Left heart region": "chest",
    "Right heart region": "chest",
    "Left ribs": "torso",
    "Right ribs": "torso",
    "Left flank": "torso",
    "Right flank": "torso",
    "Left shoulder": "arms",
    "Right shoulder": "arms",
    "Left hand": "arms",
    "Right hand": "arms",
    "Left arm": "arms",
    "Right arm": "arms",
    "Right abdomen": "abdomen",
    "Left abdomen": "abdomen",
    "Right belly": "abdomen",
    "Left belly": "abdomen",
    "Navel / abdomen centre": "abdomen",
    "Navel": "abdomen",
    "Left spleen": "abdomen",
    "Right spleen": "abdomen",
    "Bladder / lower pelvis": "pelvis",
    "Left genitals / anus": "pelvis",
    "Right genitals / anus": "pelvis",
    "Left testicle": "pelvis",
    "Right testicle": "pelvis",
    "Left thigh": "legs",
    "Right thigh": "legs",
    "Left knee": "legs",
    "Right knee": "legs",
    "Left calf": "legs",
    "Right calf": "legs",
    "Left ankle": "legs",
    "Right ankle": "legs",
    "Feet": "legs",
    "Left reproductive area": "pelvis",
    "Right reproductive area": "pelvis",
    "Upper reproductive area": "pelvis",
}


ZONE_EMOJI = {
    "head": "👤",
    "neck": "🦴",
    "chest": "🫀",
    "torso": "🫁",
    "arms": "💪",
    "abdomen": "🟠",
    "pelvis": "🟣",
    "legs": "🦵",
}


def _part_payload(table: dict, house: int, section: str) -> dict[str, str]:
    house = ((int(house) - 1) % 12) + 1
    part = table.get(house, {}).get(section, {"ta": "—", "en": "—"})
    zone = BODY_PART_ZONE.get(part["en"], "torso")
    return {
        "ta": part["ta"],
        "en": part["en"],
        "zone": zone,
        "section": section,
        "house_for_map": house,
        "emoji": ZONE_EMOJI.get(zone, ""),
    }


def body_part_for_house(house_from_lagna: int, lagna_degree_in_sign: float) -> dict[str, str]:
    """Body part from the D1 house (from lagna) in the section set by the rising decan."""
    return _part_payload(BODY_PARTS, house_from_lagna, drekkana_section(lagna_degree_in_sign))


def drekkana_section_tamil(degree_in_sign: float) -> str:
    """Previous Health tab boundaries: 10° and 20° stayed in the current decan."""
    d = float(degree_in_sign) % 30.0
    if d <= 10.0:
        return "first"
    if d <= 20.0:
        return "second"
    return "third"


def body_part_for_d3_house(d3_house: int, degree_in_sign: float) -> dict[str, str]:
    """Earlier map: D3 whole-sign house + the planet's own drekkana slice."""
    return _part_payload(TAMIL_D3_BODY_PARTS, d3_house, drekkana_section_tamil(degree_in_sign))


def maps_agree(classical: dict, tamil: dict) -> bool:
    """Same limb name or the same silhouette region."""
    if (classical.get("en") or "") == (tamil.get("en") or ""):
        return True
    return bool(classical.get("zone") and classical.get("zone") == tamil.get("zone"))
