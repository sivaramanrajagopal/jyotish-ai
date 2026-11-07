"""
chat_agent.py
=============
Multi-turn Vedic astrology chat using OpenAI.
The user's full natal chart is injected as system context so every
answer is grounded in their specific chart.
"""

from __future__ import annotations

import datetime
from time_utils import today_in
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
)
from agents.ashtakavarga_agent import bav_context_for_narrator
from agents.tamil_dosha_agent import dosha_context_for_narrator
from agents.indu_lagna_agent import indu_context_for_narrator
from agents.career_agent import career_context_for_narrator
from agents.health_agent import health_context_for_narrator
from agents.dosha_radar_agent import dosha_radar_context_for_narrator
from agents.house_connections_agent import house_connections_context_for_narrator
from agents.bhavat_bhavam_agent import bhavat_bhavam_context_for_narrator
from agents.life_cycle import life_cycle_context_for_narrator
from dasha_core import (
    format_bhukti_table,
    format_full_dasha_cycle_markdown,
    format_mahadasha_timeline_table,
    format_next_mahadashas_block,
    format_upcoming_bhuktis_block,
)

TOKENS = 1200   # room for dasha cycle tables + brief interpretation

SYSTEM_TEMPLATE = """\
You are Parashara Jyotish — a classical Vedic astrology advisor (Parashari system, \
Lahiri ayanamsa, Whole Sign houses, Vimshottari Dasha).

You are speaking with {name}. Their natal chart and today's Panchangam are below. \
Answer their questions with specific, chart-grounded insights. \
Be warm, direct, and concise (3–5 sentences per answer). \
Name specific planets, signs, houses, or dashas from their chart. \
Never give vague generic advice. Do not add general disclaimers. \
On health questions only, close with one short line to see a doctor for any symptoms.
Whether a house is live or quiet comes from the HOUSE CONNECTIONS block; the GOCHARA block adds transit detail. \
Never quote a 0–100 score for transits, houses or periods.
When naming body parts, use plain anatomical words and a calm, respectful tone.

CRITICAL DASHA RULES (never violate):
- Mahadasha and Bhukti are different. Bhukti = sub-period WITHIN the current Mahadasha only.
- "Next Mahadasha" = the planet labelled "NEXT Mahadasha (1st after current)" below — NOT the next Bhukti.
- NEVER invent dasha start/end dates or durations. Quote ONLY from NEXT MAHADASHAS, UPCOMING BHUKTIS, or tables below.
- If data is missing, say "recalculate your chart on Home" — do not guess.

When discussing Dasha/Bhukti sequences, always refer to the tables provided — do not guess.
When the user asks for a **dasha table**, **bhukti table**, or taps the Dasha Table topic, you MUST include \
the exact Bhukti table (markdown) block from below in your reply without changing any dates or planet names. \
When the user asks about **next Mahadasha** or **Mahadasha timeline**, include the Mahadasha timeline table below. \
When the user asks for **full dasa cycle**, **full dasha bhukti cycle**, or taps the Dasa Cycle topic, you MUST include \
the exact FULL DASA CYCLE block below (both tables, unchanged) plus 2–3 sentences on what is active now and what is next. \
Add a brief 2–3 sentence interpretation before or after any other table.

When the user asks about **Tamil doshas**, **dagdha**, **Mudakku**, **Vadhai**, **Vainasikam**, **Yogi/Avayogi**, or **parihara/remedies** for doshas, \
use ONLY the TAMIL PREDICTIVE DOSHAS block appended below. Give house-specific upaya (2–4 steps per affected house). \
Prefer Mudakku Method B; note Method A as unverified. Never invent mantras.

When the user asks about **Dosha Radar**, **Pushkara Navamsa**, **obstruction doshas**, **Visha Gati**, **Divine Protection**, \
**Chandrashtama**, **live transit doshas**, or **90-day dosha forecast**, use the DOSHA RADAR block below. \
Mention Pushkara as divine protection when present; distinguish natal blueprint from live transits.

When the user asks about **house connections**, **house links**, **lord links**, **blesser planet**, **channels in**, **channels out**, \
**which house channels results**, **explain H9** (or any house), **Raja Yoga from lords**, or **prediction map**, \
use the HOUSE CONNECTIONS block below. Follow HOW TO EXPLAIN HOUSE LINKS in that block: cite each Channels IN/OUT bullet \
from the matching house card; explain stress vs strength; name blessers with scores. Never invent lord placements or links.

When the user asks about the **next few years**, **what's coming**, **best/worst periods**, **timing** of marriage/career/health, \
**activation windows**, or a **life forecast**, use ONLY the LIFE CYCLE block below (if present). \
Quote the windows and dates verbatim — NEVER invent or shift dates. Follow HOW TO ANSWER in that block: \
one-line verdict, then 2–3 dated windows as bullets, then one caution line if relevant; keep it under 6 short lines. \
If the LIFE CYCLE block is absent or a theme has no window there, say the timeline does not flag it — do not guess.

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
MD–Bhukti relationship: {dasha_relationship}

NEXT MAHADASHAS (exact dates — use for "what comes after my Mahadasha" questions):
{next_mahadashas}

UPCOMING BHUKTIS (sub-periods within current Mahadasha only — NOT next Mahadasha):
{upcoming_bhuktis}

FULL ANTARDASHA SEQUENCE (all bhuktis within {maha_planet} Mahadasha, in order):
{antardasha}

Bhukti table (markdown — copy exactly when user asks for bhukti/antardasha table):
{bhukti_table}

Mahadasha timeline table (markdown — copy when user asks about next Mahadasha or full dasha timeline):
{mahadasha_timeline}

FULL DASA CYCLE — high level (markdown — copy exactly when user asks for full Vimshottari dasa/bhukti cycle):
{full_dasha_cycle}

=== TODAY'S PANCHANGAM ({today} · {location}, times in {location_tz}; limbs at sunrise) ===
Sunrise   : {sunrise} · Sunset: {sunset}
Vaaram    : {vaaram} (lord: {vaaram_lord})
Tithi     : {tithi_paksha} {tithi}{tithi_end}
Nakshatra : {nakshatra} (lord: {nakshatra_lord}){nakshatra_end}
Yogam     : {yogam}{yogam_end}
Karanam   : {karanam}{karanam_end}
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

=== TARA BALAM CALENDAR — next 30 days ({tara_month}) ===
(GOOD = benefic tara, BAD = malefic, ~ = neutral Janma)
Use this table to give EXACT dates when asked about good/bad days.
{tara_calendar}
"""


