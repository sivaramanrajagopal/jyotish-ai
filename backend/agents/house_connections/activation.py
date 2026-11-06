"""Which houses are active now: the dasha switches houses on, Jupiter and Saturn trigger them.

Dasha (Parashari): a running lord gives the results of the houses it rules and occupies
(main), and of the houses it aspects, the houses ruled by planets sitting with it, and the
houses its nakshatra lord rules and sits in (side). Rahu and Ketu rule no sign, so they act
for the lord of the sign they occupy (main). A node as star lord acts through its sign lord.
A house both running lords reach by any route is shared. Only main and shared houses can
be live; a side house reached by one lord alone stays a connection.

Transit (double transit, from the lagna, whole-sign): a house is triggered when Jupiter
and Saturn each occupy or aspect the house or the sign holding its lord. Aspects come
from _planet_aspects, the same table the rest of the app uses.

No score here. The words for how well a house gives are the Reading tab's fruit line.
"""

from __future__ import annotations

from datetime import date, datetime

from agents.bhavat_bhavam.core import whole_sign_house
from agents.house_connections.core import houses_owned_by, nakshatra_lord_for
from agents.house_connections.edges import PARIVARTANA_KINDS, exchanges, parivartana_kind
from agents.house_connections.themes import HOUSE_THEMES
from agents.natal_agent import SIGNS, SIGN_LORDS
from agents.nadi_agent import TZ, _fmt
from agents.reading_house import house_fruit
from agents.transit_score_agent import _planet_aspects, score_all_houses
from dasha_core import find_current_dasha_bhukti

NODES = ("Rahu", "Ketu")
ROLE = {
    "maha": ("mahadasha lord", "மகா தசை அதிபதி"),
    "bhukti": ("bhukti lord", "புக்தி அதிபதி"),
}
STATUS = {
    "live": ("Live now", "இப்போது செயலில்"),
    "waiting": ("Dasha on, transit not now", "தசை இயக்கம், கோசாரம் இப்போது இல்லை"),
    "sky": ("Transit only", "கோசாரம் மட்டும்"),
    "quiet": ("Quiet", "அமைதி"),
}
STATUS_ORDER = {"live": 0, "waiting": 1, "sky": 2, "quiet": 3}
FRUIT = {
    "The fruit holds.": ("good", "பலன் நிலைக்கும்."),
    "The fruit is available.": ("good", "பலன் கிடைக்கும்."),
    "The fruit is ordinary.": ("mixed", "பலன் சாதாரணம்."),
    "The fruit is thinner.": ("hard", "பலன் குறைவு."),
    "The fruit is weak.": ("hard", "பலன் பலவீனம்."),
}
RELATION = {
    1: ("together in one sign", "ஒரே ராசியில்", "neutral"),
    2: ("2/12 from each other, classically uneasy", "2/12 நிலை, சிரமம்", "uneasy"),
    3: ("3/11 from each other, classically supportive", "3/11 நிலை, ஆதரவு", "steady"),
    4: ("4/10 from each other, classically supportive", "4/10 நிலை, ஆதரவு", "steady"),
    5: ("5/9 from each other, classically harmonious", "5/9 நிலை, இணக்கம்", "steady"),
    6: ("6/8 from each other, classically strained", "6/8 நிலை, சிரமம்", "uneasy"),
    7: ("opposite each other (7/7), workable", "7/7 நிலை, சமாளிக்கலாம்", "steady"),
}


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _ord_ta(n: int) -> str:
    return f"{n}ஆம்"


def _ords(houses: list[int]) -> str:
    names = [f"the {ordinal(h)}" for h in houses]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _theme(h: int, lang: str = "en") -> str:
    return HOUSE_THEMES[h][lang].lower() if lang == "en" else HOUSE_THEMES[h][lang]


def _seat(pp: dict, planet: str, asc: int) -> int:
    idx = (pp.get(planet) or {}).get("sign_index")
    return 0 if idx is None else whole_sign_house(idx, asc)


def _distance(a: int, b: int) -> int:
    """Houses from a to b counted inclusively, folded to 1..7 (6 and 8 both read as 6)."""
    n = ((b - a) % 12) + 1
    return n if n <= 7 else 14 - n


