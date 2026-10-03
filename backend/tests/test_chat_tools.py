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
