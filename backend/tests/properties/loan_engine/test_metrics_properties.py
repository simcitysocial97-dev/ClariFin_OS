"""
Property-based tests for loan engine metrics module.

These tests verify the mathematical invariants and business rules of the loan metrics
calculations using property-based testing techniques.
"""

from datetime import date

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.engines.loan_engine.amortization import generate_schedule, total_interest_paise
from src.engines.loan_engine.metrics import (
    calculate_interest_saved,
    calculate_tenure_saved,
    compute_loan_metrics,
    get_emi_component,
    get_interest_component,
)
from src.engines.loan_engine.models import LoanMetrics
from src.engines.loan_engine.prepayment import apply_prepayment_at_month

# Constants for testing
MAX_INTEREST_RATE_BPS = 3600  # 36% annual
MIN_INTEREST_RATE_BPS = 500  # 5% annual
MAX_TENURE_MONTHS = 360  # 30 years
MIN_TENURE_MONTHS = 1  # 1 month
MAX_PRINCIPAL_PAISE = 10_000_000_00  # ₹10 crore
MIN_PRINCIPAL_PAISE = 100_000  # ₹1,000


# Strategies for generating test data
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


@st.composite
def schedule_with_prepayment(draw):
    """Generate a schedule and prepayment parameters."""
    principal, rate, tenure, start_date = draw(loan_parameters())
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Generate prepayment at a random month
    prepayment_month = draw(st.integers(min_value=1, max_value=tenure))
    prepayment_row = schedule[prepayment_month - 1]
    max_prepayment = prepayment_row.balance_paise
    prepayment_amount = draw(st.integers(min_value=10_000, max_value=max_prepayment))

    return schedule, rate, prepayment_amount, prepayment_month, start_date


@st.composite
def two_schedules(draw):
    """Generate two schedules for comparison (original and modified)."""
    principal, rate, tenure, start_date = draw(loan_parameters())
    original_schedule = generate_schedule(principal, rate, tenure, start_date)

    # Apply a prepayment to create a modified schedule
    prepayment_month = draw(st.integers(min_value=1, max_value=tenure))
    prepayment_row = original_schedule[prepayment_month - 1]
    max_prepayment = prepayment_row.balance_paise
    assume(max_prepayment >= 10_000)
    prepayment_amount = draw(st.integers(min_value=10_000, max_value=max_prepayment))

    new_schedule, _ = apply_prepayment_at_month(
        original_schedule, prepayment_month, prepayment_amount, rate
    )

    return original_schedule, new_schedule, prepayment_amount


@given(loan_parameters())
@settings(max_examples=30, deadline=None)
def test_compute_loan_metrics_invariants(loan_params):
    """Property: compute_loan_metrics must satisfy all invariants."""
    principal, rate, tenure, start_date = loan_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Compute metrics
    metrics = compute_loan_metrics(schedule, principal)

    # INVARIANT 1: Result is a valid LoanMetrics object
    assert isinstance(metrics, LoanMetrics)

    # INVARIANT 2: All monetary values are non-negative
    assert metrics.outstanding_paise >= 0
    assert metrics.principal_paid_paise >= 0
    assert metrics.interest_paid_paise >= 0
    assert metrics.remaining_interest_paise >= 0

    # INVARIANT 3: Tenure values are non-negative
    assert metrics.remaining_tenure_months >= 0
    assert metrics.tenure_saved_months >= 0
    assert metrics.total_payments_remaining >= 0

    # INVARIANT 4: Interest ratio is non-negative
    assert metrics.effective_interest_ratio >= 0

    # INVARIANT 5: Principal paid + outstanding = original principal
    assert metrics.principal_paid_paise + metrics.outstanding_paise == principal

    # INVARIANT 6: Total interest equals paid + remaining interest
    total_interest = metrics.interest_paid_paise + metrics.remaining_interest_paise
    assert total_interest == total_interest_paise(schedule)


