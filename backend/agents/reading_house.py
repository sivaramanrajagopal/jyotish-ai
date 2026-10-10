"""How a question's house gives its result, in the birth chart and in Navamsa.

The season still says when. These lines say whether the house can give the result.
No second score. Dignity is the same classifier Avastha uses.
"""

from __future__ import annotations

from agents.avastha_agent import classify_sign_dignity
from agents.bhavat_bhavam.core import lord_of_house
from agents.dosha_radar.pushkara import pushkara_seat
from agents.house_connections.core import analyze_house

QUESTION_HOUSE = {
    "self": 1,
    "money": 2,
    "skill": 3,
    "home": 4,
    "children": 5,
    "health": 6,
    "marriage": 7,
    "breaks": 8,
    "father": 9,
    "work": 10,
    "gains": 11,
    "foreign": 12,
}

# The Navamsa chart itself is read for self, marriage, and fortune (the 9th).
NAVAMSA_CHART_HOUSES = frozenset({1, 7, 9})

_STRONG = frozenset({"Exalted", "Moolatrikona", "Own", "Friendly"})
_THIN = frozenset({"Inimical", "Debilitated"})


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _dignity_place(state: str, sign: str) -> str:
    if state == "Exalted":
        return f"exalted in {sign}"
    if state == "Debilitated":
        return f"debilitated in {sign}"
    if state == "Own":
        return f"in {sign}, own sign"
    if state == "Moolatrikona":
        return f"in {sign}, moolatrikona"
    if state == "Friendly":
        return f"in {sign}, a friendly sign"
    if state == "Inimical":
        return f"in {sign}, an enemy sign"
    return f"in {sign}, a neutral sign"


def _fruit(dignity: str, vargottama: bool) -> str:
    if vargottama or dignity in ("Exalted", "Moolatrikona", "Own"):
        return "The fruit holds."
    if dignity == "Friendly":
        return "The fruit is available."
    if dignity == "Inimical":
        return "The fruit is thinner."
    if dignity == "Debilitated":
        return "The fruit is weak."
    return "The fruit is ordinary."


def _placement(lord: str, sign: str, dignity: str, lord_house: int, house: int, hfo: int, retrograde: bool) -> str:
    retro = "retrograde, " if retrograde else ""
    place = _dignity_place(dignity, sign)
    if lord_house == house:
        return f"The {_ordinal(house)} lord is {lord}, {retro}{place}, sitting in this house."
    if house == 1:
        return f"The 1st lord is {lord}, {retro}{place}, the {_ordinal(lord_house)}."
    return (
        f"The {_ordinal(house)} lord is {lord}, {retro}{place}, "
        f"the {_ordinal(lord_house)} from the lagna and the {_ordinal(hfo)} from this house."
    )


def _support(lord: str, house: int, row: dict) -> str:
    occupants = [name for name in row["planets_in_house"] if name != lord]
    others = [name for name in row["planets_aspecting"] if name != lord]
    if row["lord_house"] == house:
        seat = f"{lord} sits in this house"
        seat += f" with {_join(occupants)}" if occupants else ""
        bits = [seat + "."]
    elif lord in row["planets_aspecting"]:
        bits = [f"{lord} aspects this house."]
        if occupants:
            verb = "sits" if len(occupants) == 1 else "sit"
            bits.append(f"{_join(occupants)} {verb} there.")
        else:
            bits.append("The house is empty.")
    else:
        bits = [f"{lord} does not aspect this house."]
        if occupants:
            verb = "sits" if len(occupants) == 1 else "sit"
            bits.append(f"{_join(occupants)} {verb} there.")
        else:
            bits.append("The house is empty.")
    if others:
        verb = "aspects" if len(others) == 1 else "aspect"
        bits.append(f"{_join(others)} also {verb} it.")
    return " ".join(bits)


def _dusthana_join(lord: str, lord_sign: str, asc_sign_index: int, positions: dict) -> str:
    joined: dict[str, list[int]] = {}
    for house in (6, 8, 12):
        other = lord_of_house(asc_sign_index, house)
        if other == lord:
            continue
        pdata = positions.get(other) or {}
        if pdata.get("sign") == lord_sign:
            joined.setdefault(other, []).append(house)
    if not joined:
        return f"{lord} sits apart from the lords of the 6th, the 8th, and the 12th."
    parts = []
    for other, houses in joined.items():
        owned = " and ".join(f"the {_ordinal(house)}" for house in houses)
        parts.append(f"{other}, lord of {owned}")
    return f"{lord} is joined with {_join(parts)}."


def _navamsa_lord_line(lord: str, nav: dict) -> str:
    pdata = nav.get(lord) or {}
    sign = pdata.get("sign") or ""
    degree = float(pdata.get("degree_in_sign") or 0)
    dignity = classify_sign_dignity(lord, sign, degree)
    house = int(pdata.get("house") or 0)
    vargottama = bool(pdata.get("vargottama"))
    retro = "retrograde, " if pdata.get("retrograde") else ""
    same = ", vargottama" if vargottama else ""
    return (
        f"In Navamsa, {lord} is {retro}{_dignity_place(dignity, sign)}{same}, "
        f"in the {_ordinal(house)} of the Navamsa. {_fruit(dignity, vargottama)}"
    )


