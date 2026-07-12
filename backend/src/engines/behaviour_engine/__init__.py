"""Behaviour Engine — Core and Debt Metrics.

Deterministic behavioural metrics for financial analysis.
All monetary values are integers in paise (₹1.00 = 100 paise).

Structure:
- savings.py — Savings rate, borrowed lifestyle ratio, monthly surplus
- cashflow.py — Income/expense stability, cashflow stability index
- resilience.py — Liquidity months, resilience index
- lifestyle.py — Lifestyle inflation, lifestyle creep index
- debt.py — Credit dependency, debt cycle, FOIR, revolver ratio
- utils.py — Shared helper functions (median, variance, coefficient of variation)

All functions are pure - no database access.
"""

from .cashflow import (
    compute_cashflow_stability_index,
    compute_expense_stability,
    compute_income_stability,
)
from .debt import (
    compute_credit_dependency_ratio,
    compute_credit_revolver_ratio,
    compute_debt_cycle_score,
    compute_foir,
)
from .lifestyle import (
    compute_lifestyle_creep_index,
    compute_lifestyle_inflation,
)
from .resilience import (
    compute_liquidity_months,
    compute_resilience_index,
)
from .savings import (
    compute_borrowed_lifestyle_ratio,
    compute_monthly_surplus,
    compute_true_savings_rate,
)

__all__ = [
    # Savings
    "compute_true_savings_rate",
    "compute_borrowed_lifestyle_ratio",
    "compute_monthly_surplus",
    # Cashflow Stability
    "compute_income_stability",
    "compute_expense_stability",
    "compute_cashflow_stability_index",
    # Resilience
    "compute_liquidity_months",
    "compute_resilience_index",
    # Lifestyle
    "compute_lifestyle_inflation",
    "compute_lifestyle_creep_index",
    # Debt Intelligence
    "compute_credit_dependency_ratio",
    "compute_debt_cycle_score",
    "compute_foir",
    "compute_credit_revolver_ratio",
]
