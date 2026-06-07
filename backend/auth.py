"""
auth.py — Supabase JWT verification (Step 3).

Verifies Bearer tokens issued by Supabase Auth using the project JWT secret.
Anonymous routes remain available; user_id in body/path must match the token.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException
from jwt.exceptions import InvalidTokenError

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "").strip()
JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = "authenticated"


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: Optional[str] = None


def is_auth_configured() -> bool:
    return bool(JWT_SECRET)


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header.")
    token = parts[1].strip()
    return token or None


def verify_supabase_jwt(token: str) -> dict:
    if not JWT_SECRET:
        raise HTTPException(status_code=503, detail="Authentication is not configured on the server.")
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
        )
    except InvalidTokenError as exc:
        logger.info("JWT verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from exc


def user_from_payload(payload: dict) -> AuthUser:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user id.")
    email = payload.get("email")
    return AuthUser(id=str(user_id), email=str(email) if email else None)


def get_auth_user_from_token(token: str) -> AuthUser:
    return user_from_payload(verify_supabase_jwt(token))


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
) -> Optional[AuthUser]:
    """Return authenticated user when a valid Bearer token is present."""
    token = _extract_bearer_token(authorization)
    if not token:
        return None
    return get_auth_user_from_token(token)


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> AuthUser:
    """Require a valid Bearer token."""
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return get_auth_user_from_token(token)


def resolve_user_id(
    requested_user_id: Optional[str],
    auth_user: Optional[AuthUser],
) -> Optional[str]:
    """
    Determine the user_id to persist.

    - Body user_id without token → 401
    - Body user_id != token sub → 403
    - Token only → use token sub
    - Neither → None (anonymous)
    """
    if requested_user_id:
        if not auth_user:
            raise HTTPException(
                status_code=401,
                detail="A valid Bearer token is required when user_id is provided.",
            )
        if requested_user_id != auth_user.id:
            raise HTTPException(
                status_code=403,
                detail="user_id does not match authenticated user.",
            )
        return auth_user.id

    if auth_user:
        return auth_user.id

    return None


def require_path_user(auth_user: AuthUser, path_user_id: str) -> None:
    """Ensure URL {user_id} matches the authenticated JWT subject."""
    if path_user_id != auth_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")
