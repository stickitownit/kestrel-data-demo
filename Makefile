# Thin wrapper around run.py (Windows without make: use `python run.py <step>`).
PY ?= python

.PHONY: all data load dbt test clean publish

all:    ## load raw tables, then dbt build (seeds, models, tests)
	$(PY) run.py all
data:   ## regenerate the sample data
	$(PY) run.py data
load:   ## Python loaders -> warehouse/kestrel.duckdb (raw schema)
	$(PY) run.py load
dbt:    ## dbt build: seeds + models + tests
	$(PY) run.py dbt
test:   ## dbt tests only
	$(PY) run.py test
publish: ## copy raw tables to BigQuery and dbt build there (see docs/BIGQUERY.md)
	$(PY) run.py publish
clean:  ## delete the DuckDB file and dbt artifacts
	$(PY) run.py clean
