"""Copy the raw tables from the local DuckDB warehouse to BigQuery.

    python -m ingestion.publish_bigquery [--db PATH] [--project ID] [--location US]

Run `python run.py load` first (or just `python run.py publish`, which does
both and then runs dbt on BigQuery).

How it works: each DuckDB table in the `raw` schema is written to a temporary
Parquet file and loaded into BigQuery dataset `raw` with a full replace
(WRITE_TRUNCATE). Load jobs are allowed in the BigQuery sandbox; DML is not,
which is why nothing here uses INSERT or MERGE.

Sign-in: uses Application Default Credentials. Once per computer, run
    gcloud auth application-default login
No key files are created or stored in the repo.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

import duckdb
from google.cloud import bigquery

from ingestion.common import DEFAULT_DB, RAW_SCHEMA

DEFAULT_PROJECT = os.environ.get("KESTREL_GCP_PROJECT", "kestrel-demo-512601")
DEFAULT_LOCATION = os.environ.get("KESTREL_BQ_LOCATION", "US")

# DuckDB type -> BigQuery type. Raw tables are text plus three metadata columns.
TYPE_MAP = {
    "VARCHAR": "STRING",
    "BIGINT": "INT64",
    "INTEGER": "INT64",
    "HUGEINT": "INT64",
    "DOUBLE": "FLOAT64",
    "BOOLEAN": "BOOL",
    "DATE": "DATE",
    "TIMESTAMP": "TIMESTAMP",
    "TIMESTAMP_NS": "TIMESTAMP",
}


def bq_schema(con, table: str) -> list[bigquery.SchemaField]:
    rows = con.execute(
        "select column_name, data_type from information_schema.columns "
        "where table_schema = ? and table_name = ? order by ordinal_position",
        [RAW_SCHEMA, table],
    ).fetchall()
    return [bigquery.SchemaField(name, TYPE_MAP.get(dtype.upper(), "STRING")) for name, dtype in rows]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--project", default=DEFAULT_PROJECT)
    p.add_argument("--location", default=DEFAULT_LOCATION)
    a = p.parse_args()

    if not Path(a.db).exists():
        sys.exit(f"{a.db} not found. Run `python run.py load` first.")
    con = duckdb.connect(a.db, read_only=True)
    tables = [r[0] for r in con.execute(
        "select table_name from information_schema.tables where table_schema = ? order by 1",
        [RAW_SCHEMA],
    ).fetchall()]
    if not tables:
        sys.exit("No raw tables found. Run `python run.py load` first.")

    client = bigquery.Client(project=a.project, location=a.location)
    dataset = bigquery.Dataset(f"{a.project}.{RAW_SCHEMA}")
    dataset.location = a.location
    client.create_dataset(dataset, exists_ok=True)

    print(f"Publishing {len(tables)} raw tables to {a.project}.{RAW_SCHEMA} ({a.location})")
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        for t in tables:
            local_rows = con.execute(f'select count(*) from {RAW_SCHEMA}."{t}"').fetchone()[0]
            pq = Path(tmp) / f"{t}.parquet"
            con.execute(f"copy {RAW_SCHEMA}.\"{t}\" to '{pq.as_posix()}' (format parquet)")
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.PARQUET,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                schema=bq_schema(con, t),
            )
            with open(pq, "rb") as fh:
                client.load_table_from_file(
                    fh, f"{a.project}.{RAW_SCHEMA}.{t}", job_config=job_config
                ).result()
            bq_rows = client.get_table(f"{a.project}.{RAW_SCHEMA}.{t}").num_rows
            status = "ok" if bq_rows == local_rows else "MISMATCH"
            if status != "ok":
                problems.append(t)
            print(f"  {t:<28} local {local_rows:>8,}  bigquery {bq_rows:>8,}  {status}")

    if problems:
        sys.exit(f"Row counts differ for: {', '.join(problems)}")
    print("Raw layer published. Next: dbt build --target bq")


if __name__ == "__main__":
    main()
