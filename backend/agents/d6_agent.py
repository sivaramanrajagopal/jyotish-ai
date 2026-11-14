"""
d6_agent.py — D1 + D6 Ripu (obstacles: debt, enemies, exams, service, illness-as-fight).
"""

from __future__ import annotations

from typing import Optional

from time_utils import today_ist

from agents.d6.gochara import build_ripus_gochara
from agents.d6.shashthamsa import build_shashthamsa_from_natal
from agents.d6.themes import build_theme_cards, house_snapshot, _lord_of
from agents.d6.timing import READING_GUIDE, build_ripus_timing
from agents.natal_agent import SIGNS
from dasha_core import find_current_dasha_bhukti

DISCLAIMER = (
    "Traditional Jyotish notes on obstacles (Ripu). Not medical, legal, or exam advice. "
    "The body map lives on the Health tab. Career type lives on the Career tab."
)

ASK_PROMPT = (
    "In plain language, what does my D1 and D6 Ripu chart mean for me now? "
    "Cover debt, enemies, competitive exams, service work, and illness as an obstacle. "
    "Use only this app's D6 notes. Traditional Jyotish only — not medical, legal, or exam advice."
)


def build_native_meaning(
    *,
    summary: dict,
    themes: list[dict],
    current: list,
    upcoming: list,
    gochara: Optional[dict] = None,
) -> dict:
    """Short reading a native can use — no score, no diagnosis."""
    s = summary
    present = [c["title"] for c in themes if c["tone"] == "present"]
    mixed = [c["title"] for c in themes if c["tone"] == "mixed"]

    en = [
        f"D6 is the chart of Ripu: how you meet obstacles. "
        f"Your D6 lagna is {s['d6_lagna']}, so {s['d6_lagna_lord']} sets the style of that fight. "
        f"In the birth chart the 6th house is {s['d1_sixth_sign']}, ruled by {s['d1_sixth_lord']}."
    ]
    ta = [
        f"D6 ரிபு வரைபடம் — தடைகளை எப்படி எதிர்கொள்கிறீர்கள். "
        f"D6 லக்னம் {s['d6_lagna']}, அதிபதி {s['d6_lagna_lord']}. "
        f"பிறப்பு 6ம் வீடு {s['d1_sixth_sign']}, அதிபதி {s['d1_sixth_lord']}."
    ]
    if current:
        c = current[0]
        links = ", ".join(c.get("links") or [])
        en.append(
            f"This period is {c['label']} ({c['start']} to {c['end']})"
            + (f", linked to {links}." if links else ".")
            + " " + (c.get("why_en") or c.get("say_en") or "")
        )
        ta.append(
            f"இப்போது {c['label']} ({c['start']} – {c['end']})"
            + (f" — {links}." if links else ".")
            + " " + (c.get("why_ta") or "")
        )
    elif upcoming:
        u = upcoming[0]
        en.append(f"No 6th/8th Dasa link is on today. The next Ripu window is {u['label']} from {u['start']}.")
        ta.append(f"இன்று 6/8 தசை இணைப்பு இல்லை. அடுத்த ரிபு காலம் {u['label']} {u['start']} முதல்.")
    if present:
        en.append("Showing as present: " + ", ".join(present) + ".")
        ta.append("இப்போது தெரிவது: " + ", ".join(present) + ".")
    elif mixed:
        en.append("Showing as mixed: " + ", ".join(mixed) + ".")
        ta.append("கலப்பு: " + ", ".join(mixed) + ".")
    else:
        en.append("The 6th and 8th are quiet in this period. The charts still show the natal layout.")
        ta.append("இந்த காலத்தில் 6, 8 அமைதி. வரைபடங்கள் பிறப்பு அமைப்பையே காட்டுகின்றன.")
    if current and upcoming:
        u = upcoming[0]
        en.append(f"Next window: {u['label']} from {u['start']}.")
        ta.append(f"அடுத்த காலம்: {u['label']} {u['start']} முதல்.")
    if gochara and gochara.get("line_en"):
        en.append(gochara["line_en"])
        if gochara.get("line_ta"):
            ta.append(gochara["line_ta"])
    en.append("This is traditional Jyotish, not a medical, legal, or exam result. Body map: Health tab. Profession type: Career tab.")
    ta.append("இது பாரம்பரிய ஜோதிடம் மட்டும். மருத்துவம், சட்டம், தேர்வு முடிவு அல்ல. உடல் வரைபடம்: Health. தொழில் வகை: Career.")
    return {
        "en": " ".join(en),
        "ta": " ".join(ta),
        "ask_prompt": ASK_PROMPT,
    }


