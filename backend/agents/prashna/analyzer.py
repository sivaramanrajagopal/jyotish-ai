"""Main Prashna analysis orchestrator."""

from __future__ import annotations

from agents.prashna.constants import (
    CATEGORY_HOUSE,
    CATEGORY_LABELS,
    PRASHNA_DISCLAIMER,
    resolve_question,
)
from agents.prashna.chart_engine import (
    cast_prashna_chart,
    resolve_prashna_location,
)
from agents.prashna.lagna_engine import analyze_lagna, lagna_testimonies
from agents.prashna.house_engine import analyze_relevant_house, house_lord_testimonies
from agents.prashna.occupancy_engine import analyze_occupants
from agents.prashna.aspect_engine import aspects_to_house
from agents.prashna.moon_engine import analyze_moon, moon_testimonies
from agents.prashna.significator_engine import analyze_significators, significator_testimonies
from agents.prashna.timing_engine import estimate_timing
from agents.prashna.testimony_engine import collect_testimonies
from agents.prashna.verdict_engine import compute_verdict
from agents.prashna.interpretation_engine import generate_interpretation


def analyze_prashna(
    question: str,
    category: str,
    timestamp_iso: str,
    timezone: str = "Asia/Kolkata",
    lat: float | None = None,
    lon: float | None = None,
    place: str | None = None,
    question_id: str | None = None,
) -> dict:
    cat = category.lower().strip()
    if cat not in CATEGORY_HOUSE:
        raise ValueError(f"Unknown category: {category}")

    qid, qtext = resolve_question(cat, question_id, question)
    house_num = CATEGORY_HOUSE[cat]
    category_label = CATEGORY_LABELS[cat]

    plat, plon, place_label = resolve_prashna_location(lat, lon, place)
    tz_use = timezone

    chart = cast_prashna_chart(timestamp_iso, tz_use, plat, plon)
    chart["prashna_moment"]["place_label"] = place_label

    lagna = analyze_lagna(chart)
    relevant = analyze_relevant_house(chart, house_num, category_label)
    occupants = analyze_occupants(chart, house_num, relevant["occupants"])
    aspects = aspects_to_house(chart, house_num)
    moon = analyze_moon(chart, house_num)
    significators = analyze_significators(
        chart,
        lagna["lagna_lord"],
        relevant["house_lord"],
    )
    timing = estimate_timing(chart, house_num)

    aspect_testimonies = [
        {
            "type": "aspect",
            "category": f"Aspect ({a['planet']})",
            "polarity": a["polarity"],
            "description": a["description"],
        }
        for a in aspects
    ]

    testimonies = collect_testimonies(
        lagna_testimonies(lagna),
        house_lord_testimonies(relevant),
        occupants,
        aspect_testimonies,
        moon_testimonies(moon),
        significator_testimonies(significators),
    )

    verdict = compute_verdict(testimonies, moon["outcome"])
    interpretation = generate_interpretation(
        qtext,
        category_label,
        verdict,
        testimonies,
        moon,
        timing,
        lagna,
        relevant,
    )

    return {
        "question": {
            "id": qid,
            "text": qtext.strip(),
            "category": cat,
            "category_label": category_label,
            "timestamp": chart["prashna_moment"]["iso"],
            "timezone": tz_use,
            "location": {
                "lat": plat,
                "lon": plon,
                "place": place_label,
            },
        },
        "chart": {
            "ascendant": chart["ascendant"],
            "planet_positions": chart["planet_positions"],
            "house_signs": chart["house_signs"],
            "ayanamsa": chart["ayanamsa"],
            "ayanamsa_value": chart["ayanamsa_value"],
            "moment": chart["prashna_moment"],
        },
        "analysis": {
            "lagna": lagna,
            "relevant_house": relevant,
            "moon": moon,
            "significators": significators,
            "timing": timing,
            "occupants": occupants,
            "aspects": aspects,
        },
        "testimonies": testimonies,
        "verdict": verdict,
        "interpretation": interpretation,
        "disclaimer": PRASHNA_DISCLAIMER,
    }
