"""Phase 3 — short optional AI narration from pre-computed facts only."""

from __future__ import annotations

import os


def _context(simulation: dict, rule: dict) -> str:
    meta = simulation.get("meta") or {}
    lines = [
        f"Horizon: {meta.get('start_date')} → {meta.get('end_date')}",
        f"Lagna: {meta.get('lagna')} | Moon: {meta.get('moon_sign')}",
        f"Headline: {rule.get('headline', '')}",
        f"Current: {rule.get('current_period', '')}",
        "",
        "THEMES (do not invent dates):",
    ]
    for t in (simulation.get("event_themes") or [])[:4]:
        peak = t.get("peak_window") or {}
        sav = t.get("sav") or {}
        pd = (t.get("pratyantar_windows") or [{}])[0]
        line = (
            f"- {t['label']}: {t['verdict']}, SAV {sav.get('average')} ({sav.get('label')}), "
            f"natal {t['natal_promise_score']}"
        )
        if peak:
            th = ",".join(str(h) for h in (peak.get("theme_houses") or []))
            line += f"; peak={peak.get('summary')} H{th} ({peak.get('start')}→{peak.get('end')})"
        if pd.get("pratyantar"):
            line += f"; top PD={pd.get('summary')} ({pd.get('start')}→{pd.get('end')})"
        lines.append(line)
    if rule.get("caution"):
        lines.append(f"Caution: {rule['caution']}")
    return "\n".join(lines)


def narrate_life_cycle(simulation: dict, rule_narration: dict, language: str = "english") -> str | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    lang = (
        "Write in clear Tamil."
        if language == "tamil"
        else "Write in clear English."
    )
    system = (
        "You are a Parasara Vedic astrologer. Narrate pre-computed life-cycle facts only. "
        "Write EXACTLY 3 short sentences: (1) current MD/AD/PD focus, "
        "(2) top theme peak with its houses/dates, (3) one caution or practical tip. "
        "No titles, no bullet lists, no filler. Use 'indicates/suggests'. "
        "Never invent planets, houses, or dates. Never reuse one peak for every theme. "
        f"{lang}"
    )
    user = _context(simulation, rule_narration) + "\n\nWrite the 3-sentence reading now."

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=180,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (response.choices[0].message.content or "").strip() or None
    except Exception:
        return None
