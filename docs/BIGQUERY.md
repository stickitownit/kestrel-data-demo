# Publishing to BigQuery

The same dbt models and tests run on DuckDB (local) and BigQuery (cloud). BigQuery is the source for shared dashboards.

## One-time setup

1. Create a Google Cloud project and enable the BigQuery API. Without billing it runs as the BigQuery sandbox: free, but tables expire after about 60 days, so re-publish monthly or enable billing with a budget alert.
2. Install the Google Cloud CLI, then sign in:
   ```
   gcloud auth application-default login
   gcloud auth application-default set-quota-project <your-project-id>
   ```
   Credentials stay on your machine; no key files are stored in the repo.
3. Install the extra packages:
   ```
   pip install -r requirements.txt -r requirements-bigquery.txt
   ```

## Publish

```
python run.py publish
```

This rebuilds the local raw tables, copies them to the BigQuery dataset `raw` (row counts are checked table by table), then runs `dbt build --target bq`. Expected result: all tests pass with the same 4 documented warnings as the local run.

Datasets created: `raw`, `seeds`, `staging`, `intermediate`, `marts`. Dashboards read from `marts` only.

The project ID defaults to `kestrel-demo-512601`; override it with the `KESTREL_GCP_PROJECT` environment variable (and `KESTREL_BQ_LOCATION`, default `US`).
