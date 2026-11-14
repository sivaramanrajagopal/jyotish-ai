"""Tools the chat model may call. Each one returns numbers from this app."""

from __future__ import annotations

import json
from datetime import datetime

from agents.avastha_agent import compute_avastha_analysis
from agents.period_reading import compute_period_reading
from agents.shadbala_agent import compute_shadbala_for_chart
from agents.sky_today_agent import build_sky_today

CITES = {
    "period_reading": {"tab": "chart", "label": "My Chart"},
    "shadbala": {"tab": "chart", "label": "My Chart"},
    "avastha": {"tab": "avastha", "label": "Avastha"},
    "sky_today": {"tab": "panchangam", "label": "Panchangam"},
    "classical_rules": {"tab": "reading", "label": "Reading"},
    "nadi": {"tab": "nadi", "label": "Nadi"},
    "reading": {"tab": "reading", "label": "Reading"},
    "career": {"tab": "career", "label": "Career"},
    "d6": {"tab": "d6", "label": "Ripu"},
    "health": {"tab": "health", "label": "Health"},
    "dosha_radar": {"tab": "dosha-radar", "label": "Dosha Radar"},
    "house_links": {"tab": "house-links", "label": "House Links"},
    "gochar": {"tab": "gochar", "label": "Gochar"},
    "life_cycle": {"tab": "life-cycle", "label": "Life Cycle"},
    "tamil_doshas": {"tab": "chart", "label": "My Chart"},
    "indu_lagna": {"tab": "chart", "label": "My Chart"},
    "ashtakavarga": {"tab": "chart", "label": "My Chart"},
    "bhavat_bhavam": {"tab": "health", "label": "Health"},
    "prashna": {"tab": "prashna", "label": "Prashna"},
    "forecast_facts": {"tab": "forecast", "label": "Forecast"},
    "mitra_muhurta": {"tab": "panchangam", "label": "Panchangam"},
}

def _tool(name: str, description: str, properties: dict | None = None) -> dict:
    params = {"type": "object", "additionalProperties": False, "properties": properties or {}}
    return {"type": "function", "function": {"name": name, "description": description, "parameters": params}}


