"""Shadbala against the Prokerala sheet for 18 Sep 1978, 17:35, Chennai."""

from datetime import datetime
from zoneinfo import ZoneInfo

from agents.shadbala.calc import _jd, compute_shadbala

# Printed Prokerala values. Nathonnata on that sheet is about 1.5 virupas
# from apparent solar time; rank and the positional balas still have to match.
PROKERALA = {
    "Sun": {"uchcha": 12.78, "saptavargaja": 90.0, "dig": 33.0, "drik": 6.61, "rank": 1, "ratio": 1.53},
    "Moon": {"uchcha": 47.05, "saptavargaja": 30.0, "dig": 40.49, "drik": -25.05, "rank": 5, "ratio": 1.11},
    "Mars": {"uchcha": 22.51, "saptavargaja": 127.5, "dig": 44.29, "drik": 18.94, "rank": 4, "ratio": 1.14},
    "Mercury": {"uchcha": 52.09, "saptavargaja": 121.88, "dig": 0.46, "drik": 2.27, "rank": 7, "ratio": 0.98},
    "Jupiter": {"uchcha": 58.72, "saptavargaja": 75.0, "dig": 14.6, "drik": 10.71, "rank": 3, "ratio": 1.14},
    "Venus": {"uchcha": 6.3, "saptavargaja": 118.13, "dig": 12.26, "drik": 2.12, "rank": 6, "ratio": 1.02},
    "Saturn": {"uchcha": 37.72, "saptavargaja": 84.38, "dig": 56.83, "drik": 3.62, "rank": 2, "ratio": 1.34},
}


def _chennai():
    birth = datetime(1978, 9, 18, 17, 35, tzinfo=ZoneInfo("Asia/Kolkata"))
    return compute_shadbala(_jd(birth), 13.0827, 80.2707, birth)


def test_positional_balas_match_prokerala():
    by_name = {row["planet"]: row for row in _chennai()["planets"]}
    for planet, expected in PROKERALA.items():
        got = by_name[planet]
        for key in ("uchcha", "saptavargaja", "dig", "drik"):
            assert abs(got[key] - expected[key]) < 0.03, (planet, key, got[key], expected[key])


def test_rank_and_ratio_match_prokerala():
    by_name = {row["planet"]: row for row in _chennai()["planets"]}
    for planet, expected in PROKERALA.items():
        assert by_name[planet]["rank"] == expected["rank"]
        assert abs(by_name[planet]["ratio"] - expected["ratio"]) <= 0.02
    assert by_name["Mercury"]["meets_minimum"] is False
    assert all(by_name[p]["meets_minimum"] for p in PROKERALA if p != "Mercury")


def test_pondicherry_mercury_meets_minimum_when_south():
    """15 Jan 1984, 13:20, Pondicherry. Mercury is far south; Ayana stays high."""
    birth = datetime(1984, 1, 15, 13, 20, tzinfo=ZoneInfo("Asia/Kolkata"))
    result = compute_shadbala(_jd(birth), 11.9416, 79.8083, birth)
    by_name = {row["planet"]: row for row in result["planets"]}
    assert by_name["Mercury"]["ayana"] > 55
    assert by_name["Mercury"]["meets_minimum"] is True
    assert [row["planet"] for row in sorted(result["planets"], key=lambda r: r["rank"])] == [
        "Mars", "Saturn", "Sun", "Venus", "Jupiter", "Moon", "Mercury",
    ]


def test_lords_for_chennai_monday():
    result = _chennai()
    assert result["varsha_lord"] == "Sun"
    assert result["masa_lord"] == "Sun"
    assert result["dina_lord"] == "Moon"
    assert result["hora_lord"] == "Sun"
    assert all(row["yuddha"] == 0 for row in result["planets"])
