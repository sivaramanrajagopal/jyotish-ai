"""House Links — chat narrator context, on the same rules as the House Links tab.

Compact by default (status of all 12 houses, exchanges, remedies, the coming bhuktis);
full reasons for the houses the user asks about. No scores.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from agents.house_connections.activation import compute_activation
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.guidance import exchange_meanings, house_remedies
from agents.house_connections.tables import CODE_ORDER, natal_table, timeline_table
from agents.house_connections.upcoming import compute_upcoming, double_runs, sky_segments
from agents.house_connections.themes import DISCLAIMER_EN
from agents.house_connections.yogas import detect_yogas
from agents.nadi_agent import TZ, _fmt

_HOUSE_LINKS_RE = re.compile(
    r"house\s*links?|house\s*connections?|lord\s*links?|"
    r"prediction\s*map|raja\s*yoga.*lord|dharma-karma|exchange|parivartana",
    re.I,
)
_HOUSE_NUM_RE = re.compile(
    r"\bh\s*(\d{1,2})\b|(\d{1,2})(?:st|nd|rd|th)\s+house|house\s*(\d{1,2})\b",
    re.I,
)
_THEME_HOUSES = {
    "marriage": 7, "partner": 7, "spouse": 7, "relationship": 7,
    "career": 10, "profession": 10, "job": 10, "karma": 10,
    "fortune": 9, "dharma": 9, "luck": 9, "bhagya": 9,
    "wealth": 2, "money": 2, "family": 2,
    "health": 6, "disease": 6,
    "home": 4, "mother": 4, "property": 4,
    "children": 5, "education": 5, "creativity": 5,
    "gains": 11, "income": 11, "profit": 11,
    "loss": 12, "expense": 12, "foreign": 12,
    "self": 1, "personality": 1, "lagna": 1,
}
CODE_WORDS = {
    "L": "this lord sits there", "H": "that lord sits here", "X": "exchange",
    "C": "lords together", "M": "mutual aspect", "A": "one-way aspect",
    "N": "star-lord link", "S": "same lord",
}

EXPLANATION_GUIDE = """HOW TO EXPLAIN A HOUSE (same rules as the House Links tab):
1. Lord and seat, then the fruit line (how well the house gives; from the lord's Navamsa sign).
2. Status now: Live (dasha on and Jupiter + Saturn on the house or its lord), Dasha on, Transit only, or Quiet.
3. Why the dasha reaches it: quote the dasha reasons below. "connected" reasons alone do not make it live.
4. Natal ties: quote the links and the connection codes.
5. If a remedy is listed, offer it as optional, with its timing. Never invent links, dates or scores."""


def _houses_from_message(message: str) -> set[int]:
    found: set[int] = set()
    if not message:
        return found
    for m in _HOUSE_NUM_RE.finditer(message):
        for g in m.groups():
            if g and 1 <= int(g) <= 12:
                found.add(int(g))
    lower = message.lower()
    for word, h in _THEME_HOUSES.items():
        if word in lower:
            found.add(h)
    return found


def _wants_detail(message: str) -> bool:
    if not message:
        return False
    return bool(_HOUSE_LINKS_RE.search(message) or _houses_from_message(message))


def _hs(houses) -> str:
    return ", ".join(f"H{h}" for h in houses) or "none"


def _card(row: dict, natal_row: dict, remedy: dict | None) -> list[str]:
    h = row["house"]
    lines = [
        f"--- H{h} {row['theme_en']} ({row['theme_ta']}) ---",
        f"{row['sign']} · lord {row['lord']} in H{row['lord_house']} · {row['fruit']['en']}",
        f"Status now: {row['status']['en']}"
        + (f" (until {row['transit']['double_until']})" if row["transit"].get("double_until") else ""),
    ]
    for r in row["dasha"]["reasons"]:
        tag = " (connected)" if r["level"] == "side" else ""
        lines.append(f"  dasha · {r['en']}{tag}")
    for t in row["transit"]["lines"]:
        lines.append(f"  transit · {t['en']}")
    for link in row["links"]:
        lines.append(f"  natal · {link['en']}")
    ties = [
        f"H{c['house']} {c['codes']} ({', '.join(CODE_WORDS[x] for x in c['codes'] if x in CODE_ORDER)})"
        for c in natal_row["connected"]
    ]
    if ties:
        lines.append("  connections · " + "; ".join(ties))
    if remedy:
        when = "; ".join(
            f"{p['label']} ({'now' if p['now'] else p['start']} to {p['end']})" for p in remedy["when"]
        ) or "any time"
        lines.append(
            f"  remedy · {remedy['why_en']} {remedy['mantra']} ×{remedy['count']}, {remedy['day']}, "
            f"deity {remedy['deity']}, charity {', '.join(remedy['charity'])}. Best in: {when}."
        )
    return lines


def house_connections_context_for_narrator(natal_chart: dict, user_message: str = "") -> str:
    try:
        today = datetime.now(TZ).date()
        houses = analyze_all_houses(natal_chart)
        yogas = detect_yogas(houses, natal_chart)
        act = compute_activation(natal_chart, houses, yogas, today)
        timeline = timeline_table(natal_chart, today)
        remedies = house_remedies(natal_chart, timeline)
        swaps = exchange_meanings(houses, timeline)
        natal = {r["house"]: r for r in natal_table(houses, natal_chart)}
        upcoming = compute_upcoming(natal_chart, houses, today)
    except Exception:
        return ""

    asc = int((natal_chart.get("ascendant") or {}).get("sign_index") or 0)
    rows = {r["house"]: r for r in act["rows"]}
    period = act.get("period")
    if period:
        end = datetime.fromisoformat(period["bhukti"]["end_iso"]).date()
        segments = sky_segments(today, end + timedelta(days=1))
        for h, r in rows.items():
            if r["status"]["key"] == "live":
                runs = double_runs(segments, today, end, asc, h, houses[h]["lord_house"])
                if runs:
                    r["transit"]["double_until"] = _fmt(runs[0][1])

    by_status: dict[str, list[int]] = {}
    for h, r in rows.items():
        by_status.setdefault(r["status"]["key"], []).append(h)

    lines = [
        "=== HOUSE CONNECTIONS (House Links tab rules) ===",
        f"DISCLAIMER: {DISCLAIMER_EN}",
        "Rules: a running lord switches on the houses it rules and sits in (main); a house both lords "
        "reach is shared. Live = main or shared AND Jupiter and Saturn each on the house or its lord's "
        "sign. Fruit = the house lord's Navamsa sign. There are no scores; never quote one.",
    ]
    if period:
        lines.append(
            f"Now: {period['mahadasha']['planet']} mahadasha (to {period['mahadasha']['end']}) / "
            f"{period['bhukti']['planet']} bhukti (to {period['bhukti']['end']})."
        )
        if act.get("relation"):
            lines.append(f"  {act['relation']['en']}")
    lines.append(
        "  Live: " + (", ".join(
            f"H{h}" + (f" until {rows[h]['transit']['double_until']}" if rows[h]["transit"].get("double_until") else "")
            for h in by_status.get("live", [])
        ) or "none")
    )
    lines.append(f"  Dasha on, transit not now: {_hs(by_status.get('waiting', []))}")
    lines.append(f"  Transit only: {_hs(by_status.get('sky', []))}")

    lines.extend(["", "ALL HOUSES (lord · seat · fruit · status):"])
    for h in range(1, 13):
        r = rows[h]
        lines.append(f"  H{h} {r['theme_en']}: lord {r['lord']} in H{r['lord_house']} · {r['fruit']['en']} · {r['status']['en']}")

    if swaps:
        lines.extend(["", "SIGN EXCHANGES:"])
        for s in swaps:
            a, b = s["houses"]
            active = "; ".join(f"{p['label']} ({'now' if p['now'] else p['start']} to {p['end']})" for p in s["active"])
            lines.append(f"  {s['name_en']} H{a}–H{b}: {s['meaning_en']} Active in: {active or 'none ahead'}.")

    if remedies:
        lines.extend(["", "REMEDIES (houses whose fruit is thinner or weak; optional, one per lord):"])
        seen: set[str] = set()
        for h, r in sorted(remedies.items()):
            if r["lord"] in seen:
                continue
            seen.add(r["lord"])
            owned = [x for x, rr in remedies.items() if rr["lord"] == r["lord"]]
            lines.append(f"  {r['lord']} (for {_hs(sorted(owned))}): {r['mantra']} ×{r['count']}, {r['day']}, "
                         f"charity {', '.join(r['charity'])}")

    if upcoming:
        lines.extend(["", "COMING BHUKTIS (main houses · double-transit windows):"])
        for p in upcoming["periods"]:
            parts = []
            for hr in p["houses"]:
                win = ", ".join(f"{w['start']}–{w['end']}" for w in hr["windows"]) or "no window"
                parts.append(f"H{hr['house']} [{win}]")
            lines.append(f"  {p['bhukti']} bhukti in {p['mahadasha']} ({p['start']} to {p['end']}): " + "; ".join(parts))

    if _wants_detail(user_message):
        focus = _houses_from_message(user_message) or {7, 9, 10}
        lines.extend(["", EXPLANATION_GUIDE, "", f"DETAIL for {_hs(sorted(focus))} (cite exactly):"])
        for h in sorted(focus):
            lines.extend(_card(rows[h], natal[h], remedies.get(h)))
    else:
        lines.extend(["", "Ask about a specific house for its full reasons and connections."])
    return "\n".join(lines)
