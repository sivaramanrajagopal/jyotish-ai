"""Remedies for houses whose fruit is thin, and what each sign exchange means.

Remedy: the Reading verdict comes from the house lord's Navamsa dignity, so the remedy
belongs to that lord. Mantra, deity, weekday and charity come from the Avastha remedy
table, so the app keeps one source. No gemstone is offered: a lord in a weak Navamsa
sign is where the Avastha rules withhold one. Best done in the lord's own dasha or bhukti.

Exchange (Parivartana, Phaladeepika ch. 6): each lord acts as if in its own sign, so the
two houses feed each other. Maha when only good houses take part, Khala when the 3rd
does, Dainya when the 6th, 8th or 12th does.
"""

from __future__ import annotations

from agents.avastha.remedies import REMEDY_MAP
from agents.house_connections.activation import FRUIT, ordinal
from agents.house_connections.edges import PARIVARTANA_KINDS, exchanges, parivartana_kind
from agents.house_connections.themes import DUSTHANA, HOUSE_THEMES
from agents.reading_house import house_fruit

NOTE_EN = "A traditional, optional practice. 108 recitations, ideally in the lord's hora."
NOTE_TA = "பாரம்பரிய, விருப்பமான வழிபாடு. 108 முறை ஜபம், அதிபதியின் ஹோரையில் சிறப்பு."
PERIODS_SHOWN = 2
WEAK_SEAT = {"Inimical": "an enemy's sign", "Debilitated": "its debilitation sign"}


def _theme(h: int, lang: str = "en") -> str:
    text = HOUSE_THEMES[h][lang]
    return text.lower() if lang == "en" else text


def lord_periods(planets: set[str], timeline: list[dict], limit: int = PERIODS_SHOWN) -> list[dict]:
    """The running or next periods ruled by any of these planets, mahadasha first."""
    out: list[dict] = []
    for maha in timeline:
        if maha["state"] == "past":
            continue
        if maha["planet"] in planets:
            out.append({
                "label": f"{maha['planet']} mahadasha",
                "start": maha["start"],
                "end": maha["end"],
                "now": maha["state"] == "now",
            })
        else:
            for b in maha["bhuktis"]:
                if b["state"] != "past" and b["planet"] in planets:
                    out.append({
                        "label": f"{b['planet']} bhukti in {maha['planet']} mahadasha",
                        "start": b["start"],
                        "end": b["end"],
                        "now": b["state"] == "now",
                    })
        if len(out) >= limit:
            break
    return out[:limit]


def house_remedies(chart: dict, timeline: list[dict]) -> dict[int, dict]:
    """House -> remedy for its lord, only where the fruit reads thinner or weak."""
    out: dict[int, dict] = {}
    for h in range(1, 13):
        verdict = house_fruit(chart, h)
        tone, _ = FRUIT.get(verdict["fruit"], ("mixed", ""))
        lord = verdict["lord"]
        data = REMEDY_MAP.get(lord)
        if tone != "hard" or not data:
            continue
        out[h] = {
            "lord": lord,
            "why_en": f"{lord}, the lord, sits in {WEAK_SEAT.get(verdict['dignity'], 'a weak sign')} in the Navamsa.",
            "mantra": data["bija_mantra"],
            "mantra_ta": data["bija_mantra_ta"],
            "count": data["mantra_count"],
            "deity": data["deity"],
            "deity_ta": data["deity_ta"],
            "day": data["fast_day"],
            "day_ta": data["fast_day_ta"],
            "charity": data["charity_items"],
            "charity_ta": data["charity_items_ta"],
            "when": lord_periods({lord}, timeline),
            "note_en": NOTE_EN,
            "note_ta": NOTE_TA,
        }
    return out


def _meaning(kind: str, a: int, b: int) -> tuple[str, str]:
    base_en = (
        f"Each lord acts as if in its own sign, so the {ordinal(a)} ({_theme(a)}) "
        f"and the {ordinal(b)} ({_theme(b)}) feed each other."
    )
    base_ta = f"இரு அதிபதிகளும் சொந்த ராசியில் உள்ளதுபோல் செயல்படுவர்; {a}ஆம், {b}ஆம் வீடுகள் ஒன்றையொன்று வளர்க்கும்."
    if kind == "maha":
        return (
            base_en + " Both houses prosper together; classically a strong yoga.",
            base_ta + " இரு வீடுகளும் சேர்ந்து செழிக்கும்; வலுவான யோகம்.",
        )
    if kind == "khala":
        return (
            base_en + " Results come through effort and courage, and they rise and fall.",
            base_ta + " முயற்சி, தைரியம் வழி பலன்; ஏற்ற இறக்கம் உண்டு.",
        )
    hard = [h for h in (a, b) if h in DUSTHANA]
    if len(hard) == 2:
        return (
            base_en + " Both are hard houses, so the exchange can turn trouble into gain (vipareeta).",
            base_ta + " இரண்டும் துஷ்டான வீடுகள்; சிரமம் லாபமாக மாறலாம் (விபரீத).",
        )
    good = b if a in DUSTHANA else a
    bad = a if a in DUSTHANA else b
    return (
        base_en + f" The {ordinal(good)} is drawn into {_theme(bad)} matters, so its results come with effort or cost.",
        base_ta + f" {good}ஆம் வீடு {_theme(bad, 'ta')} விஷயங்களில் இழுக்கப்படும்; முயற்சி அல்லது செலவுடன் பலன்.",
    )


def exchange_meanings(houses: dict[int, dict], timeline: list[dict]) -> list[dict]:
    out = []
    for a, b in exchanges(houses):
        kind = parivartana_kind(a, b)
        name_en, name_ta = PARIVARTANA_KINDS[kind]
        la, lb = houses[a]["lord"], houses[b]["lord"]
        en, ta = _meaning(kind, a, b)
        out.append({
            "houses": [a, b],
            "lords": [la, lb],
            "kind": kind,
            "name_en": name_en,
            "name_ta": name_ta,
            "meaning_en": en,
            "meaning_ta": ta,
            "active": lord_periods({la, lb}, timeline),
        })
    return out
