"""
Loan Engine - Pure calculation library
======================================
Modular loan calculation engine for personal loan management.

All monetary values in paise (integer).
All interest rates in basis points (integer).
"""

# Types
# Amortization
from .amortization import (
    find_schedule_row,
    generate_schedule,
    total_interest_paise,
    total_payment_paise,
    validate_schedule_invariants,
)

# EMI calculations
from .emi import (
    compute_emi_fixed,
    compute_emi_floating,
    compute_monthly_interest,
    compute_principal_component,
)

# Floating Rate
from .floating_rate import (
    apply_floating_rate_change,
    simulate_floating_rate_schedule,
)

# Foreclosure
from .foreclosure import (
    compute_foreclosure_amount,
    compute_prepayment_breakup,
)

# Metrics
from .metrics import (
    calculate_interest_saved,
    calculate_tenure_saved,
    compute_loan_metrics,
)
from .models import (
    AmortizationRow,
    FloatingRateChange,
    ForeclosureResult,
    InterestType,
    LoanMetrics,
    PrepaymentMode,
    PrepaymentResult,
)

# Prepayment
from .prepayment import (
    apply_multiple_prepayments,
    apply_prepayment,
    apply_prepayment_at_month,
    compute_remaining_months,
    regenerate_schedule,
)

__all__ = [
    # Types
    "AmortizationRow",
    "FloatingRateChange",
    "ForeclosureResult",
    "InterestType",
    "LoanMetrics",
    "PrepaymentMode",
    "PrepaymentResult",
    # EMI Calculator
    "compute_emi_fixed",
    "compute_emi_floating",
    "compute_monthly_interest",
    "compute_principal_component",
    # Amortization
    "find_schedule_row",
    "generate_schedule",
    "regenerate_schedule",
    "total_interest_paise",
    "total_payment_paise",
    "validate_schedule_invariants",
    # Prepayment
    "apply_prepayment",
    "apply_prepayment_at_month",
    "apply_multiple_prepayments",
    "compute_remaining_months",
    # Floating Rate
    "apply_floating_rate_change",
    "simulate_floating_rate_schedule",
    # Foreclosure
    "compute_foreclosure_amount",
    "compute_prepayment_breakup",
    # Metrics
    "calculate_interest_saved",
    "calculate_tenure_saved",
    "compute_loan_metrics",
]