def _build_tara_calendar(natal_nak_index: int, start: datetime.date, days: int = 30,
                         timezone: str = "Asia/Kolkata") -> tuple[str, str]:
    """
    Tara Balam for each day from `start` (Moon's nakshatra at 06:00 local).
    Returns (range_label, calendar_block_string).
    """
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(timezone)
    lines = []
    for i in range(days):
        day = start + datetime.timedelta(days=i)
        dt = datetime.datetime(day.year, day.month, day.day, 6, 0, 0, tzinfo=tz)
        jd  = _dt_to_jd(dt)
        lon = _moon_longitude(jd)
        nak = _nak_index(lon)
        tara = compute_tara_balam(natal_nak_index, nak)
        nature = tara["nature"]
        marker = "GOOD" if nature == "benefic" else ("BAD " if nature == "malefic" else "~   ")
        lines.append(
            f"  {day.strftime('%b %d')} [{marker}] "
            f"{tara['name']:<12} (Tara {tara['position']}) "
            f"Moon in {NAKSHATRAS[nak]}"
        )

    end = start + datetime.timedelta(days=days - 1)
    label = f"{start.strftime('%-d %b')} → {end.strftime('%-d %b %Y')}"
    return label, "\n".join(lines)


def _build_system(natal_chart, location: str = "Chennai", user_message: str = "") -> str:
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

    loc = location if location in LOCATIONS else (next(iter(LOCATIONS)) if LOCATIONS else "")
    loc_tz = (LOCATIONS.get(loc) or {}).get("tz") or "Asia/Kolkata"
    loc_today = today_in(loc_tz)

    # ── helpers ──────────────────────────────────────────────────────────────
    def _fmt_iso(iso_str: str | None, with_day: bool = False) -> str:
        """Format an ISO timestamp as clock time in the location's timezone."""
        if not iso_str:
            return "—"
        try:
            from dateutil.parser import parse as _dp
            from zoneinfo import ZoneInfo as _ZI
            local = _dp(iso_str).astimezone(_ZI(loc_tz))
            return local.strftime("%-d %b %I:%M %p %Z" if with_day else "%I:%M %p %Z")
        except Exception:
            return iso_str

    def _ends(end_key: str, next_key: str) -> str:
        end = panch.get(end_key)
        if not end:
            return ""
        nxt = panch.get(next_key)
        return f" — ends {_fmt_iso(end, with_day=True)}" + (f", then {nxt}" if nxt else "")

    # Today's panchangam
    today = loc_today.isoformat()
    panch: dict = {}
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
                d = (loc_today + datetime.timedelta(days=i)).isoformat()
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
            td    = today_in(tz_id)
            dt    = datetime.datetime(td.year, td.month, td.day, 12, 0, 0,
                                      tzinfo=ZoneInfo(tz_id))
            raw = compute_personal_panchangam(int(nak_idx), int(rasi_idx), dt, tz_id)
            pp = raw
        except Exception as e:
            print(f"[chat_agent] personal panchangam error: {e}")

    tara    = pp.get("tara", {})
    ashtama = pp.get("chandra_ashtama", {})
    cb      = pp.get("chandrabalam", {})

    # Tara Balam calendar — the next 30 days
    _tara_month_label = ""
    _tara_cal_block   = "(not available)"
    if nak_idx is not None:
        try:
            tz_id  = birth.get("timezone", "Asia/Kolkata")
            _tara_month_label, _tara_cal_block = _build_tara_calendar(
                int(nak_idx), today_in(tz_id), 30, tz_id,
            )
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
        name           = "the person",
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
        dasha_relationship = dasha.get("relationship", "—"),
        next_mahadashas = format_next_mahadashas_block(dasha),
        upcoming_bhuktis = format_upcoming_bhuktis_block(dasha),
        antardasha     = "\n".join(antardasha_lines) or "  (not available)",
        bhukti_table   = dasha.get("bhukti_table_markdown") or format_bhukti_table(dasha) or "(not available)",
        mahadasha_timeline = (
            dasha.get("mahadasha_timeline_markdown")
            or format_mahadasha_timeline_table(dasha)
            or "(not available)"
        ),
        full_dasha_cycle = (
            dasha.get("full_dasha_cycle_markdown")
            or format_full_dasha_cycle_markdown(dasha)
            or "(not available)"
        ),
        today          = today,
        location       = loc,
        location_tz    = loc_tz,
        sunrise        = _fmt_iso(panch.get("sunrise")),
        sunset         = _fmt_iso(panch.get("sunset")),
        vaaram         = panch.get("vaaram_name", ""),
        vaaram_lord    = panch.get("vaaram_lord", ""),
        tithi          = panch.get("tithi_name", ""),
        tithi_end      = _ends("tithi_end_time", "next_tithi_name"),
        tithi_paksha   = panch.get("tithi_paksha", ""),
        nakshatra      = panch.get("nakshatra_name", ""),
        nakshatra_end  = _ends("nakshatra_end_time", "next_nakshatra_name"),
        nakshatra_lord = panch.get("nakshatra_lord", ""),
        yogam          = panch.get("yogam_name", ""),
        yogam_end      = _ends("yogam_end_time", "next_yogam_name"),
        karanam        = panch.get("karanam_name", ""),
        karanam_end    = _ends("karanam_end_time", "next_karanam_name"),
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
    ) + _build_gochara_block(natal_chart, dasha, user_message=user_message)


