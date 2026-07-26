"""Domain Invariants - Pure assertion helpers for financial correctness."""

from .account import (
    assert_account_closed_valid,
    assert_account_state_valid,
    assert_owner_scope_valid,
)
from .behaviour import (
    assert_behaviour_score_valid,
    assert_credit_dependency_ratio_valid,
    assert_temporal_pattern_consistency,
    assert_wellness_metrics_valid,
)
from .cashflow import assert_cashflow_invariants, assert_cashflow_result_invariants
from .credit import (
    assert_credit_invariants,
    assert_emi_conversion_valid,
    assert_utilization_valid,
)
from .date_consistency import (
    assert_data_has_required_dates,
    assert_date_in_range,
    assert_date_iso_format,
    assert_date_sequence_ordered,
    assert_month_bucket_alignment,
)
from .forecast import assert_forecast_invariants, assert_liquidity_forecast_invariants
from .loan import (
    assert_loan_invariants,
    assert_loan_schedule_valid,
    assert_prepayment_result_valid,
)
from .money import assert_all_paise_integers, assert_money_invariants
from .statement import assert_statement_detection_invariants, assert_statement_integrity
from .transaction import (
    assert_amount_sign_convention,
    assert_reconciliation_match_valid,
    assert_transaction_ordering_valid,
)

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
    # behaviour
    "assert_behaviour_score_valid",
    "assert_wellness_metrics_valid",
    "assert_temporal_pattern_consistency",
    "assert_credit_dependency_ratio_valid",
    # account
    "assert_account_state_valid",
    "assert_owner_scope_valid",
    "assert_account_closed_valid",
    # transaction
    "assert_transaction_ordering_valid",
    "assert_amount_sign_convention",
    "assert_reconciliation_match_valid",
    # date consistency
    "assert_date_iso_format",
    "assert_month_bucket_alignment",
    "assert_date_sequence_ordered",
    "assert_date_in_range",
    "assert_data_has_required_dates",
]
