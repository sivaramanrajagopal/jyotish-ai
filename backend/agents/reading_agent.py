"""One sitting: the engines already in the app, spoken in a fixed order."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import ephemeris as swe

from agents.avastha_agent import compute_avastha_analysis
from dasha_core import find_current_dasha_bhukti
from agents.dosha_radar_agent import compute_dosha_radar_analysis
from agents.nadi_agent import SIGNS, TZ, _fmt, _sky, _to_jd, compute_nadi
from agents.reading_house import house_giving
from agents.panchangam_agent import calculate_panchangam
from agents.shadbala_agent import compute_shadbala_for_chart
from agents.tara_engine import compute_all
from agents.transit_score_agent import score_all_houses
from location_utils import nearest_panchangam_location

MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def _birth(chart: dict) -> dict:
    return chart.get("birth_data") or {}


def _gender(chart: dict) -> str:
    raw = str(_birth(chart).get("gender") or "male").lower()
    return raw if raw in ("male", "female") else "male"


def _note(chart: dict) -> str:
    raw = str(_birth(chart).get("note") or "").lower()
    return raw if raw in ("married", "work") else ""


def _named(name: str) -> str:
    if name == "Sun":
        return "the Sun"
    if name == "Moon":
        return "the Moon"
    return name


def _join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _cap(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _born_label(chart: dict) -> str:
    birth = _birth(chart)
    dob = str(birth.get("dob") or "")
    tob = str(birth.get("tob") or "")
    try:
        day = date.fromisoformat(dob)
        when = f"{day.day} {MONTHS[day.month - 1]} {day.year}"
    except ValueError:
        when = dob
    if tob:
        when = f"{when}, {tob[:5]}"
    return when


def _who(chart: dict) -> dict:
    asc = chart.get("ascendant") or {}
    planets = chart.get("planet_positions") or {}
    moon = planets.get("Moon") or {}
    sun = planets.get("Sun") or {}
    lagna = asc.get("sign") or ""
    pada = asc.get("pada")
    star = asc.get("nakshatra") or ""
    pada_bit = f" pada {pada}" if pada else ""
    sentence = (
        f"{lagna} lagna, {star}{pada_bit}. "
        f"The Moon is in {moon.get('sign')}, {moon.get('nakshatra')}. "
        f"The Sun is in {sun.get('sign')}, {sun.get('nakshatra')}."
    )
    return {
        "sentence": sentence,
        "born": _born_label(chart),
        "place": _birth(chart).get("place_of_birth") or chart.get("place_of_birth") or "",
        "lagna": lagna,
        "moon": moon.get("sign") or "",
        "sun": sun.get("sign") or "",
    }


def _voice(chart: dict, dasha_lord: str, bhukti_lord: str, avastha: dict) -> dict:
    gender = _gender(chart)
    karaka = "Mars" if gender == "female" else "Venus"
    strength = {row["planet"]: row for row in compute_shadbala_for_chart(chart)["planets"]}
    condition = {row["planet"]: row for row in avastha.get("planets") or []}
    ranked = sorted(strength.values(), key=lambda row: row["rank"])
    meeting = [row["planet"] for row in ranked if row["meets_minimum"]]
    short = [row["planet"] for row in ranked if not row["meets_minimum"]]
    leaders = meeting[:2]

    parts = []
    if leaders:
        verb = "holds" if len(leaders) == 1 else "hold"
        parts.append(f"{_cap(_join([_named(name) for name in leaders]))} {verb} more than they need.")
    if short:
        verb = "is" if len(short) == 1 else "are"
        parts.append(f"{_cap(_join([_named(name) for name in short]))} {verb} short.")
    elif not leaders:
        parts.append("Every planet is short of what it needs.")
    else:
        parts.append("Every planet holds at least what it needs.")
    if dasha_lord in short:
        parts.append(
            f"{_cap(_named(dasha_lord))} is also the mahadasha lord, "
            "so this chapter is led by a planet that is short."
        )
    karaka_row = condition.get(karaka) or {}
    sthula = ((karaka_row.get("sthula") or {}).get("name")) or "its condition"
    held = "holds more than needed" if karaka in meeting else "is short of what is needed"
    if _note(chart) == "married":
        parts.append(
            f"{_cap(_named(karaka))} {held} and is {sthula} in condition. "
            "The marriage matter is already lived, so this sitting does not lead with it."
        )
    else:
        parts.append(
            f"{_cap(_named(karaka))} {held} and is {sthula} in condition. "
            f"Marriage starts from {_named(karaka)}, so both are read together."
        )

    wanted = []
    for name in leaders + short + [dasha_lord, bhukti_lord, karaka]:
        if name and name not in wanted and name in strength:
            wanted.append(name)
    wanted.sort(key=lambda name: strength[name]["rank"])
    rows = []
    for name in wanted:
        bal = strength[name]
        av = condition.get(name) or {}
        net = (av.get("manifestation") or {}).get("net")
        sthula_name = (av.get("sthula") or {}).get("name") or ""
        sukshma_name = (av.get("sukshma") or {}).get("name") or ""
        rows.append({
            "planet": name,
            "held": bal["rupas"],
            "needed": bal["minimum"],
            "short": not bal["meets_minimum"],
            "condition": sthula_name,
            "sukshma": sukshma_name,
            "net": round(net) if isinstance(net, (int, float)) else None,
        })
    return {"sentence": " ".join(parts), "rows": rows, "marriage": karaka}


def _chapter(chart: dict, as_of: date, avastha: dict) -> dict:
    moon = float((chart.get("planet_positions") or {})["Moon"]["longitude"])
    dob = str(_birth(chart).get("dob") or "")
    moment = datetime(as_of.year, as_of.month, as_of.day, 12, 0)
    _, mahadasha, bhuktis, bhukti = find_current_dasha_bhukti(moon, dob, moment)
    index = next(i for i, row in enumerate(bhuktis) if row is bhukti)
    nxt = bhuktis[index + 1] if index + 1 < len(bhuktis) else None
    days_left = (bhukti["end"].date() - as_of).days
    synergy = avastha.get("dasa_bhukti") or {}
    score = synergy.get("combinedScore")
    klass = synergy.get("manifestationClass") or ""
    sentence = (
        f"{mahadasha['planet']} mahadasha runs from {_fmt(mahadasha['start'].date())} "
        f"to {_fmt(mahadasha['end'].date())}. "
        f"{bhukti['planet']} bhukti ends on {_fmt(bhukti['end'].date())}."
    )
    if days_left >= 0:
        sentence += f" {days_left} days remain in this bhukti."
    if nxt:
        sentence += (
            f" {nxt['planet']} bhukti begins on {_fmt(nxt['start'].date())} "
            f"and runs to {_fmt(nxt['end'].date())}."
        )
    if score is not None and klass:
        sentence += f" The two lords together score {round(score)}, {klass}."
    return {
        "sentence": sentence,
        "mahadasha": mahadasha["planet"],
        "mahadasha_start": _fmt(mahadasha["start"].date()),
        "mahadasha_end": _fmt(mahadasha["end"].date()),
        "bhukti": bhukti["planet"],
        "bhukti_end": _fmt(bhukti["end"].date()),
        "days_left": days_left,
        "next_bhukti": None if nxt is None else {
            "planet": nxt["planet"],
            "start": _fmt(nxt["start"].date()),
            "end": _fmt(nxt["end"].date()),
        },
        "score": round(score) if isinstance(score, (int, float)) else None,
        "score_label": klass,
    }


def _location(chart: dict) -> str:
    named = chart.get("panchangam_location")
    if named:
        return str(named)
    birth = _birth(chart)
    lat, lon = birth.get("lat"), birth.get("lon")
    if lat is None or lon is None:
        return "Chennai"
    return nearest_panchangam_location(float(lat), float(lon))


def _ordinal(house: int) -> str:
    if 10 <= house % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(house % 10, "th")
    return f"{house}{suffix}"


def _houses_in_play(chart: dict, as_of: date) -> list[dict]:
    """Houses a planet is passing through, with that house's meaning and SAV label."""
    scores = score_all_houses(chart, transit_date=as_of.isoformat(), transit_time="12:00")
    by_sign: dict[str, list[dict]] = {}
    for detail in scores.get("transit_analysis") or []:
        sign = detail.get("transit_sign_en") or ""
        if sign:
            by_sign.setdefault(sign, []).append(detail)
    order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    houses = []
    for number in range(1, 13):
        house = (scores.get("houses") or {}).get(number) or {}
        sign = house.get("house_sign_en") or ""
        present = by_sign.get(sign) or []
        if not present:
            continue
        present.sort(key=lambda row: order.index(row["planet"]) if row["planet"] in order else 99)
        phrases = []
        for row in present:
            name = row["planet"]
            if row.get("retrograde") and name not in ("Sun", "Moon", "Rahu", "Ketu"):
                phrases.append(f"retrograde {name}")
            else:
                phrases.append(_named(name))
        meaning = house.get("name") or house.get("area") or ""
        sav = house.get("sav_label") or ""
        who = _join(phrases)
        verb = "is" if len(phrases) == 1 else "are"
        line = (
            f"{_cap(who)} {verb} in the {_ordinal(number)}, {meaning}, "
            f"and that house's Sarvashtakavarga is {sav}."
        )
        houses.append({
            "house": number,
            "ordinal": _ordinal(number),
            "meaning": meaning,
            "planets": [row["planet"] for row in present],
            "sav_points": house.get("sav_points"),
            "sav_label": sav,
            "line": line,
        })
    return houses


