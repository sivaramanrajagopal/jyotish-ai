"""Transparent calculation audit for Prashna — verify chart, lords, aspects, verdict."""

from __future__ import annotations

from agents.prashna.significator_engine import (
    CONJUNCTION_ORB,
    _angular_distance,
    _in_conjunction,
)
from agents.transit_score_agent import _planet_aspects


def _planet_row(
    name: str,
    data: dict,
    roles: list[str],
    used_in: list[str],
) -> dict:
    retro = data.get("retrograde", False)
    return {
        "planet": name,
        "sign": data.get("sign", ""),
        "degree_in_sign": data.get("degree_in_sign"),
        "longitude": data.get("longitude"),
        "house": data.get("house"),
        "nakshatra": data.get("nakshatra", ""),
        "pada": data.get("pada"),
        "retrograde": retro,
        "roles": roles,
        "used_in": used_in,
    }


def _significator_checks(chart: dict, lagna_lord: str, matter_lord: str) -> list[dict]:
    ll = chart["planet_positions"][lagna_lord]
    ml = chart["planet_positions"][matter_lord]
    checks: list[dict] = []

    if lagna_lord == matter_lord:
        checks.append({
            "check": "Same planet rules Lagna and matter-house",
            "result": "Yes",
            "detail": f"{lagna_lord} is both querent and quesited significator.",
        })
        return checks

    orb_deg = round(_angular_distance(ll["longitude"], ml["longitude"]), 2)
    conj = _in_conjunction(chart, lagna_lord, matter_lord)
    checks.append({
        "check": f"Conjunction (≤{CONJUNCTION_ORB}° orb)",
        "result": "Yes" if conj else "No",
        "detail": f"Separation {orb_deg}° — {lagna_lord} {ll['sign']} {ll.get('degree_in_sign', 0):.2f}° vs "
                  f"{matter_lord} {ml['sign']} {ml.get('degree_in_sign', 0):.2f}°",
    })
    checks.append({
        "check": "Same sign",
        "result": "Yes" if ll["sign"] == ml["sign"] else "No",
        "detail": f"{lagna_lord} in {ll['sign']}, {matter_lord} in {ml['sign']}",
    })
    checks.append({
        "check": "Same house",
        "result": "Yes" if ll["house"] == ml["house"] else "No",
        "detail": f"{lagna_lord} H{ll['house']}, {matter_lord} H{ml['house']}",
    })

    ll_asp = set(_planet_aspects(lagna_lord, ll["house"]))
    ml_asp = set(_planet_aspects(matter_lord, ml["house"]))
    linked = ml["house"] in ll_asp or ll["house"] in ml_asp
    checks.append({
        "check": "Mutual drishti (house-based)",
        "result": "Yes" if linked else "No",
        "detail": (
            f"{lagna_lord} aspects houses {sorted(ll_asp)}; "
            f"{matter_lord} aspects houses {sorted(ml_asp)}"
        ),
    })
    return checks


def _verdict_rule_label(verdict: dict, moon_outcome: str, counts: dict) -> str:
    pos = counts.get("positive", 0)
    neg = counts.get("negative", 0)
    total = counts.get("total", 0)
    result = verdict.get("result", "")

    if total < 3:
        return "Fewer than 3 testimonies → Unclear"
    if result == "obstructed":
        return f"Moon obstructive + challenging testimonies ({neg} challenging vs {pos} supportive)"
    if result == "likely_yes" and pos >= 4 and neg <= 1:
        return f"≥4 supportive and ≤1 challenging ({pos}🟢 / {neg}🔴)"
    if result == "likely_no" and neg >= 4 and pos <= 1:
        return f"≥4 challenging and ≤1 supportive ({neg}🔴 / {pos}🟢)"
    if result == "possible_delayed":
        return f"Balanced testimonies with challenges ({pos}🟢 / {neg}🔴), Moon: {moon_outcome}"
    if result == "likely_yes":
        return f"Supportive exceed challenging ({pos}🟢 / {neg}🔴)"
    if result == "likely_no":
        return f"Challenging exceed supportive ({neg}🔴 / {pos}🟢)"
    if result == "delayed":
        return f"Mixed testimonies ({pos}🟢 / {neg}🔴 / {counts.get('neutral', 0)}⚪)"
    return verdict.get("explanation", "")


