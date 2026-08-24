"""
Balance Engine Tests
====================

Tests for deterministic financial balance computation.
Covers date parsing, running balance, account balance, statement validation,
accounts list, and Indian rupee formatting.

Run: python -m pytest backend/tests/unit/engines/balance_engine.py -v
"""

import pytest
from src.engines.balance_engine import (
    _format_paise,
    _parse_date_for_sort,
    _parse_date_to_ymd,
    compute_account_balance,
    compute_running_balance,
    get_accounts_list,
    validate_statement_balance,
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

    @pytest.mark.parametrize(
        "input_date,expected_ymd",
        [
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
        ],
    )
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
        results = compute_running_balance(
            temp_db_with_data, "HDFC", starting_balance_paise=100000
        )

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
        results_zero = compute_running_balance(
            temp_db_with_data, "HDFC", starting_balance_paise=0
        )
        results_custom = compute_running_balance(
            temp_db_with_data, "HDFC", starting_balance_paise=100000
        )

        for r_zero, r_custom in zip(results_zero, results_custom, strict=True):
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

    def test_compute_running_balance_empty_account(self, temp_db_with_data):
        """Account with no transactions returns empty list."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (4, 'EMPTY_BANK', 'empty.pdf')"
        )
        conn.commit()
        conn.close()

        results = compute_running_balance(temp_db_with_data, "EMPTY_BANK")
        assert results == []

    def test_compute_running_balance_zero_value_transactions(self, temp_db_with_data):
        """Zero-value debit/credit transactions handled correctly."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (5, 'ZERO_BANK', 'zero.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (5, '01/01/2025', '2025-01-01', 'Zero Credit', 0, 'credit', 'ZERO_BANK', 'hash_z1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (5, '02/01/2025', '2025-01-02', 'Zero Debit', 0, 'debit', 'ZERO_BANK', 'hash_z2', 1)"
        )
        conn.commit()
        conn.close()

        results = compute_running_balance(temp_db_with_data, "ZERO_BANK")
        assert len(results) == 2
        assert results[0]["balance_paise"] == 0
        assert results[1]["balance_paise"] == 0

    def test_compute_running_balance_negative_balance(self, temp_db_with_data):
        """Running balance can go negative when debits exceed credits."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (6, 'NEG_BANK', 'neg.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (6, '01/01/2025', '2025-01-01', 'Large Debit', 1000000, 'debit', 'NEG_BANK', 'hash_n1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (6, '02/01/2025', '2025-01-02', 'Small Credit', 100000, 'credit', 'NEG_BANK', 'hash_n2', 1)"
        )
        conn.commit()
        conn.close()

        results = compute_running_balance(temp_db_with_data, "NEG_BANK")
        assert len(results) == 2
        assert results[0]["balance_paise"] == -1000000
        assert results[1]["balance_paise"] == -900000

    def test_compute_running_balance_debit_credit_handling(self, temp_db_with_data):
        """Debit decreases balance, credit increases balance."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (7, 'DC_BANK', 'dc.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (7, '01/01/2025', '2025-01-01', 'Credit 1000', 100000, 'credit', 'DC_BANK', 'hash_dc1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (7, '02/01/2025', '2025-01-02', 'Debit 500', 50000, 'debit', 'DC_BANK', 'hash_dc2', 1)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (7, '03/01/2025', '2025-01-03', 'Credit 200', 20000, 'credit', 'DC_BANK', 'hash_dc3', 2)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (7, '04/01/2025', '2025-01-04', 'Debit 300', 30000, 'debit', 'DC_BANK', 'hash_dc4', 3)"
        )
        conn.commit()
        conn.close()

        results = compute_running_balance(temp_db_with_data, "DC_BANK")
        assert len(results) == 4
        # 100000 - 50000 + 20000 - 30000 = 40000
        assert results[-1]["balance_paise"] == 40000

    def test_compute_running_balance_no_account_filter(self, temp_db_with_data):
        """Running balance without account filter returns all transactions."""
        results = compute_running_balance(temp_db_with_data)
        # All transactions: HDFC(4) + ICICI(2) + SBI(2) = 8
        assert len(results) == 8
        # Note: NULL date_iso sorts first in SQL, so SBI transactions appear first
        # The fallback parsing in Python happens after SQL ordering
        dates = [r["date_iso"] for r in results]
        # Verify all dates are valid (non-empty)
        for d in dates:
            assert d != ""
        # Verify SBI transactions (which had NULL date_iso) get parsed dates
        sbi_dates = [r["date_iso"] for r in results if r["bank"] == "SBI"]
        assert "2025-01-03" in sbi_dates
        assert "2025-01-12" in sbi_dates

    def test_compute_running_balance_secondary_id_ordering(self, temp_db_with_data):
        """Same date transactions ordered by transaction ID."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (8, 'ID_ORDER', 'id.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (8, '01/01/2025', '2025-01-01', 'First', 100000, 'credit', 'ID_ORDER', 'hash_io1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (8, '01/01/2025', '2025-01-01', 'Second', 200000, 'credit', 'ID_ORDER', 'hash_io2', 1)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (8, '01/01/2025', '2025-01-01', 'Third', 300000, 'credit', 'ID_ORDER', 'hash_io3', 2)"
        )
        conn.commit()
        conn.close()

        results = compute_running_balance(temp_db_with_data, "ID_ORDER")
        assert len(results) == 3
        # Should be ordered by id ASC (sequence_num)
        assert results[0]["description"] == "First"
        assert results[1]["description"] == "Second"
        assert results[2]["description"] == "Third"


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
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (4, 'EMPTY_BANK', 'empty.pdf')"
        )
        conn.commit()
        conn.close()

        result = compute_account_balance(temp_db_with_data, "EMPTY_BANK")
        assert result["balance_paise"] == 0
        assert result["transaction_count"] == 0
        assert result["total_credit_paise"] == 0
        assert result["total_debit_paise"] == 0

    def test_compute_account_balance_only_credits(self, temp_db_with_data):
        """Account with only credit transactions."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (5, 'CREDIT_ONLY', 'credit.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (5, '01/01/2025', '2025-01-01', 'Salary', 5000000, 'credit', 'CREDIT_ONLY', 'hash_c1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (5, '15/01/2025', '2025-01-15', 'Bonus', 1000000, 'credit', 'CREDIT_ONLY', 'hash_c2', 1)"
        )
        conn.commit()
        conn.close()

        result = compute_account_balance(temp_db_with_data, "CREDIT_ONLY")
        assert result["balance_paise"] == 6000000
        assert result["total_credit_paise"] == 6000000
        assert result["total_debit_paise"] == 0
        assert result["transaction_count"] == 2

    def test_compute_account_balance_only_debits(self, temp_db_with_data):
        """Account with only debit transactions."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (6, 'DEBIT_ONLY', 'debit.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (6, '01/01/2025', '2025-01-01', 'Rent', 1500000, 'debit', 'DEBIT_ONLY', 'hash_d1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (6, '10/01/2025', '2025-01-10', 'EMI', 300000, 'debit', 'DEBIT_ONLY', 'hash_d2', 1)"
        )
        conn.commit()
        conn.close()

        result = compute_account_balance(temp_db_with_data, "DEBIT_ONLY")
        assert result["balance_paise"] == -1800000
        assert result["total_credit_paise"] == 0
        assert result["total_debit_paise"] == 1800000
        assert result["transaction_count"] == 2

    def test_compute_account_balance_zero_values(self, temp_db_with_data):
        """Account with zero-value transactions."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (7, 'ZERO_BANK', 'zero.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (7, '01/01/2025', '2025-01-01', 'Zero Credit', 0, 'credit', 'ZERO_BANK', 'hash_z1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (7, '02/01/2025', '2025-01-02', 'Zero Debit', 0, 'debit', 'ZERO_BANK', 'hash_z2', 1)"
        )
        conn.commit()
        conn.close()

        result = compute_account_balance(temp_db_with_data, "ZERO_BANK")
        assert result["balance_paise"] == 0
        assert result["total_credit_paise"] == 0
        assert result["total_debit_paise"] == 0
        assert result["transaction_count"] == 2

    def test_compute_account_balance_negative_result(self, temp_db_with_data):
        """Negative resulting balance is correctly computed and displayed."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (8, 'NEG_BALANCE', 'neg.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (8, '01/01/2025', '2025-01-01', 'Large Expense', 2000000, 'debit', 'NEG_BALANCE', 'hash_n1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (8, '02/01/2025', '2025-01-02', 'Small Income', 500000, 'credit', 'NEG_BALANCE', 'hash_n2', 1)"
        )
        conn.commit()
        conn.close()

        result = compute_account_balance(temp_db_with_data, "NEG_BALANCE")
        assert result["balance_paise"] == -1500000
        assert result["balance_display"] == "-₹15,000.00"

    def test_compute_account_balance_starting_balance(self, temp_db_with_data):
        """Starting balance is added to computed balance."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (9, 'START_BAL', 'start.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (9, '01/01/2025', '2025-01-01', 'Income', 1000000, 'credit', 'START_BAL', 'hash_s1', 0)"
        )
        conn.commit()
        conn.close()

        result_zero = compute_account_balance(
            temp_db_with_data, "START_BAL", starting_balance_paise=0
        )
        result_custom = compute_account_balance(
            temp_db_with_data, "START_BAL", starting_balance_paise=500000
        )

        assert result_custom["balance_paise"] == result_zero["balance_paise"] + 500000
        assert result_custom["balance_display"] == _format_paise(
            result_custom["balance_paise"]
        )

    def test_compute_account_balance_account_isolation(self, temp_db_with_data):
        """Account balance is isolated per account_id."""
        hdfc_result = compute_account_balance(temp_db_with_data, "HDFC")
        icici_result = compute_account_balance(temp_db_with_data, "ICICI")

        assert hdfc_result["balance_paise"] == 4450000
        assert icici_result["balance_paise"] == 1700000
        assert hdfc_result["account_id"] == "HDFC"
        assert icici_result["account_id"] == "ICICI"

    def test_compute_account_balance_aggregation_correctness(self, temp_db_with_data):
        """Aggregated totals match sum of individual transactions."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (10, 'AGG_TEST', 'agg.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (10, '01/01/2025', '2025-01-01', 'T1', 100000, 'credit', 'AGG_TEST', 'hash_a1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (10, '02/01/2025', '2025-01-02', 'T2', 200000, 'credit', 'AGG_TEST', 'hash_a2', 1)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (10, '03/01/2025', '2025-01-03', 'T3', 50000, 'debit', 'AGG_TEST', 'hash_a3', 2)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (10, '04/01/2025', '2025-01-04', 'T4', 30000, 'debit', 'AGG_TEST', 'hash_a4', 3)"
        )
        conn.commit()
        conn.close()

        result = compute_account_balance(temp_db_with_data, "AGG_TEST")
        assert result["total_credit_paise"] == 300000
        assert result["total_debit_paise"] == 80000
        assert result["balance_paise"] == 220000
        assert result["transaction_count"] == 4


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

    def test_validate_statement_balance_zero_difference(self, temp_db_with_data):
        """Zero difference returns 'match' with zero difference display."""
        result = validate_statement_balance(temp_db_with_data, 1, 4450000)
        assert result["status"] == "match"
        assert result["difference_paise"] == 0
        assert result["difference_display"] == "₹0.00"

    def test_validate_statement_balance_one_paise_difference(self, temp_db_with_data):
        """Single paise difference correctly detected."""
        result = validate_statement_balance(temp_db_with_data, 1, 4450001)
        assert result["status"] == "mismatch"
        assert result["difference_paise"] == 1
        assert result["difference_display"] == "₹0.01"

    def test_validate_statement_balance_minus_one_paise(self, temp_db_with_data):
        """Single paise under claimed balance."""
        result = validate_statement_balance(temp_db_with_data, 1, 4449999)
        assert result["status"] == "mismatch"
        assert result["difference_paise"] == 1
        assert result["difference_display"] == "₹0.01"

    def test_validate_statement_balance_large_values(self, temp_db_with_data):
        """Large balance values handled correctly."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (4, 'LARGE_BANK', 'large.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (4, '01/01/2025', '2025-01-01', 'Large Credit', 1000000000, 'credit', 'LARGE_BANK', 'hash_l1', 0)"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (4, '02/01/2025', '2025-01-02', 'Large Debit', 500000000, 'debit', 'LARGE_BANK', 'hash_l2', 1)"
        )
        conn.commit()
        conn.close()

        # Net: 1000000000 - 500000000 = 500000000 (₹50,00,000.00)
        result = validate_statement_balance(temp_db_with_data, 4, 500000000)
        assert result["status"] == "match"
        assert result["computed_balance_paise"] == 500000000
        assert result["difference_paise"] == 0

    def test_validate_statement_balance_no_transactions(self, temp_db_with_data):
        """Statement with no transactions validates against zero."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (5, 'EMPTY_STMT', 'empty.pdf')"
        )
        conn.commit()
        conn.close()

        result = validate_statement_balance(temp_db_with_data, 5, 0)
        assert result["status"] == "match"
        assert result["computed_balance_paise"] == 0
        assert result["transaction_count"] == 0

    def test_validate_statement_balance_display_formatting(self, temp_db_with_data):
        """All display fields use _format_paise consistently."""
        result = validate_statement_balance(temp_db_with_data, 1, 5000000)
        assert result["computed_balance_display"] == _format_paise(4450000)
        assert result["claimed_balance_display"] == _format_paise(5000000)
        assert result["difference_display"] == _format_paise(550000)


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
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (4, 'EMPTY_BANK', 'empty.pdf')"
        )
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

    def test_get_accounts_list_credit_debit_aggregation(self, temp_db_with_data):
        """Credit and debit totals correctly aggregated per account."""
        results = get_accounts_list(temp_db_with_data)
        banks = {r["bank"]: r for r in results}

        # HDFC: credits=6000000, debits=1550000
        assert banks["HDFC"]["total_credit_paise"] == 6000000
        assert banks["HDFC"]["total_debit_paise"] == 1550000

        # ICICI: credits=2000000, debits=300000
        assert banks["ICICI"]["total_credit_paise"] == 2000000
        assert banks["ICICI"]["total_debit_paise"] == 300000

        # SBI: credits=50000, debits=20000
        assert banks["SBI"]["total_credit_paise"] == 50000
        assert banks["SBI"]["total_debit_paise"] == 20000

    def test_get_accounts_list_balance_calculation(self, temp_db_with_data):
        """Balance = total_credit - total_debit (assuming 0 starting balance)."""
        results = get_accounts_list(temp_db_with_data)
        for r in results:
            expected_balance = r["total_credit_paise"] - r["total_debit_paise"]
            assert r["balance_paise"] == expected_balance
            assert r["balance_display"] == _format_paise(expected_balance)

    def test_get_accounts_list_empty_account_balance(self, temp_db_with_data):
        """Account with statement but no transactions has zero balance."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (4, 'EMPTY_BANK', 'empty.pdf')"
        )
        conn.commit()
        conn.close()

        results = get_accounts_list(temp_db_with_data)
        banks = {r["bank"]: r for r in results}

        assert "EMPTY_BANK" in banks
        assert banks["EMPTY_BANK"]["balance_paise"] == 0
        assert banks["EMPTY_BANK"]["total_credit_paise"] == 0
        assert banks["EMPTY_BANK"]["total_debit_paise"] == 0
        assert banks["EMPTY_BANK"]["transaction_count"] == 0

    def test_get_accounts_list_multiple_accounts_structure(self, temp_db_with_data):
        """Each account entry has all required fields with correct types."""
        results = get_accounts_list(temp_db_with_data)
        for r in results:
            assert "account_id" in r and isinstance(r["account_id"], str)
            assert "bank" in r and isinstance(r["bank"], str)
            assert "transaction_count" in r and isinstance(r["transaction_count"], int)
            assert "total_debit_paise" in r and isinstance(r["total_debit_paise"], int)
            assert "total_credit_paise" in r and isinstance(
                r["total_credit_paise"], int
            )
            assert "balance_paise" in r and isinstance(r["balance_paise"], int)
            assert "balance_display" in r and isinstance(r["balance_display"], str)

    def test_get_accounts_list_negative_balance_display(self, temp_db_with_data):
        """Negative balances displayed correctly in accounts list."""
        from src.core.db.connection import get_connection

        conn = get_connection(temp_db_with_data)
        conn.execute(
            "INSERT INTO statements (id, bank, file_name) VALUES (5, 'OVERDRAFT', 'over.pdf')"
        )
        conn.execute(
            "INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id, hash_signature, sequence_num) VALUES (5, '01/01/2025', '2025-01-01', 'Overdraft', 500000, 'debit', 'OVERDRAFT', 'hash_o1', 0)"
        )
        conn.commit()
        conn.close()

        results = get_accounts_list(temp_db_with_data)
        banks = {r["bank"]: r for r in results}

        assert "OVERDRAFT" in banks
        assert banks["OVERDRAFT"]["balance_paise"] == -500000
        assert banks["OVERDRAFT"]["balance_display"] == "-₹5,000.00"


# ============================================================
# _format_paise Tests
# ============================================================


class TestFormatPaise:
    """Tests for Indian rupee formatting with lakh/crores grouping."""

    @pytest.mark.parametrize(
        "paise,expected",
        [
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
        ],
    )
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

    def test_format_paise_exact_lakh_boundary(self):
        """Exactly 1 lakh (100,000) formats correctly."""
        assert _format_paise(10000000) == "₹1,00,000.00"

    def test_format_paise_exact_crore_boundary(self):
        """Exactly 1 crore (10,000,000) formats correctly."""
        assert _format_paise(1000000000) == "₹1,00,00,000.00"

    def test_format_paise_large_crores(self):
        """Multiple crores format correctly."""
        assert _format_paise(12345678900) == "₹12,34,56,789.00"

    def test_format_paise_no_floating_point(self):
        """No floating-point arithmetic used internally."""
        # Large value that would cause float precision issues if floats were used
        result = _format_paise(999999999)
        assert result == "₹99,99,999.99"
        # Verify no float rounding by checking exact integer math
        # 1000000000000 paise = 10000000000 rupees = 10,000 crores
        assert _format_paise(1000000000000) == "₹10,00,00,00,000.00"
