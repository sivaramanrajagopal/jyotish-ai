"""
narrator.py
===========
Calls the OpenAI API to generate a personalized daily Vedic forecast
from the assembled context (orchestrator.py output).

Sections returned:
  career, love, health, spiritual, finance, timing_advice, dasha_context
"""

from __future__ import annotations

import os
import re
from typing import Optional

from openai import OpenAI


# ── Model config ─────────────────────────────────────────────────────────────

MODEL  = "gpt-4o-mini"   # fast + cheap; swap to "gpt-4o" for deeper analysis
TOKENS = 1200


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are Jyotish AI — an expert Vedic astrology advisor trained in classical \
Jyotish (Sanskrit: "science of light"). You interpret natal birth charts using \
the Parashari system: Lahiri ayanamsa, Whole Sign houses, Vimshottari Dasha, \
and classical graha significations.

When given a context block, generate a concise personalized daily forecast. \
Rules:
- Write in warm, confident second person ("Your Moon in Virgo…").
- Be specific: name planets, signs, houses, dashas — no vague platitudes.
- Keep each section 2–3 sentences, focused and actionable.
- Do NOT invent facts. Use only what is provided in the context.
- Do NOT add disclaimers or "consult a professional" caveats.
- When Chandra Ashtama is active, prominently mention it in timing_advice and health.
- When Tara Balam is inauspicious (Vipat/Pratyak/Naidhana), warn against new ventures.
- When Ashtakavarga (SAV) data is provided, cite strong/weak houses in career, finance, and timing_advice.
- Output ONLY the XML tags below, nothing else.

Output format (XML):
<career>…</career>
<love>…</love>
<health>…</health>
<spiritual>…</spiritual>
<finance>…</finance>
<timing_advice>…</timing_advice>
<dasha_context>…</dasha_context>
"""


# ── Context formatter ─────────────────────────────────────────────────────────

def _build_prompt(ctx: dict) -> str:
    native  = ctx.get("native", {})
    dasha   = ctx.get("dasha", {})
    panch   = ctx.get("panchangam", {})
    pp      = ctx.get("personal_panchangam", {})
    md      = dasha.get("mahadasha", {})
    bh      = dasha.get("bhukti", {})

    planets_block = "\n".join(f"  • {p}" for p in ctx.get("planets", []))
    yogas_block   = ", ".join(ctx.get("yogas", [])) or "none detected"

    upcoming = dasha.get("upcoming_bhuktis", [])
    upcoming_str = ", ".join(
        f"{b['planet']} ({b['start']}–{b['end']})" for b in upcoming
    ) or "n/a"

    # Personal Panchangam block
    if pp.get("ashtama_active"):
        ashtama_end  = pp.get("ashtama_end")
        next_start   = pp.get("next_ashtama_start")
        ashtama_line = (
            f"⚠️  ACTIVE — Moon in {pp.get('ashtama_rasi', 'your 8th sign')}."
            + (f" Ends: {ashtama_end}." if ashtama_end else "")
            + (f" Next occurrence: {next_start}." if next_start else "")
            + " Avoid new beginnings, major decisions, travel."
        )
    else:
        next_start   = pp.get("next_ashtama_start")
        ashtama_line = (
            f"Not active. Next occurrence: {next_start}."
            if next_start else "Not active."
        )
    cb_line = (
        f"{'Favourable' if pp.get('chandrabalam_good') else 'Weak'} "
        f"(Moon in house {pp.get('chandrabalam_house', '?')} from natal Moon)"
    )

    return f"""\
=== NATIVE ===
Name        : {native.get('name', 'unknown')}
DOB         : {native.get('dob', '')}
Ascendant   : {native.get('ascendant_sign')} ({native.get('ascendant_element')} / {native.get('ascendant_quality')})
Moon Sign   : {native.get('moon_sign')}  [nakshatra: {native.get('moon_nakshatra')}]
Sun Sign    : {native.get('sun_sign')}
Lagna Nak.  : {native.get('ascendant_nakshatra')}
Navamsa Asc.: {ctx.get('navamsa_ascendant', '')}
Yogas       : {yogas_block}

=== PLANET POSITIONS (D1 Rasi) ===
{planets_block}

=== VIMSHOTTARI DASHA ===
Mahadasha : {md.get('planet','')} ({md.get('start','')}–{md.get('end','')}, {md.get('remaining_years','')} yrs left)
            Focus: {md.get('focus','')}
Bhukti    : {bh.get('planet','')} ({bh.get('start','')}–{bh.get('end','')}, {bh.get('remaining_months','')} months left)
            Trigger: {bh.get('trigger','')}
Relationship: Mahadasha lord is {dasha.get('relationship','')} to Bhukti lord
Upcoming  : {upcoming_str}

=== TODAY'S PANCHANGAM ({ctx.get('date','')} · {ctx.get('location','')}) ===
Vaaram    : {panch.get('vaaram','')} (lord: {panch.get('vaaram_lord','')})
Tithi     : {panch.get('tithi_paksha','')} {panch.get('tithi','')}
Nakshatra : {panch.get('nakshatra','')} (lord: {panch.get('nakshatra_lord','')})
Yogam     : {panch.get('yogam','')}
Karanam   : {panch.get('karanam','')}
Rahu Kalam: {panch.get('rahu_kalam_start','')} – {panch.get('rahu_kalam_end','')}

=== PERSONAL PANCHANGAM ===
Natal Moon Nakshatra : {pp.get('natal_nak_name', 'n/a')}
Today's Moon         : {pp.get('today_moon_nak', '')} in {pp.get('today_moon_rasi', '')}
Tara Balam           : {pp.get('tara_name', '')} (Tara {pp.get('tara_position', '')}) — {pp.get('tara_nature', '')}
                       {pp.get('tara_meaning', '')}
Chandrabalam         : {cb_line}
Chandra Ashtama      : {ashtama_line}

=== ASHTAKAVARGA (SARVASHTAKAVARGA) ===
{ctx.get('ashtakavarga_context') or 'not available'}

Now generate the daily forecast. Remember: output ONLY the XML tags.
"""


# ── XML parser ────────────────────────────────────────────────────────────────

_SECTIONS = ["career", "love", "health", "spiritual", "finance",
             "timing_advice", "dasha_context"]


def _parse_xml(text: str) -> dict[str, str]:
    result = {}
    for tag in _SECTIONS:
        m = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        result[tag] = m.group(1).strip() if m else ""
    return result


# ── Main entry ────────────────────────────────────────────────────────────────

def generate_forecast(context: dict) -> dict:
    """
    Call OpenAI and return parsed forecast sections.

    Returns:
        {
          "career": str,
          "love": str,
          "health": str,
          "spiritual": str,
          "finance": str,
          "timing_advice": str,
          "dasha_context": str,
          "model": str,
          "raw": str,       # full model response (for debugging)
        }

    Raises:
        RuntimeError if OPENAI_API_KEY is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Get a key at https://platform.openai.com/api-keys and add it to backend/.env"
        )

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": _build_prompt(context)},
        ],
    )

    raw = response.choices[0].message.content or ""
    sections = _parse_xml(raw)
    sections["model"] = MODEL
    sections["raw"]   = raw
    return sections
