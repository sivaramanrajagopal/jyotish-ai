"""Prediction inference cards per house."""

from __future__ import annotations

from agents.bhavat_bhavam.core import bhavat_bhavam_house
from agents.house_connections.themes import DUSTHANA


def dusthana_recovery_edges(house_num: int, houses: dict[int, dict]) -> list[dict]:
    """Bhavat Bhavam recovery note for dusthana houses only — not used in channel graph."""
    if house_num not in DUSTHANA:
        return []
    bb = bhavat_bhavam_house(house_num)
    ha = houses[house_num]
    return [{
        "id": f"bhavat_bhavam:{house_num}:{bb}",
        "kind": "bhavat_bhavam",
        "from_house": house_num,
        "to_house": bb,
        "label_en": f"Bhavat Bhavam H{house_num}→H{bb} recovery path",
        "label_ta": f"Bhavat Bhavam H{house_num}→H{bb} குணமடைதல் வழி",
        "planets": [ha["lord"], houses[bb]["lord"]],
        "supportive": True,
    }]


def build_prediction_card(
    house_num: int,
    houses: dict[int, dict],
    edges: list[dict],
    blessers: list[dict],
    maha: str,
    bhukti: str,
) -> dict:
    ha = houses[house_num]
    incoming = [e for e in edges if e["to_house"] == house_num and e.get("supportive", True)]
    outgoing = [e for e in edges if e["from_house"] == house_num]
    stress = [e for e in edges if e["to_house"] == house_num and not e.get("supportive", True)]
    recovery = dusthana_recovery_edges(house_num, houses)

    channels_in = sorted({e["from_house"] for e in incoming})[:6]
    channels_out = sorted({e["to_house"] for e in outgoing if e["to_house"] != house_num})[:6]

    top_blesser = blessers[0] if blessers else None
    active = [b for b in blessers if b.get("active_maha") or b.get("active_bhukti")]

    inference_en = _inference_en(ha, channels_in, channels_out, top_blesser, maha, bhukti, stress, recovery)
    inference_ta = _inference_ta(ha, channels_in, top_blesser, maha, bhukti)

    return {
        "house": house_num,
        "theme_en": ha["theme_en"],
        "theme_ta": ha["theme_ta"],
        "structure": {
            "lord": ha["lord"],
            "lord_house": ha["lord_house"],
            "position_type": ha["position_type"],
            "position_en": ha["position_en"],
            "strength": ha["strength"],
            "rag": ha["rag"],
        },
        "channels_in": channels_in,
        "channels_out": channels_out,
        "incoming_edges": incoming[:8],
        "stress_edges": stress[:4],
        "recovery_edges": recovery,
        "blessers": blessers,
        "active_blessers": active,
        "top_blesser": top_blesser,
        "inference_en": inference_en,
        "inference_ta": inference_ta,
    }


def _inference_en(ha, channels_in, channels_out, top_blesser, maha, bhukti, stress, recovery) -> str:
    parts = [
        f"H{ha['house']} ({ha['theme_en']}): lord {ha['lord']} in H{ha['lord_house']} "
        f"({ha['position_en']}). Strength {ha['strength']}/100 ({ha['rag']['label_en']}).",
    ]
    if channels_in:
        parts.append(f"Results flow in from houses {', '.join(f'H{c}' for c in channels_in)}.")
    if channels_out:
        parts.append(f"This house channels outward to {', '.join(f'H{c}' for c in channels_out)}.")
    if top_blesser:
        parts.append(f"Primary blesser: {top_blesser['planet']} (score {top_blesser['score']}).")
    if maha or bhukti:
        parts.append(f"Current Dasa: {maha} MD · {bhukti} Bhukti.")
        if top_blesser and (top_blesser.get("active_maha") or top_blesser.get("active_bhukti")):
            parts.append(f"{top_blesser['planet']} is active now — favourable window for H{ha['house']} themes.")
    if stress:
        parts.append("Watch dusthana stress links; use Bhavat Bhavam recovery paths where shown.")
    elif recovery:
        parts.append(f"Recovery path: H{recovery[0]['to_house']} (Bhavat Bhavam).")
    return " ".join(parts)


def _inference_ta(ha, channels_in, top_blesser, maha, bhukti) -> str:
    parts = [
        f"H{ha['house']} ({ha['theme_ta']}): அதிபதி {ha['lord']} H{ha['lord_house']} இல். "
        f"வலிமை {ha['strength']}/100.",
    ]
    if channels_in:
        parts.append(f"உள்ளீடு: {', '.join(f'H{c}' for c in channels_in)}.")
    if top_blesser:
        parts.append(f"ஆசி கிரகம்: {top_blesser['planet']}.")
    if maha:
        parts.append(f"தசை: {maha}–{bhukti}.")
    return " ".join(parts)
