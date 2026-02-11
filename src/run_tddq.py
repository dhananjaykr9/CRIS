"""
CRIS — TDDQ Runner
Executes SQL assertion tests and reports PASS/FAIL for each.
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db_connector import run_sql_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "sql" / "tests"


def run_tddq():
    """Execute all TDDQ SQL test files and summarize results."""
    test_files = sorted(TESTS_DIR.glob("test_*.sql"))

    if not test_files:
        print("❌ No test files found in sql/tests/")
        return False

    total_pass = 0
    total_fail = 0
    all_messages = []

    with open("tddq_results.txt", "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("  CRIS - Test-Driven Data Quality (TDDQ) Suite\n")
        f.write("=" * 60 + "\n\n")

        for test_file in test_files:
            f.write(f"Running: {test_file.name}\n")
            f.write("-" * 50 + "\n")

            messages = run_sql_file(str(test_file))
            for msg in messages:
                # Clean up pyodbc message formatting
                clean_msg = msg.strip()
                if "[PASS]" in clean_msg:
                    total_pass += 1
                    f.write(f"  [PASS] {clean_msg}\n")
                elif "[FAIL]" in clean_msg:
                    total_fail += 1
                    f.write(f"  [FAIL] {clean_msg}\n")
                elif "[ERROR]" in clean_msg:
                    total_fail += 1
                    f.write(f"  [ERROR] {clean_msg}\n")
                else:
                    f.write(f"  {clean_msg}\n")

            all_messages.extend(messages)
            f.write("\n")

        # Summary
        f.write("=" * 60 + "\n")
        f.write(f"  SUMMARY: {total_pass} PASSED | {total_fail} FAILED\n")
        f.write("=" * 60 + "\n")

        if total_fail > 0:
            f.write("X TDDQ FAILED - Fix data quality issues before modeling!\n")
            print("TDDQ FAILED. See tddq_results.txt")
            return False
        else:
            f.write("OK ALL TESTS PASSED - Data is clean and ready for modeling.\n")
            print("TDDQ PASSED. See tddq_results.txt")
            return True


if __name__ == "__main__":
    success = run_tddq()
    sys.exit(0 if success else 1)
