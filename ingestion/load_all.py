"""Load every source file into the DuckDB raw schema (full refresh).

Usage (from the repo root):
    python -m ingestion.load_all                 # all tables
    python -m ingestion.load_all --only app_visits
    python -m ingestion.load_all --db path/to/other.duckdb
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .common import DEFAULT_DB, now_utc, write_table
from .sources import TABLES


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=f"DuckDB file (default {DEFAULT_DB})")
    parser.add_argument("--only", nargs="+", choices=sorted(TABLES), help="load only these raw tables")
    args = parser.parse_args(argv)

    import duckdb  # imported here so the extract functions work without it

    args.db.parent.mkdir(parents=True, exist_ok=True)
    loaded_at = now_utc()
    names = args.only or list(TABLES)
    print(f"Loading {len(names)} raw tables into {args.db}")
    with duckdb.connect(str(args.db)) as con:
        for name in names:
            start = time.perf_counter()
            df = TABLES[name](loaded_at)
            rows = write_table(con, name, df)
            print(f"  raw.{name:<26} {rows:>8,} rows  ({time.perf_counter() - start:.1f}s)")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