def _slow_sentence(day: date) -> str:
    moment = datetime(day.year, day.month, day.day, 12, 0, tzinfo=TZ)
    jd = _to_jd(moment)
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    parts = []
    for name, planet_id in (("Jupiter", swe.JUPITER), ("Saturn", swe.SATURN)):
        xx, _ = swe.calc_ut(jd, planet_id, flags)
        sign = SIGNS[int((xx[0] % 360) / 30) % 12]
        motion = "retrograde in" if xx[3] < 0 else "in"
        parts.append(f"{name} is {motion} {sign}")
    sky = _sky(day)
    parts.append(f"Rahu is in {SIGNS[sky['Rahu']]}")
    parts.append(f"Ketu is in {SIGNS[sky['Ketu']]}")
    return ". ".join(parts) + "."


def _pressing(chart: dict, as_of: date) -> dict:
    loc = _location(chart)
    panch = calculate_panchangam(as_of.isoformat(), loc)
    tithi = f"{panch.get('tithi_paksha', '')} {panch.get('tithi_name', '')}".strip()
    vaaram = panch.get("vaaram_name") or ""
    birth = _birth(chart)
    moment = datetime(as_of.year, as_of.month, as_of.day, 12, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    personal = compute_all(
        int(chart.get("moon_nakshatra_index") or 0),
        int(chart.get("moon_rasi_index") or 0),
        moment,
        "Asia/Kolkata",
    )
    tara = personal.get("tara") or {}
    tara_name = tara.get("name") or ""
    nature = tara.get("nature") or ""
    if nature == "malefic":
        tara_bit = f"Tara {tara_name}, unfavourable."
    elif nature == "benefic":
        tara_bit = f"Tara {tara_name}, favourable."
    else:
        tara_bit = f"Tara {tara_name}."
    ashtama = (personal.get("chandra_ashtama") or {}).get("is_active")
    ashtama_bit = "Chandra Ashtama is active." if ashtama else "Chandra Ashtama is clear."
    moon = f"Moon in {personal.get('today_moon_rasi')}, {personal.get('today_moon_nak')}."
    slow = _slow_sentence(as_of)
    sentence = f"{vaaram}, {tithi}. {moon} {tara_bit} {ashtama_bit} {slow}"
    houses = _houses_in_play(chart, as_of)
    return {
        "sentence": sentence,
        "houses": houses,
        "vaaram": vaaram,
        "tithi": tithi,
        "tara": tara_name,
        "ashtama": bool(ashtama),
        "location": loc,
        "place_note": birth.get("place_of_birth") or "",
    }


def _life(chart: dict, as_of: date) -> list[dict]:
    payload = compute_nadi(chart, as_of=as_of)
    today = as_of.isoformat()
    gender = _gender(chart)
    rows = []
    for reading in payload["readings"]:
        seasons = reading.get("seasons") or []
        open_rows = [row for row in seasons if row["start"] <= today <= row["end"]]
        upcoming = sorted((row for row in seasons if row["start"] > today), key=lambda row: row["start"])
        current = open_rows[0] if open_rows else (upcoming[0] if upcoming else None)
        rows.append({
            "id": reading["id"],
            "label": reading["label"],
            "open": bool(open_rows),
            "significator": reading.get("significator") or "",
            "when": current["label"] if current else reading.get("season_status") or "",
            "start": current["start"] if current else "",
            "sort": current["end"] if open_rows else (current["start"] if current else "9999"),
            "analysis": reading.get("analysis") or "",
            "today": reading.get("today") or "",
            "season_status": reading.get("season_status") or "",
            "house": house_giving(chart, reading["id"], gender),
        })
    note = _note(chart)

    def _rank(row: dict) -> tuple:
        if note == "work" and row["id"] == "work":
            group = -1
        elif note == "married" and row["id"] == "marriage":
            group = 2
        else:
            group = 0 if row["open"] else 1
        return (group, row["sort"], row["label"])

    rows.sort(key=_rank)
    for row in rows:
        row.pop("sort", None)
    return rows


def _snags(chart: dict) -> dict:
    alerts = compute_dosha_radar_analysis(chart).get("active_alerts") or []
    lines = []
    for alert in alerts[:8]:
        note = (alert.get("note_en") or "").strip()
        planet = alert.get("planet") or ""
        if note:
            lines.append({"planet": planet, "note": note})
    if not lines:
        sentence = "No dosha alert is active on this day."
    elif len(lines) == 1:
        sentence = "One alert is active."
    else:
        sentence = f"{len(lines)} alerts are active."
    extra = len(alerts) - len(lines)
    if extra > 0:
        sentence += f" {extra} more sit on the Dosha tab."
    return {"sentence": sentence, "alerts": lines}


def _closed_ahead(life: list[dict], note: str) -> list[dict]:
    closed = [row for row in life if not row["open"] and row.get("start")]
    if note == "married":
        closed = [row for row in closed if row["id"] != "marriage"]
    closed.sort(key=lambda row: row["start"])
    return closed


def _timeline(chapter: dict, life: list[dict], note: str) -> dict:
    open_rows = [row for row in life if row["open"]]
    if note == "married":
        open_rows = [row for row in open_rows if row["id"] != "marriage"]
    today_names = _join([row["label"] for row in open_rows]) or "No season is open"
    today = (
        f"Open: {today_names}. "
        f"{chapter['bhukti']} bhukti until {chapter['bhukti_end']}."
    )
    past = f"{chapter['mahadasha']} mahadasha began {chapter['mahadasha_start']}."
    parts = []
    nxt = chapter.get("next_bhukti")
    if nxt:
        parts.append(f"{nxt['planet']} bhukti begins {nxt['start']}.")
    closed = _closed_ahead(life, note)
    next_season = None
    if closed:
        soonest = closed[0]["start"]
        names = [row["label"] for row in closed if row["start"] == soonest]
        opening = _fmt(date.fromisoformat(soonest))
        parts.append(f"{_join(names)} open {opening}.")
        next_season = {
            "labels": names,
            "when": opening,
            "start": soonest,
        }
    return {
        "past": past,
        "today": today,
        "next": " ".join(parts),
        "next_season": next_season,
    }


def _next(chapter: dict, life: list[dict], note: str = "") -> dict:
    parts = []
    nxt = chapter.get("next_bhukti")
    if nxt:
        parts.append(
            f"{nxt['planet']} bhukti runs from {nxt['start']} to {nxt['end']}."
        )
    closed = _closed_ahead(life, note)
    if closed:
        soonest = closed[0]["when"]
        names = [row["label"] for row in closed if row["when"] == soonest]
        verb = "is" if len(names) == 1 else "are"
        parts.append(f"{_join(names)} {verb} next: {soonest}.")
    open_rows = [row for row in life if row["open"] and row.get("when")]
    if note == "married":
        open_rows = [row for row in open_rows if row["id"] != "marriage"]
    if open_rows:
        named = [
            f"{row['label']} until {row['when'].split('–')[-1].strip()}"
            for row in open_rows
        ]
        parts.append(f"Already open: {_join(named)}.")
    return {"sentence": " ".join(parts)}


def compute_reading(chart: dict, as_of: date | None = None) -> dict:
    """Seven movements for one native, from the chart engines."""
    when = as_of or datetime.now(TZ).date()
    avastha = compute_avastha_analysis(chart)
    chapter = _chapter(chart, when, avastha)
    life = _life(chart, when)
    note = _note(chart)
    return {
        "as_of": when.isoformat(),
        "gender": _gender(chart),
        "note": note,
        "who": _who(chart),
        "voice": _voice(chart, chapter["mahadasha"], chapter["bhukti"], avastha),
        "chapter": chapter,
        "pressing": _pressing(chart, when),
        "life": life,
        "snags": _snags(chart),
        "next": _next(chapter, life, note),
        "timeline": _timeline(chapter, life, note),
    }


def compute_watch(chart: dict, as_of: date | None = None) -> dict:
    """Next bhukti and next season, without the full sitting."""
    when = as_of or datetime.now(TZ).date()
    avastha = compute_avastha_analysis(chart)
    chapter = _chapter(chart, when, avastha)
    life = _life(chart, when)
    note = _note(chart)
    timeline = _timeline(chapter, life, note)
    season = timeline.get("next_season") or {}
    days_until_season = None
    if season.get("start"):
        days_until_season = (date.fromisoformat(season["start"]) - when).days
    nxt = chapter.get("next_bhukti") or {}
    days_until_bhukti = None
    if nxt.get("start"):
        # start is a display label; days come from the chapter end of the current bhukti
        days_until_bhukti = chapter["days_left"]
    return {
        "as_of": when.isoformat(),
        "days_until_bhukti": days_until_bhukti,
        "next_bhukti": nxt or None,
        "days_until_season": days_until_season,
        "next_season": season or None,
        "timeline": {
            "past": timeline["past"],
            "today": timeline["today"],
            "next": timeline["next"],
        },
    }
