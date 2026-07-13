"""
Test Suite: Reconciliation Audit Repository
=============================================
Tests for ReconciliationAuditRepository: insert + retrieval round-trip,
and FK constraint enforcement.

Run: python -m pytest tests/test_audit_repository.py -v
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repositories.reconciliation_audit_repository import ReconciliationAuditRepository


@pytest.fixture
def db_with_reconciliation():
    """Create a temp DB with a reconciliations table and one record."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Create minimal transactions table (for FK reference)
    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER,
            date TEXT,
            date_iso TEXT,
            description TEXT,
            amount_paise INTEGER,
            type TEXT,
            account_id TEXT
        )
    """)

    # Insert a transaction so our reconciliation FK works
    conn.execute("""
        INSERT INTO transactions (id, statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES (1, 1, '01/01/2025', '2025-01-01', 'Test', 100000, 'debit', 'A')
    """)

    # Create reconciliations table
    conn.execute("""
        CREATE TABLE reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debit_txn_id INTEGER NOT NULL,
            credit_txn_id INTEGER NOT NULL,
            debit_account_id TEXT,
            credit_account_id TEXT,
            amount_paise INTEGER,
            date_diff_days INTEGER DEFAULT 0,
            match_confidence REAL DEFAULT 0.0,
            match_type TEXT DEFAULT 'exact',
            status TEXT DEFAULT 'pending',
            deterministic_key TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            confirmed_at TEXT
        )
    """)

    # Insert a reconciliation record
    conn.execute("""
        INSERT INTO reconciliations (id, debit_txn_id, credit_txn_id, debit_account_id, credit_account_id,
                                      amount_paise, date_diff_days, match_confidence, match_type)
        VALUES (1, 1, 1, 'A', 'B', 100000, 0, 0.9, 'exact')
    """)

    # Create the audit log table (as migration would)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reconciliation_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            reason TEXT,
            previous_state TEXT,
            new_state TEXT,
            FOREIGN KEY (reconciliation_id) REFERENCES reconciliations(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_reconciliation_id
        ON reconciliation_audit_log(reconciliation_id)
    """)

    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def audit_repo(db_with_reconciliation):
    """Create an audit repository connected to the temp DB."""
    return ReconciliationAuditRepository(db_with_reconciliation)


# ============================================================
# Tests
# ============================================================

def test_insert_audit_log(audit_repo, db_with_reconciliation):
    """Test inserting an audit log entry returns a valid ID."""
    log_id = audit_repo.insert_audit_log(
        reconciliation_id=1,
        action="confirm",
        actor="test_user",
        reason="Manual confirmation",
        previous_state='{"status": "pending"}',
        new_state='{"status": "confirmed"}',
    )

    assert log_id is not None, "insert_audit_log should return a log ID"
    assert isinstance(log_id, int), "log ID should be an integer"
    assert log_id > 0, "log ID should be positive"


def test_get_audit_trail_single(audit_repo, db_with_reconciliation):
    """Test retrieving an audit trail with one entry."""
    audit_repo.insert_audit_log(
        reconciliation_id=1,
        action="confirm",
        actor="user1",
    )

    trail = audit_repo.get_audit_trail(reconciliation_id=1)
    assert len(trail) == 1
    assert trail[0]["action"] == "confirm"
    assert trail[0]["actor"] == "user1"
    assert trail[0]["reconciliation_id"] == 1


def test_get_audit_trail_multiple(audit_repo, db_with_reconciliation):
    """Test retrieving an audit trail with multiple entries in order."""
    actions = [
        ("confirm", "user1", "initial confirmation"),
        ("modify", "user2", "adjusted amount"),
        ("reject", "user1", "manual override"),
    ]

    for action, actor, reason in actions:
        audit_repo.insert_audit_log(
            reconciliation_id=1,
            action=action,
            actor=actor,
            reason=reason,
        )

    trail = audit_repo.get_audit_trail(reconciliation_id=1)
    assert len(trail) == 3

    # Verify order (oldest first)
    assert trail[0]["action"] == "confirm"
    assert trail[1]["action"] == "modify"
    assert trail[2]["action"] == "reject"


def test_get_audit_trail_empty(audit_repo, db_with_reconciliation):
    """Test retrieving an audit trail when no entries exist."""
    trail = audit_repo.get_audit_trail(reconciliation_id=999)
    assert trail == [], "Should return empty list for non-existent reconciliation"


def test_insert_audit_log_invalid_fk(audit_repo, db_with_reconciliation):
    """Test that inserting with an invalid reconciliation_id fails cleanly.

    This is the negative test — verifies FK constraint enforcement.
    """
    log_id = audit_repo.insert_audit_log(
        reconciliation_id=99999,  # Does not exist
        action="confirm",
        actor="test_user",
    )

    assert log_id is None, (
        "insert_audit_log should return None when FK constraint fails"
    )


def test_insert_audit_log_with_all_fields(audit_repo, db_with_reconciliation):
    """Test inserting an audit log entry with all optional fields."""
    log_id = audit_repo.insert_audit_log(
        reconciliation_id=1,
        action="split",
        actor="system",
        reason="Auto-split detected transfer",
        previous_state='{"status": "pending", "amount_paise": 100000}',
        new_state='{"status": "confirmed", "amount_paise": 50000}',
    )

    assert log_id is not None

    trail = audit_repo.get_audit_trail(reconciliation_id=1)
    entry = trail[0]
    assert entry["action"] == "split"
    assert entry["actor"] == "system"
    assert entry["reason"] == "Auto-split detected transfer"
    assert entry["previous_state"] is not None
    assert entry["new_state"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])