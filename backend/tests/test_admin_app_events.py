"""Admin app_events aggregation."""

from admin_router import _aggregate_app_events


def test_aggregate_app_events_by_name_and_funnel():
    rows = [
        {"event_name": "chart_calculated", "user_id": "u1", "created_at": "2026-06-01T10:00:00Z", "properties": {}},
        {"event_name": "chat_sent", "user_id": "u1", "created_at": "2026-06-01T11:00:00Z", "properties": {"language": "english"}},
        {"event_name": "chat_sent", "user_id": "u2", "created_at": "2026-06-02T09:00:00Z", "properties": {}},
        {"event_name": "prashna_analyze", "user_id": "u2", "created_at": "2026-06-02T10:00:00Z", "properties": {"category": "career"}},
    ]
    agg = _aggregate_app_events(rows)
    assert agg["total_in_range"] == 4
    assert agg["by_event"][0]["event_name"] == "chat_sent"
    assert agg["by_event"][0]["count"] == 2
    assert agg["funnel"]["chart_then_chat"] == 1
    assert agg["prashna_categories"][0]["category"] == "career"
