"""Phase 3 — life-event themes with SAV natal promise + Pratyantar peaks."""

from __future__ import annotations

from typing import Optional

from agents.ashtakavarga_agent import calculate_ashtakavarga
from agents.bhavat_bhavam.core import lord_of_house
from agents.prediction_simulator.constants import LIFE_THEMES

VERDICT_ORDER = ("highly_active", "active", "moderate", "quiet")
PEAK_RELEVANCE_MIN = 45


def _impact_by_house(impact_areas: list[dict]) -> dict[int, dict]:
    return {int(a["house"]): a for a in impact_areas}


def _sav_by_house(natal_chart: dict) -> dict[int, dict]:
    try:
        av = calculate_ashtakavarga(natal_chart)
        return {
            int(h["house"]): {
                "points": int(h["sav_points"]),
                "label": h.get("label", ""),
                "sign": h.get("sign", ""),
            }
            for h in (av.get("sav") or {}).get("by_house") or []
        }
    except Exception:
        return {}


def _sav_label_from_points(pts: float) -> str:
    if pts >= 30:
        return "Strong"
    if pts >= 25:
        return "Good"
    if pts >= 20:
        return "Average"
    return "Weak"


def _theme_sav(houses: list[int], sav_map: dict[int, dict]) -> dict:
    rows = []
    for h in houses:
        info = sav_map.get(h) or {}
        pts = info.get("points", 28)
        rows.append({
            "house": h,
            "points": pts,
            "label": info.get("label") or _sav_label_from_points(pts),
            "sign": info.get("sign", ""),
        })
    avg = round(sum(r["points"] for r in rows) / len(rows), 1) if rows else 28.0
    return {
        "by_house": rows,
        "average": avg,
        "label": _sav_label_from_points(avg),
    }


def _theme_d9_notes(natal_chart: dict, houses: list[int], karakas: list[str]) -> dict:
    pp = natal_chart.get("planet_positions") or {}
    nav = natal_chart.get("navamsa_positions") or {}
    asc_idx = natal_chart["ascendant"]["sign_index"]
    nav_asc = natal_chart.get("navamsa_ascendant") or {}

    house_lords: list[dict] = []
    for h in houses:
        lord = lord_of_house(asc_idx, h)
        pdata = pp.get(lord, {})
        nnav = nav.get(lord, {})
        house_lords.append({
            "house": h,
            "lord": lord,
            "d1_sign": pdata.get("sign", ""),
            "d1_house": pdata.get("house"),
            "d9_sign": nnav.get("sign", ""),
            "d9_house": nnav.get("house"),
            "vargottama": bool(nnav.get("vargottama")),
        })

    karaka_notes: list[dict] = []
    for k in karakas:
        pdata = pp.get(k, {})
        nnav = nav.get(k, {})
        if not pdata:
            continue
        karaka_notes.append({
            "planet": k,
            "d1_sign": pdata.get("sign", ""),
            "d1_house": pdata.get("house"),
            "d9_sign": nnav.get("sign", ""),
            "d9_house": nnav.get("house"),
            "vargottama": bool(nnav.get("vargottama")),
        })

    vargottama_count = sum(1 for x in house_lords + karaka_notes if x.get("vargottama"))
    return {
        "navamsa_lagna": nav_asc.get("sign", ""),
        "house_lords": house_lords,
        "karakas": karaka_notes,
        "vargottama_count": vargottama_count,
        "d9_support": (
            "strong" if vargottama_count >= 2
            else "moderate" if vargottama_count == 1
            else "neutral"
        ),
    }


def _natal_promise_score(
    theme_houses: list[int],
    impact_map: dict[int, dict],
    sav_info: dict,
) -> float:
    strengths = [impact_map[h]["strength"] for h in theme_houses if h in impact_map]
    strength_avg = sum(strengths) / len(strengths) if strengths else 50.0
    # SAV ~22–34 typical; map roughly to 0–100 (28 ≈ 50)
    sav_avg = float(sav_info.get("average") or 28)
    sav_score = max(0.0, min(100.0, (sav_avg - 18) * (100 / 20)))
    return round(0.55 * strength_avg + 0.45 * sav_score, 1)


