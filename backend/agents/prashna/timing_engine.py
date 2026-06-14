"""Simplified traditional timing from sign modality."""

from __future__ import annotations

from agents.prashna.constants import MOVABLE_SIGNS, FIXED_SIGNS, DUAL_SIGNS, SIGN_MODALITY, SIGNS
from agents.prashna.chart_engine import house_sign


def estimate_timing(chart: dict, relevant_house: int) -> dict:
    sign = house_sign(chart, relevant_house)
    sign_idx = SIGNS.index(sign)

    if sign_idx in MOVABLE_SIGNS:
        modality = "movable"
        band = "Days to Weeks"
        explanation = (
            f"Matter-house sign {sign} is movable (Chara) — results may unfold relatively quickly, "
            "though exact dates cannot be determined."
        )
    elif sign_idx in FIXED_SIGNS:
        modality = "fixed"
        band = "Months to Long Delay"
        explanation = (
            f"Matter-house sign {sign} is fixed (Sthira) — patience is required; "
            "fulfilment tends to be slow or delayed."
        )
    else:
        modality = "dual"
        band = "Weeks to Months"
        explanation = (
            f"Matter-house sign {sign} is dual (Dwiswabhava) — timing is variable; "
            "outcomes may shift before settling."
        )

    return {
        "relevant_house_sign": sign,
        "modality": modality,
        "timing_band": band,
        "explanation": explanation,
        "note": "Indicative timing only — not an exact prediction.",
    }