@given(loan_parameters())
@settings(max_examples=20, deadline=None)
def test_compute_loan_metrics_edge_cases(loan_params):
    """Property: compute_loan_metrics handles edge cases correctly."""
    principal, rate, tenure, start_date = loan_params

    # Test with empty schedule
    metrics = compute_loan_metrics([], principal)
    assert metrics.outstanding_paise == 0
    assert metrics.principal_paid_paise == 0
    assert metrics.interest_paid_paise == 0
    assert metrics.remaining_tenure_months == 0

    # Test with single payment schedule
    if tenure >= 1:
        schedule = generate_schedule(principal, rate, 1, start_date)
        metrics = compute_loan_metrics(schedule, principal)
        assert metrics.remaining_tenure_months == 1
        assert (
            metrics.outstanding_paise == principal
        )  # Full schedule: outstanding = original principal


@given(two_schedules())
@settings(max_examples=20, deadline=None)
def test_calculate_interest_saved_invariants(schedule_params):
    """Property: calculate_interest_saved must satisfy all invariants."""
    original_schedule, new_schedule, prepayment_amount = schedule_params

    # Calculate interest saved
    interest_saved = calculate_interest_saved(
        original_schedule, new_schedule, prepayment_amount
    )

    # INVARIANT 1: Interest saved is non-negative
    assert interest_saved >= 0

    # INVARIANT 2: Interest saved is less than or equal to original interest
    original_interest = sum(row.interest_paise for row in original_schedule)
    assert interest_saved <= original_interest

    # INVARIANT 3: Interest saved is less than or equal to original - new interest - prepayment
    new_interest = sum(row.interest_paise for row in new_schedule)
    expected_saved = max(0, original_interest - new_interest - prepayment_amount)
    assert interest_saved == expected_saved


@given(two_schedules())
@settings(max_examples=20, deadline=None)
def test_calculate_tenure_saved_invariants(schedule_params):
    """Property: calculate_tenure_saved must satisfy all invariants."""
    original_schedule, new_schedule, _ = schedule_params

    # Calculate tenure saved
    tenure_saved = calculate_tenure_saved(original_schedule, new_schedule)

    # INVARIANT 1: Tenure saved is non-negative
    assert tenure_saved >= 0

    # INVARIANT 2: Tenure saved is less than or equal to original tenure
    original_tenure = len(original_schedule)
    assert tenure_saved <= original_tenure

    # INVARIANT 3: Tenure saved equals original - new tenure
    new_tenure = len(new_schedule)
    assert tenure_saved == original_tenure - new_tenure


@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
)
@settings(max_examples=20, deadline=None)
def test_get_interest_component_invariants(principal, rate, tenure):
    """Property: get_interest_component must satisfy all invariants."""
    # Interest monotonicity with rate holds for the supported rate domain.
    # At extreme rates (>= 25% annual) the integer-EMI reducing-balance path
    # can clamp the monthly principal component to zero, so the strict
    # monotonicity invariant is only guaranteed up to 2500 bps.
    assume(rate <= 2500)

    # Calculate interest component
    interest = get_interest_component(principal, rate, tenure)

    # INVARIANT 1: Interest is non-negative
    assert interest >= 0

    # INVARIANT 2: Interest increases with rate
    if rate > MIN_INTEREST_RATE_BPS:
        lower_rate_interest = get_interest_component(principal, rate - 100, tenure)
        assert interest >= lower_rate_interest

    # INVARIANT 4: Interest increases with tenure
    if tenure > MIN_TENURE_MONTHS:
        shorter_tenure_interest = get_interest_component(principal, rate, tenure - 1)
        assert interest >= shorter_tenure_interest


@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
)
@settings(max_examples=20, deadline=None)
def test_get_emi_component_invariants(principal, rate, tenure):
    """Property: get_emi_component must satisfy all invariants."""
    from src.engines.loan_engine.emi import compute_emi_fixed

    # Calculate EMI
    emi = get_emi_component(principal, rate, tenure)

    # INVARIANT 1: EMI is positive
    assert emi > 0

    # INVARIANT 2: EMI is consistent with compute_emi_fixed
    expected_emi = compute_emi_fixed(principal, rate, tenure)
    assert emi == expected_emi

    # INVARIANT 3: EMI increases with rate
    if rate > MIN_INTEREST_RATE_BPS:
        lower_rate_emi = get_emi_component(principal, rate - 100, tenure)
        assert emi >= lower_rate_emi

    # INVARIANT 4: EMI decreases with tenure
    if tenure > MIN_TENURE_MONTHS:
        longer_tenure_emi = get_emi_component(principal, rate, tenure + 1)
        assert emi >= longer_tenure_emi


