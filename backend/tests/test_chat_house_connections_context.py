"""Chat prompt — House Links narrator context, on the House Links tab rules."""

from agents.chat_agent import _build_gochara_block
from agents.house_connections.narrator import house_connections_context_for_narrator
from agents.natal_agent import calculate_natal_chart


def _chart():
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


def test_chat_prompt_includes_house_connections():
    chart = _chart()
    block = _build_gochara_block(chart, chart.get("dasha") or {}, user_message="hello")
    assert "HOUSE CONNECTIONS" in block


def test_compact_context_by_default():
    ctx = house_connections_context_for_narrator(_chart(), user_message="What is my dasha?")
    assert "ALL HOUSES" in ctx
    assert "--- H9" not in ctx
    assert "H9 Fortune & dharma: lord Venus in H9" in ctx
    assert "/100" not in ctx
    assert "blesser" not in ctx.lower()


def test_context_carries_exchanges_and_remedies():
    ctx = house_connections_context_for_narrator(_chart())
    assert "Dainya Parivartana H2–H6" in ctx
    assert "Dainya Parivartana H7–H8" in ctx
    assert "Jupiter (for H2, H11)" in ctx


def test_detail_context_for_h7_question():
    ctx = house_connections_context_for_narrator(_chart(), user_message="Explain my 7th house")
    assert "HOW TO EXPLAIN A HOUSE" in ctx
    assert "--- H7 Partnership & marriage" in ctx
    assert "Moon's star lord Mercury sits here (connected)" in ctx
    assert "H8 LHX" in ctx
    assert "remedy · Sun, the lord" in ctx


def test_detail_includes_h7_h9_h10_for_generic_house_links():
    ctx = house_connections_context_for_narrator(_chart(), user_message="Map my house links")
    assert "--- H7" in ctx
    assert "--- H9" in ctx
    assert "--- H10" in ctx
