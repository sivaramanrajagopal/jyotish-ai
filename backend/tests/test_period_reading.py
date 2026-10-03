"""Period reading ties Shadbala, Avastha, BAV, and SAV into plain sentences."""

from agents.dasha_agent import get_personal_dasha
from agents.natal_agent import calculate_natal_chart
from agents.period_reading import compose_period_reading, compute_period_reading, strength_phrase


def _chennai_chart():
    chart = calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")
    chart["birth_data"] = {
        "dob": "1978-09-18",
        "tob": "17:35",
        "lat": 13.0827,
        "lon": 80.2707,
        "timezone": "Asia/Kolkata",
    }
    moon = chart["planet_positions"]["Moon"]["longitude"]
    chart["dasha"] = get_personal_dasha(moon, "1978-09-18")
    return chart


def test_short_planet_is_named_as_short():
    phrase = strength_phrase({
        "rupas": 6.87,
        "minimum": 7,
        "ratio": 0.98,
        "meets_minimum": False,
    })
    assert phrase.startswith("6.87 / 7")
    assert "short of the strength it needs" in phrase


def test_chennai_period_names_both_lords_and_their_ground():
    reading = compute_period_reading(_chennai_chart())
    assert reading["mahadasha"]
    assert reading["bhukti"]
    assert reading["lead"]
    assert [lord["role"] for lord in reading["lords"]] == ["Mahadasha", "Bhukti"]
    for lord in reading["lords"]:
        assert lord["condition"]
        assert lord["ground"]
        if lord["planet"] in ("Rahu", "Ketu"):
            assert "house it occupies" in lord["strength"]
            assert "Occupies house" in lord["ground"]
        else:
            assert "/" in lord["strength"]
            assert "points" in lord["ground"]
            assert "house" in lord["ground"]


def test_compose_uses_the_period_class_for_the_lead():
    chart = {
        "dasha": {"mahadasha": {"planet": "Sun"}, "bhukti": {"planet": "Moon"}},
        "ascendant": {"sign": "Aries"},
        "planet_positions": {
            "Sun": {"sign": "Leo", "sign_index": 4, "house": 5},
            "Moon": {"sign": "Cancer", "sign_index": 3, "house": 4},
        },
    }
    shadbala = {
        "planets": [
            {"planet": "Sun", "rupas": 7.5, "minimum": 5, "ratio": 1.5, "meets_minimum": True},
            {"planet": "Moon", "rupas": 6.2, "minimum": 6, "ratio": 1.03, "meets_minimum": True},
        ]
    }
    avastha = {
        "dasa_bhukti": {"manifestationClass": "Inertia / Delays"},
        "planets": [
            {"planet": "Sun", "sthula": {"name": "Deepta"}, "sukshma": {"name": "Nidra"},
             "manifestation": {"net": 30}},
            {"planet": "Moon", "sthula": {"name": "Muditha"}, "sukshma": {"name": "Prakasha"},
             "manifestation": {"net": 70}},
        ],
    }
    ashtakavarga = {
        "bav": {"SUN": {"sign_wise": [0] * 4 + [5] + [0] * 7}, "MOON": {"sign_wise": [0] * 3 + [3] + [0] * 8}},
        "sav": {"by_house": [
            {"house": 4, "sav_points": 22, "label": "Average"},
            {"house": 5, "sav_points": 31, "label": "Strong"},
        ]},
    }
    reading = compose_period_reading(chart, shadbala, avastha, ashtakavarga)
    assert "slow" in reading["lead"]
    sun, moon = reading["lords"]
    assert "well above" in sun["strength"]
    assert "5 points" in sun["ground"]
    assert "fertile" in sun["ground"]
    assert "nothing to spare" in moon["strength"]
    assert "thin ground" in moon["ground"]
