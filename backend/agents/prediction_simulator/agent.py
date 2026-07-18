"""
Life Cycle Simulator (Phase 1) — Parasara method synthesis.

Natal bhava + drishti-aware house analysis → 10-year Vimshottari MD/AD timeline
→ slow-planet transit hits on house lords & karakas → ranked activation windows.
"""

from __future__ import annotations

import datetime
from typing import Optional

from agents.bhavat_bhavam.core import lord_of_house
from agents.house_connections.core import analyze_all_houses, houses_owned_by, planets_aspecting_house
from agents.house_connections.yogas import detect_yogas
from agents.indu_lagna_agent import (
    _jd_at_local_noon,
    _planet_longitude,
    _sign_index_from_longitude,
)
from agents.natal_agent import SIGNS
from agents.prediction_simulator.narration import build_rule_narration
from agents.prediction_simulator.themes import build_event_theme_forecasts

from agents.prediction_simulator.constants import (
    KARAKA_ROLES,
    LIFE_THEMES,
    PLANET_WEIGHT,
    SLOW_TRANSIT_PLANETS,
)
from dasha_core import generate_bhuktis, generate_dashas, generate_pratyantars


def _parse_date(s: str) -> datetime.date:
    return datetime.datetime.strptime(s[:10], "%Y-%m-%d").date()


def _focus_houses_for_lords(natal_chart: dict, *lords: str) -> list[int]:
    asc_idx = natal_chart["ascendant"]["sign_index"]
    pp = natal_chart.get("planet_positions") or {}
    focus: set[int] = set()
    for pl in lords:
        if not pl or pl not in pp:
            continue
        h = pp[pl].get("house")
        if h:
            focus.add(int(h))
        for owned in houses_owned_by(pl, asc_idx):
            focus.add(owned)
    return sorted(focus)


def _theme_labels(houses: list[int]) -> list[str]:
    labels: list[str] = []
    for lt in LIFE_THEMES:
        if any(h in lt["houses"] for h in houses):
            labels.append(lt["label"])
    return labels


def _build_dasha_timeline(
    natal_chart: dict,
    start: datetime.date,
    end: datetime.date,
) -> tuple[list[dict], list[dict]]:
    """Return (AD segments, PD segments) clipped to the horizon."""
    pp = natal_chart.get("planet_positions") or {}
    bd = natal_chart.get("birth_data") or {}
    dob = bd.get("dob")
    if not dob:
        return [], []
    moon_lon = float((pp.get("Moon") or {}).get("longitude", 0))
    segments: list[dict] = []
    pd_segments: list[dict] = []
    today = datetime.date.today()

    for md in generate_dashas(moon_lon, dob):
        md_start = md["start"].date() if hasattr(md["start"], "date") else md["start"]
        md_end = md["end"].date() if hasattr(md["end"], "date") else md["end"]
        if md_end < start:
            continue
        if md_start > end:
            break
        for ad in generate_bhuktis(md):
            ad_start = ad["start"].date() if hasattr(ad["start"], "date") else ad["start"]
            ad_end = ad["end"].date() if hasattr(ad["end"], "date") else ad["end"]
            if ad_end < start or ad_start > end:
                continue
            clip_start = max(ad_start, start)
            clip_end = min(ad_end, end)
            focus = _focus_houses_for_lords(natal_chart, md["planet"], ad["planet"])
            segments.append({
                "mahadasha": md["planet"],
                "antardasha": ad["planet"],
                "start": clip_start.isoformat(),
                "end": clip_end.isoformat(),
                "days": (clip_end - clip_start).days + 1,
                "focus_houses": focus,
                "life_themes": _theme_labels(focus),
                "is_current": clip_start <= today <= clip_end,
            })
            for pd in generate_pratyantars(ad):
                pd_start = pd["start"].date() if hasattr(pd["start"], "date") else pd["start"]
                pd_end = pd["end"].date() if hasattr(pd["end"], "date") else pd["end"]
                if pd_end < start or pd_start > end:
                    continue
                p_clip_s = max(pd_start, start)
                p_clip_e = min(pd_end, end)
                pd_focus = _focus_houses_for_lords(
                    natal_chart, md["planet"], ad["planet"], pd["planet"],
                )
                pd_segments.append({
                    "mahadasha": md["planet"],
                    "antardasha": ad["planet"],
                    "pratyantar": pd["planet"],
                    "start": p_clip_s.isoformat(),
                    "end": p_clip_e.isoformat(),
                    "days": (p_clip_e - p_clip_s).days + 1,
                    "focus_houses": pd_focus,
                    "life_themes": _theme_labels(pd_focus),
                    "is_current": p_clip_s <= today <= p_clip_e,
                })
    return segments, pd_segments


