"""Chat prompt — rich House Links explanation context."""

from agents.chat_agent import _build_gochara_block
from agents.house_connections.narrator import house_connections_context_for_narrator
from agents.natal_agent import calculate_natal_chart


def _chart():
    c = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    c["birth_data"] = {"dob": "1978-09-18", "timezone": "Asia/Kolkata", "lat": 13.0827, "lon": 80.2707}
    return c


def test_chat_prompt_includes_house_connections():
    chart = _chart()
    dasha = chart.get("dasha") or {}
    block = _build_gochara_block(chart, dasha)
    assert "HOUSE CONNECTIONS" in block


def test_narrator_includes_explanation_guide():
    ctx = house_connections_context_for_narrator(_chart())
    assert "HOW TO EXPLAIN HOUSE LINKS" in ctx
    assert "HOUSE-BY-HOUSE DETAIL" in ctx


def test_narrator_h9_channels_for_chennai_native():
    ctx = house_connections_context_for_narrator(_chart())
    assert "--- H9 Fortune & dharma" in ctx
    assert "Channels IN (life areas feeding into H9): H1, H3, H4, H8" in ctx
    assert "Mars (H3 lord) placed in H9" in ctx
    assert "Channels OUT (H9 radiates to): H3, H4, H7, H10, H12" in ctx
    assert "Primary blesser: Venus (score 42.0)" in ctx
    assert "STRESS · Venus (H4 lord) placed in H9" in ctx
