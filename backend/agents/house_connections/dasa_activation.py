"""Dasa / Bhukti life-area activation chain — 7-step house sequence."""

from __future__ import annotations

from agents.bhavat_bhavam.core import lord_of_house, planets_in_house, whole_sign_house
from agents.house_connections.core import houses_owned_by, nakshatra_lord_for
from agents.house_connections.themes import HOUSE_THEMES

STEP_LABELS = {
    1: {
        "key": "dasa_seat",
        "en": "Dasa planet seated",
        "ta": "தசா கிரகம் அமர்ந்த வீடு",
    },
    2: {
        "key": "dasa_nakshatra",
        "en": "Birth nakshatra of Dasa planet",
        "ta": "தசா கிரகத்தின் ஜன்ம நட்சத்திரம்",
    },
    3: {
        "key": "nak_lord_seat",
        "en": "Nakshatra lord seated",
        "ta": "நட்சத்திர அதிபதி அமர்ந்த வீடு",
    },
    4: {
        "key": "nak_lord_ownership",
        "en": "Nakshatra lord's owned houses",
        "ta": "நட்சத்திர அதிபதியின் ஆட்சி வீடுகள்",
    },
    5: {
        "key": "occupant_spread",
        "en": "Occupants in Dasa lord's houses → their owned houses",
        "ta": "தசா அதிபதி வீடுகளில் உள்ள கிரகங்கள் → அவற்றின் ஆட்சி வீடுகள்",
    },
    6: {
        "key": "dasa_ownership",
        "en": "Dasa lord's owned houses",
        "ta": "தசா அதிபதியின் ஆட்சி வீடுகள்",
    },
    7: {
        "key": "dasa_seat_anchor",
        "en": "Dasa planet seat (final anchor)",
        "ta": "தசா கிரகம் அமர்ந்த வீடு (இறுதி கவனம்)",
    },
}


def _house_themes(houses: list[int]) -> list[dict]:
    out = []
    for h in sorted(set(houses)):
        t = HOUSE_THEMES.get(h, {})
        out.append({
            "house": h,
            "theme_en": t.get("en", f"House {h}"),
            "theme_ta": t.get("ta", ""),
            "impacts_en": t.get("impacts_en", ""),
        })
    return out


def _append_step(
    steps: list[dict],
    activated: set[int],
    step_num: int,
    *,
    houses: list[int],
    detail_en: str,
    detail_ta: str,
    planet: str = "",
    nakshatra: str = "",
    nakshatra_lord: str = "",
) -> None:
    meta = STEP_LABELS[step_num]
    new_houses = [h for h in houses if h not in activated]
    for h in houses:
        activated.add(h)
    steps.append({
        "step": step_num,
        "key": meta["key"],
        "label_en": meta["en"],
        "label_ta": meta["ta"],
        "planet": planet,
        "nakshatra": nakshatra,
        "nakshatra_lord": nakshatra_lord,
        "houses_added": new_houses,
        "houses_all": sorted(set(houses)),
        "house_themes": _house_themes(houses),
        "detail_en": detail_en,
        "detail_ta": detail_ta,
    })


