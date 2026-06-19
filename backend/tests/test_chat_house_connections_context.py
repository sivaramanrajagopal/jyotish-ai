"""Chat prompt includes house connections context."""

from agents.chat_agent import _build_gochara_block
from agents.natal_agent import calculate_natal_chart


def test_chat_prompt_includes_house_connections():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {"dob": "1978-09-18", "timezone": "Asia/Kolkata", "lat": 13.0827, "lon": 80.2707}
    dasha = chart.get("dasha") or {}
    block = _build_gochara_block(chart, dasha)
    assert "HOUSE CONNECTIONS" in block