# Ripu houses when speaking to a client — D6 7th is the other party, never marriage.
_HOUSE_SAY_EN = {
    1: "your own manner of facing the obstacle",
    2: "speech, money, and family store",
    3: "courage and fighting back",
    4: "home and peace of mind",
    5: "intelligence and counsel",
    6: "the obstacle itself",
    7: "the other party in a contest",
    8: "sudden or hidden pressure",
    9: "dharma and support",
    10: "daily work and public effort",
    11: "gains and networks",
    12: "cost, institutions, and work behind the scenes",
}
_HOUSE_SAY_TA = {
    1: "தடையை எதிர்கொள்ளும் உங்கள் பாணி",
    2: "பேச்சு, பணம், குடும்பச் சேமிப்பு",
    3: "தைரியம் மற்றும் எதிர்த்து நிற்பது",
    4: "வீடு மற்றும் மன அமைதி",
    5: "அறிவு மற்றும் ஆலோசனை",
    6: "தடை அதன்மேல்",
    7: "போட்டியில் எதிர்ப்பக்கம்",
    8: "திடீர் அல்லது மறைந்த அழுத்தம்",
    9: "தர்மம் மற்றும் ஆதரவு",
    10: "தினசரி பணி",
    11: "லாபம் மற்றும் வலையமைப்பு",
    12: "செலவு, நிறுவனம், பின்னணிப் பணி",
}


def _join_names(names: list[str]) -> str:
    names = [n for n in names if n]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + ", and " + names[-1]


def _house_of(positions: dict, planet: str) -> int:
    return int((positions.get(planet) or {}).get("house") or 0)


def _nth(house: int) -> str:
    house = int(house)
    if house in (11, 12):
        return f"{house}th"
    if house % 10 == 1:
        return f"{house}st"
    if house % 10 == 2:
        return f"{house}nd"
    if house % 10 == 3:
        return f"{house}rd"
    return f"{house}th"


