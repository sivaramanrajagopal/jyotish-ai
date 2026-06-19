"""Yoga detection from house lord links."""

from __future__ import annotations

from agents.bhavat_bhavam.core import _lords_linked


def detect_yogas(houses: dict[int, dict], natal_chart: dict) -> list[dict]:
    pp = natal_chart.get("planet_positions") or {}
    asc_idx = (natal_chart.get("ascendant") or {}).get("sign_index", 0)
    yogas: list[dict] = []

    kendra = [1, 4, 7, 10]
    trikona = [1, 5, 9]

    for k in kendra:
        for t in trikona:
            if k == t:
                continue
            kl = houses[k]["lord"]
            tl = houses[t]["lord"]
            kh = houses[k]["lord_house"]
            th = houses[t]["lord_house"]
            if kh == th:
                yogas.append({
                    "name": "Raja Yoga",
                    "name_ta": "ராஜ யோகம்",
                    "type": "conjunction",
                    "houses": [k, t],
                    "lords": [kl, tl],
                    "formation_house": kh,
                    "strength": round((houses[k]["strength"] + houses[t]["strength"]) / 2, 1),
                    "detail_en": f"{kl} (H{k} lord) and {tl} (H{t} lord) unite in H{kh}",
                    "detail_ta": f"{kl} (H{k}) & {tl} (H{t}) H{kh} இல் இணைவு",
                })
            links = _lords_linked(kl, tl, pp, asc_idx)
            if f"{kl} aspects {tl}" in links or f"{tl} aspects {kl}" in links:
                mutual = f"{kl} aspects {tl}" in links and f"{tl} aspects {kl}" in links
                yogas.append({
                    "name": "Raja Yoga",
                    "name_ta": "ராஜ யோகம்",
                    "type": "mutual_aspect" if mutual else "aspect",
                    "houses": [k, t],
                    "lords": [kl, tl],
                    "strength": round((houses[k]["strength"] + houses[t]["strength"]) / 2 - (0 if mutual else 5), 1),
                    "detail_en": f"Kendra H{k} lord {kl} linked to Trikona H{t} lord {tl}: {', '.join(links)}",
                    "detail_ta": f"Kendra-Trikona {kl}-{tl}: {', '.join(links)}",
                })

    if 9 in houses and 10 in houses:
        l9 = houses[9]["lord"]
        l10 = houses[10]["lord"]
        h9 = houses[9]["lord_house"]
        h10 = houses[10]["lord_house"]
        if l9 == l10 or h9 == h10:
            yogas.append({
                "name": "Dharma-Karma Adhipati Yoga",
                "name_ta": "தர்ம-கர்மாதிபதி யோகம்",
                "type": "conjunction" if h9 == h10 else "same_lord",
                "houses": [9, 10],
                "lords": [l9, l10],
                "formation_house": h9 if h9 == h10 else h10,
                "strength": round((houses[9]["strength"] + houses[10]["strength"]) / 2, 1),
                "detail_en": f"Fortune lord {l9} and career lord {l10} connected — ethical prosperity channel",
                "detail_ta": f"பாக்கிய அதிபதி {l9} & தொழில் {l10} இணைப்பு",
            })

    return yogas
