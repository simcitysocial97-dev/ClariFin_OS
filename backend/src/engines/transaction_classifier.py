"""
Transaction Classifier Engine
=============================

Classifies transactions by their true nature to distinguish between real income/expenses
and debt recycling activities (Cheq/Cred/Spaid cycles).

This is critical for accurate net worth calculation in scenarios with credit card
debt recycling patterns.
"""

from enum import Enum
from typing import Dict, Optional
from src.db.core import FinanceDB

class TransactionNature(str, Enum):
    """Transaction nature classification."""
    REAL_INCOME = "real_income"           # Salary, freelance, refunds
    REAL_EXPENSE = "real_expense"         # Groceries, rent, utilities, actual spending
    DEBT_RECYCLING_IN = "recycling_in"    # Money arriving from CC via Cheq/Cred/Spaid
    DEBT_RECYCLING_OUT = "recycling_out"  # Payment to CC from recycled money
    RECYCLING_FEE = "recycling_fee"       # The 1-3% Cheq/Cred charges
    INTEREST_CHARGE = "interest_charge"   # CC/loan interest, processing fees
    INTER_ACCOUNT = "inter_account"       # Transfer between own accounts
    LOAN_DISBURSEMENT = "loan_disbursement"  # Loan money received
    LOAN_REPAYMENT = "loan_repayment"     # EMI / loan payment
    UNKNOWN = "unknown"                   # Needs manual classification

def classify_transaction(txn: Dict, db: Optional[FinanceDB] = None) -> str:
    """
    Classify a transaction by its true nature.

    All inputs are normalized to safe types before processing.
    None values become empty strings. Numbers become strings.
    This function never raises AttributeError or TypeError.

    Args:
        txn: Transaction dictionary with description, amount_paise, type, category, etc.
        db: Optional FinanceDB instance for additional context

    Returns:
        TransactionNature enum value
    """
    # Normalize all inputs to safe types - this is the permanent fix
    description = str(txn.get('description') or '').lower().strip()
    category = str(txn.get('category') or '').lower().strip()
    type_ = str(txn.get('type') or txn.get('transaction_type') or '').lower().strip()
    amount = int(txn.get('amount_paise') or 0)
    account_id = txn.get('account_id')
    bank = str(txn.get('bank') or '').lower().strip()
    
    # All subsequent code uses these normalized local variables
    # Never access txn dict directly after this point

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

    # DEBT_RECYCLING_IN: Money arriving from credit recycling apps
    recycling_in_keywords = ['cheq', 'cred', 'spaid', 'paytm', 'phonepe', 'bhim upi']
    if (any(keyword in description for keyword in recycling_in_keywords) and
        amount > 0 and type_ == 'credit'):
        return TransactionNature.DEBT_RECYCLING_IN

    # DEBT_RECYCLING_OUT: Payments to credit cards
    cc_payment_keywords = ['credit card', 'cc bill', 'card payment', 'cc payment']
    if (any(keyword in description for keyword in cc_payment_keywords) and
        amount < 0 and type_ == 'debit'):
        return TransactionNature.DEBT_RECYCLING_OUT

    # RECYCLING_FEE: Fees charged by recycling apps (typically 1-3%)
    fee_keywords = ['fee', 'charge', 'convenience', 'processing']
    if (any(keyword in description for keyword in fee_keywords) and
        any(app in description for app in ['cheq', 'cred', 'spaid'])):
        return TransactionNature.RECYCLING_FEE

    # INTEREST_CHARGE: Bank/credit card interest and fees
    interest_keywords = ['interest', 'finance charge', 'late fee', 'processing fee', 'penalty']
    if any(keyword in description for keyword in interest_keywords):
        return TransactionNature.INTEREST_CHARGE

    # INTER_ACCOUNT: Transfers between own accounts
    transfer_keywords = ['transfer', 'neft', 'imps', 'rtgs', 'upi']
    if any(keyword in description for keyword in transfer_keywords):
        return TransactionNature.INTER_ACCOUNT

    # LOAN_DISBURSEMENT: Loan money received
    if 'loan' in description and 'disbursement' in description and amount > 0:
        return TransactionNature.LOAN_DISBURSEMENT

    # LOAN_REPAYMENT: EMI/loan payments
    repayment_keywords = ['emi', 'loan payment', 'loan repayment']
    if any(keyword in description for keyword in repayment_keywords) and amount < 0:
        return TransactionNature.LOAN_REPAYMENT

    # Default: UNKNOWN (needs manual review)
    return TransactionNature.UNKNOWN

def classify_all_transactions(db: FinanceDB) -> Dict[str, int]:
    """
    Classify all transactions and return counts by nature.

    Args:
        db: FinanceDB instance

    Returns:
        Dictionary with nature counts
    """
    transactions = db.get_all_transactions()
    counts = {nature.value: 0 for nature in TransactionNature}

    for txn in transactions:
        nature = classify_transaction(txn, db)
        counts[nature] += 1

    return counts

def get_transactions_by_nature(db: FinanceDB, nature: str) -> list:
    """
    Get all transactions of a specific nature.

    Args:
        db: FinanceDB instance
        nature: TransactionNature value

    Returns:
        List of matching transactions
    """
    transactions = db.get_all_transactions()
    return [txn for txn in transactions if classify_transaction(txn, db) == nature]