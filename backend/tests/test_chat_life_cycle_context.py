"""Chat system prompt includes Life Cycle timing context — but only when asked."""

from agents.chat_agent import _build_gochara_block, _wants_life_cycle
from agents.natal_agent import calculate_natal_chart
from chart_utils import ensure_dasha

_HEADER = "=== LIFE CYCLE —"


def _golden_chart():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    return ensure_dasha(chart)


def test_wants_life_cycle_gate():
    assert _wants_life_cycle("what is coming in the next few years?")
    assert _wants_life_cycle("when will my marriage happen?")
    assert _wants_life_cycle("best period for career timing")
    assert not _wants_life_cycle("what is my lagna?")
    assert not _wants_life_cycle("explain my 10th house")
    assert not _wants_life_cycle("")


def test_life_cycle_block_attached_for_timing_question():
    chart = _golden_chart()
    block = _build_gochara_block(chart, {}, user_message="best period in the next 5 years?")
    assert _HEADER in block
    assert "Strongest activation windows" in block
    assert "Event themes" in block
    # Anti-hallucination guard-rail must be present in the grounded block.
    assert "never invent timing" in block.lower()


def test_life_cycle_block_absent_for_non_timing_question():
    chart = _golden_chart()
    block = _build_gochara_block(chart, {}, user_message="what is my moon sign?")
    assert _HEADER not in block