def _build_transit_targets(natal_chart: dict) -> list[dict]:
    asc_idx = natal_chart["ascendant"]["sign_index"]
    pp = natal_chart.get("planet_positions") or {}
    by_sign: dict[int, list[str]] = {}

    for h in range(1, 13):
        sign_idx = (asc_idx + h - 1) % 12
        lord = lord_of_house(asc_idx, h)
        by_sign.setdefault(sign_idx, []).append(
            f"H{h} lord {lord} ({SIGNS[sign_idx]})"
        )

    for planet, role in KARAKA_ROLES.items():
        pdata = pp.get(planet)
        if not pdata:
            continue
        sign_idx = pdata.get("sign_index")
        if sign_idx is None:
            continue
        h = pdata.get("house", "?")
        by_sign.setdefault(sign_idx, []).append(f"{planet} karaka — {role} (natal H{h})")

    return [{"index": idx, "label": " · ".join(labels)} for idx, labels in sorted(by_sign.items())]


def _scan_slow_planet_windows(
    target_by_idx: dict[int, str],
    planets: list[str],
    start_date: datetime.date,
    end_date: datetime.date,
    tz_name: str,
) -> list[dict]:
    """One ephemeris pass per planet — emit a window each time a target sign is occupied.

    Unlike scanning all targets as one set (which never "leaves"), this tracks the
    current sign and only records windows while that sign is a transit target.
    """
    windows: list[dict] = []
    today = datetime.date.today()

    for planet in planets:
        d = start_date
        period_start: Optional[datetime.date] = None
        active_idx: Optional[int] = None

        while d <= end_date:
            jd = _jd_at_local_noon(d, tz_name)
            sign_idx = _sign_index_from_longitude(_planet_longitude(jd, planet))
            in_target = sign_idx in target_by_idx

            if in_target and sign_idx != active_idx:
                if period_start is not None and active_idx is not None:
                    win_end = d - datetime.timedelta(days=1)
                    label = target_by_idx[active_idx]
                    windows.append({
                        "planet": planet,
                        "target": label,
                        "start": period_start.isoformat(),
                        "end": win_end.isoformat(),
                        "duration_days": (win_end - period_start).days + 1,
                        "currently_active": period_start <= today <= win_end,
                        "activation_tier": "primary",
                        "label": f"{planet} over {label}",
                        "sign_index": active_idx,
                    })
                period_start = d
                active_idx = sign_idx
            elif not in_target and period_start is not None and active_idx is not None:
                win_end = d - datetime.timedelta(days=1)
                label = target_by_idx[active_idx]
                windows.append({
                    "planet": planet,
                    "target": label,
                    "start": period_start.isoformat(),
                    "end": win_end.isoformat(),
                    "duration_days": (win_end - period_start).days + 1,
                    "currently_active": period_start <= today <= win_end,
                    "activation_tier": "primary",
                    "label": f"{planet} over {label}",
                    "sign_index": active_idx,
                })
                period_start = None
                active_idx = None

            d += datetime.timedelta(days=1)

        if period_start is not None and active_idx is not None:
            label = target_by_idx[active_idx]
            windows.append({
                "planet": planet,
                "target": label,
                "start": period_start.isoformat(),
                "end": end_date.isoformat(),
                "duration_days": (end_date - period_start).days + 1,
                "currently_active": period_start <= today <= end_date,
                "activation_tier": "primary",
                "label": f"{planet} over {label}",
                "sign_index": active_idx,
            })

    windows.sort(key=lambda w: (w["start"], w["planet"]))
    return windows


