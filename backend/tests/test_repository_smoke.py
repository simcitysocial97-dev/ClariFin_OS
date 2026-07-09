"""
Repository Smoke Tests
======================
Tests to verify repository methods work correctly after SQL migration from db.py.
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
# Test: TransactionRepository smoke tests
# ============================================================

def test_transaction_repository_get_all():
    """Verify TransactionRepository.get_all_transactions() returns data correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = TransactionRepository(db_path=db_path)
        stmt_repo = StatementRepository(db_path)

        # Insert test data
        stmt_id = stmt_repo.insert_statement(bank="TestBank", file_name="test.pdf")
        transactions = [
            {"date": "15/01/2025", "description": "Test Txn 1", "amount": "100.50", "type": "debit"},
            {"date": "16/01/2025", "description": "Test Txn 2", "amount": "200.75", "type": "credit"},
        ]
        repo.insert_transactions(stmt_id, transactions)

        result = repo.get_all_transactions()
        assert len(result) == 2, "Should have 2 transactions"

    finally:
        os.unlink(db_path)


def test_transaction_repository_get_all_with_filters():
    """Verify TransactionRepository.get_all_transactions() with filters works."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = TransactionRepository(db_path=db_path)
        stmt_repo = StatementRepository(db_path)

        # Insert test data
        stmt_id = stmt_repo.insert_statement(bank="TestBank", file_name="test.pdf")
        transactions = [
            {"date": "15/01/2025", "description": "Food", "amount": "100.00", "type": "debit", "category": "Food"},
            {"date": "16/01/2025", "description": "Travel", "amount": "200.00", "type": "debit", "category": "Travel"},
        ]
        repo.insert_transactions(stmt_id, transactions)

        # Test with category filter
        filters = {"category": "Food"}
        result = repo.get_all_transactions(filters=filters)

        assert len(result) == 1, "Should filter to 1 transaction"

    finally:
        os.unlink(db_path)


def test_transaction_repository_monthly_summary():
    """Verify TransactionRepository.get_monthly_summary() returns data correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = TransactionRepository(db_path=db_path)
        stmt_repo = StatementRepository(db_path)

        # Insert test data
        stmt_id = stmt_repo.insert_statement(bank="TestBank", file_name="test.pdf")
        transactions = [
            {"date": "15/01/2025", "description": "Txn 1", "amount": "100.00", "type": "debit"},
            {"date": "16/01/2025", "description": "Txn 2", "amount": "200.00", "type": "credit"},
        ]
        repo.insert_transactions(stmt_id, transactions)

        result = repo.get_monthly_summary()
        assert len(result) > 0, "Should have monthly summary"

    finally:
        os.unlink(db_path)


# ============================================================
# Test: ReconciliationRepository smoke tests
# ============================================================

def test_reconciliation_repository_get_reconciliations():
    """Verify ReconciliationRepository.get_reconciliations() returns data correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = ReconciliationRepository(db_path=db_path)
        stmt_repo = StatementRepository(db_path)

        # Insert test data
        stmt_repo.insert_statement("Account_A", "stmt_a.pdf")
        stmt_repo.insert_statement("Account_B", "stmt_b.pdf")

        # Insert transactions
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
            VALUES
                (1, '01/01/2025', '2025-01-01', 'Transfer out', 100000, 'debit', 'Account_A'),
                (2, '01/01/2025', '2025-01-01', 'Transfer in', 100000, 'credit', 'Account_B')
        """)
        conn.commit()
        conn.close()

        # Create reconciliation via repo
        repo.insert_reconciliation(
            debit_txn_id=1,
            credit_txn_id=2,
            debit_account_id="Account_A",
            credit_account_id="Account_B",
            amount=1000.00,
            date_diff_days=0,
            match_confidence=0.8,
            match_type="exact",
        )

        result = repo.get_reconciliations()
        assert len(result) == 1, "Should have 1 reconciliation"

    finally:
        os.unlink(db_path)


def test_reconciliation_repository_get_pending():
    """Verify ReconciliationRepository.get_pending_reconciliations() returns data correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = ReconciliationRepository(db_path=db_path)
        stmt_repo = StatementRepository(db_path)

        stmt_repo.insert_statement("Account_A", "stmt_a.pdf")
        stmt_repo.insert_statement("Account_B", "stmt_b.pdf")

        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
            VALUES
                (1, '01/01/2025', '2025-01-01', 'Transfer out', 100000, 'debit', 'Account_A'),
                (2, '01/01/2025', '2025-01-01', 'Transfer in', 100000, 'credit', 'Account_B')
        """)
        conn.commit()
        conn.close()

        repo.insert_reconciliation(
            debit_txn_id=1,
            credit_txn_id=2,
            debit_account_id="Account_A",
            credit_account_id="Account_B",
            amount=1000.00,
            date_diff_days=0,
            match_confidence=0.8,
            match_type="exact",
        )

        result = repo.get_pending_reconciliations()
        assert len(result) == 1, "Should have 1 pending reconciliation"

    finally:
        os.unlink(db_path)


# ============================================================
# Test: AccountRepository smoke tests
# ============================================================

def test_account_repository_get_all():
    """Verify AccountRepository.get_all_accounts() returns data correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = AccountRepository(db_path=db_path)

        repo.create_account(
            name="Test Account",
            bank="TestBank",
            account_type="savings",
            balance_paise=50000,
        )

        result = repo.get_all_accounts()
        assert len(result) == 1, "Should have 1 account"

    finally:
        os.unlink(db_path)


def test_account_repository_create_and_get():
    """Verify AccountRepository.create_account() and get_account_by_id() work."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = AccountRepository(db_path=db_path)

        repo.create_account(
            name="Test Account",
            bank="TestBank",
            account_type="savings",
            balance_paise=50000,
        )

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM accounts WHERE name = ?", ("Test Account",))
        row = cur.fetchone()
        conn.close()

        assert row is not None, "Account should be created"
        assert row["name"] == "Test Account"
        assert row["bank"] == "TestBank"
        assert row["balance_paise"] == 50000

    finally:
        os.unlink(db_path)


# ============================================================
# Test: StatementRepository smoke tests
# ============================================================

def test_statement_repository_get_all():
    """Verify StatementRepository.get_all_statements() returns data correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = StatementRepository(db_path=db_path)

        repo.insert_statement(bank="HDFC", file_name="hdfc.pdf")
        repo.insert_statement(bank="ICICI", file_name="icici.pdf")

        result = repo.get_all_statements()
        assert len(result) == 2, "Should have 2 statements"

    finally:
        os.unlink(db_path)


def test_statement_repository_insert():
    """Verify StatementRepository.insert_statement() works correctly."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        repo = StatementRepository(db_path=db_path)

        stmt_id = repo.insert_statement(
            bank="TestBank",
            file_name="test.pdf",
            period_from="01/01/2025",
            period_to="31/01/2025",
            card_last4="1234",
        )

        assert stmt_id is not None and stmt_id > 0, "Should return valid statement ID"

    finally:
        os.unlink(db_path)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
