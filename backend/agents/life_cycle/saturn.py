"""Saturn counted from the natal Moon: Sade Sati, Ardhashtama and Ashtama Sani.

Sade Sati: Saturn in the 12th, 1st and 2nd from the Moon sign (rising, peak, setting).
Ardhashtama (Kantaka) Sani: the 4th from the Moon. Ashtama Sani: the 8th from the Moon.
Saturn's sign comes from the same daily sky table as the double transit.
"""

from __future__ import annotations

from datetime import date, timedelta

from agents.nadi_agent import _fmt
from agents.natal_agent import SIGNS

PHASES = {
    12: ("sade_sati", "Sade Sati, rising (12th from Moon)", "ஏழரைச் சனி, தொடக்கம் (சந்திரனுக்கு 12)"),
    1: ("sade_sati", "Sade Sati, peak (over the Moon)", "ஏழரைச் சனி, ஜென்ம சனி"),
    2: ("sade_sati", "Sade Sati, setting (2nd from Moon)", "ஏழரைச் சனி, நிறைவு (சந்திரனுக்கு 2)"),
    4: ("ardhashtama", "Ardhashtama Sani (4th from Moon)", "அர்த்தாஷ்டம சனி (சந்திரனுக்கு 4)"),
    8: ("ashtama", "Ashtama Sani (8th from Moon)", "அஷ்டம சனி (சந்திரனுக்கு 8)"),
}
BLOCK = {
    "sade_sati": ("Sade Sati", "ஏழரைச் சனி"),
    "ardhashtama": ("Ardhashtama Sani", "அர்த்தாஷ்டம சனி"),
    "ashtama": ("Ashtama Sani", "அஷ்டம சனி"),
}
MEANING = {
    "sade_sati": (
        "A long stretch of pressure, responsibility and slow results; patience and steady work carry it.",
        "நீண்ட அழுத்தம், பொறுப்பு, மெதுவான பலன்; பொறுமையும் தொடர் உழைப்பும் உதவும்.",
    ),
    "ardhashtama": (
        "Home, mother, vehicles and peace of mind need attention.",
        "வீடு, தாய், வாகனம், மன அமைதி ஆகியவற்றில் கவனம் தேவை.",
    ),
    "ashtama": (
        "Obstacles and sudden changes; avoid risky ventures and look after health.",
        "தடைகள், திடீர் மாற்றங்கள்; ஆபத்தான முயற்சிகள் தவிர்த்து ஆரோக்கியம் காக்கவும்.",
    ),
}


def _from_moon(sign: int, moon: int) -> int:
    return (sign - moon) % 12 + 1


def saturn_from_moon(segments: list[dict], moon_sign: int, as_of: date, end: date) -> list[dict]:
    """Saturn phases from the Moon that are running now or start before the horizon ends."""
    runs: list[dict] = []
    for seg in segments:
        pos = _from_moon(seg["key"][1], moon_sign)
        if pos not in PHASES:
            continue
        if runs and runs[-1]["pos"] == pos and runs[-1]["end"] + timedelta(days=1) >= seg["start"]:
            runs[-1]["end"] = seg["end"]
        else:
            runs.append({"pos": pos, "sign": seg["key"][1], "start": seg["start"], "end": seg["end"]})

    blocks: list[dict] = []
    for run in runs:
        kind, en, ta = PHASES[run["pos"]]
        phase = {
            "from_moon": run["pos"],
            "sign": SIGNS[run["sign"]],
            "en": en,
            "ta": ta,
            "start": run["start"],
            "end": run["end"],
        }
        if blocks and blocks[-1]["kind"] == kind and blocks[-1]["end"] + timedelta(days=1) >= run["start"]:
            blocks[-1]["end"] = run["end"]
            blocks[-1]["phases"].append(phase)
        else:
            blocks.append({"kind": kind, "start": run["start"], "end": run["end"], "phases": [phase]})

    out = []
    for b in blocks:
        if b["end"] < as_of or b["start"] > end:
            continue
        mean_en, mean_ta = MEANING[b["kind"]]
        out.append({
            "kind": b["kind"],
            "en": BLOCK[b["kind"]][0],
            "ta": BLOCK[b["kind"]][1],
            "meaning_en": mean_en,
            "meaning_ta": mean_ta,
            "start": _fmt(b["start"]),
            "end": _fmt(b["end"]),
            "start_iso": b["start"].isoformat(),
            "end_iso": b["end"].isoformat(),
            "now": b["start"] <= as_of <= b["end"],
            "phases": [{
                **{k: v for k, v in p.items() if k not in ("start", "end")},
                "start": _fmt(p["start"]),
                "end": _fmt(p["end"]),
                "now": p["start"] <= as_of <= p["end"],
            } for p in b["phases"] if p["end"] >= as_of and p["start"] <= end],
        })
    return out


def overlapping(phases: list[dict], start: date, end: date) -> list[str]:
    """Names of the Saturn phases that overlap start..end."""
    names = []
    for p in phases:
        if date.fromisoformat(p["start_iso"]) <= end and date.fromisoformat(p["end_iso"]) >= start:
            if p["en"] not in names:
                names.append(p["en"])
    return names
