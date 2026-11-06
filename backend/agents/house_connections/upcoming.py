"""What comes next: the coming bhuktis, the houses each switches on, and when Jupiter and
Saturn both touch those houses (double transit, same rule as activation.py).

Signs come from the Nadi sky table (noon IST, sidereal Lahiri), one reading per day,
so a retrograde re-entry shows as its own sign change.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from agents.bhavat_bhavam.core import whole_sign_house
from agents.house_connections.activation import (
    RELATION,
    _distance,
    _seat,
    _theme,
    dasha_reasons,
    ordinal,
)
from agents.nadi_agent import _fmt, _sky
from agents.natal_agent import SIGNS
from agents.transit_score_agent import _planet_aspects
from dasha_core import generate_bhuktis, generate_dashas

MAX_YEARS = 4


def _touches(planet: str, sign_index: int, asc: int, house: int, lord_seat: int) -> bool:
    at = whole_sign_house(sign_index, asc)
    reach = {at, *_planet_aspects(planet, at)}
    return house in reach or (bool(lord_seat) and lord_seat in reach)


def sky_segments(start: date, end: date) -> list[dict]:
    """Runs of days with Jupiter and Saturn each in one sign."""
    segments: list[dict] = []
    day = start
    while day <= end:
        sky = _sky(day)
        key = (sky["Jupiter"], sky["Saturn"])
        if segments and segments[-1]["key"] == key:
            segments[-1]["end"] = day
        else:
            segments.append({"key": key, "start": day, "end": day})
        day += timedelta(days=1)
    return segments


def sign_changes(segments: list[dict], asc: int) -> list[dict]:
    out = []
    for prev, seg in zip(segments, segments[1:]):
        for i, planet in enumerate(("Jupiter", "Saturn")):
            if prev["key"][i] != seg["key"][i]:
                idx = seg["key"][i]
                house = whole_sign_house(idx, asc)
                out.append({
                    "planet": planet,
                    "date": _fmt(seg["start"]),
                    "iso": seg["start"].isoformat(),
                    "sign": SIGNS[idx],
                    "house": house,
                    "en": f"{planet} enters {SIGNS[idx]}, your {ordinal(house)} ({_theme(house)}), on {_fmt(seg['start'])}.",
                    "ta": f"{planet} {SIGNS[idx]} ({house}ஆம் வீடு) நுழைவு: {_fmt(seg['start'])}.",
                })
    return out


def _windows(segments: list[dict], start: date, end: date, asc: int, house: int, lord_seat: int) -> list[dict]:
    runs: list[list[date]] = []
    for seg in segments:
        lo, hi = max(seg["start"], start), min(seg["end"], end)
        if lo > hi:
            continue
        jup, sat = seg["key"]
        if _touches("Jupiter", jup, asc, house, lord_seat) and _touches("Saturn", sat, asc, house, lord_seat):
            if runs and runs[-1][1] + timedelta(days=1) >= lo:
                runs[-1][1] = hi
            else:
                runs.append([lo, hi])
    return [{"start": _fmt(a), "end": _fmt(b)} for a, b in runs]


def compute_upcoming(chart: dict, houses: dict[int, dict], as_of: date, count: int = 3) -> dict | None:
    pp = chart.get("planet_positions") or {}
    dob = str((chart.get("birth_data") or {}).get("dob") or "")
    moon = (pp.get("Moon") or {}).get("longitude")
    if not dob or moon is None:
        return None
    asc = int((chart.get("ascendant") or {}).get("sign_index") or 0)
    now = datetime(as_of.year, as_of.month, as_of.day, 12, 0)

    coming = []
    for maha in generate_dashas(float(moon), dob):
        if maha["end"] <= now:
            continue
        for bhukti in generate_bhuktis(maha):
            if bhukti["start"] > now:
                coming.append((maha["planet"], bhukti))
            if len(coming) == count:
                break
        if len(coming) == count:
            break
    if not coming:
        return None

    horizon = min(coming[-1][1]["end"].date(), as_of + timedelta(days=int(365.25 * MAX_YEARS)))
    segments = sky_segments(as_of, horizon)

    periods = []
    for maha_planet, bhukti in coming:
        start, end = bhukti["start"].date(), min(bhukti["end"].date(), horizon)
        planet = bhukti["planet"]
        main = sorted(
            h for h, rows in dasha_reasons(planet, "bhukti", pp, asc).items()
            if any(r["level"] == "main" for r in rows)
        )
        rows = []
        for h in main:
            windows = _windows(segments, start, end, asc, h, houses[h]["lord_house"]) if start <= horizon else []
            rows.append({
                "house": h,
                "ordinal": ordinal(h),
                "theme_en": houses[h]["theme_en"],
                "theme_ta": houses[h]["theme_ta"],
                "windows": windows,
            })
        relation = None
        if planet != maha_planet:
            en, ta, tone = RELATION[_distance(_seat(pp, maha_planet, asc), _seat(pp, planet, asc))]
            relation = {"en": f"{planet} and {maha_planet} sit {en}.", "ta": f"{planet} & {maha_planet}: {ta}.", "tone": tone}
        periods.append({
            "mahadasha": maha_planet,
            "bhukti": planet,
            "start": _fmt(start),
            "end": _fmt(bhukti["end"].date()),
            "relation": relation,
            "houses": rows,
        })

    return {
        "periods": periods,
        "sign_changes": sign_changes(segments, asc),
        "through": _fmt(horizon),
    }
