"""
admin_auth.py — owner-only access for /admin/* routes.
Accepts X-Admin-Token OR a signed-in JWT whose email is in ADMIN_EMAILS.
"""

from __future__ import annotations

import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException

from auth import AuthUser, get_current_user_optional


def admin_emails() -> set[str]:
    raw = os.getenv("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def is_admin_email(email: Optional[str]) -> bool:
    if not email:
        return False
    allowed = admin_emails()
    return bool(allowed) and email.strip().lower() in allowed


async def require_admin(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    authorization: Optional[str] = Header(None),
) -> AuthUser:
    """Allow admin token header or owner JWT."""
    expected = os.getenv("ADMIN_TOKEN", "").strip()
    if x_admin_token and expected and secrets.compare_digest(x_admin_token, expected):
        return AuthUser(id="admin-token", email="admin@token")

    user = await get_current_user_optional(authorization)
    if user and is_admin_email(user.email):
        return user

    raise HTTPException(status_code=403, detail="Admin access required.")
