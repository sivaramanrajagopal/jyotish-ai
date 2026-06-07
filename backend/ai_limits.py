"""
ai_limits.py — per-user AI quotas and prompt moderation (Step 7).
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date
from typing import Optional

from fastapi import HTTPException

logger = logging.getLogger(__name__)

DAILY_CHAT_LIMIT = int(os.getenv("AI_DAILY_CHAT_LIMIT", "40"))
DAILY_FORECAST_LIMIT = int(os.getenv("AI_DAILY_FORECAST_LIMIT", "25"))

_BLOCKED_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"disregard\s+(the\s+)?(system|above)", re.I),
    re.compile(r"you\s+are\s+now\s+(dan|evil|unrestricted)", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"<\s*script", re.I),
]

try:
    from supabase_client import get_supabase
    _SB = True
except Exception:
    _SB = False


def moderate_user_text(text: str) -> None:
    """Block obvious prompt-injection / XSS attempts in user messages."""
    if not text:
        return
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(text):
            raise HTTPException(status_code=400, detail="Message contains disallowed content.")


def moderate_messages(messages: list[dict]) -> None:
    for msg in messages:
        if msg.get("role") == "user":
            moderate_user_text(str(msg.get("content") or ""))


def _usage_column(kind: str) -> str:
    return "chat_count" if kind == "chat" else "forecast_count"


def check_ai_quota(user_id: Optional[str], kind: str) -> None:
    """
    Enforce daily AI quotas for authenticated users.
    Anonymous callers rely on SlowAPI IP rate limits.
    """
    if not user_id:
        return

    limit = DAILY_CHAT_LIMIT if kind == "chat" else DAILY_FORECAST_LIMIT
    col = _usage_column(kind)
    today = date.today().isoformat()

    if not _SB:
        return

    try:
        sb = get_supabase()
        row = (
            sb.table("ai_usage")
            .select(col)
            .eq("user_id", user_id)
            .eq("usage_date", today)
            .maybe_single()
            .execute()
        )
        current_chat = (row.data or {}).get("chat_count", 0) if row else 0
        current_forecast = (row.data or {}).get("forecast_count", 0) if row else 0
        if kind == "chat":
            if current_chat >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily {kind} limit reached ({limit}). Try again tomorrow.",
                )
            next_chat, next_forecast = current_chat + 1, current_forecast
        else:
            if current_forecast >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily {kind} limit reached ({limit}). Try again tomorrow.",
                )
            next_chat, next_forecast = current_chat, current_forecast + 1

        sb.table("ai_usage").upsert(
            {
                "user_id": user_id,
                "usage_date": today,
                "chat_count": next_chat,
                "forecast_count": next_forecast,
            },
            on_conflict="user_id,usage_date",
        ).execute()
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("AI quota check skipped: %s", exc)


def get_ai_usage(user_id: str) -> dict:
    """Return today's AI usage counts for an authenticated user."""
    today = date.today().isoformat()
    out = {
        "chat_count": 0,
        "forecast_count": 0,
        "chat_limit": DAILY_CHAT_LIMIT,
        "forecast_limit": DAILY_FORECAST_LIMIT,
        "usage_date": today,
    }
    if not _SB:
        return out
    try:
        sb = get_supabase()
        row = (
            sb.table("ai_usage")
            .select("chat_count, forecast_count")
            .eq("user_id", user_id)
            .eq("usage_date", today)
            .maybe_single()
            .execute()
        )
        if row and row.data:
            out["chat_count"] = row.data.get("chat_count", 0) or 0
            out["forecast_count"] = row.data.get("forecast_count", 0) or 0
    except Exception as exc:
        logger.warning("AI usage read skipped: %s", exc)
    return out
