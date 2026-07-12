"""Phase 3 — short deterministic narration from pre-computed facts."""

from __future__ import annotations

VERDICT_COPY = {
    "highly_active": "strong activation",
    "active": "active",
    "moderate": "moderate",
    "quiet": "quiet",
}


def build_rule_narration(simulation: dict) -> dict:
    themes = simulation.get("event_themes") or []
    current = simulation.get("current_period")
    cautions = simulation.get("caution_windows") or []

    ranked = sorted(themes, key=lambda t: -t.get("activation_score", 0))
    lead = ranked[0] if ranked else None
    secondary = ranked[1] if len(ranked) > 1 else None

    if lead and secondary:
        lead_note = " (caution)" if lead.get("has_caution") else ""
        headline = (
            f"{lead['label']}: {VERDICT_COPY.get(lead['verdict'], lead['verdict'])}{lead_note}; "
            f"{secondary['label'].split('&')[0].strip()} secondary."
        )
    elif lead:
        headline = f"{lead['label']}: {VERDICT_COPY.get(lead['verdict'], lead['verdict'])}."
    else:
        headline = "Review Dasa and transit windows for this horizon."

    current_para = ""
    if current:
        pd = current.get("pratyantar")
        pd_bit = f" / {pd} PD" if pd else ""
        houses = ", ".join(f"H{h}" for h in current.get("focus_houses", [])) or "—"
        current_para = (
            f"Now: {current['mahadasha']} MD / {current['antardasha']} AD{pd_bit} "
            f"({current['start']} → {current['end']}). Focus {houses}."
        )

    caution_line = ""
    if cautions:
        c = cautions[0]
        caution_line = (
            f"Caution: {c['transit_planet']} {c['transit_start']} → {c['transit_end']}."
        )

    theme_summaries = []
    for t in ranked[:3]:
        peak = t.get("peak_window") or {}
        sav = t.get("sav") or {}
        bits = [
            f"SAV {sav.get('average', '—')} ({sav.get('label', '—')})",
            f"natal {t['natal_promise_score']}",
            VERDICT_COPY.get(t["verdict"], t["verdict"]),
        ]
        if peak:
            th = peak.get("theme_houses") or []
            htxt = f" H{','.join(str(x) for x in th)}" if th else ""
            bits.append(f"peak {peak.get('summary', '')}{htxt} ({peak.get('start')}→{peak.get('end')})")
        theme_summaries.append({
            "key": t["key"],
            "label": t["label"],
            "text": f"{t['label']}: " + "; ".join(bits) + ".",
        })

    return {
        "headline": headline,
        "current_period": current_para,
        "top_windows": [w.get("summary", "") for w in (simulation.get("top_windows") or [])[:2]],
        "caution": caution_line,
        "theme_summaries": theme_summaries,
        "d9_note": "",
        "method_note": "Bhava → SAV → MD/AD/PD → Gochara. Windows are indications, not guarantees.",
    }
