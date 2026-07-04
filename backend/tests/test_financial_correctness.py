"""
Financial Correctness Tests
These tests verify that the NUMBERS are right, not just that endpoints respond.
"""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta


def test_salary_classified_as_real_income():
    from src.engines.transaction_classifier import classify_transaction
    salary_descriptions = [
        "SALARY CREDIT", "SALARY - TECHCORP PVT LTD",
        "MONTHLY SALARY", "SALARY FOR APRIL 2025", "NEFT CR-SALARY-",
    ]
    for desc in salary_descriptions:
        result = classify_transaction({
            'description': desc, 'amount_paise': 6000000,
            'transaction_type': 'credit', 'account_id': 1, 'category': None
        })
        assert result == 'real_income', f"'{desc}' should be real_income, got {result}"


def test_recycling_apps_classified_as_recycling_in():
    from src.engines.transaction_classifier import classify_transaction
    recycling_descriptions = [
        "UPI-CHEQ TECHNOLOGIES-9876543210", "NEFT CR-SPAID FINTECH-20250125",
        "UPI-CRED CLUB-PAYMENT", "CHEQ - CREDIT", "SPAID - CREDIT",
    ]
    for desc in recycling_descriptions:
        result = classify_transaction({
            'description': desc, 'amount_paise': 2418400,
            'transaction_type': 'credit', 'account_id': 1, 'category': None
        })
        assert result == 'recycling_in', f"'{desc}' should be recycling_in, got {result}"


def test_true_net_income_formula(db_path):
    from src.engines.cashflow_engine_true_net import compute_true_monthly_cashflow
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    months = conn.execute("""
        SELECT strftime('%Y-%m', date) as month FROM transactions
        WHERE nature != 'unknown' GROUP BY month
        HAVING COUNT(*) > 10 ORDER BY month DESC LIMIT 1
    """).fetchone()
    if not months: pytest.skip("No classified transactions in database")
    month = months['month']
    sql_result = conn.execute("""
        SELECT SUM(CASE WHEN nature='real_income' AND amount_paise > 0 THEN amount_paise ELSE 0 END) as real_income,
               SUM(CASE WHEN nature='real_expense' AND amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END) as real_expense,
               SUM(CASE WHEN nature='recycling_fee' AND amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END) as recycling_fees,
               SUM(CASE WHEN nature='interest_charge' AND amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END) as interest_charged
        FROM transactions WHERE strftime('%Y-%m', date) = ?
    """, (month,)).fetchone()
    conn.close()
    from src.db.core import FinanceDB
    db = FinanceDB(db_path)
    api_result = compute_true_monthly_cashflow(db, month)
    expected_net = ((sql_result['real_income'] or 0) - (sql_result['real_expense'] or 0) -
                    (sql_result['recycling_fees'] or 0) - (sql_result['interest_charged'] or 0))
    assert api_result['true_net_income_paise'] == expected_net, \
        f"True net income mismatch for {month}: expected {expected_net}, got {api_result['true_net_income_paise']}"


def test_recycling_not_counted_as_income(db_path):
    from src.engines.cashflow_engine_true_net import compute_true_monthly_cashflow
    from src.db.core import FinanceDB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    recycling_month = conn.execute("""
        SELECT strftime('%Y-%m', date_iso) as month,
               SUM(CASE WHEN nature='recycling_in' THEN amount_paise ELSE 0 END) as recycling_total
        FROM transactions WHERE date_iso IS NOT NULL AND date_iso != ''
        GROUP BY strftime('%Y-%m', date_iso) HAVING recycling_total > 0 ORDER BY month DESC LIMIT 1
    """).fetchone()
    conn.close()
    if not recycling_month: pytest.skip("No recycling transactions found")
    month = recycling_month['month']; recycling_total = recycling_month['recycling_total']
    if not month: pytest.skip("No valid month found for recycling transactions")
    db = FinanceDB(db_path)
    result = compute_true_monthly_cashflow(db, month)
    assert result['real_income_paise'] != recycling_total, \
        f"Recycling amount is being counted as real income in {month}"


def test_cashflow_totals_match_database(db_path):
    from src.engines.cashflow_engine import compute_monthly_cashflow
    from src.db.core import FinanceDB
    today = datetime.now()
    cutoff_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    for _ in range(11): cutoff_date = (cutoff_date - timedelta(days=1)).replace(day=1)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    month_row = conn.execute("""
        SELECT strftime('%Y-%m', date_iso) as month, COUNT(*) as cnt
        FROM transactions WHERE date_iso IS NOT NULL AND date_iso != ''
        AND date_iso >= ? GROUP BY month ORDER BY cnt DESC LIMIT 1
    """, (cutoff_str,)).fetchone()
    if not month_row: conn.close(); pytest.skip("No transactions in engine's view window")
    month = month_row['month']
    sql_totals = conn.execute("""
        SELECT SUM(CASE WHEN amount_paise > 0 THEN amount_paise ELSE 0 END) as credits,
               SUM(CASE WHEN amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END) as debits
        FROM transactions WHERE strftime('%Y-%m', date_iso) = ? AND date_iso >= ?
    """, (month, cutoff_str)).fetchone()
    conn.close()
    db = FinanceDB(db_path)
    engine_result = compute_monthly_cashflow(db, months=12)
    month_data = next((m for m in engine_result if m.get('month') == month), None)
    if not month_data: pytest.skip(f"Month {month} not found in engine results")
    engine_credits = month_data.get('total_income_paise', 0)
    engine_debits = month_data.get('total_expense_paise', 0)
    assert engine_credits == sql_totals['credits'], \
        f"Credit mismatch for {month}: engine={engine_credits}, sql={sql_totals['credits']}"
    assert engine_debits == sql_totals['debits'], \
        f"Debit mismatch for {month}: engine={engine_debits}, sql={sql_totals['debits']}"


