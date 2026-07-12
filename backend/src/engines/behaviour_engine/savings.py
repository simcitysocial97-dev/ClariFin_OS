"""Savings metrics for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.
"""


from decimal import Decimal


def compute_true_savings_rate(
    income_paise: int,
    actual_expenses_paise: int,
    financial_fees_paise: int,
) -> Decimal:
    """
    Compute true savings rate as a decimal value.

    Formula: (income - actual_expenses - financial_fees) / income

    Parameters:
        income_paise: Total income for the period (salary, credits).
                     This is the total money coming in.
        actual_expenses_paise: Total expenses/debits excluding transfers.
                               This is money going out for consumption.
        financial_fees_paise: Mandatory financial outflows including:
                             - Credit card annual fees
                             - Loan processing fees, prepayment penalties
                             - Interest paid on loans (if not already captured)

    Returns:
        Decimal savings rate. Can be negative (income < expenses+fees).
        Does NOT clamp - negative rates indicate overspending.
        Returns Decimal('0') for zero income.

    Note:
        This function returns the raw rate. Callers can clamp if needed
        for display purposes (e.g., savings rate can't exceed 100%).
    """
    if income_paise == 0:
        return Decimal('0')

    net_savings = income_paise - actual_expenses_paise - financial_fees_paise
    return Decimal(str(net_savings)) / Decimal(str(income_paise))


def compute_borrowed_lifestyle_ratio(
    credit_funded_paise: int,
    total_expenses_paise: int,
) -> Decimal:
    """
    Compute the ratio of credit-funded expenses to total expenses.

    Formula: credit_funded_expenses / total_expenses

    Parameters:
        credit_funded_paise: Total expenses funded by credit (credit card purchases
                            not paid off in full, or revolving credit usage).
                            This parameter is expected to be pre-computed by the
                            caller based on transaction classification.
                            For now, a simple approximation can be used:
                            - All credit card transactions flagged as non-EMI
        total_expenses_paise: Total expenses for the period.

    Returns:
        Decimal ratio between 0 and 1+. Returns Decimal('0') for zero expenses.
        Values > 1 indicate credit funding exceeds reported expenses (unusual).

    Note:
        This provides insight into lifestyle inflation from credit availability.
        Higher values suggest reliance on credit for daily expenses.
    """
    if total_expenses_paise == 0:
        return Decimal('0')

    return Decimal(str(credit_funded_paise)) / Decimal(str(total_expenses_paise))


def compute_monthly_surplus(
    income_paise: int,
    total_expenses_paise: int,
    fees_paise: int = 0,
) -> int:
    """
    Compute monthly surplus in paise.

    Formula: income - total_expenses - fees

    Parameters:
        income_paise: Total income for the period.
        total_expenses_paise: Total expenses for the period.
        fees_paise: Optional financial fees (defaults to 0).

    Returns:
        Integer surplus in paise. Can be negative (deficit).
        Negative values indicate spending exceeds income.
    """
    return income_paise - total_expenses_paise - fees_paise
