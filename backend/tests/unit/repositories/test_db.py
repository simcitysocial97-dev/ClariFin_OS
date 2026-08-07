"""
Test suite for db.py - Money Integrity Tests
============================================

Tests for _parse_amount_paise function to verify integer paise parsing.
"""

import sqlite3

import pytest

from db import _parse_amount_paise
from repositories.statement_repository import StatementRepository
from repositories.transaction_repository import TransactionRepository


def test_parse_amount_paise():
    """Test that _parse_amount_paise correctly parses amounts to integer paise."""
    assert _parse_amount_paise("Rs 1,234.56") == 123456
    assert _parse_amount_paise("₹1234.56") == 123456
    assert _parse_amount_paise("1234") == 123400
    assert _parse_amount_paise("1234.56") == 123456

    assert _parse_amount_paise("0") == 0
    assert _parse_amount_paise("0.01") == 1
    assert _parse_amount_paise("0.99") == 99
    assert _parse_amount_paise("100.00") == 10000

    assert _parse_amount_paise(" 1234.56 ") == 123456
    assert _parse_amount_paise("Rs 1,234.56 ") == 123456


def test_parse_amount_paise_raises_on_invalid():
    """Test that _parse_amount_paise raises ValueError on invalid input."""
    with pytest.raises(ValueError, match="Empty amount string"):
        _parse_amount_paise("")

    with pytest.raises(ValueError, match="Empty amount string"):
        _parse_amount_paise("   ")

    with pytest.raises(ValueError, match="Invalid amount format"):
        _parse_amount_paise("invalid")

    with pytest.raises(ValueError, match="Invalid amount format"):
        _parse_amount_paise("abc123")


def test_parse_amount_paise_no_float_precision_loss():
    """Test that Decimal is used internally to avoid float precision issues."""
    assert _parse_amount_paise("0.01") == 1
    assert _parse_amount_paise("0.29") == 29
    assert _parse_amount_paise("0.56") == 56
    assert _parse_amount_paise("1234567.89") == 123456789


def test_insert_transactions_uses_paise(temp_db: str) -> None:
    """Test that insert_transactions correctly stores amount_paise (in paise)."""
    stmt_repo = StatementRepository(temp_db)
    txn_repo = TransactionRepository(temp_db)

    stmt_id = stmt_repo.insert_statement(
        bank="TestBank",
        file_name="test_statement.pdf",
    )

    transactions = [
        {
            "date": "15/01/2025",
            "description": "Test Transaction",
            "amount_paise": 123456,
            "type": "debit",
        },
    ]

    txn_repo.insert_transactions(stmt_id, transactions)

    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT amount_paise, debit, credit FROM transactions WHERE statement_id = ?",
        (stmt_id,),
    )
    row = cur.fetchone()
    conn.close()

    assert row is not None, "Transaction not found"
    assert row["amount_paise"] == 123456
    assert row["debit"] == 123456
    assert row["credit"] == 0


def test_insert_csv_transactions_uses_paise(temp_db: str) -> None:
    """Test that insert_csv_transactions correctly stores amount_paise (in paise)."""
    txn_repo = TransactionRepository(temp_db)

    transactions = [
        {
            "date": "15/01/2025",
            "description": "CSV Transaction",
            "amount_paise": 99999,
            "type": "credit",
        },
    ]

    txn_repo.insert_csv_transactions(transactions, bank="CSVTest")

    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT amount_paise, debit, credit FROM transactions")
    row = cur.fetchone()
    conn.close()

    assert row is not None, "Transaction not found"
    assert row["amount_paise"] == 99999
    assert row["debit"] == 0
    assert row["credit"] == 99999


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
