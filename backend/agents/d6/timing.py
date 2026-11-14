"""Ripu timing from Vimshottari Dasa/Bhukti (dasha_core)."""

from __future__ import annotations

import datetime

from dasha_core import generate_bhuktis, generate_dashas

NODES = frozenset({"Rahu", "Ketu"})

LINK_SAY = {
    "D1 6th lord": {
        "en": "Dues, opposition, contests, service strain, health-as-a-fight are on.",
        "ta": "கடன், எதிர்ப்பு, போட்டி, சேவை, நோய்-தடை இப்போது உள்ளன.",
        "remedy_en": "Sleep and food regular; settle dues in writing; do not pick a new fight.",
        "remedy_ta": "உறக்கம், உணவு ஒழுங்கு; கடனை எழுத்தில் முடிக்கவும்; புதிய சண்டை எடுக்க வேண்டாம்.",
    },
    "D1 8th lord": {
        "en": "Watch documents, nerves, shocks, a chronic undercurrent.",
        "ta": "ஆவணம், நரம்பு, திடீர், நாள்பட்ட அழுத்தம்.",
        "remedy_en": "Keep copies of papers; no impulsive signatures; a second opinion if something acute appears.",
        "remedy_ta": "ஆவண நகல் வைக்கவும்; அவசர கையொப்பம் வேண்டாம்; திடீரென ஏற்பட்டால் இரண்டாம் கருத்து.",
    },
    "D6 lagna lord": {
        "en": "The struggle is more visible; pride and vitality are in play.",
        "ta": "போராட்டம் வெளிப்படும்; கர்வம், உயிர்சக்தி முன் நிற்கும்.",
        "remedy_en": "Keep the contest documented and public-clean; do not let pride run the fight.",
        "remedy_ta": "போட்டியை ஆவணப்படுத்துங்கள்; கர்வத்தால் முடிவு எடுக்க வேண்டாம்.",
    },
    "D6 6th lord": {
        "en": "Slow, heavy, delay; work through with patience.",
        "ta": "மெது, கனம், தாமதம்; பொறுமையுடன் கடக்கவும்.",
        "remedy_en": "Give time; do not rush a case or a treatment plan. Bones/joints: see Health.",
        "remedy_ta": "நேரம் கொடுங்கள்; வழக்கு அல்லது சிகிச்சையை அவசரப்படுத்த வேண்டாம். எலும்பு/மூட்டு: Health.",
    },
}

NODE_REMEDY = {
    "en": "Node with Ripu: finish what must end; do not start a new war.",
    "ta": "ராகு/கேது ரிபுவுடன்: முடிக்க வேண்டியதை முடிக்கவும்; புதிய போர் தொடங்க வேண்டாம்.",
}

