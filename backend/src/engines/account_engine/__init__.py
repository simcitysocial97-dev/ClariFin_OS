"""
Account Engine - Pure calculation library
==========================================
Modular account calculation engine for account lifecycle and analytics.

All monetary values in paise (integer).
All days are integer counts.

Provides factual metrics only — no recommendations or heuristics.
"""

from .balance import (
    compute_average_balance,
    compute_balance_change,
    compute_balance_growth_percentage,
)
from .cashflow import (
    compute_cash_flow_rate,
    compute_income_expense_ratio,
    compute_net_cash_flow,
)
from .dormant import (
    compute_days_since_activity,
    is_account_dormant,
)
from .history import (
    compute_balance_trend,
    compute_balance_velocity,
)
from .lifecycle import (
    compute_account_status,
    is_account_closed,
)
from .metrics import compute_account_metrics

__all__ = [
    # Lifecycle
    "compute_account_status",
    "is_account_closed",
    # Balance
    "compute_average_balance",
    "compute_balance_change",
    "compute_balance_growth_percentage",
    # Cashflow
    "compute_net_cash_flow",
    "compute_cash_flow_rate",
    "compute_income_expense_ratio",
    # Dormant
    "compute_days_since_activity",
    "is_account_dormant",
    # History
    "compute_balance_trend",
    "compute_balance_velocity",
    # Metrics
    "compute_account_metrics",
]
