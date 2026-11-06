"""Yoga detection from house lord links.

Raja Yoga: a kendra lord (1, 4, 7, 10) linked with a trikona lord (1, 5, 9) by
conjunction, aspect or sign exchange. The lagna counts as both, so its lord pairs
with the other kendra and trikona lords. Each pair of planets is reported once.
Yogakaraka: one planet ruling a kendra (4, 7, 10) and a trikona (5, 9) itself.
Dharma-Karma Adhipati: the Raja Yoga between the 9th and 10th lords. One planet
rules both only for Taurus lagna (Saturn), which the Yogakaraka branch names.
"""

from __future__ import annotations

from agents.bhavat_bhavam.core import _lords_linked

KENDRA_HOUSES = (1, 4, 7, 10)
TRIKONA_HOUSES = (1, 5, 9)
ROLE_HOUSES = (1, 4, 5, 7, 9, 10)


def _houses_label(houses: list[int]) -> str:
    return ", ".join(f"H{h}" for h in houses)


def _link(
    houses: dict[int, dict],
    a: str,
    b: str,
    a_houses: list[int],
    b_houses: list[int],
    pp: dict,
    asc_idx: int,
) -> tuple[str, str, str] | None:
    """How two lords are joined: (type, English, Tamil), or None.

    An exchange counts only when it swaps the kendra/trikona houses themselves.
    """
    for ha in a_houses:
        for hb in b_houses:
            if ha != hb and houses[ha]["lord_house"] == hb and houses[hb]["lord_house"] == ha:
                return (
                    "exchange",
                    f"{a} and {b} exchange signs (H{ha} and H{hb})",
                    f"{a} & {b} பரிவர்த்தனை (H{ha}, H{hb})",
                )
    seat_a = next((h["lord_house"] for h in houses.values() if h["lord"] == a), 0)
    links = _lords_linked(a, b, pp, asc_idx)
    if "conjunction" in links:
        return "conjunction", f"{a} and {b} sit together in H{seat_a}", f"{a} & {b} H{seat_a} இல் இணைவு"
    a_aspects = f"{a} aspects {b}" in links
    b_aspects = f"{b} aspects {a}" in links
    if a_aspects and b_aspects:
        return "mutual_aspect", f"{a} and {b} aspect each other", f"{a} & {b} பரஸ்பர பார்வை"
    if a_aspects or b_aspects:
        giver, taker = (a, b) if a_aspects else (b, a)
        return "aspect", f"{giver} aspects {taker}", f"{giver} → {taker} பார்வை"
    return None


def _strength(houses: dict[int, dict], nums: list[int], penalty: float = 0) -> float:
    return round(sum(houses[h]["strength"] for h in nums) / len(nums) - penalty, 1)


def detect_yogas(houses: dict[int, dict], natal_chart: dict) -> list[dict]:
    pp = natal_chart.get("planet_positions") or {}
    asc_idx = (natal_chart.get("ascendant") or {}).get("sign_index", 0)
    yogas: list[dict] = []

    roles: dict[str, list[int]] = {}
    for h in ROLE_HOUSES:
        roles.setdefault(houses[h]["lord"], []).append(h)

    for planet, owned in roles.items():
        kendras = [h for h in owned if h in (4, 7, 10)]
        trikonas = [h for h in owned if h in (5, 9)]
        if not (kendras and trikonas):
            continue
        nums = sorted(kendras + trikonas)
        dharma_karma = 9 in nums and 10 in nums
        seat = houses[nums[0]]["lord_house"]
        yogas.append({
            "name": "Yogakaraka (Dharma-Karma Adhipati)" if dharma_karma else "Yogakaraka",
            "name_ta": "யோககாரகன் (தர்ம-கர்மாதிபதி)" if dharma_karma else "யோககாரகன்",
            "type": "same_lord",
            "houses": nums,
            "lords": [planet],
            "formation_house": seat,
            "strength": _strength(houses, nums),
            "detail_en": f"{planet} rules kendra {_houses_label(kendras)} and trikona {_houses_label(trikonas)}, seated in H{seat}",
            "detail_ta": f"{planet} கேந்திர {_houses_label(kendras)} & திரிகோண {_houses_label(trikonas)} அதிபதி, H{seat} இல்",
        })

    seen: set[frozenset[str]] = set()
    for k in KENDRA_HOUSES:
        for t in TRIKONA_HOUSES:
            kl, tl = houses[k]["lord"], houses[t]["lord"]
            pair = frozenset((kl, tl))
            if k == t or kl == tl or pair in seen:
                continue
            seen.add(pair)
            k_roles, t_roles = roles.get(kl, []), roles.get(tl, [])
            link = _link(houses, kl, tl, k_roles, t_roles, pp, asc_idx)
            if not link:
                continue
            kind, how_en, how_ta = link
            nums = sorted(set(k_roles + t_roles))
            dharma_karma = (houses[9]["lord"] in pair and houses[10]["lord"] in pair)
            yoga = {
                "name": "Dharma-Karma Adhipati Yoga" if dharma_karma else "Raja Yoga",
                "name_ta": "தர்ம-கர்மாதிபதி யோகம்" if dharma_karma else "ராஜ யோகம்",
                "type": kind,
                "houses": nums,
                "lords": [kl, tl],
                "strength": _strength(houses, nums, 5 if kind == "aspect" else 0),
                "detail_en": f"{kl} ({_houses_label(k_roles)} lord) and {tl} ({_houses_label(t_roles)} lord): {how_en}",
                "detail_ta": f"{kl} ({_houses_label(k_roles)}) & {tl} ({_houses_label(t_roles)}): {how_ta}",
            }
            if kind == "conjunction":
                yoga["formation_house"] = houses[k]["lord_house"]
            yogas.append(yoga)

    return yogas
