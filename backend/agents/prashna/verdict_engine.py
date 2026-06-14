"""Verdict from testimony counts — no fake confidence percentages."""

from __future__ import annotations


VERDICT_LABELS = {
    "likely_yes": "Likely Yes",
    "likely_no": "Likely No",
    "delayed": "Delayed",
    "obstructed": "Obstructed",
    "unclear": "Unclear",
    "possible_delayed": "Possible but Delayed",
}


def compute_verdict(testimonies: dict, moon_outcome: str) -> dict:
    pos = testimonies["counts"]["positive"]
    neg = testimonies["counts"]["negative"]
    total = testimonies["counts"]["total"]

    if total < 3:
        result = "unclear"
        explanation = (
            "Insufficient astrological testimonies were found to form a clear judgment. "
            "Consider rephrasing the question or consulting a qualified astrologer."
        )
    elif moon_outcome == "obstructive" and neg >= pos + 2:
        result = "obstructed"
        explanation = (
            "Multiple challenging testimonies together with an obstructive Moon suggest "
            "the matter may face significant blocks or delays."
        )
    elif pos >= 4 and neg <= 1:
        result = "likely_yes"
        explanation = (
            "Several supportive testimonies outweigh the challenges — the chart suggests "
            "a favourable inclination toward the question."
        )
    elif neg >= 4 and pos <= 1:
        result = "likely_no"
        explanation = (
            "Challenging testimonies dominate — the chart suggests the matter is unlikely "
            "to resolve favourably in the near term."
        )
    elif abs(pos - neg) <= 1 and neg >= 2:
        result = "possible_delayed"
        explanation = (
            "Testimonies are balanced with notable challenges — the matter is possible "
            "but may be delayed or require sustained effort."
        )
    elif neg > pos + 1:
        result = "likely_no"
        explanation = "Negative testimonies exceed positive ones — unfavourable indications prevail."
    elif pos > neg + 1:
        result = "likely_yes"
        explanation = "Positive testimonies exceed negative ones — favourable indications prevail."
    else:
        result = "delayed"
        explanation = (
            "Mixed testimonies with delay factors — progress is indicated but not immediate."
        )

    return {
        "result": result,
        "label": VERDICT_LABELS.get(result, result),
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": testimonies["counts"]["neutral"],
        "explanation": explanation,
    }
