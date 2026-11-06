"""Life Cycle on the House Links rules — Chart A (1978-09-18 17:35 Chennai, Aquarius lagna)."""

from datetime import date

import pytest

from agents.life_cycle import compute_life_cycle
from agents.natal_agent import calculate_natal_chart

AS_OF = date(2026, 11, 6)


@pytest.fixture(scope="module")
def chart():
    return calculate_natal_chart("1978-09-18", "17:35", 13.0827, 80.2707, "Asia/Kolkata")


@pytest.fixture(scope="module")
def lc(chart):
    return compute_life_cycle(chart, as_of=AS_OF, married=True)


def _theme(lc, key):
    return next(t for t in lc["themes"] if t["key"] == key)


def test_now_matches_house_links(lc):
    now = lc["now"]
    assert (now["mahadasha"], now["bhukti"]) == ("Moon", "Ketu")
    assert [r["house"] for r in now["on"]] == [2, 6, 8, 11]
    assert {r["house"]: r["until"] for r in now["live"]} == {8: "7 Jan 2027", 11: "7 Jan 2027"}


def test_sade_sati_now(lc):
    first = lc["saturn"][0]
    assert first["kind"] == "sade_sati"
    assert first["start"] == "18 Jan 2023"
    assert first["now"]
    assert any(p["now"] and p["from_moon"] == 1 for p in first["phases"])
    assert any(s["kind"] == "ardhashtama" and s["start"] == "31 May 2032" for s in lc["saturn"])


def test_themes_have_no_scores_and_marriage_does_not_lead(lc):
    assert lc["themes"][0]["key"] != "marriage"
    for t in lc["themes"]:
        assert "score" not in str(t.keys())
    spouse = _theme(lc, "marriage")
    assert spouse["label_en"] == "Spouse & partnership"
    assert spouse["notes"]


def test_education_hidden_for_adult(lc):
    assert "education" not in [t["key"] for t in lc["themes"]]


def test_theme_status_and_next_window(lc):
    assert _theme(lc, "health")["status"]["key"] == "live"
    assert _theme(lc, "wealth")["status"]["key"] == "live"
    assert _theme(lc, "career")["status"]["key"] == "quiet"
    nxt = _theme(lc, "property")["next_live"]
    assert (nxt["start"], nxt["bhukti"]) == ("27 Nov 2027", "Venus")


def test_next_window_can_fall_inside_the_running_bhukti(chart):
    later = compute_life_cycle(chart, as_of=date(2027, 1, 10))
    children = _theme(later, "children")
    assert children["status"]["key"] == "waiting"
    assert (children["next_live"]["start"], children["next_live"]["bhukti"]) == ("26 Jun 2027", "Venus")
    for t in later["themes"]:
        if t["next_live"]:
            assert t["next_live"]["start_iso"] > "2027-01-10"


def test_marriage_windows_start_at_eighteen():
    young = calculate_natal_chart("2010-03-12", "08:10", 13.08, 80.27, "Asia/Kolkata")
    lc = compute_life_cycle(young, as_of=AS_OF)
    marriage = _theme(lc, "marriage")
    assert marriage["next_live"]["start_iso"] >= "2028-03-12"
    for w in marriage["windows"]:
        for h in w["houses"]:
            for r in h["live"]:
                assert date.fromisoformat(_iso(r["start"])) >= date(2028, 3, 12)


def _iso(text):
    from datetime import datetime
    return datetime.strptime(text, "%d %b %Y").date().isoformat()


def test_theme_remedies_one_per_lord(lc):
    wealth = _theme(lc, "wealth")
    assert [r["lord"] for r in wealth["remedies"]] == ["Jupiter"]
    assert "gem" not in str(wealth["remedies"]).lower()
