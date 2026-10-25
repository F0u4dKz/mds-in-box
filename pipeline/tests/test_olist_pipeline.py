"""Integration tests for the Olist dlt pipeline using tiny CI fixtures."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
FIXTURES_DIR = PROJECT_ROOT / "ci" / "fixtures"

sys.path.insert(0, str(PIPELINE_DIR))

from olist_pipeline import OLIST_TABLES, run  # noqa: E402

EXPECTED_TABLES = [table_name for _, table_name in OLIST_TABLES]
REQUIRED_COLUMNS = {
    "olist_customers": {"customer_id", "customer_unique_id"},
    "olist_orders": {"order_id", "customer_id", "order_status"},
    "olist_order_items": {"order_id", "order_item_id", "product_id", "price"},
    "olist_products": {"product_id", "product_category_name"},
    "product_category_name_translation": {
        "product_category_name",
        "product_category_name_english",
    },
}


@pytest.fixture()
def ci_raw_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    raw_path = tmp_path / "ci_raw.duckdb"
    monkeypatch.setenv("DATA_DIR", str(FIXTURES_DIR))
    monkeypatch.setenv("DUCKDB_PATH", str(raw_path))
    monkeypatch.setenv("DLT_TELEMETRY_DISABLED", "1")
    monkeypatch.chdir(tmp_path)
    return raw_path


def _table_columns(con: duckdb.DuckDBPyConnection, table: str) -> set[str]:
    rows = con.execute(f"describe olist.{table}").fetchall()
    return {row[0] for row in rows}


def _table_count(con: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(con.execute(f"select count(*) from olist.{table}").fetchone()[0])


def test_pipeline_loads_fixture_tables(ci_raw_path: Path) -> None:
    run()

    assert ci_raw_path.exists()
    con = duckdb.connect(str(ci_raw_path), read_only=True)
    try:
        tables = {
            row[0]
            for row in con.execute(
                "select table_name from information_schema.tables "
                "where table_schema = 'olist'"
            ).fetchall()
        }
        for table in EXPECTED_TABLES:
            assert table in tables, f"missing table olist.{table}"
            assert _table_count(con, table) >= 1, f"olist.{table} is empty"

        for table, columns in REQUIRED_COLUMNS.items():
            present = _table_columns(con, table)
            missing = columns - present
            assert not missing, f"olist.{table} missing columns: {sorted(missing)}"
    finally:
        con.close()


def test_pipeline_replace_is_idempotent(ci_raw_path: Path) -> None:
    run()
    con = duckdb.connect(str(ci_raw_path), read_only=True)
    try:
        first_counts = {table: _table_count(con, table) for table in EXPECTED_TABLES}
    finally:
        con.close()

    run()
    con = duckdb.connect(str(ci_raw_path), read_only=True)
    try:
        second_counts = {table: _table_count(con, table) for table in EXPECTED_TABLES}
    finally:
        con.close()

    assert first_counts == second_counts
