"""Rule-based interpretation — no AI fabrication."""

from __future__ import annotations


def generate_interpretation(
    question: str,
    category_label: str,
    verdict: dict,
    testimonies: dict,
    moon: dict,
    timing: dict,
    lagna: dict,
    relevant_house: dict,
) -> dict:
    pos = testimonies["positive"]
    neg = testimonies["negative"]

    summary = (
        f"For your {category_label.lower()} question, the Prashna chart cast at the moment "
        f"of inquiry indicates a verdict of \"{verdict['label']}\". "
        f"{verdict['explanation']} "
        "This is a traditional rule-based reading, not a guarantee."
    )

    positive_factors = [t["description"] for t in pos[:6]] or [
        "No strongly positive testimonies were isolated — review neutral factors below."
    ]
    challenges = [t["description"] for t in neg[:6]] or [
        "No strongly challenging testimonies were isolated."
    ]

    timing_text = (
        f"{timing['timing_band']}: {timing['explanation']} "
        f"{timing['note']}"
    )

    guidance = _practical_guidance(verdict["result"], moon["outcome"], category_label)

    return {
        "summary": summary,
        "positive_factors": positive_factors,
        "challenges": challenges,
        "timing_indication": timing_text,
        "practical_guidance": guidance,
    }


def _practical_guidance(verdict_result: str, moon_outcome: str, category: str) -> str:
    base = {
        "likely_yes": (
            "Conditions appear supportive. Proceed with clarity and appropriate action, "
            "while remaining aware that astrological indications are not certainties."
        ),
        "likely_no": (
            "Consider alternative approaches or timing. Reflect on whether the question "
            "itself needs refinement before acting."
        ),
        "delayed": (
            "Patience is advised. Use the waiting period to strengthen preparation "
            "rather than forcing an outcome."
        ),
        "obstructed": (
            "Identify concrete obstacles. Address Saturn- or Mars-type challenges "
            "(delays, conflicts) through patience and structured effort."
        ),
        "unclear": (
            "The chart does not give a clear testimony. You may ask again with a "
            "specific, sincere question when the mind is calm."
        ),
        "possible_delayed": (
            "The matter may succeed with persistence. Avoid impulsive decisions; "
            "steady effort is indicated."
        ),
    }.get(verdict_result, "Proceed thoughtfully and avoid treating this as certain prediction.")

    if moon_outcome == "obstructive":
        base += " The Moon's obstructive placement suggests emotional clarity and calm timing matter."
    return base
