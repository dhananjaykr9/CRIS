import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(r"d:\VNIT\Projects\CRIS\data\cris.db")

try:
    with sqlite3.connect(DB_PATH) as conn:
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        results = []
        results.append(f"Tables: {tables['name'].tolist()}")
        
        for table in tables['name']:
            df = pd.read_sql(f"SELECT * FROM {table} LIMIT 5", conn)
            results.append(f"\nTable: {table}")
            results.append(f"Columns: {df.columns.tolist()}")
            
    with open("db_inspection_utf8.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
        
except Exception as e:
    with open("db_inspection_utf8.txt", "w", encoding="utf-8") as f:
        f.write(str(e))
