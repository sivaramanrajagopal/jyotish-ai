"""House Connections — chat narrator context (compact default, detail on demand)."""

from __future__ import annotations

import re

from agents.house_connections.blessers import rank_blessers
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.dasa_activation import compute_dasa_life_areas
from agents.house_connections.edges import build_edges
from agents.house_connections.inference import build_prediction_card
from agents.house_connections.themes import DISCLAIMER_EN
from agents.house_connections.yogas import detect_yogas
from dasha_core import find_current_dasha_bhukti

_HOUSE_LINKS_RE = re.compile(
    r"house\s*links?|house\s*connections?|lord\s*links?|blesser\s*planet?|"
    r"channels?\s*(in|out)|prediction\s*map|raja\s*yoga.*lord|dharma-karma",
    re.I,
)
_HOUSE_NUM_RE = re.compile(
    r"\bh\s*(\d{1,2})\b|(\d{1,2})(?:st|nd|rd|th)\s+house|house\s*(\d{1,2})\b",
    re.I,
)
_THEME_HOUSES = {
    "marriage": 7, "partner": 7, "spouse": 7, "relationship": 7,
    "career": 10, "profession": 10, "job": 10, "karma": 10,
    "fortune": 9, "dharma": 9, "luck": 9, "bhagya": 9,
    "wealth": 2, "money": 2, "family": 2,
    "health": 6, "disease": 6,
    "home": 4, "mother": 4, "property": 4,
    "children": 5, "education": 5, "creativity": 5,
    "gains": 11, "income": 11, "profit": 11,
    "loss": 12, "expense": 12, "foreign": 12,
    "self": 1, "personality": 1, "lagna": 1,
}

EXPLANATION_GUIDE = """HOW TO EXPLAIN HOUSE LINKS (when user asks about a specific house):
1. Open with lord, seat, from-own placement, strength (Strong/Moderate/Weak).
2. Channels IN — cite each IN bullet from the house card below.
3. Channels OUT — cite each OUT bullet.
4. Name primary blesser and score; note if ACTIVE in Mahadasha/Bhukti.
5. Strong house + STRESS links: strength is real; some ties use dusthana-from-own lords — caution, not contradiction.
6. Bhavat Bhavam recovery only when listed on the card (H6/H8/H12). Never invent links."""


def _dasa_lords(natal_chart: dict) -> tuple[str, str]:
    bd = natal_chart.get("birth_data") or {}
    pp = natal_chart.get("planet_positions") or {}
    if not bd.get("dob"):
        return "", ""
    moon_lon = (pp.get("Moon") or {}).get("longitude", 0.0)
    _, cur_d, _, cur_b = find_current_dasha_bhukti(moon_lon, bd["dob"])
    return cur_d["planet"], cur_b["planet"]


def _houses_from_message(message: str) -> set[int]:
    found: set[int] = set()
    if not message:
        return found
    for m in _HOUSE_NUM_RE.finditer(message):
        for g in m.groups():
            if g:
                n = int(g)
                if 1 <= n <= 12:
                    found.add(n)
    lower = message.lower()
    for word, h in _THEME_HOUSES.items():
        if word in lower:
            found.add(h)
    return found


def _wants_detail(message: str) -> bool:
    if not message:
        return False
    if _HOUSE_LINKS_RE.search(message):
        return True
    if _houses_from_message(message):
        return True
    if re.search(r"explain\s+h\d|channels?\s+in|channels?\s+out", message, re.I):
        return True
    return False


def _format_house_card(
    pred: dict,
    house_row: dict,
    outgoing_edges: list[dict],
) -> str:
    st = pred["structure"]
    rag = st["rag"]
    lines = [
        f"--- H{pred['house']} {pred['theme_en']} ({pred['theme_ta']}) ---",
        (
            f"Lord {st['lord']} in H{st['lord_house']} · {st['position_en']} · "
            f"Strength {st['strength']}/100 ({rag['label_en']})"
        ),
    ]
    if house_row.get("planets_in_house"):
        lines.append(f"Planets in house: {', '.join(house_row['planets_in_house'])}")
    if house_row.get("planets_aspecting"):
        lines.append(f"Planets aspecting: {', '.join(house_row['planets_aspecting'])}")

    cin = pred.get("channels_in") or []
    if cin:
        lines.append(
            f"Channels IN (feeding H{pred['house']}): {', '.join(f'H{x}' for x in cin)}"
        )
        for e in pred.get("incoming_edges") or []:
            lines.append(f"  IN · {e['label_en']}")
    else:
        lines.append("Channels IN: none")

    cout = pred.get("channels_out") or []
    if cout:
        lines.append(
            f"Channels OUT (from H{pred['house']}): {', '.join(f'H{x}' for x in cout)}"
        )
        for e in outgoing_edges[:8]:
            lines.append(f"  OUT · {e['label_en']}")
    else:
        lines.append("Channels OUT: none")

    for e in (pred.get("stress_edges") or [])[:5]:
        lines.append(f"  STRESS · {e['label_en']}")

    for e in pred.get("recovery_edges") or []:
        lines.append(f"Bhavat Bhavam recovery: {e['label_en']}")

    top = pred.get("top_blesser")
    if top:
        active = []
        if top.get("active_maha"):
            active.append("Mahadasha")
        if top.get("active_bhukti"):
            active.append("Bhukti")
        act = f" · ACTIVE in {'/'.join(active)}" if active else ""
        lines.append(f"Primary blesser: {top['planet']} (score {top['score']}){act}")

    blessers = pred.get("blessers") or []
    if len(blessers) > 1:
        lines.append(
            "Other blessers: "
            + ", ".join(f"{b['planet']} ({b['score']})" for b in blessers[1:4])
        )

    return "\n".join(lines)


