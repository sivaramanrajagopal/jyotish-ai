"""Bhavat Bhavam — house-from-house (D1 whole-sign)."""

from __future__ import annotations

from agents.natal_agent import EXALTATION, SIGN_LORDS, SIGNS
from agents.transit_score_agent import _planet_aspects

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]
BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
KENDRA = frozenset({1, 4, 7, 10})

OWN_SIGNS: dict[str, list[str]] = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

HOUSE_THEMES: dict[int, dict[str, str]] = {
    1: {"en": "Self & vitality", "ta": "சுயம் / உயிர்சக்தி"},
    2: {"en": "Wealth & family", "ta": "செல்வம் / குடும்பம்"},
    3: {"en": "Courage & skills", "ta": "தைரியம் / திறன்"},
    4: {"en": "Home & happiness", "ta": "வீடு / சந்தோஷம்"},
    5: {"en": "Creativity & children", "ta": "படைப்பு / பிள்ளை"},
    6: {"en": "Health & service", "ta": "ஆரோக்கியம் / சேவை"},
    7: {"en": "Partnership & public", "ta": "கூட்டாளர் / பொது"},
    8: {"en": "Chronic / transformation", "ta": "நாள்பட்ட / மாற்றம்"},
    9: {"en": "Fortune & dharma", "ta": "பாக்கியம் / தர்மம்"},
    10: {"en": "Career & karma", "ta": "தொழில் / கர்மம்"},
    11: {"en": "Gains & recovery", "ta": "லாபம் / குணமடைதல்"},
    12: {"en": "Loss / hospital", "ta": "இழப்பு / மருத்துவம்"},
}

BB_THEMES: dict[int, dict[str, str]] = {
    6: {"en": "Disease → recovery through gains (11th)", "ta": "நோய் → 11ம் வழி குணமடைதல்"},
    8: {"en": "Crisis → courage & will (3rd)", "ta": "சிக்கல் → 3ம் வழி தைரியம்"},
    12: {"en": "Hospital / expense → fulfillment (11th)", "ta": "செலவு → 11ம் வழி நிறைவு"},
    10: {"en": "Career → partnerships & public (7th)", "ta": "தொழில் → 7ம் வழி கூட்டாளர்"},
    2: {"en": "Wealth → courage & skills (3rd)", "ta": "செல்வம் → 3ம் வழி திறன்"},
}


def bhavat_bhavam_house(house: int) -> int:
    """Count `house` houses from `house` (whole-sign)."""
    h = int(house)
    return ((h - 1) + (h - 1)) % 12 + 1


def whole_sign_house(planet_sign_index: int, asc_sign_index: int) -> int:
    return (int(planet_sign_index) - int(asc_sign_index)) % 12 + 1


def lord_of_house(asc_sign_index: int, house: int) -> str:
    sign_idx = (int(asc_sign_index) + int(house) - 1) % 12
    return SIGN_LORDS[SIGNS[sign_idx]]


def sign_of_house(asc_sign_index: int, house: int) -> str:
    sign_idx = (int(asc_sign_index) + int(house) - 1) % 12
    return SIGNS[sign_idx]


def planets_in_house(
    planet_positions: dict,
    asc_sign_index: int,
    house: int,
) -> list[str]:
    out: list[str] = []
    for planet in PLANETS:
        pdata = planet_positions.get(planet) or {}
        if pdata.get("sign_index") is None:
            continue
        if whole_sign_house(pdata["sign_index"], asc_sign_index) == house:
            out.append(planet)
    return sorted(out)


def _lord_strength_tags(lord: str, planet_positions: dict, asc_sign_index: int) -> list[str]:
    if not lord or lord not in planet_positions:
        return []
    pdata = planet_positions[lord]
    sign = pdata.get("sign", "")
    house = whole_sign_house(pdata.get("sign_index", 0), asc_sign_index)
    tags: list[str] = []
    if sign in OWN_SIGNS.get(lord, []):
        tags.append("own sign")
    ex_idx, _ = EXALTATION.get(lord, (-1, 0))
    if ex_idx >= 0 and SIGNS[ex_idx] == sign:
        tags.append("exalted")
    if house in KENDRA:
        tags.append("Kendra")
    return tags


