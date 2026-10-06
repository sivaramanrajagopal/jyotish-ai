"""The sitting speaks the Muzaffarpur chart in order, from engines already in the app."""

from datetime import date

from agents.natal_agent import calculate_natal_chart
from agents.reading_agent import compute_reading

AS_OF = date(2026, 10, 6)


def _muzaffarpur():
    chart = calculate_natal_chart("1996-05-10", "10:54", 26.1482548, 85.3316097, "Asia/Kolkata")
    chart["birth_data"]["gender"] = "female"
    chart["birth_data"]["place_of_birth"] = "Muzaffarpur"
    return chart


def test_sitting_for_muzaffarpur_woman():
    reading = compute_reading(_muzaffarpur(), as_of=AS_OF)

    assert "Cancer lagna" in reading["who"]["sentence"]
    assert "Capricorn" in reading["who"]["sentence"]
    assert "Aries" in reading["who"]["sentence"]

    voice = reading["voice"]["sentence"]
    assert "Jupiter" in voice and "short" in voice
    assert "Saturn" in voice
    assert "Marriage starts from Mars" in voice
    jupiter = next(row for row in reading["voice"]["rows"] if row["planet"] == "Jupiter")
    assert jupiter["short"] is True
    sun = next(row for row in reading["voice"]["rows"] if row["planet"] == "Sun")
    assert sun["short"] is False
    assert sun["sukshma"]

    chapter = reading["chapter"]
    assert chapter["mahadasha"] == "Jupiter"
    assert chapter["bhukti"] == "Mercury"
    assert chapter["bhukti_end"] == "11 Oct 2026"
    assert chapter["days_left"] == 5
    assert chapter["next_bhukti"]["planet"] == "Ketu"

    pressing = reading["pressing"]["sentence"]
    assert "Krishna Ekadashi" in pressing
    assert "Tara Pratyari" in pressing
    assert "Saturn is retrograde in Pisces" in pressing
    assert "Chandra Ashtama is clear" in pressing
    by_planet = {}
    for house in reading["pressing"]["houses"]:
        assert house["sav_label"] in ("Strong", "Good", "Average", "Weak")
        for planet in house["planets"]:
            by_planet[planet] = house
    assert by_planet["Jupiter"]["house"] == 1
    assert by_planet["Saturn"]["house"] == 9
    assert "9th" in by_planet["Saturn"]["line"]
    assert "Fortune" in by_planet["Saturn"]["line"]
    assert "Retrograde Saturn is in the 9th" in by_planet["Saturn"]["line"]
    assert "Sarvashtakavarga" in by_planet["Saturn"]["line"]

    life = {row["id"]: row for row in reading["life"]}
    assert life["work"]["open"] is True
    assert life["marriage"]["open"] is False
    assert life["marriage"]["significator"] == "Mars"
    assert "3 Jun 2027" in life["marriage"]["when"]
    assert reading["life"][0]["open"] is True

    assert "Ketu bhukti" in reading["next"]["sentence"]
    assert "Father, Marriage and Skill are next" in reading["next"]["sentence"]
    assert reading["snags"]["alerts"]
    assert reading["snags"]["sentence"].endswith("active.") or "alerts are active" in reading["snags"]["sentence"]
