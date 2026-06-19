"""House Connections — logic validation tests."""

import pytest

from agents.house_connections.core import (
    analyze_all_houses,
    houses_from_own,
    position_type_from_own,
)
from agents.natal_agent import calculate_natal_chart

CHENNAI = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}


def _manual_houses_from_own(owned: int, placed: int) -> int:
    """Reference: owned house counts as 1st."""
    for n in range(1, 13):
        h = ((owned - 1 + n - 1) % 12) + 1
        if h == placed:
            return n
    raise ValueError(f"no placement {placed} from {owned}")


@pytest.mark.parametrize("owned,placed", [
    (1, 1), (5, 5), (11, 11),
    (11, 6), (10, 7), (5, 9), (5, 4), (5, 5),
    (1, 7), (4, 10), (9, 10),
])
def test_houses_from_own_matches_manual(owned, placed):
    assert houses_from_own(owned, placed) == _manual_houses_from_own(owned, placed)


def test_position_type_own_is_first_only():
    assert position_type_from_own(1) == "own_house"
    assert position_type_from_own(12) == "dusthana_from_own"  # 12th from own, not own house


def test_sivaraman_h11_jupiter_in_h6():
    c = calculate_natal_chart(
        CHENNAI["dob"], CHENNAI["tob"],
        CHENNAI["lat"], CHENNAI["lon"], CHENNAI["tz"],
    )
    h11 = analyze_all_houses(c)[11]
    assert h11["lord"] == "Jupiter"
    assert h11["lord_house"] == 6
    assert h11["houses_from_own"] == 8
    assert h11["position_type"] == "dusthana_from_own"
    assert h11["rag"]["status"] == "moderate"


def test_all_houses_have_valid_hfo():
    c = calculate_natal_chart(
        CHENNAI["dob"], CHENNAI["tob"],
        CHENNAI["lat"], CHENNAI["lon"], CHENNAI["tz"],
    )
    for h, row in analyze_all_houses(c).items():
        assert 1 <= row["houses_from_own"] <= 12
        assert row["position_type"] in (
            "own_house", "kendra_from_own", "trikona_from_own",
            "upachaya_from_own", "dusthana_from_own", "neutral_from_own",
        )
