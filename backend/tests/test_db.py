"""
Test suite for db.py - Money Integrity Tests
============================================

Tests for _parse_amount_paise function to verify integer paise parsing.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from db import FinanceDB, _parse_amount_paise

# ============================================================
# Test: _parse_amount_paise
# ============================================================

def test_parse_amount_paise():
    """Test that _parse_amount_paise correctly parses amounts to integer paise."""
    # Test standard formats
    assert _parse_amount_paise("Rs 1,234.56") == 123456
    assert _parse_amount_paise("₹1234.56") == 123456
    assert _parse_amount_paise("1234") == 123400
    assert _parse_amount_paise("1234.56") == 123456

    # Test edge cases
    assert _parse_amount_paise("0") == 0
    assert _parse_amount_paise("0.01") == 1
    assert _parse_amount_paise("0.99") == 99
    assert _parse_amount_paise("100.00") == 10000

    # Test with spaces
    assert _parse_amount_paise(" 1234.56 ") == 123456
    assert _parse_amount_paise("Rs 1,234.56 ") == 123456


def test_parse_amount_paise_raises_on_invalid():
    """Test that _parse_amount_paise raises ValueError on invalid input."""
    # Empty string should raise
    with pytest.raises(ValueError, match="Empty amount string"):
        _parse_amount_paise("")

    with pytest.raises(ValueError, match="Empty amount string"):
        _parse_amount_paise("   ")

    # Invalid format should raise
    with pytest.raises(ValueError, match="Invalid amount format"):
        _parse_amount_paise("invalid")

    with pytest.raises(ValueError, match="Invalid amount format"):
        _parse_amount_paise("abc123")


def test_parse_amount_paise_no_float_precision_loss():
    """Test that Decimal is used internally to avoid float precision issues."""
    # These values would lose precision with float arithmetic
    # 0.01 * 100 = 1.0 (correct)
    assert _parse_amount_paise("0.01") == 1

    # 0.29 * 100 = 29.0 (correct, but float might give 28.9999...)
    assert _parse_amount_paise("0.29") == 29

    # 0.56 * 100 = 56.0 (correct)
    assert _parse_amount_paise("0.56") == 56

    # Large amounts
    assert _parse_amount_paise("1234567.89") == 123456789


def test_insert_transactions_uses_paise():
    """Test that insert_transactions correctly stores amount_paise."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        db = FinanceDB(db_path)

        # Create statement
        stmt_id = db.insert_statement(
            bank="TestBank",
            file_name="test_statement.pdf",
        )

        # Insert transaction with known amount
        transactions = [
            {"date": "15/01/2025", "description": "Test Transaction", "amount": "1234.56", "type": "debit"},
        ]

        db.insert_transactions(stmt_id, transactions)

        # Verify amount_paise is stored correctly
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT amount, amount_paise FROM transactions WHERE statement_id = ?", (stmt_id,))
        row = cur.fetchone()
        conn.close()

        assert row is not None, "Transaction not found"
        assert row["amount_paise"] == 123456, f"amount_paise should be 123456, got {row['amount_paise']}"
        # debit/credit are GENERATED ALWAYS AS columns, computed from amount_paise and type
        # They are not stored directly, so we don't check them here

    finally:
        os.unlink(db_path)


def test_insert_csv_transactions_uses_paise():
    """Test that insert_csv_transactions correctly stores amount_paise."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        db = FinanceDB(db_path)

        # Insert CSV transactions
        transactions = [
            {"date": "15/01/2025", "description": "CSV Transaction", "amount": "999.99", "type": "credit"},
        ]

        db.insert_csv_transactions(transactions, bank="CSVTest")

        # Verify amount_paise is stored correctly
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT amount, amount_paise, debit, credit FROM transactions")
        row = cur.fetchone()
        conn.close()

        assert row is not None, "Transaction not found"
        assert row["amount_paise"] == 99999, f"amount_paise should be 99999, got {row['amount_paise']}"
        assert row["debit"] == 0, f"debit should be 0, got {row['debit']}"
        assert row["credit"] == 99999, f"credit should be 99999, got {row['credit']}"

    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
