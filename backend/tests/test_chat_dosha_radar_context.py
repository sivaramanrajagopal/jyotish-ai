"""Chat prompt must include Dosha Radar context."""

from agents.chat_agent import _build_gochara_block
from agents.natal_agent import calculate_natal_chart


def test_chat_prompt_includes_dosha_radar():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {"dob": "1978-09-18", "timezone": "Asia/Kolkata"}
    dasha = chart.get("dasha") or {}
    ctx = _build_gochara_block(chart, dasha)
    assert "DOSHA RADAR" in ctx
