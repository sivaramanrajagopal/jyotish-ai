"""Tools the chat model may call. Each one returns numbers from this app."""

from __future__ import annotations

import json

from agents.avastha_agent import compute_avastha_analysis
from agents.period_reading import compute_period_reading
from agents.shadbala_agent import compute_shadbala_for_chart
from agents.sky_today_agent import build_sky_today

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "period_reading",
            "description": (
                "Current mahadasha and bhukti. Call when the question is about "
                "the period now running, dasha, or bhukti results."
            ),
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shadbala",
            "description": (
                "Natal Shadbala ranks. Call when the question is about planet "
                "strength, who is strongest, or who is short of the minimum."
            ),
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "avastha",
            "description": (
                "Natal condition of the planets and of the current period pair. "
                "Call when the question is about avastha, awake or asleep planets, "
                "or whether the period lords can deliver."
            ),
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sky_today",
            "description": (
                "Today's sky for this native: weekday, tithi, nakshatra, Moon sign, "
                "Tara, Chandra Ashtama, and Rahu Kalam. Call for questions about today."
            ),
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
]


CLASSICAL_TOOL = {
    "type": "function",
    "function": {
        "name": "classical_rules",
        "description": (
            "BPHS chapter 24 rules matched to this chart: where each house lord sits and "
            "what the text says. Call when the question asks what the classics or BPHS say, "
            "or about the results of a house. Optionally narrow to one house or topic."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "house": {"type": "integer", "minimum": 1, "maximum": 12},
                "topic": {
                    "type": "string",
                    "enum": [
                        "career", "wealth", "income", "marriage", "children", "health",
                        "foreign", "home", "father", "mother", "siblings", "education",
                    ],
                },
            },
            "additionalProperties": False,
        },
    },
}

CLASSICAL_GUIDE = (
    "When the question asks what the classical texts say, or about the results of a house, "
    "call classical_rules. Put each rule's cite (for example BPHS 24.7) beside what it says, "
    "and use only the rules the tool returns. These rules back up the house judgment and "
    "sit under it. Where a rule says to leave something out of a client reading, follow that.\n"
)


def active_tools() -> list[dict]:
    from agents.classical import classical_enabled

    return [*TOOLS, CLASSICAL_TOOL] if classical_enabled() else TOOLS


def _classical_rules(chart: dict, house: int | None = None, topic: str | None = None) -> dict:
    from agents.classical import classical_for_chart

    result = classical_for_chart(chart)
    rows = result["matches"]
    if house:
        rows = [m for m in rows if house in (m["lord_of"], m["in_house"])]
    if topic:
        rows = [m for m in rows if topic in m["topics"]]
    return {
        "source": "BPHS chapter 24, house lords placed in houses",
        "rules": [
            {
                "cite": m["source"]["cite"],
                "lord": m["lord"],
                "lord_of": m["lord_of"],
                "in_house": m["in_house"],
                "tone": m["tone"],
                "effect": m["strength_label"],
                "summary": m["summary"],
                "why": m["why"],
            }
            for m in rows
        ],
        "dual_lordship": [
            n["note"] for n in result["dual_lordship"]
            if not house or house in n["houses"]
        ],
    }


def run_chart_tool(name: str, chart: dict, location: str = "Chennai", args: dict | None = None) -> dict:
    if name == "classical_rules":
        from agents.classical import classical_enabled

        if not classical_enabled():
            return {"error": "Classical rules are switched off."}
        args = args or {}
        try:
            house = int(args.get("house") or 0)
        except (TypeError, ValueError):
            house = 0
        topic = args.get("topic") if isinstance(args.get("topic"), str) else None
        return _classical_rules(chart, house if 1 <= house <= 12 else None, topic)
    if name == "period_reading":
        reading = compute_period_reading(chart)
        return {
            "period": reading.get("period_label"),
            "lead": reading.get("lead"),
            "lords": reading.get("lords"),
            "note": reading.get("note"),
        }
    if name == "shadbala":
        data = compute_shadbala_for_chart(chart)
        planets = sorted(data.get("planets") or [], key=lambda row: row["rank"])
        return {
            "planets": [
                {
                    "planet": row["planet"],
                    "rank": row["rank"],
                    "held": row["rupas"],
                    "needed": row["minimum"],
                    "ratio": row["ratio"],
                    "meets_minimum": row["meets_minimum"],
                }
                for row in planets
            ],
        }
    if name == "avastha":
        analysis = compute_avastha_analysis(chart)
        synergy = analysis.get("dasa_bhukti") or {}
        by_name = {row["planet"]: row for row in analysis.get("planets") or []}
        lords = []
        for planet in (synergy.get("dasaLord"), synergy.get("bhuktiLord")):
            row = by_name.get(planet) or {}
            lords.append({
                "planet": planet,
                "net": (row.get("manifestation") or {}).get("net"),
                "state": (row.get("sthula") or {}).get("name"),
                "mood": (row.get("sukshma") or {}).get("name"),
            })
        return {
            "period_class": synergy.get("manifestationClass"),
            "combined": synergy.get("combinedScore"),
            "outcomes": synergy.get("objectiveOutcome"),
            "lords": lords,
        }
    if name == "sky_today":
        moon_nak = chart.get("moon_nakshatra_index")
        moon_rasi = chart.get("moon_rasi_index")
        asc = (chart.get("ascendant") or {}).get("sign_index")
        sky = build_sky_today(
            location or "Chennai",
            moon_nak_index=moon_nak,
            moon_rasi_index=moon_rasi,
            natal_asc_sign_index=asc,
        )
        personal = sky.get("personal") or {}
        rahu = sky.get("rahu_kalam") or {}
        return {
            "date": sky.get("date_label"),
            "location": sky.get("location"),
            "vaaram": sky.get("vaaram"),
            "tithi": sky.get("tithi"),
            "nakshatra": sky.get("nakshatra"),
            "moon_sign": sky.get("moon_sign"),
            "sun_sign": sky.get("sun_sign"),
            "retrograde": sky.get("retrograde"),
            "tara": personal.get("tara_name"),
            "tara_nature": personal.get("tara_nature"),
            "moon_house_from_lagna": personal.get("moon_house"),
            "chandra_ashtama": personal.get("ashtama_active"),
            "rahu_kalam_active": rahu.get("active"),
            "alert": (sky.get("alert") or {}).get("message"),
        }
    return {"error": f"Unknown tool {name}"}


def tool_result_json(name: str, chart: dict, location: str = "Chennai", arguments: str = "") -> str:
    try:
        args = json.loads(arguments) if arguments else {}
    except ValueError:
        args = {}
    try:
        payload = run_chart_tool(name, chart, location, args if isinstance(args, dict) else {})
    except Exception as exc:
        payload = {"error": str(exc)}
    # All twelve classical rules with their reasons can run past the usual cap.
    limit = 14000 if name == "classical_rules" else 6000
    return json.dumps(payload, default=str)[:limit]