def _transit_targets_theme_lord(target: str, theme_houses: set[int], asc_idx: int) -> bool:
    for h in theme_houses:
        lord = lord_of_house(asc_idx, h)
        if f"H{h} lord {lord}" in target:
            return True
    return False


def _dasa_relevance(theme: dict, seg: dict, asc_idx: int) -> tuple[int, list[int], dict]:
    houses = set(theme["houses"])
    karakas = set(theme["karakas"])
    overlap_h = sorted(houses & set(seg.get("focus_houses", [])))
    md, ad = seg.get("mahadasha", ""), seg.get("antardasha", "")
    pd = seg.get("pratyantar", "")

    relevance = 0
    if overlap_h:
        relevance += 35 + len(overlap_h) * 12
    if md in karakas:
        relevance += 18
    if ad in karakas:
        relevance += 22
    if pd and pd in karakas:
        relevance += 28
    for pl in (md, ad, pd):
        if not pl:
            continue
        for h in houses:
            if lord_of_house(asc_idx, h) == pl:
                relevance += 15 if pl != pd else 22

    signals = {
        "dasa_lords": [x for x in (md, ad, pd) if x and x in karakas],
        "house_overlap": overlap_h,
    }
    return relevance, overlap_h, signals


def _overlap_relevance(theme: dict, w: dict, asc_idx: int) -> tuple[int, list[int], dict]:
    houses = set(theme["houses"])
    karakas = set(theme["karakas"])
    w_houses = set(w.get("houses") or [])
    theme_hit = sorted(houses & w_houses)

    target = w.get("transit_target") or w.get("summary", "")
    transit = w.get("transit_planet", "")
    lord_hit = _transit_targets_theme_lord(target, houses, asc_idx)
    karaka_hit = transit in karakas and "karaka" in target

    relevance = 0
    if theme_hit:
        relevance += 40 + len(theme_hit) * 15
    if lord_hit:
        relevance += 38
    if karaka_hit:
        relevance += 25
    md, ad = w.get("mahadasha", ""), w.get("antardasha", "")
    if md in karakas:
        relevance += 12
    if ad in karakas:
        relevance += 15

    signals = {
        "transit_planet": transit,
        "theme_houses": theme_hit,
        "lord_transit": lord_hit,
        "karaka_transit": karaka_hit,
    }
    return relevance, theme_hit, signals


def _transit_relevance(theme: dict, hit: dict, asc_idx: int) -> tuple[int, list[int], dict]:
    houses = set(theme["houses"])
    karakas = set(theme["karakas"])
    matched = sorted(houses & set(hit.get("matched_houses", [])))
    target = hit.get("target", "")
    lord_hit = _transit_targets_theme_lord(target, houses, asc_idx)
    karaka_hit = hit["planet"] in karakas

    relevance = 0
    if matched:
        relevance += 30 + len(matched) * 18
    if lord_hit:
        relevance += 40
    if karaka_hit:
        relevance += 20 if (matched or lord_hit) else 8

    return relevance, matched, {
        "transit_planet": hit["planet"],
        "theme_houses": matched,
        "lord_transit": lord_hit,
        "karaka_transit": karaka_hit,
    }


def _pick_peak(windows: list[dict]) -> dict | None:
    eligible = [w for w in windows if w.get("relevance", 0) >= PEAK_RELEVANCE_MIN]
    if not eligible:
        eligible = [w for w in windows if w.get("theme_houses")]
    if not eligible:
        return None
    return max(eligible, key=lambda w: (w.get("relevance", 0), w.get("score", 0)))