TOOLS = [
    _tool(
        "period_reading",
        "Current mahadasha and bhukti. Call when the question is about the period now running, dasha, or bhukti results.",
    ),
    _tool(
        "shadbala",
        "Natal Shadbala ranks. Call when the question is about planet strength, who is strongest, or who is short of the minimum.",
    ),
    _tool(
        "avastha",
        "Natal condition of the planets and of the current period pair. Call for avastha, awake or asleep planets, or whether the period lords can deliver.",
    ),
    _tool(
        "sky_today",
        "Today's sky for this native: weekday, tithi, nakshatra, Moon sign, Tara, Chandra Ashtama, and Rahu Kalam.",
    ),
    _tool(
        "nadi",
        "Bhrigu Nandi Nadi chain for a life question. Call for work, marriage, money, foreign, children, or other Nadi questions. Pass question as work, marriage, money, self, skill, home, children, health, breaks, father, gains, or foreign.",
        {
            "question": {
                "type": "string",
                "description": "Nadi question id such as work or marriage. Omit to list all questions.",
            },
        },
    ),
    _tool(
        "reading",
        "One sitting: who, voice, current chapter, open seasons, and next. Call for a full reading or what is open now.",
    ),
    _tool(
        "career",
        "Career from D1 and D10. Call for profession, 10th house, or work direction.",
    ),
    _tool(
        "d6",
        "Ripu from D1 and D6 Shashthamsa (Narasimha Rao / JHora: odd from Aries, even from Libra). Call for debt, enemies, litigation, competitive exams, service jobs, or illness as an obstacle. Not D60. Not medical, legal, or exam advice. Body map is health; profession type is career.",
    ),
    _tool(
        "health",
        "Health awareness from Drekkana. Call for body, illness, or health timing. This is not medical advice.",
    ),
    _tool(
        "dosha_radar",
        "Natal obstruction blueprint and live transit alerts. Call for Mudakku, Soonya, Vadhai, Pushkara, or Chandrashtama.",
    ),
    _tool(
        "house_links",
        "House Links: which houses are live, main, or shared, and channels in or out. Call to explain a house or lord links.",
        {"question": {"type": "string", "description": "The user's question, used to pick the house."}},
    ),
    _tool(
        "gochar",
        "Transits from the natal Moon and from the lagna. Call for gochara or transits. Never quote a 0-100 score.",
    ),
    _tool(
        "life_cycle",
        "Dated windows for the next ten years. Call for timing of career, marriage, health, or what is coming. Quote dates verbatim.",
    ),
    _tool(
        "tamil_doshas",
        "Natal Tamil doshas: dagdha, Mudakku, Vadhai, Vainasikam, Yogi. Call for parihara or Tamil dosha questions.",
    ),
    _tool(
        "indu_lagna",
        "Indu Lagna fortune sign and periods. Call for wealth, fortune, or Indu.",
    ),
    _tool(
        "ashtakavarga",
        "Ashtakavarga bindus used by this app. Call for SAV, BAV, or bindu strength.",
    ),
    _tool(
        "bhavat_bhavam",
        "Bhavat Bhavam house-from-house links for career and health. Call when the question is about derived houses.",
    ),
    _tool(
        "forecast_facts",
        "Today's forecast facts from this app (dasha, panchangam, identity). Call for a daily forecast. Do not invent a score.",
    ),
    _tool(
        "prashna",
        "Cast a Prashna chart for a question asked now. Requires question text. Category is career, marriage, money, property, health, travel, education, or general.",
        {
            "question": {"type": "string", "description": "The horary question."},
            "category": {
                "type": "string",
                "description": "career, marriage, money, property, health, travel, education, or general.",
            },
        },
    ),
    _tool(
        "mitra_muhurta",
        "Mitra muhurta windows for paying a loan or debt: Ashwini with Mesha lagna, and Anusham (Anuradha) with Vrischika lagna. Uses a panchangam city, not the birth chart. Call for loan repayment timing, Mitra, Mythra, or those two pairs.",
        {
            "location": {
                "type": "string",
                "description": "Panchangam city such as Chennai. Omit to use the current sky location.",
            },
            "month": {
                "type": "string",
                "description": "Calendar month YYYY-MM. Omit for the current month at that city.",
            },
        },
    ),
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

ENGINE_GUIDE = (
    "Call the matching engine tool for Nadi, the sitting, career, Ripu (D6), health, Dosha Radar, House Links, "
    "Gochara, Life Cycle, Tamil doshas, Indu, Ashtakavarga, Bhavat Bhavam, forecast facts, Prashna, "
    "or Mitra muhurta (loan-repayment windows). "
    "Answer from the tool JSON. Do not invent dates, seasons, or 0-100 scores. "
    "If the native is already married, do not lead with marriage unless they asked. "
    "Prashna needs the question text; it is a chart of the moment, not the birth chart. "
    "Mitra muhurta uses the panchangam city, not the birth chart. Quote the returned windows.\n"
)


def active_tools() -> list[dict]:
    from agents.classical import classical_enabled

    return [*TOOLS, CLASSICAL_TOOL] if classical_enabled() else TOOLS


def cite_for(name: str) -> dict | None:
    row = CITES.get(name)
    return dict(row) if row else None


def _strip_disclaimer(text: str) -> str:
    return "\n".join(
        line for line in (text or "").split("\n") if not line.lstrip().startswith("DISCLAIMER")
    )


def _with_cite(name: str, payload: dict) -> dict:
    cite = cite_for(name)
    if cite:
        payload = {**payload, "cite": cite}
    return payload


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


def _period(chart: dict, location: str, args: dict) -> dict:
    reading = compute_period_reading(chart)
    return {
        "period": reading.get("period_label"),
        "lead": reading.get("lead"),
        "lords": reading.get("lords"),
        "note": reading.get("note"),
    }


def _shadbala(chart: dict, location: str, args: dict) -> dict:
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


def _avastha(chart: dict, location: str, args: dict) -> dict:
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


def _sky(chart: dict, location: str, args: dict) -> dict:
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


def _nadi(chart: dict, location: str, args: dict) -> dict:
    from agents.nadi_agent import compute_nadi

    payload = compute_nadi(chart)
    wanted = str(args.get("question") or "").strip().lower()
    rows = payload.get("readings") or []
    if wanted:
        picked = [row for row in rows if row["id"] == wanted or row["id"].startswith(wanted)]
        rows = picked or rows

    def _row(row: dict) -> dict:
        timing = row.get("timing") or []
        return {
            "id": row["id"],
            "label": row["label"],
            "karaka": row.get("karaka"),
            "happening": (row.get("now") or {}).get("sign"),
            "analysis": row.get("analysis"),
            "season_status": row.get("season_status"),
            "timing": [
                {"planet": bit.get("planet"), "kind": bit.get("kind"), "when": bit.get("when")}
                for bit in timing[:4]
            ],
        }

    if wanted:
        return {"gender": payload.get("gender"), "questions": [_row(row) for row in rows]}
    return {
        "gender": payload.get("gender"),
        "questions": [
            {
                "id": row["id"],
                "label": row["label"],
                "karaka": row.get("karaka"),
                "happening": (row.get("now") or {}).get("sign"),
                "season_status": row.get("season_status"),
            }
            for row in rows
        ],
        "note": "Call nadi again with question set to one id for the chain and seasons.",
    }


def _reading(chart: dict, location: str, args: dict) -> dict:
    from agents.reading_agent import compute_reading

    data = compute_reading(chart)
    life = data.get("life") or []
    return {
        "who": (data.get("who") or {}).get("sentence"),
        "voice": (data.get("voice") or {}).get("sentence"),
        "timeline": data.get("timeline"),
        "next": (data.get("next") or {}).get("sentence"),
        "life": [
            {
                "id": row.get("id"),
                "label": row.get("label"),
                "open": row.get("open"),
                "when": row.get("when"),
                "significator": row.get("significator"),
            }
            for row in life
        ],
    }


def _career(chart: dict, location: str, args: dict) -> dict:
    from agents.career_agent import career_context_for_narrator
    return {"text": _strip_disclaimer(career_context_for_narrator(chart))}


def _d6(chart: dict, location: str, args: dict) -> dict:
    from agents.d6_agent import d6_context_for_narrator
    return {"text": _strip_disclaimer(d6_context_for_narrator(chart))}


def _health(chart: dict, location: str, args: dict) -> dict:
    from agents.health_agent import health_context_for_narrator
    return {"text": _strip_disclaimer(health_context_for_narrator(chart))}


def _dosha_radar(chart: dict, location: str, args: dict) -> dict:
    from agents.dosha_radar_agent import dosha_radar_context_for_narrator
    return {"text": _strip_disclaimer(dosha_radar_context_for_narrator(chart))}


def _house_links(chart: dict, location: str, args: dict) -> dict:
    from agents.house_connections.narrator import house_connections_context_for_narrator
    question = str(args.get("question") or "")
    return {"text": _strip_disclaimer(house_connections_context_for_narrator(chart, question))}


def _gochar(chart: dict, location: str, args: dict) -> dict:
    from agents.transit_score_agent import compact_gochara_summary, score_all_houses
    scores = score_all_houses(chart)
    return {"text": compact_gochara_summary(scores, chart.get("dasha") or {})}


def _life_cycle(chart: dict, location: str, args: dict) -> dict:
    from agents.life_cycle import life_cycle_context_for_narrator
    return {"text": _strip_disclaimer(life_cycle_context_for_narrator(chart))}


def _tamil_doshas(chart: dict, location: str, args: dict) -> dict:
    from agents.tamil_dosha_agent import dosha_context_for_narrator
    return {"text": _strip_disclaimer(dosha_context_for_narrator(chart))}


def _indu(chart: dict, location: str, args: dict) -> dict:
    from agents.indu_lagna_agent import indu_context_for_narrator
    return {"text": _strip_disclaimer(indu_context_for_narrator(chart))}


def _ashtakavarga(chart: dict, location: str, args: dict) -> dict:
    from agents.ashtakavarga_agent import bav_context_for_narrator
    return {"text": _strip_disclaimer(bav_context_for_narrator(chart))}


def _bhavat_bhavam(chart: dict, location: str, args: dict) -> dict:
    from agents.bhavat_bhavam_agent import bhavat_bhavam_context_for_narrator
    return {"text": _strip_disclaimer(bhavat_bhavam_context_for_narrator(chart))}


def _forecast_facts(chart: dict, location: str, args: dict) -> dict:
    from agents.orchestrator import assemble_context

    ctx = assemble_context(chart, location=location or "Chennai")
    dasha = ctx.get("dasha") or {}
    maha = dasha.get("mahadasha") or {}
    bhukti = dasha.get("bhukti") or {}
    native = ctx.get("native") or {}
    panch = ctx.get("panchangam") or {}
    personal = ctx.get("personal_panchangam") or {}
    return {
        "date": ctx.get("date"),
        "location": ctx.get("location"),
        "lagna": native.get("ascendant_sign"),
        "moon": native.get("moon_sign"),
        "mahadasha": maha.get("planet") or maha.get("name"),
        "bhukti": bhukti.get("planet") or bhukti.get("name"),
        "vaaram": panch.get("vaaram"),
        "tithi": panch.get("tithi"),
        "nakshatra": panch.get("nakshatra"),
        "tara": personal.get("tara_name") or personal.get("tara"),
        "note": "Speak from these facts. Do not invent a score or a second forecast voice.",
    }


def _mitra_muhurta(chart: dict, location: str, args: dict) -> dict:
    from agents.mitra_muhurta import compute_mitra_muhurta
    from agents.panchangam_agent import LOCATIONS

    place = str(args.get("location") or location or "Chennai").strip()
    match = next((name for name in LOCATIONS if name.lower() == place.lower()), None)
    if not match:
        return {"error": "Unknown location.", "locations": list(LOCATIONS)}
    month = str(args.get("month") or "").strip() or None
    if month and (len(month) != 7 or month[4] != "-"):
        return {"error": "month must be YYYY-MM, for example 2026-11."}
    try:
        data = compute_mitra_muhurta(match, month)
    except ValueError as exc:
        return {"error": str(exc)}
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo(data["timezone"]))

    def _row(row: dict) -> dict:
        return {
            "date": row["date"],
            "start": row["start"],
            "end": row["end"],
            "label": row["label"],
        }

    windows = [_row(row) for row in data.get("windows") or []]
    nxt = None
    for row in data.get("windows") or []:
        if datetime.fromisoformat(row["end"]) > now:
            nxt = _row(row)
            break
    return {
        "location": data["location"],
        "timezone": data["timezone"],
        "month": data["month"],
        "purpose": data["purpose"],
        "pairs": data["pairs"],
        "next": nxt,
        "windows": windows,
        "count": data["count"],
        "note": "Quote these times verbatim. Traditional timing for paying a loan, not a promise.",
    }


