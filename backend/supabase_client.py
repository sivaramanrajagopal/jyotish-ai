"""
supabase_client.py
==================
Singleton Supabase client using the service role key (backend only).
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env from the backend directory (works regardless of cwd)
load_dotenv(Path(__file__).parent / ".env")


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL") or ""
    key = os.getenv("SUPABASE_SERVICE_KEY") or ""
    if not url or not key:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_KEY not set in .env")
    return create_client(url, key)