def _collect_pd_windows(
    theme: dict,
    natal_chart: dict,
    pd_segments: list[dict],
) -> list[dict]:
    """Top Pratyantar clusters for this theme (MA-style finer timing)."""
    asc_idx = natal_chart["ascendant"]["sign_index"]
    scored: list[dict] = []
    for seg in pd_segments:
        relevance, theme_hit, signals = _dasa_relevance(theme, seg, asc_idx)
        if relevance < 40:
            continue
        score = relevance + seg.get("days", 0) / 20
        scored.append({
            "type": "pratyantar",
            "mahadasha": seg["mahadasha"],
            "antardasha": seg["antardasha"],
            "pratyantar": seg["pratyantar"],
            "start": seg["start"],
            "end": seg["end"],
            "summary": (
                f"{seg['mahadasha']}–{seg['antardasha']}–{seg['pratyantar']} Pratyantar"
            ),
            "score": round(score, 1),
            "relevance": relevance,
            "theme_houses": theme_hit,
            "signals": signals,
            "is_current": seg.get("is_current", False),
        })
    scored.sort(key=lambda x: (-x["relevance"], -x["score"], x["start"]))
    return scored[:5]


def _collect_theme_windows(
    theme: dict,
    natal_chart: dict,
    segments: list[dict],
    hits: list[dict],
    top_windows: list[dict],
    caution_windows: list[dict],
    pd_segments: Optional[list] = None,
) -> tuple:
    asc_idx = natal_chart["ascendant"]["sign_index"]
    activation = 0.0
    windows: list = []

    for seg in segments:
        relevance, theme_hit, signals = _dasa_relevance(theme, seg, asc_idx)
        if relevance < 25:
            continue
        score = relevance + seg.get("days", 0) / 45
        activation += score
        windows.append({
            "type": "dasa",
            "start": seg["start"],
            "end": seg["end"],
            "summary": f"{seg['mahadasha']}–{seg['antardasha']} Antardasha",
            "score": round(score, 1),
            "relevance": relevance,
            "theme_houses": theme_hit,
            "signals": signals,
        })

    pd_windows = _collect_pd_windows(theme, natal_chart, pd_segments or [])
    for pw in pd_windows:
        activation += pw["score"] * 0.6
        windows.append(pw)

    for hit in hits:
        relevance, theme_hit, signals = _transit_relevance(theme, hit, asc_idx)
        if relevance < 20:
            continue
        score = relevance + hit.get("duration_days", 0) * 0.15
        activation += score
        windows.append({
            "type": "transit",
            "start": hit["start"],
            "end": hit["end"],
            "summary": f"{hit['planet']} → {hit['target'].split('(')[0].strip()}",
            "score": round(score, 1),
            "relevance": relevance,
            "theme_houses": theme_hit,
            "signals": signals,
            "planet": hit["planet"],
        })

    for w in top_windows:
        relevance, theme_hit, signals = _overlap_relevance(theme, w, asc_idx)
        if relevance < 30:
            continue
        score = relevance + w.get("score", 0) * 0.08
        activation += score
        windows.append({
            "type": "overlap",
            "start": w["transit_start"],
            "end": w["transit_end"],
            "summary": w["summary"],
            "score": round(score, 1),
            "relevance": relevance,
            "theme_houses": theme_hit,
            "signals": signals,
        })

    cautions: list = []
    for w in caution_windows:
        relevance, theme_hit, signals = _overlap_relevance(theme, w, asc_idx)
        # Require theme-house hit so global Saturn/Rahu overlaps don't caution every theme
        if relevance < 40 or not theme_hit:
            continue
        cautions.append({
            "start": w["transit_start"],
            "end": w["transit_end"],
            "summary": w["summary"],
            "planet": w["transit_planet"],
            "theme_houses": theme_hit,
            "relevance": relevance,
            "lord_transit": signals.get("lord_transit", False),
            "karaka_transit": signals.get("karaka_transit", False),
        })

    windows.sort(key=lambda x: (-x.get("relevance", 0), -x["score"], x["start"]))
    return windows[:10], cautions[:4], pd_windows, activation


