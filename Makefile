.PHONY: venv install ingest transform streamlit sqlfmt sqlfmt-check test-dlt seed-ci-raw test-dbt-ci test-ci

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
DBT := $(VENV)/bin/dbt
SQLFMT := $(VENV)/bin/sqlfmt
PYTEST := $(VENV)/bin/pytest

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install \
		"dlt[duckdb]>=1.0" \
		"dbt-duckdb>=1.8" \
		"streamlit>=1.32" \
		"plotly>=5.20" \
		"pandas>=2.0" \
		"pytest>=8.0" \
		"shandy-sqlfmt[jinjafmt]>=0.21"

ingest: install
	$(PYTHON) pipeline/olist_pipeline.py

transform:
	cd dbt && ../$(DBT) run --profiles-dir .

streamlit:
	cd streamlit && ../.venv/bin/streamlit run app.py

sqlfmt: install
	$(SQLFMT) dbt/models

sqlfmt-check: install
	$(SQLFMT) --check dbt/models

test-dlt: install
	$(PYTEST) pipeline/tests -q

seed-ci-raw: install
	mkdir -p warehouse
	DATA_DIR=ci/fixtures DUCKDB_PATH=warehouse/ci_raw.duckdb $(PYTHON) pipeline/olist_pipeline.py

test-dbt-ci: seed-ci-raw
	cd dbt && ../$(DBT) deps --profiles-dir .
	cd dbt && ../$(DBT) build --profiles-dir . --target ci

test-ci: sqlfmt-check test-dlt test-dbt-ci