def dasha_reasons(planet: str, role: str, pp: dict, asc: int) -> dict[int, list[dict]]:
    """House -> reasons the running lord switches it on, each marked main or side."""
    out: dict[int, list[dict]] = {}
    role_en, role_ta = ROLE[role]

    def add(house: int, level: str, en: str, ta: str) -> None:
        if house:
            out.setdefault(house, []).append({"planet": planet, "role": role, "level": level, "en": en, "ta": ta})

    seat = _seat(pp, planet, asc)
    add(seat, "main", f"{planet}, the {role_en}, sits here", f"{role_ta} {planet} இங்கு அமர்வு")
    if planet in NODES:
        dispositor = SIGN_LORDS.get((pp.get(planet) or {}).get("sign", ""), "")
        for h in houses_owned_by(dispositor, asc):
            add(h, "main", f"{planet}, the {role_en}, acts for its sign lord {dispositor}, who rules this house",
                f"{role_ta} {planet}, ராசி அதிபதி {dispositor} வழியாக இந்த வீட்டை இயக்குகிறது")
    else:
        for h in houses_owned_by(planet, asc):
            add(h, "main", f"{planet}, the {role_en}, rules this house", f"{role_ta} {planet} இந்த வீட்டின் அதிபதி")
    if seat:
        for h in _planet_aspects(planet, seat):
            add(h, "side", f"{planet}, the {role_en}, aspects this house", f"{role_ta} {planet} பார்வை")
    if seat:
        for other in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            if other == planet or _seat(pp, other, asc) != seat:
                continue
            for h in houses_owned_by(other, asc):
                if h in out:
                    continue
                add(h, "side", f"{planet}, the {role_en}, sits with {other}, who rules this house",
                    f"{role_ta} {planet} {other} உடன், {other} இந்த வீட்டின் அதிபதி")
    star_lord = nakshatra_lord_for(pp.get(planet) or {})
    if star_lord and star_lord != planet:
        acting = star_lord
        if star_lord in NODES:
            acting = SIGN_LORDS.get((pp.get(star_lord) or {}).get("sign", ""), "")
        for h in houses_owned_by(acting, asc):
            if h in out:
                continue
            if acting == star_lord:
                en = f"{planet}'s star lord {star_lord} rules this house"
                ta = f"{planet} நட்சத்திர அதிபதி {star_lord} இந்த வீட்டின் அதிபதி"
            else:
                en = f"{planet}'s star lord {star_lord} acts for its sign lord {acting}, who rules this house"
                ta = f"{planet} நட்சத்திர அதிபதி {star_lord}, ராசி அதிபதி {acting} வழியாக இந்த வீடு"
            add(h, "side", en, ta)
        star_seat = _seat(pp, star_lord, asc)
        if star_seat and star_seat not in out:
            add(star_seat, "side", f"{planet}'s star lord {star_lord} sits here",
                f"{planet} நட்சத்திர அதிபதி {star_lord} இங்கு அமர்வு")
    return out


def shared_houses(maha: str, bhukti: str, pp: dict, asc: int) -> set[int]:
    """Houses both the mahadasha lord and the bhukti lord reach, by any route."""
    return set(dasha_reasons(maha, "maha", pp, asc)) & set(dasha_reasons(bhukti, "bhukti", pp, asc))


def _transit_touch(planet: str, sign_index: int | None, asc: int, house: int, lord_seat: int) -> dict:
    if sign_index is None:
        return {"house": False, "lord": False, "lines": []}
    at = whole_sign_house(sign_index, asc)
    reach = {at, *_planet_aspects(planet, at)}
    lines = []
    if at == house:
        lines.append((f"{planet} is passing through this house", f"{planet} இந்த வீட்டில் சஞ்சாரம்"))
    elif house in reach:
        lines.append((f"{planet} aspects this house from the {ordinal(at)}",
                      f"{planet} {_ord_ta(at)} வீட்டிலிருந்து பார்வை"))
    if lord_seat and lord_seat in reach:
        verb = "is passing over" if at == lord_seat else "aspects"
        lines.append((f"{planet} {verb} the house lord's sign", f"{planet} அதிபதியின் ராசியைத் தொடுகிறது"))
    return {
        "house": house in reach,
        "lord": bool(lord_seat) and lord_seat in reach,
        "lines": [{"en": en, "ta": ta} for en, ta in lines],
    }


