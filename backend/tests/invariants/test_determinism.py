"""
Determinism Test Suite - Phase 2A.1
====================================

Tests to verify ledger integrity and deterministic behavior.

Run with: python -m pytest tests/test_determinism.py -v
"""

import sqlite3

import pytest

from repositories.statement_repository import StatementRepository
from repositories.transaction_repository import TransactionRepository
from src.engines.balance_engine import compute_running_balance


@pytest.fixture
def determinism_db(temp_db: str) -> str:
    """Provide a schema-initialized database for determinism tests."""
    return temp_db


def _populate_test_data(db_path: str) -> None:
    """Populate test database with sample transactions."""
    stmt_repo = StatementRepository(db_path)
    txn_repo = TransactionRepository(db_path)

    stmt_id = stmt_repo.insert_statement(
        bank="TestBank",
        file_name="test_statement.pdf",
        period_from="01/01/2025",
        period_to="31/01/2025",
    )

    transactions = [
        {
            "date": "15/01/2025",
            "description": "Transaction C",
            "amount": 100,
            "type": "debit",
        },
        {
            "date": "10/01/2025",
            "description": "Transaction A",
            "amount": 200,
            "type": "debit",
        },
        {
            "date": "12/01/2025",
            "description": "Transaction B",
            "amount": 50,
            "type": "credit",
        },
        {
            "date": "10/01/2025",
            "description": "Transaction A2",
            "amount": 75,
            "type": "debit",
        },
    ]

    txn_repo.insert_transactions(stmt_id, transactions)


def test_replay_stability(determinism_db: str) -> None:
    """Test that running balance computation produces identical results when run multiple times."""
    _populate_test_data(determinism_db)

    result1 = compute_running_balance(determinism_db, "TestBank")
    result2 = compute_running_balance(determinism_db, "TestBank")

    assert len(result1) == len(result2), "Result counts differ"

    for r1, r2 in zip(result1, result2, strict=False):
        assert r1["transaction_id"] == r2["transaction_id"], "Transaction IDs differ"
        assert (
            r1["balance_paise"] == r2["balance_paise"]
        ), f"Balances differ: {r1['balance_paise']} vs {r2['balance_paise']}"

    print("PASS: Replay produces identical results")
    print(f"   Transactions: {len(result1)}")
    print(f"   Final balance: {result1[-1]['balance_paise'] / 100:.2f}")


def test_insert_order_independence(determinism_db: str) -> None:
    """Test that transactions inserted out of chronological order are still replayed in correct date order."""
    stmt_repo = StatementRepository(determinism_db)
    txn_repo = TransactionRepository(determinism_db)

    stmt_id = stmt_repo.insert_statement(
        bank="OrderTest",
        file_name="order_test.pdf",
    )

    transactions = [
        {"date": "30/01/2025", "description": "Last", "amount": 100, "type": "debit"},
        {"date": "20/01/2025", "description": "Middle", "amount": 200, "type": "debit"},
        {"date": "10/01/2025", "description": "First", "amount": 300, "type": "debit"},
    ]

    txn_repo.insert_transactions(stmt_id, transactions)

    result = compute_running_balance(determinism_db, "OrderTest")

    dates = [r["date_iso"] for r in result]
    assert dates == sorted(dates), f"Dates not in order: {dates}"

    descriptions = [r["description"] for r in result]
    assert descriptions == ["First", "Middle", "Last"], f"Wrong order: {descriptions}"

    print("PASS: Transactions replayed in correct date order")
    print(f"   Order: {' -> '.join(descriptions)}")


def test_duplicate_prevention(determinism_db: str) -> None:
    """Test that duplicate transactions are rejected."""
    stmt_repo = StatementRepository(determinism_db)
    txn_repo = TransactionRepository(determinism_db)

    stmt_id = stmt_repo.insert_statement(
        bank="DupTest",
        file_name="dup_test.pdf",
    )

    txn = {
        "date": "15/01/2025",
        "description": "Duplicate Test",
        "amount": 100,
        "type": "debit",
    }

    count1 = txn_repo.insert_transactions(stmt_id, [txn])
    assert count1 == 1, f"First insert should succeed: {count1}"

    count2 = txn_repo.insert_transactions(stmt_id, [txn])
    assert count2 == 0, f"Second insert should be rejected: {count2}"

    conn = sqlite3.connect(determinism_db)
    cur = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE statement_id = ?", (stmt_id,)
    )
    count = cur.fetchone()[0]
    conn.close()

    assert count == 1, f"Should have exactly 1 transaction: {count}"

    print("PASS: Duplicate transactions rejected")
    print(f"   First insert: {count1} row")
    print(f"   Second insert: {count2} rows (blocked)")


def test_update_prevention(determinism_db: str) -> None:
    """Test that UPDATE on transactions is blocked by trigger."""
    _populate_test_data(determinism_db)

    conn = sqlite3.connect(determinism_db)

    blocked = False
    error_msg = ""
    try:
        conn.execute("UPDATE transactions SET amount_paise = 999 WHERE id = 1")
        conn.commit()
    except Exception as e:
        blocked = True
        error_msg = str(e).lower()

    conn.close()

    if blocked and ("immutable" in error_msg or "cannot" in error_msg):
        print("PASS: UPDATE blocked by trigger")
        print(f"   Trigger message: {error_msg}")
    elif blocked:
        raise AssertionError(f"Unexpected error: {error_msg}")
    else:
        raise AssertionError("UPDATE should have been blocked by trigger")