def _build_transit_hits(
    natal_chart: dict,
    start: datetime.date,
    end: datetime.date,
    tz_name: str,
) -> list[dict]:
    targets = _build_transit_targets(natal_chart)
    if not targets:
        return []

    target_by_idx = {t["index"]: t["label"] for t in targets}
    raw = _scan_slow_planet_windows(
        target_by_idx,
        list(SLOW_TRANSIT_PLANETS),
        start,
        end,
        tz_name,
    )

    asc_idx = natal_chart["ascendant"]["sign_index"]
    hits: list[dict] = []
    for w in raw:
        target_label = w.get("target", "")
        matched_houses: list[int] = []
        for h in range(1, 13):
            sign_idx = (asc_idx + h - 1) % 12
            lord = lord_of_house(asc_idx, h)
            if f"H{h} lord {lord}" in target_label or f"({SIGNS[sign_idx]})" in target_label:
                if SIGNS[sign_idx] in target_label:
                    matched_houses.append(h)

        for lt in LIFE_THEMES:
            for k in lt["karakas"]:
                if k in target_label and "karaka" in target_label:
                    matched_houses.extend(lt["houses"])

        hits.append({
            "planet": w["planet"],
            "target": target_label,
            "start": w["start"],
            "end": w["end"],
            "duration_days": w.get("duration_days", 0),
            "currently_active": w.get("currently_active", False),
            "tier": w.get("activation_tier", "primary"),
            "label": w.get("label", ""),
            "matched_houses": sorted(set(matched_houses)),
            "matched_themes": _theme_labels(sorted(set(matched_houses))),
        })
    return hits


def _build_impact_areas(natal_chart: dict, segments: list[dict], hits: list[dict]) -> list[dict]:
    houses_map = analyze_all_houses(natal_chart)
    yogas = detect_yogas(houses_map, natal_chart)
    yoga_houses: dict[int, list[str]] = {}
    for y in yogas:
        for h in y.get("houses") or []:
            yoga_houses.setdefault(int(h), []).append(y.get("name", y.get("type", "Yoga")))

    pp = natal_chart.get("planet_positions") or {}
    asc_idx = natal_chart["ascendant"]["sign_index"]

    areas: list[dict] = []
    for h in range(1, 13):
        ha = houses_map[h]
        active_periods: list[str] = []
        for seg in segments:
            if h in seg.get("focus_houses", []):
                active_periods.append(f"{seg['mahadasha']}–{seg['antardasha']} ({seg['start']} → {seg['end']})")

        transit_triggers = [
            f"{t['planet']} → {t['target']} ({t['start']} → {t['end']})"
            for t in hits
            if h in t.get("matched_houses", [])
        ][:5]

        drishti = planets_aspecting_house(pp, asc_idx, h)
        areas.append({
            "house": h,
            "theme": ha["theme_en"],
            "impacts": ha["impacts_en"],
            "lord": ha["lord"],
            "lord_house": ha["lord_house"],
            "strength": ha["strength"],
            "rag": ha["rag"]["status"],
            "planets_in_house": ha["planets_in_house"],
            "planets_aspecting": drishti,
            "yogas": yoga_houses.get(h, []),
            "active_dasa_periods": active_periods[:4],
            "transit_triggers": transit_triggers,
        })
    areas.sort(key=lambda x: x["strength"], reverse=True)
    return areas


def _overlap_days(s1: datetime.date, e1: datetime.date, s2: datetime.date, e2: datetime.date) -> int:
    start = max(s1, s2)
    end = min(e1, e2)
    if end < start:
        return 0
    return (end - start).days + 1


