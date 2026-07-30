"""
Outstanding Engine - Pure calculation module
=============================================
Computes outstanding balance for credit cards.

All monetary values in paise (integer).

Formula:
    Outstanding = Σ(spend) + Σ(EMI_conversions) + Σ(fees) - Σ(payments)
"""


def compute_outstanding(
    total_spend_paise: int,
    total_emi_paise: int,
    total_fees_paise: int,
    total_payments_paise: int,
) -> int:
    """
    Compute current outstanding balance.

    Args:
        total_spend_paise: Total spending in current cycle.
        total_emi_paise: Total EMI conversions outstanding.
        total_fees_paise: Total fees charged (annual fee, late fee, etc.).
        total_payments_paise: Total payments made.

    Returns:
        Outstanding balance in paise (non-negative).

    INVARIANT 1: Money is always integer paise.
    INVARIANT 5: Balances are never negative.
    """
    if total_spend_paise < 0:
        raise ValueError("total_spend_paise must be non-negative")
    if total_emi_paise < 0:
        raise ValueError("total_emi_paise must be non-negative")
    if total_fees_paise < 0:
        raise ValueError("total_fees_paise must be non-negative")
    if total_payments_paise < 0:
        raise ValueError("total_payments_paise must be non-negative")

    outstanding = (
        total_spend_paise + total_emi_paise + total_fees_paise - total_payments_paise
    )

    # INVARIANT 5: Balance must never be negative
    return max(0, outstanding)