def build_activation_chain(
    dasa_planet: str,
    natal_chart: dict,
    *,
    period: str = "mahadasha",
) -> dict:
    """
    Build ordered 7-step activation chain for one Dasa/Bhukti lord.

    period: 'mahadasha' | 'antardasha'
    """
    asc_idx = (natal_chart.get("ascendant") or {}).get("sign_index", 0)
    pp = natal_chart.get("planet_positions") or {}
    pdata = pp.get(dasa_planet) or {}

    steps: list[dict] = []
    activated: set[int] = set()

    if not pdata.get("sign_index") is None:
        seat = whole_sign_house(pdata["sign_index"], asc_idx)
    else:
        seat = 0

    nak = pdata.get("nakshatra") or ""
    nak_lord = nakshatra_lord_for(pdata) if nak else ""

    # 1 — Dasa planet seat
    if seat:
        _append_step(
            steps, activated, 1,
            houses=[seat],
            planet=dasa_planet,
            detail_en=f"{dasa_planet} is placed in H{seat} ({HOUSE_THEMES[seat]['en']}).",
            detail_ta=f"{dasa_planet} H{seat} இல் ({HOUSE_THEMES[seat]['ta']}).",
        )

    # 2 — Birth nakshatra (link step, no houses)
    _append_step(
        steps, activated, 2,
        houses=[],
        planet=dasa_planet,
        nakshatra=nak,
        nakshatra_lord=nak_lord,
        detail_en=(
            f"{dasa_planet} travels in {nak} at birth; nakshatra lord is {nak_lord}."
            if nak and nak_lord else f"{dasa_planet} nakshatra data unavailable."
        ),
        detail_ta=(
            f"{dasa_planet} ஜன்மத்தில் {nak} நட்சத்திரம்; அதிபதி {nak_lord}."
            if nak and nak_lord else ""
        ),
    )

    # 3 — Nakshatra lord seat
    if nak_lord and nak_lord in pp and pp[nak_lord].get("sign_index") is not None:
        nl_seat = whole_sign_house(pp[nak_lord]["sign_index"], asc_idx)
        _append_step(
            steps, activated, 3,
            houses=[nl_seat],
            planet=nak_lord,
            nakshatra_lord=nak_lord,
            detail_en=f"Nakshatra lord {nak_lord} sits in H{nl_seat}.",
            detail_ta=f"நட்சத்திர அதிபதி {nak_lord} H{nl_seat} இல்.",
        )

    # 4 — Nakshatra lord owned houses
    if nak_lord:
        nl_owned = houses_owned_by(nak_lord, asc_idx)
        if nl_owned:
            _append_step(
                steps, activated, 4,
                houses=nl_owned,
                planet=nak_lord,
                detail_en=f"{nak_lord} rules {', '.join(f'H{h}' for h in nl_owned)}.",
                detail_ta=f"{nak_lord} ஆட்சி: {', '.join(f'H{h}' for h in nl_owned)}.",
            )

    # 5 — Occupants in dasa lord's houses → their owned houses
    dasa_owned = houses_owned_by(dasa_planet, asc_idx)
    spread_houses: list[int] = []
    spread_details_en: list[str] = []
    spread_details_ta: list[str] = []
    for oh in dasa_owned:
        occupants = [p for p in planets_in_house(pp, asc_idx, oh) if p != dasa_planet]
        for occ in occupants:
            occ_owned = houses_owned_by(occ, asc_idx)
            spread_houses.extend(occ_owned)
            spread_details_en.append(
                f"{occ} in H{oh} (owned by {dasa_planet}) rules {', '.join(f'H{h}' for h in occ_owned)}"
            )
            spread_details_ta.append(
                f"{occ} H{oh} இல் → {', '.join(f'H{h}' for h in occ_owned)}"
            )
    if spread_houses:
        _append_step(
            steps, activated, 5,
            houses=spread_houses,
            planet=dasa_planet,
            detail_en="; ".join(spread_details_en),
            detail_ta="; ".join(spread_details_ta),
        )
    else:
        _append_step(
            steps, activated, 5,
            houses=[],
            planet=dasa_planet,
            detail_en=(
                f"No other planets occupy houses ruled by {dasa_planet} "
                f"({', '.join(f'H{h}' for h in dasa_owned) or 'none'})."
            ),
            detail_ta=f"{dasa_planet} ஆட்சி வீடுகளில் பிற கிரகங்கள் இல்லை.",
        )

    # 6 — Dasa lord owned houses
    if dasa_owned:
        _append_step(
            steps, activated, 6,
            houses=dasa_owned,
            planet=dasa_planet,
            detail_en=f"{dasa_planet} rules {', '.join(f'H{h}' for h in dasa_owned)}.",
            detail_ta=f"{dasa_planet} ஆட்சி: {', '.join(f'H{h}' for h in dasa_owned)}.",
        )

    # 7 — Dasa seat anchor
    if seat:
        _append_step(
            steps, activated, 7,
            houses=[seat],
            planet=dasa_planet,
            detail_en=f"Final focus returns to {dasa_planet} in H{seat} — primary life channel.",
            detail_ta=f"இறுதி கவனம் {dasa_planet} H{seat} — முதன்மை வாழ்க்கை துறை.",
        )

    focus = sorted(activated)
    background = [h for h in range(1, 13) if h not in activated]

    period_en = "Mahadasha" if period == "mahadasha" else "Antardasha (Bhukti)"
    period_ta = "மகா தசை" if period == "mahadasha" else "அந்தர் தசை (புக்தி)"

    return {
        "planet": dasa_planet,
        "period": period,
        "period_en": period_en,
        "period_ta": period_ta,
        "seat_house": seat,
        "nakshatra": nak,
        "nakshatra_lord": nak_lord,
        "steps": steps,
        "focus_houses": focus,
        "background_houses": background,
        "focus_themes": _house_themes(focus),
        "background_themes": _house_themes(background),
        "guidance_en": (
            f"During {dasa_planet} {period_en.lower()}, emphasize themes of "
            f"{', '.join(f'H{h}' for h in focus)}. "
            f"De-emphasize {', '.join(f'H{h}' for h in background) or 'none'} — "
            "transits and divisionals still apply."
        ),
        "guidance_ta": (
            f"{dasa_planet} {period_ta} காலத்தில் "
            f"{', '.join(f'H{h}' for h in focus)} துறைகளில் கவனம். "
            f"மற்ற வீடுகள் பின்னணியில்."
        ),
    }


def compute_dasa_life_areas(natal_chart: dict, maha: str, bhukti: str) -> dict:
    """Mahadasha + Antardasha chains and combined focus set."""
    maha_chain = build_activation_chain(maha, natal_chart, period="mahadasha") if maha else {}
    bhukti_chain = build_activation_chain(bhukti, natal_chart, period="antardasha") if bhukti else {}

    combined_focus = sorted(
        set(maha_chain.get("focus_houses") or [])
        | set(bhukti_chain.get("focus_houses") or [])
    )
    combined_bg = [h for h in range(1, 13) if h not in combined_focus]

    return {
        "maha_dasa": maha,
        "bhukti": bhukti,
        "mahadasha": maha_chain,
        "antardasha": bhukti_chain,
        "combined": {
            "focus_houses": combined_focus,
            "background_houses": combined_bg,
            "focus_themes": _house_themes(combined_focus),
            "background_themes": _house_themes(combined_bg),
            "guidance_en": (
                f"Active life areas: {', '.join(f'H{h}' for h in combined_focus)}. "
                f"Background: {', '.join(f'H{h}' for h in combined_bg)}."
            ),
            "guidance_ta": (
                f"செயலில்: {', '.join(f'H{h}' for h in combined_focus)}. "
                f"பின்னணி: {', '.join(f'H{h}' for h in combined_bg)}."
            ),
        },
    }
