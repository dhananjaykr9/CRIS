"""
CRIS — Database Connector
Manages SQLAlchemy engine and SQL execution utilities.
"""

import os
import pyodbc
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path


# ──────────────────────────────────────────────
# Connection Configuration
# ──────────────────────────────────────────────
DB_TYPE = os.getenv("CRIS_DB_TYPE", "sqlserver")  # Options: sqlserver, sqlite
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = PROJECT_ROOT / "data" / "cris.db"

DB_CONFIG = {
    "server": os.getenv("CRIS_DB_SERVER", "127.0.0.1"),
    "port": os.getenv("CRIS_DB_PORT", "1434"),
    "database": os.getenv("CRIS_DB_NAME", "CRIS"),
    "username": os.getenv("CRIS_DB_USER", "sa"),
    "password": os.getenv("CRIS_DB_PASSWORD", "MyStr0ng!Passw0rd"),
    "driver": os.getenv("CRIS_DB_DRIVER", "ODBC Driver 18 for SQL Server"),
}


def get_connection_string(include_db: bool = True) -> str:
    """Build pyodbc connection string."""
    db_part = f";DATABASE={DB_CONFIG['database']}" if include_db else ""
    return (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']},{DB_CONFIG['port']}"
        f"{db_part};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"TrustServerCertificate=yes;Encrypt=yes"
    )


def get_engine(include_db: bool = True):
    """Create SQLAlchemy engine (SQL Server or SQLite)."""
    if DB_TYPE == "sqlite":
        # SQLite connection
        if not SQLITE_DB_PATH.exists():
            raise FileNotFoundError(f"SQLite DB not found at {SQLITE_DB_PATH}. Run src/export_to_sqlite.py first.")
        # Ensure forward slashes for Windows compatibility
        return create_engine(f"sqlite:///{SQLITE_DB_PATH.as_posix()}", echo=False)
    
    # SQL Server connection
    conn_str = get_connection_string(include_db)
    url = f"mssql+pyodbc:///?odbc_connect={conn_str}"
    print(f"DEBUG: Connection string: {url}")
    return create_engine(url, echo=False)


def run_query(sql: str, params: dict = None) -> pd.DataFrame:
    """Execute a SELECT query and return results as a DataFrame."""
    # Adapt SQL for SQLite if needed
    if DB_TYPE == "sqlite":
        sql = sql.replace("dbo.", "")
        
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


def run_sql_file(filepath: str, include_db: bool = True) -> list[str]:
    """
    Execute a .sql file against the database.
    Splits on 'GO' batch separators (SQL Server convention).
    Returns captured PRINT messages.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {filepath}")

    sql_content = path.read_text(encoding="utf-8")

    # Split by GO (case-insensitive, on its own line)
    import re
    batches = re.split(r"^\s*GO\s*$", sql_content, flags=re.MULTILINE | re.IGNORECASE)

    messages = []
    conn_str = get_connection_string(include_db)

    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()

    for batch in batches:
        batch = batch.strip()
        if not batch:
            continue
        try:
            cursor.execute(batch)
            # Collect PRINT output
            while cursor.messages:
                for msg in cursor.messages:
                    messages.append(str(msg[1]))
                cursor.messages.clear()
                try:
                    cursor.nextset()
                except:
                    break
        except pyodbc.ProgrammingError as e:
            if "No results" not in str(e):
                messages.append(f"[ERROR] {e}")
        except Exception as e:
            messages.append(f"[ERROR] {e}")

    cursor.close()
    conn.close()
    return messages


def test_connection() -> bool:
    """Quick connectivity check."""
    try:
        engine = get_engine(include_db=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS ok"))
            row = result.fetchone()
            return row[0] == 1
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing database connection...")
    if test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed. Is Docker running?")
