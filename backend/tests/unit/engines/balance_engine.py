"""
Balance Engine Tests
====================

Tests for deterministic financial balance computation.
Covers date parsing, running balance, account balance, statement validation,
accounts list, and Indian rupee formatting.

Run: python -m pytest backend/tests/unit/engines/balance_engine.py -v
"""

import pytest
from datetime import date
from decimal import Decimal

from src.engines.balance_engine import (
    _parse_date_to_ymd,
    _parse_date_for_sort,
    compute_running_balance,
    compute_account_balance,
    validate_statement_balance,
    get_accounts_list,
    _format_paise,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db_with_data(temp_db: str) -> str:
    """Populate database with test transactions across multiple accounts."""
    from src.core.db.connection import get_connection

    conn = get_connection(temp_db)
    conn.executescript("""
        INSERT INTO statements (id, bank, file_name) VALUES
            (1, 'HDFC', 'stmt1.pdf'),
            (2, 'ICICI', 'stmt2.pdf'),
            (3, 'SBI', 'stmt3.pdf');

        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES
            -- HDFC transactions
            (1, '01/01/2025', '2025-01-01', 'Salary Credit', 5000000, 'credit', 'HDFC', 'hash1', 0),
            (1, '05/01/2025', '2025-01-05', 'Rent Payment', 1500000, 'debit', 'HDFC', 'hash2', 1),
            (1, '10/01/2025', '2025-01-10', 'Grocery', 50000, 'debit', 'HDFC', 'hash3', 2),
            (1, '15/01/2025', '2025-01-15', 'Bonus', 1000000, 'credit', 'HDFC', 'hash4', 3),
            -- ICICI transactions
            (2, '02/01/2025', '2025-01-02', 'Freelance Income', 2000000, 'credit', 'ICICI', 'hash5', 0),
            (2, '08/01/2025', '2025-01-08', 'EMI Payment', 300000, 'debit', 'ICICI', 'hash6', 1),
            -- SBI transactions (no date_iso to test fallback)
            (3, '03/01/2025', NULL, 'Interest', 50000, 'credit', 'SBI', 'hash7', 0),
            (3, '12/01/2025', NULL, 'Fee', 20000, 'debit', 'SBI', 'hash8', 1);
    """)
    conn.commit()
    conn.close()
    return temp_db


# ============================================================
# _parse_date_to_ymd Tests
# ============================================================

class TestParseDateToYmd:
    """Tests for _parse_date_to_ymd - all supported Indian date formats."""

    @pytest.mark.parametrize("input_date,expected_ymd", [
        ("01/01/2025", "2025-01-01"),
        ("31/12/2024", "2024-12-31"),
        ("01-01-2025", "2025-01-01"),
        ("31-12-2024", "2024-12-31"),
        ("01/01/25", "2025-01-01"),
        ("31/12/24", "2024-12-31"),
        ("01-01-25", "2025-01-01"),
        ("31-12-24", "2024-12-31"),
        ("01 Jan 2025", "2025-01-01"),
        ("31 Dec 2024", "2024-12-31"),
        ("01 Jan 25", "2025-01-01"),
        ("31 Dec 24", "2024-12-31"),
        ("01-Jan-2025", "2025-01-01"),
        ("31-Dec-2024", "2024-12-31"),
        ("XX01-Jan-25XX", "2025-01-01"),
        ("2025-01-01", "2025-01-01"),
    ])
    def test_parse_date_to_ymd_all_formats(self, input_date, expected_ymd):
        """All supported formats produce valid YYYY-MM-DD."""
        result = _parse_date_to_ymd(input_date)
        assert result == expected_ymd, f"Failed for format: {input_date}"

    def test_parse_date_to_ymd_unparseable_returns_empty(self):
        """Unparseable dates return empty string."""
        assert _parse_date_to_ymd("") == ""
        assert _parse_date_to_ymd("not-a-date") == ""
        assert _parse_date_to_ymd("32/01/2025") == ""  # Invalid day
        assert _parse_date_to_ymd("01/13/2025") == ""  # Invalid month

    def test_parse_date_to_ymd_idempotent(self):
        """Parsing is idempotent: parse(parse(x)) == parse(x)."""
        test_dates = ["01/01/2025", "01-01-2025", "01 Jan 2025", "2025-01-01"]
        for d in test_dates:
            first = _parse_date_to_ymd(d)
            second = _parse_date_to_ymd(first)
            assert first == second, f"Idempotence failed for {d}: {first} != {second}"

    def test_parse_date_to_ymd_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped before parsing."""
        assert _parse_date_to_ymd("  01/01/2025  ") == "2025-01-01"
        assert _parse_date_to_ymd("\t05-01-2025\n") == "2025-01-05"


# ============================================================
# _parse_date_for_sort Tests
# ============================================================

class TestParseDateForSort:
    """Tests for _parse_date_for_sort - sorting key generation."""

    def test_parse_date_for_sort_valid(self):
        """Valid dates return YMD string."""
        assert _parse_date_for_sort("01/01/2025") == "2025-01-01"
        assert _parse_date_for_sort("05-01-2025") == "2025-01-05"

    def test_parse_date_for_sort_invalid(self):
        """Invalid dates return '0000-00-00' (sorts first)."""
        assert _parse_date_for_sort("") == "0000-00-00"
        assert _parse_date_for_sort("not-a-date") == "0000-00-00"
        assert _parse_date_for_sort("32/01/2025") == "0000-00-00"

    def test_parse_date_for_sort_ordering(self):
        """Output usable for string sorting matches chronological order."""
        dates = ["31/12/2024", "01/01/2025", "15/01/2025", "01/02/2025"]
        sorted_keys = sorted(_parse_date_for_sort(d) for d in dates)
        assert sorted_keys == ["2024-12-31", "2025-01-01", "2025-01-15", "2025-02-01"]


# ============================================================
# compute_running_balance Tests
# ============================================================

class TestComputeRunningBalance:
    """Integration tests for running balance computation."""

    def test_compute_running_balance_basic(self, temp_db_with_data):
        """Running balance = starting + sum(credit - debit) in SQL order."""
        results = compute_running_balance(temp_db_with_data, "HDFC", starting_balance_paise=100000)

        assert len(results) == 4
        # Transaction 1: +5000000 -> 5100000
        assert results[0]["balance_paise"] == 5100000
        # Transaction 2: -1500000 -> 3600000
        assert results[1]["balance_paise"] == 3600000
        # Transaction 3: -50000 -> 3550000
        assert results[2]["balance_paise"] == 3550000
        # Transaction 4: +1000000 -> 4550000
        assert results[3]["balance_paise"] == 4550000

    def test_compute_running_balance_account_scoped(self, temp_db_with_data):
        """Account filtering isolates transactions correctly."""
        hdfc_results = compute_running_balance(temp_db_with_data, "HDFC")
        icici_results = compute_running_balance(temp_db_with_data, "ICICI")
        sbi_results = compute_running_balance(temp_db_with_data, "SBI")

        assert len(hdfc_results) == 4
        assert len(icici_results) == 2
        assert len(sbi_results) == 2

        # HDFC balances: 5000000 - 1500000 - 50000 + 1000000 = 4450000
        assert hdfc_results[-1]["balance_paise"] == 4450000
        # ICICI balances: 2000000 - 300000 = 1700000
        assert icici_results[-1]["balance_paise"] == 1700000
        # SBI balances: 50000 - 20000 = 30000
        assert sbi_results[-1]["balance_paise"] == 30000

    def test_compute_running_balance_date_ordering(self, temp_db_with_data):
        """SQL ORDER BY enforces chronological replay regardless of insert order."""
        results = compute_running_balance(temp_db_with_data, "HDFC")
        dates = [r["date_iso"] for r in results]
        assert dates == ["2025-01-01", "2025-01-05", "2025-01-10", "2025-01-15"]

    def test_compute_running_balance_fallback_parsing(self, temp_db_with_data):
        """Missing date_iso falls back to _parse_date_to_ymd on date field."""
        # SBI transactions have NULL date_iso but valid date field
        results = compute_running_balance(temp_db_with_data, "SBI")
        assert len(results) == 2
        assert results[0]["date_iso"] == "2025-01-03"
        assert results[1]["date_iso"] == "2025-01-12"

    def test_compute_running_balance_starting_balance(self, temp_db_with_data):
        """Starting balance added to first transaction."""
        results_zero = compute_running_balance(temp_db_with_data, "HDFC", starting_balance_paise=0)
        results_custom = compute_running_balance(temp_db_with_data, "HDFC", starting_balance_paise=100000)

        for r_zero, r_custom in zip(results_zero, results_custom):
            assert r_custom["balance_paise"] == r_zero["balance_paise"] + 100000

    def test_compute_running_balance_output_fields(self, temp_db_with_data):
        """All 7 output fields present with correct types."""
        results = compute_running_balance(temp_db_with_data, "HDFC")
        r = results[0]

        assert "transaction_id" in r and isinstance(r["transaction_id"], int)
        assert "date" in r and isinstance(r["date"], str)
        assert "date_iso" in r and isinstance(r["date_iso"], str)
        assert "description" in r and isinstance(r["description"], str)
        assert "debit_paise" in r and isinstance(r["debit_paise"], int)
        assert "credit_paise" in r and isinstance(r["credit_paise"], int)
        assert "balance_paise" in r and isinstance(r["balance_paise"], int)
        assert "bank" in r and isinstance(r["bank"], str)


# ============================================================
# compute_account_balance Tests
# ============================================================

class TestComputeAccountBalance:
    """Integration tests for single account balance."""

    def test_compute_account_balance_aggregation(self, temp_db_with_data):
        """SQL SUM aggregation matches manual iteration."""
        result = compute_account_balance(temp_db_with_data, "HDFC")

        # Manual: 5000000 + 1000000 - 1500000 - 50000 = 4450000
        assert result["balance_paise"] == 4450000
        assert result["total_credit_paise"] == 6000000
        assert result["total_debit_paise"] == 1550000
        assert result["transaction_count"] == 4

    def test_compute_account_balance_display_format(self, temp_db_with_data):
        """balance_display matches _format_paise(balance_paise)."""
        result = compute_account_balance(temp_db_with_data, "HDFC")
        expected_display = _format_paise(result["balance_paise"])
        assert result["balance_display"] == expected_display

    def test_compute_account_balance_zero_transactions(self, temp_db_with_data):
        """Account with statement but no transactions returns starting balance."""
        # SBI has transactions, so add a new empty account
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute("INSERT INTO statements (id, bank, file_name) VALUES (4, 'EMPTY_BANK', 'empty.pdf')")
        conn.commit()
        conn.close()

        result = compute_account_balance(temp_db_with_data, "EMPTY_BANK")
        assert result["balance_paise"] == 0
        assert result["transaction_count"] == 0
        assert result["total_credit_paise"] == 0
        assert result["total_debit_paise"] == 0


# ============================================================
# validate_statement_balance Tests
# ============================================================

class TestValidateStatementBalance:
    """Integration tests for statement balance validation."""

    def test_validate_statement_balance_match(self, temp_db_with_data):
        """Matching claimed balance returns 'match' status."""
        # HDFC statement_id=1: net = 5000000 + 1000000 - 1500000 - 50000 = 4450000
        result = validate_statement_balance(temp_db_with_data, 1, 4450000)

        assert result["status"] == "match"
        assert result["computed_balance_paise"] == 4450000
        assert result["claimed_balance_paise"] == 4450000
        assert result["difference_paise"] == 0
        assert result["difference_display"] == "₹0.00"

    def test_validate_statement_balance_mismatch(self, temp_db_with_data):
        """Mismatched claimed balance returns 'mismatch' with correct difference."""
        result = validate_statement_balance(temp_db_with_data, 1, 5000000)

        assert result["status"] == "mismatch"
        assert result["computed_balance_paise"] == 4450000
        assert result["claimed_balance_paise"] == 5000000
        assert result["difference_paise"] == 550000
        assert result["difference_display"] == _format_paise(550000)

    def test_validate_statement_balance_display_fields(self, temp_db_with_data):
        """Display fields match _format_paise."""
        result = validate_statement_balance(temp_db_with_data, 1, 5000000)

        assert result["computed_balance_display"] == _format_paise(4450000)
        assert result["claimed_balance_display"] == _format_paise(5000000)
        assert result["difference_display"] == _format_paise(550000)

    def test_validate_statement_balance_txn_count(self, temp_db_with_data):
        """Transaction count matches transactions in statement."""
        result = validate_statement_balance(temp_db_with_data, 1, 4450000)
        assert result["transaction_count"] == 4


# ============================================================
# get_accounts_list Tests
# ============================================================

class TestGetAccountsList:
    """Integration tests for listing all accounts."""

    def test_get_accounts_list_multiple_accounts(self, temp_db_with_data):
        """All accounts returned with correct balances."""
        results = get_accounts_list(temp_db_with_data)

        banks = {r["bank"]: r for r in results}
        assert "HDFC" in banks
        assert "ICICI" in banks
        assert "SBI" in banks

        # HDFC: 5000000 + 1000000 - 1500000 - 50000 = 4450000
        assert banks["HDFC"]["balance_paise"] == 4450000
        # ICICI: 2000000 - 300000 = 1700000
        assert banks["ICICI"]["balance_paise"] == 1700000
        # SBI: 50000 - 20000 = 30000
        assert banks["SBI"]["balance_paise"] == 30000

    def test_get_accounts_list_empty_account(self, temp_db_with_data):
        """Account with statement but no transactions returns zero balance."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute("INSERT INTO statements (id, bank, file_name) VALUES (4, 'EMPTY_BANK', 'empty.pdf')")
        conn.commit()
        conn.close()

        results = get_accounts_list(temp_db_with_data)
        banks = {r["bank"]: r for r in results}

        assert "EMPTY_BANK" in banks
        assert banks["EMPTY_BANK"]["balance_paise"] == 0
        assert banks["EMPTY_BANK"]["transaction_count"] == 0

    def test_get_accounts_list_ordering(self, temp_db_with_data):
        """Results ordered by bank name alphabetically."""
        results = get_accounts_list(temp_db_with_data)
        banks = [r["bank"] for r in results]
        assert banks == sorted(banks)


# ============================================================
# _format_paise Tests
# ============================================================

class TestFormatPaise:
    """Tests for Indian rupee formatting with lakh/crores grouping."""

    @pytest.mark.parametrize("paise,expected", [
        (0, "₹0.00"),
        (1, "₹0.01"),
        (99, "₹0.99"),
        (100, "₹1.00"),
        (123, "₹1.23"),
        (10000, "₹100.00"),
        (100000, "₹1,000.00"),
        (1000000, "₹10,000.00"),
        (10000000, "₹1,00,000.00"),
        (100000000, "₹10,00,000.00"),
        (1000000000, "₹1,00,00,000.00"),
        (123456789, "₹12,34,567.89"),
        (999999999, "₹99,99,999.99"),
    ])
    def test_format_paise_indian_grouping(self, paise, expected):
        """Indian grouping: 3 digits, then 2-2-2... (lakhs, crores)."""
        assert _format_paise(paise) == expected

    def test_format_paise_negative(self):
        """Negative values get minus prefix."""
        assert _format_paise(-100) == "-₹1.00"
        assert _format_paise(-10000000) == "-₹1,00,000.00"

    def test_format_paise_zero(self):
        """Zero returns '₹0.00'."""
        assert _format_paise(0) == "₹0.00"
        assert _format_paise(-0) == "₹0.00"

    @pytest.mark.parametrize("paise", [1, 100, 12345, 1000000, 123456789])
    def test_format_paise_paise_portion_two_digits(self, paise):
        """Paise portion always exactly 2 digits (00-99)."""
        result = _format_paise(paise)
        # Find the decimal point and check 2 digits after
        parts = result.split(".")
        assert len(parts) == 2
        assert len(parts[1]) == 2
        assert parts[1].isdigit()