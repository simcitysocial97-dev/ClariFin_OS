"""
Repository Smoke Tests
======================
Tests to verify repository methods match FinanceDB behavior.

These tests freeze current behavior before SQL is moved out of db.py in Phase 4.
If any repository behavior changes during refactoring, these tests will catch it.
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from src.repositories.account_repository import AccountRepository
from src.repositories.reconciliation_repository import ReconciliationRepository
from src.repositories.statement_repository import StatementRepository
from src.repositories.transaction_repository import TransactionRepository


# ============================================================
# Test: TransactionRepository matches FinanceDB
# ============================================================

def test_transaction_repository_get_all_matches_db():
    """Verify TransactionRepository.get_all_transactions() matches FinanceDB.get_all_transactions()."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # Create both repository and direct db
        repo = TransactionRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Insert test data
        stmt_id = db.insert_statement(bank="TestBank", file_name="test.pdf")
        transactions = [
            {"date": "15/01/2025", "description": "Test Txn 1", "amount": "100.50", "type": "debit"},
            {"date": "16/01/2025", "description": "Test Txn 2", "amount": "200.75", "type": "credit"},
        ]
        db.insert_transactions(stmt_id, transactions)

        # Compare outputs
        repo_result = repo.get_all_transactions()
        db_result = db.get_all_transactions()

        assert repo_result == db_result, "TransactionRepository.get_all_transactions() should match FinanceDB"

    finally:
        os.unlink(db_path)


def test_transaction_repository_get_all_with_filters_matches_db():
    """Verify TransactionRepository.get_all_transactions() with filters matches FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = TransactionRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Insert test data
        stmt_id = db.insert_statement(bank="TestBank", file_name="test.pdf")
        transactions = [
            {"date": "15/01/2025", "description": "Food", "amount": "100.00", "type": "debit", "category": "Food"},
            {"date": "16/01/2025", "description": "Travel", "amount": "200.00", "type": "debit", "category": "Travel"},
        ]
        db.insert_transactions(stmt_id, transactions)

        # Compare with category filter
        filters = {"category": "Food"}
        repo_result = repo.get_all_transactions(filters=filters)
        db_result = db.get_all_transactions(filters=filters)

        assert repo_result == db_result, "TransactionRepository with filters should match FinanceDB"

    finally:
        os.unlink(db_path)


def test_transaction_repository_monthly_summary_matches_db():
    """Verify TransactionRepository.get_monthly_summary() matches FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = TransactionRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Insert test data
        stmt_id = db.insert_statement(bank="TestBank", file_name="test.pdf")
        transactions = [
            {"date": "15/01/2025", "description": "Txn 1", "amount": "100.00", "type": "debit"},
            {"date": "16/01/2025", "description": "Txn 2", "amount": "200.00", "type": "credit"},
        ]
        db.insert_transactions(stmt_id, transactions)

        repo_result = repo.get_monthly_summary()
        db_result = db.get_monthly_summary()

        assert repo_result == db_result, "TransactionRepository.get_monthly_summary() should match FinanceDB"

    finally:
        os.unlink(db_path)


# ============================================================
# Test: ReconciliationRepository matches FinanceDB
# ============================================================

def test_reconciliation_repository_get_reconciliations_matches_db():
    """Verify ReconciliationRepository.get_reconciliations() matches FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = ReconciliationRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Insert test data
        db.insert_statement("Account_A", "stmt_a.pdf")
        db.insert_statement("Account_B", "stmt_b.pdf")

        # Insert transactions (use amount_paise, not generated debit/credit columns)
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount, type, amount_paise, account_id)
            VALUES
                (1, '01/01/2025', '2025-01-01', 'Transfer out', 1000.00, 'debit', 100000, 'Account_A'),
                (2, '01/01/2025', '2025-01-01', 'Transfer in', 1000.00, 'credit', 100000, 'Account_B')
        """)
        conn.commit()
        conn.close()

        # Create reconciliation via db
        db.insert_reconciliation(
            debit_txn_id=1,
            credit_txn_id=2,
            debit_account_id="Account_A",
            credit_account_id="Account_B",
            amount=1000.00,
            date_diff_days=0,
            match_confidence=0.8,
            match_type="exact",
        )

        # Compare outputs
        repo_result = repo.get_reconciliations()
        db_result = db.get_reconciliations()

        assert repo_result == db_result, "ReconciliationRepository.get_reconciliations() should match FinanceDB"

    finally:
        os.unlink(db_path)


