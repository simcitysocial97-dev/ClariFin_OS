"""
Property-based tests for loan engine prepayment module.

These tests verify the mathematical invariants and business rules of the prepayment
calculations using property-based testing techniques.
"""

from datetime import date

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.engines.loan_engine.amortization import generate_schedule, total_interest_paise
from src.engines.loan_engine.models import (
    AmortizationRow,
    PrepaymentMode,
    PrepaymentResult,
)
from src.engines.loan_engine.prepayment import (
    _compute_tenure_from_emi,
    apply_multiple_prepayments,
    apply_prepayment,
    apply_prepayment_at_month,
    compute_remaining_months,
    regenerate_schedule,
)

# Constants for testing
MAX_INTEREST_RATE_BPS = 3600  # 36% annual
MIN_INTEREST_RATE_BPS = 500  # 5% annual
MAX_TENURE_MONTHS = 360  # 30 years
MIN_TENURE_MONTHS = 1  # 1 month
MAX_PRINCIPAL_PAISE = 10_000_000_00  # ₹10 crore
MIN_PRINCIPAL_PAISE = 100_000  # ₹1,000
MAX_PREPAYMENT_PAISE = 5_000_000_00  # ₹5 crore
MIN_PREPAYMENT_PAISE = 10_000  # ₹100


# Strategies for generating test data
@st.composite
def prepayment_parameters(draw):
    """Generate valid prepayment parameters for testing."""
    principal = draw(
        st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE)
    )
    rate = draw(
        st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS)
    )
    tenure = draw(st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS))
    prepayment_amount = draw(
        st.integers(
            min_value=MIN_PREPAYMENT_PAISE,
            max_value=min(MAX_PREPAYMENT_PAISE, principal),
        )
    )
    prepayment_month = draw(st.integers(min_value=1, max_value=tenure))
    start_date = draw(
        st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)).map(
            lambda d: d.isoformat()
        )
    )

    return principal, rate, tenure, prepayment_amount, prepayment_month, start_date


@st.composite
def schedule_with_prepayment(draw):
    """Generate a schedule and prepayment parameters."""
    principal, rate, tenure, start_date = draw(loan_parameters())
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Generate prepayment at a random month
    prepayment_month = draw(st.integers(min_value=1, max_value=tenure))
    prepayment_row = schedule[prepayment_month - 1]
    max_prepayment = prepayment_row.balance_paise
    assume(max_prepayment >= 10_000)
    prepayment_amount = draw(st.integers(min_value=10_000, max_value=max_prepayment))

    return schedule, rate, prepayment_amount, prepayment_month, start_date


@st.composite
def loan_parameters(draw):
    """Generate valid loan parameters for testing."""
    principal = draw(
        st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE)
    )
    rate = draw(
        st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS)
    )
    tenure = draw(st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS))
    start_date = draw(
        st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)).map(
            lambda d: d.isoformat()
        )
    )

    return principal, rate, tenure, start_date


def test_compute_tenure_from_emi_edge_cases():
    """Test _compute_tenure_from_emi with edge cases."""
    # Zero interest case
    assert _compute_tenure_from_emi(1_000_000, 0, 100_000) == 10

    # Very low EMI (should return large number)
    assert _compute_tenure_from_emi(1_000_000, 1000, 100) == 999

    # EMI exactly equal to interest (should return large number)
    from src.engines.loan_engine.utils import bps_to_monthly_rate

    monthly_rate = bps_to_monthly_rate(1000)  # 10% annual
    interest_only_emi = int(1_000_000 * monthly_rate)
    assert _compute_tenure_from_emi(1_000_000, 1000, interest_only_emi) == 999


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=10_000, max_value=100_000),  # EMI
)
@settings(max_examples=20, deadline=None)
def test_compute_tenure_from_emi_always_positive(principal, rate, emi):
    """Property: _compute_tenure_from_emi always returns positive number."""
    result = _compute_tenure_from_emi(principal, rate, emi)
    assert result > 0


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
)
@settings(max_examples=20, deadline=None)
def test_compute_remaining_months_consistency(principal, rate, tenure):
    """Property: compute_remaining_months is consistent with _compute_tenure_from_emi."""
    from src.engines.loan_engine.emi import compute_emi_fixed

    emi = compute_emi_fixed(principal, rate, tenure)
    result1 = compute_remaining_months(principal, rate, emi)
    result2 = _compute_tenure_from_emi(principal, rate, emi)

    assert result1 == result2


