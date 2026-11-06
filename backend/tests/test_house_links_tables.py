"""House Links tables: natal connections, dasha lords, today's transits."""

from datetime import date

from agents.house_connections.activation import compute_activation
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.tables import compute_tables
from agents.house_connections.upcoming import compute_upcoming
from agents.house_connections.yogas import detect_yogas
from agents.natal_agent import calculate_natal_chart

AS_OF = date(2026, 11, 6)


def _tables() -> dict:
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    houses = analyze_all_houses(chart)
    activation = compute_activation(chart, houses, detect_yogas(houses, chart), AS_OF)
    upcoming = compute_upcoming(chart, houses, AS_OF)
    return compute_tables(chart, houses, activation, upcoming)


def _codes(row: dict) -> dict[int, str]:
    return {c["house"]: c["codes"] for c in row["connected"]}


def test_natal_codes_for_the_10th():
    tenth = _codes(_tables()["natal"][9])
    assert tenth == {1: "A", 3: "S", 4: "C", 9: "LC", 12: "A"}  # Mars in its own star


def test_natal_exchange_reads_both_ways():
    natal = _tables()["natal"]
    assert "X" in _codes(natal[1])[6] and "X" in _codes(natal[5])[2]


def test_natal_connections_are_symmetric_for_two_way_codes():
    natal = {r["house"]: _codes(r) for r in _tables()["natal"]}
    for h, links in natal.items():
        for other, codes in links.items():
            for code in set(codes) & set("XCMANS"):
                assert code in natal[other][h]


def test_natal_mutual_aspect_is_told_apart_from_one_way():
    natal = {r["house"]: _codes(r) for r in _tables()["natal"]}
    assert natal[6][7] == "M"
    assert natal[10][1] == "A"


def test_natal_star_lord_links():
    natal = {r["house"]: _codes(r) for r in _tables()["natal"]}
    # 6th lord Moon in Revati (Mercury): Mercury rules the 5th and 8th
    assert natal[6][5] == "N" and natal[6][8] == "N"
    # 4th lord Venus in Swati (Rahu); Rahu in Virgo acts for Mercury
    assert natal[4][5] == "N" and natal[4][8] == "N"
    # 1st lord Saturn in Magha (Ketu); Ketu in Pisces acts for Jupiter
    assert natal[1][2] == "N" and natal[1][11] == "N"


def _brief(both: list[dict]) -> list[tuple]:
    return [(b["house"], b["level"], b["start"], b["end"], b["now"]) for b in both]


def test_dasha_rows_current_and_next():
    rows = _tables()["dasha"]
    assert [(r["planet"], r["current"]) for r in rows[:3]] == [("Moon", True), ("Ketu", True), ("Venus", False)]
    ketu = rows[1]
    assert ketu["activated"] == [2, 11] and ketu["connected"] == [4, 6, 8, 12]
    assert _brief(ketu["both"]) == [
        (11, "main", "6 Nov 2026", "7 Jan 2027", True),
        (8, "side", "6 Nov 2026", "7 Jan 2027", True),
    ]
    venus = rows[2]
    assert venus["activated"] == [4, 9] and venus["connected"] == [3, 5, 8]
    assert (4, "main", "27 Nov 2027", "28 Feb 2028", False) in _brief(venus["both"])


def test_live_until_dates():
    assert _tables()["live_until"] == {7: "24 Jan 2027", 8: "24 Jan 2027", 11: "2 Jun 2027"}


def test_live_now_ends_when_jupiter_turns_back():
    moon = _tables()["dasha"][0]
    assert moon["connected"] == [5, 7, 8]
    assert _brief(moon["both"])[:4] == [
        (7, "side", "6 Nov 2026", "24 Jan 2027", True),
        (8, "side", "6 Nov 2026", "24 Jan 2027", True),
        (2, "main", "25 Jan 2027", "2 Jun 2027", False),
        (6, "main", "25 Jan 2027", "2 Jun 2027", False),
    ]


def test_transit_rows_today():
    rows = {r["planet"]: r for r in _tables()["transit"]}
    assert rows["Jupiter"]["house"] == 7 and rows["Jupiter"]["aspects"] == [1, 3, 11]
    assert rows["Saturn"]["house"] == 2 and rows["Saturn"]["retrograde"]
    assert rows["Saturn"]["aspects"] == [4, 8, 11]
    assert rows["Ketu"]["aspects"] == [1, 5, 9]
    assert rows["Jupiter"]["next"] == {"sign": "Cancer", "house": 6, "date": "25 Jan 2027"}
    assert rows["Saturn"]["next"] == {"sign": "Aries", "house": 3, "date": "3 Jun 2027"}
