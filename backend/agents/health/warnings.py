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
TRANSIT_PLANETS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]

SIGN_TA = {
    "Aries": "மேஷம்", "Taurus": "ரிஷபம்", "Gemini": "மிதுனம்",
    "Cancer": "கடகம்", "Leo": "சிம்மம்", "Virgo": "கன்னி",
    "Libra": "துலாம்", "Scorpio": "விருச்சிகம்", "Sagittarius": "தனுசு",
    "Capricorn": "மகரம்", "Aquarius": "கும்பம்", "Pisces": "மீனம்",
}


def _lord_of_house(asc_sign_index: int, house: int) -> str:
    sign_idx = (int(asc_sign_index) + int(house) - 1) % 12
    return SIGN_LORDS[SIGNS[sign_idx]]


def _whole_sign_house(planet_sign_index: int, asc_sign_index: int) -> int:
    return (int(planet_sign_index) - int(asc_sign_index)) % 12 + 1


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
) -> list[dict]:
    """Dasa factors as structured items (no duplicate body-part lines)."""
    items: list[dict] = []
    lords = {maha, bhukti} - {""}
    health_lords = {
        _lord_of_house(d1_asc_idx, h) for h in (6, 8, 12)
    } | {
        _lord_of_house(d3_asc_idx, h) for h in (6, 8, 12)
    }

    for lord in sorted(lords):
        row = next((r for r in rows if r["planet"] == lord), None)
        if row:
            zone_scores[row["body_zone"]] = zone_scores.get(row["body_zone"], 0) + 2.0
        if lord in health_lords:
            items.append({
                "text_en": f"{lord} (Mahadasha or Bhukti) rules a health house (6/8/12) in D1 or D3",
                "text_ta": f"{lord} (மகாதசை/புத்தி) D1/D3-ல் ஆரோக்கிய வீடு (6/8/12) அதிபதி",
            })
    return items


def apply_transit_scores(
    zone_scores: dict[str, float],
    rows: list[dict],
    *,
    transit_positions: dict,
    d3_positions: dict,
    d3_asc_idx: int,
    d1_asc_idx: int,
) -> list[dict]:
    """Transit factors with D1 + D3 house context and Tamil labels."""
    items: list[dict] = []
    if not transit_positions:
        return items

    row_by_planet = {r["planet"]: r for r in rows}

    for tplanet in SLOW_TRANSITS:
        tdata = transit_positions.get(tplanet)
        if not tdata or tdata.get("sign_index") is None:
            continue
        sign = tdata.get("sign", "")
        sign_ta = SIGN_TA.get(sign, sign)
        sign_idx = int(tdata["sign_index"])
        deg = float(tdata.get("degree_in_sign", 0))
        house_d1 = _whole_sign_house(sign_idx, d1_asc_idx)
        house_d3 = _whole_sign_house(sign_idx, d3_asc_idx)
        body = body_part_for_d3_house(house_d3, deg)

        if house_d3 in HEALTH_HOUSES:
            boost = 2.5 if tplanet == "Saturn" else 2.0
            for row in rows:
                if row["d3_house"] == house_d3:
                    zone_scores[row["body_zone"]] = zone_scores.get(row["body_zone"], 0) + boost
            items.append({
                "planet": tplanet,
                "sign": sign,
                "sign_ta": sign_ta,
                "house_d1": house_d1,
                "house_d3": house_d3,
                "body_part_en": body["en"],
                "body_part_ta": body["ta"],
                "health_sensitive": True,
                "text_en": (
                    f"Transit {tplanet} in {sign} — D1 H{house_d1}, D3 H{house_d3} "
                    f"({body['en']})"
                ),
                "text_ta": (
                    f"கோசார {tplanet} {sign_ta}-ல் — D1 {house_d1}, D3 {house_d3} "
                    f"({body['ta']})"
                ),
            })
        elif house_d1 in HEALTH_HOUSES:
            items.append({
                "planet": tplanet,
                "sign": sign,
                "sign_ta": sign_ta,
                "house_d1": house_d1,
                "house_d3": house_d3,
                "body_part_en": "",
                "body_part_ta": "",
                "health_sensitive": True,
                "text_en": f"Transit {tplanet} in {sign} — D1 health house H{house_d1}",
                "text_ta": f"கோசார {tplanet} {sign_ta}-ல் — D1 ஆரோக்கிய வீடு {house_d1}",
            })

        t_sign = sign
        for planet, row in row_by_planet.items():
            if not row["malefic"]:
                continue
            natal_d3_sign = (d3_positions.get(planet) or {}).get("sign")
            if natal_d3_sign and natal_d3_sign == t_sign and planet != tplanet:
                zone_scores[row["body_zone"]] = zone_scores.get(row["body_zone"], 0) + 1.0
                items.append({
                    "planet": tplanet,
                    "sign": sign,
                    "sign_ta": sign_ta,
                    "house_d1": house_d1,
                    "house_d3": house_d3,
                    "natal_planet": planet,
                    "body_part_en": row["body_part_en"],
                    "body_part_ta": row["body_part_ta"],
                    "health_sensitive": True,
                    "text_en": (
                        f"Transit {tplanet} conjunct natal {planet} in {sign} "
                        f"→ {row['body_part_en']}"
                    ),
                    "text_ta": (
                        f"கோசார {tplanet} ஜாதக {planet}-உடன் {sign_ta}-ல் — {row['body_part_ta']}"
                    ),
                })

    return items


