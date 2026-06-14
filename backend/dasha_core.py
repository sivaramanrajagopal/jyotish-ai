"""
dasha_core.py — canonical Vimshottari Mahadasha / Bhukti math.

Single source of truth for jyotish-ai and the Mundane Astrology dashboard
(dasha_logic.py imports this module). Keep calculation logic here only.
"""

from __future__ import annotations

import datetime
from collections import OrderedDict
from typing import Optional

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3

DASA_DURATIONS: OrderedDict[str, int] = OrderedDict([
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10),
    ("Mars", 7), ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
])

PLANET_FRIENDSHIPS: dict[str, dict[str, set[str]]] = {
    "Sun":     {"friends": {"Moon", "Mars", "Jupiter"},          "enemies": {"Venus", "Saturn", "Rahu", "Ketu"}},
    "Moon":    {"friends": {"Sun", "Mercury"},                  "enemies": {"Rahu", "Ketu"}},
    "Mercury": {"friends": {"Sun", "Venus"},                    "enemies": {"Moon"}},
    "Venus":   {"friends": {"Mercury", "Saturn"},               "enemies": {"Sun", "Moon", "Rahu", "Ketu"}},
    "Mars":    {"friends": {"Sun", "Moon", "Jupiter"},           "enemies": {"Mercury", "Rahu", "Ketu"}},
    "Jupiter": {"friends": {"Sun", "Moon", "Mars"},              "enemies": {"Mercury", "Venus", "Rahu", "Ketu"}},
    "Saturn":  {"friends": {"Mercury", "Venus", "Rahu", "Ketu"},  "enemies": {"Sun", "Moon", "Mars"}},
    "Rahu":    {"friends": {"Venus", "Saturn"},                 "enemies": {"Sun", "Moon", "Mars"}},
    "Ketu":    {"friends": {"Mars", "Jupiter"},                 "enemies": {"Sun", "Moon", "Venus"}},
}

_NAK_LEN = 360.0 / 27


def get_nakshatra(longitude: float) -> tuple[str, int, int]:
    """Return (nakshatra_name, pada 1–4, index 0–26)."""
    idx = int((float(longitude) % 360) / _NAK_LEN)
    idx = min(idx, 26)
    pada = int(((float(longitude) % _NAK_LEN) / (_NAK_LEN / 4))) + 1
    return NAKSHATRAS[idx], min(pada, 4), idx


def get_relationship(dasha_lord: str, bhukti_lord: str) -> str:
    if dasha_lord == bhukti_lord:
        return "Same"
    rel = PLANET_FRIENDSHIPS.get(dasha_lord, {})
    if bhukti_lord in rel.get("friends", set()):
        return "Friend"
    if bhukti_lord in rel.get("enemies", set()):
        return "Enemy"
    return "Neutral"


def generate_dashas(moon_long: float, birth_date_str: str) -> list[dict]:
    """Full Mahadasha timeline from birth (3 × 9 lord cycles)."""
    _, _, idx = get_nakshatra(moon_long)
    portion_done = (moon_long % _NAK_LEN) / _NAK_LEN
    start_lord = NAKSHATRA_LORDS[idx]
    lords = list(DASA_DURATIONS.keys())
    start_i = lords.index(start_lord)

    birth_dt = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d")
    dashas: list[dict] = []
    current = birth_dt

    for i in range(3 * len(lords)):
        j = (start_i + i) % len(lords)
        planet = lords[j]
        full = float(DASA_DURATIONS[planet])
        years = full * (1.0 - portion_done) if i == 0 else full
        end = current + datetime.timedelta(days=years * 365.25)
        dashas.append({
            "planet": planet,
            "start": current,
            "end": end,
            "years": round(years, 2),
        })
        current = end

    return dashas


def generate_bhuktis(dasha: dict) -> list[dict]:
    """All 9 Bhukti sub-periods within one Mahadasha."""
    lords = list(DASA_DURATIONS.keys())
    m_lord = dasha["planet"]
    m_years = dasha["years"]
    start_i = lords.index(m_lord)
    current = dasha["start"]
    bhuktis: list[dict] = []

    for i in range(len(lords)):
        b_lord = lords[(start_i + i) % len(lords)]
        b_years = (DASA_DURATIONS[b_lord] / 120.0) * m_years
        end = current + datetime.timedelta(days=b_years * 365.25)
        bhuktis.append({
            "planet": b_lord,
            "start": current,
            "end": end,
            "years": round(b_years, 3),
        })
        current = end

    return bhuktis


def find_current_dasha_bhukti(
    moon_long: float,
    birth_date: str,
    current_dt: Optional[datetime.datetime] = None,
) -> tuple[list[dict], dict, list[dict], dict]:
    """
    Returns (all_dashas, current_mahadasha, all_bhuktis, current_bhukti).
    """
    if current_dt is None:
        current_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    dashas = generate_dashas(moon_long, birth_date)
    cur_dasha = next(
        (d for d in dashas if d["start"] <= current_dt < d["end"]),
        dashas[-1],
    )
    bhuktis = generate_bhuktis(cur_dasha)
    cur_bhukti = next(
        (b for b in bhuktis if b["start"] <= current_dt < b["end"]),
        bhuktis[-1],
    )
    return dashas, cur_dasha, bhuktis, cur_bhukti


def fmt_period(dt: datetime.datetime) -> str:
    return dt.strftime("%b %Y")


def fmt_period_day(dt: datetime.datetime) -> str:
    return dt.strftime("%d %b %Y")


