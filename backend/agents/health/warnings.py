"""Health awareness scoring — D3 body parts + Dasa + transits."""

from __future__ import annotations

from collections import defaultdict

from agents.health.body_map import body_part_for_d3_house, drekkana_section_label
from agents.natal_agent import SIGN_LORDS, SIGNS

PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]
MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
HEALTH_HOUSES = frozenset({6, 8, 12})
SLOW_TRANSITS = frozenset({"Saturn", "Mars", "Rahu", "Ketu"})


def _lord_of_house(asc_sign_index: int, house: int) -> str:
    sign_idx = (int(asc_sign_index) + int(house) - 1) % 12
    return SIGN_LORDS[SIGNS[sign_idx]]


def _risk_label(score: float) -> str:
    if score >= 6:
        return "high"
    if score >= 3:
        return "moderate"
    return "low"


def build_planet_rows(
    *,
    d1_asc_idx: int,
    d1_positions: dict,
    d3_asc_idx: int,
    d3_positions: dict,
) -> list[dict]:
    rows: list[dict] = []
    for planet in PLANETS:
        if planet not in d3_positions or planet not in d1_positions:
            continue
        d1p = d1_positions[planet]
        d3p = d3_positions[planet]
        d1_deg = float(d1p.get("degree_in_sign", 0))
        d3_house = int(d3p.get("house", 0))
        body = body_part_for_d3_house(d3_house, d1_deg)
        rows.append({
            "planet": planet,
            "d1_house": int(d1p.get("house", 0)),
            "d3_house": d3_house,
            "d1_degree_in_sign": round(d1_deg, 2),
            "drekkana_section": body["section"],
            "drekkana_label_en": drekkana_section_label(body["section"], "en"),
            "drekkana_label_ta": drekkana_section_label(body["section"], "ta"),
            "body_part_en": body["en"],
            "body_part_ta": body["ta"],
            "body_zone": body["zone"],
            "retrograde": bool(d1p.get("retrograde")),
            "malefic": planet in MALEFICS,
            "health_house_d3": d3_house in HEALTH_HOUSES,
            "health_house_d1": int(d1p.get("house", 0)) in HEALTH_HOUSES,
        })
    return rows


def _zone_scores_from_rows(rows: list[dict]) -> dict[str, float]:
    scores: dict[str, float] = defaultdict(float)
    for row in rows:
        zone = row["body_zone"]
        s = 0.0
        if row["health_house_d3"]:
            s += 2.0
        if row["malefic"] and row["health_house_d3"]:
            s += 2.0
        if row["malefic"]:
            s += 0.5
        if row["health_house_d1"]:
            s += 0.5
        scores[zone] += s
    return dict(scores)


def apply_dasa_scores(
    zone_scores: dict[str, float],
    rows: list[dict],
    *,
    maha: str,
    bhukti: str,
    d1_asc_idx: int,
    d3_asc_idx: int,
) -> list[str]:
    """Boost zones linked to current MD/AD lords."""
    notes: list[str] = []
    lords = {maha, bhukti} - {""}
    sixth_d1 = _lord_of_house(d1_asc_idx, 6)
    eighth_d1 = _lord_of_house(d1_asc_idx, 8)
    twelfth_d1 = _lord_of_house(d1_asc_idx, 12)
    sixth_d3 = _lord_of_house(d3_asc_idx, 6)
    eighth_d3 = _lord_of_house(d3_asc_idx, 8)
    twelfth_d3 = _lord_of_house(d3_asc_idx, 12)
    health_lords = {sixth_d1, eighth_d1, twelfth_d1, sixth_d3, eighth_d3, twelfth_d3}

    for lord in lords:
        if lord in health_lords:
            notes.append(f"Dasa/Bhukti lord {lord} links health houses (6/8/12)")
        for row in rows:
            if row["planet"] == lord:
                zone_scores[row["body_zone"]] = zone_scores.get(row["body_zone"], 0) + 2.0
                notes.append(
                    f"{lord} MD/AD maps to {row['body_part_en']} (D3 H{row['d3_house']})"
                )
    return notes