def _lords_linked(
    lord_a: str,
    lord_b: str,
    planet_positions: dict,
    asc_sign_index: int,
) -> list[str]:
    if not lord_a or not lord_b:
        return []
    links: list[str] = []
    if lord_a == lord_b:
        links.append("same planet")
        return links

    pa = planet_positions.get(lord_a) or {}
    pb = planet_positions.get(lord_b) or {}
    if not pa.get("sign_index") or not pb.get("sign_index"):
        return links

    ha = whole_sign_house(pa["sign_index"], asc_sign_index)
    hb = whole_sign_house(pb["sign_index"], asc_sign_index)

    if pa.get("sign") == pb.get("sign"):
        links.append("conjunction")
    if ha == hb:
        links.append("same house")

    asp_a = set(_planet_aspects(lord_a, ha))
    asp_b = set(_planet_aspects(lord_b, hb))
    if hb in asp_a:
        links.append(f"{lord_a} aspects {lord_b}")
    if ha in asp_b:
        links.append(f"{lord_b} aspects {lord_a}")

    return links


def _signal_label(score: float) -> str:
    if score >= 3:
        return "support"
    if score >= 1.5:
        return "watch"
    return "neutral"


def _signal_label_ta(signal: str) -> str:
    return {
        "support": "ஆதரவு வழி",
        "watch": "கவனம்",
        "neutral": "நடுநிலை",
    }.get(signal, signal)


def evaluate_link(
    primary_house: int,
    *,
    asc_sign_index: int,
    planet_positions: dict,
    maha: str = "",
    bhukti: str = "",
    slice_kind: str = "health",
) -> dict:
    """Evaluate one primary → Bhavat Bhavam link."""
    bb_house = bhavat_bhavam_house(primary_house)
    primary_lord = lord_of_house(asc_sign_index, primary_house)
    bb_lord = lord_of_house(asc_sign_index, bb_house)
    primary_planets = planets_in_house(planet_positions, asc_sign_index, primary_house)
    bb_planets = planets_in_house(planet_positions, asc_sign_index, bb_house)

    primary_active = False
    triggers_en: list[str] = []
    triggers_ta: list[str] = []

    if primary_planets:
        primary_active = True
        triggers_en.append(f"Planets in H{primary_house}: {', '.join(primary_planets)}")
        triggers_ta.append(f"H{primary_house} கிரகங்கள்: {', '.join(primary_planets)}")
    if any(p in MALEFICS for p in primary_planets):
        triggers_en.append("Malefic pressure on primary house")
        triggers_ta.append("பாப கிரக அழுத்தம்")
    if primary_lord in (maha, bhukti):
        primary_active = True
        triggers_en.append(f"{primary_lord} active Dasa/Bhukti lord")
        triggers_ta.append(f"{primary_lord} நடப்பு தசை/புத்தி")
    if slice_kind == "career" and primary_house == 10:
        primary_active = True
        triggers_en.append("Career house under analysis")
        triggers_ta.append("தொழில் வீடு பகுப்பாய்வு")

    score = 0.0
    support_en: list[str] = []
    support_ta: list[str] = []

    bb_tags = _lord_strength_tags(bb_lord, planet_positions, asc_sign_index)
    if bb_tags:
        score += 1.5
        support_en.append(f"BB lord {bb_lord} strong ({', '.join(bb_tags)})")
        support_ta.append(f"BB அதிபதி {bb_lord} வலிமை ({', '.join(bb_tags)})")
    if any(p in BENEFICS for p in bb_planets):
        score += 1.0
        support_en.append(f"Benefic in H{bb_house}: {', '.join(p for p in bb_planets if p in BENEFICS)}")
        support_ta.append(f"H{bb_house} நன்மை கிரகம்")
    if bb_lord in (maha, bhukti):
        score += 1.5
        support_en.append(f"BB lord {bb_lord} in active Dasa/Bhukti")
        support_ta.append(f"BB அதிபதி {bb_lord} தசை/புத்தியில்")

    links = _lords_linked(primary_lord, bb_lord, planet_positions, asc_sign_index)
    if links:
        score += 1.0
        support_en.append(f"Lords linked: {', '.join(links)}")
        support_ta.append(f"அதிபதிகள் தொடர்பு: {', '.join(links)}")

    signal = _signal_label(score) if primary_active else "inactive"
    theme = BB_THEMES.get(primary_house, {})

    insight_en = _build_insight_en(
        primary_house, bb_house, primary_lord, bb_lord,
        primary_planets, bb_planets, signal, slice_kind,
    )
    insight_ta = _build_insight_ta(
        primary_house, bb_house, primary_lord, bb_lord, signal, slice_kind,
    )

    return {
        "primary_house": primary_house,
        "bb_house": bb_house,
        "primary_label_en": HOUSE_THEMES[primary_house]["en"],
        "primary_label_ta": HOUSE_THEMES[primary_house]["ta"],
        "bb_label_en": HOUSE_THEMES[bb_house]["en"],
        "bb_label_ta": HOUSE_THEMES[bb_house]["ta"],
        "theme_en": theme.get("en", ""),
        "theme_ta": theme.get("ta", ""),
        "primary_lord": primary_lord,
        "bb_lord": bb_lord,
        "primary_planets": primary_planets,
        "bb_planets": bb_planets,
        "primary_sign": sign_of_house(asc_sign_index, primary_house),
        "bb_sign": sign_of_house(asc_sign_index, bb_house),
        "lord_links": links,
        "bb_lord_strength": bb_tags,
        "primary_active": primary_active,
        "triggers_en": triggers_en,
        "triggers_ta": triggers_ta,
        "support_en": support_en,
        "support_ta": support_ta,
        "signal": signal,
        "signal_ta": _signal_label_ta(signal) if signal != "inactive" else "செயலற்ற",
        "score": round(score, 1),
        "insight_en": insight_en,
        "insight_ta": insight_ta,
    }


