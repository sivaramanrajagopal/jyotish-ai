"""Chat tools return chart numbers without calling the model."""

from agents.chat_tools import run_chart_tool
from agents.dasha_agent import get_personal_dasha
from agents.natal_agent import calculate_natal_chart


def _chennai():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {
        "dob": "1978-09-18",
        "tob": "17:35",
        "lat": 13.0827,
        "lon": 80.2707,
        "timezone": "Asia/Kolkata",
    }
    moon = chart["planet_positions"]["Moon"]["longitude"]
    chart["dasha"] = get_personal_dasha(moon, "1978-09-18")
    return chart


def test_strength_and_period_tools_name_the_chart():
    chart = _chennai()
    strength = run_chart_tool("shadbala", chart)
    assert [row["planet"] for row in strength["planets"]][0] == "Sun"
    assert strength["planets"][-1]["planet"] == "Mercury"
    assert strength["planets"][-1]["meets_minimum"] is False

    period = run_chart_tool("period_reading", chart)
    assert "mahadasha" in period["period"]
    assert period["lords"]

    condition = run_chart_tool("avastha", chart)
    assert condition["period_class"]
    assert len(condition["lords"]) == 2


def test_sky_today_names_the_weekday():
    sky = run_chart_tool("sky_today", _chennai(), "Chennai")
    assert sky["vaaram"]
    assert sky["tithi"]
    assert sky["moon_sign"]


def test_engine_tools_cover_the_desk():
    chart = _chennai()
    nadi = run_chart_tool("nadi", chart, args={"question": "work"})
    assert nadi["cite"]["tab"] == "nadi"
    assert nadi["questions"][0]["id"] == "work"
    assert nadi["questions"][0]["happening"] == "Leo"

    sitting = run_chart_tool("reading", chart)
    assert sitting["cite"]["tab"] == "reading"
    assert sitting["who"]
    assert any(row["id"] == "work" for row in sitting["life"])

    life = run_chart_tool("life_cycle", chart)
    assert "LIFE CYCLE" in life["text"]
    assert life["cite"]["tab"] == "life-cycle"

    career = run_chart_tool("career", chart)
    assert "Career" in career["text"]
    ripu = run_chart_tool("d6", chart)
    assert "Ripu" in ripu["text"]
    assert ripu["cite"]["tab"] == "d6"
    health = run_chart_tool("health", chart)
    assert "Health" in health["text"]
    radar = run_chart_tool("dosha_radar", chart)
    assert "DOSHA RADAR" in radar["text"]
    links = run_chart_tool("house_links", chart, args={"question": "Explain my 10th house"})
    assert "HOUSE CONNECTIONS" in links["text"]
    gochar = run_chart_tool("gochar", chart)
    assert "GOCHARA" in gochar["text"]
    assert "score" not in gochar["text"].lower() or "Never quote a score" in gochar["text"]
    facts = run_chart_tool("forecast_facts", chart, "Chennai")
    assert facts["date"]
    assert facts["cite"]["tab"] == "forecast"
    missing = run_chart_tool("prashna", chart, "Chennai", {})
    assert "error" in missing
    tamil = run_chart_tool("tamil_doshas", chart)
    assert tamil["text"]
    indu = run_chart_tool("indu_lagna", chart)
    assert "Indu" in indu["text"]
    sav = run_chart_tool("ashtakavarga", chart)
    assert sav["text"]
    bhavam = run_chart_tool("bhavat_bhavam", chart)
    assert bhavam["cite"]["tab"] == "health"
    mitra = run_chart_tool("mitra_muhurta", chart, "Chennai", {"month": "2026-11"})
    assert mitra["cite"]["tab"] == "panchangam"
    assert mitra["location"] == "Chennai"
    assert mitra["month"] == "2026-11"
    assert mitra["count"] >= 1
    labels = {row["label"] for row in mitra["windows"]}
    assert any("Ashwini" in label and "Mesha" in label for label in labels)
    assert any("Anusham" in label and "Vrischika" in label for label in labels)
    unknown = run_chart_tool("mitra_muhurta", chart, "Chennai", {"location": "Atlantis"})
    assert "error" in unknown
