"""Tests for EMI Detection - schedule generation, detector logic, and service orchestration.

Run: python -m pytest tests/test_emi_detection.py -v
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.db import FinanceDB
from src.engines.loan_engine import generate_schedule
from src.engines.transaction_intelligence import detect_emi_payment, find_loan_candidates_for_account
from src.repositories.loan_repository import LoanRepository
from src.repositories.transaction_classification_repository import TransactionClassificationRepository
from src.services.transaction_intelligence_service import TransactionIntelligenceService
from scripts.migration_emi_detection import run_migration


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database with EMI detection schema."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Initialize FinanceDB schema
    db = FinanceDB(db_path=db_path)

    # Run EMI detection migration
    run_migration(db_path)

    yield db, db_path

    # Cleanup
    if db._conn:
        db._conn.close()
        db._conn = None
    os.unlink(db_path)


@pytest.fixture
def populated_emi_db(temp_db):
    """Database with loan and transaction for EMI detection testing."""
    db, db_path = temp_db

    # Create a loan account
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO accounts (id, name, bank, account_type, balance_paise, is_active)
        VALUES ('HDFC_SB', 'HDFC Savings', 'HDFC', 'savings', 500000, 1)
    """)

    # Create a loan (must have is_active for list_loans to return it)
    loan_id = conn.execute("""
        INSERT INTO loans (name, lender, loan_type, principal_paise, outstanding_paise,
                           interest_rate, tenure_months, emi_paise, disbursed_date, is_active)
        VALUES ('Home Loan', 'HDFC', 'home', 50000000, 45000000, 8.5, 240, 470000, '2023-01-01', 1)
    """).lastrowid

    # Create a statement and transaction
    # Note: debit/credit are GENERATED columns from amount_paise and type
    stmt_id = conn.execute("""
        INSERT INTO statements (bank, file_name) VALUES ('HDFC', 'emi_test.pdf')
    """).lastrowid

    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, member)
        VALUES (?, '01/07/2025', '2025-07-01', 'HDFC Home Loan EMI', 470000, 'debit', 'HDFC', 'Self')
    """, (stmt_id,))

    # Another transaction that's NOT EMI (should not match)
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, member)
        VALUES (?, '01/07/2025', '2025-07-01', 'Grocery Shopping', 50000, 'debit', 'HDFC', 'Self')
    """, (stmt_id,))

    conn.commit()
    conn.close()

    return db, db_path, loan_id


# ============================================================
# Test 1: Schedule Generation
# ============================================================

