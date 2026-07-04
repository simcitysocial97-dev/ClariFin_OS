#!/usr/bin/env python3
"""
Simple Transaction Classification Script
========================================

Standalone script to classify transactions and persist results.
Doesn't depend on complex import structure.
"""

import sqlite3
from enum import Enum
from typing import Dict, List, Tuple

class TransactionNature(str, Enum):
    """Transaction nature classification."""
    REAL_INCOME = "real_income"
    REAL_EXPENSE = "real_expense"
    DEBT_RECYCLING_IN = "recycling_in"
    DEBT_RECYCLING_OUT = "recycling_out"
    RECYCLING_FEE = "recycling_fee"
    INTEREST_CHARGE = "interest_charge"
    INTER_ACCOUNT = "inter_account"
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    UNKNOWN = "unknown"

def classify_transaction(txn: Dict) -> str:
    """
    Classify a transaction by its true nature.

    Args:
        txn: Transaction dictionary

    Returns:
        TransactionNature enum value
    """
    description = (txn.get('description') or '').lower()
    amount = txn.get('amount_paise', 0)
    category = txn.get('category', '').lower()
    type_ = txn.get('type', '').lower()

    # REAL_INCOME: Salary, freelance, refunds
    if any(keyword in description for keyword in ['salary', 'freelance', 'refund', 'dividend', 'interest received']):
        return TransactionNature.REAL_INCOME

    # REAL_EXPENSE: Actual spending on goods/services
    expense_keywords = ['grocery', 'rent', 'utility', 'electricity', 'water', 'internet', 'phone', 'mobile']
    if any(keyword in description for keyword in expense_keywords):
        return TransactionNature.REAL_EXPENSE

    # Merchant categories that indicate real expenses
    expense_categories = ['groceries', 'rent', 'utilities', 'shopping', 'transport', 'entertainment', 'dining']
    if any(cat in category for cat in expense_categories):
        return TransactionNature.REAL_EXPENSE

    # Medical and education expenses
    medical_keywords = ['pharmacy', 'hospital', 'medicine', 'medical', 'health', 'apollo', 'diagnostic center']
    education_keywords = ['books', 'unacademy', 'byjus', 'school fee', 'tuition fee', 'online course', 'education', 'college fee']
    if any(keyword in description for keyword in medical_keywords) or any(keyword in description for keyword in education_keywords):
        return TransactionNature.REAL_EXPENSE

    # DEBT_RECYCLING_IN: Money arriving from credit recycling apps
    recycling_in_keywords = ['cheq', 'cred', 'spaid', 'paytm', 'phonepe', 'bhim upi']
    if (any(keyword in description for keyword in recycling_in_keywords) and
        amount > 0 and type_ == 'credit'):
        return TransactionNature.DEBT_RECYCLING_IN

    # DEBT_RECYCLING_OUT: Payments to credit cards
    cc_payment_keywords = ['credit card', 'cc bill', 'card payment', 'cc payment', 'cc bill payment', 'cc payment', 'auto debit']
    if (any(keyword in description for keyword in cc_payment_keywords) and
        amount < 0 and type_ == 'debit'):
        return TransactionNature.DEBT_RECYCLING_OUT

    # RECYCLING_FEE: Fees charged by recycling apps (typically 1-3%)
    fee_keywords = ['fee', 'charge', 'convenience', 'processing']
    if (any(keyword in description for keyword in fee_keywords) and
        any(app in description for app in ['cheq', 'cred', 'spaid'])):
        return TransactionNature.RECYCLING_FEE

    # INTEREST_CHARGE: Bank/credit card interest and fees
    interest_keywords = ['interest', 'finance charge', 'late fee', 'processing fee', 'penalty',
                       'gst', 'igst', 'cgst', 'annual fee', 'cash advance fee']
    if any(keyword in description for keyword in interest_keywords):
        return TransactionNature.INTEREST_CHARGE

    # INTER_ACCOUNT: Transfers between own accounts
    transfer_keywords = ['transfer', 'neft', 'imps', 'rtgs', 'upi', 'sweep']
    if any(keyword in description for keyword in transfer_keywords):
        return TransactionNature.INTER_ACCOUNT

    # CASH WITHDRAWALS
    cash_keywords = ['atm', 'cash withdrawal', 'atm wdl', 'cash -']
    if any(keyword in description for keyword in cash_keywords):
        return TransactionNature.REAL_EXPENSE

    # FAILED/REVERSED TRANSACTIONS (credits)
    failed_keywords = ['reversal', 'refund', 'transaction failed', 'payment reversal']
    if any(keyword in description for keyword in failed_keywords) and amount > 0:
        return TransactionNature.REAL_INCOME

    # LOAN_DISBURSEMENT: Loan money received (credits with loan keywords)
    if ('loan' in description and 'disbursement' in description and amount > 0) or \
       ('loan disbursed' in description and amount > 0) or \
       (any(keyword in description for keyword in ['home loan', 'car loan', 'personal loan', 'loan']) and type_ == 'credit'):
        return TransactionNature.LOAN_DISBURSEMENT

    # LOAN_REPAYMENT: EMI/loan payments (these are debits with positive amounts)
    repayment_keywords = ['emi', 'loan payment', 'loan repayment', 'home loan', 'car loan', 'personal loan', 'loan']
    if any(keyword in description for keyword in repayment_keywords) and type_ == 'debit':
        return TransactionNature.LOAN_REPAYMENT

    # Default: UNKNOWN (needs manual review)
    return TransactionNature.UNKNOWN

