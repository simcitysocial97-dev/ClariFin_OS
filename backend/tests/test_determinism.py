"""
Determinism Test Suite - Phase 2A.1
===================================

Tests to verify ledger integrity and deterministic behavior.

Run with: python -m pytest tests/test_determinism.py -v

Or directly: python tests/test_determinism.py
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from engines.balance_engine import compute_running_balance
from repositories.statement_repository import StatementRepository
from repositories.transaction_repository import TransactionRepository

# ============================================================
# Test Fixtures
# ============================================================

def create_test_db():
    """Create a temporary test database."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return db_path


def populate_test_data(db_path: str):
    """Populate test database with sample transactions."""
    FinanceDB(db_path)  # Ensure schema exists
    stmt_repo = StatementRepository(db_path)
    txn_repo = TransactionRepository(db_path)

    # Create statement
    stmt_id = stmt_repo.insert_statement(
        bank="TestBank",
        file_name="test_statement.pdf",
        period_from="01/01/2025",
        period_to="31/01/2025",
    )

    # Insert transactions out of chronological order
    # to test ordering
    transactions = [
        {"date": "15/01/2025", "description": "Transaction C", "amount": 100, "type": "debit"},
        {"date": "10/01/2025", "description": "Transaction A", "amount": 200, "type": "debit"},
        {"date": "12/01/2025", "description": "Transaction B", "amount": 50, "type": "credit"},
        {"date": "10/01/2025", "description": "Transaction A2", "amount": 75, "type": "debit"},  # Same date as A
    ]

    txn_repo.insert_transactions(stmt_id, transactions)


# ============================================================
# Test 1: Replay Stability
# ============================================================

def test_replay_stability():
    """
    Test that running balance computation produces identical results
    when run multiple times.
    """
    print("\n" + "=" * 60)
    print("TEST 1: Replay Stability")
    print("=" * 60)

    db_path = create_test_db()
    try:
        populate_test_data(db_path)

        # Run balance computation twice
        result1 = compute_running_balance(db_path, "TestBank")
        result2 = compute_running_balance(db_path, "TestBank")

        # Compare results
        assert len(result1) == len(result2), "Result counts differ"

        for r1, r2 in zip(result1, result2):
            assert r1["transaction_id"] == r2["transaction_id"], "Transaction IDs differ"
            assert r1["balance_paise"] == r2["balance_paise"], f"Balances differ: {r1['balance_paise']} vs {r2['balance_paise']}"

        print("✅ PASS: Replay produces identical results")
        print(f"   Transactions: {len(result1)}")
        print(f"   Final balance: {result1[-1]['balance_paise'] / 100:.2f}")

    finally:
        os.unlink(db_path)


# ============================================================
# Test 2: Insert Order Independence
# ============================================================

def test_insert_order_independence():
    """
    Test that transactions inserted out of chronological order
    are still replayed in correct date order.
    """
    print("\n" + "=" * 60)
    print("TEST 2: Insert Order Independence")
    print("=" * 60)

    db_path = create_test_db()
    try:
        FinanceDB(db_path)  # Ensure schema exists
        stmt_repo = StatementRepository(db_path)
        txn_repo = TransactionRepository(db_path)

        # Create statement
        stmt_id = stmt_repo.insert_statement(
            bank="OrderTest",
            file_name="order_test.pdf",
        )

        # Insert in reverse chronological order
        transactions = [
            {"date": "30/01/2025", "description": "Last", "amount": 100, "type": "debit"},
            {"date": "20/01/2025", "description": "Middle", "amount": 200, "type": "debit"},
            {"date": "10/01/2025", "description": "First", "amount": 300, "type": "debit"},
        ]

        txn_repo.insert_transactions(stmt_id, transactions)

        # Get running balance
        result = compute_running_balance(db_path, "OrderTest")

        # Verify order is chronological (by date_iso)
        dates = [r["date_iso"] for r in result]
        assert dates == sorted(dates), f"Dates not in order: {dates}"

        # Verify descriptions are in chronological order
        descriptions = [r["description"] for r in result]
        assert descriptions == ["First", "Middle", "Last"], f"Wrong order: {descriptions}"

        print("✅ PASS: Transactions replayed in correct date order")
        print(f"   Order: {' -> '.join(descriptions)}")

    finally:
        os.unlink(db_path)


# ============================================================
# Test 3: Duplicate Prevention
# ============================================================