def _build_gochara_block(natal_chart: dict, dasha: dict, user_message: str = "") -> str:
    """
    Silently compute Gochara scores + Dasha-Transit correlation + Ashtakavarga,
    then return a compact text block to append to the system prompt.
    Errors are swallowed — chat should still work if scoring fails.
    """
    try:
        scores   = score_all_houses(natal_chart)
        gochara  = compact_gochara_summary(scores, dasha)
    except Exception as e:
        print(f"[chat_agent] Gochara block error (non-fatal): {e}")
        gochara  = ""

    try:
        bav_ctx = "\n\n" + bav_context_for_narrator(natal_chart)
    except Exception:
        bav_ctx = ""

    try:
        dosha_ctx = "\n\n" + dosha_context_for_narrator(natal_chart)
    except Exception:
        dosha_ctx = ""

    try:
        indu_ctx = "\n\n" + indu_context_for_narrator(natal_chart)
    except Exception:
        indu_ctx = ""

    try:
        career_ctx = "\n\n" + career_context_for_narrator(natal_chart)
    except Exception:
        career_ctx = ""

    try:
        health_ctx = "\n\n" + health_context_for_narrator(natal_chart)
    except Exception:
        health_ctx = ""

    try:
        bhavam_ctx = "\n\n" + bhavat_bhavam_context_for_narrator(natal_chart)
    except Exception:
        bhavam_ctx = ""

    try:
        radar_ctx = "\n\n" + dosha_radar_context_for_narrator(natal_chart)
    except Exception:
        radar_ctx = ""

    try:
        house_ctx = "\n\n" + house_connections_context_for_narrator(natal_chart, user_message)
    except Exception:
        house_ctx = ""

    # The Life Cycle block is long, so attach it only for timing-related questions.
    life_cycle_ctx = ""
    if _wants_life_cycle(user_message):
        try:
            block = life_cycle_context_for_narrator(natal_chart)
            if block:
                life_cycle_ctx = "\n\n" + block
        except Exception:
            life_cycle_ctx = ""

    block = (
        ("\n\n" + gochara if gochara else "")
        + bav_ctx + dosha_ctx + indu_ctx + career_ctx + health_ctx + bhavam_ctx + radar_ctx + house_ctx
        + life_cycle_ctx
    )
    return _strip_disclaimers(block)


