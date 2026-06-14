"""Analytics event endpoint."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_analytics_event_accepts_valid_name():
    r = client.post("/analytics/event", json={"event_name": "tab_view", "properties": {"tab": "chart"}})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_analytics_event_rejects_invalid_name():
    r = client.post("/analytics/event", json={"event_name": "Bad Name!", "properties": {}})
    assert r.status_code == 400
