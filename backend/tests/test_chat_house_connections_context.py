"""Chat prompt — House Links narrator context."""

from agents.chat_agent import _build_gochara_block
from agents.house_connections.narrator import house_connections_context_for_narrator
from agents.natal_agent import calculate_natal_chart


def _chart():
    c = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    c["birth_data"] = {"dob": "1978-09-18", "timezone": "Asia/Kolkata", "lat": 13.0827, "lon": 80.2707}
    return c


def test_chat_prompt_includes_house_connections():
    chart = _chart()
    block = _build_gochara_block(chart, chart.get("dasha") or {}, user_message="hello")
    assert "HOUSE CONNECTIONS" in block


def test_compact_context_by_default():
    ctx = house_connections_context_for_narrator(_chart(), user_message="What is my dasha?")
    assert "COMPACT SUMMARY" in ctx
    assert "--- H9" not in ctx
    assert "H9 Fortune" in ctx


def test_detail_context_for_h9_question():
    ctx = house_connections_context_for_narrator(_chart(), user_message="Explain my H9 house links")
    assert "HOW TO EXPLAIN HOUSE LINKS" in ctx
    assert "--- H9 Fortune & dharma" in ctx
    assert "Channels IN (feeding H9): H1, H3, H4, H8" in ctx
    assert "Mars (H3 lord) placed in H9" in ctx
    assert "Primary blesser: Venus (score 42.0)" in ctx


def test_detail_includes_h7_h10_for_generic_house_links():
    ctx = house_connections_context_for_narrator(_chart(), user_message="Map my house links")
    assert "--- H7" in ctx
    assert "--- H9" in ctx
    assert "--- H10" in ctx