def build_client_summary(
    *,
    summary: dict,
    themes: list[dict],
    current: list,
    upcoming: list,
    d6_positions: dict,
    d6_asc_idx: int,
    maha: str,
    bhukti: str,
    outlook: Optional[dict] = None,
    gochara: Optional[dict] = None,
) -> dict:
    """Spoken consultation script — second person, no score, no diagnosis."""
    s = summary
    d6_3 = house_snapshot(d6_positions, d6_asc_idx, 3)
    d6_6 = house_snapshot(d6_positions, d6_asc_idx, 6)
    d6_8 = house_snapshot(d6_positions, d6_asc_idx, 8)
    maha_h = _house_of(d6_positions, maha)
    bhukti_h = _house_of(d6_positions, bhukti)
    present = [c["title"] for c in themes if c["tone"] == "present"]
    mixed = [c["title"] for c in themes if c["tone"] == "mixed"]

    en: list[str] = []
    ta: list[str] = []

    en.append(
        f"Let me tell you in simple words what this Ripu chart is saying for you now. "
        f"Your D6 lagna is {s['d6_lagna']}, so {s['d6_lagna_lord']} sets how you meet a fight. "
        f"In the birth chart the sixth house is {s['d1_sixth_sign']}, ruled by {s['d1_sixth_lord']}."
    )
    ta.append(
        f"இந்த ரிபு வரைபடம் உங்களுக்கு இப்போது சொல்வதை எளிய வார்த்தையில் சொல்கிறேன். "
        f"D6 லக்னம் {s['d6_lagna']}, அதிபதி {s['d6_lagna_lord']} — தடையை எதிர்கொள்ளும் பாணி. "
        f"பிறப்பு 6ம் வீடு {s['d1_sixth_sign']}, அதிபதி {s['d1_sixth_lord']}."
    )

    if current:
        c = current[0]
        maha_bit = (
            f"The Dasa lord {maha} sits in the D6 {_nth(maha_h)} — {_HOUSE_SAY_EN.get(maha_h, 'this house')}."
            if maha_h else f"The Dasa lord is {maha}."
        )
        if bhukti_h and bhukti_h != maha_h:
            bhukti_bit = (
                f" The Bhukti lord {bhukti} sits in the D6 {_nth(bhukti_h)} — "
                f"{_HOUSE_SAY_EN.get(bhukti_h, 'this house')}."
            )
        elif bhukti_h == maha_h:
            bhukti_bit = f" {bhukti} joins {maha} in that same house."
        else:
            bhukti_bit = ""
        en.append(
            f"You are running {c['label']} from {c['start']} to {c['end']}. "
            f"{maha_bit}{bhukti_bit} "
            + (c.get("say_en") or c.get("why_en") or "")
        )
        ta.append(
            f"இப்போது {c['label']} — {c['start']} முதல் {c['end']} வரை. "
            f"தசை அதிபதி {maha} D6 {maha_h}ம் வீட்டில் — {_HOUSE_SAY_TA.get(maha_h, '')}. "
            + (
                f"புக்தி {bhukti} D6 {bhukti_h}ம் வீட்டில் — {_HOUSE_SAY_TA.get(bhukti_h, '')}. "
                if bhukti_h and bhukti_h != maha_h
                else (f"{bhukti} அதே வீட்டில் சேர்கிறது. " if bhukti_h == maha_h else "")
            )
            + (c.get("why_ta") or "")
        )
    elif upcoming:
        u = upcoming[0]
        en.append(f"No 6th or 8th Dasa link is on today. The next Ripu window is {u['label']} from {u['start']}.")
        ta.append(f"இன்று 6/8 தசை இணைப்பு இல்லை. அடுத்த ரிபு காலம் {u['label']} {u['start']} முதல்.")

    sixth_empty = not d6_6["occupants"]
    eighth_empty = not d6_8["occupants"]
    if sixth_empty and eighth_empty:
        en.append(
            f"The D6 sixth ({d6_6['sign']}) and eighth ({d6_8['sign']}) are empty. "
            f"The sixth lord {d6_6['lord']} is in the D6 {_nth(d6_6['lord_house'])} — "
            f"{_HOUSE_SAY_EN.get(d6_6['lord_house'], 'that house')}. "
            "The path is to work through with patience."
        )
        ta.append(
            f"D6 6ம் வீடு ({d6_6['sign']}) மற்றும் 8ம் வீடு ({d6_8['sign']}) காலியாக உள்ளன. "
            f"6ம் அதிபதி {d6_6['lord']} D6 {d6_6['lord_house']}ம் வீட்டில். பொறுமையுடன் கடந்து செல்லும் பாதை."
        )
    elif d6_6["occupants"]:
        en.append(
            f"In the D6 sixth sit {_join_names(d6_6['occupants'])}. That is the obstacle house in this varga."
        )
        ta.append(f"D6 6ம் வீட்டில் {_join_names(d6_6['occupants'])} உள்ளனர். இதுவே இந்த வர்கத்தில் தடை வீடு.")

    if d6_3["occupants"]:
        en.append(
            f"In the D6 third sit {_join_names(d6_3['occupants'])}. That house shows you do fight back."
        )
        ta.append(
            f"D6 3ம் வீட்டில் {_join_names(d6_3['occupants'])} உள்ளனர். எதிர்த்து நிற்கும் வீடு இது."
        )

    if present:
        en.append("What is live for you now: " + ", ".join(present) + ".")
        ta.append("இப்போது நேரடியாகத் தெரிவது: " + ", ".join(present) + ".")
    if mixed:
        en.append("What needs care, and can be worked through: " + ", ".join(mixed) + ".")
        ta.append("கவனமும், கடந்து செல்லும் வழியும் உள்ளவை: " + ", ".join(mixed) + ".")
    if not present and not mixed:
        en.append("The 6th and 8th are quiet in this period. The charts still show the natal layout.")
        ta.append("இந்த காலத்தில் 6, 8 அமைதி. வரைபடங்கள் பிறப்பு அமைப்பையே காட்டுகின்றன.")

    if any(c["id"] == "illness" and c["tone"] != "quiet" for c in themes):
        en.append("For the body map, open the Health tab. This is not a medical reading.")
        ta.append("உடல் வரைபடம் Health தாவலில். இது மருத்துவ வாசிப்பு அல்ல.")
    if any(c["id"] == "service" and c["tone"] != "quiet" for c in themes):
        en.append("Daily work may feel like a contest. Profession type stays on the Career tab.")
        ta.append("தினசரி பணி போட்டியாகத் தெரியலாம். தொழில் வகை Career தாவலில்.")

    if current:
        win = current[0]
        if win.get("read_en"):
            en.append(
                f"I would mark this Dasa window as {win['read_en']}: {win.get('why_en', '')} "
                f"{win.get('say_en', '')} Remedy: {win.get('remedy_en', '')}"
            )
            ta.append(
                f"இந்த தசை காலம் {win.get('read_ta') or win['read_en']}: {win.get('why_ta', '')} "
                f"{win.get('remedy_ta', '')}"
            )
    if gochara and gochara.get("read") != "quiet":
        en.append(
            f"This month the sky is {gochara.get('read_en')}: {gochara.get('now_en', '')} "
            f"Remedy: {gochara.get('remedy_en', '')}"
        )
        ta.append(
            f"இந்த மாதம் வானம் {gochara.get('read_ta') or gochara.get('read_en')}: "
            f"{gochara.get('now_ta', '')} {gochara.get('remedy_ta', '')}"
        )
    elif gochara:
        en.append(gochara.get("now_en", ""))
        ta.append(gochara.get("now_ta", ""))
    if current and upcoming:
        u = upcoming[0]
        nxt = f"{u['label']} from {u['start']}"
        if u.get("read_en"):
            nxt += f" — {u['read_en']}"
        en.append(f"Next I would watch {nxt}.")
        ta.append(f"அடுத்து பார்க்க வேண்டியது {u['label']} {u['start']} முதல்" + (
            f" — {u.get('read_ta') or u.get('read_en', '')}." if u.get("read_en") else "."
        ))

    if outlook:
        if outlook.get("on"):
            en.append(outlook["recover_en"])
            ta.append(outlook["recover_ta"])
        else:
            en.append(outlook["now_en"])
            ta.append(outlook["now_ta"])

    en.append(
        "This is traditional Jyotish I can share with you. "
        "It is not a court result, an exam result, or a medical diagnosis."
    )
    ta.append("இது பாரம்பரிய ஜோதிடம் மட்டும். நீதிமன்றம், தேர்வு, மருத்துவ முடிவு அல்ல.")

    return {
        "title_en": "Say this to the client",
        "title_ta": "வாடிக்கையாளரிடம் இவ்வாறு சொல்லவும்",
        "en": " ".join(en),
        "ta": " ".join(ta),
        "paragraphs_en": en,
        "paragraphs_ta": ta,
    }


