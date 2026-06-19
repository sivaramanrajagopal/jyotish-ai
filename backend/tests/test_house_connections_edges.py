"""House Connections — edge graph excludes Bhavat Bhavam from channels."""

from agents.house_connections.edges import build_edges
from agents.house_connections.inference import dusthana_recovery_edges
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.blessers import rank_blessers
from agents.house_connections_agent import compute_house_connections
from agents.natal_agent import calculate_natal_chart

CHENNAI = {
    "dob": "1978-09-18",
    "tob": "17:35",
    "lat": 13.0827,
    "lon": 80.2707,
    "tz": "Asia/Kolkata",
}


def _chart():
    c = calculate_natal_chart(
        CHENNAI["dob"], CHENNAI["tob"],
        CHENNAI["lat"], CHENNAI["lon"], CHENNAI["tz"],
    )
    c["birth_data"] = {"dob": CHENNAI["dob"], "timezone": CHENNAI["tz"]}
    return c


def test_build_edges_excludes_bhavat_bhavam():
    chart = _chart()
    houses = analyze_all_houses(chart)
    edges = build_edges(houses, chart)
    assert not any(e["kind"] == "bhavat_bhavam" for e in edges)


def test_dusthana_recovery_edges_separate_from_graph():
    chart = _chart()
    houses = analyze_all_houses(chart)
    assert dusthana_recovery_edges(6, houses)[0]["to_house"] == 11
    assert dusthana_recovery_edges(8, houses)[0]["to_house"] == 3
    assert dusthana_recovery_edges(12, houses)[0]["to_house"] == 11
    assert dusthana_recovery_edges(10, houses) == []


def test_chennai_native_channels_after_bb_removal():
    """Sivaraman chart — BB out of graph; recovery notes on H6/H12; blessers recalculated."""
    out = compute_house_connections(_chart())
    h6 = next(p for p in out["predictions"] if p["house"] == 6)
    h11 = next(p for p in out["predictions"] if p["house"] == 11)
    h12 = next(p for p in out["predictions"] if p["house"] == 12)

    assert h6["recovery_edges"][0]["to_house"] == 11
    assert h12["recovery_edges"][0]["to_house"] == 11
    assert h11["channels_in"] == [2, 6]
    assert h12["channels_out"] == [1, 6, 7]
    assert h6["top_blesser"]["planet"] == "Moon"
    assert h6["top_blesser"]["score"] == 29.0
    assert h11["top_blesser"]["score"] == 22.0


def test_blessers_exclude_bb_edges():
    chart = _chart()
    houses = analyze_all_houses(chart)
    edges = build_edges(houses, chart)
    bl = rank_blessers(6, houses, edges, chart, "Moon", "Mercury")
    reasons = [r["en"] for b in bl for r in b.get("reasons", [])]
    assert not any("Bhavat Bhavam" in r for r in reasons)
