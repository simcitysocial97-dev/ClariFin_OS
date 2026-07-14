"""Domain Invariants - Pure assertion helpers for financial correctness."""

from .cashflow import assert_cashflow_invariants, assert_cashflow_result_invariants
from .credit import assert_credit_invariants, assert_emi_conversion_valid, assert_utilization_valid
from .forecast import assert_forecast_invariants, assert_liquidity_forecast_invariants
from .loan import assert_loan_invariants, assert_loan_schedule_valid, assert_prepayment_result_valid
from .money import assert_all_paise_integers, assert_money_invariants
from .statement import assert_statement_detection_invariants, assert_statement_integrity

__all__ = [
    "assert_money_invariants",
    "assert_all_paise_integers",
    "assert_cashflow_invariants",
    "assert_cashflow_result_invariants",
    "assert_loan_schedule_valid",
    "assert_loan_invariants",
    "assert_prepayment_result_valid",
    "assert_forecast_invariants",
    "assert_liquidity_forecast_invariants",
    "assert_credit_invariants",
    "assert_utilization_valid",
    "assert_emi_conversion_valid",
    "assert_statement_integrity",
    "assert_statement_detection_invariants",
]
