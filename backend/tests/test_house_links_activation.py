"""House Links activation: dasha switches houses on, Jupiter and Saturn trigger them."""

from datetime import date

from agents.house_connections.activation import _distance, compute_activation, dasha_reasons
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.yogas import detect_yogas
from agents.house_connections_agent import compute_house_connections
from agents.natal_agent import calculate_natal_chart

AS_OF = date(2026, 11, 6)


def _chart() -> dict:
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


def _activation() -> dict:
    chart = _chart()
    houses = analyze_all_houses(chart)
    return compute_activation(chart, houses, detect_yogas(houses, chart), AS_OF)


def _rows() -> dict[int, dict]:
    return {r["house"]: r for r in _activation()["rows"]}


def test_period_moon_ketu():
    period = _activation()["period"]
    assert period["mahadasha"]["planet"] == "Moon"
    assert period["bhukti"]["planet"] == "Ketu"
    assert period["bhukti"]["end"] == "7 Jan 2027"
    assert period["next_bhukti"]["planet"] == "Venus"


def test_distance_folds_to_classical_pairs():
    assert _distance(1, 1) == 1
    assert _distance(1, 8) == 6 and _distance(8, 1) == 6
    assert _distance(1, 12) == 2
    assert _distance(1, 9) == 5
    assert _distance(1, 7) == 7


def test_ketu_acts_for_its_sign_lord():
    chart = _chart()
    reasons = dasha_reasons("Ketu", "bhukti", chart["planet_positions"], chart["ascendant"]["sign_index"])
    main = {h for h, rows in reasons.items() if any(r["level"] == "main" for r in rows)}
    assert main == {2, 11}  # Ketu in Pisces (2nd), Jupiter rules the 2nd and 11th


def test_ketu_also_gives_the_moon_it_sits_with():
    chart = _chart()
    reasons = dasha_reasons("Ketu", "bhukti", chart["planet_positions"], chart["ascendant"]["sign_index"])
    assert [r["level"] for r in reasons[6]] == ["side"]
    assert "sits with Moon" in reasons[6][0]["en"]


def test_node_star_lord_acts_through_its_sign_lord():
    chart = _chart()
    reasons = dasha_reasons("Venus", "bhukti", chart["planet_positions"], chart["ascendant"]["sign_index"])
    # Venus in Swati (Rahu's star); Rahu in Virgo, so Mercury's 5th and 8th
    for h in (5, 8):
        assert reasons[h][0]["level"] == "side"
        assert "sign lord Mercury" in reasons[h][0]["en"]


def test_double_transit_chart_a():
    rows = _rows()
    # Jupiter in Leo (7th) aspects 11, 1, 3; Saturn in Pisces (2nd) aspects 4, 8, 11.
    assert rows[11]["transit"]["double"] and rows[11]["status"]["key"] == "live"
    assert rows[8]["status"]["key"] == "live"
    assert rows[7]["status"]["key"] == "sky"
    assert rows[2]["status"]["key"] == "waiting"
    assert rows[10]["status"]["key"] == "quiet"


def test_now_ranks_main_dasha_houses_first():
    activation = _activation()
    assert activation["now"][:3] == [11, 2, 6]
    assert 7 not in activation["now"]


def test_rows_carry_reading_fruit_and_no_scores():
    rows = _rows()
    assert rows[10]["fruit"]["en"] == "The fruit holds."
    for row in rows.values():
        assert "strength" not in row and "score" not in row
        assert row["fruit"]["tone"] in ("good", "mixed", "hard")
        assert len(row["links"]) <= 3


def test_house_connections_includes_activation():
    out = compute_house_connections(_chart())
    assert len(out["activation"]["rows"]) == 12


def test_activation_failure_leaves_the_rest_of_the_tab():
    chart = _chart()
    chart["birth_data"] = {"dob": "1978-09-18"}  # no birth time: transit scoring cannot run
    out = compute_house_connections(chart)
    assert out["activation"] is None
    assert len(out["houses"]) == 12