@given(schedule_with_prepayment())
@settings(max_examples=30, deadline=None)
def test_apply_prepayment_at_month_invariants(schedule_params):
    """Property: apply_prepayment_at_month must satisfy all invariants."""
    schedule, rate, prepayment_amount, prepayment_month, start_date = schedule_params

    # Apply prepayment
    new_schedule, result = apply_prepayment_at_month(
        schedule, prepayment_month, prepayment_amount, rate
    )

    # INVARIANT 1: Result is a valid PrepaymentResult
    assert isinstance(result, PrepaymentResult)
    assert result.prepayment_paise == prepayment_amount
    assert result.original_remaining_months == len(schedule) - prepayment_month + 1
    assert result.interest_saved_paise >= 0

    # INVARIANT 2: New schedule is valid
    assert isinstance(new_schedule, list)
    assert all(isinstance(row, AmortizationRow) for row in new_schedule)

    # INVARIANT 3: Prepayment reduces remaining months or EMI
    if result.mode == PrepaymentMode.REDUCE_TENURE:
        assert result.new_remaining_months <= result.original_remaining_months + 1
    else:  # REDUCE_EMI
        assert result.new_emi_paise <= result.original_emi_paise + 10

    # INVARIANT 4: Interest saved is non-negative
    assert result.interest_saved_paise >= 0

    # INVARIANT 5: If loan is closed, new remaining months is 0
    if result.loan_closed:
        assert result.new_remaining_months == 0
        assert len(new_schedule) == prepayment_month
    else:
        # INVARIANT 6: New schedule length is appropriate
        expected_length = prepayment_month - 1 + result.new_remaining_months
        assert len(new_schedule) == expected_length


@given(prepayment_parameters())
@settings(max_examples=20, deadline=None)
def test_apply_prepayment_invariants(prepayment_params):
    """Property: apply_prepayment must satisfy all invariants."""
    principal, rate, tenure, prepayment_amount, prepayment_month, start_date = (
        prepayment_params
    )

    # Apply prepayment
    result = apply_prepayment(
        principal,
        rate,
        tenure,
        prepayment_amount,
        PrepaymentMode.REDUCE_TENURE,
        start_date,
    )

    # INVARIANT 1: Result is a valid PrepaymentResult
    assert isinstance(result, PrepaymentResult)
    assert result.prepayment_paise == prepayment_amount
    assert result.original_remaining_months == tenure
    assert result.interest_saved_paise >= 0

    # INVARIANT 2: Prepayment reduces remaining months or EMI
    if result.mode == PrepaymentMode.REDUCE_TENURE:
        assert result.new_remaining_months <= result.original_remaining_months
    else:  # REDUCE_EMI
        assert result.new_emi_paise <= result.original_emi_paise

    # INVARIANT 3: Interest saved is non-negative
    assert result.interest_saved_paise >= 0

    # INVARIANT 4: If loan is closed, new remaining months is 0
    if result.loan_closed:
        assert result.new_remaining_months == 0


@given(schedule_with_prepayment())
@settings(max_examples=20, deadline=None)
def test_apply_prepayment_at_month_math_accuracy(schedule_params):
    """Property: apply_prepayment_at_month math must be accurate."""
    schedule, rate, prepayment_amount, prepayment_month, start_date = schedule_params

    # Apply prepayment
    new_schedule, result = apply_prepayment_at_month(
        schedule, prepayment_month, prepayment_amount, rate
    )

    # Calculate original and new interest
    original_interest = total_interest_paise(schedule)
    new_interest = total_interest_paise(new_schedule)

    # Interest saved should match (within rounding)
    expected_saved = original_interest - new_interest
    assert abs(result.interest_saved_paise - expected_saved) <= len(schedule)


@given(schedule_with_prepayment())
@settings(max_examples=20, deadline=None)
def test_apply_prepayment_at_month_loan_closure(schedule_params):
    """Property: Large prepayments close the loan."""
    schedule, rate, _, prepayment_month, start_date = schedule_params

    # Use the full balance as prepayment
    prepayment_row = schedule[prepayment_month - 1]
    # Prepay the full opening balance to close the loan
    prepayment_amount = prepayment_row.balance_paise + prepayment_row.principal_paise

    # Apply prepayment
    new_schedule, result = apply_prepayment_at_month(
        schedule, prepayment_month, prepayment_amount, rate
    )

    # Loan should be closed
    assert result.loan_closed
    assert result.new_remaining_months == 0
    assert len(new_schedule) == prepayment_month


@given(schedule_with_prepayment())
@settings(max_examples=20, deadline=None)
def test_apply_prepayment_at_month_reduce_emi_mode(schedule_params):
    """Property: reduce_emi mode keeps tenure but reduces EMI."""
    schedule, rate, prepayment_amount, prepayment_month, start_date = schedule_params

    # Apply prepayment in reduce_emi mode
    new_schedule, result = apply_prepayment_at_month(
        schedule,
        prepayment_month,
        prepayment_amount,
        rate,
        mode=PrepaymentMode.REDUCE_EMI,
    )

    # Tenure should remain the same
    original_remaining_months = len(schedule) - prepayment_month + 1
    assert result.new_remaining_months == original_remaining_months

    # EMI should be reduced (allow small increase due to rounding)
    assert result.new_emi_paise <= result.original_emi_paise + 10

    # Total payments should be less (allow small increase due to rounding)
    original_total = sum(row.emi_paise for row in schedule)
    new_total = sum(row.emi_paise for row in new_schedule)
    assert new_total <= original_total + 1000


