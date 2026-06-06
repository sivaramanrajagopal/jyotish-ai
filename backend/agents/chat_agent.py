"""
chat_agent.py
=============
Multi-turn Vedic astrology chat using OpenAI.
The user's full natal chart is injected as system context so every
answer is grounded in their specific chart.
"""

from __future__ import annotations

import datetime
import os
from typing import Optional

from openai import OpenAI
from agents.panchangam_agent import calculate_panchangam, LOCATIONS
from agents.tara_engine import (
    compute_all as compute_personal_panchangam,
    compute_tara_balam,
    _dt_to_jd, _moon_longitude, _nak_index,
    NAKSHATRAS, TARA_TABLE,
)
from agents.transit_score_agent import (
    score_all_houses,
    compact_gochara_summary,
    dasha_transit_correlation,
)

MODEL  = "gpt-4o-mini"
TOKENS = 800   # per reply — keep responses concise

SYSTEM_TEMPLATE = """\
You are Jyotish AI — a classical Vedic astrology advisor (Parashari system, \
Lahiri ayanamsa, Whole Sign houses, Vimshottari Dasha).

You are speaking with {name}. Their natal chart and today's Panchangam are below. \
Answer their questions with specific, chart-grounded insights. \
Be warm, direct, and concise (3–5 sentences per answer). \
Name specific planets, signs, houses, or dashas from their chart. \
Never give vague generic advice. Never add disclaimers. \
When discussing Dasha/Bhukti sequences, always refer to the antardasha table provided — do not guess.

=== {name}'s NATAL CHART ===
Ascendant  : {ascendant} (nakshatra: {asc_nak}, pada {asc_pada})
Sun Sign   : {sun_sign} ({sun_nak})
Moon Sign  : {moon_sign} ({moon_nak})
Navamsa Asc: {navamsa_asc}
Yogas      : {yogas}

PLANETS:
{planets}

CURRENT DASHA:
Mahadasha : {maha_planet} ({maha_start}–{maha_end}, {maha_rem} yrs left) — {maha_focus}
Bhukti    : {bhukti_planet} ({bhukti_start}–{bhukti_end}, {bhukti_rem} months left) — {bhukti_trigger}

FULL ANTARDASHA SEQUENCE (all bhuktis within {maha_planet} Mahadasha, in order):
{antardasha}

=== TODAY'S PANCHANGAM ({today} · {location}) ===
Vaaram    : {vaaram} (lord: {vaaram_lord})
Tithi     : {tithi_paksha} {tithi}
Nakshatra : {nakshatra} (lord: {nakshatra_lord})
Yogam     : {yogam}
Karanam   : {karanam}
Rahu Kalam: {rahu_start} – {rahu_end}

=== PERSONAL PANCHANGAM ===
Natal Moon Nakshatra : {natal_nak}
Today's Moon         : {today_nak} in {today_rasi}
Tara Balam           : {tara_name} (Tara {tara_pos}) — {tara_nature} · {tara_meaning}
Chandrabalam         : {cb_status} (house {cb_house} from natal Moon)
Chandra Ashtama      : {ashtama_status}

=== 7-DAY PANCHANGAM OUTLOOK ({location}) ===
(Use this to answer questions about panchangam for upcoming dates)
{week_panch}

=== TARA BALAM CALENDAR — {tara_month} ===
(GOOD = benefic tara, BAD = malefic, ~ = neutral Janma)
Use this table to give EXACT dates when asked about good/bad days.
{tara_calendar}
"""


def _build_tara_calendar(natal_nak_index: int, year: int, month: int,
                         timezone: str = "Asia/Kolkata") -> tuple[str, str]:
    """
    Compute Tara Balam for every day of the given month.
    Returns (month_label, calendar_block_string).
    """
    from zoneinfo import ZoneInfo
    import calendar as cal_mod

    tz = ZoneInfo(timezone)
    days_in_month = cal_mod.monthrange(year, month)[1]
    month_name = datetime.date(year, month, 1).strftime("%B %Y")

    lines = []
    for day in range(1, days_in_month + 1):
        dt = datetime.datetime(year, month, day, 6, 0, 0, tzinfo=tz)
        jd  = _dt_to_jd(dt)
        lon = _moon_longitude(jd)
        nak = _nak_index(lon)
        tara = compute_tara_balam(natal_nak_index, nak)
        nature = tara["nature"]
        marker = "GOOD" if nature == "benefic" else ("BAD " if nature == "malefic" else "~   ")
        lines.append(
            f"  {month_name[:3]} {day:02d} [{marker}] "
            f"{tara['name']:<12} (Tara {tara['position']}) "
            f"Moon in {NAKSHATRAS[nak]}"
        )

    return month_name, "\n".join(lines)