def build_karaka_outlook(
    *,
    cur_d: dict,
    cur_b: dict,
    current: list,
    d1_sixth_lord: str,
    d1_eighth_lord: str,
    d6_lagna_lord: str,
    d6_sixth_lord: str,
) -> dict:
    """Shared Now / Eases for all 6th-house karakas — dates only, no diagnosis."""
    roles = []
    maha = cur_d["planet"]
    bhukti = cur_b["planet"]
    mapping = [
        (d1_sixth_lord, "D1 6th lord"),
        (d1_eighth_lord, "D1 8th lord"),
        (d6_lagna_lord, "D6 lagna lord"),
        (d6_sixth_lord, "D6 6th lord"),
    ]
    key_planets = {p for p, _ in mapping if p}
    for planet, role in mapping:
        if planet and planet not in {r[0] for r in roles} and planet in {maha, bhukti}:
            roles.append((planet, role))
    role_en = ", ".join(f"{p} ({r})" for p, r in roles) or "no 6th/8th lord in this Dasa"
    spell = current[0] if current else None
    spell_label = spell["label"] if spell else f"{maha}–{bhukti}"
    spell_end = spell["end"] if spell else cur_b["end"].strftime("%Y-%m-%d")
    spell_start = spell["start"] if spell else cur_b["start"].strftime("%Y-%m-%d")
    on = bool(spell) or maha in key_planets or bhukti in key_planets
    chapter_end = cur_d["end"].strftime("%Y-%m-%d") if maha in key_planets else spell_end
    chapter_start = cur_d["start"].strftime("%Y-%m-%d")
    chapter_planet = maha if maha in key_planets else (bhukti if bhukti in key_planets else maha)

    if on:
        now_en = (
            f"A 6th-house chapter is on now. {role_en}. "
            f"This spell is {spell_label} ({spell_start} to {spell_end})."
        )
        now_ta = (
            f"6ம் வீட்டு அத்தியாயம் இப்போது நடக்கிறது. {role_en}. "
            f"இந்த புக்தி {spell_label} ({spell_start} – {spell_end})."
        )
        eases_en = (
            f"This spell eases on {spell_end}. "
            f"The {chapter_planet} chapter eases on {chapter_end}. "
            "In Jyotish that is when 6th-house pressure lifts for debt, opposition, "
            "contests, service strain, and health-as-a-fight."
        )
        eases_ta = (
            f"இந்த புக்தி {spell_end} அன்று தளர்கிறது. "
            f"{chapter_planet} அத்தியாயம் {chapter_end} அன்று தளர்கிறது. "
            "கடன், எதிர்ப்பு, போட்டி, சேவை, நோய்-தடை அழுத்தம் அப்போது இறங்குகிறது."
        )
        recover_en = (
            f"When I speak of recovery, I mean this obstacle-chapter lifting — "
            f"this spell eases {spell_end}, and the {chapter_planet} chapter eases {chapter_end}. "
            "Possible body areas are on the Health tab. That is not a medical recovery date, "
            "and I do not name a disease from D6."
        )
        recover_ta = (
            f"குணமடைதல் என்பது இந்த தடை அத்தியாயம் இறங்குவது — "
            f"புக்தி {spell_end}, {chapter_planet} அத்தியாயம் {chapter_end}. "
            "உடல் பகுதிகள் Health தாவலில். மருத்துவ குணமடைதல் தேதி அல்ல; D6 நோய் பெயர் சொல்லாது."
        )
    else:
        now_en = "No 6th/8th Dasa lord is running today. The natal 6th-house layout still stands."
        now_ta = "இன்று 6/8 தசை அதிபதி இல்லை. பிறப்பு 6ம் வீட்டு அமைப்பு நிற்கிறது."
        eases_en = "Watch the next Ripu Dasa window on the timing tables."
        eases_ta = "அடுத்த ரிபு தசை காலத்தை அட்டவணையில் பாருங்கள்."
        recover_en = (
            "Health-as-a-fight is quiet in Dasa now. Body areas still live on the Health tab."
        )
        recover_ta = "தசைப்படி நோய்-தடை அமைதி. உடல் பகுதிகள் Health தாவலில்."

    return {
        "on": on,
        "role_en": role_en,
        "chapter_planet": chapter_planet,
        "chapter_start": chapter_start,
        "chapter_end": chapter_end,
        "spell_label": spell_label,
        "spell_start": spell_start,
        "spell_end": spell_end,
        "now_en": now_en,
        "now_ta": now_ta,
        "eases_en": eases_en,
        "eases_ta": eases_ta,
        "recover_en": recover_en,
        "recover_ta": recover_ta,
    }


