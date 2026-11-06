"""House Links logic fixes: Aries links, exchanges, deduplicated yogas, BPHS benefics."""

from agents.bhavat_bhavam.core import _lords_linked
from agents.house_connections.core import analyze_all_houses
from agents.house_connections.edges import build_edges, parivartana_kind
from agents.house_connections.yogas import detect_yogas
from agents.natal_agent import SIGNS, calculate_natal_chart


def _synthetic(asc: int, seats: dict[str, int]) -> dict:
    return {
        "ascendant": {"sign_index": asc, "sign": SIGNS[asc]},
        "planet_positions": {
            p: {"sign_index": s, "sign": SIGNS[s], "longitude": s * 30 + 10.0}
            for p, s in seats.items()
        },
    }


# Aries lagna. Moon (4th lord) in Sagittarius and Jupiter (9th lord) in Cancer swap signs.
ARIES_EXCHANGE = _synthetic(0, {
    "Sun": 0, "Mars": 0, "Moon": 8, "Jupiter": 3, "Mercury": 1,
    "Venus": 10, "Saturn": 6, "Rahu": 2, "Ketu": 8,
})


def _chart_a() -> dict:
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


def test_lords_in_aries_still_link():
    pp = ARIES_EXCHANGE["planet_positions"]
    assert "conjunction" in _lords_linked("Mars", "Sun", pp, 0)


def test_conjunction_reported_once():
    pp = ARIES_EXCHANGE["planet_positions"]
    assert _lords_linked("Mars", "Sun", pp, 0).count("conjunction") == 1


def test_no_redundant_sign_lord_edges():
    chart = _chart_a()
    edges = build_edges(analyze_all_houses(chart), chart)
    assert not any(e["kind"] == "sign_lord" for e in edges)


def test_exchange_edges_chart_a():
    chart = _chart_a()
    edges = build_edges(analyze_all_houses(chart), chart)
    pairs = {(e["from_house"], e["to_house"]) for e in edges if e["kind"] == "exchange"}
    assert pairs == {(2, 6), (7, 8)}
    assert all(not e["supportive"] for e in edges if e["kind"] == "exchange")


def test_parivartana_kind():
    assert parivartana_kind(4, 9) == "maha"
    assert parivartana_kind(3, 10) == "khala"
    assert parivartana_kind(2, 6) == "dainya"


def test_exchange_raja_yoga_needs_kendra_trikona_swap():
    yogas = detect_yogas(analyze_all_houses(ARIES_EXCHANGE), ARIES_EXCHANGE)
    exchange = [y for y in yogas if y["type"] == "exchange"]
    assert len(exchange) == 1
    assert set(exchange[0]["lords"]) == {"Moon", "Jupiter"}
    assert "H4 and H9" in exchange[0]["detail_en"]


def test_chart_a_yogas_deduplicated():
    chart = _chart_a()
    yogas = detect_yogas(analyze_all_houses(chart), chart)
    pairs = [frozenset(y["lords"]) for y in yogas]
    assert len(pairs) == len(set(pairs))
    assert all(len(y["lords"]) == 1 or y["lords"][0] != y["lords"][1] for y in yogas)
    names = sorted(y["name"] for y in yogas)
    assert names == [
        "Dharma-Karma Adhipati Yoga",
        "Raja Yoga",
        "Raja Yoga",
        "Raja Yoga",
        "Yogakaraka",
    ]
    karaka = next(y for y in yogas if y["name"] == "Yogakaraka")
    assert karaka["lords"] == ["Venus"] and karaka["houses"] == [4, 9]
    assert not any(y["type"] == "exchange" for y in yogas)


def test_taurus_saturn_is_dharma_karma_yogakaraka():
    chart = _synthetic(1, {
        "Sun": 0, "Moon": 3, "Mars": 4, "Mercury": 5, "Jupiter": 6,
        "Venus": 7, "Saturn": 9, "Rahu": 2, "Ketu": 8,
    })
    yogas = detect_yogas(analyze_all_houses(chart), chart)
    karaka = next(y for y in yogas if y["lords"] == ["Saturn"])
    assert karaka["name"] == "Yogakaraka (Dharma-Karma Adhipati)"
    assert karaka["houses"] == [9, 10]


def test_waning_moon_aspect_is_not_supportive():
    chart = _synthetic(0, {
        "Sun": 0, "Moon": 9, "Mars": 2, "Mercury": 1, "Jupiter": 5,
        "Venus": 1, "Saturn": 6, "Rahu": 4, "Ketu": 10,
    })
    chart["planet_positions"]["Moon"]["longitude"] = 280.0  # 270 degrees ahead of the Sun: waning
    edges = build_edges(analyze_all_houses(chart), chart)
    moon = [e for e in edges if e["kind"] == "aspect_on_house" and e["planets"] == ["Moon"]]
    assert moon and all(not e["supportive"] for e in moon)
