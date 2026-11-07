"""Prashna endpoint: the rule-based verdict survives an AI limit; a bad timezone is a 422."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import ai_limits
import main

BODY = {
    "category": "career",
    "question_id": "promotion",
    "timestamp": "2026-06-06T14:30:00",
    "timezone": "Asia/Kolkata",
    "lat": 13.0827,
    "lon": 80.2707,
    "place": "Chennai",
}


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(ai_limits, "_SB", False)
    ai_limits._mem_anon.clear()
    return TestClient(main.app)


def test_ai_limit_still_returns_verdict(client, monkeypatch):
    def limited(*_args, **_kwargs):
        raise HTTPException(status_code=429, detail="Daily AI limit reached.")

    monkeypatch.setattr(main, "charge_ai_quota", limited)
    res = client.post("/prashna/analyze", json={**BODY, "include_ai": True})
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"]["label"]
    assert "ai_reading" not in data
    assert data["meta"]["ai_skipped"] == "Daily AI limit reached."


def test_bad_timezone_is_422(client):
    res = client.post("/prashna/analyze", json={**BODY, "timezone": "Mars/Olympus"})
    assert res.status_code == 422
