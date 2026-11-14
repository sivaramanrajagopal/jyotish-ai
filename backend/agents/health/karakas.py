"""Planet illness karakas + Kalapurusha limbs — awareness only, not diagnosis."""

from __future__ import annotations

from agents.natal_agent import SIGNS

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]

# Parashara / Saravali-style body significations. Zones match Health BodyMapSvg.
PLANET_ROGA: dict[str, dict] = {
    "Sun": {
        "en": "Heart, vitality, bones, right eye, pitta stomach, head",
        "ta": "இதயம், உயிர்சக்தி, எலும்பு, வலது கண், பித்த வயிறு, தலை",
        "zones": ["chest", "head"],
    },
    "Moon": {
        "en": "Mind, blood, lungs, left eye, breasts, fluids, sleep",
        "ta": "மனம், இரத்தம், நுரையீரல், இடது கண், மார்பகம், நீர், உறக்கம்",
        "zones": ["chest", "head"],
    },
    "Mars": {
        "en": "Blood, muscles, marrow, inflammation, accidents, surgery",
        "ta": "இரத்தம், தசை, எலும்பு மஜ்ஜை, அழற்சி, விபத்து, அறுவை",
        "zones": ["head", "arms", "legs"],
    },
    "Mercury": {
        "en": "Skin, nerves, speech, lungs, intestines",
        "ta": "தோல், நரம்பு, பேச்சு, நுரையீரல், குடல்",
        "zones": ["torso", "abdomen", "head"],
    },
    "Jupiter": {
        "en": "Liver, fat, pancreas, ears, growth, thighs",
        "ta": "கல்லீரல், கொழுப்பு, கணையம், காது, வளர்ச்சி, தொடை",
        "zones": ["abdomen", "legs", "head"],
    },
    "Venus": {
        "en": "Reproductive organs, kidneys, throat, face, semen / ovaries",
        "ta": "இனப்பெருக்க உறுப்பு, சிறுநீரகம், தொண்டை, முகம்",
        "zones": ["pelvis", "abdomen", "neck", "head"],
    },
    "Saturn": {
        "en": "Bones, joints, teeth, knees, chronic delay, constipation",
        "ta": "எலும்பு, மூட்டு, பல், முழங்கால், நாள்பட்ட நிலை, மலச்சிக்கல்",
        "zones": ["legs", "head"],
    },
    "Rahu": {
        "en": "Sudden / unusual illness, poisoning, phobia, viral-like onset",
        "ta": "திடீர் / அசாதாரண நோய், நஞ்சு, பயம், வைரஸ் போன்ற தொடக்கம்",
        "zones": ["head", "abdomen"],
    },
    "Ketu": {
        "en": "Wounds, surgery, chronic mystery, lesions, feet",
        "ta": "காயம், அறுவை, மறைந்த நாள்பட்ட நிலை, புண், பாதம்",
        "zones": ["legs", "pelvis"],
    },
}

# Kalapurusha: Aries = head … Pisces = feet (sign the planet occupies in D1).
KALAPURUSHA: list[dict] = [
    {"sign": "Aries", "en": "Head", "ta": "தலை", "zones": ["head"]},
    {"sign": "Taurus", "en": "Face, throat, neck", "ta": "முகம், தொண்டை, கழுத்து", "zones": ["head", "neck"]},
    {"sign": "Gemini", "en": "Arms, shoulders, lungs, hands", "ta": "கை, தோள், நுரையீரல்", "zones": ["arms", "chest"]},
    {"sign": "Cancer", "en": "Chest, stomach, breasts", "ta": "மார்பு, வயிறு, மார்பகம்", "zones": ["chest", "abdomen"]},
    {"sign": "Leo", "en": "Heart, spine, upper back", "ta": "இதயம், முதுகெலும்பு", "zones": ["chest", "torso"]},
    {"sign": "Virgo", "en": "Intestines, abdomen", "ta": "குடல், வயிறு", "zones": ["abdomen"]},
    {"sign": "Libra", "en": "Kidneys, lumbar, skin", "ta": "சிறுநீரகம், இடுப்பு, தோல்", "zones": ["abdomen", "pelvis"]},
    {"sign": "Scorpio", "en": "Genitals, bladder, colon", "ta": "பிறப்புறுப்பு, சிறுநீர்ப்பை, பெருங்குடல்", "zones": ["pelvis"]},
    {"sign": "Sagittarius", "en": "Hips, thighs", "ta": "இடுப்பு, தொடை", "zones": ["pelvis", "legs"]},
    {"sign": "Capricorn", "en": "Knees, bones, joints", "ta": "முழங்கால், எலும்பு, மூட்டு", "zones": ["legs"]},
    {"sign": "Aquarius", "en": "Calves, ankles, circulation", "ta": "கெண்டைக்கால், கணுக்கால், சுழற்சி", "zones": ["legs"]},
    {"sign": "Pisces", "en": "Feet, lymph", "ta": "பாதம், நிணநீர்", "zones": ["legs"]},
]

_KALA_BY_SIGN = {row["sign"]: row for row in KALAPURUSHA}


def build_planet_karakas(
    d1_positions: dict,
    planet_rows: list[dict],
) -> list[dict]:
    """One row per planet: illness karaka + Kalapurusha from D1 sign + live marks."""
    live = {row.get("planet"): row for row in planet_rows or []}
    out: list[dict] = []
    for planet in PLANETS:
        spec = PLANET_ROGA[planet]
        d1 = d1_positions.get(planet) or {}
        sign = d1.get("sign") or SIGNS[int(d1.get("sign_index") or 0) % 12]
        kala = _KALA_BY_SIGN.get(sign) or KALAPURUSHA[0]
        row_live = live.get(planet) or {}
        out.append({
            "planet": planet,
            "roga_en": spec["en"],
            "roga_ta": spec["ta"],
            "zones": list(spec["zones"]),
            "sign": sign,
            "kalapurusha_en": kala["en"],
            "kalapurusha_ta": kala["ta"],
            "kalapurusha_zones": list(kala["zones"]),
            "live_dasa": bool(row_live.get("live_dasa")),
            "live_transit_bj": bool(row_live.get("live_transit_bj")),
        })
    return out


def karakas_for_zone(karaka_rows: list[dict], zone: str) -> list[dict]:
    if not zone:
        return []
    return [
        row for row in karaka_rows
        if zone in (row.get("zones") or []) or zone in (row.get("kalapurusha_zones") or [])
    ]