def _format_compact_line(pred: dict) -> str:
    st = pred["structure"]
    cin = ", ".join(f"H{x}" for x in (pred.get("channels_in") or [])) or "—"
    cout = ", ".join(f"H{x}" for x in (pred.get("channels_out") or [])) or "—"
    bless = pred.get("top_blesser") or {}
    bname = bless.get("planet", "—")
    bscore = bless.get("score", "")
    return (
        f"  H{pred['house']} {pred['theme_en']}: lord {st['lord']} H{st['lord_house']} · "
        f"{st['strength']}/100 ({st['rag']['label_en']}) · "
        f"in [{cin}] out [{cout}] · blesser {bname} ({bscore})"
    )


def _build_data(natal_chart: dict) -> dict | None:
    try:
        maha, bhukti = _dasa_lords(natal_chart)
        houses_map = analyze_all_houses(natal_chart)
        edges = build_edges(houses_map, natal_chart)
        yogas = detect_yogas(houses_map, natal_chart)
        dasa_life_areas = compute_dasa_life_areas(natal_chart, maha, bhukti)
        predictions = {}
        for h in range(1, 13):
            bl = rank_blessers(h, houses_map, edges, natal_chart, maha, bhukti)
            predictions[h] = build_prediction_card(h, houses_map, edges, bl, maha, bhukti)
        strong = sorted(houses_map.values(), key=lambda x: x["strength"], reverse=True)[:3]
        weak = sorted(houses_map.values(), key=lambda x: x["strength"])[:3]
        return {
            "maha": maha,
            "bhukti": bhukti,
            "houses_map": houses_map,
            "edges": edges,
            "yogas": yogas,
            "dasa_life_areas": dasa_life_areas,
            "predictions": predictions,
            "strong": strong,
            "weak": weak,
        }
    except Exception:
        return None


def house_connections_context_for_narrator(
    natal_chart: dict,
    user_message: str = "",
) -> str:
    data = _build_data(natal_chart)
    if not data:
        return ""

    maha = data["maha"]
    bhukti = data["bhukti"]
    predictions = data["predictions"]
    houses_map = data["houses_map"]
    edges = data["edges"]
    detail = _wants_detail(user_message)
    focus_houses = _houses_from_message(user_message)

    if detail and not focus_houses:
        focus_houses = {7, 9, 10}

    lines = [
        "=== HOUSE CONNECTIONS (prediction map) ===",
        f"DISCLAIMER: {DISCLAIMER_EN}",
        f"Current Dasa: {maha} Mahadasha · {bhukti} Bhukti",
        "",
        "STRONGEST HOUSES:",
    ]
    for h in data["strong"]:
        lines.append(f"  H{h['house']} {h['theme_en']} — {h['strength']}/100 ({h['rag']['label_en']})")
    lines.append("WEAKEST HOUSES:")
    for h in data["weak"]:
        lines.append(f"  H{h['house']} {h['theme_en']} — {h['strength']}/100 ({h['rag']['label_en']})")

    yogas = data["yogas"]
    if yogas:
        lines.extend(["", "KEY YOGAS:"])
        for y in yogas[:4]:
            lines.append(f"  • {y['name']}: {y['detail_en']}")

    combined = (data["dasa_life_areas"].get("combined") or {})
    if combined.get("focus_houses"):
        lines.extend([
            "",
            "DASA LIFE AREAS:",
            f"  Focus: {', '.join(f'H{x}' for x in combined['focus_houses'])}",
            f"  Background: {', '.join(f'H{x}' for x in combined.get('background_houses', []))}",
        ])

    if detail:
        lines.extend(["", EXPLANATION_GUIDE, ""])
        if focus_houses:
            lines.append(
                f"DETAIL for {', '.join(f'H{h}' for h in sorted(focus_houses))} (cite exactly):"
            )
            for h in sorted(focus_houses):
                outgoing = [e for e in edges if e["from_house"] == h and e["to_house"] != h]
                lines.append(_format_house_card(predictions[h], houses_map[h], outgoing))
        else:
            lines.append("DETAIL (all houses):")
            for h in range(1, 13):
                outgoing = [e for e in edges if e["from_house"] == h and e["to_house"] != h]
                lines.append(_format_house_card(predictions[h], houses_map[h], outgoing))
    else:
        lines.extend([
            "",
            "COMPACT SUMMARY (ask about a specific house for full Channels IN/OUT detail):",
        ])
        for h in range(1, 13):
            lines.append(_format_compact_line(predictions[h]))

    return "\n".join(lines)
