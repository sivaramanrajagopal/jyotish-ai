"""Extract BPHS chapter 24 (house lords in houses) into backend/data/classical.

Source: Hugging Face dataset JDhruv14/Brihat_Parashara_Hora_Shastra (Apache-2.0).
Run once with network access:  python scripts/extract_bphs.py
"""

from __future__ import annotations

import csv
import io
import json
import re
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://huggingface.co/datasets/JDhruv14/Brihat_Parashara_Hora_Shastra"
    "/resolve/main/parashara_data.csv"
)
CHAPTER = 24
OUT = Path(__file__).resolve().parent.parent / "data" / "classical" / "bphs_ch24.json"

# Words in a translation that mean the verse adds a condition the matcher must check.
CONDITION_WORDS = re.compile(
    r"\b(benefic|malefic|aspect|conjunct|conjunction|associated|joined|"
    r"strong|strength|weak|exalt|debilit|own sign|afflicted)\w*",
    re.IGNORECASE,
)


# Verses whose wording in the dataset disagrees with their place in the chapter.
SOURCE_NOTES = {
    37: (
        "The dataset reads 'dhanage' (in the 2nd) here, repeating verse 38. The chapter's "
        "order and standard editions place this verse at the 4th lord in the lagna."
    ),
}


def placement_for_verse(verse: int) -> tuple[int, int] | None:
    """Verses 1-144 run lord by lord: verse 1 = 1st lord in 1st, verse 13 = 2nd lord in 1st."""
    if not 1 <= verse <= 144:
        return None
    return (verse - 1) // 12 + 1, (verse - 1) % 12 + 1


def extract(csv_text: str) -> dict:
    rows = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    verses = []
    for row in rows:
        if int(float(row["chapter_no"])) != CHAPTER:
            continue
        verse = int(float(row["verse_no"]))
        placement = placement_for_verse(verse)
        translation = row["translation"].strip()
        verses.append({
            "verse": verse,
            "lord_of": placement[0] if placement else None,
            "in_house": placement[1] if placement else None,
            "sanskrit": row["sanskrit"].strip(),
            "transliteration": row["transliteration"].strip(),
            "translation": translation,
            "condition_hints": sorted({m.lower() for m in CONDITION_WORDS.findall(translation)}),
            "source_note": SOURCE_NOTES.get(verse),
        })
    verses.sort(key=lambda v: v["verse"])
    if [v["verse"] for v in verses] != list(range(1, 149)):
        raise SystemExit("Chapter 24 should have verses 1-148 with no gaps.")
    return {
        "text": "Brihat Parashara Hora Shastra",
        "chapter": CHAPTER,
        "chapter_title": "Effects of the house lords placed in the houses",
        "source_url": SOURCE_URL,
        "license": "Apache-2.0",
        "attribution": "JDhruv14/Brihat_Parashara_Hora_Shastra on Hugging Face",
        "verses": verses,
    }


def main() -> None:
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as resp:
        csv_text = resp.read().decode("utf-8")
    data = extract(csv_text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    flagged = sum(1 for v in data["verses"] if v["condition_hints"])
    print(f"Wrote {len(data['verses'])} verses to {OUT} ({flagged} carry conditions).")


if __name__ == "__main__":
    main()
