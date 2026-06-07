"""
Delete all server-side data for an authenticated user.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

_USER_TABLES = (
    "ai_usage",
    "chat_history",
    "forecasts",
    "ashtama_alerts",
    "user_daily_panchangam",
    "user_locations",
    "natal_charts",
    "users",
)


def delete_user_account(user_id: str) -> None:
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Account deletion is temporarily unavailable.") from exc

    for table in _USER_TABLES:
        try:
            sb.table(table).delete().eq("user_id", user_id).execute()
        except Exception as exc:
            logger.warning("delete_user_account: %s for %s: %s", table, user_id, exc)

    try:
        sb.auth.admin.delete_user(user_id)
    except Exception as exc:
        logger.exception("auth.admin.delete_user failed for %s", user_id)
        raise HTTPException(
            status_code=500,
            detail="Could not complete account deletion. Please contact support.",
        ) from exc