def build_calculation_audit(
    *,
    question: dict,
    chart: dict,
    house_num: int,
    lagna: dict,
    relevant: dict,
    moon: dict,
    significators: dict,
    aspects: list[dict],
    occupants: list[dict],
    testimonies: dict,
    verdict: dict,
) -> dict:
    """Structured audit trail for UI verification table."""
    asc = chart.get("ascendant", {})
    moment = chart.get("moment", {})
    positions = chart.get("planet_positions", {})
    lagna_lord = lagna.get("lagna_lord", "")
    matter_lord = relevant.get("house_lord", "")

    aspect_planets = {a["planet"] for a in aspects}
    occupant_names = {o["planet"] for o in occupants}

    planet_rows = []
    for name, data in positions.items():
        roles: list[str] = []
        used: list[str] = []
        if name == lagna_lord:
            roles.append("Querent (Lagna lord)")
            used.append("Lagna analysis")
        if name == matter_lord:
            roles.append("Quesited (matter-house lord)")
            used.append("Matter-house analysis")
        if name in occupant_names:
            roles.append(f"Occupant H{house_num}")
            used.append("Occupancy testimony")
        if name in aspect_planets:
            roles.append(f"Aspects H{house_num}")
            used.append("Aspect testimony")
        if name == "Moon":
            used.append("Moon analysis")
        if not roles:
            roles.append("—")
        if not used:
            used.append("Chart reference")
        planet_rows.append(_planet_row(name, data, roles, used))

    counts = testimonies.get("counts", {})
    moon_outcome = moon.get("outcome", "neutral")

    return {
        "method": {
            "engine": "Parashara rule-based Prashna",
            "ephemeris": "Swiss Ephemeris (sidereal Lahiri)",
            "houses": "Whole Sign",
            "note": (
                "Real chart at question moment — no random planets, degrees, or probability rolls. "
                f"Conjunction uses {CONJUNCTION_ORB}° longitude orb."
            ),
        },
        "moment": {
            "timestamp_iso": question.get("timestamp") or moment.get("iso"),
            "date": moment.get("date"),
            "time": moment.get("time"),
            "timezone": question.get("timezone"),
            "place": question.get("location", {}).get("place"),
            "latitude": question.get("location", {}).get("lat"),
            "longitude": question.get("location", {}).get("lon"),
            "ayanamsa": chart.get("ayanamsa"),
            "ayanamsa_value": chart.get("ayanamsa_value"),
        },
        "question": {
            "text": question.get("text"),
            "category": question.get("category"),
            "category_label": question.get("category_label"),
            "question_id": question.get("id"),
        },
        "matter_house": {
            "house_num": house_num,
            "house_sign": relevant.get("house_sign"),
            "category_label": relevant.get("category_label"),
            "house_lord": matter_lord,
            "lord_sign": relevant.get("house_lord_sign"),
            "lord_house": relevant.get("house_lord_house"),
            "lord_dignity": relevant.get("lord_dignity"),
            "lord_strength": relevant.get("lord_strength_label"),
            "occupants": relevant.get("occupants") or [],
        },
        "lagna": {
            "sign": asc.get("sign") or lagna.get("ascendant_sign"),
            "degree_in_sign": asc.get("degree_in_sign"),
            "nakshatra": asc.get("nakshatra"),
            "pada": asc.get("pada"),
            "lagna_lord": lagna_lord,
            "lord_sign": lagna.get("lagna_lord_sign"),
            "lord_house": lagna.get("lagna_lord_house"),
            "dignity": lagna.get("dignity"),
            "strength": lagna.get("strength_label"),
        },
        "significators": {
            "querent_lord": lagna_lord,
            "quesited_lord": matter_lord,
            "connection": significators.get("connection"),
            "connection_label": significators.get("connection_label"),
            "explanation": significators.get("explanation"),
            "checks": _significator_checks(
                {"planet_positions": positions},
                lagna_lord,
                matter_lord,
            ),
        },
        "aspects_to_matter_house": [
            {
                "planet": a.get("planet"),
                "from_house": a.get("from_house"),
                "target_house": a.get("target_house"),
                "polarity": a.get("polarity"),
                "description": a.get("description"),
            }
            for a in aspects
        ],
        "moon": {
            "sign": moon.get("moon_sign"),
            "house": moon.get("moon_house"),
            "nakshatra": moon.get("moon_nakshatra"),
            "nakshatra_lord": moon.get("moon_nakshatra_lord"),
            "pada": moon.get("moon_pada"),
            "dignity": moon.get("dignity"),
            "strength": moon.get("strength_label"),
            "relation_to_matter": moon.get("relation_to_matter"),
            "outcome": moon_outcome,
        },
        "occupants": [
            {
                "planet": o.get("planet"),
                "sign": o.get("sign"),
                "dignity": o.get("dignity"),
                "polarity": o.get("polarity"),
                "description": o.get("description"),
            }
            for o in occupants
        ],
        "planets": planet_rows,
        "testimonies_summary": [
            {
                "polarity": t.get("polarity"),
                "category": t.get("category"),
                "type": t.get("type"),
                "description": t.get("description"),
            }
            for group in ("positive", "negative", "neutral")
            for t in testimonies.get(group, [])
        ],
        "verdict_logic": {
            "result": verdict.get("result"),
            "label": verdict.get("label"),
            "positive_count": counts.get("positive", 0),
            "negative_count": counts.get("negative", 0),
            "neutral_count": counts.get("neutral", 0),
            "total_testimonies": counts.get("total", 0),
            "moon_outcome": moon_outcome,
            "rule_applied": _verdict_rule_label(verdict, moon_outcome, counts),
        },
    }
