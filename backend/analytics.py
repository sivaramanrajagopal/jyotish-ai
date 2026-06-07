"""
Lightweight product event logging (optional Supabase app_events table).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from supabase_client import get_supabase
    _SB = True
except Exception:
    _SB = False


def track_event(
    event_name: str,
    user_id: Optional[str] = None,
    properties: Optional[dict[str, Any]] = None,
) -> None:
    """Best-effort insert; never raises to callers."""
    if not _SB:
        return
    try:
        sb = get_supabase()
        sb.table("app_events").insert({
            "user_id": user_id,
            "event_name": event_name,
            "properties": properties or {},
        }).execute()
    except Exception as exc:
        logger.debug("track_event skipped (%s): %s", event_name, exc)
