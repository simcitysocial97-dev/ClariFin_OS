"""Debt intelligence metrics for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.
"""

from decimal import Decimal

from .savings import compute_borrowed_lifestyle_ratio
from .utils import round_decimal

# Scoring constants for debt cycle - easily tunable
_CREDIT_ADVANCE_SCORES = {
    0: 0,
    1: 10,
    2: 30,
    3: 30,
    4: 60,
    5: 60,
}  # >=6 maps to 90 via default

_REVOLVING_MONTH_SCORES = {
    0: 0,
    1: 20,
    2: 20,
    3: 50,
    4: 50,
    5: 80,
    6: 80,
}

_DEBT_TREND_SCORES = [
    (-1.0, 1.0, 0),      # negative -> 0
    (0.0, 0.1, 5),       # 0 to 0.1 -> 5
    (0.1, 0.3, 20),      # 0.1 to 0.3 -> 20
    (0.3, 0.6, 50),      # 0.3 to 0.6 -> 50
    (0.6, 1.0, 80),      # 0.6+ -> 80
]


def compute_credit_dependency_ratio(
    credit_funded_expenses_paise: int,
    total_expenses_paise: int,
) -> Decimal:
    """
    Compute the ratio of credit-funded expenses to total expenses.

    Formula: credit_funded_expenses / total_expenses

    Note:
        This function is semantically equivalent to compute_borrowed_lifestyle_ratio.
        Provided as a separate function for clarity in the debt intelligence layer.
        The caller should pre-compute credit_funded_expenses based on transaction
        classification (credit card purchases not paid in full).

    Parameters:
        credit_funded_expenses_paise: Total expenses funded by credit/loan proceeds.
        total_expenses_paise: Total expenses for the period.

    Returns:
        Decimal ratio between 0 and 1+. Returns Decimal('0') for zero expenses.
    """
    return compute_borrowed_lifestyle_ratio(credit_funded_expenses_paise, total_expenses_paise)


def _score_credit_advances(credit_advances_count: int) -> int:
    """Score credit advances count (last 6 months)."""
    if credit_advances_count >= 6:
        return 90
    if credit_advances_count == 0:
        return 0
    if credit_advances_count == 1:
        return 10
    if 2 <= credit_advances_count <= 3:
        return 30
    if 4 <= credit_advances_count <= 5:
        return 60
    return 0


def _score_revolving_months(revolving_months: int) -> int:
    """Score revolving months (out of last 6)."""
    if revolving_months <= 0:
        return 0
    if 1 <= revolving_months <= 2:
        return 20
    if 3 <= revolving_months <= 4:
        return 50
    if revolving_months >= 5:
        return 80
    return 0


def _score_debt_trend(debt_increase_trend: Decimal) -> int:
    """Score debt increase trend (Decimal from -1 to 1)."""
    if debt_increase_trend < Decimal('0'):
        return 0
    if Decimal('0') <= debt_increase_trend < Decimal('0.1'):
        return 5
    if Decimal('0.1') <= debt_increase_trend < Decimal('0.3'):
        return 20
    if Decimal('0.3') <= debt_increase_trend < Decimal('0.6'):
        return 50
    if debt_increase_trend >= Decimal('0.6'):
        return 80
    return 0


def compute_debt_cycle_score(
    credit_advances_count: int,
    revolving_months: int,
    debt_increase_trend: Decimal,
) -> int:
    """
    Compute debt cycle score (0-100) based on credit behavior indicators.

    Weighted formula: 0.3 * advance_score + 0.3 * revolve_score + 0.4 * trend_score

    Scoring bands:
        Credit advances (last 6 months):
        - 0 advances -> 0
        - 1 advance -> 10
        - 2-3 advances -> 30
        - 4-5 advances -> 60
        - >=6 advances -> 90

        Revolving months (out of last 6):
        - 0 months -> 0
        - 1-2 months -> 20
        - 3-4 months -> 50
        - 5-6 months -> 80

        Debt increase trend (Decimal -1 to 1):
        - Negative -> 0
        - 0 to 0.1 -> 5
        - 0.1 to 0.3 -> 20
        - 0.3 to 0.6 -> 50
        - 0.6+ -> 80

    Parameters:
        credit_advances_count: Number of credit advances in last 6 months.
        revolving_months: Number of months with revolving credit usage.
        debt_increase_trend: Decimal trend value from -1 to 1.

    Returns:
        Integer score from 0 to 100. Higher indicates more concerning debt cycle.
    """
    advance_score = _score_credit_advances(credit_advances_count)
    revolve_score = _score_revolving_months(revolving_months)
    trend_score = _score_debt_trend(debt_increase_trend)

    # Weighted average
    weighted = (0.3 * advance_score) + (0.3 * revolve_score) + (0.4 * trend_score)

    return int(min(weighted, 100))


def compute_foir(
    loan_emi_paise: int,
    credit_card_min_due_paise: int,
    monthly_income_paise: int,
) -> tuple[Decimal, str]:
    """
    Compute Fixed Obligation to Income Ratio (FOIR).

    Formula: (loan_emi + minimum_credit_due) / monthly_income

    The minimum due amount should be provided by the caller, typically
    5% of credit card outstanding (or ₹100, whichever is higher in India).

    Bands:
        - <30% -> "HEALTHY"
        - 30-50% -> "MODERATE"
        - 50-60% -> "WARNING"
        - >=60% -> "CRITICAL"

    Parameters:
        loan_emi_paise: Total monthly loan EMI obligations in paise.
        credit_card_min_due_paise: Total minimum credit card dues in paise.
        monthly_income_paise: Monthly income in paise.

    Returns:
        Tuple of (Decimal ratio, band string).
        Returns (Decimal('0'), "HEALTHY") for zero income.
    """
    if monthly_income_paise == 0:
        return Decimal('0'), "HEALTHY"

    total_obligations = loan_emi_paise + credit_card_min_due_paise
    ratio = Decimal(str(total_obligations)) / Decimal(str(monthly_income_paise))

    # Determine band (inclusive upper bounds per spec bands)
    if ratio <= Decimal('0.30'):
        band = "HEALTHY"
    elif ratio <= Decimal('0.50'):
        band = "MODERATE"
    elif ratio < Decimal('0.60'):
        band = "WARNING"
    else:
        band = "CRITICAL"

    return round_decimal(ratio), band


def compute_credit_revolver_ratio(
    months_partial_payment: int,
    active_credit_months: int,
) -> Decimal:
    """
    Compute credit revolver ratio.

    Formula: months_partial_payment / active_credit_months

    This measures the proportion of credit card months where only partial
    payment was made (indicating revolving credit behavior).

    Parameters:
        months_partial_payment: Number of months with partial credit payments.
        active_credit_months: Number of months with active credit card usage.

    Returns:
        Decimal ratio between 0 and 1+. Returns Decimal('0') for zero active months.
    """
    if active_credit_months == 0:
        return Decimal('0')

    ratio = Decimal(str(months_partial_payment)) / Decimal(str(active_credit_months))
    return round_decimal(ratio)
