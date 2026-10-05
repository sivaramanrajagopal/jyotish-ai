"""
nadi_agent.py — Bhrigu Nandi Nadi style reading for twelve life questions.

The story starts from a karaka planet's sign, not from a house number.
Same sign means together. The other two signs of the same fire, earth, air,
or water family tell the same story. The sign behind is already in motion.
The next sign is what follows. The seventh sign is the person or matter
opposite. Jupiter and Saturn open the season. Rahu and Ketu only sharpen it.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import ephemeris as swe
from ephemeris import RAHU_NODE

from agents.natal_agent import SIGNS, _to_jd

TZ = ZoneInfo("Asia/Kolkata")
SCAN_YEARS = 22
SEASON_GAP_DAYS = 400
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

PLANET_ORDER = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]
SLOW = ("Jupiter", "Saturn")
NODES = ("Rahu", "Ketu")

ELEMENTS = {
    0: "fire", 4: "fire", 8: "fire",
    1: "earth", 5: "earth", 9: "earth",
    2: "air", 6: "air", 10: "air",
    3: "water", 7: "water", 11: "water",
}
ELEMENT_SIGNS = {
    "fire": (0, 4, 8),
    "earth": (1, 5, 9),
    "air": (2, 6, 10),
    "water": (3, 7, 11),
}

METHOD = (
    "Each question starts from one planet's sign. Already is the sign behind that planet. "
    "Happening is the sign they sit in, together with the other two signs of the same "
    "fire, earth, air, or water family. Follows is the next sign. "
    "Jupiter or Saturn opens the season when one of them stands on the happening sign "
    "or the sign that follows. Rahu and Ketu only sharpen that season. "
    "Vimshottari dasha stays on My Chart."
)
VIEW = (
    "This explains who the story starts from, who sits with them, and which season "
    "can bring it forward. It does not name a job, and it does not pick a single day."
)

# helpers are named only when they are absent from the chain.
QUESTIONS = (
    {"id": "self", "label": "Self", "karaka": "Jupiter", "helpers": (),
     "intro": "Self starts from Jupiter."},
    {"id": "money", "label": "Money", "karaka": "Venus", "helpers": (),
     "intro": "Money starts from Venus.", "extra": "jupiter_second"},
    {"id": "skill", "label": "Skill", "karaka": "Mars", "helpers": ("Mercury",),
     "intro": "Skill and courage start from Mars."},
    {"id": "home", "label": "Home", "karaka": "Moon", "helpers": ("Venus", "Mars"),
     "intro": "Home and the mother start from the Moon."},
    {"id": "children", "label": "Children", "karaka": "Jupiter", "helpers": ("Mercury",),
     "intro": "Children and learning start from Jupiter."},
    {"id": "health", "label": "Health", "karaka": "Saturn", "helpers": ("Mars", "Rahu"),
     "intro": "Disease, debt, and disputes start from Saturn."},
    {"id": "marriage", "label": "Marriage", "karaka": "spouse", "helpers": ("Jupiter", "Saturn")},
    {"id": "breaks", "label": "Breaks", "karaka": "Ketu", "helpers": ("Saturn",),
     "intro": "Breaks and research start from Ketu."},
    {"id": "father", "label": "Father", "karaka": "Sun", "helpers": ("Jupiter",),
     "intro": "Father and fortune start from the Sun."},
    {"id": "work", "label": "Work", "karaka": "Saturn", "helpers": ("Mercury", "Mars", "Sun"),
     "intro": "Work starts from Saturn."},
    {"id": "gains", "label": "Gains", "karaka": "Jupiter", "helpers": ("Venus",),
     "intro": "Gains start from Jupiter."},
    {"id": "foreign", "label": "Foreign", "karaka": "Rahu", "helpers": ("Moon",),
     "intro": "Foreign starts from Rahu."},
)

_CALENDAR_CACHE: dict[str, dict] = {}
_SKY_CACHE: dict[str, dict[str, int]] = {}


def _shift(sign: int, steps: int) -> int:
    return (sign + steps) % 12


def _plain(name: str) -> str:
    if name == "Sun":
        return "the Sun"
    if name == "Moon":
        return "the Moon"
    return name


def _phrase(planet: dict) -> str:
    name = _plain(planet["planet"])
    if not planet["retrograde"]:
        return name
    if name.startswith("the "):
        return "the retrograde " + name[4:]
    return "retrograde " + name


def _join(planets: list[dict]) -> str:
    parts = [_phrase(p) for p in planets]
    if len(parts) <= 1:
        return parts[0] if parts else ""
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _join_words(words: list[str]) -> str:
    if len(words) <= 1:
        return words[0] if words else ""
    return ", ".join(words[:-1]) + " and " + words[-1]


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _fmt(day: date) -> str:
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _placements(chart: dict) -> list[dict]:
    positions = chart.get("planet_positions") or {}
    rows = []
    for name in PLANET_ORDER:
        row = positions.get(name)
        if not row or not row.get("sign"):
            raise ValueError("Chart is missing planet positions.")
        sign_name = row["sign"]
        if sign_name not in SIGNS:
            raise ValueError("Chart is missing planet positions.")
        rows.append({
            "planet": name,
            "sign": SIGNS.index(sign_name),
            "retrograde": bool(row.get("retrograde")),
        })
    return rows


def _by_sign(planets: list[dict]) -> dict[int, list[dict]]:
    grouped = {i: [] for i in range(12)}
    for planet in planets:
        grouped[planet["sign"]].append(planet)
    return grouped


def _box(sign: int, planets: list[dict]) -> dict:
    return {
        "sign": SIGNS[sign],
        "planets": [_phrase(p) for p in planets],
        "label": _join(planets) if planets else "empty",
    }


def _chain(karaka_name: str, planets: list[dict], grouped: dict[int, list[dict]]) -> dict:
    karaka = next(p for p in planets if p["planet"] == karaka_name)
    sign = karaka["sign"]
    element = ELEMENTS[sign]
    trine = tuple(s for s in ELEMENT_SIGNS[element] if s != sign)
    past = _shift(sign, -1)
    follows = _shift(sign, 1)
    opposite = _shift(sign, 6)
    companions = [p for p in grouped[sign] if p["planet"] != karaka_name]
    linked = {sign, past, follows, opposite, *trine}
    return {
        "karaka": karaka,
        "sign": sign,
        "element": element,
        "trine": trine,
        "past": past,
        "follows": follows,
        "opposite": opposite,
        "companions": companions,
        "linked": linked,
        "grouped": grouped,
    }


def _sign_label(grouped: dict[int, list[dict]], sign: int, karaka: str | None = None) -> str:
    people = grouped[sign]
    if not people:
        return "empty"
    parts = []
    for planet in people:
        text = _phrase(planet)
        if karaka and planet["planet"] == karaka:
            text += " (significator)"
        parts.append(text)
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _planet_bits(people: list[dict], karaka: str | None) -> list[dict]:
    bits = []
    for planet in people:
        bits.append({
            "name": _phrase(planet),
            "significator": planet["planet"] == karaka,
        })
    return bits


def _board(grouped: dict[int, list[dict]], chain: dict, extra_signs: set[int]) -> list[dict]:
    roles = {
        chain["sign"]: "happening",
        chain["past"]: "behind",
        chain["follows"]: "follows",
        chain["opposite"]: "opposite",
    }
    for sign in chain["trine"]:
        roles.setdefault(sign, "family")
    for sign in extra_signs:
        roles.setdefault(sign, "after Jupiter")
    karaka = chain["karaka"]["planet"]
    board = []
    for element, signs in ELEMENT_SIGNS.items():
        available = []
        cells = []
        for sign in signs:
            people = grouped[sign]
            bits = _planet_bits(people, karaka)
            available.extend(bit["name"] for bit in bits)
            cells.append({
                "sign": SIGNS[sign],
                "label": _sign_label(grouped, sign),
                "planets": bits,
                "role": roles.get(sign),
            })
        board.append({
            "name": element,
            "signs_line": ", ".join(SIGNS[sign] for sign in signs),
            "available": ", ".join(available) if available else "none",
            "signs": cells,
        })
    return board


def _reason_row(place: str, sign: str, planets: str, reason: str) -> dict:
    return {"place": place, "sign": sign, "planets": planets, "reason": reason}


def _reasons(chain: dict, absent: list[str], extra: str, extra_signs: set[int]) -> list[dict]:
    grouped = chain["grouped"]
    element = chain["element"]
    karaka = _plain(chain["karaka"]["planet"])
    sign = SIGNS[chain["sign"]]
    happening = f"This question starts from {karaka} in {sign}."
    if chain["companions"]:
        phrase = _join(chain["companions"])
        verb = "sit" if " and " in phrase else "sits"
        happening += f" {_cap(phrase)} {verb} with {karaka}."
    happening_planets = _sign_label(grouped, chain["sign"], chain["karaka"]["planet"])
    rows = [_reason_row("Happening", sign, happening_planets, happening)]
    for trine in chain["trine"]:
        people = grouped[trine]
        if people:
            reason = f"Same {element} family, so this is the same story."
        else:
            reason = f"Same {element} family. Empty, and it stays empty."
        rows.append(_reason_row("Family", SIGNS[trine], _sign_label(grouped, trine), reason))
    behind = grouped[chain["past"]]
    rows.append(_reason_row(
        "Already",
        SIGNS[chain["past"]],
        _sign_label(grouped, chain["past"]),
        "The sign behind. This part is already in motion." if behind else "The sign behind. Empty, so nothing is already waiting there.",
    ))
    follows = grouped[chain["follows"]]
    rows.append(_reason_row(
        "Follows",
        SIGNS[chain["follows"]],
        _sign_label(grouped, chain["follows"]),
        "The next sign. This is what follows." if follows else "The next sign. Empty, and it stays empty.",
    ))
    opposite = grouped[chain["opposite"]]
    rows.append(_reason_row(
        "Opposite",
        SIGNS[chain["opposite"]],
        _sign_label(grouped, chain["opposite"]),
        "The seventh sign. This is the person or matter opposite." if opposite else "The seventh sign. Empty, so no one stands opposite.",
    ))
    wealth = extra or "This is also the sign after Jupiter, the other wealth link."
    explained = {chain["sign"], chain["past"], chain["follows"], chain["opposite"], *chain["trine"]}
    for sign in sorted(extra_signs):
        if sign in explained:
            for row in rows:
                if row["sign"] == SIGNS[sign] and wealth not in row["reason"]:
                    row["reason"] = f"{row['reason']} {wealth}"
            continue
        rows.append(_reason_row("After Jupiter", SIGNS[sign], _sign_label(grouped, sign), wealth))
    for name in absent:
        rows.append(_reason_row("Outside", "—", _plain(name), f"{_cap(_plain(name))} is not sitting in this chain."))
    return rows


def _timing_row(season: dict, kind: str) -> dict:
    signs = []
    for item in season["passes"]:
        if item["sign"] not in signs:
            signs.append(item["sign"])
    start = date.fromisoformat(season["start"])
    end = date.fromisoformat(season["end"])
    return {
        "planet": season["planet"],
        "kind": kind,
        "from": _fmt(start),
        "to": _fmt(end),
        "when": f"{_fmt(start)} – {_fmt(end)}",
        "signs": ", ".join(signs),
    }


def _season_status(when: date, seasons: list[dict]) -> str:
    today = when.isoformat()
    open_rows = [row for row in seasons if row["start"] <= today <= row["end"]]
    if open_rows:
        return "This season is open. " + " ".join(f"{row['label']}." for row in open_rows)
    upcoming = sorted((row for row in seasons if row["start"] > today), key=lambda row: row["start"])
    if upcoming:
        return f"This season is not open today. The next one is {upcoming[0]['label']}."
    if seasons:
        return "This season is not open today."
    return "No Jupiter or Saturn season falls on these signs in the next 22 years."


def _family_line(chain: dict) -> str:
    parts = []
    for sign in (chain["sign"], *chain["trine"]):
        people = chain["grouped"][sign]
        label = _join(people) if people else "empty"
        parts.append(f"{SIGNS[sign]}: {label}")
    return " · ".join(parts)


def _family_sentence(chain: dict) -> str:
    occupied = []
    empty = []
    for sign in chain["trine"]:
        people = chain["grouped"][sign]
        if people:
            occupied.append(_sit(people, SIGNS[sign]))
        else:
            empty.append(SIGNS[sign])
    element = chain["element"]
    if occupied and empty:
        return (
            f"{_cap(' and '.join(occupied))}, the same {element} family. "
            f"{_join_words(empty)} {'is' if len(empty) == 1 else 'are'} empty."
        )
    if occupied:
        return f"{_cap(' and '.join(occupied))}, the same {element} family."
    return (
        f"{_join_words(empty)} {'is' if len(empty) == 1 else 'are'} empty, "
        f"so no one else joins from the {element} family."
    )


def _sit(planets: list[dict], sign: str) -> str:
    phrase = _join(planets)
    verb = "sit" if " and " in phrase else "sits"
    return f"{phrase} {verb} in {sign}"


def _place(planets: list[dict], sign: str, role: str) -> str:
    if not planets:
        return f"No planet sits in {sign}, {role}."
    return f"{_cap(_sit(planets, sign))}, {role}."


def _now_sentence(chain: dict) -> str:
    name = _cap(_phrase(chain["karaka"]))
    sign = SIGNS[chain["sign"]]
    if chain["companions"]:
        return f"{name} sits with {_join(chain['companions'])} in {sign}."
    return f"{name} sits alone in {sign}."


def _absent_sentence(names: list[str]) -> str:
    phrases = [_plain(name) for name in names]
    if len(phrases) == 1:
        return f"{_cap(phrases[0])} is not in this chain."
    return f"{_cap(_join_words(phrases))} are not in this chain."


def _money_extra(chain: dict, grouped: dict[int, list[dict]], planets: list[dict]) -> tuple[str, set[int]]:
    jupiter = next(p["sign"] for p in planets if p["planet"] == "Jupiter")
    second = _shift(jupiter, 1)
    sign = SIGNS[second]
    people = grouped[second]
    if second == chain["follows"]:
        line = f"The sign after Jupiter is {sign}, the same sign that follows {_plain(chain['karaka']['planet'])}."
    elif people:
        line = f"The sign after Jupiter is {sign}, with {_join(people)}."
    else:
        line = f"The sign after Jupiter is {sign}, and it is empty."
    return line, {second}


def _analysis(intro: str, chain: dict, absent: list[str], extra: str) -> str:
    parts = [
        intro,
        _now_sentence(chain),
        _family_sentence(chain),
        _place(chain["grouped"][chain["past"]], SIGNS[chain["past"]], "the sign behind"),
        _place(chain["grouped"][chain["follows"]], SIGNS[chain["follows"]], "the sign that follows"),
        _place(chain["grouped"][chain["opposite"]], SIGNS[chain["opposite"]], "the sign opposite"),
    ]
    if extra:
        parts.append(extra)
    if absent:
        parts.append(_absent_sentence(absent))
    if chain["karaka"]["retrograde"]:
        parts.append(
            f"Because {_plain(chain['karaka']['planet'])} is retrograde, "
            "this story looks back, repeats, or arrives late."
        )
    return " ".join(parts)


def _role(sign: int, chain: dict, timing: set[int]) -> str | None:
    if sign in timing:
        return "a sign of this story"
    if sign == chain["past"]:
        return "the sign behind this story"
    if sign == chain["opposite"]:
        return "the sign opposite this story"
    if sign in chain["trine"]:
        return "the same family as this story"
    return None


def _today_line(today: dict[str, int], chain: dict, timing: set[int]) -> str:
    notes = []
    for name in (*SLOW, *NODES):
        sign = today[name]
        role = _role(sign, chain, timing)
        if not role:
            continue
        if name in NODES:
            notes.append(f"{name} is in {SIGNS[sign]}, a sharper pass on {role}.")
        else:
            notes.append(f"{name} is in {SIGNS[sign]}, {role}.")
    if not notes:
        return (
            f"Today Jupiter is in {SIGNS[today['Jupiter']]} and Saturn is in {SIGNS[today['Saturn']]}. "
            "Neither stands on this story."
        )
    return "Today " + " ".join(notes)


def _sky(day: date) -> dict[str, int]:
    key = day.isoformat()
    cached = _SKY_CACHE.get(key)
    if cached:
        return cached
    moment = datetime(day.year, day.month, day.day, 12, 0, tzinfo=TZ)
    jd = _to_jd(moment)
    flags = swe.FLG_SIDEREAL
    out = {}
    for name, planet_id in (("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN), ("Rahu", RAHU_NODE)):
        xx, _ = swe.calc_ut(jd, planet_id, flags)
        out[name] = int((xx[0] % 360) / 30) % 12
    out["Ketu"] = _shift(out["Rahu"], 6)
    _SKY_CACHE[key] = out
    return out


def _today_signs(day: date) -> dict[str, int]:
    return _sky(day)


def _entry(day: date, sign: int, name: str) -> date:
    cursor = day
    floor = day - timedelta(days=1200)
    while cursor > floor:
        previous = cursor - timedelta(days=1)
        if _sky(previous)[name] != sign:
            return cursor
        cursor = previous
    return cursor


def _intervals_for(start: date, name: str, samples: list[tuple[date, int]]) -> list[tuple[int, date, date]]:
    if not samples:
        return []
    sign, began, ended = samples[0][1], samples[0][0], samples[0][0]
    rows = []
    for day, current in samples[1:]:
        if current != sign:
            rows.append((sign, began, ended))
            sign, began = current, day
        ended = day
    rows.append((sign, began, ended))
    first_sign, first_start, first_end = rows[0]
    if first_start == start:
        rows[0] = (first_sign, _entry(start, first_sign, name), first_end)
    return rows


def _calendar(start: date) -> dict[str, list[tuple[int, date, date]]]:
    key = start.isoformat()
    cached = _CALENDAR_CACHE.get(key)
    if cached:
        return cached
    end = start + timedelta(days=SCAN_YEARS * 365)
    samples = {name: [] for name in (*SLOW, *NODES)}
    day = start
    while day <= end:
        sky = _sky(day)
        for name in samples:
            samples[name].append((day, sky[name]))
        day += timedelta(days=1)
    built = {name: _intervals_for(start, name, rows) for name, rows in samples.items()}
    _CALENDAR_CACHE[key] = built
    return built


def _seasons(intervals: list[tuple[int, date, date]], targets: set[int], limit: int) -> list[dict]:
    hits = [row for row in intervals if row[0] in targets]
    if not hits:
        return []
    groups = [[hits[0]]]
    for row in hits[1:]:
        gap = (row[1] - groups[-1][-1][2]).days
        if gap <= SEASON_GAP_DAYS:
            groups[-1].append(row)
        else:
            groups.append([row])
    seasons = []
    for group in groups[:limit]:
        start = group[0][1]
        end = group[-1][2]
        seasons.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "label": f"{_fmt(start)} – {_fmt(end)}",
            "passes": [
                {
                    "sign": SIGNS[sign],
                    "label": f"{SIGNS[sign]} · {_fmt(began)} – {_fmt(finished)}",
                }
                for sign, began, finished in group
            ],
        })
    return seasons


def _gender(chart: dict) -> str:
    raw = str((chart.get("birth_data") or {}).get("gender") or "male").lower()
    return raw if raw in ("male", "female") else "male"


def _question_spec(spec: dict, gender: str) -> dict:
    if spec["id"] != "marriage":
        return spec
    if gender == "female":
        intro = "This is a female chart, so marriage starts from Mars."
        karaka = "Mars"
    else:
        intro = "This is a male chart, so marriage starts from Venus."
        karaka = "Venus"
    return {**spec, "karaka": karaka, "intro": intro}


def compute_nadi(chart: dict, as_of: date | None = None) -> dict:
    """Twelve Nadi readings for one natal chart, timed from as_of (Kolkata today)."""
    planets = _placements(chart)
    grouped = _by_sign(planets)
    when = as_of or datetime.now(TZ).date()
    gender = _gender(chart)
    today = _today_signs(when)
    calendar = _calendar(when)
    readings = []
    for spec in QUESTIONS:
        item = _question_spec(spec, gender)
        chain = _chain(item["karaka"], planets, grouped)
        extra = ""
        extra_signs: set[int] = set()
        timing = {chain["sign"], chain["follows"]}
        if item.get("extra") == "jupiter_second":
            extra, extra_signs = _money_extra(chain, grouped, planets)
            timing |= extra_signs
        absent = [
            name for name in item["helpers"]
            if name != item["karaka"]
            and next(p["sign"] for p in planets if p["planet"] == name) not in chain["linked"]
        ]
        slow = []
        for name in SLOW:
            found = _seasons(calendar[name], timing, limit=2)
            for season in found:
                slow.append({"planet": name, **season, "label": f"{name} · {season['label']}"})
        sharper = []
        for name in NODES:
            found = _seasons(calendar[name], timing, limit=1)
            for season in found:
                sharper.append({"planet": name, **season, "label": f"{name} · {season['label']}"})
        readings.append({
            "id": item["id"],
            "label": item["label"],
            "karaka": item["karaka"],
            "significator": item["karaka"],
            "family": {"name": chain["element"], "line": _family_line(chain)},
            "past": _box(chain["past"], grouped[chain["past"]]),
            "now": _box(chain["sign"], grouped[chain["sign"]]),
            "follows": _box(chain["follows"], grouped[chain["follows"]]),
            "opposite": _box(chain["opposite"], grouped[chain["opposite"]]),
            "analysis": _analysis(item["intro"], chain, absent, extra),
            "today": _today_line(today, chain, timing),
            "season_status": _season_status(when, slow),
            "board": _board(grouped, chain, extra_signs),
            "reasons": _reasons(chain, absent, extra, extra_signs),
            "timing": [_timing_row(row, "Season") for row in slow] + [_timing_row(row, "Sharper") for row in sharper],
            "seasons": slow,
            "sharper": sharper,
        })
    return {
        "method": METHOD,
        "view": VIEW,
        "as_of": when.isoformat(),
        "gender": gender,
        "readings": readings,
    }