def _prashna(chart: dict, location: str, args: dict) -> dict:
    from agents.prashna.analyzer import analyze_prashna
    from agents.prashna.constants import CATEGORY_HOUSE

    question = str(args.get("question") or "").strip()
    category = str(args.get("category") or "general").strip().lower()
    if not question:
        return {
            "error": "Prashna needs the question text.",
            "categories": sorted(CATEGORY_HOUSE),
        }
    if category not in CATEGORY_HOUSE:
        category = "general"
    birth = chart.get("birth_data") or {}
    result = analyze_prashna(
        question=question[:500],
        category=category,
        timestamp_iso=datetime.now().isoformat(),
        timezone=str(birth.get("timezone") or "Asia/Kolkata"),
        lat=birth.get("lat"),
        lon=birth.get("lon"),
        place=location or birth.get("place_of_birth"),
    )
    verdict = result.get("verdict") or {}
    interp = result.get("interpretation") or {}
    if isinstance(interp, dict):
        spoken = interp.get("en") or interp.get("summary") or interp.get("verdict_line") or ""
    else:
        spoken = str(interp)
    return {
        "category": category,
        "question": question,
        "verdict": {
            "label": verdict.get("label") or verdict.get("outcome") or verdict.get("lean"),
            "detail": verdict.get("summary") or verdict.get("en") or verdict.get("reason"),
        },
        "interpretation": spoken,
        "note": "This is a chart of the moment. Send the person to the Prashna tab for the full board.",
    }