def build_transit_today(
    transit_positions: dict,
    *,
    d1_asc_idx: int,
    d3_asc_idx: int,
) -> list[dict]:
    """Full sky snapshot for today with D1/D3 houses."""
    out: list[dict] = []
    for planet in TRANSIT_PLANETS:
        tdata = transit_positions.get(planet)
        if not tdata or tdata.get("sign_index") is None:
            continue
        sign = tdata.get("sign", "")
        sign_idx = int(tdata["sign_index"])
        deg = float(tdata.get("degree_in_sign", 0))
        house_d1 = _whole_sign_house(sign_idx, d1_asc_idx)
        house_d3 = _whole_sign_house(sign_idx, d3_asc_idx)
        body = body_part_for_d3_house(house_d3, deg)
        sensitive = house_d1 in HEALTH_HOUSES or house_d3 in HEALTH_HOUSES
        out.append({
            "planet": planet,
            "sign": sign,
            "sign_ta": SIGN_TA.get(sign, sign),
            "degree_in_sign": round(deg, 2),
            "house_d1": house_d1,
            "house_d3": house_d3,
            "body_part_en": body["en"] if house_d3 in HEALTH_HOUSES else "",
            "body_part_ta": body["ta"] if house_d3 in HEALTH_HOUSES else "",
            "health_sensitive": sensitive,
            "slow": planet in SLOW_TRANSITS,
        })
    return out


def build_d3_natal_factors(
    rows: list[dict],
    *,
    maha: str,
    bhukti: str,
) -> list[dict]:
    """Natal D3 body-part factors (malefics in 6/8/12 + active dasa lords)."""
    factors: list[dict] = []
    for row in rows:
        score = 0.0
        tags: list[str] = ["D3"]
        reasons_en: list[str] = []
        reasons_ta: list[str] = []

        if row["health_house_d3"]:
            score += 2
            reasons_en.append(f"D3 house {row['d3_house']} (health house)")
            reasons_ta.append(f"D3 {row['d3_house']}ம் வீடு")
        if row["malefic"] and row["health_house_d3"]:
            score += 2
            reasons_en.append(f"Malefic {row['planet']}")
            reasons_ta.append(f"பாப கிரகம் {row['planet']}")
        if row["planet"] in (maha, bhukti):
            score += 2
            tags.append("Dasa")
            reasons_en.append("Active Dasa/Bhukti lord")
            reasons_ta.append("நடப்பு தசை/புத்தி அதிபதி")

        if score < 2:
            continue

        factors.append({
            "planet": row["planet"],
            "body_part_en": row["body_part_en"],
            "body_part_ta": row["body_part_ta"],
            "body_zone": row["body_zone"],
            "d3_house": row["d3_house"],
            "d1_house": row["d1_house"],
            "score": score,
            "risk": _risk_label(score),
            "tags": tags,
            "reasons_en": reasons_en,
            "reasons_ta": reasons_ta,
        })

    factors.sort(key=lambda f: -f["score"])
    return factors


def build_factor_groups(
    rows: list[dict],
    *,
    dasa_items: list[dict],
    transit_items: list[dict],
    maha: str,
    bhukti: str,
) -> dict:
    return {
        "d3_natal": build_d3_natal_factors(rows, maha=maha, bhukti=bhukti),
        "dasa": dasa_items,
        "transit": transit_items,
    }


def enrich_body_regions_rationale(
    regions: list[dict],
    rows: list[dict],
    d3_natal: list[dict],
    transit_items: list[dict],
) -> list[dict]:
    """Attach short EN/TA explanations for why each body zone is scored."""
    en_parts: dict[str, list[str]] = defaultdict(list)
    ta_parts: dict[str, list[str]] = defaultdict(list)

    for f in d3_natal:
        z = f["body_zone"]
        en_parts[z].append(f"{f['planet']} D3 H{f['d3_house']} → {f['body_part_en']}")
        ta_parts[z].append(f"{f['planet']} D3 {f['d3_house']} → {f['body_part_ta']}")

    part_to_zone = {r["body_part_en"]: r["body_zone"] for r in rows}
    for t in transit_items:
        bp_en = t.get("body_part_en") or ""
        bp_ta = t.get("body_part_ta") or ""
        if not bp_en:
            continue
        z = part_to_zone.get(bp_en)
        if z:
            en_parts[z].append(f"Transit {t['planet']} → {bp_en}")
            ta_parts[z].append(f"கோசார {t['planet']} → {bp_ta}")

    for region in regions:
        z = region["zone"]
        triggers_en = en_parts.get(z, [])
        triggers_ta = ta_parts.get(z, [])
        region["rationale_en"] = "; ".join(triggers_en[:3]) if triggers_en else ""
        region["rationale_ta"] = "; ".join(triggers_ta[:3]) if triggers_ta else ""

    return regions


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


def flatten_warnings_for_chat(factor_groups: dict) -> list[dict]:
    """Compact list for narrator / legacy consumers."""
    flat: list[dict] = []
    for f in factor_groups.get("d3_natal", []):
        flat.append({
            "body_part_en": f["body_part_en"],
            "reasons_en": f.get("reasons_en", []),
        })
    for d in factor_groups.get("dasa", []):
        flat.append({"body_part_en": "Dasa", "reasons_en": [d["text_en"]]})
    for t in factor_groups.get("transit", []):
        flat.append({"body_part_en": "Transit", "reasons_en": [t["text_en"]]})
    return flat[:12]
