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


def run_chart_tool(name: str, chart: dict, location: str = "Chennai") -> dict:
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


def tool_result_json(name: str, chart: dict, location: str = "Chennai") -> str:
    try:
        payload = run_chart_tool(name, chart, location)
    except Exception as exc:
        payload = {"error": str(exc)}
    return json.dumps(payload, default=str)[:6000]
