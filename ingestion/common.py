"""Shared helpers for the Kestrel loaders.

Raw-layer rules (same for every source):
- Values are landed as text, exactly as handed over. No trimming, no type
  casting, no de-duplication: cleaning happens in dbt staging, where it is
  tested and visible.
- Column names are converted to snake_case ("Week Ending" -> week_ending) so
  they are valid in both DuckDB and BigQuery.
- Three metadata columns are added: _source_file, _row_number (1-based
  position in the source file/sheet) and _loaded_at (UTC).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw"
DEFAULT_DB = REPO_ROOT / "warehouse" / "kestrel.duckdb"
RAW_SCHEMA = "raw"


def snake_case(name: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip())
    return name.strip("_").lower()


def to_text(value):
    """Convert a cell to text, keeping blanks/None as NULL."""
    if value is None:
        return None
    if not isinstance(value, str) and pd.isna(value):  # NaN, NaT, pd.NA
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        # Excel dates arrive as datetimes; keep an ISO string (date part only
        # when there is no time component).
        ts = pd.Timestamp(value)
        return ts.strftime("%Y-%m-%d") if ts == ts.normalize() else ts.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value)
    return None if text == "" else text


def finalise(df: pd.DataFrame, source_file: Path, loaded_at: datetime) -> pd.DataFrame:
    """Snake-case columns, cast to text, add metadata columns."""
    df = df.copy()
    df.columns = [snake_case(c) for c in df.columns]
    for col in df.columns:
        df[col] = df[col].map(to_text).astype(object)
    df["_source_file"] = source_file.relative_to(REPO_ROOT).as_posix()
    df["_row_number"] = range(1, len(df) + 1)
    df["_loaded_at"] = loaded_at
    return df


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def write_table(con, table: str, df: pd.DataFrame) -> int:
    """Replace raw.<table> with the dataframe (full refresh). Returns row count."""
    con.execute(f"create schema if not exists {RAW_SCHEMA}")
    con.register("_incoming", df)
    con.execute(f"create or replace table {RAW_SCHEMA}.{table} as select * from _incoming")
    con.unregister("_incoming")
    return con.execute(f"select count(*) from {RAW_SCHEMA}.{table}").fetchone()[0]
