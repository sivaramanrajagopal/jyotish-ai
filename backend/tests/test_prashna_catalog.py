"""Prashna catalog sync — every dropdown question_id must resolve on the backend."""

import pytest

from agents.prashna.analyzer import analyze_prashna
from agents.prashna.constants import (
    CATEGORY_HOUSE,
    CATEGORY_QUESTIONS,
    KEY_INTEREST_HOUSE,
    resolve_question,
)


def test_every_catalog_question_id_resolves():
    for category, questions in CATEGORY_QUESTIONS.items():
        assert category in CATEGORY_HOUSE, f"Missing house mapping for {category}"
        for q in questions:
            qid, text = resolve_question(category, q["id"], None)
            assert qid == q["id"], f"{category}/{q['id']}"
            assert text == q["text"]


def test_key_interest_house_overrides():
    for qid, house in KEY_INTEREST_HOUSE.items():
        _, text = resolve_question("key_interest", qid, None)
        assert text
        result = analyze_prashna(
            question=text,
            category="key_interest",
            question_id=qid,
            timestamp_iso="2026-06-06T12:00:00",
            timezone="Asia/Kolkata",
            lat=13.0827,
            lon=80.2707,
            place="Chennai",
        )
        assert result["analysis"]["relevant_house"]["house_num"] == house


@pytest.mark.parametrize("category,question_id", [
    ("career", "interview_career"),
    ("money", "salary_raise"),
    ("travel", "pilgrimage"),
    ("general", "decision"),
    ("competitive_exam", "govt_exam"),
    ("lost_and_found", "lost_document"),
])
def test_new_catalog_questions_analyze(category, question_id):
    _, text = resolve_question(category, question_id, None)
    result = analyze_prashna(
        question=text,
        category=category,
        question_id=question_id,
        timestamp_iso="2026-06-06T14:00:00",
        timezone="Asia/Kolkata",
    )
    assert result["question"]["id"] == question_id
    assert result["verdict"]["result"]
