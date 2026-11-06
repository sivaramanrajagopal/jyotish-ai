"""Plain tables for House Links: natal house connections, dasha lords, and today's transits.

Natal codes, one per way two houses are tied through their lords:
  L  this house's lord sits in that house
  H  that house's lord sits in this house
  X  the two lords exchange signs
  C  the two lords sit together
  M  the two lords aspect each other
  A  one lord aspects the other, one way
  N  one lord sits in the other lord's star (a node star lord acts through its sign lord)
  S  one planet rules both houses

Dasha "both" windows use the double-transit rule from activation.py, day by day.
"""

from __future__ import annotations

from datetime import date, timedelta

from agents.bhavat_bhavam.core import _lords_linked
from agents.house_connections.activation import dasha_reasons
from agents.house_connections.core import nakshatra_lord_for
from agents.house_connections.edges import exchanges
from agents.natal_agent import SIGN_LORDS
from agents.house_connections.upcoming import MAX_YEARS, double_runs, sign_changes, sky_segments
from agents.nadi_agent import _fmt
from agents.transit_score_agent import _planet_aspects

CODE_ORDER = "LHXCMANS"
SKY_ORDER = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _star_lords(planet: str, pp: dict) -> set[str]:
    """The planet's star lord; a node star lord acts through its sign lord."""
    star = nakshatra_lord_for(pp.get(planet) or {})
    if not star or star == planet:
        return set()
    if star in ("Rahu", "Ketu"):
        return {SIGN_LORDS.get((pp.get(star) or {}).get("sign", ""), "")} - {"", planet}
    return {star}


def natal_table(houses: dict[int, dict], chart: dict) -> list[dict]:
    pp = chart.get("planet_positions") or {}
    asc = int((chart.get("ascendant") or {}).get("sign_index") or 0)
    codes: dict[int, dict[int, set[str]]] = {h: {} for h in range(1, 13)}

    def tie(a: int, b: int, code: str) -> None:
        if a != b:
            codes[a].setdefault(b, set()).add(code)

    swaps = set(exchanges(houses))
    for h in range(1, 13):
        lh = houses[h]["lord_house"]
        if lh:
            tie(h, lh, "L")
            tie(lh, h, "H")
    for a, b in swaps:
        tie(a, b, "X")
        tie(b, a, "X")
    for a in range(1, 13):
        for b in range(a + 1, 13):
            la, lb = houses[a]["lord"], houses[b]["lord"]
            if la == lb:
                tie(a, b, "S")
                tie(b, a, "S")
                continue
            links = _lords_linked(la, lb, pp, asc)
            if "conjunction" in links:
                tie(a, b, "C")
                tie(b, a, "C")
            one = f"{la} aspects {lb}" in links
            other = f"{lb} aspects {la}" in links
            if one or other:
                code = "M" if one and other else "A"
                tie(a, b, code)
                tie(b, a, code)
            if la in _star_lords(lb, pp) or lb in _star_lords(la, pp):
                tie(a, b, "N")
                tie(b, a, "N")

    rows = []
    for h in range(1, 13):
        rows.append({
            "house": h,
            "theme_en": houses[h]["theme_en"],
            "lord": houses[h]["lord"],
            "lord_house": houses[h]["lord_house"],
            "connected": [
                {"house": other, "codes": "".join(c for c in CODE_ORDER if c in found)}
                for other, found in sorted(codes[h].items())
            ],
        })
    return rows


def _split(planet: str, role: str, pp: dict, asc: int) -> tuple[list[int], list[int]]:
    reasons = dasha_reasons(planet, role, pp, asc)
    main = sorted(h for h, rows in reasons.items() if any(r["level"] == "main" for r in rows))
    side = sorted(h for h in reasons if h not in main)
    return main, side


