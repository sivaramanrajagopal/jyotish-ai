"""House Connections — astrologer prediction map."""

from __future__ import annotations

from agents.house_connections.blessers import rank_blessers
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.dasa_activation import compute_dasa_life_areas
from agents.house_connections.edges import build_edges
from agents.house_connections.inference import build_prediction_card
from agents.house_connections.themes import DISCLAIMER_EN, DISCLAIMER_TA, HOUSE_THEMES
from agents.house_connections.yogas import detect_yogas
from dasha_core import find_current_dasha_bhukti


def _dasa_lords(natal_chart: dict) -> tuple[str, str]:
    bd = natal_chart.get("birth_data") or {}
    pp = natal_chart.get("planet_positions") or {}
    if not bd.get("dob"):
        return "", ""
    moon_lon = (pp.get("Moon") or {}).get("longitude", 0.0)
    _, cur_d, _, cur_b = find_current_dasha_bhukti(moon_lon, bd["dob"])
    return cur_d["planet"], cur_b["planet"]


def compute_house_connections(natal_chart: dict) -> dict:
    houses_map = analyze_all_houses(natal_chart)
    houses = [houses_map[h] for h in range(1, 13)]
    edges = build_edges(houses_map, natal_chart)
    maha, bhukti = _dasa_lords(natal_chart)
    yogas = detect_yogas(houses_map, natal_chart)

    predictions = {}
    blessers_by_house = {}
    for h in range(1, 13):
        bl = rank_blessers(h, houses_map, edges, natal_chart, maha, bhukti)
        blessers_by_house[h] = bl
        predictions[h] = build_prediction_card(h, houses_map, edges, bl, maha, bhukti)

    strong = sorted(houses, key=lambda x: x["strength"], reverse=True)[:3]
    weak = sorted(houses, key=lambda x: x["strength"])[:3]
    dasa_life_areas = compute_dasa_life_areas(natal_chart, maha, bhukti)

    return {
        "disclaimer": {"en": DISCLAIMER_EN, "ta": DISCLAIMER_TA},
        "summary": {
            "maha_dasa": maha,
            "bhukti": bhukti,
            "edge_count": len(edges),
            "yoga_count": len(yogas),
            "strongest_houses": [{"house": h["house"], "theme_en": h["theme_en"], "strength": h["strength"]} for h in strong],
            "weakest_houses": [{"house": h["house"], "theme_en": h["theme_en"], "strength": h["strength"]} for h in weak],
        },
        "houses": houses,
        "edges": edges,
        "yogas": yogas,
        "predictions": [predictions[h] for h in range(1, 13)],
        "blessers_by_house": blessers_by_house,
        "dasa_life_areas": dasa_life_areas,
        "graph": _graph_payload(houses_map, edges),
    }


def _graph_payload(houses_map: dict[int, dict], edges: list[dict]) -> dict:
    """12-node circular layout positions + edge list for SVG renderer."""
    import math
    nodes = []
    n = 12
    for i, h in enumerate(range(1, 13)):
        angle = (i / n) * 2 * math.pi - math.pi / 2
        ha = houses_map[h]
        nodes.append({
            "id": h,
            "house": h,
            "label": f"H{h}",
            "theme_en": ha["theme_en"],
            "lord": ha["lord"],
            "strength": ha["strength"],
            "rag": ha["rag"]["status"],
            "x": round(50 + 42 * math.cos(angle), 2),
            "y": round(50 + 42 * math.sin(angle), 2),
        })
    return {
        "nodes": nodes,
        "edges": [
            {
                "id": e["id"],
                "from": e["from_house"],
                "to": e["to_house"],
                "kind": e["kind"],
                "supportive": e.get("supportive", True),
                "weight": e.get("weight", 1),
            }
            for e in edges
        ],
    }


from agents.house_connections.narrator import house_connections_context_for_narrator
