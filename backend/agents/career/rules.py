"""Ten core career rules (PDF10 / thesis matrix) — D1 + D10 whole sign."""

from __future__ import annotations

from agents.natal_agent import EXALTATION, SIGN_LORDS, SIGNS
from agents.career.atmakaraka import whole_sign_house

BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
MALEFICS = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})
KENDRA = frozenset({1, 4, 7, 10})
TRIKONA = frozenset({5, 9})
CAREER_PLANETS = frozenset({
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
})

OWN_SIGNS: dict[str, list[str]] = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

PDF10_LABELS = [
    ("1", "D1 planets in 10th"),
    ("2", "D1 10th lord placement"),
    ("3", "D1 10th lord in 10th"),
    ("4", "D10 planets in 10th"),
    ("5", "D10 10th lord strength"),
    ("6", "D10 Lagna lord strength"),
    ("7", "Atmakaraka in D10"),
    ("8", "Dasha linked to 10th lord"),
    ("9", "Sun/Mars/Saturn in D10 Kendra"),
    ("10", "Benefic/malefic in D10 Kendra"),
]


def _tenth_sign_index(asc_sign_index: int) -> int:
    return (int(asc_sign_index) + 9) % 12


def _lord_strength(planet: str, sign: str) -> list[str]:
    tags: list[str] = []
    if sign in OWN_SIGNS.get(planet, []):
        tags.append("own sign")
    ex_idx, _ = EXALTATION.get(planet, (-1, 0))
    if ex_idx >= 0 and SIGNS[ex_idx] == sign:
        tags.append("exalted")
    return tags


def _lord_strong_in_chart(
    lord: str,
    planet_positions: dict,
    asc_sign_index: int,
) -> tuple[bool, str]:
    if not lord or lord not in planet_positions:
        return False, f"{lord or '—'} not found"
    pdata = planet_positions[lord]
    sign = pdata.get("sign", "")
    house = whole_sign_house(pdata.get("sign_index", 0), asc_sign_index)
    tags = _lord_strength(lord, sign)
    if house in KENDRA:
        tags.append("Kendra")
    elif house in TRIKONA:
        tags.append("Trikona")
    return bool(tags), f"{lord} in {sign} H{house} ({', '.join(tags) if tags else 'neutral'})"


def _planets_in_house(planet_positions: dict, asc_idx: int, house: int) -> list[str]:
    out: list[str] = []
    for planet, pdata in planet_positions.items():
        if planet not in CAREER_PLANETS:
            continue
        h = whole_sign_house(pdata.get("sign_index", 0), asc_idx)
        if h == house:
            out.append(planet)
    return sorted(out)


def evaluate_pdf10_rules(
    *,
    asc_sign_index: int,
    planet_positions: dict,
    dasamsa_positions: dict,
    dasamsa_ascendant: dict,
    tenth_lord: str,
    ak_eval: dict,
    dasha_links_10th: bool,
) -> list[dict]:
    d10_asc_idx = dasamsa_ascendant.get("sign_index", 0)
    d10_10th_idx = _tenth_sign_index(d10_asc_idx)
    d10_10th_lord = SIGN_LORDS[SIGNS[d10_10th_idx]]
    d10_lagna_lord = dasamsa_ascendant.get("sign_lord", "")

    d1_in_10 = _planets_in_house(planet_positions, asc_sign_index, 10)
    d10_in_10 = _planets_in_house(dasamsa_positions, d10_asc_idx, 10)

    lord_pdata = planet_positions.get(tenth_lord) or {}
    lord_house = (
        whole_sign_house(lord_pdata["sign_index"], asc_sign_index)
        if lord_pdata.get("sign_index") is not None else None
    )
    lord_tags = _lord_strength(tenth_lord, lord_pdata.get("sign", ""))
    r2 = bool(lord_tags) or lord_house in (2, 3)
    r2_detail = f"{tenth_lord} H{lord_house} ({', '.join(lord_tags) if lord_tags else 'placement'})"

    r5_ok, r5_detail = _lord_strong_in_chart(d10_10th_lord, dasamsa_positions, d10_asc_idx)
    r6_ok, r6_detail = _lord_strong_in_chart(d10_lagna_lord, dasamsa_positions, d10_asc_idx)

    sms_kendra = any(
        whole_sign_house(dasamsa_positions[p]["sign_index"], d10_asc_idx) in KENDRA
        for p in ("Sun", "Mars", "Saturn")
        if p in dasamsa_positions
    )
    kendra_planets = [
        p for p, pdata in dasamsa_positions.items()
        if whole_sign_house(pdata.get("sign_index", 0), d10_asc_idx) in KENDRA
        and p in (BENEFICS | MALEFICS)
    ]

    checks = [
        ("1", bool(d1_in_10), f"Planets in D1 H10: {', '.join(d1_in_10) or 'none'}"),
        ("2", r2, r2_detail),
        ("3", lord_house == 10, f"{tenth_lord} in D1 H10" if lord_house == 10 else f"{tenth_lord} in D1 H{lord_house}"),
        ("4", bool(d10_in_10), f"Planets in D10 H10: {', '.join(d10_in_10) or 'none'}"),
        ("5", r5_ok, f"D10 10th lord — {r5_detail}"),
        ("6", r6_ok, f"D10 Lagna lord — {r6_detail}"),
        ("7", bool(ak_eval.get("rule_matched")), ak_eval.get("detail", "")),
        ("8", dasha_links_10th, "Mahadasha or Bhukti touches 10th lord in career timeline"),
        ("9", sms_kendra, "Sun/Mars/Saturn in D10 Kendra" if sms_kendra else "Not in D10 Kendra"),
        ("10", bool(kendra_planets), f"Kendra grahas: {', '.join(kendra_planets) or 'none'}"),
    ]

    rules: list[dict] = []
    for rule_id, label in PDF10_LABELS:
        matched, detail = next((m, d) for rid, m, d in checks if rid == rule_id)
        rules.append({
            "id": rule_id,
            "label": label,
            "matched": matched,
            "detail": detail,
        })
    return rules
