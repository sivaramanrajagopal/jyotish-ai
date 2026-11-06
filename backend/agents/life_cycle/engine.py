"""Life Cycle: the next years, theme by theme, on the House Links rules.

Dasha: a bhukti switches on the houses its lords rule and sit in (main), and the houses both
lords reach (shared), exactly as activation.py. Transit: a switched-on house is live when
Jupiter and Saturn each occupy or aspect it or its lord's sign (double transit), exactly as
upcoming.py. A theme is on when one of its key houses is switched on. Saturn is also
counted from the Moon (Sade Sati, Ardhashtama, Ashtama). How well a house gives is the
Reading tab's Navamsa fruit line. No score.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from agents.house_connections.activation import (
    FRUIT,
    RELATION,
    _distance,
    _seat,
    dasha_reasons,
    ordinal,
    shared_houses,
)
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.guidance import house_remedies
from agents.house_connections.tables import timeline_table
from agents.house_connections.upcoming import double_runs, sky_segments
from agents.life_cycle.saturn import overlapping, saturn_from_moon
from agents.life_cycle.themes import (
    CARE_NOTE_EN,
    CARE_NOTE_TA,
    MARRIED_NOTE_EN,
    MARRIED_NOTE_TA,
    THEMES,
)
from agents.nadi_agent import TZ, _fmt
from agents.reading_house import house_fruit
from dasha_core import generate_bhuktis, generate_dashas

SATURN_LOOKBACK_YEARS = 8
WINDOWS_SHOWN = 6
STATUS = {
    "live": ("On now, with transit", "இப்போது செயலில் (கோசாரத்துடன்)"),
    "waiting": ("Dasha on, transit not now", "தசை இயக்கம், கோசாரம் இப்போது இல்லை"),
    "quiet": ("Quiet now", "இப்போது அமைதி"),
}
STATUS_ORDER = {"live": 0, "waiting": 1, "quiet": 2}
BY = {
    "both": ("both lords", "இரு அதிபதிகளும்"),
    "bhukti": ("the bhukti lord", "புக்தி அதிபதி"),
    "maha": ("the mahadasha lord", "மகா தசை அதிபதி"),
}
DISCLAIMER_EN = (
    "Windows show when the dasha and the transit point at a part of life. "
    "Read them with the full chart and the client's situation."
)
DISCLAIMER_TA = "தசையும் கோசாரமும் ஒரு வாழ்க்கைப் பகுதியைச் சுட்டும் காலங்கள்; முழு ஜாதகத்துடன் சேர்த்துப் பார்க்கவும்."


def _main(planet: str, role: str, pp: dict, asc: int) -> set[int]:
    return {
        h for h, rows in dasha_reasons(planet, role, pp, asc).items()
        if any(r["level"] == "main" for r in rows)
    }


def _age(dob: str, on: date) -> int:
    born = date.fromisoformat(dob[:10])
    return on.year - born.year - ((on.month, on.day) < (born.month, born.day))


def _merge(runs: list[list[date]]) -> list[list[date]]:
    out: list[list[date]] = []
    for lo, hi in sorted(runs):
        if out and out[-1][1] + timedelta(days=1) >= lo:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


def _periods(chart: dict, as_of: date, end: date, segments: list[dict], houses: dict[int, dict]) -> list[dict]:
    """Every bhukti that overlaps as_of..end, with the houses it switches on and their live runs."""
    pp = chart.get("planet_positions") or {}
    asc = int((chart.get("ascendant") or {}).get("sign_index") or 0)
    dob = str((chart.get("birth_data") or {}).get("dob") or "")
    moon = (pp.get("Moon") or {}).get("longitude")
    if not dob or moon is None:
        return []
    out = []
    for maha in generate_dashas(float(moon), dob):
        if maha["end"].date() < as_of:
            continue
        if maha["start"].date() > end:
            break
        m_main = _main(maha["planet"], "maha", pp, asc)
        for b in generate_bhuktis(maha):
            start, stop = b["start"].date(), b["end"].date()
            if stop < as_of or start > end:
                continue
            md, bh = maha["planet"], b["planet"]
            b_main = _main(bh, "bhukti", pp, asc)
            shared = shared_houses(md, bh, pp, asc)
            lo, hi = max(start, as_of), min(stop, end)
            on = {}
            for h in sorted(m_main | b_main | shared):
                if h in shared or (h in m_main and h in b_main):
                    by = "both"
                elif h in b_main:
                    by = "bhukti"
                else:
                    by = "maha"
                on[h] = {
                    "by": by,
                    "runs": double_runs(segments, lo, hi, asc, h, houses[h]["lord_house"]),
                }
            relation = None
            if md != bh:
                en, ta, tone = RELATION[_distance(_seat(pp, md, asc), _seat(pp, bh, asc))]
                relation = {"en": f"{bh} and {md} sit {en}.", "ta": f"{bh} & {md}: {ta}.", "tone": tone}
            out.append({
                "mahadasha": md,
                "bhukti": bh,
                "start": start,
                "end": stop,
                "now": start <= as_of <= stop,
                "on": on,
                "relation": relation,
            })
    return out


def _fruit(chart: dict, h: int) -> dict:
    verdict = house_fruit(chart, h)
    tone, ta = FRUIT.get(verdict["fruit"], ("mixed", ""))
    return {"house": h, "ordinal": ordinal(h), "lord": verdict["lord"], "en": verdict["fruit"], "ta": ta, "tone": tone}


def _theme_windows(theme: dict, periods: list[dict], born: date | None, saturn: list[dict]) -> list[dict]:
    windows = []
    for p in periods:
        hits = {h: p["on"][h] for h in theme["key_houses"] if h in p["on"]}
        if not hits:
            continue
        if born and theme.get("min_age") and _age(born.isoformat(), p["end"]) < theme["min_age"]:
            continue
        if born and theme.get("max_age") and _age(born.isoformat(), p["start"]) > theme["max_age"]:
            continue
        runs = _merge([list(r) for v in hits.values() for r in v["runs"]])
        strongest = "both" if any(v["by"] == "both" for v in hits.values()) else (
            "bhukti" if any(v["by"] == "bhukti" for v in hits.values()) else "maha"
        )
        windows.append({
            "mahadasha": p["mahadasha"],
            "bhukti": p["bhukti"],
            "start": _fmt(p["start"]),
            "end": _fmt(p["end"]),
            "start_iso": p["start"].isoformat(),
            "end_iso": p["end"].isoformat(),
            "now": p["now"],
            "houses": [{
                "house": h,
                "ordinal": ordinal(h),
                "by": v["by"],
                "by_en": BY[v["by"]][0],
                "live": [{"start": _fmt(a), "end": _fmt(b)} for a, b in v["runs"]],
            } for h, v in hits.items()],
            "by": strongest,
            "live": [{"start": _fmt(a), "end": _fmt(b), "start_iso": a.isoformat(), "end_iso": b.isoformat()} for a, b in runs],
            "saturn": overlapping(saturn, p["start"], p["end"]),
            "relation": p["relation"],
        })
    return windows


def _status(windows: list[dict], as_of: date) -> tuple[str, dict | None]:
    cur = next((w for w in windows if w["now"]), None)
    if cur:
        live_now = next((r for r in cur["live"] if r["start_iso"] <= as_of.isoformat() <= r["end_iso"]), None)
        if live_now:
            return "live", live_now
        return "waiting", None
    return "quiet", None


def _next_live(windows: list[dict], as_of: date) -> dict | None:
    """The next transit-backed run, preferring a bhukti that reaches the key house itself."""
    today = as_of.isoformat()
    for wanted in (("both", "bhukti"), ("both", "bhukti", "maha")):
        for w in windows:
            if w["by"] not in wanted:
                continue
            for r in w["live"]:
                if r["start_iso"] > today:
                    return {**r, "mahadasha": w["mahadasha"], "bhukti": w["bhukti"]}
    return None


def compute_life_cycle(
    chart: dict,
    *,
    horizon_years: int = 10,
    as_of: date | None = None,
    married: bool | None = None,
) -> dict:
    when = as_of or datetime.now(TZ).date()
    end = when + timedelta(days=int(365.25 * horizon_years))
    pp = chart.get("planet_positions") or {}
    asc_row = chart.get("ascendant") or {}
    dob = str((chart.get("birth_data") or {}).get("dob") or "")
    born = date.fromisoformat(dob[:10]) if dob else None
    houses = analyze_all_houses(chart)

    segments = sky_segments(when - timedelta(days=int(365.25 * SATURN_LOOKBACK_YEARS)), end)
    moon_sign = (pp.get("Moon") or {}).get("sign_index")
    saturn = saturn_from_moon(segments, int(moon_sign), when, end) if moon_sign is not None else []
    periods = _periods(chart, when, end, segments, houses)
    remedies = house_remedies(chart, timeline_table(chart, when))

    themes = []
    for t in THEMES:
        age_now = _age(dob, when) if born else None
        if age_now is not None and t.get("max_age") and age_now > t["max_age"]:
            continue
        windows = _theme_windows(t, periods, born, saturn)
        status, live_now = _status(windows, when)
        label_en, label_ta = t["en"], t["ta"]
        notes = []
        if t["key"] == "marriage" and married:
            label_en, label_ta = t["married_en"], t["married_ta"]
            notes.append({"en": MARRIED_NOTE_EN, "ta": MARRIED_NOTE_TA})
        if t.get("care"):
            notes.append({"en": CARE_NOTE_EN, "ta": CARE_NOTE_TA})
        seen_lords: set[str] = set()
        theme_remedies = []
        for h in t["key_houses"]:
            r = remedies.get(h)
            if r and r["lord"] not in seen_lords:
                seen_lords.add(r["lord"])
                theme_remedies.append({**r, "house": h})
        upcoming = [w for w in windows if not w["now"]]
        themes.append({
            "key": t["key"],
            "label_en": label_en,
            "label_ta": label_ta,
            "key_houses": t["key_houses"],
            "support": t["support"],
            "care": bool(t.get("care")),
            "notes": notes,
            "fruit": [_fruit(chart, h) for h in t["key_houses"]],
            "status": {"key": status, "en": STATUS[status][0], "ta": STATUS[status][1]},
            "live_now": live_now,
            "next_live": _next_live(windows, when),
            "windows": [w for w in windows if w["now"]] + upcoming[:WINDOWS_SHOWN],
            "more_windows": max(0, len(upcoming) - WINDOWS_SHOWN),
            "remedies": theme_remedies,
        })
    themes.sort(key=lambda th: (
        STATUS_ORDER[th["status"]["key"]],
        (th["next_live"] or {}).get("start_iso", "9999"),
    ))

    now = next((p for p in periods if p["now"]), None)
    now_out = None
    if now:
        live = [
            {"house": h, "ordinal": ordinal(h), "until": _fmt(v["runs"][0][1])}
            for h, v in now["on"].items()
            if v["runs"] and v["runs"][0][0] <= when
        ]
        now_out = {
            "mahadasha": now["mahadasha"],
            "bhukti": now["bhukti"],
            "start": _fmt(now["start"]),
            "end": _fmt(now["end"]),
            "on": [{"house": h, "ordinal": ordinal(h), "by": v["by"], "by_en": BY[v["by"]][0]} for h, v in now["on"].items()],
            "live": live,
            "relation": now["relation"],
        }

    timeline = [{
        "mahadasha": p["mahadasha"],
        "bhukti": p["bhukti"],
        "start": _fmt(p["start"]),
        "end": _fmt(p["end"]),
        "now": p["now"],
        "on": sorted(p["on"]),
        "live": sorted(h for h, v in p["on"].items() if v["runs"]),
        "themes": [th["key"] for th in themes if any(h in p["on"] for h in th["key_houses"])],
        "relation": p["relation"],
    } for p in periods]

    return {
        "meta": {
            "as_of": when.isoformat(),
            "start": _fmt(when),
            "end": _fmt(end),
            "horizon_years": horizon_years,
            "lagna": asc_row.get("sign", ""),
            "moon_sign": (pp.get("Moon") or {}).get("sign", ""),
            "age": _age(dob, when) if born else None,
            "married": married,
            "method_en": (
                "Dasha switches a house on (the houses its lords rule and sit in, and houses both lords reach). "
                "Jupiter and Saturn together on the house or its lord's sign make it live. "
                "Saturn is also counted from the Moon."
            ),
            "disclaimer_en": DISCLAIMER_EN,
            "disclaimer_ta": DISCLAIMER_TA,
        },
        "now": now_out,
        "themes": themes,
        "saturn": saturn,
        "timeline": timeline,
    }
