"""Classical text rules (BPHS) matched against the natal chart. Read-only add-on."""

from __future__ import annotations

import os


def classical_enabled() -> bool:
    """On by default; set CLASSICAL_RULES_ENABLED=0 to remove the route, chat tool and card."""
    return os.getenv("CLASSICAL_RULES_ENABLED", "1").strip().lower() not in ("0", "false", "off", "no")


def classical_for_chart(chart: dict) -> dict:
    from agents.classical.rules import match_rules
    from agents.shadbala_agent import compute_shadbala_for_chart

    try:
        shadbala = compute_shadbala_for_chart(chart)
    except Exception:
        shadbala = None
    return match_rules(chart, shadbala)