def _build_insight_en(
    ph: int, bb: int, pl: str, bl: str,
    p_planets: list[str], bb_planets: list[str],
    signal: str, slice_kind: str,
) -> str:
    if signal == "inactive":
        return f"H{ph} quiet — Bhavat Bhavam H{bb} link dormant until primary house activates."
    role = "recovery path" if slice_kind == "health" else "support path"
    parts = [f"H{ph} ({pl}) → Bhavat Bhavam H{bb} ({bl}) as {role}."]
    if p_planets:
        parts.append(f"H{ph} has {', '.join(p_planets)}.")
    if bb_planets:
        parts.append(f"H{bb} has {', '.join(bb_planets)}.")
    if signal == "support":
        parts.append(f"BB lord {bl} offers a constructive channel — watch Dasa/transits on {bl}.")
    elif signal == "watch":
        parts.append(f"Link present but moderate — combine with Dasa timing on {pl} and {bl}.")
    return " ".join(parts)


def _build_insight_ta(ph: int, bb: int, pl: str, bl: str, signal: str, slice_kind: str) -> str:
    if signal == "inactive":
        return f"H{ph} அமைதி — BB H{bb} தொடர்பு செயலில் இல்லை."
    role = "குணமடைதல் வழி" if slice_kind == "health" else "ஆதரவு வழி"
    base = f"H{ph} ({pl}) → BB H{bb} ({bl}) {role}."
    if signal == "support":
        return base + f" BB அதிபதி {bl} ஆதரவு — {bl} தசை/கோசாரம் கவனிக்கவும்."
    return base + f" {pl}, {bl} தசை காலங்களுடன் இணைத்துப் பார்க்கவும்."
