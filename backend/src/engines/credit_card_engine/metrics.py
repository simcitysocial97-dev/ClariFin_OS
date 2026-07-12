"""
Metrics Engine - Pure calculation module
=========================================
Computes financial metrics for credit cards.

All monetary values in paise (integer).
All rates in basis points (integer).

Provides factual metrics only — no recommendations or heuristics.
"""


def compute_financial_metrics(
    outstanding_paise: int,
    credit_limit_paise: int,
    annual_rate_bps: int,
    total_interest_paid_paise: int = 0,
) -> dict[str, int]:
    """
    Compute core financial metrics for a credit card.

    Args:
        outstanding_paise: Current outstanding balance in paise.
        credit_limit_paise: Total credit limit in paise.
        annual_rate_bps: Annual interest rate in basis points.
        total_interest_paid_paise: Total interest paid to date (optional).

    Returns:
        dict with:
            - utilization_bps: Credit utilization in basis points
            - available_credit_paise: Available credit in paise
            - annual_rate_bps: Effective annual rate (pass-through)
            - total_interest_paid_paise: Total interest paid (pass-through)

    INVARIANT 1: All monetary values in integer paise.
    INVARIANT 2: Rates stored as basis points.
    """
    if outstanding_paise < 0:
        raise ValueError("outstanding_paise must be non-negative")
    if credit_limit_paise < 0:
        raise ValueError("credit_limit_paise must be non-negative")
    if annual_rate_bps < 0:
        raise ValueError("annual_rate_bps must be non-negative")
    if total_interest_paid_paise < 0:
        raise ValueError("total_interest_paid_paise must be non-negative")

    # Utilization in basis points
    if credit_limit_paise > 0 and outstanding_paise > 0:
        from decimal import ROUND_HALF_EVEN, Decimal
        util_decimal = Decimal(outstanding_paise) * Decimal(10000) / Decimal(credit_limit_paise)
        utilization_bps = int(util_decimal.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
        utilization_bps = min(utilization_bps, 10000)
    else:
        utilization_bps = 0

    # Available credit
    available = max(0, credit_limit_paise - outstanding_paise)

    return {
        "utilization_bps": utilization_bps,
        "available_credit_paise": available,
        "annual_rate_bps": annual_rate_bps,
        "total_interest_paid_paise": total_interest_paid_paise,
    }
