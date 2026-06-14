"""Aggregate testimonies from all Prashna engines."""

from __future__ import annotations


def collect_testimonies(*groups: list[dict]) -> dict:
    positive, negative, neutral = [], [], []
    for group in groups:
        for t in group:
            entry = {
                "type": t.get("type", "general"),
                "category": t.get("category", "General"),
                "polarity": t.get("polarity", "neutral"),
                "description": t.get("description", ""),
            }
            if entry["polarity"] == "positive":
                positive.append(entry)
            elif entry["polarity"] == "negative":
                negative.append(entry)
            else:
                neutral.append(entry)
    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "counts": {
            "positive": len(positive),
            "negative": len(negative),
            "neutral": len(neutral),
            "total": len(positive) + len(negative) + len(neutral),
        },
    }