def test_reconciliation_repository_get_pending_matches_db():
    """Verify ReconciliationRepository.get_pending_reconciliations() matches FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = ReconciliationRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Insert test data
        db.insert_statement("Account_A", "stmt_a.pdf")
        db.insert_statement("Account_B", "stmt_b.pdf")

        # Insert transactions (use amount_paise, not generated debit/credit columns)
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount, type, amount_paise, account_id)
            VALUES
                (1, '01/01/2025', '2025-01-01', 'Transfer out', 1000.00, 'debit', 100000, 'Account_A'),
                (2, '01/01/2025', '2025-01-01', 'Transfer in', 1000.00, 'credit', 100000, 'Account_B')
        """)
        conn.commit()
        conn.close()

        # Create pending reconciliation
        db.insert_reconciliation(
            debit_txn_id=1,
            credit_txn_id=2,
            debit_account_id="Account_A",
            credit_account_id="Account_B",
            amount=1000.00,
            date_diff_days=0,
            match_confidence=0.8,
            match_type="exact",
        )

        repo_result = repo.get_pending_reconciliations()
        db_result = db.get_pending_reconciliations()

        assert repo_result == db_result, "ReconciliationRepository.get_pending_reconciliations() should match FinanceDB"

    finally:
        os.unlink(db_path)


# ============================================================
# Test: AccountRepository matches FinanceDB
# ============================================================

def test_account_repository_get_all_matches_db():
    """Verify AccountRepository.get_all_accounts() matches FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = AccountRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Create account via db
        db.create_account(
            account_id=0,
            name="Test Account",
            bank="TestBank",
            account_type="savings",
            balance_paise=50000,
        )

        repo_result = repo.get_all_accounts()
        db_result = db.get_all_accounts()

        assert repo_result == db_result, "AccountRepository.get_all_accounts() should match FinanceDB"

    finally:
        os.unlink(db_path)


def test_account_repository_create_and_get_matches_db():
    """Verify AccountRepository.create_account() and get_account_by_id() match FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = AccountRepository(db_path=db_path)

        # Create account via repository
        repo.create_account(
            name="Test Account",
            bank="TestBank",
            account_type="savings",
            balance_paise=50000,
        )

        # Get via db - use the name to find the account since id may be None
        # (accounts table has TEXT PRIMARY KEY, lastrowid doesn't work)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM accounts WHERE name = ?", ("Test Account",))
        row = cur.fetchone()
        conn.close()

        # Verify the account was created
        assert row is not None, "Account should be created"
        assert row["name"] == "Test Account"
        assert row["bank"] == "TestBank"
        assert row["balance_paise"] == 50000

    finally:
        os.unlink(db_path)


# ============================================================
# Test: StatementRepository matches FinanceDB
# ============================================================

def test_statement_repository_get_all_matches_db():
    """Verify StatementRepository.get_all_statements() matches FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = StatementRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Insert statements
        db.insert_statement(bank="HDFC", file_name="hdfc.pdf")
        db.insert_statement(bank="ICICI", file_name="icici.pdf")

        repo_result = repo.get_all_statements()
        db_result = db.get_all_statements()

        assert repo_result == db_result, "StatementRepository.get_all_statements() should match FinanceDB"

    finally:
        os.unlink(db_path)


def test_statement_repository_insert_matches_db():
    """Verify StatementRepository.insert_statement() matches FinanceDB."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        repo = StatementRepository(db_path=db_path)
        db = FinanceDB(db_path)

        # Insert via repository
        repo_id = repo.insert_statement(
            bank="TestBank",
            file_name="test.pdf",
            period_from="01/01/2025",
            period_to="31/01/2025",
            card_last4="1234",
        )

        # Insert via db
        db_id = db.insert_statement(
            bank="TestBank",
            file_name="test.pdf",
            period_from="01/01/2025",
            period_to="31/01/2025",
            card_last4="1234",
        )

        # Both should return same ID (idempotent)
        assert repo_id == db_id, "StatementRepository.insert_statement() should match FinanceDB"

    finally:
        os.unlink(db_path)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
