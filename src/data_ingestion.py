"""
CRIS — Data Ingestion
Loads raw CSVs into the SQL Server database.
Runs schema creation first, then bulk-inserts data.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db_connector import get_engine, run_sql_file, get_connection_string

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
SQL_DIR = PROJECT_ROOT / "sql"


def create_schema():
    """Run schema creation SQL (creates DB + tables)."""
    print("═" * 50)
    print("Step 1: Creating database schema...")
    print("═" * 50)
    messages = run_sql_file(str(SQL_DIR / "schema_creation.sql"), include_db=False)
    for msg in messages:
        print(f"  {msg}")
    print()


def load_csv_to_table(csv_name: str, table_name: str):
    """Load a CSV file into a SQL Server table."""
    csv_path = DATA_DIR / csv_name
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"  Loading {csv_name} → {table_name} ({len(df)} rows)...")

    engine = get_engine()
    # Use fast_executemany for bulk insert performance
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        chunksize=200,
    )
    print(f"  ✅ {table_name}: {len(df)} rows loaded.")
    return len(df)


def ingest_all():
    """Full ingestion pipeline."""
    # 1. Create schema
    create_schema()

    # 2. Load data (order matters for FK constraints)
    print("═" * 50)
    print("Step 2: Ingesting CSV data...")
    print("═" * 50)

    tables = [
        ("customers.csv", "customers"),
        ("orders.csv", "orders"),
        ("order_items.csv", "order_items"),
    ]

    total_rows = 0
    for csv_name, table_name in tables:
        total_rows += load_csv_to_table(csv_name, table_name)

    print()
    print(f"✅ Ingestion complete. Total rows loaded: {total_rows}")
    return total_rows


def run_target_engineering():
    """Execute target engineering SQL to create churn labels."""
    print()
    print("═" * 50)
    print("Step 3: Running target engineering...")
    print("═" * 50)
    messages = run_sql_file(str(SQL_DIR / "target_engineering.sql"))
    for msg in messages:
        print(f"  {msg}")


def run_feature_engineering():
    """Execute feature engineering SQL to create the feature view."""
    print()
    print("═" * 50)
    print("Step 4: Running feature engineering...")
    print("═" * 50)
    messages = run_sql_file(str(SQL_DIR / "feature_eng.sql"))
    for msg in messages:
        print(f"  {msg}")


def full_pipeline():
    """Run the complete data pipeline."""
    ingest_all()
    run_target_engineering()
    run_feature_engineering()
    print()
    print("🚀 Full data pipeline complete!")


if __name__ == "__main__":
    full_pipeline()