HANDLERS = {
    "period_reading": _period,
    "shadbala": _shadbala,
    "avastha": _avastha,
    "sky_today": _sky,
    "nadi": _nadi,
    "reading": _reading,
    "career": _career,
    "d6": _d6,
    "health": _health,
    "dosha_radar": _dosha_radar,
    "house_links": _house_links,
    "gochar": _gochar,
    "life_cycle": _life_cycle,
    "tamil_doshas": _tamil_doshas,
    "indu_lagna": _indu,
    "ashtakavarga": _ashtakavarga,
    "bhavat_bhavam": _bhavat_bhavam,
    "forecast_facts": _forecast_facts,
    "prashna": _prashna,
    "mitra_muhurta": _mitra_muhurta,
}

LIMITS = {
    "classical_rules": 14000,
    "nadi": 12000,
    "house_links": 12000,
    "life_cycle": 12000,
    "reading": 10000,
    "dosha_radar": 10000,
}


def run_chart_tool(name: str, chart: dict, location: str = "Chennai", args: dict | None = None) -> dict:
    args = args if isinstance(args, dict) else {}
    if name == "classical_rules":
        from agents.classical import classical_enabled

        if not classical_enabled():
            return {"error": "Classical rules are switched off."}
        try:
            house = int(args.get("house") or 0)
        except (TypeError, ValueError):
            house = 0
        topic = args.get("topic") if isinstance(args.get("topic"), str) else None
        return _with_cite(name, _classical_rules(chart, house if 1 <= house <= 12 else None, topic))
    handler = HANDLERS.get(name)
    if not handler:
        return {"error": f"Unknown tool {name}"}
    return _with_cite(name, handler(chart, location, args))


def tool_result_json(name: str, chart: dict, location: str = "Chennai", arguments: str = "") -> str:
    try:
        args = json.loads(arguments) if arguments else {}
    except ValueError:
        args = {}
    try:
        payload = run_chart_tool(name, chart, location, args if isinstance(args, dict) else {})
    except Exception as exc:
        payload = {"error": str(exc)}
    limit = LIMITS.get(name, 6000)
    return json.dumps(payload, default=str)[:limit]
