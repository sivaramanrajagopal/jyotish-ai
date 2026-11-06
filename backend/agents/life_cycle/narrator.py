"""Life Cycle block for the chat system prompt: facts and dates only, quoted verbatim."""

from __future__ import annotations

from agents.life_cycle.engine import compute_life_cycle


def _houses(rows: list[dict]) -> str:
    return ", ".join(f"H{r['house']} (by {r['by_en']})" for r in rows) or "none"


def life_cycle_context_for_narrator(natal_chart: dict, horizon_years: int = 10) -> str:
    try:
        lc = compute_life_cycle(natal_chart, horizon_years=horizon_years)
    except Exception:
        return ""
    meta = lc["meta"]
    lines = [
        f"=== LIFE CYCLE — next {horizon_years} years ({meta['start']} → {meta['end']}) ===",
        "Same rules as the House Links tab. " + meta["method_en"],
        "Quote windows and dates verbatim; never invent timing. There are no scores.",
    ]
    now = lc.get("now")
    if now:
        lines.append(f"Now: {now['mahadasha']} mahadasha / {now['bhukti']} bhukti ({now['start']} → {now['end']}).")
        lines.append(f"  Houses on: {_houses(now['on'])}.")
        if now["live"]:
            lines.append("  Live with transit: " + ", ".join(f"H{r['house']} until {r['until']}" for r in now["live"]) + ".")
        if now.get("relation"):
            lines.append(f"  {now['relation']['en']}")

    lines.append("Themes (status now · next transit-backed window · natal fruit of key houses):")
    for t in lc["themes"]:
        nxt = t.get("next_live")
        nxt_txt = f"{nxt['start']} → {nxt['end']} ({nxt['mahadasha']}–{nxt['bhukti']})" if nxt else "none in this horizon"
        live = t.get("live_now")
        live_txt = f" until {live['end']}" if live else ""
        fruit = "; ".join(f"H{f['house']} {f['en']}" for f in t["fruit"])
        lines.append(f"  - {t['label_en']} [H{', H'.join(map(str, t['key_houses']))}]: "
                     f"{t['status']['en']}{live_txt} · next {nxt_txt} · {fruit}")
        for n in t["notes"]:
            lines.append(f"      note: {n['en']}")
        for r in t["remedies"]:
            lines.append(f"      remedy ({r['lord']}): {r['mantra']} ×{r['count']}, {r['day']}, charity {', '.join(r['charity'])}")

    if lc["saturn"]:
        lines.append("Saturn from the Moon:")
        for s in lc["saturn"]:
            tag = " (NOW)" if s["now"] else ""
            lines.append(f"  - {s['en']}: {s['start']} → {s['end']}{tag}. {s['meaning_en']}")
            for p in s["phases"]:
                lines.append(f"      {p['en']}: {p['start']} → {p['end']}{' (NOW)' if p['now'] else ''}")

    lines.append(
        "HOW TO ANSWER timing questions: one-line verdict, then 2–3 dated windows from above, then one "
        "Saturn or care line if relevant. Under 6 short lines. If the native is already married, read "
        "the marriage theme as spouse and partnerships. If a theme has no window here, say so."
    )
    return "\n".join(lines)
