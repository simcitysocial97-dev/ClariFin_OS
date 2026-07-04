"""
True Net Cash Flow Engine
==========================

Computes true net income by excluding debt recycling activities
(Cheq/Cred/Spaid cycles) from income calculations.

This provides the "real" financial picture vs the "accounting" picture.
"""

from typing import Dict, List, Optional
from src.db.core import FinanceDB
from src.engines.transaction_classifier import TransactionNature, classify_transaction
from src.logger import log

def compute_true_monthly_cashflow(db: FinanceDB, month: str) -> dict:
    """
    Calculate real net income excluding recycled money.

    Formula:
    true_net_income = 
        sum(REAL_INCOME) 
        - sum(REAL_EXPENSE)
        - sum(RECYCLING_FEE)
        - sum(INTEREST_CHARGE)

    Args:
        db: FinanceDB instance
        month: Month in YYYY-MM format

    Returns:
        Dict with true net income calculation and breakdown
    """
    log.info("Computing true monthly cashflow for %s", month)

    with db.connection() as conn:
        # Get all transactions for the month
        cur = conn.execute("""
            SELECT * FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
            ORDER BY date_iso
        """, (month,))
        transactions = [dict(row) for row in cur.fetchall()]

    # Classify transactions by nature
    classified = {}
    for txn in transactions:
        nature = classify_transaction(txn, db)
        classified.setdefault(nature, []).append(txn)

    # Calculate amounts by nature
    real_income = sum(abs(t.get('credit', 0)) for t in classified.get(TransactionNature.REAL_INCOME, []))
    real_expense = sum(abs(t.get('debit', 0)) for t in classified.get(TransactionNature.REAL_EXPENSE, []))
    recycling_fees = sum(abs(t.get('debit', 0)) for t in classified.get(TransactionNature.RECYCLING_FEE, []))
    interest_charged = sum(abs(t.get('debit', 0)) for t in classified.get(TransactionNature.INTEREST_CHARGE, []))

    # True net income calculation
    true_net_income = real_income - real_expense - recycling_fees - interest_charged

    # Additional metrics
    total_recycled_volume = sum(abs(t.get('credit', 0)) for t in classified.get(TransactionNature.DEBT_RECYCLING_IN, []))
    recycling_count = len(classified.get(TransactionNature.DEBT_RECYCLING_IN, []))

    # Breakdown by nature
    breakdown_by_nature = {
        nature: sum(abs(t.get('credit', 0) if t.get('type') == 'credit' else t.get('debit', 0))
                   for t in txns)
        for nature, txns in classified.items()
    }

    result = {
        "month": month,
        "real_income_paise": real_income,
        "real_expense_paise": real_expense,
        "recycling_fees_paise": recycling_fees,
        "interest_charged_paise": interest_charged,
        "true_net_income_paise": true_net_income,
        "total_recycled_volume_paise": total_recycled_volume,
        "recycling_count": recycling_count,
        "breakdown_by_nature": breakdown_by_nature,
        "transaction_counts_by_nature": {
            nature: len(txns)
            for nature, txns in classified.items()
        }
    }

    log.info("True monthly cashflow computed for %s: Real Income=₹%.2f, True Net=₹%.2f",
            month, real_income/100, true_net_income/100)
    return result