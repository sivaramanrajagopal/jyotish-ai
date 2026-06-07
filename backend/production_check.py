"""
production_check.py — validate env config at startup (Step 1 security hardening).
Logs warnings in development; logs errors in production for misconfiguration.
"""

from __future__ import annotations

import logging
import os
import secrets

logger = logging.getLogger(__name__)

LOCALHOST_MARKERS = ("localhost", "127.0.0.1", "0.0.0.0")


def _is_production() -> bool:
    return os.getenv("APP_ENV", "development").lower() == "production"


def _origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()]


def run_production_checks() -> None:
    """Call once at app startup."""
    prod = _is_production()
    issues: list[str] = []
    warnings: list[str] = []

    origins = _origins()
    if not origins:
        issues.append("ALLOWED_ORIGINS is empty — CORS will block all browsers.")

    if prod:
        for o in origins:
            if any(m in o for m in LOCALHOST_MARKERS):
                issues.append(f"ALLOWED_ORIGINS contains localhost in production: {o}")

        admin = os.getenv("ADMIN_TOKEN", "")
        if not admin:
            warnings.append("ADMIN_TOKEN is not set — bulk-preload admin route disabled.")
        elif len(admin) < 24:
            issues.append("ADMIN_TOKEN is too short — use at least 32 random characters.")

        if not os.getenv("OPENAI_API_KEY", "").strip():
            warnings.append("OPENAI_API_KEY not set — chat/forecast AI routes will fail.")

        if not os.getenv("SUPABASE_URL", "").strip():
            warnings.append("SUPABASE_URL not set — Panchangam cache disabled.")

        if not os.getenv("SUPABASE_JWT_SECRET", "").strip():
            warnings.append(
                "SUPABASE_JWT_SECRET not set — authenticated user_id routes will reject tokens."
            )

        if os.getenv("SUPABASE_SERVICE_KEY", "").strip():
            pass  # expected for backend
        else:
            warnings.append("SUPABASE_SERVICE_KEY not set — DB features disabled.")
    else:
        warnings.append("APP_ENV is not 'production' — user_id routes and debug endpoints stay relaxed.")

    for w in warnings:
        logger.warning("[config] %s", w)
    for issue in issues:
        if prod:
            logger.error("[config] PRODUCTION MISCONFIG: %s", issue)
        else:
            logger.warning("[config] %s (would block in production)", issue)

    if prod and issues:
        logger.error(
            "[config] Fix %d production issue(s) before accepting public traffic. See docs/STEP-1-PRODUCTION-CONFIG.md",
            len(issues),
        )


def generate_admin_token() -> str:
    """Helper for docs — generate a secure admin token."""
    return secrets.token_urlsafe(32)