_THEME_FOCUS = {
    "debt": ("Debt and cases follow your {lord} of {sign} 6th.", 6),
    "enemies": ("Opposition follows your {lord} of {sign} 6th.", 6),
    "exams": ("Rivals / the paper follow your {lord} of {sign} 6th.", 6),
    "service": ("Daily service follows your {lord} of {sign} 6th; D6 10th is how the work lands.", 6),
    "illness": ("Health-as-a-fight follows your {lord} of {sign} 6th. Body map: Health tab.", 8),
}


def _sky_bit(house: int, sky_houses: dict) -> str:
    row = sky_houses.get(house) or {}
    occ = ", ".join(row.get("occupants") or [])
    asp = ", ".join(row.get("aspects") or [])
    if not occ and not asp:
        return ""
    bits = []
    if occ:
        bits.append(f"sky in H{house} {row.get('sign', '')}: {occ}")
    if asp:
        bits.append(f"aspected by {asp}")
    return " This month " + "; ".join(bits) + "."


def _fill_theme_now(card: dict, *, outlook: dict, native: dict, sky_houses: dict, gochara: dict) -> None:
    """Per-theme now/eases — not the same sentence on all five cards."""
    focus, sky_house = _THEME_FOCUS[card["id"]]
    lord = native.get("d1_sixth_lord") or ""
    sign = native.get("d1_sixth_sign") or ""
    head = focus.format(lord=lord, sign=sign)
    sky = _sky_bit(6 if card["id"] != "illness" else 8, sky_houses)
    if card["id"] == "illness":
        sky += _sky_bit(6, sky_houses)
        sky += _sky_bit(1, sky_houses)
    if outlook["on"] and card["tone"] != "quiet":
        card["now"] = (
            f"{head} On through {outlook['spell_end']} ({outlook['spell_label']}).{sky}"
        )
        card["eases"] = (
            f"This spell eases {outlook['spell_end']}. "
            f"The {outlook['chapter_planet']} chapter eases {outlook['chapter_end']}."
        )
        if card["id"] == "illness":
            card["eases"] += " Body areas: Health tab. Not a medical recovery date."
    elif outlook["on"]:
        card["now"] = f"{head} Quieter than the live 6th-house chapter.{sky}"
        card["eases"] = (
            f"The shared 6th-house chapter still eases {outlook['chapter_end']}."
        )
    else:
        card["now"] = f"{head} Not a live 6th-lord Dasa chapter today.{sky}"
        card["eases"] = ""
    if gochara.get("read") in ("careful", "challenging") and sky:
        card["now"] += f" Sky this month is {gochara.get('read_en')}."


