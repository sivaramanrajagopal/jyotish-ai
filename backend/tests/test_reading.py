"""The sitting speaks the Muzaffarpur chart in order, from engines already in the app."""

from datetime import date

from agents.natal_agent import calculate_natal_chart
from agents.reading_agent import compute_reading, compute_watch

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

    marriage = life["marriage"]["house"]["lines"]
    assert any("7th lord" in line for line in marriage)
    assert any("Mars is the marriage significator" in line for line in marriage)
    assert life["work"]["house"]["lines"]


def _chennai():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"]["gender"] = "male"
    return chart


def test_house_giving_for_chennai_man():
    life = {row["id"]: row["house"]["lines"] for row in compute_reading(_chennai(), as_of=AS_OF)["life"]}

    money = life["money"]
    assert money[0] == (
        "The 2nd lord is Jupiter, exalted in Cancer, "
        "the 6th from the lagna and the 5th from this house."
    )
    assert "Jupiter aspects this house" in money[1]
    assert "Ketu and Moon sit there" in money[1]
    assert "sits apart from the lords of the 6th, the 8th, and the 12th" in money[2]
    assert "in Virgo, an enemy sign" in money[3]
    assert "The fruit is thinner." in money[3]
    assert any(
        "Jupiter aspects from 8.85° Cancer, Pushya pada 2, a Pushkara Navamsa" in line
        and "Ketu sits at 3.20° Pisces" in line
        for line in money
    )
    assert any(line.startswith("A remedy for Jupiter") for line in money)
    assert any("Mercury, the lord, is at 21.28° Leo, on the Pushkara degree" in line for line in life["children"])
    assert not any("Pushkara" in line for line in life["skill"])

    gains = life["gains"]
    assert "the 8th from this house" in gains[0]
    assert "does not aspect this house" in gains[1]

    marriage = life["marriage"]
    assert "The 7th lord is Sun" in marriage[0]
    assert "Venus is the marriage significator, in Libra, own sign, the 9th." in marriage
    assert not any(line.startswith("A remedy") for line in marriage)

    assert "The fruit holds." in life["skill"][3]
    assert "joined with Mercury, lord of the 8th" in life["self"][2]
    assert "In the Navamsa chart the 9th is Sagittarius" in "".join(life["father"])


def test_timeline_note_and_watch():
    chart = _muzaffarpur()
    reading = compute_reading(chart, as_of=AS_OF)
    assert "mahadasha began" in reading["timeline"]["past"]
    assert reading["timeline"]["today"].startswith("Open:")
    assert "Ketu bhukti begins" in reading["timeline"]["next"]
    assert "Father, Marriage and Skill are next" in reading["next"]["sentence"]

    watch = compute_watch(chart, as_of=AS_OF)
    assert watch["days_until_bhukti"] == 5
    assert watch["next_bhukti"]["planet"] == "Ketu"
    assert watch["days_until_season"] is not None

    chart["birth_data"]["note"] = "married"
    noted = compute_reading(chart, as_of=AS_OF)
    assert "already lived" in noted["voice"]["sentence"]
    assert "Marriage starts from" not in noted["voice"]["sentence"]
    lead = noted["next"]["sentence"].split("Already open")[0]
    assert "Marriage" not in lead
    assert noted["life"][-1]["id"] == "marriage"

    chart["birth_data"]["note"] = "work"
    focused = compute_reading(chart, as_of=AS_OF)
    assert focused["life"][0]["id"] == "work"
