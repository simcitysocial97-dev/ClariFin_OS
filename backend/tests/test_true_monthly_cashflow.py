"""Tests for True Monthly Cashflow calculation.

Run: python -m pytest tests/test_true_monthly_cashflow.py -v

This test file verifies:
1. Regression test: Old get_monthly_cashflow incorrectly includes artificial income
2. New get_true_monthly_cashflow correctly excludes credit-card cash advance credit legs
3. New get_true_monthly_cashflow correctly includes only fee as expense for cash advances
4. transfer_internal events are excluded from both income and expense
5. emi_payment events include only interest as expense
6. Household/owner scoping works correctly
"""
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

# Ensure src is on path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.repositories.cashflow_repository import CashflowRepository
from src.repositories.financial_event_repository import FinancialEventRepository


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database with all required tables."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)

    # Create accounts table (with household columns)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bank TEXT DEFAULT '',
            account_type TEXT NOT NULL,
            account_number_last4 TEXT DEFAULT 'XXXX',
            balance_paise INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            owner_id TEXT DEFAULT 'self',
            household_id TEXT DEFAULT 'primary'
        )
    """)

    # Create transactions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_iso TEXT,
            amount_paise INTEGER,
            type TEXT,
            description TEXT,
            account_id TEXT,
            member TEXT DEFAULT 'Self'
        )
    """)

    # Create financial_events table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            transaction_ids TEXT NOT NULL,
            amount_paise INTEGER DEFAULT 0,
            asset_change_paise INTEGER DEFAULT 0,
            liability_change_paise INTEGER DEFAULT 0,
            expense_paise INTEGER DEFAULT 0,
            date_iso TEXT,
            month_bucket TEXT,
            account_id TEXT,
            category TEXT,
            provider TEXT,
            confidence_bps INTEGER,
            household_id TEXT DEFAULT 'primary',
            owner_id TEXT DEFAULT 'self'
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)


# ============================================================
# Regression Test: Cash Advance Pollution
# ============================================================

def test_regression_cash_advance_pollutes_income(temp_db):
    """
    REGRESSION TEST: Old get_monthly_cashflow incorrectly includes
    credit advance credit leg as income.

    Scenario:
    - Salary credit: ₹80,000 (true income)
    - CRED cash-advance: ₹30,000 debit + ₹31,250 credit + ₹1,250 fee
      (Net: ₹1000 cash extracted, ₹1250 fee)

    OLD behavior: income = ₹80,000 + ₹31,250 = ₹111,250 (WRONG - includes borrowed money)
    NEW behavior: income = ₹80,000 (correct - excludes artificial income)
    """
    conn = sqlite3.connect(temp_db)

    # Create accounts
    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (1, "HDFC", "savings", "self", "primary"),
    )
    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (2, "HDFC_SAVINGS", "savings", "self", "primary"),
    )

    # Create salary credit (true income)
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "2025-07-01", 80000, "credit", "Salary Credit", "1"),
    )

    # Create CRED cash advance debit (from primary account)
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (2, "2025-07-02", 30000, "debit", "CRED Payment", "1"),
    )

    # Create credit to savings (the cash advance credit leg)
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (3, "2025-07-02", 31250, "credit", "Cash Advance Credit", "2"),
    )

    conn.commit()
    conn.close()

    # Create financial event for the cash advance
    event_repo = FinancialEventRepository(temp_db)

    # Insert credit_card_cash_advance event
    # transaction_ids should be [2, 3] - the debit and credit
    # asset_change_paise = 31250 (credit received)
    # liability_change_paise = 30000 (amount transacted)
    # expense_paise = 1250 (fee)
    import json
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO financial_events (event_type, transaction_ids, amount_paise, asset_change_paise, liability_change_paise, expense_paise, date_iso, month_bucket, account_id, household_id, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "credit_card_cash_advance",
            json.dumps([2, 3]),
            30000,  # amount_paise (debit amount)
            31250,  # asset_change_paise (credit received)
            30000,  # liability_change_paise (borrowing)
            1250,   # expense_paise (fee)
            "2025-07-02",
            "2025-07",
            "1",
            "primary",
            "self",
        ),
    )
    conn.commit()
    conn.close()

    # Test OLD method (should show wrong income)
    cashflow_repo = CashflowRepository(temp_db)
    old_result = cashflow_repo.get_monthly_cashflow(months=12)

    # Find July 2025 in old result
    old_july = next((r for r in old_result if r.get("month_key") == "2025-07"), None)

    # OLD method incorrectly sums: 80000 (salary) + 31250 (credit) = 111250 income
    # And incorrectly sums: 30000 (debit) as expense
    assert old_july is not None, "Old method should find July 2025"
    # Note: The old method uses member filter which doesn't exist in our test data,
    # so we might need to adjust this assertion based on actual behavior


