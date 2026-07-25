"""Lifestyle metrics for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.
"""

from decimal import Decimal


def compute_lifestyle_inflation(
    current_period_non_essential_paise: int,
    previous_period_non_essential_paise: int,
) -> Decimal:
    """
    Compute lifestyle inflation rate for non-essential spending.

    Formula: (current - previous) / previous

    Parameters:
        current_period_non_essential_paise: Current period non-essential spending in paise.
        previous_period_non_essential_paise: Previous period non-essential spending in paise.

    Returns:
        Decimal inflation rate. Positive values indicate increased lifestyle spending.
        Returns Decimal('0') for zero previous period (no baseline for comparison).
        Returns Decimal('-1') for zero current period (complete reduction).

    Note:
        This measures discretionary spending growth. Non-essential categories
        typically include: Entertainment, Dining, Shopping, Travel, Lifestyle.
    """
    if previous_period_non_essential_paise == 0:
        # No baseline - cannot compute inflation
        return Decimal("0")

    if current_period_non_essential_paise == 0:
        # Complete elimination of non-essential spending
        return Decimal("-1")

    change = current_period_non_essential_paise - previous_period_non_essential_paise
    return Decimal(str(change)) / Decimal(str(previous_period_non_essential_paise))


def compute_lifestyle_creep_index(
    monthly_discretionary_spending_paise: list[int],
) -> Decimal:
    """
    Compute lifestyle creep index based on discretionary spending trend.

    Formula: (latest - earliest) / earliest

    Parameters:
        monthly_discretionary_spending_paise: List of monthly discretionary spending
                                             values in paise, ordered chronologically.
                                             This function does not impute missing months.

    Returns:
        Decimal creep index. Positive values indicate increasing discretionary spending.
        Returns Decimal('0') for single data point or zero earliest value.
        The index can exceed 1 (100%) for significant increases.

    Note:
        Uses simple percentage change between first and last values.
        Future versions may use linear regression for more sophisticated trend analysis.
    """
    if len(monthly_discretionary_spending_paise) < 2:
        # No trend data available
        return Decimal("0")

    earliest = monthly_discretionary_spending_paise[0]
    latest = monthly_discretionary_spending_paise[-1]

    if earliest == 0:
        # Cannot compute creep from zero baseline
        return Decimal("0")

    change = latest - earliest
    return Decimal(str(change)) / Decimal(str(earliest))
