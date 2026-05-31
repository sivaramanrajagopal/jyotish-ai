#!/usr/bin/env python3
"""
preload_panchangam.py
=====================
Bulk-compute and store Panchangam for a full year into Supabase.

Usage:
    # From jyotish-ai/backend/ directory:
    python scripts/preload_panchangam.py                        # current year, all locations
    python scripts/preload_panchangam.py --year 2027            # specific year
    python scripts/preload_panchangam.py --year 2027 --location Chennai   # one location
    python scripts/preload_panchangam.py --start 2026-01-01 --end 2026-12-31  # date range

Options:
    --year YYYY         Year to preload (default: current year)
    --start YYYY-MM-DD  Start date (overrides --year)
    --end   YYYY-MM-DD  End date   (overrides --year)
    --location NAME     Single location (default: all locations)
    --workers N         Parallel threads (default: 4)
    --dry-run           Compute but do NOT write to Supabase
    --skip-existing     Skip dates already in Supabase (faster re-runs)
    --sql FILE          Write SQL INSERT file instead of hitting Supabase directly
                        Run the file in Supabase SQL Editor to bulk import
"""

from __future__ import annotations

import argparse
import datetime
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── Make sure backend/ is on sys.path ───────────────────────────────────────
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from agents.panchangam_agent import LOCATIONS, calculate_panchangam

# ── Optional Supabase ────────────────────────────────────────────────────────
try:
    from supabase_client import get_supabase
    SUPABASE_ENABLED = True
except Exception as e:
    SUPABASE_ENABLED = False
    print(f"[warning] Supabase not available ({e}) — dry-run mode forced")