def test_generate_and_persist_schedule():
    """get_or_generate_schedule generates and persists a full schedule."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        run_migration(db_path)

        # Create a loan (without providing emi_paise - let engine compute it)
        conn = sqlite3.connect(db_path)
        loan_id = conn.execute("""
            INSERT INTO loans (name, lender, loan_type, principal_paise, outstanding_paise,
                               interest_rate, tenure_months, emi_paise, disbursed_date, is_active)
            VALUES ('Test Loan', 'ICICI', 'personal', 10000000, 10000000, 12.0, 60, 250000, '2025-01-01', 1)
        """).lastrowid
        conn.commit()
        conn.close()

        # Generate schedule via service
        from src.services.loan_service import LoanService
        service = LoanService(db_path)
        schedule = service.get_or_generate_schedule(loan_id)

        assert len(schedule) == 60, f"Expected 60 months, got {len(schedule)}"
        # EMI is computed by engine based on principal and rate
        assert schedule[0]["emi_paise"] > 0  # Some valid EMI value

        # Verify persisted
        repo = LoanRepository(db_path)
        persisted = repo.get_schedule_rows(loan_id)
        assert len(persisted) == 60
        assert persisted[0]["source"] == "computed"

    finally:
        os.unlink(db_path)


# ============================================================
# Test 2: EMI Detection
# ============================================================

def test_detect_emi_exact_amount_match(populated_emi_db):
    """detect_emi_payment identifies EMI with exact amount match."""
    db, db_path, loan_id = populated_emi_db

    # Transaction: ₹4700 EMI on HDFC account
    txn = {
        "id": 1,
        "account_id": "HDFC",
        "date_iso": "2025-07-01",
        "debit": 470000,
        "description": "HDFC Home Loan EMI",
    }

    loan = {
        "id": loan_id,
        "lender": "HDFC",
        "emi_paise": 470000,
        "next_emi_date": "2025-07-01",
    }

    # Empty schedule lookup (will still match on amount+description)
    result = detect_emi_payment(txn, [loan], {})

    assert result is not None
    assert result.matched_entity_id == loan_id
    assert result.sub_classification == "emi"
    # Priority 60 = description only, 75 = date_proximity, 80 = amount_only, 85 = amount+date, 90 = amount+schedule, 100 = bank_statement
    assert result.priority in [60, 75, 80, 85, 90, 100]


def test_detect_emi_within_tolerance(populated_emi_db):
    """detect_emi_payment matches amounts within ±1% tolerance."""
    db, db_path, loan_id = populated_emi_db

    # EMI of 470000, transaction of 471000 (within 1%)
    txn = {
        "id": 1,
        "account_id": "HDFC",
        "date_iso": "2025-07-01",
        "debit": 471000,  # 0.2% higher
        "description": "Loan Payment",
    }

    loan = {"id": loan_id, "lender": "HDFC", "emi_paise": 470000}

    result = detect_emi_payment(txn, [loan], {})

    assert result is not None
    assert result.matched_entity_id == loan_id


def test_detect_emi_outside_tolerance(populated_emi_db):
    """detect_emi_payment rejects amounts outside ±1% tolerance."""
    db, db_path, loan_id = populated_emi_db

    # EMI of 470000, transaction of 500000 (way outside 1%)
    txn = {
        "id": 2,
        "account_id": "HDFC",
        "date_iso": "2025-07-01",
        "debit": 500000,  # 6% higher
        "description": "Grocery Shopping",
    }

    loan = {"id": loan_id, "lender": "HDFC", "emi_paise": 470000}

    result = detect_emi_payment(txn, [loan], {})

    assert result is None


def test_detect_emi_with_schedule_row(populated_emi_db):
    """detect_emi_payment returns principal/interest from schedule row when available."""
    db, db_path, loan_id = populated_emi_db

    txn = {
        "id": 1,
        "account_id": "HDFC",
        "date_iso": "2025-07-01",
        "debit": 470000,
        "description": "EMI Payment",
    }

    loan = {"id": loan_id, "lender": "HDFC", "emi_paise": 470000}

    schedule_row = {
        "id": 1,
        "loan_id": loan_id,
        "due_date": "2025-07-01",
        "emi_paise": 470000,
        "principal_paise": 200000,
        "interest_paise": 270000,
        "outstanding_after_paise": 44730000,
        "source": "computed",
    }

    schedule_lookup = {(loan_id, "2025-07-01"): schedule_row}

    result = detect_emi_payment(txn, [loan], schedule_lookup)

    assert result is not None
    assert result.principal_paise == 200000
    assert result.interest_paise == 270000


# ============================================================
# Test 3: Bank Statement Override
# ============================================================

def test_bank_statement_override():
    """Bank statement schedule rows take precedence over computed."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        run_migration(db_path)

        conn = sqlite3.connect(db_path)
        loan_id = conn.execute("""
            INSERT INTO loans (name, lender, loan_type, principal_paise, outstanding_paise,
                               interest_rate, tenure_months, emi_paise, disbursed_date, is_active)
            VALUES ('Override Loan', 'Axis', 'personal', 10000000, 10000000, 11.0, 12, 100000, '2025-01-01', 1)
        """).lastrowid
        conn.commit()
        conn.close()

        txn = {
            "id": 1,
            "account_id": "Axis",
            "date_iso": "2025-01-01",
            "debit": 100000,
            "description": "EMI",
        }

        loan = {"id": loan_id, "lender": "Axis", "emi_paise": 100000}

        # Bank statement row
        bank_row = {
            "id": 1,
            "loan_id": loan_id,
            "due_date": "2025-01-01",
            "emi_paise": 100000,
            "principal_paise": 90000,
            "interest_paise": 10000,
            "outstanding_after_paise": 9900000,
            "source": "bank_statement",
        }

        schedule_lookup = {(loan_id, "2025-01-01"): bank_row}

        result = detect_emi_payment(txn, [loan], schedule_lookup)

        assert result is not None
        assert result.source == "bank_statement"
        assert result.priority == 100

    finally:
        os.unlink(db_path)


# ============================================================
# Test 4: Detector Purity (No DB Access)
# ============================================================