def test_duplicate_prevention():
    """
    Test that duplicate transactions are rejected.
    """
    print("\n" + "=" * 60)
    print("TEST 3: Duplicate Prevention")
    print("=" * 60)

    db_path = create_test_db()
    try:
        FinanceDB(db_path)  # Ensure schema exists
        stmt_repo = StatementRepository(db_path)
        txn_repo = TransactionRepository(db_path)

        # Create statement
        stmt_id = stmt_repo.insert_statement(
            bank="DupTest",
            file_name="dup_test.pdf",
        )

        # Insert transaction
        txn = {"date": "15/01/2025", "description": "Duplicate Test", "amount": 100, "type": "debit"}

        count1 = txn_repo.insert_transactions(stmt_id, [txn])
        assert count1 == 1, f"First insert should succeed: {count1}"

        # Try to insert same transaction again
        count2 = txn_repo.insert_transactions(stmt_id, [txn])
        assert count2 == 0, f"Second insert should be rejected: {count2}"

        # Verify only one transaction exists
        conn = sqlite3.connect(db_path)
        cur = conn.execute("SELECT COUNT(*) FROM transactions WHERE statement_id = ?", (stmt_id,))
        count = cur.fetchone()[0]
        conn.close()

        assert count == 1, f"Should have exactly 1 transaction: {count}"

        print("✅ PASS: Duplicate transactions rejected")
        print(f"   First insert: {count1} row")
        print(f"   Second insert: {count2} rows (blocked)")

    finally:
        os.unlink(db_path)


# ============================================================
# Test 4: Update Prevention
# ============================================================

def test_update_prevention():
    """
    Test that UPDATE on transactions is blocked by trigger.
    """
    print("\n" + "=" * 60)
    print("TEST 4: Update Prevention")
    print("=" * 60)

    db_path = create_test_db()
    try:
        populate_test_data(db_path)

        conn = sqlite3.connect(db_path)

        # Try to update a transaction (use amount_paise since amount column no longer exists)
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
            print("✅ PASS: UPDATE blocked by trigger")
            print(f"   Trigger message: {error_msg}")
        elif blocked:
            print(f"❌ FAIL: Blocked but unexpected error: {error_msg}")
            assert False, f"Unexpected error: {error_msg}"
        else:
            print("❌ FAIL: UPDATE should have been blocked")
            assert False, "UPDATE should have been blocked by trigger"

    finally:
        os.unlink(db_path)


# ============================================================
# Test 5: Delete Prevention
# ============================================================

def test_delete_prevention():
    """
    Test that DELETE on transactions is blocked by trigger.
    """
    print("\n" + "=" * 60)
    print("TEST 5: Delete Prevention")
    print("=" * 60)

    db_path = create_test_db()
    try:
        populate_test_data(db_path)

        conn = sqlite3.connect(db_path)

        # Try to delete a transaction
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
            print("✅ PASS: DELETE blocked by trigger")
            print(f"   Trigger message: {error_msg}")
        elif blocked:
            print(f"❌ FAIL: Blocked but unexpected error: {error_msg}")
            assert False, f"Unexpected error: {error_msg}"
        else:
            print("❌ FAIL: DELETE should have been blocked")
            assert False, "DELETE should have been blocked by trigger"

    finally:
        os.unlink(db_path)


# ============================================================
# Test 6: Date ISO Migration
# ============================================================

def test_date_iso_migration():
    """
    Test that dates are correctly migrated to ISO format.
    """
    print("\n" + "=" * 60)
    print("TEST 6: Date ISO Migration")
    print("=" * 60)

    db_path = create_test_db()
    try:
        FinanceDB(db_path)  # Ensure schema exists
        stmt_repo = StatementRepository(db_path)
        txn_repo = TransactionRepository(db_path)

        # Create statement
        stmt_id = stmt_repo.insert_statement(
            bank="DateTest",
            file_name="date_test.pdf",
        )

        # Insert transactions with various date formats
        transactions = [
            {"date": "15/01/2025", "description": "DD/MM/YYYY", "amount": 100, "type": "debit"},
            {"date": "15-01-2025", "description": "DD-MM-YYYY", "amount": 200, "type": "debit"},
            {"date": "15 Jan 2025", "description": "DD Mon YYYY", "amount": 300, "type": "debit"},
        ]

        txn_repo.insert_transactions(stmt_id, transactions)

        # Check date_iso values
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT date, date_iso, description FROM transactions WHERE statement_id = ?", (stmt_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        for row in rows:
            assert row["date_iso"] == "2025-01-15", f"Wrong ISO date for {row['description']}: {row['date_iso']}"

        print("✅ PASS: All dates correctly converted to ISO format")
        for row in rows:
            print(f"   {row['date']} -> {row['date_iso']} ({row['description']})")

    finally:
        os.unlink(db_path)


