"""Chat system prompt includes Bhavat Bhavam context."""

from agents.chat_agent import _build_gochara_block


def test_chat_prompt_includes_bhavam():
    from agents.natal_agent import calculate_natal_chart

    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {
        "dob": "1978-09-18",
        "name": "Test",
        "timezone": "Asia/Kolkata",
        "lat": 13.0827,
        "lon": 80.2707,
    }
    block = _build_gochara_block(chart, {})
    assert "Bhavat Bhavam" in block
