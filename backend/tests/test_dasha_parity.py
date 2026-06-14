"""Cross-app Vimshottari parity — jyotish-ai dasha_core vs Mundane dasha_logic."""

import datetime
import sys
from pathlib import Path

import pytest

from agents.dasha_agent import get_personal_dasha
from dasha_core import find_current_dasha_bhukti, fmt_period, generate_dashas, get_nakshatra

# Mundane dashboard (sibling app — optional, not in CI checkout)
_ROOT = Path(__file__).resolve().parents[3]
_dasha_logic_path = _ROOT / "dasha_logic.py"
if _dasha_logic_path.is_file():
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    import dasha_logic  # noqa: E402
else:
    dasha_logic = None

pytestmark_mundane = pytest.mark.skipif(
    dasha_logic is None,
    reason="dasha_logic.py not present (local monorepo only)",
)


REF = datetime.datetime(2026, 6, 6, 12, 0, 0)


def test_nakshatra_boundary_matches_core():
    """360° edge case — index must not exceed 26."""
    nak, pada, idx = get_nakshatra(359.99)
    assert idx == 26
    assert nak == "Revati"
    assert 1 <= pada <= 4


@pytestmark_mundane
def test_personal_and_mundane_india_dasha_match():
    """India founding chart — personal engine vs mundane get_country_dasha."""
    moon = dasha_logic.COUNTRY_BIRTH_DATA["India"]["moon_long"]
    dob = dasha_logic.COUNTRY_BIRTH_DATA["India"]["birth_date"]

    personal = get_personal_dasha(moon, dob, current_dt=REF)
    mundane = dasha_logic.get_country_dasha("India", current_dt=REF)

    assert personal["mahadasha"]["planet"] == mundane["mahadasha"]["planet"]
    assert personal["bhukti"]["planet"] == mundane["bhukti"]["planet"]
    assert personal["mahadasha"]["start"] == mundane["mahadasha"]["start"]
    assert personal["mahadasha"]["end"] == mundane["mahadasha"]["end"]
    assert personal["bhukti"]["start"] == mundane["bhukti"]["start"]
    assert personal["bhukti"]["end"] == mundane["bhukti"]["end"]
    assert personal["relationship"] == mundane["relationship"]


@pytestmark_mundane
def test_generate_dashas_shared_with_mundane():
    moon = 100.0
    dob = "1990-06-15"
    core_dashas = generate_dashas(moon, dob)
    mundane_dashas = dasha_logic.generate_dashas(moon, dob)

    assert len(core_dashas) == len(mundane_dashas) == 27
    for a, b in zip(core_dashas, mundane_dashas):
        assert a["planet"] == b["planet"]
        assert a["start"] == b["start"]
        assert a["end"] == b["end"]
        assert a["years"] == b["years"]


def test_bhukti_table_markdown_present():
    result = get_personal_dasha(100.0, "1990-06-15", current_dt=REF)
    table = result.get("bhukti_table_markdown") or ""
    assert "| Bhukti (Planet) |" in table
    assert result["bhukti"]["planet"] in table
    assert "← **current**" in table
    assert len(result["antardasha_sequence"]) == 9


def test_find_current_dasha_bhukti_dates():
    _, cur_d, _, cur_b = find_current_dasha_bhukti(100.0, "1990-06-15", REF)
    assert cur_d["start"] <= REF < cur_d["end"]
    assert cur_b["start"] <= REF < cur_b["end"]
    assert fmt_period(cur_d["start"]) == get_personal_dasha(100.0, "1990-06-15", REF)["mahadasha"]["start"]
