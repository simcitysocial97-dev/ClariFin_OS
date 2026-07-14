"""Financial Intelligence Engine - Forecasting and Prediction.

Deterministic forecasting functions for financial planning.
All monetary values are integers in paise (₹1.00 = 100 paise).

Structure:
- forecasting.py — Cashflow, liquidity, credit forecasting functions
- goal_planner.py — Financial goal projection and health scoring
- utils.py — Shared helper functions

All functions are pure - no database access.
"""

from .forecasting import (
    detect_future_cash_shortfall,
    forecast_cashflow,
    forecast_credit_utilization,
    forecast_liquidity,
)
from .goal_planner import (
    DEFAULT_GOAL_ALLOCATION_RATIO,
    DEFAULT_EMERGENCY_MONTHS,
    calculate_debt_payoff_projection,
    calculate_emergency_fund_target,
    calculate_goal_health,
    calculate_goal_projection,
    calculate_household_goal_summary,
)
from .utils import (
    DEFAULT_EMERGENCY_THRESHOLD_PAISE,
    DEFAULT_FORECAST_MONTHS,
    compute_confidence_from_variance,
    compute_trend_direction,
    compute_utilization_ratio,
    find_stress_month,
    generate_month_sequence,
    project_running_balance,
)

__all__ = [
    # Constants
    "DEFAULT_EMERGENCY_THRESHOLD_PAISE",
    "DEFAULT_FORECAST_MONTHS",
    "DEFAULT_GOAL_ALLOCATION_RATIO",
    "DEFAULT_EMERGENCY_MONTHS",
    # Forecasting functions
    "forecast_cashflow",
    "forecast_liquidity",
    "forecast_credit_utilization",
    "detect_future_cash_shortfall",
    # Goal planner functions
    "calculate_goal_projection",
    "calculate_emergency_fund_target",
    "calculate_debt_payoff_projection",
    "calculate_goal_health",
    "calculate_household_goal_summary",
    # Utility functions
    "compute_confidence_from_variance",
    "compute_trend_direction",
    "compute_utilization_ratio",
    "generate_month_sequence",
    "project_running_balance",
    "find_stress_month",
]
