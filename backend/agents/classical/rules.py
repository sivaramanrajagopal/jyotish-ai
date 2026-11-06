"""Match BPHS chapter 24 rules (house lords in houses) to a natal chart."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from agents.classical.facts import lord_facts

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "classical"

HOUSE_TOPICS: dict[int, list[str]] = {
    1: ["self", "health"],
    2: ["wealth", "family"],
    3: ["courage", "siblings"],
    4: ["home", "mother", "property"],
    5: ["children", "education"],
    6: ["health", "enemies", "service"],
    7: ["marriage", "partnership"],
    8: ["longevity", "occult"],
    9: ["fortune", "father", "dharma"],
    10: ["career", "status"],
    11: ["gains", "income"],
    12: ["expenses", "foreign"],
}

_STRENGTH_SHARE = {"full": "full effect", "half": "half effect", "quarter": "quarter effect"}

_DIGNITY_PHRASE = {
    "Exalted": "is exalted",
    "Own Sign": "is in its own sign",
    "Friend": "is in a friendly sign",
    "Enemy": "is in an enemy sign",
    "Debilitated": "is debilitated",
}


def _ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _names(planets: list[str]) -> str:
    if len(planets) <= 1:
        return "".join(planets)
    return ", ".join(planets[:-1]) + " and " + planets[-1]


@lru_cache(maxsize=1)
def load_verses() -> dict:
    data = json.loads((DATA_DIR / "bphs_ch24.json").read_text(encoding="utf-8"))
    data["by_verse"] = {v["verse"]: v for v in data["verses"]}
    return data


@lru_cache(maxsize=1)
def load_rules() -> list[dict]:
    data = json.loads((DATA_DIR / "bphs_ch24_rules.json").read_text(encoding="utf-8"))
    return data["rules"]


def _pick_variant(rule: dict, checks: dict) -> dict | None:
    for variant in rule["variants"]:
        if all(checks.get(key) == want for key, want in variant["when"].items()):
            return variant
    return None


def why_line(fact: dict) -> str:
    """Plain account of the chart facts behind a matched rule."""
    lord = fact["lord"]
    parts = [
        f"{lord}, lord of the {_ordinal(fact['house'])} ({fact['house_sign']}), "
        f"sits in {fact['lord_sign']} in the {_ordinal(fact['lord_house'])} house"
    ]
    parts.append(f"joined by {_names(fact['joined_by'])}" if fact["joined_by"] else "no planet joins it")
    parts.append(f"aspected by {_names(fact['aspected_by'])}" if fact["aspected_by"] else "no planet aspects it")
    line = "; ".join(parts) + "."
    traits = [f"counts as a {fact['lord_nature']} in this chart"]
    if fact["dignity"] in _DIGNITY_PHRASE:
        traits.append(_DIGNITY_PHRASE[fact["dignity"]])
    if fact["retrograde"]:
        traits.append("is retrograde")
    if fact["combust"]:
        traits.append("is combust")
    return f"{line} {lord} {_names(traits)}."


def _dual_lordship_notes(matches: list[dict]) -> list[dict]:
    """BPHS 24.146-147: a planet ruling two houses gives both results; equal opposite results cancel."""
    by_lord: dict[str, list[dict]] = {}
    for m in matches:
        by_lord.setdefault(m["lord"], []).append(m)
    notes = []
    for lord, rows in by_lord.items():
        if len(rows) < 2:
            continue
        tones = {r["tone"] for r in rows}
        houses = " and ".join(_ordinal(r["lord_of"]) for r in rows)
        if tones == {"favourable", "challenging"}:
            text = (
                f"{lord} rules the {houses} and the two results pull in opposite directions. "
                "Where they are evenly matched both weaken (verse 146); judge which house is stronger."
            )
        else:
            text = f"{lord} rules the {houses}, so both results apply (verse 147)."
        notes.append({"lord": lord, "houses": [r["lord_of"] for r in rows], "verses": [146, 147], "note": text})
    return notes


def match_rules(chart: dict, shadbala: dict | None = None) -> dict:
    """Rules that apply to this chart, one per house lord placement covered so far."""
    verses = load_verses()
    rules = {(r["lord_of"], r["in_house"]): r for r in load_rules()}
    matches = []
    pending = []
    for fact in lord_facts(chart, shadbala):
        rule = rules.get((fact["house"], fact["lord_house"]))
        if not rule:
            pending.append(fact["house"])
            continue
        variant = _pick_variant(rule, fact["checks"])
        if not variant:
            continue
        verse = verses["by_verse"][rule["verse"]]
        matches.append({
            "id": rule["id"],
            "lord_of": fact["house"],
            "in_house": fact["lord_house"],
            "lord": fact["lord"],
            "tone": variant["tone"],
            "summary": variant["summary"],
            "conditions": variant["when"],
            "why": why_line(fact),
            "strength": fact["strength"],
            "strength_label": _STRENGTH_SHARE.get(fact["strength"] or ""),
            "topics": sorted(set(HOUSE_TOPICS[fact["house"]] + HOUSE_TOPICS[fact["lord_house"]])),
            "status": rule.get("status", "draft"),
            "source": {
                "text": "BPHS",
                "chapter": verses["chapter"],
                "verse": rule["verse"],
                "cite": f"BPHS {verses['chapter']}.{rule['verse']}",
                "translation": verse["translation"],
                "sanskrit": verse["sanskrit"],
                "transliteration": verse["transliteration"],
            },
        })
    return {
        "source": {
            "text": verses["text"],
            "chapter": verses["chapter"],
            "chapter_title": verses["chapter_title"],
            "license": verses["license"],
            "attribution": verses["attribution"],
        },
        "matches": matches,
        "dual_lordship": _dual_lordship_notes(matches),
        "pending_houses": pending,
    }