def _build_system(natal_chart, location: str = "Chennai") -> str:
    """Build the system prompt from the natal chart response + today's panchangam."""
    chart: dict = natal_chart if isinstance(natal_chart, dict) else {}
    planets = chart.get("planet_positions", {})
    asc     = chart.get("ascendant", {})
    yogas   = [y["name"] for y in chart.get("yogas", []) if isinstance(y, dict)]
    nav_asc = chart.get("navamsa_ascendant", {})
    birth   = chart.get("birth_data", {})
    dasha   = chart.get("dasha", {})
    md      = dasha.get("mahadasha", {}) if dasha else {}
    bh      = dasha.get("bhukti", {})    if dasha else {}
    seq     = dasha.get("antardasha_sequence", []) if dasha else []

    planet_lines = []
    for name, p in planets.items():
        if not isinstance(p, dict):
            continue
        retro = " ℞" if p.get("retrograde") else ""
        vargo = " [Vargottama]" if p.get("vargottama") else ""
        planet_lines.append(
            f"  {name}: {p.get('sign')} H{p.get('house')} "
            f"{p.get('nakshatra')} P{p.get('pada')} "
            f"{p.get('degree_in_sign', 0):.1f}°{retro}{vargo}"
        )

    # Full antardasha sequence
    antardasha_lines = []
    for b in seq:
        if not isinstance(b, dict):
            continue
        planet = b.get("planet", "?")
        is_cur = planet == bh.get("planet")
        antardasha_lines.append(
            f"  {'→ ' if is_cur else '  '}{planet}: {b.get('start','')} – {b.get('end','')}"
            + (" ← current" if is_cur else "")
        )

    # ── helpers ──────────────────────────────────────────────────────────────
    def _fmt_iso(iso_str: str | None) -> str:
        """Format an ISO timestamp to human-readable IST time."""
        if not iso_str:
            return "—"
        try:
            from dateutil.parser import parse as _dp
            from zoneinfo import ZoneInfo as _ZI
            return _dp(iso_str).astimezone(_ZI("Asia/Kolkata")).strftime("%I:%M %p IST")
        except Exception:
            return iso_str

    # Today's panchangam
    today = datetime.date.today().isoformat()
    panch: dict = {}
    loc = location if location in LOCATIONS else (next(iter(LOCATIONS)) if LOCATIONS else "")
    if loc:
        try:
            panch = calculate_panchangam(today, loc)
        except Exception as e:
            print(f"[chat_agent] panchangam error: {e}")

    # 7-day panchangam outlook (for questions about upcoming dates)
    _week_panch = ""
    if loc:
        try:
            import contextlib as _cl, io as _io
            lines = []
            for i in range(1, 8):
                d = (datetime.date.today() + datetime.timedelta(days=i)).isoformat()
                with _cl.redirect_stdout(_io.StringIO()), _cl.redirect_stderr(_io.StringIO()):
                    p = calculate_panchangam(d, loc)
                rahu = f"{_fmt_iso(p.get('rahu_kalam_start'))}–{_fmt_iso(p.get('rahu_kalam_end'))}"
                lines.append(
                    f"  {d}  {p.get('vaaram_name',''):<14} "
                    f"{p.get('tithi_paksha','')} {p.get('tithi_name',''):<14} "
                    f"{p.get('nakshatra_name',''):<18} Rahu: {rahu}"
                )
            _week_panch = "\n".join(lines)
        except Exception as e:
            print(f"[chat_agent] week panchangam error: {e}")

    # Personal Panchangam (Tara Balam + Chandra Ashtama)
    pp: dict = {}
    nak_idx  = chart.get("moon_nakshatra_index")
    rasi_idx = chart.get("moon_rasi_index")
    if nak_idx is not None and rasi_idx is not None:
        try:
            from zoneinfo import ZoneInfo
            tz_id = birth.get("timezone", "Asia/Kolkata")
            td    = datetime.date.today()
            dt    = datetime.datetime(td.year, td.month, td.day, 12, 0, 0,
                                      tzinfo=ZoneInfo(tz_id))
            raw = compute_personal_panchangam(int(nak_idx), int(rasi_idx), dt, tz_id)
            pp = raw
        except Exception as e:
            print(f"[chat_agent] personal panchangam error: {e}")

    tara    = pp.get("tara", {})
    ashtama = pp.get("chandra_ashtama", {})
    cb      = pp.get("chandrabalam", {})

    # Tara Balam calendar — current month + next month
    _tara_month_label = ""
    _tara_cal_block   = "(not available)"
    if nak_idx is not None:
        try:
            tz_id  = birth.get("timezone", "Asia/Kolkata")
            td     = datetime.date.today()
            # current month
            m_label, m_cal = _build_tara_calendar(int(nak_idx), td.year, td.month, tz_id)
            # next month
            if td.month == 12:
                nm_label, nm_cal = _build_tara_calendar(int(nak_idx), td.year + 1, 1, tz_id)
            else:
                nm_label, nm_cal = _build_tara_calendar(int(nak_idx), td.year, td.month + 1, tz_id)
            _tara_month_label = f"{m_label} + {nm_label}"
            _tara_cal_block   = m_cal + "\n" + nm_cal
        except Exception as e:
            print(f"[chat_agent] tara calendar error: {e}")

    def _fmt_dt(v):
        if v is None:
            return None
        if hasattr(v, "strftime"):
            return v.strftime("%-d %b %Y %H:%M %Z")
        return str(v)

    if ashtama.get("is_active"):
        ashtama_end  = _fmt_dt(ashtama.get("end"))
        next_start   = _fmt_dt(ashtama.get("next_ashtama_start"))
        ashtama_status = (
            f"⚠️  ACTIVE — Moon transiting {ashtama.get('ashtama_rasi_name', '8th sign')}."
            + (f" Current period ends: {ashtama_end}." if ashtama_end else "")
            + (f" NEXT occurrence starts: {next_start}." if next_start else "")
            + " Warn the user to avoid new beginnings, major decisions, important travel."
        )
    else:
        next_start   = _fmt_dt(ashtama.get("next_ashtama_start"))
        ashtama_status = (
            f"Not active. Next occurrence starts: {next_start}."
            if next_start else "Not active."
        )

    return SYSTEM_TEMPLATE.format(
        name           = birth.get("name", "the native"),
        ascendant      = asc.get("sign", ""),
        asc_nak        = asc.get("nakshatra", ""),
        asc_pada       = asc.get("pada", ""),
        sun_sign       = planets.get("Sun", {}).get("sign", ""),
        sun_nak        = planets.get("Sun", {}).get("nakshatra", ""),
        moon_sign      = planets.get("Moon", {}).get("sign", ""),
        moon_nak       = planets.get("Moon", {}).get("nakshatra", ""),
        navamsa_asc    = nav_asc.get("sign", "") if nav_asc else "",
        yogas          = ", ".join(yogas) or "none detected",
        planets        = "\n".join(planet_lines),
        maha_planet    = md.get("planet", ""),
        maha_start     = md.get("start", ""),
        maha_end       = md.get("end", ""),
        maha_rem       = md.get("remaining_years", ""),
        maha_focus     = md.get("focus", ""),
        bhukti_planet  = bh.get("planet", ""),
        bhukti_start   = bh.get("start", ""),
        bhukti_end     = bh.get("end", ""),
        bhukti_rem     = bh.get("remaining_months", ""),
        bhukti_trigger = bh.get("trigger", ""),
        antardasha     = "\n".join(antardasha_lines) or "  (not available)",
        today          = today,
        location       = loc,
        vaaram         = panch.get("vaaram_name", ""),
        vaaram_lord    = panch.get("vaaram_lord", ""),
        tithi          = panch.get("tithi_name", ""),
        tithi_paksha   = panch.get("tithi_paksha", ""),
        nakshatra      = panch.get("nakshatra_name", ""),
        nakshatra_lord = panch.get("nakshatra_lord", ""),
        yogam          = panch.get("yogam_name", ""),
        karanam        = panch.get("karanam_name", ""),
        rahu_start     = _fmt_iso(panch.get("rahu_kalam_start")),
        rahu_end       = _fmt_iso(panch.get("rahu_kalam_end")),
        natal_nak      = pp.get("natal_nak_name", ""),
        today_nak      = pp.get("today_moon_nak", ""),
        today_rasi     = pp.get("today_moon_rasi", ""),
        tara_name      = tara.get("name", ""),
        tara_pos       = tara.get("position", ""),
        tara_nature    = tara.get("nature", ""),
        tara_meaning   = tara.get("meaning", ""),
        cb_status      = "Favourable" if cb.get("good") else "Weak",
        cb_house       = cb.get("house_from_natal", "?"),
        ashtama_status = ashtama_status,
        week_panch     = _week_panch or "  (not available)",
        tara_month     = _tara_month_label,
        tara_calendar  = _tara_cal_block,
    ) + _build_gochara_block(natal_chart, dasha)


