"""Quick test to debug data ingestion."""
import sys, traceback
sys.path.insert(0, '.')

from src.db_connector import get_engine, run_sql_file
from src.data_ingestion import full_pipeline
from sqlalchemy import text

print("Step 1: Testing basic query...")
try:
    engine = get_engine(include_db=False)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS ok"))
        print(f"  Basic query OK: {result.fetchone()}")
except Exception as e:
    print(f"  Basic query FAILED: {e}")
    sys.exit(1)

print("\nStep 2: Running full pipeline...")
try:
    full_pipeline()
    print("\n✅ FULL PIPELINE COMPLETE!")
except Exception as e:
    print(f"\n❌ Pipeline failed:")
    traceback.print_exc()