def _verdict(
    natal_score: float,
    activation_norm: float,
    d9_support: str,
    sav_label: str,
) -> str:
    combined = natal_score * 0.45 + activation_norm * 0.55
    if d9_support == "strong":
        combined += 6
    elif d9_support == "moderate":
        combined += 3
    if sav_label == "Strong":
        combined += 4
    elif sav_label == "Weak":
        combined -= 3
    if combined >= 72:
        base = "highly_active"
    elif combined >= 55:
        base = "active"
    elif combined >= 38:
        base = "moderate"
    else:
        base = "quiet"
    return base


def _has_strong_caution(cautions: list) -> bool:
    """Flag caution only when a slow malefic afflicts the theme's own lord or karaka.

    A mere transit through a theme-house sign (relevance ~40) is too weak — it fired
    on almost every theme. Require the malefic to hit the house-lord or theme karaka
    (lord/karaka_transit) with high relevance so the flag stays meaningful.
    """
    return any(
        c.get("theme_houses")
        and (c.get("lord_transit") or c.get("karaka_transit"))
        and c.get("relevance", 0) >= 70
        for c in cautions
    )


def build_event_theme_forecasts(
    natal_chart: dict,
    segments: list[dict],
    hits: list[dict],
    top_windows: list[dict],
    caution_windows: list[dict],
    impact_areas: list[dict],
    pd_segments: Optional[list] = None,
) -> list:
    impact_map = _impact_by_house(impact_areas)
    sav_map = _sav_by_house(natal_chart)
    raw_forecasts: list[dict] = []

    for theme in LIFE_THEMES:
        houses = theme["houses"]
        sav_info = _theme_sav(houses, sav_map)
        natal_score = _natal_promise_score(houses, impact_map, sav_info)
        d9 = _theme_d9_notes(natal_chart, houses, theme["karakas"])
        windows, cautions, pd_windows, activation = _collect_theme_windows(
            theme, natal_chart, segments, hits, top_windows, caution_windows,
            pd_segments=pd_segments,
        )

        yogas: list[str] = []
        for h in houses:
            yogas.extend(impact_map.get(h, {}).get("yogas") or [])
        yogas = sorted(set(yogas))

        # Prefer a Pratyantar as peak when relevance is competitive
        peak = _pick_peak(windows)
        if pd_windows:
            best_pd = pd_windows[0]
            if not peak or best_pd["relevance"] >= (peak.get("relevance") or 0) - 5:
                peak = best_pd

        raw_forecasts.append({
            "key": theme["key"],
            "label": theme["label"],
            "houses": houses,
            "karakas": theme["karakas"],
            "natal_promise_score": natal_score,
            "activation_raw": activation,
            "sav": sav_info,
            "d9_support": d9["d9_support"],
            "d9_overlay": d9,
            "yogas": yogas,
            "active_windows": windows,
            "pratyantar_windows": pd_windows,
            "caution_windows": cautions,
            "peak_window": peak,
        })

    max_act = max((f["activation_raw"] for f in raw_forecasts), default=1.0) or 1.0
    forecasts: list[dict] = []
    for f in raw_forecasts:
        act_norm = round(f["activation_raw"] / max_act * 100, 1)
        verdict = _verdict(
            f["natal_promise_score"], act_norm,
            f["d9_support"], f["sav"]["label"],
        )
        forecasts.append({
            **{k: v for k, v in f.items() if k != "activation_raw"},
            "activation_score": act_norm,
            "verdict": verdict,
            "has_caution": _has_strong_caution(f["caution_windows"]),
        })

    forecasts.sort(
        key=lambda t: (VERDICT_ORDER.index(t["verdict"]), -t["activation_score"]),
    )
    return forecasts