def _rank_windows(segments: list[dict], hits: list[dict]) -> tuple[list[dict], list[dict]]:
    scored: list[dict] = []

    for seg in segments:
        s1 = _parse_date(seg["start"])
        e1 = _parse_date(seg["end"])
        for hit in hits:
            s2 = _parse_date(hit["start"])
            e2 = _parse_date(hit["end"])
            overlap = _overlap_days(s1, e1, s2, e2)
            if overlap < 14:
                continue
            pw = PLANET_WEIGHT.get(hit["planet"], 1)
            theme_overlap = set(seg.get("life_themes", [])) & set(hit.get("matched_themes", []))
            score = overlap * pw + len(theme_overlap) * 30 + len(set(seg["focus_houses"]) & set(hit.get("matched_houses", []))) * 20
            scored.append({
                "score": round(score, 1),
                "overlap_days": overlap,
                "mahadasha": seg["mahadasha"],
                "antardasha": seg["antardasha"],
                "dasa_start": seg["start"],
                "dasa_end": seg["end"],
                "transit_planet": hit["planet"],
                "transit_target": hit["target"],
                "transit_start": hit["start"],
                "transit_end": hit["end"],
                "themes": sorted(theme_overlap) or seg.get("life_themes", [])[:2],
                "houses": sorted(set(seg.get("focus_houses", [])) | set(hit.get("matched_houses", []))),
                "summary": (
                    f"{seg['mahadasha']}–{seg['antardasha']} AD overlaps "
                    f"{hit['planet']} transit on {hit['target'].split('(')[0].strip()} "
                    f"({overlap} days)"
                ),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:12]
    caution = [w for w in scored if w["transit_planet"] in ("Saturn", "Rahu", "Mars")][:6]
    return top, caution


def compute_life_cycle_simulation(
    natal_chart: dict,
    *,
    horizon_years: int = 10,
    start_date: Optional[str] = None,
    include_ai: bool = False,
    language: str = "english",
) -> dict:
    """Main life-cycle simulator — Phase 1 timeline + Phase 2 themes & narration."""
    bd = natal_chart.get("birth_data") or {}
    tz_name = bd.get("timezone") or "Asia/Kolkata"
    today = datetime.date.today()
    start = _parse_date(start_date) if start_date else today
    end = start + datetime.timedelta(days=int(horizon_years * 365.25))

    segments, pd_segments = _build_dasha_timeline(natal_chart, start, end)
    hits = _build_transit_hits(natal_chart, start, end, tz_name)
    impact_areas = _build_impact_areas(natal_chart, segments, hits)
    top_windows, caution_windows = _rank_windows(segments, hits)
    event_themes = build_event_theme_forecasts(
        natal_chart, segments, hits, top_windows, caution_windows, impact_areas,
        pd_segments=pd_segments,
    )

    current_seg = next((s for s in segments if s.get("is_current")), None)
    current_pd = next((p for p in pd_segments if p.get("is_current")), None)
    if current_seg and current_pd:
        current_seg = {**current_seg, "pratyantar": current_pd["pratyantar"],
                       "pratyantar_start": current_pd["start"],
                       "pratyantar_end": current_pd["end"]}
    asc = natal_chart.get("ascendant") or {}
    nav_asc = natal_chart.get("navamsa_ascendant") or {}

    result = {
        "meta": {
            "phase": 3,
            "horizon_years": horizon_years,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "lagna": asc.get("sign", ""),
            "moon_sign": (natal_chart.get("planet_positions") or {}).get("Moon", {}).get("sign", ""),
            "navamsa_lagna": nav_asc.get("sign", ""),
            "method": (
                "Parasara: Bhava → SAV → Drishti → D9 → Vimshottari MD/AD/PD → Gochara "
                "(whole-sign, Lahiri)"
            ),
            "drishti_rules": (
                "All planets aspect 7th; Mars 4th/8th; Jupiter 5th/9th; "
                "Saturn 3rd/10th; Rahu/Ketu 3rd/11th"
            ),
            "disclaimer": (
                "Indicated activation windows — not guaranteed events. "
                "Combine with divisional charts and muhurta for conclusions."
            ),
        },
        "current_period": current_seg,
        "dasha_timeline": segments,
        "pratyantar_timeline": pd_segments,
        "transit_hits": hits,
        "impact_areas": impact_areas,
        "top_windows": top_windows,
        "caution_windows": caution_windows,
        "life_themes": LIFE_THEMES,
        "event_themes": event_themes,
    }

    rule_narration = build_rule_narration(result)
    result["narration"] = rule_narration

    if include_ai:
        from agents.prediction_simulator.ai_narrator import narrate_life_cycle
        ai_reading = narrate_life_cycle(result, rule_narration, language)
        if ai_reading:
            result["ai_reading"] = ai_reading
            result["meta"]["ai_narration"] = True

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Chat grounding — compact, facts-only block for the Jyotish chat narrator.
# Keyword-gated in chat_agent so it only runs for timing-related questions.
# ─────────────────────────────────────────────────────────────────────────────

_VERDICT_TEXT = {
    "highly_active": "Highly active",
    "active": "Active",
    "moderate": "Moderate",
    "quiet": "Quiet",
}


def _fmt_month(iso: str) -> str:
    """2027-03-14 → Mar 2027 (windows are month-scale, so day is noise)."""
    try:
        d = datetime.datetime.strptime(iso[:10], "%Y-%m-%d").date()
        return d.strftime("%b %Y")
    except Exception:
        return iso or "?"


def _fmt_range(start: str, end: str) -> str:
    return f"{_fmt_month(start)}–{_fmt_month(end)}"


def life_cycle_context_for_narrator(natal_chart: dict, horizon_years: int = 10) -> str:
    """Compact, dates-verbatim life-cycle block for the chat system prompt.

    Facts only — no interpretation. The narrator must quote windows/dates from
    here and never invent timing (mirrors the CRITICAL DASHA RULES in the prompt).
    """
    try:
        sim = compute_life_cycle_simulation(natal_chart, horizon_years=horizon_years)
    except Exception:
        return ""

    meta = sim.get("meta", {})
    lines: list[str] = [
        f"=== LIFE CYCLE — next {horizon_years} years "
        f"({meta.get('start_date', '?')} → {meta.get('end_date', '?')}) ===",
        "Parasara: Bhava → SAV → D9 → Vimshottari MD/AD/PD → Gochara. "
        "Quote windows and dates verbatim; never invent timing.",
    ]

    cur = sim.get("current_period")
    if cur:
        pd_txt = ""
        if cur.get("pratyantar"):
            pd_txt = (
                f" · PD {cur['pratyantar']} "
                f"({_fmt_range(cur.get('pratyantar_start', ''), cur.get('pratyantar_end', ''))})"
            )
        lines.append(
            f"Now: {cur.get('mahadasha')} MD / {cur.get('antardasha')} AD "
            f"({_fmt_range(cur.get('start', ''), cur.get('end', ''))}){pd_txt}"
        )

    tops = sim.get("top_windows") or []
    if tops:
        lines.append("Strongest activation windows:")
        for w in tops[:5]:
            themes = ", ".join(w.get("themes") or []) or "general"
            lines.append(
                f"  - {_fmt_range(w.get('transit_start', ''), w.get('transit_end', ''))}: "
                f"{w.get('summary', '')} [{themes}]"
            )

    themes = sim.get("event_themes") or []
    if themes:
        lines.append("Event themes (verdict · SAV · peak window):")
        for t in themes:
            peak = t.get("peak_window") or {}
            peak_txt = (
                _fmt_range(peak.get("start", ""), peak.get("end", ""))
                if peak else "no clear peak"
            )
            sav = (t.get("sav") or {}).get("label", "")
            caution = " · CAUTION" if t.get("has_caution") else ""
            lines.append(
                f"  - {t.get('label')}: {_VERDICT_TEXT.get(t.get('verdict'), t.get('verdict'))}"
                f" · SAV {sav} · peak {peak_txt}{caution}"
            )

    cautions = sim.get("caution_windows") or []
    if cautions:
        lines.append("Caution windows (slow malefics — plan carefully, not doom):")
        seen: set = set()
        for c in cautions[:4]:
            rng = _fmt_range(c.get("transit_start", ""), c.get("transit_end", ""))
            key = (c.get("transit_planet"), rng)
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"  - {rng}: {c.get('transit_planet')} — {c.get('summary', '')}")

    lines.append(
        "HOW TO ANSWER timing questions: lead with a 1-line verdict, then 2–3 dated "
        "windows as bullets (quote dates above), then one caution line if relevant. "
        "Keep it under 6 short lines. If asked about a theme with no data here, say so."
    )
    return "\n".join(lines)