D6_HOUSE_SAY_EN = {
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
D6_HOUSE_SAY_TA = {
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

PLANET_CONDUCT = {
    "Sun": (
        "Keep the contest public-clean; do not let pride decide.",
        "போட்டியை வெளிப்படையாக வைக்கவும்; கர்வத்தால் முடிவு வேண்டாம்.",
    ),
    "Moon": (
        "Sleep and food regular; settle dues in writing.",
        "உறக்கம், உணவு ஒழுங்கு; கடனை எழுத்தில் முடிக்கவும்.",
    ),
    "Mars": (
        "Do not pick a new fight; keep dispute papers dated.",
        "புதிய சண்டை எடுக்க வேண்டாம்; தகராறு ஆவணம் தேதியுடன்.",
    ),
    "Mercury": (
        "Keep copies of papers; no impulsive signatures.",
        "ஆவண நகல் வைக்கவும்; அவசர கையொப்பம் வேண்டாம்.",
    ),
    "Jupiter": (
        "Ask counsel before a settlement; follow the right procedure.",
        "தீர்வுக்கு முன் ஆலோசனை; முறைப்படி நடத்துங்கள்.",
    ),
    "Venus": (
        "Do not buy peace with a rushed agreement.",
        "அவசர ஒப்பந்தத்தால் அமைதி வாங்க வேண்டாம்.",
    ),
    "Saturn": (
        "Give time; do not rush a case or a treatment plan.",
        "நேரம் கொடுங்கள்; வழக்கு அல்லது சிகிச்சையை அவசரப்படுத்த வேண்டாம்.",
    ),
    "Rahu": (
        "Finish unusual unfinished business; do not start a new war.",
        "முடியாத வினோத காரியத்தை முடிக்கவும்; புதிய போர் வேண்டாம்.",
    ),
    "Ketu": (
        "Finish what must end; do not start a new war.",
        "முடிக்க வேண்டியதை முடிக்கவும்; புதிய போர் தொடங்க வேண்டாம்.",
    ),
}

LINK_NATIVE_KEY = {
    "D1 6th lord": ("d1_sixth_lord", "d1_sixth_sign"),
    "D1 8th lord": ("d1_eighth_lord", "d1_eighth_sign"),
    "D6 lagna lord": ("d6_lagna_lord", "d6_lagna"),
    "D6 6th lord": ("d6_sixth_lord", "d6_sixth_sign"),
}

READING_GUIDE = {
    "intro_en": (
        "Being on this list does not mean bad years. It means a Ripu switch is on: "
        "a 6th/8th or D6-fight lord is running. Read Links, then how many links, then who."
    ),
    "intro_ta": (
        "இப்பட்டியலில் இருப்பது கெட்ட ஆண்டு அல்ல. 6/8 அல்லது D6 போர் அதிபதி ஓடுகிறது. "
        "முதலில் Links, பிறகு எத்தனை இணைப்பு, பிறகு யார்."
    ),
    "links": [
        {
            "id": "D1 6th lord",
            "en": "The obstacle field itself — dues, opposition, contests, service, health-as-a-fight.",
            "ta": "தடை வெளி — கடன், எதிர்ப்பு, போட்டி, சேவை, நோய்-தடை.",
        },
        {
            "id": "D1 8th lord",
            "en": "Sudden / hidden / paperwork — documents, nerves, shocks.",
            "ta": "திடீர் / மறைந்த / ஆவணம் — நரம்பு, அதிர்ச்சி.",
        },
        {
            "id": "D6 lagna lord",
            "en": "How you meet the fight — more visible; pride and vitality.",
            "ta": "போரை எதிர்கொள்ளும் பாணி — வெளிப்படும்; கர்வம், உயிர்சக்தி.",
        },
        {
            "id": "D6 6th lord",
            "en": "The obstacle in D6 — slow, delay, patience.",
            "ta": "D6 தடை — மெது, தாமதம், பொறுமை.",
        },
    ],
    "tones": [
        {
            "id": "watch",
            "label_en": "Watch",
            "label_ta": "கவனிப்பு",
            "en": "One link. Live normally; stay awake to that house.",
            "ta": "ஒரு இணைப்பு. வாழ்க்கை நடத்தலாம்; அந்த வீட்டைக் கவனிக்கவும்.",
        },
        {
            "id": "careful",
            "label_en": "Careful",
            "label_ta": "கவனம்",
            "en": "Two links, or the D6 6th lord. Same life; slower decisions, papers and health checks.",
            "ta": "இரண்டு இணைப்பு, அல்லது D6 6ம் அதிபதி. மெது முடிவு, ஆவணம், உடல் பரிசோதனை.",
        },
        {
            "id": "challenging",
            "label_en": "Challenging",
            "label_ta": "கடினம்",
            "en": "D6 lagna lord and D6 6th lord together, or two links with a node. Still not a curse — extra care.",
            "ta": "D6 லக்ன அதிபதியும் D6 6ம் அதிபதியும், அல்லது கிரகணத்துடன் இரண்டு இணைப்பு. சாபம் அல்ல — கூடுதல் கவனம்.",
        },
    ],
    "remedy_note_en": (
        "Remedy here is conduct, not a gem. Body areas stay on Health. "
        "Gochara (this month) is counted from YOUR lagna into houses 1, 6 and 8 — "
        "same sky, different houses for each native."
    ),
    "remedy_note_ta": (
        "பரிகாரம் நடத்தை; ரத்தினம் அல்ல. உடல் பகுதிகள் Health தாவலில். "
        "கோசாரம் உங்கள் லக்னத்திலிருந்து 1, 6, 8 — அதே வானம், ஒவ்வொருவருக்கும் வேறு வீடு."
    ),
}


def _nth(house: int) -> str:
    house = int(house or 0)
    if house in (11, 12):
        return f"{house}th"
    if house % 10 == 1:
        return f"{house}st"
    if house % 10 == 2:
        return f"{house}nd"
    if house % 10 == 3:
        return f"{house}rd"
    return f"{house}th"


def _native_voice(row: dict, native: dict, links: list[str]) -> tuple[str, str, str, str, str, str]:
    """Why / say / remedy named for THIS native's lords, signs, and D6 houses."""
    maha = row.get("maha_dasa") or ""
    bhukti = row.get("bukti") or ""
    d6_houses = native.get("d6_houses") or {}
    named = []
    named_ta = []
    say = []
    say_ta = []
    remedies = []
    remedies_ta = []
    for link in links:
        keys = LINK_NATIVE_KEY.get(link)
        if not keys:
            continue
        lord_key, sign_key = keys
        lord = native.get(lord_key) or ""
        sign = native.get(sign_key) or ""
        who = maha if maha == lord else (bhukti if bhukti == lord else lord)
        named.append(f"{who} is your {link}" + (f" of {sign}" if sign else ""))
        named_ta.append(f"{who} உங்கள் {link}" + (f" ({sign})" if sign else ""))
        house = int(d6_houses.get(who) or 0)
        house_bit = ""
        house_bit_ta = ""
        if house:
            house_bit = (
                f" In D6, {who} sits in the {_nth(house)} — "
                f"{D6_HOUSE_SAY_EN.get(house, 'this house')}."
            )
            house_bit_ta = (
                f" D6 {house}ம் வீட்டில் {who} — {D6_HOUSE_SAY_TA.get(house, '')}."
            )
        say.append(
            (LINK_SAY.get(link) or {}).get("en", "") + house_bit
        )
        say_ta.append(
            (LINK_SAY.get(link) or {}).get("ta", "") + house_bit_ta
        )
        conduct = PLANET_CONDUCT.get(who)
        if conduct:
            remedies.append(conduct[0])
            remedies_ta.append(conduct[1])
        else:
            remedies.append((LINK_SAY.get(link) or {}).get("remedy_en", ""))
            remedies_ta.append((LINK_SAY.get(link) or {}).get("remedy_ta", ""))
    if maha in NODES or bhukti in NODES:
        remedies.append(NODE_REMEDY["en"])
        remedies_ta.append(NODE_REMEDY["ta"])
    why_en = "; ".join(named) + "." if named else ""
    why_ta = "; ".join(named_ta) + "." if named_ta else ""
    return (
        why_en,
        why_ta,
        " ".join(s for s in say if s).strip(),
        " ".join(s for s in say_ta if s).strip(),
        " ".join(dict.fromkeys(r for r in remedies if r)),
        " ".join(dict.fromkeys(r for r in remedies_ta if r)),
    )


def classify_ripus_window(row: dict, native: dict | None = None) -> dict:
    """Watch / Careful / Challenging from Links — qualitative, no score.

    When `native` is passed, why / say / remedy name this chart's lords,
    signs, and D6 houses so two natives never share a canned script.
    """
    links = list(row.get("links") or [])
    linkset = set(links)
    n = len(linkset)
    maha = row.get("maha_dasa") or ""
    bhukti = row.get("bukti") or ""
    node = maha in NODES or bhukti in NODES
    d6_both = "D6 lagna lord" in linkset and "D6 6th lord" in linkset
    sixth_eighth = "D1 6th lord" in linkset and "D1 8th lord" in linkset

    if d6_both or (n >= 2 and node):
        tone = "challenging"
        tone_en = "Challenging"
        tone_ta = "கடினம்"
        why_en = "D6 fight-style and D6 obstacle together" if d6_both else "Two Ripu links with a node"
        why_ta = "D6 பாணியும் D6 தடையும் சேர்ந்தன" if d6_both else "இரண்டு ரிபு இணைப்புகளுடன் கிரகணம்"
    elif n >= 2 or "D6 6th lord" in linkset or sixth_eighth:
        tone = "careful"
        tone_en = "Careful"
        tone_ta = "கவனம்"
        why_en = "Two Ripu links, or the D6 6th lord (delay)."
        why_ta = "இரண்டு ரிபு இணைப்பு, அல்லது D6 6ம் அதிபதி (தாமதம்)."
    else:
        tone = "watch"
        tone_en = "Watch"
        tone_ta = "கவனிப்பு"
        why_en = "One Ripu link. Live normally; stay awake to that house."
        why_ta = "ஒரு ரிபு இணைப்பு. வாழ்க்கை நடத்தலாம்; அந்த வீட்டைக் கவனிக்கவும்."

    say_en = " ".join(LINK_SAY[k]["en"] for k in links if k in LINK_SAY)
    say_ta = " ".join(LINK_SAY[k]["ta"] for k in links if k in LINK_SAY)
    remedies = [LINK_SAY[k]["remedy_en"] for k in links if k in LINK_SAY]
    remedies_ta = [LINK_SAY[k]["remedy_ta"] for k in links if k in LINK_SAY]
    if node:
        remedies.append(NODE_REMEDY["en"])
        remedies_ta.append(NODE_REMEDY["ta"])

    if native:
        n_why, n_why_ta, n_say, n_say_ta, n_rem, n_rem_ta = _native_voice(row, native, links)
        if n_why:
            why_en = n_why + " " + why_en
            why_ta = n_why_ta + " " + why_ta
        if n_say:
            say_en, say_ta = n_say, n_say_ta
        if n_rem:
            remedies, remedies_ta = [n_rem], [n_rem_ta]

    row = dict(row)
    row.update({
        "read": tone,
        "read_en": tone_en,
        "read_ta": tone_ta,
        "why_en": why_en,
        "why_ta": why_ta,
        "say_en": say_en,
        "say_ta": say_ta,
        "remedy_en": " ".join(dict.fromkeys(r for r in remedies if r)),
        "remedy_ta": " ".join(dict.fromkeys(r for r in remedies_ta if r)),
    })
    return row


def build_ripus_timing(
    moon_longitude: float,
    birth_date: str,
    *,
    d1_sixth_lord: str,
    d1_eighth_lord: str,
    d6_lagna_lord: str,
    d6_sixth_lord: str,
    years: int = 90,
    native: dict | None = None,
) -> list[dict]:
    """MD/AD windows linked to D1 6th/8th lords and D6 lagna/6th lords."""
    birth_dt = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
    cutoff = birth_dt + datetime.timedelta(days=years * 365.25)
    keys = {d1_sixth_lord, d1_eighth_lord, d6_lagna_lord, d6_sixth_lord} - {""}
    periods: list[dict] = []

    for dasa in generate_dashas(moon_longitude, birth_date):
        if dasa["start"] >= cutoff:
            break
        maha = dasa["planet"]
        for b in generate_bhuktis(dasa):
            if b["end"] <= birth_dt or b["start"] >= cutoff:
                continue
            bukti = b["planet"]
            if maha not in keys and bukti not in keys:
                continue
            links = []
            if maha == d1_sixth_lord or bukti == d1_sixth_lord:
                links.append("D1 6th lord")
            if maha == d1_eighth_lord or bukti == d1_eighth_lord:
                links.append("D1 8th lord")
            if maha == d6_lagna_lord or bukti == d6_lagna_lord:
                links.append("D6 lagna lord")
            if maha == d6_sixth_lord or bukti == d6_sixth_lord:
                links.append("D6 6th lord")
            periods.append(classify_ripus_window({
                "maha_dasa": maha,
                "bukti": bukti,
                "start": b["start"].strftime("%Y-%m-%d"),
                "end": b["end"].strftime("%Y-%m-%d"),
                "links": links,
                "label": f"{maha}–{bukti}",
            }, native=native))
    return periods