def house_links(h: int, houses: dict[int, dict], yogas: list[dict], pp: dict, asc: int) -> list[dict]:
    """Up to three plain lines on how this house is tied to others."""
    row = houses[h]
    lord, lh = row["lord"], row["lord_house"]
    lines: list[dict] = []
    if lh == h:
        lines.append({"en": f"Its lord {lord} sits in its own house", "ta": f"அதிபதி {lord} சொந்த வீட்டில்"})
    elif lh:
        lines.append({
            "en": f"Its lord {lord} sits in the {ordinal(lh)}, {_theme(lh)}, the {ordinal(row['houses_from_own'])} from this house",
            "ta": f"அதிபதி {lord} {_ord_ta(lh)} வீட்டில் ({_theme(lh, 'ta')})",
        })
    for a, b in exchanges(houses):
        if h in (a, b):
            other = b if h == a else a
            name_en, name_ta = PARIVARTANA_KINDS[parivartana_kind(a, b)]
            lines.append({
                "en": f"Its lord exchanges signs with the {ordinal(other)} lord, {_theme(other)} ({name_en})",
                "ta": f"{_ord_ta(other)} அதிபதியுடன் பரிவர்த்தனை ({name_ta})",
            })
    for y in yogas:
        if h in y["houses"]:
            lines.append({"en": f"{y['name']}: {y['detail_en']}", "ta": f"{y['name_ta']}: {y['detail_ta']}"})
    lord_sign = (pp.get(lord) or {}).get("sign_index")
    if lord_sign is not None:
        for other in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            if other == lord or (pp.get(other) or {}).get("sign_index") != lord_sign:
                continue
            owned = houses_owned_by(other, asc)
            lines.append({
                "en": f"{lord} sits with {other}, lord of {_ords(owned)}",
                "ta": f"{lord} உடன் {other} ({', '.join(_ord_ta(o) for o in owned)} அதிபதி)",
            })
    seen = set()
    unique = []
    for line in lines:
        if line["en"] not in seen:
            seen.add(line["en"])
            unique.append(line)
    return unique[:3]


def _period(chart: dict, as_of: date) -> dict | None:
    pp = chart.get("planet_positions") or {}
    dob = str((chart.get("birth_data") or {}).get("dob") or "")
    moon = (pp.get("Moon") or {}).get("longitude")
    if not dob or moon is None:
        return None
    moment = datetime(as_of.year, as_of.month, as_of.day, 12, 0)
    _, maha, bhuktis, bhukti = find_current_dasha_bhukti(float(moon), dob, moment)
    index = next((i for i, row in enumerate(bhuktis) if row is bhukti), None)
    nxt = bhuktis[index + 1] if index is not None and index + 1 < len(bhuktis) else None

    def span(row: dict) -> dict:
        return {
            "planet": row["planet"],
            "start": _fmt(row["start"].date()),
            "end": _fmt(row["end"].date()),
            "end_iso": row["end"].date().isoformat(),
        }

    return {
        "mahadasha": span(maha),
        "bhukti": span(bhukti),
        "next_bhukti": span(nxt) if nxt else None,
        "days_left": (bhukti["end"].date() - as_of).days,
    }