def compute_d6_analysis(natal_chart: dict, *, timing_years: int = 90) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    bd = natal_chart.get("birth_data") or {}
    d1_asc_idx = asc.get("sign_index")
    if d1_asc_idx is None:
        raise ValueError("Chart must include ascendant sign_index.")
    birth_date = bd.get("dob")
    if not birth_date:
        raise ValueError("birth_data.dob required for Ripu timing.")

    d6_asc, d6_pos = build_shashthamsa_from_natal(natal_chart)
    d6_asc_idx = d6_asc["sign_index"]
    d1_sixth_lord = _lord_of(d1_asc_idx, 6)
    d1_eighth_lord = _lord_of(d1_asc_idx, 8)
    d6_lagna_lord = d6_asc["sign_lord"]
    d6_sixth_lord = _lord_of(d6_asc_idx, 6)
    d1_sixth_sign = SIGNS[(int(d1_asc_idx) + 5) % 12]
    d1_eighth_sign = SIGNS[(int(d1_asc_idx) + 7) % 12]
    d6_sixth_sign = SIGNS[(int(d6_asc_idx) + 5) % 12]
    native = {
        "d1_sixth_lord": d1_sixth_lord,
        "d1_sixth_sign": d1_sixth_sign,
        "d1_eighth_lord": d1_eighth_lord,
        "d1_eighth_sign": d1_eighth_sign,
        "d6_lagna": d6_asc["sign"],
        "d6_lagna_lord": d6_lagna_lord,
        "d6_sixth_lord": d6_sixth_lord,
        "d6_sixth_sign": d6_sixth_sign,
        "d6_houses": {
            name: int((d6_pos.get(name) or {}).get("house") or 0)
            for name in (
                "Sun", "Moon", "Mars", "Mercury", "Jupiter",
                "Venus", "Saturn", "Rahu", "Ketu",
            )
        },
    }

    moon_lon = (pp.get("Moon") or {}).get("longitude", 0.0)
    _, cur_d, _, cur_b = find_current_dasha_bhukti(moon_lon, birth_date)
    maha = cur_d["planet"]
    bhukti = cur_b["planet"]

    themes = build_theme_cards(
        d1_positions=pp,
        d1_asc_idx=d1_asc_idx,
        d6_positions=d6_pos,
        d6_asc_idx=d6_asc_idx,
        maha=maha,
        bhukti=bhukti,
    )
    timing = build_ripus_timing(
        moon_lon,
        birth_date,
        d1_sixth_lord=d1_sixth_lord,
        d1_eighth_lord=d1_eighth_lord,
        d6_lagna_lord=d6_lagna_lord,
        d6_sixth_lord=d6_sixth_lord,
        years=timing_years,
        native=native,
    )
    today = today_ist().isoformat()
    current_timing = [p for p in timing if p["start"] <= today <= p["end"]]
    upcoming_timing = [p for p in timing if p["start"] > today][:10]

    present = [c["title"] for c in themes if c["tone"] == "present"]
    meaning_summary = {
        "d6_lagna": d6_asc["sign"],
        "d6_lagna_lord": d6_lagna_lord,
        "d1_sixth_lord": d1_sixth_lord,
        "d1_sixth_sign": d1_sixth_sign,
        "d1_eighth_lord": d1_eighth_lord,
        "d1_eighth_sign": d1_eighth_sign,
        "d6_sixth_lord": d6_sixth_lord,
        "d6_sixth_sign": d6_sixth_sign,
    }
    gochara = build_ripus_gochara(natal_chart, int(d1_asc_idx))
    if current_timing:
        current_timing[0]["sky"] = gochara.get("read")
        current_timing[0]["sky_en"] = gochara.get("line_en") or gochara.get("now_en")
        current_timing[0]["sky_ta"] = gochara.get("line_ta") or gochara.get("now_ta")
        current_timing[0]["sky_read_en"] = gochara.get("read_en")
        current_timing[0]["sky_remedy_en"] = gochara.get("remedy_en")
    outlook = build_karaka_outlook(
        cur_d=cur_d,
        cur_b=cur_b,
        current=current_timing,
        d1_sixth_lord=d1_sixth_lord,
        d1_eighth_lord=d1_eighth_lord,
        d6_lagna_lord=d6_lagna_lord,
        d6_sixth_lord=d6_sixth_lord,
    )
    meaning = build_native_meaning(
        summary=meaning_summary,
        themes=themes,
        current=current_timing,
        upcoming=upcoming_timing,
        gochara=gochara,
    )
    sky_houses = {
        int(h["house"]): h
        for h in (gochara.get("houses") or [])
        if h.get("occupants") or h.get("aspects")
    }
    for card in themes:
        _fill_theme_now(
            card,
            outlook=outlook,
            native=native,
            sky_houses=sky_houses,
            gochara=gochara,
        )

    consult = build_client_summary(
        summary=meaning_summary,
        themes=themes,
        current=current_timing,
        upcoming=upcoming_timing,
        d6_positions=d6_pos,
        d6_asc_idx=d6_asc_idx,
        maha=maha,
        bhukti=bhukti,
        outlook=outlook,
        gochara=gochara,
    )
    if current_timing:
        win = current_timing[0]
        read = win.get("read_en") or "Ripu"
        headline = (
            f"{read}: {win['label']} "
            f"({', '.join(win['links'])})"
        )
    elif present:
        headline = f"D6 flags {', '.join(present[:3])} as present — read D1 beside D6."
    elif upcoming_timing:
        headline = f"Next Ripu window: {upcoming_timing[0]['label']} from {upcoming_timing[0]['start']}"
    else:
        headline = "No 6th/8th Dasa link today. Charts still show the natal Ripu layout."

    return {
        "disclaimer": DISCLAIMER,
        "summary": {
            "d6_lagna": d6_asc["sign"],
            "d6_lagna_lord": d6_lagna_lord,
            "d1_sixth_lord": d1_sixth_lord,
            "d1_eighth_lord": d1_eighth_lord,
            "d6_sixth_lord": d6_sixth_lord,
            "d1_sixth_sign": d1_sixth_sign,
            "d1_eighth_sign": d1_eighth_sign,
            "d6_sixth_sign": d6_sixth_sign,
            "maha_dasa": maha,
            "bhukti": bhukti,
            "dasa_period": (
                f"{cur_b['start'].strftime('%Y-%m-%d')} → {cur_b['end'].strftime('%Y-%m-%d')}"
            ),
        },
        "shashthamsa_ascendant": d6_asc,
        "shashthamsa_positions": d6_pos,
        "themes": themes,
        "current_dasa": {
            "maha_dasa": maha,
            "bukti": bhukti,
            "start": cur_b["start"].strftime("%Y-%m-%d"),
            "end": cur_b["end"].strftime("%Y-%m-%d"),
        },
        "timing": {
            "current": current_timing,
            "upcoming": upcoming_timing,
            "all": timing,
            "guide": READING_GUIDE,
        },
        "hero": {"headline": headline},
        "meaning": meaning,
        "outlook": outlook,
        "gochara": gochara,
        "consult": consult,
        "highlight_d1": [6, 8],
        "highlight_d6": [1, 6, 8],
    }


