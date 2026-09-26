"""Load Olist CSV files from data/ into DuckDB raw schema via dlt."""

import os
from pathlib import Path

import dlt
from dlt.sources.filesystem import filesystem, read_csv_duckdb

# Resolve paths relative to the project root (parent of pipeline/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DUCKDB_PATH = PROJECT_ROOT / "warehouse" / "raw.duckdb"

# Each tuple is (csv filename, destination table name in the raw schema)
OLIST_TABLES: list[tuple[str, str]] = [
    ("product_category_name_translation.csv", "product_category_name_translation"),
    ("olist_products_dataset.csv", "olist_products"),
    ("olist_sellers_dataset.csv", "olist_sellers"),
    ("olist_customers_dataset.csv", "olist_customers"),
    ("olist_orders_dataset.csv", "olist_orders"),
    ("olist_order_items_dataset.csv", "olist_order_items"),
    ("olist_order_payments_dataset.csv", "olist_order_payments"),
    ("olist_order_reviews_dataset.csv", "olist_order_reviews"),
    ("olist_geolocation_dataset.csv", "olist_geolocation"),
]


def _resolve_path(env_var: str, default: Path) -> Path:
    # Allow overriding paths via environment variables for portability
    value = os.getenv(env_var)
    if value:
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path
    return default


@dlt.source(name="olist")
def olist_csv_source(data_dir: str):
    # One resource per CSV: filesystem lists files, read_csv_duckdb parses them
    for file_glob, table_name in OLIST_TABLES:
        resource = (
            filesystem(bucket_url=data_dir, file_glob=file_glob)
            | read_csv_duckdb(header=True)
        ).with_name(table_name)
        # Full refresh on every run — static CSVs, no incremental logic needed
        resource.apply_hints(write_disposition="replace")
        yield resource


def run() -> None:
    data_dir = str(_resolve_path("DATA_DIR", DEFAULT_DATA_DIR))
    duckdb_path = str(_resolve_path("DUCKDB_PATH", DEFAULT_DUCKDB_PATH))

    # Ensure the warehouse directory exists before dlt writes the database file
    Path(duckdb_path).parent.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="olist",
        destination=dlt.destinations.duckdb(duckdb_path),
        # Schema cannot also be named "raw" — DuckDB treats the filename as the catalog
        dataset_name="olist",
    )

    source = olist_csv_source(data_dir)

    # Load one table per run to keep replace loads isolated and row counts correct
    for table_name in source.resources.keys():
        load_info = pipeline.run(source.with_resources(table_name))
        print(f"\n{'─' * 60}")
        print(f"{table_name}: {load_info}")


if __name__ == "__main__":
    run()