def test_no_infinity_in_projections(finance_db):
    from src.engines.projection_engine import project_net_worth
    import math
    result = project_net_worth(finance_db, months_ahead=12)
    def check_no_infinity(obj, path=""):
        if isinstance(obj, float):
            assert not math.isinf(obj), f"Infinity at {path}"
            assert not math.isnan(obj), f"NaN at {path}"
            assert obj != 999.0, f"Sentinel 999.0 at {path}"
        elif isinstance(obj, dict):
            for k, v in obj.items(): check_no_infinity(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj): check_no_infinity(v, f"{path}[{i}]")
    check_no_infinity(result)


def test_immutability_trigger_surgical(db_path):
    conn = sqlite3.connect(db_path)
    txn = conn.execute("SELECT id, nature, amount_paise FROM transactions WHERE id >= 83 LIMIT 1").fetchone()
    if not txn: pytest.skip("No transactions")
    txn_id, original_nature, original_amount = txn
    try:
        conn.execute("UPDATE transactions SET nature = 'test_audit' WHERE id = ?", (txn_id,))
        conn.commit()
        conn.execute("UPDATE transactions SET nature = ? WHERE id = ?", (original_nature, txn_id))
        conn.commit()
        nature_ok = True
    except Exception as e:
        nature_ok = False; nature_error = str(e)
    try:
        conn.execute("UPDATE transactions SET amount_paise = ? WHERE id = ?", (original_amount + 1, txn_id))
        conn.commit()
        amount_blocked = False
    except Exception:
        amount_blocked = True
    conn.close()
    assert nature_ok, f"Nature update failed (trigger too strict): {nature_error}"
    assert amount_blocked, "Amount update was not blocked (immutability broken)"


def test_import_pipeline_classifies_transactions(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    salary_unknown = conn.execute("""
        SELECT COUNT(*) as cnt FROM transactions
        WHERE (description LIKE '%SALARY%' OR description LIKE '%salary%') AND nature = 'unknown'
    """).fetchone()['cnt']
    conn.close()
    assert salary_unknown == 0, f"{salary_unknown} salary transactions still unknown."


def test_net_worth_matches_accounts(db_path):
    from src.engines.networth_engine import compute_net_worth
    from src.db.core import FinanceDB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    sql_result = conn.execute("""
        SELECT SUM(CASE WHEN account_type NOT IN ('credit_card','loan') THEN COALESCE(balance_paise,0) ELSE 0 END) as assets
        FROM accounts WHERE is_active = 1
    """).fetchone()
    conn.close()
    db = FinanceDB(db_path)
    engine_assets = compute_net_worth(db).get('total_assets_paise', 0)
    assert engine_assets == (sql_result['assets'] or 0), \
        f"Asset mismatch: engine={engine_assets}, sql={sql_result['assets']}"


def test_known_patterns_not_unknown(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    must_classify = [("SALARY", "real_income"), ("CHEQ", "recycling_in"), ("SPAID", "recycling_in"),
                     ("INTEREST CHARGED", "interest_charge"), ("ANNUAL FEE", "interest_charge")]
    failures = []
    for pattern, expected in must_classify:
        count = conn.execute("SELECT COUNT(*) as cnt FROM transactions WHERE description LIKE ? AND nature = 'unknown'",
                             (f'%{pattern}%',)).fetchone()['cnt']
        if count > 0: failures.append(f"'{pattern}': {count} still 'unknown' (expected '{expected}')")
    conn.close()
    assert not failures, "Known patterns misclassified:\n" + "\n".join(failures)


def test_credit_debit_match_amount_paise(db_path):
    """GENERATED ALWAYS columns must match amount_paise sign convention."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    discrepancies = conn.execute("""
        SELECT COUNT(*) as cnt FROM transactions
        WHERE credit != CASE WHEN amount_paise > 0 THEN amount_paise ELSE 0 END
        OR debit != CASE WHEN amount_paise < 0 THEN ABS(amount_paise) ELSE 0 END
    """).fetchone()['cnt']
    conn.close()
    assert discrepancies == 0, \
        f"{discrepancies} transactions have credit/debit mismatch. Schema integrity broken."