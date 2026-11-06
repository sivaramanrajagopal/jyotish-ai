"""BPHS chapter 24 rules matched against charts the app already calculates."""

from itertools import product

from agents.classical.facts import lord_facts, planet_natures, strength_label
from agents.classical.rules import _pick_variant, load_rules, load_verses, match_rules
from agents.natal_agent import calculate_natal_chart
from agents.shadbala_agent import compute_shadbala_for_chart
from scripts.extract_bphs import placement_for_verse


def _chart_a():
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


def test_verse_numbers_map_to_each_lord_and_house_once():
    pairs = {placement_for_verse(v) for v in range(1, 145)}
    assert len(pairs) == 144
    assert placement_for_verse(1) == (1, 1)
    assert placement_for_verse(13) == (2, 1)
    assert placement_for_verse(144) == (12, 12)
    assert placement_for_verse(145) is None


def test_stored_verses_carry_their_placement():
    verses = load_verses()["by_verse"]
    assert sorted(verses) == list(range(1, 149))
    assert "lord of the ascendant" in verses[1]["translation"]
    assert "twelfth house" in verses[144]["translation"]
    for rule in load_rules():
        verse = verses[rule["verse"]]
        assert (verse["lord_of"], verse["in_house"]) == (rule["lord_of"], rule["in_house"])


def test_all_144_placements_have_a_rule():
    rules = load_rules()
    assert len(rules) == 144
    assert {(r["lord_of"], r["in_house"]) for r in rules} == {(l, h) for l in range(1, 13) for h in range(1, 13)}
    assert all(v["tone"] in ("favourable", "mixed", "challenging") for r in rules for v in r["variants"])


def test_every_rule_gives_a_result_for_any_chart():
    used = {key for r in load_rules() for v in r["variants"] for key in v["when"]}
    values = {key: (True, False) for key in used}
    values["lord_nature"] = ("benefic", "malefic")
    values["lord_strong"] = (True, False, None)
    keys = sorted(used)
    for rule in load_rules():
        for combo in product(*(values[k] for k in keys)):
            assert _pick_variant(rule, dict(zip(keys, combo))), rule["id"]


def test_verse_37_carries_its_source_correction():
    verse = load_verses()["by_verse"][37]
    assert (verse["lord_of"], verse["in_house"]) == (4, 1)
    assert "dhanage" in verse["source_note"]


def test_chart_a_natures_follow_bphs():
    natures = planet_natures(_chart_a()["planet_positions"])
    assert natures["Moon"] == "malefic"      # waning Moon (Krishna paksha)
    assert natures["Mercury"] == "malefic"   # shares Leo with Saturn
    assert natures["Jupiter"] == natures["Venus"] == "benefic"


def test_chart_a_lord_facts():
    facts = {f["house"]: f for f in lord_facts(_chart_a())}
    assert len(facts) == 12
    first = facts[1]
    assert (first["lord"], first["lord_house"], first["lord_sign"]) == ("Saturn", 7, "Leo")
    assert first["joined_by"] == ["Mercury"]
    assert first["aspected_by"] == []
    assert facts[2]["dignity"] == "Exalted"           # Jupiter in Cancer
    assert facts[6]["aspected_by"] == ["Sun", "Jupiter", "Rahu"]


def test_chart_a_matches_one_rule_per_house_lord():
    chart = _chart_a()
    result = match_rules(chart, compute_shadbala_for_chart(chart))
    cites = [m["source"]["cite"] for m in result["matches"]]
    assert cites == [f"BPHS 24.{v}" for v in (7, 18, 33, 45, 55, 62, 80, 91, 105, 117, 126, 139)]
    assert result["pending_houses"] == []

    first = result["matches"][0]
    assert first["conditions"] == {"lord_nature": "malefic"}
    assert first["tone"] == "challenging"
    assert first["strength"] == "full"
    assert "marriage" in first["topics"]
    assert first["why"].startswith("Saturn, lord of the 1st (Aquarius), sits in Leo in the 7th house")
    assert "enemy sign" in first["why"]

    by_verse = {m["source"]["verse"]: m for m in result["matches"]}
    assert by_verse[18]["conditions"] == {}              # exalted Jupiter in the 6th, joined by no one
    assert by_verse[91]["conditions"] == {"malefic_conjunct": True}   # Mercury with Saturn


def test_chart_a_dual_lordship_notes():
    chart = _chart_a()
    notes = {n["lord"]: n for n in match_rules(chart, compute_shadbala_for_chart(chart))["dual_lordship"]}
    assert set(notes) == {"Saturn", "Jupiter", "Mars", "Venus", "Mercury"}
    assert "opposite directions" in notes["Mercury"]["note"]   # 5th favourable, 8th challenging
    assert "both results apply" in notes["Venus"]["note"]


def test_lagna_lord_in_twelfth_is_held_back_by_benefic_support():
    rule = next(r for r in load_rules() if r["verse"] == 12)
    assert _pick_variant(rule, {"benefic_aspect_or_conjunct": False})["tone"] == "challenging"
    assert _pick_variant(rule, {"benefic_aspect_or_conjunct": True})["tone"] == "mixed"


def test_strength_label_reads_shadbala_ratio():
    shadbala = {"planets": [
        {"planet": "Sun", "ratio": 1.2}, {"planet": "Moon", "ratio": 0.85}, {"planet": "Mars", "ratio": 0.6},
    ]}
    assert strength_label(shadbala, "Sun") == "full"
    assert strength_label(shadbala, "Moon") == "half"
    assert strength_label(shadbala, "Mars") == "quarter"
    assert strength_label(None, "Sun") is None


def test_matching_leaves_the_chart_unchanged():
    chart = _chart_a()
    before = repr(chart)
    match_rules(chart)
    assert repr(chart) == before
