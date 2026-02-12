import os
from sqlalchemy import create_engine, text
from pathlib import Path

DB_PATH = Path(r"d:\VNIT\Projects\CRIS\data\cris.db")
print(f"Path exists: {DB_PATH.exists()}")

# Try different connection strings
strings = [
    f"sqlite:///{DB_PATH}",
    f"sqlite:///{DB_PATH.as_posix()}",
    f"sqlite:////{DB_PATH.as_posix()}",
    r"sqlite:///d:\VNIT\Projects\CRIS\data\cris.db"
]

for s in strings:
    print(f"\nTesting: {s}")
    try:
        engine = create_engine(s, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).fetchone()
            print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Failed: {e}")
