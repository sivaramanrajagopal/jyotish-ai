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
from agents.tamil_dosha.constants import SIGN_LORDS

# Whole-sign house themes for remedy framing (Parashari)
_HOUSE_THEMES = {
    1: "self, body, vitality",
    2: "wealth, speech, family",
    3: "courage, siblings, communication",
    4: "home, mother, peace of mind",
    5: "children, creativity, merit",
    6: "health, service, obstacles",
    7: "marriage, partnerships",
    8: "longevity, sudden change, inheritance",
    9: "dharma, fortune, father/guru",
    10: "career, status, karma",
    11: "gains, networks, aspirations",
    12: "expenses, moksha, rest",
}


def _house_lord(asc_sign_index: int, house: int) -> str:
    sign_idx = (int(asc_sign_index) + int(house) - 1) % 12
    return SIGN_LORDS[sign_idx]


def _remedy_seed(asc_sign_index: int, house: int, label: str) -> str:
    lord = _house_lord(asc_sign_index, house)
    theme = _HOUSE_THEMES.get(house, "life area")
    return (
        f"  H{house} ({theme}): lord {lord} — strengthen {lord} on its weekday; "
        f"charity/service aligned with {theme}; defer major new starts in this area "
        f"during malefic transits through dagdha/mudakku signs ({label})."
    )


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
    """Compact text block for AI chat — dosha facts + house-level remedy seeds."""
    try:
        d = compute_tamil_doshas(natal_chart)
    except Exception:
        return ""
    t = d["thithi_soonyam"]
    rz = d["red_zones"]
    y = d["yogi"]
    m = d["mudakku"]
    asc_idx = d["meta"]["lagna_rasi"]["index"]

    dagdha_parts = [
        f"{r['name']} (H{h})"
        for r, h in zip(t.get("dagdha_rasis") or [], t.get("affected_houses") or [])
    ]
    dagdha = ", ".join(dagdha_parts) or "none (exempt tithi)"

    in_dagdha = ", ".join(
        f"{p['planet']} in {p['sign']} H{p['house']}"
        for p in t.get("planets_in_dagdha") or []
    ) or "none"

    remedy_seeds: list[str] = []
    seen_houses: set[int] = set()
    for h in t.get("affected_houses") or []:
        if h not in seen_houses:
            remedy_seeds.append(_remedy_seed(asc_idx, h, "Thithi Soonyam"))
            seen_houses.add(h)
    for key in ("method_b", "method_a"):
        mh = m[key].get("house")
        if mh and mh not in seen_houses:
            tag = "Mudakku B (preferred)" if key == "method_b" else "Mudakku A (unverified)"
            remedy_seeds.append(_remedy_seed(asc_idx, mh, tag))
            seen_houses.add(mh)

    lines = [
        "=== TAMIL PREDICTIVE DOSHAS (natal — use for dosha / parihara questions) ===",
        f"Thithi Soonyam ({t.get('confidence')}): {t.get('tithi_name')} — dagdha {dagdha}",
        f"  Planets natally in dagdha: {in_dagdha}",
        f"Vadhai red zone (7th from Janma Moon): {rz['vadhai']['name']} (lord {rz['vadhai']['lord']})",
        f"Vainasikam red zone (22nd from Moon): {rz['vainasikam']['name']} (lord {rz['vainasikam']['lord']})",
        f"  Transit caution: avoid new ventures when Moon transits Vadhai or Vainasikam nakshatras.",
        f"Yogi graha ({y.get('confidence')}): {y['yogi_graha']} (duplicate yogi: {y['duplicate_yogi_graha']})",
        f"  Favour: strengthen {y['yogi_graha']} — activities on its weekday, dharma aligned with its nature.",
        f"Avayogi graha: {y['avayogi_graha']} — temperance; do not over-amplify this planet.",
        f"Mudakku A ({m['method_a']['confidence']}): {m['method_a']['rasi']['name']} H{m['method_a']['house']}",
        f"Mudakku B ({m['method_b']['confidence']}): {m['method_b']['rasi']['name']} H{m['method_b']['house']}",
        "",
        "HOUSE-SPECIFIC PARIHARA SEEDS (expand per house when user asks for remedies):",
        *remedy_seeds,
        "",
        "DOSHA REMEDY RULES FOR AI:",
        "- Cite only houses/planets listed above; map each to house lord from PLANETS section.",
        "- Give 2–4 practical parihara steps per affected house (weekday, charity, timing caution).",
        "- Prefer Mudakku Method B over A; label A as unverified if mentioned.",
        "- Do not invent Sanskrit mantras or guarantee results; classical lifestyle/timing guidance only.",
        "=== END TAMIL DOSHAS ===",
    ]
    return "\n".join(lines)