def _build_gochara_block(natal_chart: dict, dasha: dict) -> str:
    """
    Silently compute Gochara scores and Dasha-Transit correlation,
    then return a compact text block to append to the system prompt.
    Errors are swallowed — chat should still work if scoring fails.
    """
    try:
        scores = score_all_houses(natal_chart)
        return "\n\n" + compact_gochara_summary(scores, dasha)
    except Exception as e:
        print(f"[chat_agent] Gochara block error (non-fatal): {e}")
        return ""


def chat(
    natal_chart: dict,
    messages: list[dict],   # [{"role": "user"|"assistant", "content": str}, ...]
    location: str = "Chennai",
) -> str:
    """
    Send one turn of conversation and return the assistant reply.

    Args:
        natal_chart:  Full /natal-chart response (needs dasha included).
        messages:     Full conversation history including the latest user message.

    Returns:
        Assistant reply string.

    Raises:
        RuntimeError if OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")

    try:
        system_prompt = _build_system(natal_chart, location)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("_build_system failed: %s", e, exc_info=True)
        system_prompt = (
            "You are Jyotish AI, a Vedic astrology advisor. "
            "The user's natal chart could not be loaded. "
            "Answer their question as best you can based on today's Panchangam alone."
        )

    from openai import APIError, AuthenticationError, RateLimitError
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                *messages,
            ],
        )
        return response.choices[0].message.content or ""
    except AuthenticationError:
        raise RuntimeError("OpenAI API key is invalid. Please check server configuration.")
    except RateLimitError:
        raise RuntimeError("OpenAI rate limit reached. Please try again in a moment.")
    except APIError as e:
        raise RuntimeError(f"OpenAI API error: {e}")
