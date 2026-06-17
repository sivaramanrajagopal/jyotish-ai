"""Chat prompt must include Tamil dosha context for remedy questions."""

from agents.chat_agent import _build_system
from agents.dasha_agent import get_personal_dasha
from agents.natal_agent import calculate_natal_chart


def test_chat_prompt_includes_tamil_doshas():
    chart = calculate_natal_chart(
        "1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata",
    )
    chart["birth_data"] = {"dob": "1978-09-18", "name": "Test", "timezone": "Asia/Kolkata"}
    moon_lon = chart["planet_positions"]["Moon"]["longitude"]
    chart["dasha"] = get_personal_dasha(moon_lon, "1978-09-18")

    prompt = _build_system(chart, "Chennai")

    assert "TAMIL PREDICTIVE DOSHAS" in prompt
    assert "Thithi Soonyam" in prompt
    assert "Vadhai red zone" in prompt
    assert "Vainasikam red zone" in prompt
    assert "Yogi graha" in prompt
    assert "HOUSE-SPECIFIC PARIHARA SEEDS" in prompt
    assert "DOSHA REMEDY RULES FOR AI" in prompt
    assert "Dwitiya" in prompt or "dagdha" in prompt.lower()
    assert chart["planet_positions"]["Moon"]["nakshatra"] in prompt or "Revati" in prompt
