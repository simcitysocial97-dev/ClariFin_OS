"""Behaviour Engine — Core, Debt, Pattern Detection, Income Intelligence, and Account Intelligence.

Deterministic behavioural metrics for financial analysis.
All monetary values are integers in paise (₹1.00 = 100 paise).

Structure:
- savings.py — Savings rate, borrowed lifestyle ratio, monthly surplus
- cashflow.py — Income/expense stability, cashflow stability index
- resilience.py — Liquidity months, resilience index
- lifestyle.py — Lifestyle inflation, lifestyle creep index
- debt.py — Credit dependency, debt cycle, FOIR, revolver ratio
- patterns.py — Impulse detection, weekend/night ratios, recurring merchants, subscriptions
- income.py — Income source classification, diversification score
- account.py — Account concentration, idle cash, balance volatility, low balance risk
- profile.py — Financial personality classification (SAVER, BALANCED, SPENDER, DEBT_OPTIMIZER, DEBT_DEPENDENT)
- insights.py — Behavioral insight generation
- nudges.py — Behavioral nudge generation

All functions are pure - no database access.
"""

from .account import (
    compute_account_concentration,
    compute_idle_cash_amount,
    detect_balance_volatility,
    detect_low_balance_risk,
)
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
from .income import (
    classify_income_source,
    compute_income_diversification_score,
    compute_salary_dependence_ratio,
    compute_true_income_total,
    filter_true_income,
)
from .insights import (
    generate_behavioral_insights,
    generate_summary_text,
)
from .lifestyle import (
    compute_lifestyle_creep_index,
    compute_lifestyle_inflation,
)
from .nudges import (
    generate_nudges,
    get_nudge_summary,
    get_top_nudge,
)
from .patterns import (
    compute_night_spend_ratio,
    compute_weekend_spend_ratio,
    detect_impulse_transactions,
    detect_recurring_merchants,
    detect_subscription_patterns,
)
from .profile import classify_financial_personality
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
    # Pattern Detection
    "detect_impulse_transactions",
    "compute_weekend_spend_ratio",
    "compute_night_spend_ratio",
    "detect_recurring_merchants",
    "detect_subscription_patterns",
    # Income Intelligence
    "classify_income_source",
    "compute_income_diversification_score",
    "compute_salary_dependence_ratio",
    "compute_true_income_total",
    "filter_true_income",
    # Account Intelligence
    "compute_account_concentration",
    "compute_idle_cash_amount",
    "detect_balance_volatility",
    "detect_low_balance_risk",
    # Profile Classification
    "classify_financial_personality",
    # Insight generation
    "generate_behavioral_insights",
    "generate_summary_text",
    # Nudge engine
    "generate_nudges",
    "get_top_nudge",
    "get_nudge_summary",
]
