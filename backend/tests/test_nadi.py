"""Nadi readings explain the chain and name a season, not a job or a single day."""

from datetime import date

from agents.natal_agent import calculate_natal_chart
from agents.nadi_agent import compute_nadi

AS_OF = date(2026, 10, 4)


def _chennai(gender="male"):
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {"gender": gender}
    return chart


def _reading(payload, key):
    return next(row for row in payload["readings"] if row["id"] == key)


def test_work_and_foreign_chains_for_chennai():
    payload = compute_nadi(_chennai(), as_of=AS_OF)
    assert "does not name a job" in payload["view"]
    assert "fire, earth, air, or water" in payload["method"]

    work = _reading(payload, "work")
    assert work["now"]["sign"] == "Leo"
    assert "Saturn" in work["now"]["label"] and "Mercury" in work["now"]["label"]
    assert work["past"]["label"] == "Jupiter"
    assert "Rahu" in work["follows"]["label"]
    assert "Aries and Sagittarius are empty" in work["analysis"]
    assert "Mars is not in this chain" in work["analysis"]
    assert work["significator"] == "Saturn"
    fire = next(fam for fam in work["board"] if fam["name"] == "fire")
    assert fire["signs_line"] == "Aries, Leo, Sagittarius"
    assert fire["available"] == "Mercury, Saturn"
    earth = next(fam for fam in work["board"] if fam["name"] == "earth")
    assert "the Sun" in earth["available"] and "Rahu" in earth["available"]
    leo = next(cell for cell in fire["signs"] if cell["sign"] == "Leo")
    assert leo["role"] == "happening"
    assert next(bit for bit in leo["planets"] if bit["name"] == "Saturn")["significator"] is True
    assert next(bit for bit in leo["planets"] if bit["name"] == "Mercury")["significator"] is False
    assert any(row["planets"] == "Mercury and Saturn (significator)" for row in work["reasons"])
    assert any(row["place"] == "Outside" and row["planets"] == "Mars" for row in work["reasons"])
    assert work["season_status"].startswith("This season is not open today")
    assert work["timing"][0]["kind"] == "Season"
    assert work["timing"][0]["planet"] == "Jupiter"
    assert "software" not in work["analysis"].lower()

    foreign = _reading(payload, "foreign")
    assert foreign["family"]["name"] == "earth"
    assert "Taurus" in foreign["family"]["line"] and "Capricorn" in foreign["family"]["line"]
    assert "empty" in foreign["analysis"]
    assert foreign["now"]["sign"] == "Virgo"
    assert "Saturn" in foreign["past"]["label"] and "Mercury" in foreign["past"]["label"]
    assert foreign["follows"]["sign"] == "Libra"
    assert foreign["opposite"]["sign"] == "Pisces"
    assert "Because Rahu is retrograde" in foreign["analysis"]
    assert any(row["planets"] == "the Sun and retrograde Rahu (significator)" for row in foreign["reasons"])
    assert "the Moon is not in this chain" not in foreign["analysis"]

    jupiter = next(row for row in foreign["seasons"] if row["planet"] == "Jupiter")
    assert jupiter["start"].startswith("2027")
    assert jupiter["end"].startswith("2030")
    signs = {row["sign"] for row in jupiter["passes"]}
    assert "Virgo" in signs and "Libra" in signs


def test_marriage_follows_gender():
    male = _reading(compute_nadi(_chennai("male"), as_of=AS_OF), "marriage")
    female = _reading(compute_nadi(_chennai("female"), as_of=AS_OF), "marriage")
    assert male["karaka"] == "Venus"
    assert "male chart" in male["analysis"]
    assert female["karaka"] == "Mars"
    assert "female chart" in female["analysis"]
    assert female["now"]["sign"] == "Libra"
