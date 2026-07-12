"""Resilience metrics for behaviour engine.

All monetary values are integers in paise (₹1.00 = 100 paise).
All functions are pure - no database access.
"""

from decimal import Decimal


def compute_liquidity_months(
    liquid_assets_paise: int,
    essential_monthly_expenses_paise: int,
) -> int:
    """
    Compute number of months of essential expenses covered by liquid assets.

    Formula: liquid_assets / essential_monthly_expenses

    Parameters:
        liquid_assets_paise: Total liquid assets (savings accounts, cash) in paise.
        essential_monthly_expenses_paise: Monthly essential expenses (rent, utilities,
                                          groceries, minimum loan payments) in paise.

    Returns:
        Integer number of months of coverage.
        Returns 999 for zero essential expenses (effectively infinite coverage).
        Returns 0 if liquid_assets is 0 and essential_expenses > 0.
        This is an integer approximation - uses floor division for conservative estimate.
    """
    if essential_monthly_expenses_paise == 0:
        # No essential expenses means infinite coverage
        return 999

    months = liquid_assets_paise // essential_monthly_expenses_paise
    return months


def compute_resilience_index(
    liquid_assets_paise: int,
    essential_monthly_expenses_paise: int,
    total_income_paise: int,
    monthly_incomes_paise: list[int],
) -> Decimal:
    """
    Compute composite resilience index.

    Formula: 0.6 * min(liquidity_months, 12) / 12 + 0.4 * income_stability

    Parameters:
        liquid_assets_paise: Total liquid assets in paise.
        essential_monthly_expenses_paise: Monthly essential expenses in paise.
        total_income_paise: Total income for the period in paise.
        monthly_incomes_paise: List of monthly income values for stability calculation.

    Returns:
        Decimal resilience score between 0 and 1.
        Higher values indicate better ability to weather financial shocks.

    Note:
        Liquidity is capped at 12 months because beyond that, additional
        liquid assets don't significantly improve resilience (opportunity cost).
        Income stability provides the remaining component.
    """
    from .cashflow import compute_income_stability

    # Liquidity component (capped at 12 months)
    liquidity_months = compute_liquidity_months(liquid_assets_paise, essential_monthly_expenses_paise)
    liquidity_capped = min(liquidity_months, 12)
    liquidity_score = Decimal(str(liquidity_capped)) / Decimal('12')

    # Income stability component
    income_stability = compute_income_stability(monthly_incomes_paise)

    # Composite: 60% liquidity, 40% income stability
    resilience = Decimal('0.6') * liquidity_score + Decimal('0.4') * income_stability

    return resilience
