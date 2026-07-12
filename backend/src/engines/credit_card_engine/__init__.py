"""
Credit Card Engine - Pure calculation library
=============================================
Modular credit card calculation engine for liability management.

All monetary values in paise (integer).
All interest rates in basis points (integer).

Reuses loan_engine utilities for EMI, foreclosure, and date math.
No heuristic or recommendation logic.
"""

from .billing import (
    compute_due_date,
    compute_minimum_due,
    compute_next_statement_date,
    compute_statement_dates,
)
from .emi import compute_emi_conversion
from .foreclosure import compute_card_foreclosure
from .interest import (
    compute_daily_interest,
    compute_monthly_interest_charge,
)
from .metrics import compute_financial_metrics
from .outstanding import compute_outstanding
from .utilization import (
    compute_available_credit,
    compute_utilization,
)

__all__ = [
    # Billing
    "compute_due_date",
    "compute_minimum_due",
    "compute_next_statement_date",
    "compute_statement_dates",
    # Interest
    "compute_daily_interest",
    "compute_monthly_interest_charge",
    # Outstanding
    "compute_outstanding",
    # Utilization
    "compute_available_credit",
    "compute_utilization",
    # EMI (delegates to loan_engine)
    "compute_emi_conversion",
    # Foreclosure (delegates to loan_engine)
    "compute_card_foreclosure",
    # Metrics
    "compute_financial_metrics",
]
