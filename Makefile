.PHONY: venv install ingest transform streamlit

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install "dlt[duckdb]>=1.0" "dbt-duckdb>=1.8" "streamlit>=1.32" "plotly>=5.20" "pandas>=2.0"

ingest: install
	$(PYTHON) pipeline/olist_pipeline.py

transform:
	cd dbt && ../.venv/bin/dbt run --profiles-dir .

streamlit:
	cd streamlit && ../.venv/bin/streamlit run app.py
