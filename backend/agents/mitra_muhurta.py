"""
Mitra muhurta for debt repayment.

Traditional pairing, both signs of Mars:
  Ashwini nakshatra with Mesha (Aries) lagna
  Anuradha (Anusham) nakshatra with Vrischika (Scorpio) lagna

Windows are the overlap of those two clocks at a panchangam location.
Lahiri sidereal, Swiss Ephemeris. Not a promise of repayment.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import ephemeris as swe

from agents.panchangam_agent import LOCATIONS, _from_jd, _moon_lon, _to_jd

NAK_ARC = 360.0 / 27.0
MIN_WINDOW_JD = 1.0 / 1440.0  # one minute
STEP_JD = 8.0 / 1440.0

PAIRS = (
    {
        "id": "ashwini_mesha",
        "nakshatra_index": 0,
        "nakshatra": "Ashwini",
        "nakshatra_tamil": "Ashwini",
        "lagna_index": 0,
        "lagna": "Mesha",
        "lagna_en": "Aries",
    },
    {
        "id": "anusham_vrischika",
        "nakshatra_index": 16,
        "nakshatra": "Anuradha",
        "nakshatra_tamil": "Anusham",
        "lagna_index": 7,
        "lagna": "Vrischika",
        "lagna_en": "Scorpio",
    },
)


def _bucket(lon: float, count: int) -> int:
    return int((lon % 360.0) / (360.0 / count)) % count


def _asc_lon(jd: float, lat: float, lon: float) -> float:
    _, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    return ascmc[0] % 360.0


def _search_change(fn, count: int, jd_lo: float, jd_hi: float) -> float:
    """JD where the bucket of fn changes between jd_lo and jd_hi."""
    left_b = _bucket(fn(jd_lo), count)
    lo, hi = jd_lo, jd_hi
    for _ in range(40):
        if hi - lo <= 1.0 / 86400.0:
            break
        mid = (lo + hi) / 2
        if _bucket(fn(mid), count) == left_b:
            lo = mid
        else:
            hi = mid
    return hi


def _index_windows(fn, count: int, wanted: int, jd_start: float, jd_end: float) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    jd = jd_start
    cur = _bucket(fn(jd), count)
    win_start = jd if cur == wanted else None
    while jd < jd_end:
        nxt = min(jd + STEP_JD, jd_end)
        nxt_b = _bucket(fn(nxt), count)
        if cur == wanted and nxt_b != wanted:
            edge = _search_change(fn, count, jd, nxt)
            if win_start is not None and edge - win_start >= MIN_WINDOW_JD:
                out.append((win_start, edge))
            win_start = None
        elif cur != wanted and nxt_b == wanted:
            win_start = _search_change(fn, count, jd, nxt)
        jd = nxt
        cur = nxt_b
    if win_start is not None and jd_end - win_start >= MIN_WINDOW_JD:
        out.append((win_start, jd_end))
    return out


def _overlaps(nak_wins, lag_wins) -> list[tuple[float, float]]:
    found: list[tuple[float, float]] = []
    for n0, n1 in nak_wins:
        for l0, l1 in lag_wins:
            start, end = max(n0, l0), min(n1, l1)
            if end - start >= MIN_WINDOW_JD:
                found.append((start, end))
    found.sort()
    return found


def compute_mitra_muhurta(location: str = "Chennai", month: str | None = None) -> dict:
    """All Mitra windows in a calendar month for one supported city."""
    if location not in LOCATIONS:
        raise ValueError(f"Unknown location '{location}'.")
    loc = LOCATIONS[location]
    tz = ZoneInfo(loc["tz"])
    if month:
        try:
            year_s, mon_s = month.split("-")
            first = date(int(year_s), int(mon_s), 1)
            month = first.strftime("%Y-%m")
        except ValueError as exc:
            raise ValueError("Invalid month. Use YYYY-MM.") from exc
    else:
        today = datetime.now(tz).date()
        first = date(today.year, today.month, 1)
        month = first.strftime("%Y-%m")
    last_day = calendar.monthrange(first.year, first.month)[1]
    start_dt = datetime(first.year, first.month, 1, 0, 0, 0, tzinfo=tz)
    end_dt = datetime(first.year, first.month, last_day, 0, 0, 0, tzinfo=tz) + timedelta(days=1)
    jd0, jd1 = _to_jd(start_dt), _to_jd(end_dt)

    def moon(jd: float) -> float:
        return _moon_lon(jd)

    def asc(jd: float) -> float:
        return _asc_lon(jd, loc["lat"], loc["lon"])

    windows = []
    for pair in PAIRS:
        nak_wins = _index_windows(moon, 27, pair["nakshatra_index"], jd0, jd1)
        lag_wins = _index_windows(asc, 12, pair["lagna_index"], jd0, jd1)
        for start_jd, end_jd in _overlaps(nak_wins, lag_wins):
            start = _from_jd(start_jd, tz)
            end = _from_jd(end_jd, tz)
            mid_jd = (start_jd + end_jd) / 2
            windows.append({
                "id": pair["id"],
                "date": start.date().isoformat(),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "nakshatra": pair["nakshatra"],
                "nakshatra_tamil": pair["nakshatra_tamil"],
                "lagna": pair["lagna"],
                "lagna_en": pair["lagna_en"],
                "label": f"{pair['nakshatra_tamil']} · {pair['lagna']} lagna",
                "nakshatra_index": _bucket(moon(mid_jd), 27),
                "lagna_index": _bucket(asc(mid_jd), 12),
            })
    windows.sort(key=lambda row: row["start"])
    return {
        "location": location,
        "timezone": loc["tz"],
        "month": month,
        "purpose": "Traditional timing used for paying back a loan or debt. Both signs belong to Mars.",
        "pairs": [
            {
                "id": p["id"],
                "nakshatra": p["nakshatra"],
                "nakshatra_tamil": p["nakshatra_tamil"],
                "lagna": p["lagna"],
                "lagna_en": p["lagna_en"],
            }
            for p in PAIRS
        ],
        "windows": windows,
        "count": len(windows),
    }
