"""Career timing from Vimshottari Dasa/Bhukti (dasha_core)."""

from __future__ import annotations

import datetime

from dasha_core import generate_bhuktis, generate_dashas


def build_career_timing(
    moon_longitude: float,
    birth_date: str,
    *,
    tenth_lord: str,
    atmakaraka: str,
    amatyakaraka: str,
    years: int = 90,
) -> list[dict]:
    """MD/AD windows with links to 10th lord, AK, AmK."""
    birth_dt = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
    cutoff = birth_dt + datetime.timedelta(days=years * 365.25)
    keys = {tenth_lord, atmakaraka, amatyakaraka} - {""}
    periods: list[dict] = []

    for dasa in generate_dashas(moon_longitude, birth_date):
        if dasa["start"] >= cutoff:
            break
        maha = dasa["planet"]
        for b in generate_bhuktis(dasa):
            if b["end"] <= birth_dt or b["start"] >= cutoff:
                continue
            bukti = b["planet"]
            if maha not in keys and bukti not in keys:
                continue
            links = []
            if maha == tenth_lord or bukti == tenth_lord:
                links.append("10th lord")
            if maha == atmakaraka or bukti == atmakaraka:
                links.append("AK")
            if maha == amatyakaraka or bukti == amatyakaraka:
                links.append("AmK")
            periods.append({
                "maha_dasa": maha,
                "bukti": bukti,
                "start": b["start"].strftime("%Y-%m-%d"),
                "end": b["end"].strftime("%Y-%m-%d"),
                "links": links,
                "label": f"{maha}–{bukti}",
                "tenth_lord_link": tenth_lord in (maha, bukti),
                "ak_link": atmakaraka in (maha, bukti),
                "amk_link": amatyakaraka in (maha, bukti),
            })
    return periods