def run_classification(db_path: str = "backend/data/finance.db") -> None:
    """Run classification and persist results."""
    print(f"🔍 Classifying transactions in {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Get transactions needing classification
        cursor = conn.execute("""
            SELECT id, date, description, amount_paise, type, category, account_id
            FROM transactions
            WHERE nature IS NULL OR nature = 'unknown'
        """)
        transactions = cursor.fetchall()

        print(f"📊 Found {len(transactions)} transactions to classify")

        if not transactions:
            print("✅ No transactions need classification")
            return

        # Classify and prepare updates
        updates = []
        counts = {}

        for txn in transactions:
            nature = classify_transaction(dict(txn))
            updates.append((nature, txn['id']))
            counts[nature] = counts.get(nature, 0) + 1

        # Persist to database
        if updates:
            conn.executemany("UPDATE transactions SET nature = ? WHERE id = ?", updates)
            conn.commit()
            print(f"✅ Classified and saved {len(updates)} transactions")

            # Show results
            print("\n📈 Classification Results:")
            for nature, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {nature:20s}: {count:3d} transactions")
        else:
            print("✅ No updates needed")

    finally:
        conn.close()

def verify_results(db_path: str = "backend/data/finance.db") -> None:
    """Verify classification results."""
    print("\n🔎 Verifying classification results...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Summary by nature
        cursor = conn.execute("""
            SELECT nature, COUNT(*) as count,
                   ROUND(SUM(ABS(amount_paise))/100.0, 2) as total_inr
            FROM transactions
            GROUP BY nature
            ORDER BY total_inr DESC
        """)
        results = cursor.fetchall()

        print("\n📊 Classification Summary:")
        print(f"{'NATURE':<20} {'COUNT':>8} {'TOTAL (₹)':>15}")
        print("-" * 48)

        total_count = 0
        total_amount = 0.0

        for row in results:
            print(f"{row['nature']:<20} {row['count']:>8} {row['total_inr']:>15.2f}")
            total_count += row['count']
            total_amount += row['total_inr']

        print("-" * 48)
        print(f"{'TOTAL':<20} {total_count:>8} {total_amount:>15.2f}")

        # Check salary classification
        print("\n💰 Salary Transactions:")
        cursor = conn.execute("""
            SELECT date, description, amount_paise/100.0 as amount_inr, nature
            FROM transactions
            WHERE description LIKE '%SALARY%' OR description LIKE '%salary%'
            ORDER BY date DESC
            LIMIT 5
        """)
        for txn in cursor.fetchall():
            print(f"  {txn['date']} | {txn['description']:<30} | ₹{txn['amount_inr']:>10.2f} | {txn['nature']}")

        # Check recycling classification
        print("\n🔄 Recycling Transactions:")
        cursor = conn.execute("""
            SELECT date, description, amount_paise/100.0 as amount_inr, nature
            FROM transactions
            WHERE description LIKE '%CHEQ%' OR description LIKE '%SPAID%'
               OR description LIKE '%CRED%' OR description LIKE '%CREDIT CARD%'
            ORDER BY date DESC
            LIMIT 5
        """)
        for txn in cursor.fetchall():
            print(f"  {txn['date']} | {txn['description']:<30} | ₹{txn['amount_inr']:>10.2f} | {txn['nature']}")

    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting Transaction Classification")
    print("=" * 50)

    # Run classification
    run_classification()

    # Verify results
    verify_results()

    print("\n✅ Classification complete!")