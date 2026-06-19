"""Build house-to-house connection edges for the prediction graph."""

from __future__ import annotations

from agents.bhavat_bhavam.core import lord_of_house, whole_sign_house, _lords_linked
from agents.house_connections.core import houses_owned_by, nakshatra_lord_for
from agents.house_connections.themes import DUSTHANA
from agents.natal_agent import SIGN_LORDS
from agents.transit_score_agent import _planet_aspects


def _edge_id(kind: str, from_h: int, to_h: int, detail: str = "") -> str:
    return f"{kind}:{from_h}:{to_h}:{detail}"


def build_edges(houses: dict[int, dict], natal_chart: dict) -> list[dict]:
    asc_idx = (natal_chart.get("ascendant") or {}).get("sign_index", 0)
    pp = natal_chart.get("planet_positions") or {}
    edges: list[dict] = []
    seen: set[str] = set()

    def add(edge: dict) -> None:
        eid = edge.get("id") or _edge_id(edge["kind"], edge["from_house"], edge["to_house"], edge.get("detail", ""))
        if eid in seen:
            return
        seen.add(eid)
        edge["id"] = eid
        edges.append(edge)

    # 1. Lord placement: H_a lord in H_b
    for h, ha in houses.items():
        lh = ha["lord_house"]
        if lh and lh != h:
            add({
                "kind": "lord_placement",
                "from_house": h,
                "to_house": lh,
                "label_en": f"{ha['lord']} (H{h} lord) placed in H{lh}",
                "label_ta": f"{ha['lord']} (H{h} அதிபதி) H{lh} இல்",
                "planets": [ha["lord"]],
                "weight": 3 if lh in (4, 5, 7, 9, 10) else 2,
                "supportive": ha["position_type"] not in ("dusthana_from_own",),
            })

    # 2. Lord-to-lord links (conjunction, aspect)
    for h1 in range(1, 13):
        for h2 in range(h1 + 1, 13):
            l1 = houses[h1]["lord"]
            l2 = houses[h2]["lord"]
            if l1 == l2:
                add({
                    "kind": "same_lord",
                    "from_house": h1,
                    "to_house": h2,
                    "label_en": f"H{h1} & H{h2} share lord {l1}",
                    "label_ta": f"H{h1} & H{h2} ஒரே அதிபதி {l1}",
                    "planets": [l1],
                    "weight": 4,
                    "supportive": True,
                })
                continue
            links = _lords_linked(l1, l2, pp, asc_idx)
            if not links:
                continue
            mutual = (
                f"{l1} aspects {l2}" in links and f"{l2} aspects {l1}" in links
            ) or "conjunction" in links
            add({
                "kind": "mutual_aspect" if mutual else "lord_link",
                "from_house": h1,
                "to_house": h2,
                "label_en": f"H{h1} lord {l1} ↔ H{h2} lord {l2}: {', '.join(links)}",
                "label_ta": f"H{h1} {l1} ↔ H{h2} {l2}: {', '.join(links)}",
                "planets": [l1, l2],
                "detail": ",".join(links),
                "weight": 5 if mutual else 3,
                "supportive": True,
            })

    # 3. Planet in house → pada lord owns / sits
    for h, ha in houses.items():
        for planet in ha["planets_in_house"]:
            pdata = pp.get(planet) or {}
            pada_lord = nakshatra_lord_for(pdata)
            if not pada_lord or pada_lord not in pp:
                continue
            pl_house = whole_sign_house(pp[pada_lord]["sign_index"], asc_idx)
            for owned in houses_owned_by(pada_lord, asc_idx):
                add({
                    "kind": "pada_lord",
                    "from_house": owned,
                    "to_house": h,
                    "label_en": f"H{h} occupant {planet} pada lord {pada_lord} (owns H{owned})",
                    "label_ta": f"H{h} {planet} pada அதிபதி {pada_lord} (H{owned})",
                    "planets": [planet, pada_lord],
                    "weight": 2,
                    "supportive": pada_lord not in ("Saturn", "Mars", "Rahu", "Ketu") or owned in DUSTHANA,
                })
            if pl_house != h:
                add({
                    "kind": "pada_lord_placement",
                    "from_house": pl_house,
                    "to_house": h,
                    "label_en": f"H{h} via {planet} pada lord {pada_lord} in H{pl_house}",
                    "label_ta": f"H{h} ← {pada_lord} pada வழி H{pl_house}",
                    "planets": [pada_lord],
                    "weight": 2,
                    "supportive": True,
                })

    # 4. Sign lord (dispositor) of house lord
    for h, ha in houses.items():
        sign = ha["sign"]
        dispositor = SIGN_LORDS.get(sign, "")
        if not dispositor or dispositor not in pp:
            continue
        disp_house = whole_sign_house(pp[dispositor]["sign_index"], asc_idx)
        for owned in houses_owned_by(dispositor, asc_idx):
            if owned != h:
                add({
                    "kind": "sign_lord",
                    "from_house": owned,
                    "to_house": h,
                    "label_en": f"H{h} sign lord {dispositor} owns H{owned}",
                    "label_ta": f"H{h} ராசி அதிபதி {dispositor} → H{owned}",
                    "planets": [dispositor],
                    "weight": 2,
                    "supportive": True,
                })

    # 5. Dusthana lord cross-links
    for h in DUSTHANA:
        lh = houses[h]["lord_house"]
        if lh in DUSTHANA and lh != h:
            add({
                "kind": "dusthana_chain",
                "from_house": h,
                "to_house": lh,
                "label_en": f"Dusthana chain H{h} lord in H{lh}",
                "label_ta": f"துஷ்டான சங்கிலி H{h}→H{lh}",
                "planets": [houses[h]["lord"]],
                "weight": 2,
                "supportive": False,
            })

    # 6. Aspecting a house (planet drishti on house)
    for h, ha in houses.items():
        for planet in ha["planets_aspecting"]:
            ph = whole_sign_house(pp[planet]["sign_index"], asc_idx)
            add({
                "kind": "aspect_on_house",
                "from_house": ph,
                "to_house": h,
                "label_en": f"{planet} aspects H{h} from H{ph}",
                "label_ta": f"{planet} H{ph} இலிருந்து H{h} பார்வை",
                "planets": [planet],
                "weight": 2,
                "supportive": planet in ("Jupiter", "Venus", "Mercury", "Moon"),
            })

    return edges