def format_bhukti_table(
    dasha: dict,
    *,
    include_mahadasha_header: bool = True,
) -> str:
    """
    Markdown pipe table for chat display. Uses antardasha_sequence from dasha dict.
    """
    md = dasha.get("mahadasha") or {}
    bh = dasha.get("bhukti") or {}
    seq = dasha.get("antardasha_sequence") or []
    if not seq:
        return "(Dasha table not available — recalculate chart on Home.)"

    lines = []
    if include_mahadasha_header and md.get("planet"):
        lines.append(
            f"**Mahadasha:** {md['planet']} ({md.get('start', '—')} – {md.get('end', '—')})"
        )
        if bh.get("planet"):
            lines.append(
                f"**Current Bhukti:** {bh['planet']} ({bh.get('start', '—')} – {bh.get('end', '—')})"
            )
        lines.append("")

    lines.append("| Bhukti (Planet) | Start | End | Years | Status |")
    lines.append("|-----------------|-------|-----|-------|--------|")
    for row in seq:
        planet = row.get("planet", "?")
        is_current = planet == bh.get("planet")
        status = "← **current**" if is_current else ""
        years = row.get("years", "")
        if isinstance(years, (int, float)):
            years = f"{years:.2f}"
        lines.append(
            f"| {planet} | {row.get('start', '—')} | {row.get('end', '—')} | {years} | {status} |"
        )
    return "\n".join(lines)


def format_next_mahadashas_block(dasha: dict) -> str:
    """Plain-text block for LLM — current MD + next 5 Mahadashas with exact dates."""
    md = dasha.get("mahadasha") or {}
    lines: list[str] = []
    if md.get("planet"):
        lines.append(
            f"  CURRENT Mahadasha: {md['planet']} — {md.get('start', '—')} – {md.get('end', '—')} "
            f"({md.get('remaining_years', '?')} yrs remaining)"
        )
    next_list = dasha.get("next_dashas") or []
    if not next_list:
        return "\n".join(lines) if lines else "  (not available — recalculate chart on Home)"
    for i, d in enumerate(next_list):
        prefix = "NEXT Mahadasha (1st after current)" if i == 0 else f"  Then Mahadasha #{i + 1}"
        lines.append(
            f"  {prefix}: {d.get('planet', '?')} — {d.get('start', '—')} – {d.get('end', '—')} "
            f"({d.get('years', '?')} yrs)"
        )
    return "\n".join(lines)


def format_upcoming_bhuktis_block(dasha: dict) -> str:
    """Plain-text block — current + next 3 Bhuktis within current Mahadasha only."""
    bh = dasha.get("bhukti") or {}
    lines: list[str] = []
    if bh.get("planet"):
        lines.append(
            f"  CURRENT Bhukti (sub-period): {bh['planet']} — {bh.get('start', '—')} – {bh.get('end', '—')} "
            f"({bh.get('remaining_months', '?')} months left)"
        )
    for d in dasha.get("upcoming_bhuktis") or []:
        lines.append(
            f"  Upcoming Bhukti: {d.get('planet', '?')} — {d.get('start', '—')} – {d.get('end', '—')}"
        )
    if not lines:
        return "  (not available)"
    lines.append("  (Bhuktis are sub-periods INSIDE the current Mahadasha — not the same as next Mahadasha.)")
    return "\n".join(lines)


def format_mahadasha_timeline_table(dasha: dict) -> str:
    """Markdown table: current + next Mahadashas."""
    md = dasha.get("mahadasha") or {}
    rows: list[dict] = []
    if md.get("planet"):
        rows.append({
            "planet": md["planet"],
            "start": md.get("start", "—"),
            "end": md.get("end", "—"),
            "years": md.get("years", "—"),
            "status": "← **current**",
        })
    for d in dasha.get("next_dashas") or []:
        rows.append({
            "planet": d.get("planet", "?"),
            "start": d.get("start", "—"),
            "end": d.get("end", "—"),
            "years": d.get("years", "—"),
            "status": "next" if len(rows) == 1 else "",
        })
    if not rows:
        return "(Mahadasha timeline not available — recalculate chart on Home.)"

    lines = [
        "| Mahadasha (Planet) | Start | End | Years | Status |",
        "|--------------------|-------|-----|-------|--------|",
    ]
    for row in rows:
        years = row["years"]
        if isinstance(years, (int, float)):
            years = f"{years:.2f}"
        lines.append(
            f"| {row['planet']} | {row['start']} | {row['end']} | {years} | {row['status']} |"
        )
    return "\n".join(lines)


def format_full_dasha_cycle_markdown(dasha: dict) -> str:
    """
    High-level Vimshottari overview for chat: Mahadasha roadmap + current-MD bhuktis.
    Two markdown tables — copy exactly when user asks for full dasa/bhukti cycle.
    """
    md = dasha.get("mahadasha") or {}
    if not md.get("planet"):
        return "(Full Dasa cycle not available — recalculate chart on Home.)"

    nak = dasha.get("nakshatra", "—")
    pada = dasha.get("pada", "—")
    birth_lord = dasha.get("birth_nakshatra_lord", "—")
    balance = dasha.get("balance_at_birth_years", "—")

    parts = [
        f"**Vimshottari Dasa–Bhukti overview** — Moon nakshatra **{nak}** (pada {pada}), "
        f"birth dasha lord **{birth_lord}**, balance at birth **{balance}** yrs.",
        "",
        "**Mahadasha cycle (major periods)**",
        format_mahadasha_timeline_table(dasha),
        "",
        f"**Bhuktis within current {md['planet']} Mahadasha (sub-periods)**",
        format_bhukti_table(dasha, include_mahadasha_header=False),
    ]
    return "\n".join(parts)
