"""Qualitative Ripu theme notes from D1 and D6 houses — no score."""

from __future__ import annotations

from agents.natal_agent import SIGN_LORDS, SIGNS

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]
MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
TONES = ("quiet", "mixed", "present")


def _lord_of(asc_idx: int, house: int) -> str:
    sign_idx = (int(asc_idx) + int(house) - 1) % 12
    return SIGN_LORDS[SIGNS[sign_idx]]


def _sign_of(asc_idx: int, house: int) -> str:
    return SIGNS[(int(asc_idx) + int(house) - 1) % 12]


def house_snapshot(positions: dict, asc_idx: int, house: int) -> dict:
    occupants = [
        name for name in PLANETS
        if name in positions and int((positions[name] or {}).get("house") or 0) == house
    ]
    lord = _lord_of(asc_idx, house)
    lord_house = int((positions.get(lord) or {}).get("house") or 0)
    return {
        "house": house,
        "sign": _sign_of(asc_idx, house),
        "lord": lord,
        "occupants": occupants,
        "lord_house": lord_house,
        "malefic_here": any(p in MALEFICS for p in occupants),
        "lord_in_dusthana": lord_house in (6, 8, 12),
    }


def _line(snap: dict, chart: str) -> str:
    occ = ", ".join(snap["occupants"]) if snap["occupants"] else "empty"
    dust = " in a dusthana" if snap["lord_in_dusthana"] else f" in H{snap['lord_house']}" if snap["lord_house"] else ""
    return (
        f"{chart} H{snap['house']} {snap['sign']}: lord {snap['lord']}{dust}; "
        f"occupants {occ}."
    )


def _hit(snap: dict, maha: str, bhukti: str) -> bool:
    return bool(
        snap["occupants"]
        or snap["lord_in_dusthana"]
        or snap["lord"] in (maha, bhukti)
    )


def _tone(hits: int, malefic_both: bool) -> str:
    if malefic_both or hits >= 2:
        return "present"
    if hits == 1:
        return "mixed"
    return "quiet"


def _card(
    *,
    theme_id: str,
    title: str,
    primer: str,
    d1_line: str,
    d6_line: str,
    dasa_line: str,
    hits: int,
    malefic_both: bool,
) -> dict:
    return {
        "id": theme_id,
        "title": title,
        "primer": primer,
        "tone": _tone(hits, malefic_both),
        "d1": d1_line,
        "d6": d6_line,
        "dasa": dasa_line,
    }


def build_theme_cards(
    *,
    d1_positions: dict,
    d1_asc_idx: int,
    d6_positions: dict,
    d6_asc_idx: int,
    maha: str,
    bhukti: str,
) -> list[dict]:
    d1_6 = house_snapshot(d1_positions, d1_asc_idx, 6)
    d1_8 = house_snapshot(d1_positions, d1_asc_idx, 8)
    d1_12 = house_snapshot(d1_positions, d1_asc_idx, 12)
    d6_1 = house_snapshot(d6_positions, d6_asc_idx, 1)
    d6_6 = house_snapshot(d6_positions, d6_asc_idx, 6)
    d6_8 = house_snapshot(d6_positions, d6_asc_idx, 8)
    d6_10 = house_snapshot(d6_positions, d6_asc_idx, 10)

    period = f"{maha}–{bhukti}"
    lords = {maha, bhukti}

    def dasa_for(*snaps: dict) -> str:
        names = []
        seen = set()
        for snap in snaps:
            lord = snap["lord"]
            if lord in lords and lord not in seen:
                seen.add(lord)
                names.append(f"{lord} rules {snap['sign']} H{snap['house']}")
        if names:
            return f"{period} touches " + "; ".join(names) + "."
        return f"{period} does not rule these houses now."

    cards = [
        _card(
            theme_id="debt",
            title="Debt / litigation (Rina)",
            primer="D1 6th is the terrain of debt and cases; D6 shows how the fight proceeds.",
            d1_line=_line(d1_6, "D1"),
            d6_line=_line(d6_6, "D6"),
            dasa_line=dasa_for(d1_6, d6_6),
            hits=int(_hit(d1_6, maha, bhukti)) + int(_hit(d6_6, maha, bhukti)),
            malefic_both=d1_6["malefic_here"] and d6_6["malefic_here"],
        ),
        _card(
            theme_id="enemies",
            title="Enemies / opposition (Ripu)",
            primer="Open opposition sits in the 6th; D6 is whether you can work through it.",
            d1_line=_line(d1_6, "D1"),
            d6_line=_line(d6_6, "D6"),
            dasa_line=dasa_for(d1_6, d6_6),
            hits=int(_hit(d1_6, maha, bhukti)) + int(_hit(d6_6, maha, bhukti)),
            malefic_both=d1_6["malefic_here"] and d6_6["malefic_here"],
        ),
        _card(
            theme_id="exams",
            title="Competitive exams (Shatru)",
            primer="D6 is defeating rivals / clearing the paper, not the subject (that is D24).",
            d1_line=_line(d1_6, "D1"),
            d6_line=_line(d6_6, "D6"),
            dasa_line=dasa_for(d1_6, d6_6),
            hits=int(_hit(d1_6, maha, bhukti)) + int(_hit(d6_6, maha, bhukti)),
            malefic_both=d1_6["malefic_here"] and d6_6["malefic_here"],
        ),
        _card(
            theme_id="service",
            title="Service jobs (Seva)",
            primer="D1 6th is service under others; D6 10th is how that daily work lands. Career/D10 stays profession type.",
            d1_line=_line(d1_6, "D1"),
            d6_line=_line(d6_10, "D6"),
            dasa_line=dasa_for(d1_6, d6_10),
            hits=int(_hit(d1_6, maha, bhukti)) + int(_hit(d6_10, maha, bhukti)),
            malefic_both=d1_6["malefic_here"] and d6_10["malefic_here"],
        ),
        _card(
            theme_id="illness",
            title="Illness as obstacle (Roga)",
            primer="D6 is whether a health obstacle can be worked through. The body map stays on the Health tab. Not a diagnosis.",
            d1_line=_line(d1_6, "D1") + " " + _line(d1_8, "D1") + " " + _line(d1_12, "D1"),
            d6_line=_line(d6_1, "D6") + " " + _line(d6_6, "D6") + " " + _line(d6_8, "D6"),
            dasa_line=dasa_for(d1_6, d1_8, d6_1, d6_6),
            hits=int(_hit(d1_6, maha, bhukti) or _hit(d1_8, maha, bhukti))
            + int(_hit(d6_6, maha, bhukti) or _hit(d6_8, maha, bhukti)),
            malefic_both=(d1_6["malefic_here"] or d1_8["malefic_here"])
            and (d6_6["malefic_here"] or d6_8["malefic_here"]),
        ),
    ]
    return cards