def apply_transit_scores(
    zone_scores: dict[str, float],
    rows: list[dict],
    *,
    transit_positions: dict,
    d3_positions: dict,
    d3_asc_idx: int,
) -> list[str]:
    """Slow transits through D3 health houses and over natal malefics."""
    notes: list[str] = []
    if not transit_positions:
        return notes

    row_by_planet = {r["planet"]: r for r in rows}

    for tplanet in SLOW_TRANSITS:
        tdata = transit_positions.get(tplanet)
        if not tdata or tdata.get("sign_index") is None:
            continue
        t_house_d3 = (int(tdata["sign_index"]) - int(d3_asc_idx)) % 12 + 1
        if t_house_d3 in HEALTH_HOUSES:
            boost = 2.5 if tplanet == "Saturn" else 2.0
            notes.append(f"Transit {tplanet} in D3 house {t_house_d3}")
            for row in rows:
                if row["d3_house"] == t_house_d3:
                    zone_scores[row["body_zone"]] = zone_scores.get(row["body_zone"], 0) + boost

        t_sign = tdata.get("sign")
        for planet, row in row_by_planet.items():
            if not row["malefic"]:
                continue
            natal_d3_sign = (d3_positions.get(planet) or {}).get("sign")
            if natal_d3_sign and natal_d3_sign == t_sign and planet != tplanet:
                zone_scores[row["body_zone"]] = zone_scores.get(row["body_zone"], 0) + 1.0
                notes.append(f"Transit {tplanet} with natal {planet} in {t_sign}")

    return notes


def build_body_regions(zone_scores: dict[str, float]) -> list[dict]:
    zone_labels = {
        "head": {"en": "Head / face", "ta": "தலை / முகம்"},
        "neck": {"en": "Neck", "ta": "கழுத்து"},
        "chest": {"en": "Chest", "ta": "மார்பு"},
        "torso": {"en": "Torso / ribs", "ta": "விலா / முதுகு"},
        "abdomen": {"en": "Abdomen", "ta": "வயிறு"},
        "arms": {"en": "Arms / shoulders", "ta": "கை / தோள்"},
        "legs": {"en": "Legs / knees / feet", "ta": "கால் / முழங்கால் / பாதம்"},
        "pelvis": {"en": "Pelvis / reproductive", "ta": "இடுப்பு / இனப்பெருக்க உறுப்பு"},
    }
    regions = []
    for zone, score in sorted(zone_scores.items(), key=lambda x: -x[1]):
        labels = zone_labels.get(zone, {"en": zone, "ta": zone})
        regions.append({
            "zone": zone,
            "label_en": labels["en"],
            "label_ta": labels["ta"],
            "score": round(score, 1),
            "risk": _risk_label(score),
        })
    return regions


def build_warnings(
    rows: list[dict],
    *,
    dasa_notes: list[str],
    transit_notes: list[str],
    maha: str,
    bhukti: str,
) -> list[dict]:
    warnings: list[dict] = []
    for row in rows:
        score = 0.0
        reasons_en: list[str] = []
        reasons_ta: list[str] = []

        if row["health_house_d3"]:
            score += 2
            reasons_en.append(f"In D3 house {row['d3_house']} (health house)")
            reasons_ta.append(f"D3 {row['d3_house']}ம் வீடு (ஆரோக்கிய வீடு)")
        if row["malefic"] and row["health_house_d3"]:
            score += 2
            reasons_en.append(f"Malefic {row['planet']} in sensitive D3 house")
            reasons_ta.append(f"பாப கிரகம் {row['planet']} D3-ல்")
        if row["planet"] in (maha, bhukti):
            score += 2
            reasons_en.append(f"Active Dasa/Bhukti lord ({row['planet']})")
            reasons_ta.append(f"நடப்பு தசை/புத்தி அதிபதி ({row['planet']})")

        if score < 2:
            continue

        risk = _risk_label(score)
        warnings.append({
            "planet": row["planet"],
            "body_part_en": row["body_part_en"],
            "body_part_ta": row["body_part_ta"],
            "body_zone": row["body_zone"],
            "d3_house": row["d3_house"],
            "score": score,
            "risk": risk,
            "reasons_en": reasons_en,
            "reasons_ta": reasons_ta,
        })

    warnings.sort(key=lambda w: -w["score"])

    for note in dasa_notes[:3]:
        warnings.append({
            "planet": "",
            "body_part_en": "General",
            "body_part_ta": "பொது",
            "body_zone": "torso",
            "d3_house": 0,
            "score": 2.5,
            "risk": "moderate",
            "reasons_en": [note],
            "reasons_ta": [note],
        })

    for note in transit_notes[:3]:
        warnings.append({
            "planet": "",
            "body_part_en": "Transit",
            "body_part_ta": "கோசாரம்",
            "body_zone": "torso",
            "d3_house": 0,
            "score": 2.5,
            "risk": "moderate",
            "reasons_en": [note],
            "reasons_ta": [note],
        })

    return warnings[:12]