def _navamsa_house_line(house: int, nav_row: dict, nav_positions: dict) -> str:
    lord = nav_row["lord"]
    pdata = nav_positions.get(lord) or {}
    sign = pdata.get("sign") or ""
    degree = float(pdata.get("degree_in_sign") or 0)
    dignity = classify_sign_dignity(lord, sign, degree)
    lord_house = int(nav_row.get("lord_house") or 0)
    if lord_house == house:
        place = "sitting in this Navamsa house"
    else:
        place = f"the {_ordinal(lord_house)} of the Navamsa"
    return (
        f"In the Navamsa chart the {_ordinal(house)} is {nav_row['sign']}. "
        f"Its lord {lord} is {_dignity_place(dignity, sign)}, {place}."
    )


def _significator_line(name: str, positions: dict) -> str:
    pdata = positions.get(name) or {}
    sign = pdata.get("sign") or ""
    degree = float(pdata.get("degree_in_sign") or 0)
    dignity = classify_sign_dignity(name, sign, degree)
    house = int(pdata.get("house") or 0)
    retro = "retrograde, " if pdata.get("retrograde") else ""
    return (
        f"{name} is the marriage significator, {retro}{_dignity_place(dignity, sign)}, "
        f"the {_ordinal(house)}."
    )


def _pushkara_phrase(name: str, pdata: dict, row: dict) -> str:
    lon = pdata.get("longitude")
    if lon is None:
        return ""
    seat = pushkara_seat(lon)
    if not seat["mark"]:
        return ""
    sign = pdata.get("sign") or seat["sign"]
    degree = float(pdata.get("degree_in_sign") or seat["degree_in_sign"])
    place = f"{degree:.2f}° {sign}"
    if seat["mark"] == "degree":
        detail = f"{place}, on the Pushkara degree"
    else:
        detail = f"{place}, {seat['nakshatra']} pada {seat['pada']}, a Pushkara Navamsa"
    if name in row["planets_in_house"]:
        return f"{name} sits at {detail}"
    if name in row["planets_aspecting"]:
        return f"{name} aspects from {detail}"
    return f"{name}, the lord, is at {detail}"


def _pushkara_line(lord: str, row: dict, positions: dict) -> str:
    ordered = [lord]
    ordered.extend(name for name in row["planets_in_house"] if name != lord)
    ordered.extend(name for name in row["planets_aspecting"] if name != lord)
    phrases = []
    seen = set()
    for name in ordered:
        if name in seen:
            continue
        seen.add(name)
        phrase = _pushkara_phrase(name, positions.get(name) or {}, row)
        if phrase:
            phrases.append(phrase)
    if not phrases:
        return ""
    return "Pushkara reaches this house. " + _join(phrases) + "."


def _remedy_line(lord: str, d1_dignity: str, d9_dignity: str) -> str:
    if d1_dignity in _STRONG and d9_dignity in _THIN:
        return (
            f"A remedy for {lord} can support the delivery. "
            "The mantra, the weekday, and the charity are on the Avastha tab."
        )
    return ""


def house_giving(chart: dict, question_id: str, gender: str) -> dict:
    """Four lines, plus the Navamsa house for self, marriage, and the 9th."""
    house = QUESTION_HOUSE.get(question_id)
    if not house:
        return {"house": 0, "lines": []}
    asc = chart.get("ascendant") or {}
    asc_idx = int(asc.get("sign_index") or 0)
    positions = chart.get("planet_positions") or {}
    nav_positions = chart.get("navamsa_positions") or {}
    nav_asc = chart.get("navamsa_ascendant") or {}
    nav_idx = int(nav_asc.get("sign_index") or 0)

    row = analyze_house(house, asc_sign_index=asc_idx, planet_positions=positions)
    lord = row["lord"]
    pdata = positions.get(lord) or {}
    sign = pdata.get("sign") or row.get("lord_sign") or ""
    degree = float(pdata.get("degree_in_sign") or 0)
    dignity = classify_sign_dignity(lord, sign, degree)
    nav = nav_positions.get(lord) or {}
    d9_sign = nav.get("sign") or ""
    d9_dignity = classify_sign_dignity(lord, d9_sign, float(nav.get("degree_in_sign") or 0))

    lines = [
        _placement(
            lord, sign, dignity, int(row["lord_house"] or 0), house,
            int(row["houses_from_own"] or 1), bool(pdata.get("retrograde")),
        ),
        _support(lord, house, row),
        _dusthana_join(lord, sign, asc_idx, positions),
        _navamsa_lord_line(lord, nav_positions),
    ]
    pushkara = _pushkara_line(lord, row, positions)
    if pushkara:
        lines.append(pushkara)
    if house in NAVAMSA_CHART_HOUSES and nav_positions:
        nav_row = analyze_house(house, asc_sign_index=nav_idx, planet_positions=nav_positions)
        lines.append(_navamsa_house_line(house, nav_row, nav_positions))
    if question_id == "marriage":
        significator = "Mars" if gender == "female" else "Venus"
        if significator != lord:
            lines.append(_significator_line(significator, positions))
    remedy = _remedy_line(lord, dignity, d9_dignity)
    if remedy:
        lines.append(remedy)
    return {"house": house, "lord": lord, "lines": lines}
