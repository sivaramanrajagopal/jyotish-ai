"""
ai_client.py — one place that builds the chat-completions client.

OPENAI_API_KEY holds either an OpenAI key or a Gemini key. A Gemini key
(starts with "AIza") is sent to Google's OpenAI-compatible endpoint.
AI_BASE_URL and AI_MODEL override the server and model when set.
"""

from __future__ import annotations

import os

from openai import OpenAI

OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def ai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


def ai_base_url() -> str | None:
    explicit = os.getenv("AI_BASE_URL", "").strip()
    if explicit:
        return explicit
    return GEMINI_BASE_URL if ai_api_key().startswith("AIza") else None


def is_gemini() -> bool:
    return "generativelanguage.googleapis.com" in (ai_base_url() or "")


def ai_model() -> str:
    return os.getenv("AI_MODEL", "").strip() or (GEMINI_MODEL if is_gemini() else OPENAI_MODEL)


def ai_client(api_key: str | None = None) -> OpenAI:
    return OpenAI(api_key=api_key or ai_api_key(), base_url=ai_base_url())


def ai_extra() -> dict:
    """Gemini 2.5 Flash thinks by default, and thinking eats the short max_tokens budgets."""
    return {"extra_body": {"reasoning_effort": "none"}} if is_gemini() else {}


def ai_provider() -> str:
    return "Gemini" if is_gemini() else "OpenAI"
