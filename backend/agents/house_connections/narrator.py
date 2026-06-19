"""House Connections — rich chat / narrator context for per-house explanations."""

from __future__ import annotations

from agents.house_connections.blessers import rank_blessers
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.dasa_activation import compute_dasa_life_areas
from agents.house_connections.edges import build_edges
from agents.house_connections.inference import build_prediction_card
from agents.house_connections.themes import DISCLAIMER_EN
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
        lines.append(f"Channels IN (life areas feeding into H{pred['house']}): {', '.join(f'H{x}' for x in cin)}")
        for e in pred.get("incoming_edges") or []:
            lines.append(f"  IN · {e['label_en']}")
    else:
        lines.append(f"Channels IN: none listed")

    cout = pred.get("channels_out") or []
    if cout:
        lines.append(f"Channels OUT (H{pred['house']} radiates to): {', '.join(f'H{x}' for x in cout)}")
        for e in outgoing_edges[:8]:
            lines.append(f"  OUT · {e['label_en']}")
    else:
        lines.append(f"Channels OUT: none listed")

    stress = pred.get("stress_edges") or []
    if stress:
        lines.append("Stress links (caution — lord in dusthana-from-own or malefic tie):")
        for e in stress[:5]:
            lines.append(f"  STRESS · {e['label_en']}")

    recovery = pred.get("recovery_edges") or []
    if recovery:
        for e in recovery:
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


EXPLANATION_GUIDE = """HOW TO EXPLAIN HOUSE LINKS (follow when user asks about any house, e.g. H9):
1. Open with lord, house seat, "from own" placement, and strength (Strong/Moderate/Weak).
2. Channels IN — for each source house, cite the exact IN bullet from the house card (why results flow in).
3. Channels OUT — for each target house, cite the exact OUT bullet (where this house channels energy).
4. Name the primary blesser planet and score; say if it is ACTIVE in current Mahadasha/Bhukti.
5. If STRESS links exist on a Strong house, explain: structural strength is good, but some links arrive via \
dusthana-from-own lord placements — mention caution, not contradiction.
6. Bhavat Bhavam recovery applies ONLY when the house card lists it (H6/H8/H12). Do NOT assign BB recovery to other houses.
7. Use plain life-area language (fortune, marriage, career) tied to the chart facts — never invent lords or channels.
8. Optional: relate to DASA LIFE AREAS focus houses if the asked house is in the current focus set."""


def house_connections_context_for_narrator(natal_chart: dict) -> str:
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
    except Exception:
        return ""

    lines = [
        "=== HOUSE CONNECTIONS (prediction map — explain like an astrologer) ===",
        f"DISCLAIMER: {DISCLAIMER_EN}",
        f"Current Dasa: {maha} Mahadasha · {bhukti} Bhukti",
        "",
        EXPLANATION_GUIDE,
        "",
        "STRONGEST HOUSES:",
    ]
    for h in strong:
        lines.append(f"  H{h['house']} {h['theme_en']} — {h['strength']}/100 ({h['rag']['label_en']})")
    lines.append("WEAKEST HOUSES:")
    for h in weak:
        lines.append(f"  H{h['house']} {h['theme_en']} — {h['strength']}/100 ({h['rag']['label_en']})")

    if yogas:
        lines.extend(["", "KEY YOGAS (lord links):"])
        for y in yogas[:6]:
            lines.append(f"  • {y['name']}: {y['detail_en']} (strength {y['strength']})")

    combined = (dasa_life_areas.get("combined") or {})
    if combined.get("focus_houses"):
        lines.extend([
            "",
            "DASA LIFE AREAS (current period emphasis):",
            f"  Focus: {', '.join(f'H{x}' for x in combined['focus_houses'])}",
            f"  Background: {', '.join(f'H{x}' for x in combined.get('background_houses', []))}",
        ])

    lines.extend(["", "HOUSE-BY-HOUSE DETAIL (cite these exactly when explaining):"])
    for h in range(1, 13):
        pred = predictions[h]
        outgoing = [e for e in edges if e["from_house"] == h and e["to_house"] != h]
        lines.append(_format_house_card(pred, houses_map[h], outgoing))

    return "\n".join(lines)
