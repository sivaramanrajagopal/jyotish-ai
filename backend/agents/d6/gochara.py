"""Gochara on D1 houses 1, 6, 8 — month layer, unique per lagna. No score."""

from __future__ import annotations

from agents.natal_agent import SIGNS, calculate_natal_chart
from agents.transit_score_agent import _planet_aspects
from time_utils import today_ist

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]
SLOW = frozenset({"Mars", "Jupiter", "Saturn", "Rahu", "Ketu"})
MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
RIPU_HOUSES = (1, 6, 8)

HOUSE_EN = {
    1: "body and how you meet the fight",
    6: "debt, opposition, contests, service, health-as-a-fight",
    8: "documents, shocks, a chronic undercurrent",
}
HOUSE_TA = {
    1: "உடல் மற்றும் போரை எதிர்கொள்ளும் பாணி",
    6: "கடன், எதிர்ப்பு, போட்டி, சேவை, நோய்-தடை",
    8: "ஆவணம், திடீர், நாள்பட்ட அழுத்தம்",
}


def _house_of(sign_index: int, asc_idx: int) -> int:
    return (int(sign_index) - int(asc_idx)) % 12 + 1


def _sign_of(asc_idx: int, house: int) -> str:
    return SIGNS[(int(asc_idx) + int(house) - 1) % 12]


def transit_positions_for_today(natal_chart: dict) -> tuple[dict, str]:
    bd = natal_chart.get("birth_data") or {}
    lat, lon = bd.get("lat"), bd.get("lon")
    tz = bd.get("timezone") or "Asia/Kolkata"
    day = today_ist().isoformat()
    if lat is None or lon is None:
        return {}, day
    try:
        sky = calculate_natal_chart(day, "12:00", float(lat), float(lon), tz)
        return sky.get("planet_positions") or {}, day
    except Exception:
        return {}, day


def _empty(as_of: str) -> dict:
    houses = [
        {
            "house": h,
            "sign": "",
            "theme_en": HOUSE_EN[h],
            "theme_ta": HOUSE_TA[h],
            "occupants": [],
            "aspects": [],
        }
        for h in RIPU_HOUSES
    ]
    return {
        "as_of": as_of,
        "read": "quiet",
        "read_en": "Quiet",
        "read_ta": "அமைதி",
        "why_en": "Sky on 1 / 6 / 8 is quiet today.",
        "why_ta": "1 / 6 / 8 வானம் அமைதி.",
        "line_en": "This month the sky is Quiet on your lagna's 1 / 6 / 8.",
        "line_ta": "இந்த மாதம் வானம் அமைதி — உங்கள் லக்ன 1 / 6 / 8.",
        "now_en": "Gochara on your 1st, 6th and 8th is quiet today. Same sky — houses follow your lagna.",
        "now_ta": "இன்று 1, 6, 8 கோசாரம் அமைதி. அதே வானம் — வீடுகள் உங்கள் லக்னத்தைப் பொறுத்தது.",
        "remedy_en": "No extra sky pressure this month on 1 / 6 / 8. Keep the Dasa conduct.",
        "remedy_ta": "இந்த மாதம் 1 / 6 / 8 கூடுதல் அழுத்தம் இல்லை. தசை நடத்தையையே பின்பற்றுங்கள்.",
        "houses": houses,
        "hits": [],
    }


