"""Chat system prompt includes Career (D1 + D10) context."""

from agents.chat_agent import _build_gochara_block


def test_chat_prompt_includes_career():
    from agents.natal_agent import calculate_natal_chart

    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {"dob": "1978-09-18", "name": "Test", "timezone": "Asia/Kolkata"}
    block = _build_gochara_block(chart, {})
    assert "Career (D1 + D10)" in block
    assert "10th lord" in block
    assert "Mars" in block  # Sivaraman canonical 10th lord
