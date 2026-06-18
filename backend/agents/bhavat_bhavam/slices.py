"""Bhavat Bhavam slices for Health and Career tabs."""

from __future__ import annotations

from agents.bhavat_bhavam.core import evaluate_link

HEALTH_PRIMARY_HOUSES = (6, 8, 12)
CAREER_PRIMARY_HOUSES = (10, 2)

DISCLAIMER_EN = (
    "Bhavat Bhavam is a secondary Parashari layer (house-from-house). "
    "Support/recovery paths only — not medical or career advice on its own."
)
DISCLAIMER_TA = (
    "பாவத்தின் பாவம் இரண்டாம் நிலை பராசர முறை. ஆதரவு வழி மட்டும் — "
    "தனி மருத்துவ/தொழில் ஆலோசனை அல்ல."
)


def compute_health_bhavat_bhavam(
    natal_chart: dict,
    *,
    maha: str = "",
    bhukti: str = "",
) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    asc_idx = asc.get("sign_index", 0)

    links = [
        evaluate_link(
            h,
            asc_sign_index=asc_idx,
            planet_positions=pp,
            maha=maha,
            bhukti=bhukti,
            slice_kind="health",
        )
        for h in HEALTH_PRIMARY_HOUSES
    ]
    active = [lk for lk in links if lk["primary_active"]]
    return {
        "slice": "health",
        "disclaimer": {"en": DISCLAIMER_EN, "ta": DISCLAIMER_TA},
        "links": active,
        "all_links": links,
        "active_count": len(active),
    }


def compute_career_bhavat_bhavam(
    natal_chart: dict,
    *,
    maha: str = "",
    bhukti: str = "",
) -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    asc_idx = asc.get("sign_index", 0)

    links = [
        evaluate_link(
            h,
            asc_sign_index=asc_idx,
            planet_positions=pp,
            maha=maha,
            bhukti=bhukti,
            slice_kind="career",
        )
        for h in CAREER_PRIMARY_HOUSES
    ]
    active = [lk for lk in links if lk["primary_active"]]
    return {
        "slice": "career",
        "disclaimer": {"en": DISCLAIMER_EN, "ta": DISCLAIMER_TA},
        "links": active,
        "all_links": links,
        "active_count": len(active),
    }