@given(schedule_with_prepayment())
@settings(max_examples=20, deadline=None)
def test_apply_prepayment_at_month_reduce_tenure_mode(schedule_params):
    """Property: reduce_tenure mode keeps EMI but reduces tenure."""
    schedule, rate, prepayment_amount, prepayment_month, start_date = schedule_params

    # Apply prepayment in reduce_tenure mode
    new_schedule, result = apply_prepayment_at_month(
        schedule,
        prepayment_month,
        prepayment_amount,
        rate,
        mode=PrepaymentMode.REDUCE_TENURE,
    )

    # EMI should remain the same (except when remaining balance is so small
    # that the loan closes in 1 month, in which case the single EMI equals
    # the full balance + interest rather than the original EMI)
    if result.new_remaining_months > 1:
        assert result.new_emi_paise == result.original_emi_paise, (
            f"EMI changed from {result.original_emi_paise} to {result.new_emi_paise} "
            f"with {result.new_remaining_months} months remaining"
        )

    # Tenure should be reduced
    assert result.new_remaining_months <= result.original_remaining_months

    # Total payments should be less
    original_total = sum(row.emi_paise for row in schedule)
    new_total = sum(row.emi_paise for row in new_schedule)
    assert new_total <= original_total


@given(schedule_with_prepayment())
@settings(max_examples=10, deadline=None)
def test_apply_multiple_prepayments_invariants(schedule_params):
    """Property: apply_multiple_prepayments must satisfy all invariants."""
    schedule, rate, _, _, start_date = schedule_params

    # Create multiple prepayments
    prepayments = [
        (2, 50_000_00),  # Month 2, ₹5,000
        (6, 30_000_00),  # Month 6, ₹3,000
        (12, 20_000_00),  # Month 12, ₹2,000
    ]

    # Apply multiple prepayments
    new_schedule, results = apply_multiple_prepayments(
        schedule, prepayments, rate, mode=PrepaymentMode.REDUCE_TENURE
    )

    # INVARIANT 1: Results list has correct length (may be less if loan closes early)
    valid_prepayments = [p for p in prepayments if p[0] <= len(schedule)]
    assert len(results) <= len(valid_prepayments)

    # INVARIANT 2: All results are valid PrepaymentResult
    for result in results:
        assert isinstance(result, PrepaymentResult)
        assert result.interest_saved_paise >= 0

    # INVARIANT 3: New schedule is valid
    assert isinstance(new_schedule, list)
    assert all(isinstance(row, AmortizationRow) for row in new_schedule)

    # INVARIANT 4: Total interest is reduced
    original_interest = total_interest_paise(schedule)
    new_interest = total_interest_paise(new_schedule)
    assert new_interest <= original_interest


@given(schedule_with_prepayment())
@settings(max_examples=10, deadline=None)
def test_regenerate_schedule_invariants(schedule_params):
    """Property: regenerate_schedule must satisfy all invariants."""
    schedule, rate, _, prepayment_month, start_date = schedule_params

    if len(schedule) < prepayment_month:
        return

    # Get the row at prepayment month
    prepayment_row = schedule[prepayment_month - 1]
    remaining_balance = prepayment_row.balance_paise
    remaining_schedule = schedule[prepayment_month - 1 :]

    # Regenerate schedule
    new_schedule = regenerate_schedule(
        remaining_schedule, remaining_balance, rate, "reduce_tenure", start_date
    )

    # INVARIANT 1: New schedule is valid
    assert isinstance(new_schedule, list)
    assert all(isinstance(row, AmortizationRow) for row in new_schedule)

    # INVARIANT 2: Month numbers continue from original schedule
    if new_schedule:
        first_new_month = new_schedule[0].month_number
        expected_first_month = prepayment_row.month_number
        assert first_new_month == expected_first_month

    # INVARIANT 3: First month balance is non-negative
    if new_schedule:
        assert new_schedule[0].balance_paise >= 0

    # INVARIANT 4: Last payment balance is 0
    if new_schedule:
        assert new_schedule[-1].balance_paise == 0


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
    st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31)).map(
        lambda d: d.isoformat()
    ),
)
@settings(max_examples=10, deadline=None)
def test_regenerate_schedule_math_accuracy(principal, rate, tenure, start_date):
    """Property: regenerate_schedule math must be accurate."""
    # Generate original schedule
    original_schedule = generate_schedule(principal, rate, tenure, start_date)

    # Regenerate from month 1 (should be identical)
    remaining_schedule = original_schedule[0:]
    new_schedule = regenerate_schedule(
        remaining_schedule, principal, rate, "reduce_tenure", start_date
    )

    # Should be identical
    assert len(new_schedule) == len(original_schedule)

    for new_row, original_row in zip(new_schedule, original_schedule, strict=False):
        assert new_row.month_number == original_row.month_number
        assert new_row.emi_paise == original_row.emi_paise
        assert new_row.principal_paise == original_row.principal_paise
        assert new_row.interest_paise == original_row.interest_paise
        assert new_row.balance_paise == original_row.balance_paise
        assert (
            new_row.cumulative_interest_paise == original_row.cumulative_interest_paise
        )