def test_delete_prevention(determinism_db: str) -> None:
    """Test that DELETE on transactions is blocked by trigger."""
    _populate_test_data(determinism_db)

    conn = sqlite3.connect(determinism_db)

    blocked = False
    error_msg = ""
    try:
        conn.execute("DELETE FROM transactions WHERE id = 1")
        conn.commit()
    except Exception as e:
        blocked = True
        error_msg = str(e).lower()

    conn.close()

    if blocked and ("immutable" in error_msg or "cannot" in error_msg):
        print("PASS: DELETE blocked by trigger")
        print(f"   Trigger message: {error_msg}")
    elif blocked:
        raise AssertionError(f"Unexpected error: {error_msg}")
    else:
        raise AssertionError("DELETE should have been blocked by trigger")


def test_date_iso_migration(determinism_db: str) -> None:
    """Test that dates are correctly migrated to ISO format."""
    stmt_repo = StatementRepository(determinism_db)
    txn_repo = TransactionRepository(determinism_db)

    stmt_id = stmt_repo.insert_statement(
        bank="DateTest",
        file_name="date_test.pdf",
    )

    transactions = [
        {
            "date": "15/01/2025",
            "description": "DD/MM/YYYY",
            "amount": 100,
            "type": "debit",
        },
        {
            "date": "15-01-2025",
            "description": "DD-MM-YYYY",
            "amount": 200,
            "type": "debit",
        },
        {
            "date": "15 Jan 2025",
            "description": "DD Mon YYYY",
            "amount": 300,
            "type": "debit",
        },
    ]

    txn_repo.insert_transactions(stmt_id, transactions)

    conn = sqlite3.connect(determinism_db)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT date, date_iso, description FROM transactions WHERE statement_id = ?",
        (stmt_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    for row in rows:
        assert (
            row["date_iso"] == "2025-01-15"
        ), f"Wrong ISO date for {row['description']}: {row['date_iso']}"

    print("PASS: All dates correctly converted to ISO format")
    for row in rows:
        print(f"   {row['date']} -> {row['date_iso']} ({row['description']})")


def test_account_scoped_determinism(determinism_db: str) -> None:
    """Test that account_id is populated and balance engine queries work correctly."""
    stmt_repo = StatementRepository(determinism_db)
    txn_repo = TransactionRepository(determinism_db)

    stmt_id1 = stmt_repo.insert_statement(
        bank="AccountA",
        file_name="statement1.pdf",
    )
    stmt_id2 = stmt_repo.insert_statement(
        bank="AccountA",
        file_name="statement2.pdf",
    )
    stmt_id3 = stmt_repo.insert_statement(
        bank="AccountB",
        file_name="statement3.pdf",
    )

    txns1 = [
        {"date": "10/01/2025", "description": "A-Txn1", "amount": 100, "type": "debit"},
        {
            "date": "15/01/2025",
            "description": "A-Txn2",
            "amount": 200,
            "type": "credit",
        },
    ]
    txns2 = [
        {"date": "20/01/2025", "description": "A-Txn3", "amount": 50, "type": "debit"},
    ]
    txns3 = [
        {"date": "12/01/2025", "description": "B-Txn1", "amount": 300, "type": "debit"},
    ]

    txn_repo.insert_transactions(stmt_id1, txns1)
    txn_repo.insert_transactions(stmt_id2, txns2)
    txn_repo.insert_transactions(stmt_id3, txns3)

    conn = sqlite3.connect(determinism_db)
    conn.row_factory = sqlite3.Row

    cur = conn.execute("SELECT id, account_id, description FROM transactions")
    rows = [dict(r) for r in cur.fetchall()]

    for row in rows:
        assert (
            row["account_id"] is not None and row["account_id"] != ""
        ), f"Missing account_id for {row['description']}"

    cur = conn.execute("""
        SELECT t.id, t.account_id, s.bank
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
    """)
    for row in cur.fetchall():
        assert (
            row["account_id"] == row["bank"]
        ), f"account_id mismatch: {row['account_id']} != {row['bank']}"

    result_a = compute_running_balance(determinism_db, "AccountA")
    descriptions_a = [r["description"] for r in result_a]

    assert (
        len(result_a) == 3
    ), f"Expected 3 transactions for AccountA, got {len(result_a)}"
    assert (
        "B-Txn1" not in descriptions_a
    ), "AccountB transaction leaked into AccountA results"

    result_b = compute_running_balance(determinism_db, "AccountB")
    assert (
        len(result_b) == 1
    ), f"Expected 1 transaction for AccountB, got {len(result_b)}"
    assert result_b[0]["description"] == "B-Txn1"

    cur = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_account_date_iso'"
    )
    index_sql = cur.fetchone()
    if index_sql:
        assert "account_id" in index_sql[0], f"Index not account-scoped: {index_sql[0]}"

    conn.close()

    print("PASS: Account-scoped determinism verified")
    print(f"   AccountA: {len(result_a)} transactions")
    print(f"   AccountB: {len(result_b)} transactions")
    print("   All account_ids populated correctly")


def test_hash_signature_uniqueness(determinism_db: str) -> None:
    """Test that hash signatures are computed and unique."""
    _populate_test_data(determinism_db)

    conn = sqlite3.connect(determinism_db)
    conn.row_factory = sqlite3.Row

    cur = conn.execute(
        "SELECT id, hash_signature FROM transactions WHERE hash_signature IS NOT NULL"
    )
    rows = cur.fetchall()

    assert len(rows) > 0, "No hash signatures found"

    hashes = [r["hash_signature"] for r in rows]
    unique_hashes = set(hashes)

    assert len(hashes) == len(
        unique_hashes
    ), f"Duplicate hashes found: {len(hashes)} total, {len(unique_hashes)} unique"

    print("PASS: All hash signatures are unique")
    print(f"   Total transactions: {len(rows)}")
    print(f"   Unique hashes: {len(unique_hashes)}")

    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
