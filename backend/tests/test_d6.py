"""D6 Shashthamsa / Ripu tab tests."""

from copy import deepcopy

from agents.d6.shashthamsa import build_shashthamsa_from_natal, d1_longitude_to_d6
from agents.d6.timing import classify_ripus_window
from agents.d6_agent import compute_d6_analysis, d6_context_for_narrator
from agents.natal_agent import calculate_natal_chart, SIGNS

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
    c["birth_data"] = {
        "dob": CHENNAI["dob"],
        "timezone": CHENNAI["tz"],
        "lat": CHENNAI["lat"],
        "lon": CHENNAI["lon"],
    }
    return c


def _sign_of_lon(lon: float) -> str:
    return SIGNS[int(d1_longitude_to_d6(lon) // 30) % 12]


def test_odd_sign_counts_from_aries():
    # Aries 12° → 3rd 5° slice from Aries → Gemini.
    assert _sign_of_lon(12.0) == "Gemini"
    assert _sign_of_lon(0.0) == "Aries"
    assert _sign_of_lon(5.0) == "Taurus"
    assert _sign_of_lon(29.9) == "Virgo"


def test_even_sign_counts_from_libra():
    # Taurus 12° → 3rd 5° slice from Libra → Sagittarius.
    assert _sign_of_lon(30.0 + 12.0) == "Sagittarius"
    assert _sign_of_lon(30.0) == "Libra"
    assert _sign_of_lon(30.0 + 29.9) == "Pisces"


def test_narasimha_rao_textbook_examples():
    # Mercury 11° Gemini (odd, 3rd slice from Aries) → Gemini.
    assert _sign_of_lon(60.0 + 11.0) == "Gemini"
    # Jupiter 19° Scorpio (even, 4th slice from Libra) → Capricorn.
    assert _sign_of_lon(210.0 + 19.0) == "Capricorn"


def test_rahu_ketu_share_d6_sign():
    # 180° = 36 slices = three rounds of twelve, so the nodes coincide.
    _, pos = build_shashthamsa_from_natal(_chart())
    assert pos["Rahu"]["sign_index"] == pos["Ketu"]["sign_index"]


def test_d6_lagna_changes_houses_not_signs():
    chart = _chart()
    _, pos = build_shashthamsa_from_natal(chart)
    chart2 = deepcopy(chart)
    chart2["ascendant"] = dict(chart["ascendant"])
    chart2["ascendant"]["sign_index"] = (chart["ascendant"]["sign_index"] + 1) % 12
    chart2["ascendant"]["longitude"] = (
        chart2["ascendant"]["sign_index"] * 30.0
        + float(chart["ascendant"].get("degree_in_sign", 0))
    )
    _, pos2 = build_shashthamsa_from_natal(chart2)
    assert pos["Sun"]["sign_index"] == pos2["Sun"]["sign_index"]
    assert pos["Sun"]["house"] != pos2["Sun"]["house"]


def test_chart_a_rao_placements():
    _, pos = build_shashthamsa_from_natal(_chart())
    assert {n: pos[n]["sign"] for n in ("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")} == {
        "Sun": "Libra",
        "Moon": "Aquarius",
        "Mercury": "Leo",
        "Venus": "Cancer",
        "Mars": "Taurus",
        "Jupiter": "Scorpio",
        "Saturn": "Gemini",
        "Rahu": "Libra",
        "Ketu": "Libra",
    }


def test_ripus_analysis_has_themes_and_no_score():
    out = compute_d6_analysis(_chart())
    ids = [c["id"] for c in out["themes"]]
    assert ids == ["debt", "enemies", "exams", "service", "illness"]
    assert all(c["tone"] in ("quiet", "mixed", "present") for c in out["themes"])
    assert "score" not in out["summary"]
    assert out["shashthamsa_ascendant"]["sign"] == "Leo"
    assert "Sun" in out["shashthamsa_positions"]
    assert out["highlight_d1"] == [6, 8]
    assert out["disclaimer"]
    assert out["summary"]["maha_dasa"]
    assert "all" in out["timing"]
    assert out["meaning"]["en"]
    assert out["summary"]["d1_sixth_lord"] in out["meaning"]["en"]
    assert "ask_prompt" in out["meaning"]
    assert out["outlook"]["on"] is True
    assert out["outlook"]["spell_end"]
    assert out["outlook"]["chapter_end"]
    assert "medical" in out["outlook"]["recover_en"].lower()
    illness = next(c for c in out["themes"] if c["id"] == "illness")
    assert illness["eases"]
    assert "Health" in illness["eases"]
    consult = out["consult"]
    assert consult["paragraphs_en"]
    assert "Leo" in consult["en"]
    assert "other party" in consult["en"]
    assert "medical" in consult["en"].lower()
    assert "marriage" not in consult["en"].lower()


def test_narrator_stays_qualitative():
    ctx = d6_context_for_narrator(_chart())
    assert "Ripu" in ctx
    assert "DISCLAIMER" in ctx
    assert "0-100" in ctx
    assert "Health" in ctx
    assert "For the native:" in ctx
    assert "Say to the client:" in ctx
    assert "Watch" in ctx or "Careful" in ctx or "Challenging" in ctx


def test_window_read_watch_careful_challenging():
    watch = classify_ripus_window({
        "maha_dasa": "Moon", "bukti": "Ketu", "links": ["D1 6th lord"],
        "start": "2026-06-08", "end": "2027-01-07", "label": "Moon–Ketu",
    })
    assert watch["read"] == "watch"
    careful = classify_ripus_window({
        "maha_dasa": "Moon", "bukti": "Saturn", "links": ["D1 6th lord", "D6 6th lord"],
        "start": "2023-06-08", "end": "2025-01-06", "label": "Moon–Saturn",
    })
    assert careful["read"] == "careful"
    challenge = classify_ripus_window({
        "maha_dasa": "Sun", "bukti": "Saturn", "links": ["D6 lagna lord", "D6 6th lord"],
        "start": "2016-01-13", "end": "2016-12-25", "label": "Sun–Saturn",
    })
    assert challenge["read"] == "challenging"
    out = compute_d6_analysis(_chart())
    assert out["timing"]["guide"]["tones"]
    current = out["timing"]["current"][0]
    assert current["read"] == "watch"
    assert current["remedy_en"]
    assert "score" not in current
    assert "Moon" in current["why_en"]
    assert "Cancer" in current["why_en"]
    assert "other party" in current["say_en"].lower() or "D6" in current["say_en"]


def _chart_b():
    # Aries lagna — same sky as Chart A, different 1 / 6 / 8 houses.
    c = calculate_natal_chart("1982-04-12", "06:30", 13.0827, 80.2707, "Asia/Kolkata")
    c["birth_data"] = {
        "dob": "1982-04-12",
        "timezone": "Asia/Kolkata",
        "lat": 13.0827,
        "lon": 80.2707,
    }
    return c


def test_two_natives_are_not_the_same_script():
    a = compute_d6_analysis(_chart())
    b = compute_d6_analysis(_chart_b())
    assert a["summary"]["d1_sixth_lord"] != b["summary"]["d1_sixth_lord"] or (
        a["summary"]["d6_lagna"] != b["summary"]["d6_lagna"]
    )
    assert a["consult"]["en"] != b["consult"]["en"]
    assert a["meaning"]["en"] != b["meaning"]["en"]
    a_now = [c["now"] for c in a["themes"]]
    b_now = [c["now"] for c in b["themes"]]
    assert a_now != b_now
    assert len(set(a_now)) > 1


def test_gochara_is_from_this_lagna():
    a = compute_d6_analysis(_chart())
    b = compute_d6_analysis(_chart_b())
    ga, gb = a["gochara"], b["gochara"]
    assert "score" not in ga
    assert {h["house"] for h in ga["houses"]} == {1, 6, 8}
    assert ga["houses"][0]["sign"] != gb["houses"][0]["sign"]
    assert ga["now_en"] != gb["now_en"]
    assert "your lagna" in ga["now_en"].lower()
    assert ga["line_en"]
    assert ga["as_of"]
    assert a["timing"]["current"][0].get("sky_read_en")
