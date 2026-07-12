"""
Account Metrics Engine - Pure calculation module
=================================================
Aggregate deterministic account metrics.

All monetary values in paise (integer).
All days are integer counts.

Composes existing engine functions — no duplicate calculations.
"""

from .cashflow import compute_cash_flow_rate, compute_net_cash_flow
from .dormant import is_account_dormant


def compute_account_metrics(
    current_balance_paise: int,
    average_balance_paise: int,
    cash_in_paise: int,
    cash_out_paise: int,
    days_since_activity: int,
    dormancy_threshold_days: int = 365,
) -> dict[str, int | bool]:
    """
    Compute aggregate deterministic account metrics.

    Args:
        current_balance_paise: Current account balance in paise.
        average_balance_paise: Average balance in paise.
        cash_in_paise: Total credits in paise.
        cash_out_paise: Total debits in paise.
        days_since_activity: Days since last transaction.
        dormancy_threshold_days: Days threshold for dormancy (default 365).

    Returns:
        dict with deterministic metrics:
            - current_balance_paise: Current balance (pass-through)
            - average_balance_paise: Average balance (pass-through)
            - net_flow_paise: credits - debits
            - cash_flow_rate_paise: paise/day
            - days_since_activity: Days since last activity (pass-through)
            - is_dormant: Boolean dormancy status

    INVARIANT 1: All values are integers.
    INVARIANT 2: No duplicate calculations - composes existing functions.
    """
    # Net cash flow using cashflow module
    net_flow_paise = compute_net_cash_flow(cash_in_paise, cash_out_paise)

    # Cash flow rate over period
    # If days_since_activity is 0, use 1 to avoid division by zero
    days_for_rate = max(days_since_activity, 1)
    cash_flow_rate_paise = compute_cash_flow_rate(net_flow_paise, days_for_rate)

    # Dormancy check
    is_dormant_flag = is_account_dormant(days_since_activity, dormancy_threshold_days)

    return {
        "current_balance_paise": current_balance_paise,
        "average_balance_paise": average_balance_paise,
        "net_flow_paise": net_flow_paise,
        "cash_flow_rate_paise": cash_flow_rate_paise,
        "days_since_activity": days_since_activity,
        "is_dormant": is_dormant_flag,
    }
