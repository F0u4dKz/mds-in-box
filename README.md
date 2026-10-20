# mds-in-box

Local [MDS-in-a-box](https://duckdb.org/2022/10/12/modern-data-stack-in-a-box.html) stack for Olist: **dlt → DuckDB → dbt → Streamlit**.

## Quickstart

```bash
make install
make ingest      # data/*.csv → warehouse/raw.duckdb
make transform   # dbt → warehouse/analytics.duckdb
make streamlit   # dashboard on analytics.duckdb
```

## CI (no CD)

PRs and pushes to `main` run [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

1. **sqlfmt** — `sqlfmt --check dbt/models`
2. **dlt** — pytest against tiny CSVs in [`ci/fixtures/`](ci/fixtures/)
3. **dbt** — seed `warehouse/ci_raw.duckdb` from fixtures, then `dbt build --target ci`

Reproduce locally:

```bash
make test-ci
```

### Require checks before merge

In GitHub: **Settings → Rules → Rulesets** (or Branch protection on `main`):

- Require status check **`ci`** (the job name in the workflow)
- Require branch to be up to date before merging

Until that rule is enabled, CI still runs but merge is not blocked.
