"""Income source analysis for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Income Sources (categories):
- SALARY: Regular employment income, payroll, wages, salaried
- BUSINESS: Business income, freelance, consulting, commission
- INVESTMENT: Investment returns, dividends, interest, capital gains
- TRANSFER: Internal transfers between own accounts
- REFUND: Refunds, cashbacks, reversals of previous payments
- BORROWING: Loans, credit advances (not true income)
- UNKNOWN: Cannot determine source from description
"""

from decimal import Decimal
from typing import Any

from .utils import round_decimal

# Keyword patterns for income classification - using list to guarantee order
# Order matters: more specific matches should come first
_INCOME_KEYWORDS: list[tuple[str, list[str]]] = [
    ("salary", ["salary", "payroll", "wages", "professional fee", "salaried"]),
    (
        "business",
        [
            "business",
            "consulting",
            "freelance",
            "commission",
            "services",
            "service fee",
        ],
    ),
    (
        "investment",
        [
            "dividend",
            "mutual fund",
            "stocks",
            "trading",
            "capital gains",
            "interest income",
            "investment",
        ],
    ),
    ("transfer", ["transfer", "own account", "self transfer", "internal transfer"]),
    ("refund", ["refund", "cashback", "reversal", "cash back"]),
    ("borrowing", ["loan", "credit", "borrow", "overdraft", "lending"]),
]

# Categories that represent true income (recurring/stable sources)
_TRUE_INCOME_CATEGORIES = {"salary", "business", "investment"}


def classify_income_source(transaction: dict[str, Any]) -> tuple[str, float]:
    """
    Classify an income transaction's source based on description keywords.

    Classification priority (first match wins):
    1. SALARY - employment income
    2. BUSINESS - business/freelance income
    3. INVESTMENT - investment returns
    4. TRANSFER - internal transfers (excluded from true income)
    5. REFUND - refunds/cashbacks (excluded from true income)
    6. BORROWING - loans/advances (excluded from true income)
    7. UNKNOWN - no matching keywords

    Confidence scoring:
    - 1.0: Exact whole-word match
    - 0.8: Partial word match

    Parameters:
        transaction: dict with 'description' key (and optionally 'amount_paise').

    Returns:
        Tuple of (category: str, confidence: float).
        Category is lowercase string: "salary", "business", "investment",
        "transfer", "refund", "borrowing", or "unknown".
    """
    description = transaction.get("description", "").lower()

    if not description:
        return ("unknown", 0.0)

    for category, keywords in _INCOME_KEYWORDS:
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in description:
                # Check for whole word match (higher confidence)
                confidence = _compute_match_confidence(keyword_lower, description)
                return (category, confidence)

    return ("unknown", 0.0)


def _compute_match_confidence(keyword: str, description: str) -> float:
    """
    Compute confidence score for a keyword match.

    Returns:
        1.0 for whole-word match, 0.8 for partial match.
    """
    words = description.split()
    for word in words:
        # Clean punctuation from word
        clean_word = word.strip(".,;:!?'\"-")
        if clean_word == keyword:
            return 1.0
    return 0.8


def compute_salary_dependence_ratio(
    salary_income_paise: int,
    true_income_paise: int,
) -> Decimal:
    """
    Compute the ratio of salary income to true income.

    Formula: salary_income / true_income

    This measures how dependent a person's income is on their salary.
    Higher values indicate greater dependence (lower diversification).

    Note:
        true_income_paise should be pre-computed by the caller by summing
        all income transactions excluding TRANSFER, REFUND, and BORROWING
        categories using classify_income_source().

    Parameters:
        salary_income_paise: Total salary income in paise.
        true_income_paise: Total true income (SALARY + BUSINESS + INVESTMENT) in paise.

    Returns:
        Decimal ratio between 0 and 1+. Returns Decimal('0') for zero true income.
    """
    if true_income_paise == 0:
        return Decimal("0")

    return round_decimal(
        Decimal(str(salary_income_paise)) / Decimal(str(true_income_paise))
    )


def compute_income_diversification_score(
    income_transactions: list[dict[str, Any]],
) -> Decimal:
    """
    Compute income diversification score based on unique income sources.

    Scoring:
        - Counts unique income sources from true income categories only
        - true_income_categories: SALARY, BUSINESS, INVESTMENT
        - Excludes: TRANSFER, REFUND, BORROWING (not considered "true income")

    Formula: min(unique_sources / 3, 1.0)
    - 1 source = 0.33 score
    - 2 sources = 0.67 score
    - 3 sources = 1.0 score (maximum diversification)

    Note:
        Future versions could use Herfindahl-Hirschman Index (HHI) for
        weighted diversification based on income proportion.

    Parameters:
        income_transactions: List of income transaction dicts, each with
                           'description' key and optionally 'amount_paise'.

    Returns:
        Decimal score between 0 and 1. Higher indicates more diversified income.
    """
    if not income_transactions:
        return Decimal("0")

    unique_sources: set[str] = set()

    for txn in income_transactions:
        category, _confidence = classify_income_source(txn)
        if category in _TRUE_INCOME_CATEGORIES:
            unique_sources.add(category)

    # Score: 3+ sources = capped at 1.0 (max true income categories)
    score = min(len(unique_sources) / 3, 1.0)
    return round_decimal(Decimal(str(score)))


def filter_true_income(
    income_transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Filter income transactions to only include true income sources.

    True income sources are: SALARY, BUSINESS, INVESTMENT
    Excludes: TRANSFER, REFUND, BORROWING

    Parameters:
        income_transactions: List of income transaction dicts.

    Returns:
        List of transactions that qualify as true income.
    """
    true_income_txns = []
    for txn in income_transactions:
        category, _confidence = classify_income_source(txn)
        if category in _TRUE_INCOME_CATEGORIES:
            true_income_txns.append(txn)
    return true_income_txns


def compute_true_income_total(
    income_transactions: list[dict[str, Any]],
) -> int:
    """
    Compute total true income from a list of income transactions.

    Sums amounts for all transactions classified as SALARY, BUSINESS, or INVESTMENT.

    Parameters:
        income_transactions: List of income transaction dicts with 'amount_paise' key.

    Returns:
        Total true income in paise (integer).
    """
    total = 0
    for txn in filter_true_income(income_transactions):
        total += txn.get("amount_paise", 0)
    return total