DB_EXCLUDE = {"ayanamsa", "ayanamsa_value"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def date_range(start: datetime.date, end: datetime.date):
    """Yield every date from start to end inclusive."""
    d = start
    while d <= end:
        yield d
        d += datetime.timedelta(days=1)


def _existing_dates(location: str) -> set[str]:
    """Fetch all dates already stored in Supabase for this location."""
    if not SUPABASE_ENABLED:
        return set()
    try:
        sb = get_supabase()
        rows = (
            sb.table("panchangam_daily")
            .select("date")
            .eq("location_name", location)
            .execute()
        )
        return {row["date"] for row in (rows.data or [])}
    except Exception as e:
        print(f"  [warning] Could not fetch existing dates: {e}")
        return set()


def process_one(date_str: str, location: str, dry_run: bool) -> dict:
    """Compute panchangam for one date+location; upsert to Supabase."""
    import io, contextlib
    try:
        # Suppress any internal print() calls from the engine
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = calculate_panchangam(date_str, location)

        if not dry_run and SUPABASE_ENABLED:
            db_row = {k: v for k, v in result.items() if k not in DB_EXCLUDE}
            sb = get_supabase()
            sb.table("panchangam_daily").upsert(db_row).execute()

        return {"date": date_str, "location": location, "status": "ok"}
    except Exception as e:
        return {"date": date_str, "location": location, "status": "error", "error": str(e)}


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bulk preload Panchangam into Supabase")
    parser.add_argument("--year",     type=int, default=None,
                        help="Year to preload (default: current year)")
    parser.add_argument("--start",    type=str, default=None,
                        help="Start date YYYY-MM-DD")
    parser.add_argument("--end",      type=str, default=None,
                        help="End date YYYY-MM-DD")
    parser.add_argument("--location", type=str, default=None,
                        help=f"Location name. Available: {', '.join(LOCATIONS.keys())}")
    parser.add_argument("--workers",  type=int, default=4,
                        help="Parallel worker threads (default: 4)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Compute only, do not write to Supabase")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip dates already stored in Supabase")
    parser.add_argument("--sql", type=str, default=None, metavar="FILE",
                        help="Write SQL INSERT file (run in Supabase SQL Editor)")
    args = parser.parse_args()

    # ── Date range ──────────────────────────────────────────────────────────
    if args.start and args.end:
        start_date = datetime.date.fromisoformat(args.start)
        end_date   = datetime.date.fromisoformat(args.end)
    else:
        year = args.year or datetime.date.today().year
        start_date = datetime.date(year, 1, 1)
        end_date   = datetime.date(year, 12, 31)

    total_days = (end_date - start_date).days + 1

    # ── Locations ───────────────────────────────────────────────────────────
    if args.location:
        if args.location not in LOCATIONS:
            print(f"[error] Unknown location '{args.location}'.")
            print(f"  Available: {', '.join(LOCATIONS.keys())}")
            sys.exit(1)
        locations = [args.location]
    else:
        locations = list(LOCATIONS.keys())

    total_jobs = total_days * len(locations)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║           JYOTISH AI — Panchangam Preloader              ║
╚══════════════════════════════════════════════════════════╝
  Date range : {start_date} → {end_date} ({total_days} days)
  Locations  : {', '.join(locations)}
  Total jobs : {total_jobs}
  Workers    : {args.workers}
  Dry run    : {'YES — no DB writes' if args.dry_run else 'NO — writing to Supabase'}
  Skip exist : {args.skip_existing}
""")

    if not SUPABASE_ENABLED and not args.dry_run:
        print("[warning] Supabase not configured — running as dry-run")
        args.dry_run = True

    # ── Build work queue ────────────────────────────────────────────────────
    jobs = []
    for loc in locations:
        existing = _existing_dates(loc) if args.skip_existing else set()
        if existing:
            print(f"  {loc}: {len(existing)} dates already in DB — skipping those")
        for d in date_range(start_date, end_date):
            date_str = d.isoformat()
            if date_str not in existing:
                jobs.append((date_str, loc))

    print(f"  Jobs to run: {len(jobs)} (skipped {total_jobs - len(jobs)})\n")

    if not jobs:
        print("Nothing to do — all dates already stored.")
        return

    # ── SQL file mode ────────────────────────────────────────────────────────
    if args.sql:
        import io, contextlib, json as _json

        sql_path = Path(args.sql)
        print(f"  Generating SQL → {sql_path} ...")
        t_start = time.time()
        ok = errors = 0

        # Columns in panchangam_daily (matching DB schema; exclude computed fields)
        def _escape(v):
            if v is None:
                return "NULL"
            if isinstance(v, bool):
                return "TRUE" if v else "FALSE"
            if isinstance(v, (int, float)):
                return str(v)
            # string — escape single quotes
            return "'" + str(v).replace("'", "''") + "'"

        with open(sql_path, "w") as fout:
            fout.write("-- Jyotish AI — Panchangam bulk insert\n")
            fout.write("-- Generated by preload_panchangam.py\n")
            fout.write(f"-- Range: {start_date} → {end_date}  Locations: {', '.join(locations)}\n\n")
            fout.write("INSERT INTO panchangam_daily (\n")
            # Write header on first row; we'll collect column names from first result
            sample_cols = None

            rows_buf = []
            for date_str, loc in jobs:
                try:
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        result = calculate_panchangam(date_str, loc)
                    db_row = {k: v for k, v in result.items() if k not in DB_EXCLUDE}
                    if sample_cols is None:
                        sample_cols = list(db_row.keys())
                        fout.seek(0)
                        fout.write("-- Jyotish AI — Panchangam bulk insert\n")
                        fout.write("-- Generated by preload_panchangam.py\n")
                        fout.write(f"-- Range: {start_date} → {end_date}  Locations: {', '.join(locations)}\n\n")
                        fout.write("INSERT INTO panchangam_daily (\n  ")
                        fout.write(",\n  ".join(sample_cols))
                        fout.write("\n) VALUES\n")
                    vals = ", ".join(_escape(db_row.get(c)) for c in sample_cols)
                    rows_buf.append(f"  ({vals})")
                    ok += 1
                except Exception as e:
                    errors += 1
                    fout.write(f"-- ERROR {date_str}/{loc}: {e}\n")

            fout.write(",\n".join(rows_buf))
            fout.write("\nON CONFLICT (date, location_name) DO UPDATE SET\n")
            if sample_cols:
                update_cols = [c for c in sample_cols if c not in ("date", "location_name")]
                fout.write(",\n".join(f"  {c} = EXCLUDED.{c}" for c in update_cols))
            fout.write(";\n")

        elapsed = time.time() - t_start
        size_kb = sql_path.stat().st_size // 1024
        print(f"""
SQL file written: {sql_path}  ({size_kb} KB)
  ✓ Rows : {ok}
  ✗ Errors: {errors}
  Time  : {elapsed:.1f}s

Next step — paste into Supabase SQL Editor and run:
  https://supabase.com/dashboard/project/_/sql
""")
        return

    # ── Direct Supabase mode ─────────────────────────────────────────────────
    # ── Execute ─────────────────────────────────────────────────────────────
    t_start  = time.time()
    ok = errors = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(process_one, date_str, loc, args.dry_run): (date_str, loc)
            for date_str, loc in jobs
        }

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result["status"] == "ok":
                ok += 1
            else:
                errors += 1
                print(f"  [error] {result['date']} / {result['location']}: {result.get('error')}")

    elapsed = time.time() - t_start
    print(f"""
Done in {elapsed:.1f}s
  ✓ Success : {ok}
  ✗ Errors  : {errors}
  Stored    : {'Supabase panchangam_daily' if not args.dry_run else 'dry-run (nothing stored)'}
""")


if __name__ == "__main__":
    main()