def test_detector_purity_no_db_calls():
    """detect_emi_payment makes ZERO database calls."""
    txn = {
        "id": 1,
        "account_id": "HDFC",
        "date_iso": "2025-07-01",
        "debit": 470000,
        "description": "EMI",
    }

    loan = {"id": 1, "lender": "HDFC", "emi_paise": 470000}
    schedule_lookup = {}

    with patch('sqlite3.connect') as mock_connect:
        result = detect_emi_payment(txn, [loan], schedule_lookup)
        # Should not have called sqlite3.connect
        assert not mock_connect.called or mock_connect.call_count == 0


# ============================================================
# Test 5: Service Orchestration
# ============================================================

def test_service_classify_emi(populated_emi_db):
    """TransactionIntelligenceService classifies EMI payments correctly."""
    db, db_path, loan_id = populated_emi_db

    service = TransactionIntelligenceService(db_path)
    results = service.classify_emi_payments()

    assert len(results) >= 1
    assert results[0]["classification"] == "liability_payment"
    assert results[0]["sub_classification"] == "emi"
    assert results[0]["loan_id"] == loan_id


def test_service_idempotency(populated_emi_db):
    """Running detector twice does not create duplicate classifications."""
    db, db_path, loan_id = populated_emi_db

    service = TransactionIntelligenceService(db_path)

    # First run
    results1 = service.classify_emi_payments()
    assert len(results1) >= 1

    # Second run
    results2 = service.classify_emi_payments()
    assert len(results2) == 0  # No new classifications

    # Verify only one classification exists
    repo = TransactionClassificationRepository(db_path)
    classification = repo.get_by_transaction_id(1)
    assert classification is not None
    assert classification["classification"] == "liability_payment"


def test_household_isolation():
    """Spouse's transactions are not classified when in self mode."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        FinanceDB(db_path=db_path)
        run_migration(db_path)

        conn = sqlite3.connect(db_path)

        # Create self and spouse accounts (no household_id column in accounts table)
        conn.execute("""
            INSERT INTO accounts (id, name, bank, account_type, balance_paise, is_active)
            VALUES ('Self_Account', 'Self Account', 'SelfBank', 'savings', 500000, 1)
        """)
        conn.execute("""
            INSERT INTO accounts (id, name, bank, account_type, balance_paise, is_active)
            VALUES ('Spouse_Account', 'Spouse Account', 'SpouseBank', 'savings', 300000, 1)
        """)

        # Create loan (must have is_active for list_loans to return it)
        loan_id = conn.execute("""
            INSERT INTO loans (name, lender, loan_type, principal_paise, outstanding_paise,
                               interest_rate, tenure_months, emi_paise, disbursed_date, is_active)
            VALUES ('Isolated Loan', 'SelfBank', 'personal', 10000000, 10000000, 10.0, 60, 200000, '2025-01-01', 1)
        """).lastrowid

        # Create transactions for both
        stmt_id = conn.execute(
            "INSERT INTO statements (bank, file_name) VALUES ('SelfBank', 'test.pdf')"
        ).lastrowid

        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, member)
            VALUES (?, '01/01/2025', '2025-01-01', 'EMI Payment', 200000, 'debit', 'SelfBank', 'Self')
        """, (stmt_id,))

        conn.execute("""
            INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, member)
            VALUES (?, '01/01/2025', '2025-01-01', 'Spouse EMI', 200000, 'debit', 'SpouseBank', 'Spouse')
        """, (stmt_id,))

        conn.commit()
        conn.close()

        service = TransactionIntelligenceService(db_path)
        results = service.classify_emi_payments(owner_id="self")

        # Only Self member transaction should be classified
        assert len(results) == 1
        assert results[0]["transaction_id"] == 1

    finally:
        os.unlink(db_path)


# ============================================================
# Test 6: find_loan_candidates_for_account
# ============================================================

def test_find_loan_candidates():
    """find_loan_candidates_for_account filters correctly."""
    loans = [
        {"id": 1, "lender": "HDFC", "name": "Home Loan"},
        {"id": 2, "lender": "ICICI", "name": "Personal Loan"},
        {"id": 3, "lender": "SBI", "name": "Car Loan"},
    ]

    # Exact match
    candidates = find_loan_candidates_for_account("HDFC", loans)
    assert len(candidates) == 1
    assert candidates[0]["id"] == 1

    # No match
    candidates = find_loan_candidates_for_account("Axis", loans)
    assert len(candidates) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])