def _both(segments, start: date, end: date, as_of: date, houses, asc, main, side) -> list[dict]:
    out = []
    for level, group in (("main", main), ("side", side)):
        for h in group:
            for lo, hi in double_runs(segments, start, end, asc, h, houses[h]["lord_house"]):
                out.append({
                    "house": h,
                    "level": level,
                    "now": lo <= as_of,
                    "start": _fmt(lo),
                    "end": _fmt(hi),
                    "start_iso": lo.isoformat(),
                })
    out.sort(key=lambda b: (b["start_iso"], b["level"] != "main", b["house"]))
    return out


def dasha_table(
    chart: dict,
    houses: dict[int, dict],
    activation: dict | None,
    upcoming: dict | None,
    as_of: date,
    segments: list[dict],
    horizon: date,
) -> list[dict]:
    pp = chart.get("planet_positions") or {}
    asc = int((chart.get("ascendant") or {}).get("sign_index") or 0)
    rows: list[dict] = []
    period = (activation or {}).get("period")
    if period:
        for key in ("mahadasha", "bhukti"):
            span = period[key]
            main, side = _split(span["planet"], "maha" if key == "mahadasha" else "bhukti", pp, asc)
            end = min(date.fromisoformat(span["end_iso"]), horizon)
            rows.append({
                "planet": span["planet"],
                "label": key,
                "when": f"to {span['end']}",
                "current": True,
                "activated": main,
                "connected": side,
                "both": _both(segments, as_of, end, as_of, houses, asc, main, side),
            })
    for p in (upcoming or {}).get("periods") or []:
        main, side = _split(p["bhukti"], "bhukti", pp, asc)
        start = date.fromisoformat(p["start_iso"])
        end = min(date.fromisoformat(p["end_iso"]), horizon)
        rows.append({
            "planet": p["bhukti"],
            "label": f"bhukti in {p['mahadasha']} mahadasha",
            "when": f"{p['start']} to {p['end']}",
            "current": False,
            "activated": main,
            "connected": side,
            "both": _both(segments, start, end, as_of, houses, asc, main, side) if start <= horizon else [],
        })
    return rows


def transit_table(houses: dict[int, dict], activation: dict | None, changes: list[dict]) -> list[dict]:
    sky = (activation or {}).get("sky") or {}
    rows = []
    for planet in SKY_ORDER:
        now = sky.get(planet)
        if not now:
            continue
        at = now["house"]
        aspects = sorted(h for h in _planet_aspects(planet, at) if h != at)
        reach = {at, *aspects}
        lords = sorted(h for h in range(1, 13) if houses[h]["lord_house"] in reach)
        nxt = next((c for c in changes if c["planet"] == planet), None)
        rows.append({
            "planet": planet,
            "sign": now["sign"],
            "house": at,
            "retrograde": now["retrograde"],
            "aspects": aspects,
            "lords_of": lords,
            "next": {"sign": nxt["sign"], "house": nxt["house"], "date": nxt["date"]} if nxt else None,
        })
    return rows


def compute_tables(
    chart: dict,
    houses: dict[int, dict],
    activation: dict | None,
    upcoming: dict | None,
    as_of: date | None = None,
) -> dict:
    when = as_of or date.fromisoformat((activation or {}).get("as_of") or date.today().isoformat())
    asc = int((chart.get("ascendant") or {}).get("sign_index") or 0)
    ends = [date.fromisoformat(p["end_iso"]) for p in (upcoming or {}).get("periods") or []]
    period = (activation or {}).get("period")
    if period:
        ends.append(date.fromisoformat(period["mahadasha"]["end_iso"]))
    horizon = min(max(ends, default=when), when + timedelta(days=int(365.25 * MAX_YEARS)))
    segments = sky_segments(when, horizon)
    live_until = {}
    for h in range(1, 13):
        runs = double_runs(segments, when, horizon, asc, h, houses[h]["lord_house"])
        if runs and runs[0][0] <= when:
            live_until[h] = _fmt(runs[0][1])
    return {
        "live_until": live_until,
        "natal": natal_table(houses, chart),
        "dasha": dasha_table(chart, houses, activation, upcoming, when, segments, horizon),
        "transit": transit_table(houses, activation, sign_changes(segments, asc)),
    }
