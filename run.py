"""One cross-platform entry point (works on Windows without make).

    python run.py all      # load + dbt build
    python run.py data     # regenerate sample data
    python run.py load     # Python loaders -> DuckDB raw schema
    python run.py dbt      # dbt build (seeds, models, tests)
    python run.py test     # dbt test only
    python run.py clean    # remove the DuckDB file and dbt artifacts
    python run.py powerbi  # export dashboard tables to powerbi/data/*.csv
    python run.py publish  # load -> copy raw tables to BigQuery -> dbt build on BigQuery
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DBT_DIR = ROOT / "dbt"
DB_PATH = ROOT / "warehouse" / "kestrel.duckdb"


def run(cmd, cwd=ROOT):
    env = {**os.environ, "KESTREL_DUCKDB_PATH": str(DB_PATH)}
    print("$", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def dbt(*args):
    exe = shutil.which("dbt")
    cmd = [exe] if exe else [sys.executable, "-m", "dbt.cli.main"]
    run([*cmd, *args, "--profiles-dir", str(DBT_DIR), "--project-dir", str(DBT_DIR)], cwd=DBT_DIR)


def main(step: str) -> None:
    if step == "data":
        run([sys.executable, "scripts/generate_sample_data.py"])
    elif step == "load":
        run([sys.executable, "-m", "ingestion.load_all", "--db", str(DB_PATH)])
    elif step == "dbt":
        dbt("build")
    elif step == "test":
        dbt("test")
    elif step == "powerbi":
        run([sys.executable, "scripts/export_powerbi.py"])
    elif step == "publish":
        main("load")
        run([sys.executable, "-m", "ingestion.publish_bigquery", "--db", str(DB_PATH)])
        dbt("build", "--target", "bq")
    elif step == "all":
        main("load")
        main("dbt")
    elif step == "clean":
        for p in [DB_PATH, DB_PATH.with_suffix(".duckdb.wal")]:
            p.unlink(missing_ok=True)
        for d in ["target", "logs", "dbt_packages"]:
            shutil.rmtree(DBT_DIR / d, ignore_errors=True)
        print("Cleaned.")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
