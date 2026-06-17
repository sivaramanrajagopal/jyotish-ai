"""
tamil_dosha_agent.py — Tamil predictive doshas for natal chart.

Thithi Soonyam, Mudakku (A/B), natal Vadhai/Vainasikam, Yogi/Avayogi.
"""

from __future__ import annotations

from agents.tamil_dosha.mudakku import compute_mudakku
from agents.tamil_dosha.red_zones import compute_natal_red_zones
from agents.tamil_dosha.thithi_soonyam import compute_thithi_soonyam
from agents.tamil_dosha.utils import nakshatra_index_from_longitude, rasi_label
from agents.tamil_dosha.yogi import compute_yogi


def _nak_index_from_planet(pdata: dict) -> int:
    from agents.tamil_dosha.constants import NAKSHATRA_ORDER
    nak = pdata.get("nakshatra")
    if nak and nak in NAKSHATRA_ORDER:
        return NAKSHATRA_ORDER.index(nak)
    return nakshatra_index_from_longitude(pdata.get("longitude", 0))


def compute_tamil_doshas(natal_chart: dict, *, shashti_variant: str = "mesha_simha") -> dict:
    asc = natal_chart.get("ascendant") or {}
    pp = natal_chart.get("planet_positions") or {}
    sun = pp.get("Sun") or {}
    moon = pp.get("Moon") or {}

    lagna_idx = asc.get("sign_index")
    if lagna_idx is None:
        from agents.tamil_dosha.utils import rasi_index_from_longitude
        lagna_idx = rasi_index_from_longitude(asc.get("longitude", 0))

    moon_nak_idx = _nak_index_from_planet(moon)
    sun_nak_idx = _nak_index_from_planet(sun)

    thithi = compute_thithi_soonyam(
        moon_lon=moon.get("longitude", 0),
        sun_lon=sun.get("longitude", 0),
        lagna_rasi_index=lagna_idx,
        shashti_variant=shashti_variant,
        planet_positions=pp,
    )
    mudakku = compute_mudakku(
        moon_rasi_index=moon.get("sign_index", 0),
        sun_rasi_index=sun.get("sign_index", 0),
        sun_nakshatra_index=sun_nak_idx,
        sun_nakshatra_pada=sun.get("pada", 1),
        lagna_rasi_index=lagna_idx,
    )
    red_zones = compute_natal_red_zones(moon_nak_idx)
    yogi = compute_yogi(sun_lon=sun.get("longitude", 0), moon_lon=moon.get("longitude", 0))

    return {
        "meta": {
            "lagna_rasi": rasi_label(lagna_idx),
            "moon_nakshatra": moon.get("nakshatra"),
            "sun_nakshatra": sun.get("nakshatra"),
            "shashti_variant": shashti_variant,
        },
        "summary": {
            "dagdha_count": len(thithi.get("dagdha_rasis") or []),
            "mudakku_methods_disagree": mudakku.get("methods_disagree", False),
            "yogi_graha": yogi.get("yogi_graha"),
            "vadhai_nakshatra": red_zones["vadhai"]["name"],
            "vainasikam_nakshatra": red_zones["vainasikam"]["name"],
        },
        "thithi_soonyam": thithi,
        "mudakku": mudakku,
        "red_zones": red_zones,
        "yogi": yogi,
    }


def dosha_context_for_narrator(natal_chart: dict) -> str:
    """Compact text block for AI chat / forecast context."""
    try:
        d = compute_tamil_doshas(natal_chart)
    except Exception:
        return ""
    t = d["thithi_soonyam"]
    rz = d["red_zones"]
    y = d["yogi"]
    dagdha = ", ".join(r["name"] for r in t.get("dagdha_rasis") or []) or "none"
    lines = [
        "Tamil predictive doshas (natal):",
        f"- Thithi Soonyam (dagdha): {dagdha}; houses {t.get('affected_houses')}",
        f"- Vadhai zone (7th from Moon): {rz['vadhai']['name']}",
        f"- Vainasikam zone (22nd from Moon): {rz['vainasikam']['name']}",
        f"- Yogi graha: {y['yogi_graha']}; Avayogi: {y['avayogi_graha']}",
        f"- Mudakku A: {d['mudakku']['method_a']['rasi']['name']} H{d['mudakku']['method_a']['house']}",
        f"- Mudakku B: {d['mudakku']['method_b']['rasi']['name']} H{d['mudakku']['method_b']['house']}",
    ]
    return "\n".join(lines)