# ============================================================
# Test 7: Account-Scoped Determinism (Phase 2A.2)
# ============================================================

def test_account_scoped_determinism():
    """
    Test that account_id is populated and balance engine queries work correctly.
    Phase 2A.2: Verify account-scoped replay determinism.
    """
    print("\n" + "=" * 60)
    print("TEST 7: Account-Scoped Determinism")
    print("=" * 60)

    db_path = create_test_db()
    try:
        FinanceDB(db_path)  # Ensure schema exists
        stmt_repo = StatementRepository(db_path)
        txn_repo = TransactionRepository(db_path)

        # Create two statements for same bank (account)
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

        # Insert transactions across multiple statements for same account
        txns1 = [
            {"date": "10/01/2025", "description": "A-Txn1", "amount": 100, "type": "debit"},
            {"date": "15/01/2025", "description": "A-Txn2", "amount": 200, "type": "credit"},
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

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Verify account_id is populated for all transactions
        cur = conn.execute("SELECT id, account_id, description FROM transactions")
        rows = [dict(r) for r in cur.fetchall()]

        for row in rows:
            assert row["account_id"] is not None and row["account_id"] != "", f"Missing account_id for {row['description']}"

        # Verify account_id matches bank
        cur = conn.execute("""
            SELECT t.id, t.account_id, s.bank 
            FROM transactions t 
            JOIN statements s ON t.statement_id = s.id
        """)
        for row in cur.fetchall():
            assert row["account_id"] == row["bank"], f"account_id mismatch: {row['account_id']} != {row['bank']}"

        # Verify balance engine returns correct transactions for AccountA
        result_a = compute_running_balance(db_path, "AccountA")
        descriptions_a = [r["description"] for r in result_a]

        assert len(result_a) == 3, f"Expected 3 transactions for AccountA, got {len(result_a)}"
        assert "B-Txn1" not in descriptions_a, "AccountB transaction leaked into AccountA results"

        # Verify balance engine returns correct transactions for AccountB
        result_b = compute_running_balance(db_path, "AccountB")
        assert len(result_b) == 1, f"Expected 1 transaction for AccountB, got {len(result_b)}"
        assert result_b[0]["description"] == "B-Txn1"

        # Verify index exists and is account-scoped
        cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_account_date_iso'")
        index_sql = cur.fetchone()
        if index_sql:
            assert "account_id" in index_sql[0], f"Index not account-scoped: {index_sql[0]}"

        conn.close()

        print("✅ PASS: Account-scoped determinism verified")
        print(f"   AccountA: {len(result_a)} transactions")
        print(f"   AccountB: {len(result_b)} transactions")
        print("   All account_ids populated correctly")

    finally:
        os.unlink(db_path)


# ============================================================
# Test 8: Hash Signature Uniqueness
# ============================================================

def test_hash_signature_uniqueness():
    """
    Test that hash signatures are computed and unique.
    """
    print("\n" + "=" * 60)
    print("TEST 7: Hash Signature Uniqueness")
    print("=" * 60)

    db_path = create_test_db()
    try:
        populate_test_data(db_path)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Check all transactions have hash signatures
        cur = conn.execute("SELECT id, hash_signature FROM transactions WHERE hash_signature IS NOT NULL")
        rows = cur.fetchall()

        assert len(rows) > 0, "No hash signatures found"

        # Check uniqueness
        hashes = [r["hash_signature"] for r in rows]
        unique_hashes = set(hashes)

        assert len(hashes) == len(unique_hashes), f"Duplicate hashes found: {len(hashes)} total, {len(unique_hashes)} unique"

        print("✅ PASS: All hash signatures are unique")
        print(f"   Total transactions: {len(rows)}")
        print(f"   Unique hashes: {len(unique_hashes)}")

        conn.close()

    finally:
        os.unlink(db_path)


# ============================================================
# Run All Tests
# ============================================================

def run_all_tests():
    """Run all determinism tests."""
    print("\n" + "=" * 60)
    print("PHASE 2A.1 DETERMINISM TEST SUITE")
    print("=" * 60)

    tests = [
        test_replay_stability,
        test_insert_order_independence,
        test_duplicate_prevention,
        test_update_prevention,
        test_delete_prevention,
        test_date_iso_migration,
        test_account_scoped_determinism,
        test_hash_signature_uniqueness,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✅ ALL TESTS PASSED - Ledger is deterministic and immutable")
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