def compute_activation(chart: dict, houses: dict[int, dict], yogas: list[dict], as_of: date | None = None) -> dict:
    when = as_of or datetime.now(TZ).date()
    pp = chart.get("planet_positions") or {}
    asc = int((chart.get("ascendant") or {}).get("sign_index") or 0)

    period = _period(chart, when)
    reasons: dict[int, list[dict]] = {}
    shared: set[int] = set()
    relation = None
    if period:
        md, bh = period["mahadasha"]["planet"], period["bhukti"]["planet"]
        shared = shared_houses(md, bh, pp, asc)
        for planet, role in ((md, "maha"), (bh, "bhukti")):
            for h, rows in dasha_reasons(planet, role, pp, asc).items():
                reasons.setdefault(h, []).extend(rows)
        if md != bh:
            en, ta, tone = RELATION[_distance(_seat(pp, md, asc), _seat(pp, bh, asc))]
            relation = {"en": f"{bh} and {md} sit {en}.", "ta": f"{bh} & {md}: {ta}.", "tone": tone}

    scores = score_all_houses(chart, transit_date=when.isoformat(), transit_time="12:00")
    sky = {row["planet"]: row for row in scores.get("transit_analysis") or []}

    def sky_sign(planet: str) -> int | None:
        name = (sky.get(planet) or {}).get("transit_sign_en") or ""
        return SIGNS.index(name) if name in SIGNS else None

    jupiter_sign, saturn_sign = sky_sign("Jupiter"), sky_sign("Saturn")
    moon_sign = sky_sign("Moon")
    by_house: dict[int, list[str]] = {}
    sky_now: dict[str, dict] = {}
    for planet, row in sky.items():
        idx = sky_sign(planet)
        if idx is None:
            continue
        retro = bool(row.get("retrograde")) and planet not in ("Sun", "Moon", *NODES)
        at = whole_sign_house(idx, asc)
        by_house.setdefault(at, []).append(f"{planet} (R)" if retro else planet)
        sky_now[planet] = {"sign": SIGNS[idx], "house": at, "retrograde": retro}

    rows = []
    for h in range(1, 13):
        hrow = houses[h]
        jup = _transit_touch("Jupiter", jupiter_sign, asc, h, hrow["lord_house"])
        sat = _transit_touch("Saturn", saturn_sign, asc, h, hrow["lord_house"])
        double = (jup["house"] or jup["lord"]) and (sat["house"] or sat["lord"])
        why = reasons.get(h, [])
        if any(r["level"] == "main" for r in why):
            level = "main"
        elif h in shared:
            level = "shared"
        else:
            level = "side" if why else ""
        strong = level in ("main", "shared")
        if strong and double:
            status = "live"
        elif strong:
            status = "waiting"
        elif double:
            status = "sky"
        else:
            status = "quiet"
        fruit = house_fruit(chart, h)["fruit"]
        tone, fruit_ta = FRUIT.get(fruit, ("mixed", ""))
        sav = (scores.get("houses") or {}).get(h) or {}
        rows.append({
            "house": h,
            "ordinal": ordinal(h),
            "sign": hrow["sign"],
            "theme_en": hrow["theme_en"],
            "theme_ta": hrow["theme_ta"],
            "lord": hrow["lord"],
            "lord_house": hrow["lord_house"],
            "fruit": {"en": fruit, "ta": fruit_ta, "tone": tone},
            "status": {"key": status, "en": STATUS[status][0], "ta": STATUS[status][1]},
            "dasha": {"level": level, "reasons": why},
            "transit": {
                "double": bool(double),
                "jupiter": jup["house"] or jup["lord"],
                "saturn": sat["house"] or sat["lord"],
                "lines": jup["lines"] + sat["lines"],
                "planets_now": by_house.get(h, []),
                "sav_points": sav.get("sav_points"),
                "sav_label": sav.get("sav_label") or "",
            },
            "links": house_links(h, houses, yogas, pp, asc),
        })

    active = [r for r in rows if r["dasha"]["level"] in ("main", "shared")]
    active.sort(key=lambda r: (
        0 if r["dasha"]["level"] == "main" else 1,
        STATUS_ORDER[r["status"]["key"]],
        -len(r["dasha"]["reasons"]),
        r["house"],
    ))
    moon_house = whole_sign_house(moon_sign, asc) if moon_sign is not None else 0
    today = None
    if moon_house:
        today = {
            "house": moon_house,
            "en": f"Today the Moon passes your {ordinal(moon_house)}, {_theme(moon_house)}.",
            "ta": f"இன்று சந்திரன் {_ord_ta(moon_house)} வீட்டில் ({_theme(moon_house, 'ta')}).",
        }
    return {
        "as_of": when.isoformat(),
        "period": period,
        "relation": relation,
        "today": today,
        "now": [r["house"] for r in active[:4]],
        "sky_only": [r["house"] for r in rows if r["status"]["key"] == "sky"],
        "sky": sky_now,
        "rows": rows,
    }
