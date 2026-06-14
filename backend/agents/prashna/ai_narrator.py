"""Phase 2 — AI narration of pre-computed Prashna testimonies only."""

from __future__ import annotations

import os
from typing import Any


def _build_context(result: dict) -> str:
    q = result.get("question", {})
    v = result.get("verdict", {})
    t = result.get("testimonies", {})
    a = result.get("analysis", {})
    chart = result.get("chart", {})

    pos = "\n".join(f"- {x['description']}" for x in t.get("positive", [])) or "- None"
    neg = "\n".join(f"- {x['description']}" for x in t.get("negative", [])) or "- None"
    neu = "\n".join(f"- {x['description']}" for x in t.get("neutral", [])) or "- None"

    asc = chart.get("ascendant", {})
    rh = a.get("relevant_house", {})
    moon = a.get("moon", {})
    timing = a.get("timing", {})

    return f"""Question: {q.get('text')}
Category: {q.get('category_label')}
Moment: {q.get('timestamp')} ({q.get('location', {}).get('place', '')})

CHART (computed — do not change):
Lagna: {asc.get('sign')} — lord {asc.get('sign_lord')}
Relevant house H{rh.get('house_num')} ({rh.get('house_sign')}) — lord {rh.get('house_lord')}
Moon: {moon.get('moon_sign')} in H{moon.get('moon_house')} — {moon.get('outcome')}

VERDICT: {v.get('label')} — {v.get('explanation')}
Timing band: {timing.get('timing_band')}

POSITIVE TESTIMONIES:
{pos}

CHALLENGING TESTIMONIES:
{neg}

NEUTRAL TESTIMONIES:
{neu}

Rule-based summary: {result.get('interpretation', {}).get('summary', '')}
"""


def narrate_prashna(result: dict, language: str = "english") -> str | None:
    """
    Generate a balanced AI reading from existing testimonies.
    Returns None if OpenAI is unavailable.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    lang_note = (
        "Write in clear Tamil suitable for a general audience."
        if language == "tamil"
        else "Write in clear English."
    )

    system = (
        "You are a traditional Vedic Prashna (horary) advisor. "
        "You receive PRE-COMPUTED chart facts and testimonies. "
        "Your job is to narrate them in 4–6 sentences — professional, balanced, traditional. "
        "Use words like 'indicates', 'suggests', 'shows potential'. "
        "NEVER claim guaranteed outcomes. NEVER invent planetary positions, houses, or testimonies "
        "not present in the context. NEVER contradict the verdict. "
        f"{lang_note}"
    )

    user = (
        _build_context(result)
        + "\nWrite a flowing Prashna reading: open with the verdict tone, "
        "mention 1–2 key testimonies, note timing band, end with practical non-certain guidance."
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=280,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (response.choices[0].message.content or "").strip() or None
    except Exception:
        return None
