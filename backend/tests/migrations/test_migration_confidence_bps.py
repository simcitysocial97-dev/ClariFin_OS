"""
Test Suite: Migration 007 — confidence_bps backfill correctness
================================================================
Verifies that the confidence_bps backfill logic correctly converts
match_confidence (REAL) to confidence_bps (INTEGER basis points).

Run: python -m pytest tests/test_migration_confidence_bps.py -v
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scripts.migration_007_reconciliation_audit import run_migration


@pytest.fixture
def db_with_confidence_values():
    """Create a temp DB with reconciliations having known match_confidence values."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Create minimal reconciliations table (pre-migration schema)
    conn.execute("""
        CREATE TABLE reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debit_txn_id INTEGER NOT NULL,
            credit_txn_id INTEGER NOT NULL,
            debit_account_id TEXT,
            credit_account_id TEXT,
            amount_paise INTEGER,
            date_diff_days INTEGER DEFAULT 0,
            match_confidence REAL,
            match_type TEXT DEFAULT 'exact',
            status TEXT DEFAULT 'pending',
            deterministic_key TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            confirmed_at TEXT
        )
    """)

    # Insert test rows with known match_confidence values
    test_cases = [
        (1, 1, 2, "A", "B", 10000, 0, 0.9, "exact"),
        (2, 3, 4, "A", "B", 20000, 0, 1.0, "exact"),
        (3, 5, 6, "A", "B", 30000, 1, 0.6, "window"),
        (4, 7, 8, "A", "B", 40000, 2, 0.0, "window"),
        (5, 9, 10, "A", "B", 50000, 0, 0.5, "exact"),
        (6, 11, 12, "A", "B", 60000, 0, 0.1234, "exact"),
        (7, 13, 14, "A", "B", 70000, 0, 0.9999, "exact"),
    ]
    conn.executemany(
        """
        INSERT INTO reconciliations
            (id, debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
             amount_paise, date_diff_days, match_confidence, match_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        test_cases,
    )

    # Insert a row with NULL match_confidence (should be left for manual review)
    conn.execute("""
        INSERT INTO reconciliations
            (id, debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
             amount_paise, date_diff_days, match_confidence, match_type)
        VALUES (8, 15, 16, 'A', 'B', 80000, 0, NULL, 'exact')
        """)

    # Insert a row with out-of-range match_confidence (should be left for manual review)
    conn.execute("""
        INSERT INTO reconciliations
            (id, debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
             amount_paise, date_diff_days, match_confidence, match_type)
        VALUES (9, 17, 18, 'A', 'B', 90000, 0, 1.5, 'exact')
        """)

    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)


# ============================================================
# Tests
# ============================================================


def test_confidence_bps_backfill_correctness(db_with_confidence_values):
    """Verify that confidence_bps = ROUND(match_confidence * 10000) for valid rows."""
    db_path = db_with_confidence_values

    # Run migration
    run_migration(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Check valid rows were backfilled correctly
    expected = {
        1: 9000,  # 0.9 * 10000
        2: 10000,  # 1.0 * 10000
        3: 6000,  # 0.6 * 10000
        4: 0,  # 0.0 * 10000
        5: 5000,  # 0.5 * 10000
        6: 1234,  # 0.1234 * 10000
        7: 9999,  # 0.9999 * 10000
    }

    for rec_id, expected_bps in expected.items():
        row = conn.execute(
            "SELECT confidence_bps FROM reconciliations WHERE id = ?",
            (rec_id,),
        ).fetchone()
        assert row is not None, f"Reconciliation {rec_id} not found"
        assert (
            row["confidence_bps"] == expected_bps
        ), f"id={rec_id}: expected confidence_bps={expected_bps}, got {row['confidence_bps']}"

    conn.close()


def test_null_match_confidence_left_null(db_with_confidence_values):
    """Verify that rows with NULL match_confidence are NOT backfilled."""
    db_path = db_with_confidence_values
    run_migration(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        "SELECT confidence_bps FROM reconciliations WHERE id = 8"
    ).fetchone()
    assert row is not None
    assert (
        row["confidence_bps"] is None
    ), "Row with NULL match_confidence should have NULL confidence_bps"

    conn.close()


def test_out_of_range_confidence_left_null(db_with_confidence_values):
    """Verify that rows with match_confidence outside [0.0, 1.0] are NOT backfilled."""
    db_path = db_with_confidence_values
    run_migration(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        "SELECT confidence_bps FROM reconciliations WHERE id = 9"
    ).fetchone()
    assert row is not None
    assert (
        row["confidence_bps"] is None
    ), "Row with match_confidence=1.5 should have NULL confidence_bps (left for review)"

    conn.close()


def test_migration_idempotent(db_with_confidence_values):
    """Verify that running the migration twice causes no errors or changes."""
    db_path = db_with_confidence_values

    # Run migration twice
    run_migration(db_path)
    run_migration(db_path)  # Second run should be a no-op

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Check that values are still correct after second run
    row = conn.execute(
        "SELECT confidence_bps FROM reconciliations WHERE id = 1"
    ).fetchone()
    assert row["confidence_bps"] == 9000

    # Check that the audit_log table still exists
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='reconciliation_audit_log'"
    ).fetchone()
    assert (
        tables is not None
    ), "reconciliation_audit_log table should exist after second run"

    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