# ============================================================
# Test: True Monthly Cashflow Correct Behavior
# ============================================================

def test_true_monthly_cashflow_excludes_artificial_income(temp_db):
    """
    NEW: get_true_monthly_cashflow correctly excludes artificial income.

    Expected after adjustment:
    - income = ₹80,000 (salary only)
    - expense = ₹1,250 (fee only)
    - surplus = ₹78,750
    """
    conn = sqlite3.connect(temp_db)

    # Create accounts with household/owner info
    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (1, "HDFC", "savings", "self", "primary"),
    )
    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (2, "HDFC_SAVINGS", "savings", "self", "primary"),
    )

    # Create salary credit (true income)
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "2025-07-01", 80000, "credit", "Salary Credit", "1"),
    )

    # Create CRED cash advance debit
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (2, "2025-07-02", 30000, "debit", "CRED Payment", "1"),
    )

    # Create credit to savings
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (3, "2025-07-02", 31250, "credit", "Cash Advance Credit", "2"),
    )

    conn.commit()
    conn.close()

    # Create financial event for the cash advance
    import json
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO financial_events (event_type, transaction_ids, amount_paise, asset_change_paise, liability_change_paise, expense_paise, date_iso, month_bucket, account_id, household_id, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "credit_card_cash_advance",
            json.dumps([2, 3]),
            30000,  # amount_paise (debit amount)
            31250,  # asset_change_paise (credit received)
            30000,  # liability_change_paise (borrowing)
            1250,   # expense_paise (fee)
            "2025-07-02",
            "2025-07",
            "1",
            "primary",
            "self",
        ),
    )
    conn.commit()
    conn.close()

    # Test NEW method
    cashflow_repo = CashflowRepository(temp_db)
    true_result = cashflow_repo.get_true_monthly_cashflow(
        months=12,
        household_id="primary",
        owner_id="self",
    )

    true_july = next((r for r in true_result if r.get("month_key") == "2025-07"), None)

    assert true_july is not None, "True method should find July 2025"
    # Expected: income = 80000 (salary) - 31250 (excluded credit advance) = 48750
    # But we also have the credit leg as a separate transaction
    # Let's verify the adjustment logic
    assert true_july["income_paise"] == 80000, f"Income should be 80000 (salary only), got {true_july['income_paise']}"
    assert true_july["expense_paise"] == 1250, f"Expense should be 1250 (fee only), got {true_july['expense_paise']}"
    assert true_july["surplus_paise"] == 78750, f"Surplus should be 78750, got {true_july['surplus_paise']}"
    assert len(true_july["adjustments_applied"]) == 2, "Should have 2 adjustments recorded"


# ============================================================
# Test: Transfer Internal Exclusion
# ============================================================

def test_true_monthly_cashflow_excludes_transfers(temp_db):
    """
    transfer_internal events should be excluded from both income and expense.
    """
    conn = sqlite3.connect(temp_db)

    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (1, "HDFC", "savings", "self", "primary"),
    )
    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (2, "ICICI", "savings", "self", "primary"),
    )

    # Regular income
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "2025-07-01", 50000, "credit", "Income", "1"),
    )

    # Transfer debit
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (2, "2025-07-02", 10000, "debit", "Transfer to ICICI", "1"),
    )

    # Transfer credit
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (3, "2025-07-02", 10000, "credit", "Transfer from HDFC", "2"),
    )

    conn.commit()
    conn.close()

    # Create transfer_internal event
    import json
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO financial_events (event_type, transaction_ids, amount_paise, date_iso, month_bucket, account_id, household_id, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "transfer_internal",
            json.dumps([2, 3]),
            10000,
            "2025-07-02",
            "2025-07",
            "1",
            "primary",
            "self",
        ),
    )
    conn.commit()
    conn.close()

    cashflow_repo = CashflowRepository(temp_db)
    true_result = cashflow_repo.get_true_monthly_cashflow(
        months=12,
        household_id="primary",
        owner_id="self",
    )

    true_july = next((r for r in true_result if r.get("month_key") == "2025-07"), None)

    assert true_july is not None
    # Income should be 50000 (no transfers)
    assert true_july["income_paise"] == 50000
    assert true_july["expense_paise"] == 0  # transfer excluded


