"""Chat system prompt must include computed next Mahadashas (anti-hallucination)."""

from agents.chat_agent import _build_system
from agents.dasha_agent import get_personal_dasha
from agents.natal_agent import calculate_natal_chart


def test_chat_prompt_includes_next_mahadasha_block():
    chart = calculate_natal_chart(
        "1990-06-15", "14:30", 13.0827, 80.2707, "Asia/Kolkata",
    )
    chart["birth_data"] = {"dob": "1990-06-15", "name": "Test"}
    moon_lon = chart["planet_positions"]["Moon"]["longitude"]
    chart["dasha"] = get_personal_dasha(moon_lon, "1990-06-15")

    prompt = _build_system(chart, "Chennai")
    next_md = chart["dasha"]["next_dashas"][0]

    assert "NEXT MAHADASHAS" in prompt
    assert "NEXT Mahadasha (1st after current)" in prompt
    assert next_md["planet"] in prompt
    assert next_md["start"] in prompt
    assert next_md["end"] in prompt
    assert "UPCOMING BHUKTIS" in prompt
    assert "Mahadasha timeline table" in prompt
    assert "CRITICAL DASHA RULES" in prompt
    assert "FULL DASA CYCLE" in prompt
    assert chart["dasha"]["full_dasha_cycle_markdown"]
    assert "Mahadasha cycle (major periods)" in chart["dasha"]["full_dasha_cycle_markdown"]


def test_full_dasha_cycle_markdown_structure():
    from dasha_core import format_full_dasha_cycle_markdown
    from agents.dasha_agent import get_personal_dasha

    dasha = get_personal_dasha(100.0, "1990-06-15")
    block = format_full_dasha_cycle_markdown(dasha)
    assert "Vimshottari Dasa–Bhukti overview" in block
    assert "| Mahadasha (Planet) |" in block
    assert "| Bhukti (Planet) |" in block
    assert dasha["mahadasha"]["planet"] in block


def test_refresh_dasha_recomputes_next_mahadashas():
    from chart_utils import refresh_dasha

    chart = {
        "planet_positions": {"Moon": {"longitude": 100.0, "sign": "Cancer"}},
        "birth_data": {"dob": "1990-06-15"},
        "dasha": {
            "mahadasha": {"planet": "Moon", "start": "Jan 2020", "end": "Jan 2030"},
            # stale — missing next_dashas
        },
    }
    out = refresh_dasha(chart, force=True)
    assert len(out["dasha"]["next_dashas"]) >= 1
    assert out["dasha"]["mahadasha_timeline_markdown"]