def d6_context_for_narrator(natal_chart: dict) -> str:
    try:
        data = compute_d6_analysis(natal_chart)
    except Exception:
        return ""
    s = data["summary"]
    lines = [
        "=== Ripu (D1 + D6 Shashthamsa) ===",
        f"DISCLAIMER: {DISCLAIMER}",
        f"D6 Lagna: {s['d6_lagna']} lord {s['d6_lagna_lord']}",
        f"D1 6th lord: {s['d1_sixth_lord']} · D1 8th lord: {s['d1_eighth_lord']} · D6 6th lord: {s['d6_sixth_lord']}",
        f"Dasa: {s['maha_dasa']}–{s['bhukti']} ({s['dasa_period']})",
        "D6 method: odd signs from Aries, even from Libra (Narasimha Rao / JHora). Not D60, not BPHS 16 vargas.",
        "D6 is obstacles (debt, enemies, contests, service, illness-as-fight). "
        "Body map is Health. Profession type is Career. No 0-100 score.",
    ]
    meaning = (data.get("meaning") or {}).get("en")
    if meaning:
        lines.append("For the native: " + meaning)
    outlook = data.get("outlook") or {}
    if outlook.get("now_en"):
        lines.append("Now: " + outlook["now_en"])
    if outlook.get("eases_en"):
        lines.append("Eases: " + outlook["eases_en"])
    consult = (data.get("consult") or {}).get("en")
    if consult:
        lines.append("Say to the client: " + consult)
    if data["hero"].get("headline"):
        lines.append(data["hero"]["headline"])
    for card in data["themes"]:
        lines.append(
            f"• {card['title']} [{card['tone']}]: {card['d1']} {card['d6']} {card['dasa']}"
        )
    current = data["timing"]["current"]
    if current:
        c = current[0]
        lines.append(
            f"Active window: {c.get('read_en', '')} {c['label']} {c['start']} → {c['end']} "
            f"({', '.join(c['links'])}). {c.get('why_en', '')} {c.get('remedy_en', '')}"
        )
    gochara = data.get("gochara") or {}
    if gochara.get("now_en"):
        lines.append(
            f"Gochara this month ({gochara.get('as_of', '')}): "
            f"{gochara.get('read_en', '')}. {gochara['now_en']}"
        )
    return "\n".join(lines)