def _strip_disclaimers(text: str) -> str:
    """The chat has one disclaimer rule in the system prompt; drop per-block DISCLAIMER lines."""
    return "\n".join(
        line for line in text.split("\n") if not line.lstrip().startswith("DISCLAIMER")
    )


# Timing / "what's coming" cues → attach the Life Cycle grounding block.
_LIFE_CYCLE_KEYWORDS = (
    "life cycle", "lifecycle", "next few years", "next year", "coming years",
    "next 5 years", "next 10 years", "next three years", "next 3 years",
    "future", "upcoming", "what's coming", "whats coming", "what is coming",
    "best period", "best time", "worst period", "tough period", "hard period",
    "difficult period", "good period", "favourable period", "favorable period",
    "when will", "when can", "when should", "timing", "time frame", "timeframe",
    "activation window", "peak period", "10-year", "10 year", "forecast",
    "marriage timing", "career timing", "when marriage", "when job", "when career",
    "life forecast", "life prediction", "milestone",
)


def _wants_life_cycle(user_message: str) -> bool:
    if not user_message:
        return False
    text = user_message.lower()
    return any(kw in text for kw in _LIFE_CYCLE_KEYWORDS)


_TAMIL_CHAT_SUFFIX = """

=== மொழி அறிவுறுத்தல் (STRICT TAMIL ONLY) ===
உங்கள் பதில் முழுவதும் தூய தமிழில் இருக்க வேண்டும்.
தங்கிலீஷ் (Tanglish) வேண்டாம். தேவநாகரி / ஹிந்தி எழுத்துகள் வேண்டாம்.
ஆங்கில எழுத்துகளை உரை வரிகளில் கலக்காதீர்கள்.

கிரக பெயர்கள் (இவற்றை மட்டுமே பயன்படுத்தவும்):
சூரியன் | சந்திரன் | செவ்வாய் | புதன் | குரு | சுக்கிரன் | சனி | ராகு | கேது

ஜோதிட சொற்கள்:
மகாதசை = Mahadasha | புத்தி = Bhukti | பாவம் = House
நட்சத்திரம் = Nakshatra | லக்னம் = Lagna | கோசாரம் = Transit
உச்சம் = Exalted | நீசம் = Debilitated | வக்கிரம் = Retrograde

அனுமதிக்கப்படுவன (ALLOWED in English):
H1…H12 (வீட்டு எண்கள்) | எண் மதிப்புகள் (scores)
=== END INSTRUCTION ==="""


