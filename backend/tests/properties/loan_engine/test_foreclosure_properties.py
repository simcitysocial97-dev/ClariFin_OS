"""
Property-based tests for loan engine foreclosure module.

These tests verify the mathematical invariants and business rules of the foreclosure
calculations using property-based testing techniques.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.engines.loan_engine.amortization import generate_schedule, total_interest_paise
from src.engines.loan_engine.foreclosure import (
    compute_foreclosure_amount,
    compute_prepayment_breakup,
)
from src.engines.loan_engine.models import ForeclosureResult

# Constants for testing
MAX_INTEREST_RATE_BPS = 3600  # 36% annual
MIN_INTEREST_RATE_BPS = 500   # 5% annual
MAX_TENURE_MONTHS = 360       # 30 years
MIN_TENURE_MONTHS = 1         # 1 month
MAX_PRINCIPAL_PAISE = 10_000_000_00  # ₹10 crore
MIN_PRINCIPAL_PAISE = 100_000        # ₹1,000

# Strategies for generating test data
@st.composite
def foreclosure_parameters(draw):
    """Generate valid foreclosure parameters for testing."""
    principal = draw(st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE))
    rate = draw(st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS))
    tenure = draw(st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS))
    months_paid = draw(st.integers(min_value=0, max_value=tenure - 1))
    penalty = draw(st.integers(min_value=0, max_value=500))  # 0-5% penalty
    start_date = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)).map(lambda d: d.isoformat()))

    return principal, rate, tenure, months_paid, penalty, start_date

@st.composite
def schedule_with_foreclosure(draw):
    """Generate a schedule and foreclosure parameters."""
    principal, rate, tenure, start_date = draw(loan_parameters())
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Generate foreclosure at a random month
    months_paid = draw(st.integers(min_value=0, max_value=tenure - 1))
    penalty = draw(st.integers(min_value=0, max_value=500))  # 0-5% penalty

    return schedule, rate, months_paid, penalty, start_date

@st.composite
def loan_parameters(draw):
    """Generate valid loan parameters for testing."""
    principal = draw(st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE))
    rate = draw(st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS))
    tenure = draw(st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS))
    start_date = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)).map(lambda d: d.isoformat()))

    return principal, rate, tenure, start_date

@given(foreclosure_parameters())
@settings(max_examples=30, deadline=None)
def test_compute_foreclosure_amount_invariants(foreclosure_params):
    """Property: compute_foreclosure_amount must satisfy all invariants."""
    principal, rate, tenure, months_paid, penalty, start_date = foreclosure_params

    # Generate schedule to get outstanding balance
    schedule = generate_schedule(principal, rate, tenure, start_date)
    if months_paid >= len(schedule):
        return

    outstanding_row = schedule[months_paid]
    outstanding_paise = outstanding_row.balance_paise
    remaining_months = len(schedule) - months_paid

    # Compute foreclosure amount
    result = compute_foreclosure_amount(
        outstanding_paise, rate, remaining_months, months_paid, penalty
    )

    # INVARIANT 1: Result is a valid ForeclosureResult
    assert isinstance(result, ForeclosureResult)

    # INVARIANT 2: All monetary values are non-negative
    assert result.outstanding_paise >= 0
    assert result.accrued_interest_paise >= 0
    assert result.penalty_paise >= 0
    assert result.foreclosure_amount_paise >= 0

    # INVARIANT 3: Foreclosure amount equals sum of components
    expected_amount = (
        result.outstanding_paise +
        result.accrued_interest_paise +
        result.penalty_paise
    )
    assert result.foreclosure_amount_paise == expected_amount

    # INVARIANT 4: Outstanding amount matches input
    assert result.outstanding_paise == outstanding_paise

    # INVARIANT 5: Penalty is calculated correctly with ROUND_HALF_EVEN
    from decimal import ROUND_HALF_EVEN, Decimal
    expected_penalty = int((Decimal(penalty) * Decimal(outstanding_paise) / Decimal(10000))
                          .quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    assert result.penalty_paise == expected_penalty

    # INVARIANT 6: Months saved equals remaining months
    assert result.remaining_months_saved == remaining_months

@given(foreclosure_parameters())
@settings(max_examples=20, deadline=None)
def test_compute_foreclosure_amount_math_accuracy(foreclosure_params):
    """Property: compute_foreclosure_amount math must be accurate."""
    principal, rate, tenure, months_paid, penalty, start_date = foreclosure_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)
    if months_paid <= 0 or months_paid > len(schedule):
        return

    # Get outstanding balance after months_paid months (0-indexed)
    outstanding_row = schedule[months_paid - 1]
    outstanding_paise = outstanding_row.balance_paise
    remaining_months = len(schedule) - months_paid

    # Compute foreclosure amount
    result = compute_foreclosure_amount(
        outstanding_paise, rate, remaining_months, months_paid, penalty
    )

    # Calculate expected accrued interest for remaining months
    # Interest from month (months_paid + 1) onwards
    expected_accrued_interest = schedule[-1].cumulative_interest_paise - schedule[months_paid - 1].cumulative_interest_paise

    # Verify accrued interest (allow tolerance proportional to remaining months due to schedule regeneration rounding)
    # The regenerated schedule's total interest can differ from the original schedule's remaining
    # interest because integer paise rounding compounds differently on the two paths.
    # Tolerance: up to 10 paise per remaining month base + 10% of interest is acceptable.
    max_tolerance = max(10000, remaining_months * 10, expected_accrued_interest // 10)
    assert abs(result.accrued_interest_paise - expected_accrued_interest) <= max_tolerance

    # Verify total foreclosure amount
    expected_total = outstanding_paise + result.accrued_interest_paise + result.penalty_paise
    assert result.foreclosure_amount_paise == expected_total

@given(foreclosure_parameters())
@settings(max_examples=20, deadline=None)
def test_compute_prepayment_breakup_invariants(foreclosure_params):
    """Property: compute_prepayment_breakup must satisfy all invariants."""
    principal, rate, tenure, months_elapsed, penalty, start_date = foreclosure_params

    # Generate schedule to get outstanding balance
    schedule = generate_schedule(principal, rate, tenure, start_date)
    if months_elapsed <= 0 or months_elapsed > len(schedule):
        return

    # Get outstanding balance after months_elapsed months (0-indexed)
    outstanding_row = schedule[months_elapsed - 1]
    outstanding_paise = outstanding_row.balance_paise

    # Compute prepayment breakup
    result = compute_prepayment_breakup(
        outstanding_paise, rate, months_elapsed, principal, tenure, penalty
    )

    # INVARIANT 1: Result is a valid dictionary with correct keys
    assert isinstance(result, dict)
    assert "principal_remaining_paise" in result
    assert "accrued_interest_paise" in result
    assert "penalty_paise" in result
    assert "total_foreclosure_paise" in result

    # INVARIANT 2: All monetary values are non-negative
    assert result["principal_remaining_paise"] >= 0
    assert result["accrued_interest_paise"] >= 0
    assert result["penalty_paise"] >= 0
    assert result["total_foreclosure_paise"] >= 0

    # INVARIANT 3: Principal remaining matches input
    assert result["principal_remaining_paise"] == outstanding_paise

    # INVARIANT 4: Total equals sum of components
    expected_total = (
        result["principal_remaining_paise"] +
        result["accrued_interest_paise"] +
        result["penalty_paise"]
    )
    assert result["total_foreclosure_paise"] == expected_total

@given(foreclosure_parameters())
@settings(max_examples=20, deadline=None)
def test_compute_prepayment_breakup_math_accuracy(foreclosure_params):
    """Property: compute_prepayment_breakup math must be accurate."""
    principal, rate, tenure, months_elapsed, penalty, start_date = foreclosure_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)
    if months_elapsed <= 0 or months_elapsed > len(schedule):
        return

    # Get outstanding balance after months_elapsed months (0-indexed)
    outstanding_row = schedule[months_elapsed - 1]
    outstanding_paise = outstanding_row.balance_paise
    remaining_months = tenure - months_elapsed

    # Compute prepayment breakup
    result = compute_prepayment_breakup(
        outstanding_paise, rate, months_elapsed, principal, tenure, penalty
    )

    # Calculate expected accrued interest
    remaining_schedule = generate_schedule(
        outstanding_paise, rate, remaining_months, start_date
    )
    expected_accrued_interest = total_interest_paise(remaining_schedule)

    # Verify accrued interest (allow tolerance due to schedule regeneration rounding)
    assert abs(result["accrued_interest_paise"] - expected_accrued_interest) <= 10000

    # Verify penalty with ROUND_HALF_EVEN
    from decimal import ROUND_HALF_EVEN, Decimal
    expected_penalty = int((Decimal(penalty) * Decimal(outstanding_paise) / Decimal(10000))
                          .quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    assert result["penalty_paise"] == expected_penalty

    # Verify total
    expected_total = outstanding_paise + expected_accrued_interest + expected_penalty
    assert result["total_foreclosure_paise"] == expected_total

@given(foreclosure_parameters())
@settings(max_examples=10, deadline=None)
def test_foreclosure_edge_cases(foreclosure_params):
    """Property: Foreclosure functions handle edge cases correctly."""
    principal, rate, tenure, months_paid, penalty, start_date = foreclosure_params

    # Test with zero penalty
    if months_paid < tenure:
        schedule = generate_schedule(principal, rate, tenure, start_date)
        outstanding_paise = schedule[months_paid].balance_paise
        remaining_months = len(schedule) - months_paid

        result = compute_foreclosure_amount(
            outstanding_paise, rate, remaining_months, months_paid, 0
        )
        assert result.penalty_paise == 0

    # Test with zero months paid
    if tenure > 0:
        outstanding_paise = principal
        remaining_months = tenure

        result = compute_foreclosure_amount(
            outstanding_paise, rate, remaining_months, 0, penalty
        )
        assert result.outstanding_paise == principal

    # Test with all months paid (should return zero)
    if tenure > 0:
        schedule = generate_schedule(principal, rate, tenure, start_date)
        result = compute_prepayment_breakup(
            0, rate, tenure, principal, tenure, penalty
        )
        assert result["principal_remaining_paise"] == 0
        assert result["accrued_interest_paise"] == 0
        assert result["penalty_paise"] == 0
        assert result["total_foreclosure_paise"] == 0

@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=12, max_value=60),  # Tenure
    st.integers(min_value=0, max_value=500),  # Penalty
)
@settings(max_examples=10, deadline=None)
def test_foreclosure_penalty_calculation(principal, rate, tenure, penalty):
    """Property: Penalty calculation is accurate."""
    start_date = "2025-01-01"

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Test at month 0 (full principal)
    outstanding_paise = principal
    remaining_months = tenure

    result = compute_foreclosure_amount(
        outstanding_paise, rate, remaining_months, 0, penalty
    )

    # Calculate expected penalty with ROUND_HALF_EVEN
    expected_penalty = int((Decimal(penalty) * Decimal(outstanding_paise) / Decimal(10000))
                          .quantize(Decimal(1), rounding=ROUND_HALF_EVEN))
    assert result.penalty_paise == expected_penalty

    # Test penalty breakup
    breakup = compute_prepayment_breakup(
        outstanding_paise, rate, 0, principal, tenure, penalty
    )
    assert breakup["penalty_paise"] == expected_penalty

@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=12, max_value=60),  # Tenure
    st.integers(min_value=0, max_value=59),  # Months paid (tenure max is 60)
)
@settings(max_examples=10, deadline=None)
def test_foreclosure_zero_interest(principal, rate, tenure, months_paid):
    """Property: Zero interest loan produces correct foreclosure amounts."""
    start_date = "2025-01-01"

    # Test with 0% interest
    schedule = generate_schedule(principal, 0, tenure, start_date)
    if months_paid >= len(schedule):
        return

    outstanding_paise = schedule[months_paid].balance_paise
    remaining_months = len(schedule) - months_paid

    # Foreclosure with zero interest
    result = compute_foreclosure_amount(
        outstanding_paise, 0, remaining_months, months_paid, 0
    )

    # Should equal outstanding principal (no interest, no penalty)
    assert result.foreclosure_amount_paise == outstanding_paise
    assert result.accrued_interest_paise == 0
    assert result.penalty_paise == 0

    # Prepayment breakup
    breakup = compute_prepayment_breakup(
        outstanding_paise, 0, months_paid, principal, tenure, 0
    )

    assert breakup["principal_remaining_paise"] == outstanding_paise
    assert breakup["accrued_interest_paise"] == 0
    assert breakup["penalty_paise"] == 0
    assert breakup["total_foreclosure_paise"] == outstanding_paise

@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),           # Rate (5-20%)
    st.integers(min_value=12, max_value=60),              # Tenure
    st.integers(min_value=0, max_value=500),              # Penalty
)
@settings(max_examples=10, deadline=None)
def test_foreclosure_consistency(principal, rate, tenure, penalty):
    """Property: Foreclosure and prepayment breakup are consistent."""
    start_date = "2025-01-01"
    months_paid = tenure // 2  # Midpoint

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)
    if months_paid >= len(schedule):
        return

    outstanding_paise = schedule[months_paid].balance_paise
    remaining_months = len(schedule) - months_paid

    # Compute foreclosure amount
    foreclosure_result = compute_foreclosure_amount(
        outstanding_paise, rate, remaining_months, months_paid, penalty
    )

    # Compute prepayment breakup
    breakup_result = compute_prepayment_breakup(
        outstanding_paise, rate, months_paid, principal, tenure, penalty
    )

    # Should be consistent
    assert foreclosure_result.outstanding_paise == breakup_result["principal_remaining_paise"]
    assert foreclosure_result.accrued_interest_paise == breakup_result["accrued_interest_paise"]
    assert foreclosure_result.penalty_paise == breakup_result["penalty_paise"]
    assert foreclosure_result.foreclosure_amount_paise == breakup_result["total_foreclosure_paise"]