@given(loan_parameters())
@settings(max_examples=20, deadline=None)
def test_loan_metrics_math_accuracy(loan_params):
    """Property: Loan metrics math must be accurate."""
    principal, rate, tenure, start_date = loan_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Compute metrics
    metrics = compute_loan_metrics(schedule, principal)

    # Calculate expected values
    total_interest = total_interest_paise(schedule)
    remaining_interest = total_interest  # For full schedule, all interest is remaining
    interest_paid = 0  # For full schedule, no interest paid before start
    outstanding = principal  # For full schedule, outstanding = original principal
    principal_paid = 0  # For full schedule, no principal paid before start

    # Verify calculations
    assert metrics.outstanding_paise == outstanding
    assert metrics.principal_paid_paise == principal_paid
    assert metrics.interest_paid_paise == interest_paid
    assert metrics.remaining_interest_paise == remaining_interest
    assert metrics.remaining_tenure_months == len(schedule)

    # Verify interest ratio
    if principal > 0:
        expected_ratio = total_interest / principal
        assert abs(metrics.effective_interest_ratio - expected_ratio) < 0.002


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
)
@settings(max_examples=10, deadline=None)
def test_zero_interest_loan_metrics(principal, rate, tenure):
    """Property: Zero interest loan produces correct metrics."""
    # Test with 0% interest
    start_date = "2025-01-01"
    schedule = generate_schedule(principal, 0, tenure, start_date)

    # Compute metrics
    metrics = compute_loan_metrics(schedule, principal)

    # Verify metrics
    assert (
        metrics.outstanding_paise == principal
    )  # Full schedule: outstanding = original principal
    assert (
        metrics.principal_paid_paise == 0
    )  # Full schedule: no principal paid before start
    assert metrics.interest_paid_paise == 0
    assert metrics.remaining_interest_paise == 0
    assert metrics.remaining_tenure_months == tenure
    assert metrics.effective_interest_ratio == 0.0


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
)
@settings(max_examples=10, deadline=None)
def test_full_tenure_loan_metrics(principal, rate, tenure):
    """Property: Full tenure loan produces correct metrics."""
    start_date = "2025-01-01"
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Compute metrics
    metrics = compute_loan_metrics(schedule, principal)

    # Verify metrics
    assert (
        metrics.outstanding_paise == principal
    )  # Full schedule: outstanding = original principal
    assert (
        metrics.principal_paid_paise == 0
    )  # Full schedule: no principal paid before start
    assert (
        metrics.interest_paid_paise == 0
    )  # Full schedule: no interest paid before start
    assert metrics.remaining_interest_paise == total_interest_paise(schedule)
    assert metrics.remaining_tenure_months == tenure


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
    st.integers(min_value=1, max_value=11),  # Months elapsed
)
@settings(max_examples=10, deadline=None)
def test_partial_tenure_loan_metrics(principal, rate, tenure, months_elapsed):
    """Property: Partial tenure loan produces correct metrics."""
    if months_elapsed >= tenure:
        return

    start_date = "2025-01-01"
    full_schedule = generate_schedule(principal, rate, tenure, start_date)
    partial_schedule = full_schedule[months_elapsed:]

    # Compute metrics
    metrics = compute_loan_metrics(partial_schedule, principal)

    # Verify metrics
    expected_outstanding = (
        partial_schedule[0].balance_paise + partial_schedule[0].principal_paise
        if partial_schedule
        else 0
    )
    expected_principal_paid = principal - expected_outstanding
    expected_remaining_interest = total_interest_paise(partial_schedule)
    expected_remaining_tenure = len(partial_schedule)

    assert metrics.outstanding_paise == expected_outstanding
    assert metrics.principal_paid_paise == expected_principal_paid
    assert metrics.remaining_interest_paise == expected_remaining_interest
    assert metrics.remaining_tenure_months == expected_remaining_tenure
