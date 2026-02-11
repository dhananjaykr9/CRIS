"""
CRIS — Export to SQLite
Exports critical tables from local SQL Server to a portable SQLite database
for Streamlit Cloud deployment.
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db_connector import run_query

DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "cris.db"

def export_data():
    print(f"🔄 Exporting data to SQLite: {DB_PATH}")
    
    # 1. Fetch data from SQL Server
    print("  reading from SQL Server...")
    try:
        customers = run_query("SELECT * FROM dbo.customers")
        features = run_query("SELECT * FROM dbo.customer_features")
    except Exception as e:
        print(f"❌ Failed to connect to SQL Server: {e}")
        print("Make sure your Docker container is running!")
        return

    # 2. Write to SQLite
    print(f"  writing {len(customers)} customers and {len(features)} feature rows...")
    
    with sqlite3.connect(DB_PATH) as conn:
        customers.to_sql("customers", conn, if_exists="replace", index=False)
        features.to_sql("customer_features", conn, if_exists="replace", index=False)
        
    print("✅ Export complete! You can now push 'data/cris.db' to GitHub.")

if __name__ == "__main__":
    export_data()