def build_ripus_gochara(natal_chart: dict, d1_asc_idx: int) -> dict:
    """Slow planets occupying or aspecting THIS native's D1 1 / 6 / 8."""
    transit_pp, as_of = transit_positions_for_today(natal_chart)
    if not transit_pp:
        return _empty(as_of)

    by_house: dict[int, dict] = {
        h: {
            "house": h,
            "sign": _sign_of(d1_asc_idx, h),
            "theme_en": HOUSE_EN[h],
            "theme_ta": HOUSE_TA[h],
            "occupants": [],
            "aspects": [],
        }
        for h in RIPU_HOUSES
    }
    hits: list[dict] = []

    for planet in PLANETS:
        pos = transit_pp.get(planet) or {}
        if pos.get("sign_index") is None:
            continue
        at = _house_of(int(pos["sign_index"]), d1_asc_idx)
        sign = pos.get("sign") or SIGNS[int(pos["sign_index"]) % 12]
        retro = bool(pos.get("retrograde")) and planet not in ("Sun", "Moon", "Rahu", "Ketu")
        label = f"{planet} (R)" if retro else planet
        if at in by_house:
            by_house[at]["occupants"].append(label)
            hits.append({
                "planet": planet,
                "kind": "occupy",
                "house": at,
                "sign": sign,
                "slow": planet in SLOW,
                "malefic": planet in MALEFICS,
            })
        if planet not in SLOW:
            continue
        for target in _planet_aspects(planet, at):
            if target in by_house and target != at:
                by_house[target]["aspects"].append(f"{label} from H{at}")
                hits.append({
                    "planet": planet,
                    "kind": "aspect",
                    "house": target,
                    "from_house": at,
                    "sign": sign,
                    "slow": True,
                    "malefic": planet in MALEFICS,
                })

    occupy = [h for h in hits if h["kind"] == "occupy" and h["slow"]]
    occupy_malefic_68 = [
        h for h in occupy if h["malefic"] and h["house"] in (6, 8)
    ]
    occupy_6 = [h for h in occupy if h["house"] == 6]
    occupy_8 = [h for h in occupy if h["house"] == 8]
    saturn_on_6 = any(h["planet"] == "Saturn" and h["house"] == 6 for h in occupy)
    node_on_6 = any(h["planet"] in ("Rahu", "Ketu") and h["house"] == 6 for h in occupy)
    slow_hits = [h for h in hits if h["slow"]]
    n = len({(h["planet"], h["house"], h["kind"]) for h in slow_hits})

    if (occupy_6 and occupy_8) or saturn_on_6 or node_on_6:
        tone, tone_en, tone_ta = "challenging", "Challenging", "கடினம்"
        why_en = "A slow planet sits in your 6th, or both 6th and 8th are occupied this month."
        why_ta = "மெது கிரகம் 6ம் வீட்டில், அல்லது 6 மற்றும் 8 இரண்டும் நிறைவு."
    elif occupy_malefic_68 or n >= 2:
        tone, tone_en, tone_ta = "careful", "Careful", "கவனம்"
        why_en = "A malefic occupies your 6th or 8th, or two slow hits on 1 / 6 / 8."
        why_ta = "பாப கிரகம் 6 அல்லது 8ல், அல்லது 1 / 6 / 8 இரண்டு மெது தொடுதல்."
    elif slow_hits:
        tone, tone_en, tone_ta = "watch", "Watch", "கவனிப்பு"
        why_en = "One slow planet touches your 1st, 6th or 8th this month."
        why_ta = "ஒரு மெது கிரகம் இந்த மாதம் 1, 6 அல்லது 8ஐத் தொடுகிறது."
    else:
        tone, tone_en, tone_ta = "quiet", "Quiet", "அமைதி"
        why_en = "No slow planet occupies or aspects your 1st, 6th or 8th today."
        why_ta = "இன்று மெது கிரகம் 1, 6, 8ஐத் தொடவில்லை."

    bits = []
    for h in RIPU_HOUSES:
        row = by_house[h]
        occ = ", ".join(row["occupants"]) or "empty"
        asp = ", ".join(row["aspects"])
        bit = f"H{h} {row['sign']} ({HOUSE_EN[h]}): {occ}"
        if asp:
            bit += f"; aspected by {asp}"
        bits.append(bit)
    short_bits = []
    for h in RIPU_HOUSES:
        row = by_house[h]
        names = row["occupants"] + [a.split(" from")[0] for a in row["aspects"]]
        if names:
            short_bits.append(f"H{h} {row['sign']} ({', '.join(names)})")
    line_en = (
        f"This month the sky is {tone_en} on your lagna's 1 / 6 / 8"
        + (": " + "; ".join(short_bits) if short_bits else "")
        + "."
    )
    line_ta = f"இந்த மாதம் வானம் {tone_ta} — உங்கள் லக்ன 1 / 6 / 8."
    now_en = (
        f"Gochara is counted from your lagna, so this sky is yours alone. "
        f"This month I would mark the sky as {tone_en}: {why_en} "
        + " ".join(bits) + "."
    )
    now_ta = (
        f"கோசாரம் உங்கள் லக்னத்திலிருந்து. இந்த மாதம் வானம் {tone_ta}. {why_ta}"
    )

    if tone == "challenging":
        remedy_en = "This month: papers dated, no new fight, extra rest. Body map stays on Health."
        remedy_ta = "இந்த மாதம்: ஆவணம் தேதியுடன், புதிய சண்டை வேண்டாம், கூடுதல் ஓய்வு. உடல்: Health."
    elif tone == "careful":
        remedy_en = "This month: slower decisions on dues, disputes, and health checks. Same sky, your houses."
        remedy_ta = "இந்த மாதம்: கடன், தகராறு, உடல் பரிசோதனையில் மெது முடிவு."
    elif tone == "watch":
        remedy_en = "This month: live normally; stay awake to the house the sky is touching."
        remedy_ta = "இந்த மாதம் வாழ்க்கை நடத்தலாம்; வானம் தொடும் வீட்டைக் கவனிக்கவும்."
    else:
        remedy_en = "No extra sky pressure this month on 1 / 6 / 8. Keep the Dasa conduct."
        remedy_ta = "இந்த மாதம் 1 / 6 / 8 கூடுதல் அழுத்தம் இல்லை. தசை நடத்தையையே பின்பற்றுங்கள்."

    return {
        "as_of": as_of,
        "read": tone,
        "read_en": tone_en,
        "read_ta": tone_ta,
        "why_en": why_en,
        "why_ta": why_ta,
        "line_en": line_en,
        "line_ta": line_ta,
        "now_en": now_en,
        "now_ta": now_ta,
        "remedy_en": remedy_en,
        "remedy_ta": remedy_ta,
        "houses": [by_house[h] for h in RIPU_HOUSES],
        "hits": hits,
    }
