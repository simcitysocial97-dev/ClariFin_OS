"""Account intelligence metrics for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.

Functions analyze account-level behaviour including concentration,
idle cash detection, volatility, and low balance risk.
"""

from decimal import Decimal

from .utils import _coefficient_of_variation, round_decimal


def compute_account_concentration(
    account_balances_paise: list[int],
) -> Decimal:
    """
    Compute account concentration ratio.

    Formula: largest_account_balance / total_liquid_assets

    This measures whether a user's liquid assets are concentrated
    in a single account or spread across multiple accounts.

    Parameters:
        account_balances_paise: List of liquid account balances in paise.
                              Caller should pre-filter to liquid account types
                              (savings, current) before calling this function.

    Returns:
        Decimal ratio between 0 and 1.
        Returns Decimal('0') for empty list.
        Returns Decimal('1') for single account (fully concentrated by definition).
        Values close to 1 indicate over-concentration risk.
    """
    if not account_balances_paise:
        return Decimal("0")

    if len(account_balances_paise) == 1:
        return Decimal("1")

    largest_balance = max(account_balances_paise)
    total_balance = sum(account_balances_paise)

    if total_balance == 0:
        return Decimal("0")

    return round_decimal(Decimal(str(largest_balance)) / Decimal(str(total_balance)))


def compute_idle_cash_amount(
    cash_balance_paise: int,
    loan_interest_rate_bps: int,
    deposit_interest_rate_bps: int,
    threshold_bps: int = 300,
) -> Decimal:
    """
    Compute idle cash amount based on opportunity cost.

    Returns the cash balance as idle when loan interest rate exceeds
    deposit rate by more than threshold (default 300 bps = 3%).

    Parameters:
        cash_balance_paise: Cash/savings account balance in paise.
        loan_interest_rate_bps: Loan interest rate in basis points (e.g., 1200 = 12%).
        deposit_interest_rate_bps: Savings account interest rate in basis points.
        threshold_bps: Threshold for flagging idle cash (default 300 bps = 3%).

    Returns:
        Decimal idle cash amount in paise.
        Returns the entire cash balance if loan rate exceeds deposit rate + threshold.
        Returns Decimal('0') if no significant opportunity cost.
    """
    if cash_balance_paise <= 0:
        return Decimal("0")

    rate_differential = loan_interest_rate_bps - deposit_interest_rate_bps

    if rate_differential > threshold_bps:
        return Decimal(str(cash_balance_paise))

    return Decimal("0")


def detect_balance_volatility(
    monthly_balances_paise: list[int],
) -> Decimal:
    """
    Detect account balance volatility using coefficient of variation.

    Formula: standard_deviation / mean

    This measures the relative variability of account balances over time.
    Higher values indicate more volatile balances.

    Parameters:
        monthly_balances_paise: List of monthly balance values in paise.

    Returns:
        Decimal coefficient of variation (raw, not capped).
        Returns Decimal('0') for empty list or fewer than 2 entries.
        Returns Decimal('0') when all values are equal (no variance).
    """
    if len(monthly_balances_paise) < 2:
        return Decimal("0")

    if not monthly_balances_paise:
        return Decimal("0")

    # Use the shared utility function
    cv = _coefficient_of_variation(monthly_balances_paise)

    if cv is None:
        return Decimal("0")

    return cv


def detect_low_balance_risk(
    current_balance_paise: int,
    essential_monthly_expenses_paise: int,
) -> Decimal:
    """
    Detect low balance risk based on essential expenses coverage.

    Formula: max(0, (essential_expenses - current_balance) / essential_expenses)

    This measures the risk that an account's balance is insufficient
    to cover even one month of essential expenses.

    Parameters:
        current_balance_paise: Current account balance in paise.
        essential_monthly_expenses_paise: Monthly essential expenses in paise.

    Returns:
        Decimal risk score between 0 and 1.
        0 = no risk (balance >= essential expenses)
        1 = highest risk (balance = 0)
    """
    if essential_monthly_expenses_paise == 0:
        # No essential expenses means no risk
        return Decimal("0")

    if current_balance_paise >= essential_monthly_expenses_paise:
        return Decimal("0")

    # Risk = (essential - current) / essential
    # This gives 0 when balance = essential, and approaches 1 as balance -> 0
    risk = Decimal(str(essential_monthly_expenses_paise - current_balance_paise)) / Decimal(
        str(essential_monthly_expenses_paise)
    )

    return round_decimal(risk)