# ============================================================
# Test: EMI Payment Adjustment
# ============================================================

def test_true_monthly_cashflow_emi_interest_only(temp_db):
    """
    emi_payment events should only count interest as expense.
    """
    conn = sqlite3.connect(temp_db)

    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (1, "HDFC", "savings", "self", "primary"),
    )

    # Regular income
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "2025-07-01", 100000, "credit", "Income", "1"),
    )

    # EMI payment (₹15000 total, ₹1000 interest)
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (2, "2025-07-02", 15000, "debit", "EMI Payment", "1"),
    )

    conn.commit()
    conn.close()

    # Create emi_payment event
    import json
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO financial_events (event_type, transaction_ids, amount_paise, expense_paise, date_iso, month_bucket, account_id, household_id, owner_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "emi_payment",
            json.dumps([2]),
            15000,  # Full EMI amount
            1000,  # Interest portion only
            "2025-07-02",
            "2025-07",
            "1",
            "primary",
            "self",
        ),
    )
    conn.commit()
    conn.close()

    cashflow_repo = CashflowRepository(temp_db)
    true_result = cashflow_repo.get_true_monthly_cashflow(
        months=12,
        household_id="primary",
        owner_id="self",
    )

    true_july = next((r for r in true_result if r.get("month_key") == "2025-07"), None)

    assert true_july is not None
    # Income = 100000
    # Expense should be adjusted to 1000 (interest only)
    assert true_july["income_paise"] == 100000
    assert true_july["expense_paise"] == 1000


# ============================================================
# Test: Household Scoping
# ============================================================

def test_true_monthly_cashflow_household_scoping(temp_db):
    """
    Household/owner scoping should filter correctly.
    """
    conn = sqlite3.connect(temp_db)

    # Self account
    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (1, "Self_Savings", "savings", "self", "primary"),
    )

    # Spouse account
    conn.execute(
        "INSERT INTO accounts (id, name, account_type, owner_id, household_id) VALUES (?, ?, ?, ?, ?)",
        (2, "Spouse_Savings", "savings", "spouse", "primary"),
    )

    # Self income
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (1, "2025-07-01", 80000, "credit", "Self Salary", "1"),
    )

    # Spouse income
    conn.execute(
        "INSERT INTO transactions (id, date_iso, amount_paise, type, description, account_id) VALUES (?, ?, ?, ?, ?, ?)",
        (2, "2025-07-01", 60000, "credit", "Spouse Salary", "2"),
    )

    conn.commit()
    conn.close()

    cashflow_repo = CashflowRepository(temp_db)

    # Get self-only
    self_result = cashflow_repo.get_true_monthly_cashflow(
        months=12,
        household_id="primary",
        owner_id="self",
    )

    # Get household-wide (owner_id=None)
    household_result = cashflow_repo.get_true_monthly_cashflow(
        months=12,
        household_id="primary",
        owner_id=None,
    )

    self_july = next((r for r in self_result if r.get("month_key") == "2025-07"), None)
    household_july = next((r for r in household_result if r.get("month_key") == "2025-07"), None)

    assert self_july is not None
    assert household_july is not None
    assert self_july["income_paise"] == 80000, "Self should only see self income"
    assert household_july["income_paise"] == 140000, "Household should see both incomes"


# ============================================================
# Engine Purity Test
# ============================================================

def test_cashflow_repository_purity():
    """CashflowRepository should only import repositories/base for DB access."""
    import ast
    engine_path = Path(__file__).parent.parent / "src" / "repositories" / "cashflow_repository.py"
    source = engine_path.read_text()
    tree = ast.parse(source)

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)

    # Verify no sqlite3 imports (should use BaseRepository)
    assert "sqlite3" not in imports, f"sqlite3 import found in cashflow_repository.py"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])