_TOOL_GUIDE = """
When the question needs the current period, planet strength, planetary condition, or today's sky, call the matching tool and answer from its numbers. Do not invent rupas, ranks, dates, or tithis. Write plain sentences. Strength is capacity, not a promise that the period feels pleasant.
"""


def chat(
    natal_chart: dict,
    messages: list[dict],
    location: str = "Chennai",
    language: str = "english",
    page: str = "",
) -> str:
    """
    Send one turn of conversation and return the assistant reply.
    language: "english" | "tamil"
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")

    last_user = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        "",
    )

    try:
        system_prompt = _build_system(natal_chart, location, user_message=last_user)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("_build_system failed: %s", e, exc_info=True)
        raise RuntimeError("Could not load chart context for chat.")

    if language.lower() == "tamil":
        system_prompt += _TAMIL_CHAT_SUFFIX
    page_label = " ".join(str(page or "").split())[:40]
    if page_label:
        system_prompt += f"\nThe person is looking at the {page_label} page. Start from that page when it fits the question.\n"
    system_prompt += _TOOL_GUIDE

    from agents.chat_tools import CLASSICAL_TOOL, CLASSICAL_GUIDE, active_tools, tool_result_json
    tools = active_tools()
    if CLASSICAL_TOOL in tools:
        system_prompt += CLASSICAL_GUIDE
    from openai import APIError, AuthenticationError, RateLimitError
    from ai_client import ai_base_url, ai_extra, ai_model
    from ai_limits import AI_KEY_INVALID_DETAIL, ai_error_detail
    try:
        client = OpenAI(api_key=api_key, base_url=ai_base_url())
        thread = [
            {"role": "system", "content": system_prompt},
            *messages,
        ]
        reply = ""
        for round_no in range(4):
            last_round = round_no == 3
            response = client.chat.completions.create(
                model=ai_model(),
                max_tokens=TOKENS,
                messages=thread,
                tools=tools,
                tool_choice="none" if last_round else "auto",
                **ai_extra(),
            )
            message = response.choices[0].message
            tool_calls = message.tool_calls or []
            if not tool_calls or last_round:
                reply = message.content or ""
                break
            thread.append(message.model_dump(exclude_none=True))
            for call in tool_calls:
                thread.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": tool_result_json(
                        call.function.name, natal_chart, location, call.function.arguments or "",
                    ),
                })
            reply = message.content or reply
        return reply or "I could not finish that reading from the chart."
    except AuthenticationError:
        raise RuntimeError(AI_KEY_INVALID_DETAIL)
    except RateLimitError as exc:
        raise RuntimeError(ai_error_detail(exc) or "AI rate limit reached. Please try again in a moment.")
    except APIError as e:
        raise RuntimeError(ai_error_detail(e) or f"AI API error: {e}")
