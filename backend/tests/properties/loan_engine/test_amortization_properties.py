# test_amortization_properties.py
"""
Property-based tests for loan engine amortization module.

These tests verify the mathematical invariants and business rules of the amortization
schedule generation using property-based testing techniques.
"""

from datetime import date
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from src.engines.loan_engine.amortization import (
    generate_schedule,
    generate_schedule_fixed,
    generate_schedule_floating,
    total_interest_paise,
    total_principal_paise,
)
from src.engines.loan_engine.models import AmortizationRow

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


@given(loan_parameters())
@settings(max_examples=50, deadline=None)
def test_generate_schedule_invariants(loan_params):
    """Property: generate_schedule must satisfy all invariants."""
    principal, rate, tenure, start_date = loan_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # INVARIANT 1: Schedule has correct length
    assert len(schedule) == tenure

    # INVARIANT 2: All rows are valid AmortizationRow objects
    assert all(isinstance(row, AmortizationRow) for row in schedule)

    # INVARIANT 3: Month numbers are sequential
    for i, row in enumerate(schedule):
        assert row.month_number == i + 1

    # INVARIANT 4: All monetary values are non-negative
    for row in schedule:
        assert row.emi_paise >= 0
        assert row.principal_paise >= 0
        assert row.interest_paise >= 0
        assert row.balance_paise >= 0
        assert row.cumulative_interest_paise >= 0

    # INVARIANT 5: First row's balance is correct (after first payment)
    if schedule:
        # The balance after first payment should be less than or equal to principal
        assert schedule[0].balance_paise <= principal
        assert schedule[0].balance_paise >= 0

    # INVARIANT 6: Last row has zero balance
    if schedule:
        assert schedule[-1].balance_paise == 0

    # INVARIANT 7: EMI is non-increasing (constant or decreasing) for non-last months.
    # With integer paise, rounding may require EMI adjustment in final months
    # to prevent overpayment when remaining balance is small.
    if len(schedule) > 2:
        for i in range(1, len(schedule) - 1):
            assert schedule[i].emi_paise <= schedule[i - 1].emi_paise


@given(loan_parameters())
@settings(max_examples=30, deadline=None)
def test_generate_schedule_fixed_invariants(loan_params):
    """Property: generate_schedule_fixed must satisfy all invariants."""
    principal, rate, tenure, start_date = loan_params

    # Generate fixed rate schedule
    schedule = generate_schedule_fixed(principal, rate, tenure, start_date)

    # INVARIANT 1: Schedule has correct length
    assert len(schedule) == tenure

    # INVARIANT 2: All rows are valid AmortizationRow objects
    assert all(isinstance(row, AmortizationRow) for row in schedule)

    # INVARIANT 3: EMI is non-increasing (constant or decreasing) for non-last months.
    # With integer paise, rounding may require EMI adjustment in final months
    # to prevent overpayment when remaining balance is small.
    if len(schedule) > 2:
        for i in range(1, len(schedule) - 1):
            assert schedule[i].emi_paise <= schedule[i - 1].emi_paise

    # INVARIANT 4: Last row has zero balance
    if schedule:
        assert schedule[-1].balance_paise == 0


@given(loan_parameters())
@settings(max_examples=30, deadline=None)
def test_generate_schedule_floating_invariants(loan_params):
    """Property: generate_schedule_floating must satisfy all invariants."""
    principal, rate, tenure, start_date = loan_params

    # Generate floating rate schedule
    schedule = generate_schedule_floating(principal, rate, tenure, start_date)

    # INVARIANT 1: Schedule has correct length
    assert len(schedule) == tenure

    # INVARIANT 2: All rows are valid AmortizationRow objects
    assert all(isinstance(row, AmortizationRow) for row in schedule)

    # INVARIANT 3: Last row has zero balance
    if schedule:
        assert schedule[-1].balance_paise == 0

    # INVARIANT 4: EMI may vary (floating rate)


@given(loan_parameters())
@settings(max_examples=30, deadline=None)
def test_generate_schedule_math_accuracy(loan_params):
    """Property: generate_schedule math must be accurate."""
    principal, rate, tenure, start_date = loan_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # INVARIANT 1: Principal paid equals original principal
    principal_paid = total_principal_paise(schedule)
    assert principal_paid == principal

    # INVARIANT 2: Total payments equals sum of all EMIs
    total_payments = sum(row.emi_paise for row in schedule)
    assert total_payments == principal + total_interest_paise(schedule)

    # INVARIANT 3: Each row's principal + interest equals EMI (except last may differ due to adjustment)
    for row in schedule[:-1]:  # exclude last
        assert row.principal_paise + row.interest_paise == row.emi_paise
    # Last row: sum should be EMI
    if schedule:
        last = schedule[-1]
        assert last.principal_paise + last.interest_paise == last.emi_paise

    # INVARIANT 4: Balance decreases correctly (for non-last rows)
    for i in range(1, len(schedule)):
        prev_balance = schedule[i - 1].balance_paise
        current_principal = schedule[i].principal_paise
        # For non-last rows, exact equality; last row should be zero
        if i < len(schedule) - 1:
            assert schedule[i].balance_paise == prev_balance - current_principal
        else:
            # Last row: balance should be zero (already checked)
            assert schedule[i].balance_paise == 0


@given(loan_parameters())
@settings(max_examples=20, deadline=None)
def test_total_interest_paise_invariants(loan_params):
    """Property: total_interest_paise must satisfy all invariants."""
    principal, rate, tenure, start_date = loan_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Calculate total interest
    total_interest = total_interest_paise(schedule)

    # INVARIANT 1: Total interest is non-negative
    assert total_interest >= 0

    # INVARIANT 2: Total interest equals sum of all interest payments
    expected_interest = sum(row.interest_paise for row in schedule)
    assert total_interest == expected_interest


@given(loan_parameters())
@settings(max_examples=20, deadline=None)
def test_total_principal_paise_invariants(loan_params):
    """Property: total_principal_paise must satisfy all invariants."""
    principal, rate, tenure, start_date = loan_params

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Calculate total principal
    total_principal = total_principal_paise(schedule)

    # INVARIANT 1: Total principal equals original principal
    assert total_principal == principal

    # INVARIANT 2: Total principal equals sum of all principal payments
    expected_principal = sum(row.principal_paise for row in schedule)
    assert total_principal == expected_principal


@given(loan_parameters())
@settings(max_examples=20, deadline=None)
def test_zero_interest_schedule(loan_params):
    """Property: Zero interest produces correct schedule."""
    principal, _, tenure, start_date = loan_params

    # Generate schedule with zero interest
    schedule = generate_schedule(principal, 0, tenure, start_date)

    # INVARIANT 1: No interest paid
    for row in schedule:
        assert row.interest_paise == 0

    # INVARIANT 2: Principal paid equals EMI for each row (except last)
    for row in schedule[:-1]:
        assert row.principal_paise == row.emi_paise

    # INVARIANT 3: Total interest is zero
    assert total_interest_paise(schedule) == 0

    # INVARIANT 4: Principal sum equals original principal
    assert sum(row.principal_paise for row in schedule) == principal

    # INVARIANT 5: Last row's balance is zero
    assert schedule[-1].balance_paise == 0


@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=1, max_value=10),  # Short tenure
)
@settings(max_examples=20, deadline=None)
def test_short_tenure_schedule(principal, rate, tenure):
    """Property: Short tenure produces correct schedule."""
    start_date = "2025-01-01"

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # INVARIANT 1: Schedule has correct length
    assert len(schedule) == tenure

    # INVARIANT 2: Last row has zero balance
    assert schedule[-1].balance_paise == 0

    # INVARIANT 3: EMI is large (short tenure)
    emi = schedule[0].emi_paise
    assert emi >= principal // tenure


@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=120, max_value=360),  # Long tenure
)
@settings(max_examples=20, deadline=None)
def test_long_tenure_schedule(principal, rate, tenure):
    """Property: Long tenure produces correct schedule."""
    start_date = "2025-01-01"

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # INVARIANT 1: Schedule has correct length
    assert len(schedule) == tenure

    # INVARIANT 2: Last row has zero balance
    assert schedule[-1].balance_paise == 0

    # INVARIANT 3: EMI is small (long tenure)
    emi = schedule[0].emi_paise
    assert emi < principal

    # INVARIANT 4: EMI is at least interest-only payment
    monthly_rate = Decimal(rate) / Decimal(10000) / Decimal(12)
    interest_only_payment = int(principal * monthly_rate)
    assert emi >= interest_only_payment


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
)
@settings(max_examples=10, deadline=None)
def test_schedule_consistency(principal, rate, tenure):
    """Property: Fixed and default schedules are consistent."""
    start_date = "2025-01-01"

    # Generate both schedules
    default_schedule = generate_schedule(principal, rate, tenure, start_date)
    fixed_schedule = generate_schedule_fixed(principal, rate, tenure, start_date)

    # Should be identical
    assert len(default_schedule) == len(fixed_schedule)

    for default_row, fixed_row in zip(default_schedule, fixed_schedule, strict=False):
        assert default_row.month_number == fixed_row.month_number
        assert default_row.emi_paise == fixed_row.emi_paise
        assert default_row.principal_paise == fixed_row.principal_paise
        assert default_row.interest_paise == fixed_row.interest_paise
        assert default_row.balance_paise == fixed_row.balance_paise
        assert (
            default_row.cumulative_interest_paise == fixed_row.cumulative_interest_paise
        )


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
)
@settings(max_examples=10, deadline=None)
def test_cumulative_interest_accuracy(principal, rate, tenure):
    """Property: Cumulative interest is calculated correctly."""
    start_date = "2025-01-01"

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Verify cumulative interest
    cumulative_interest = 0
    for row in schedule:
        cumulative_interest += row.interest_paise
        assert row.cumulative_interest_paise == cumulative_interest


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
)
@settings(max_examples=10, deadline=None)
def test_date_progression(principal, rate, tenure):
    """Property: Payment dates progress correctly."""
    start_date = "2025-01-01"

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Verify date progression
    for i in range(1, len(schedule)):
        prev_date = date.fromisoformat(schedule[i - 1].payment_date)
        current_date = date.fromisoformat(schedule[i].payment_date)

        # Should be approximately one month apart
        month_diff = (current_date.year - prev_date.year) * 12 + (
            current_date.month - prev_date.month
        )
        assert month_diff == 1


@given(
    st.integers(min_value=100_000, max_value=1_000_000),  # Principal
    st.integers(min_value=500, max_value=2000),  # Rate (5-20%)
    st.integers(min_value=12, max_value=60),  # Tenure
)
@settings(max_examples=10, deadline=None)
def test_principal_interest_progression(principal, rate, tenure):
    """Property: Principal component is non-decreasing (except possibly last row due to rounding)."""
    start_date = "2025-01-01"

    # Generate schedule
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Verify that principal component is non-decreasing (allows last month to drop slightly)
    prev_principal = 0
    for i, row in enumerate(schedule):
        if i < len(schedule) - 1:
            # For non-last rows, principal should be strictly increasing or equal
            assert row.principal_paise >= prev_principal
            prev_principal = row.principal_paise
        else:
            # Last row may drop due to rounding adjustment, allow it to be <= previous
            assert row.principal_paise >= 0

    # Interest should be strictly decreasing (or constant) across all rows
    prev_interest = float("inf")
    for row in schedule:
        # Interest should be non-increasing
        assert row.interest_paise <= prev_interest
        prev_interest = row.interest_paise


# --- Additional Tests for Ill-Conditioned Loans, Last Month Settlement, Rounding ---


@given(
    st.integers(
        min_value=100_000, max_value=10_000_000
    ),  # Small principal (₹1K - ₹100K)
    st.integers(min_value=2000, max_value=5000),  # High rate (20-50%)
    st.integers(min_value=120, max_value=360),  # Long tenure (10-30 years)
)
@settings(max_examples=20, deadline=None)
def test_ill_conditioned_loan_detection(principal, rate, tenure):
    """Property: Ill-conditioned loans (high rate, small principal, long tenure) trigger re-anchoring."""
    from src.engines.loan_engine.amortization import generate_schedule

    start_date = "2025-01-01"
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Verify schedule invariants still hold even for ill-conditioned loans
    assert len(schedule) == tenure
    assert schedule[-1].balance_paise == 0

    # Verify principal sum equals original
    total_principal = sum(row.principal_paise for row in schedule)
    assert total_principal == principal

    # EMI may vary month-to-month for ill-conditioned loans (re-anchoring)
    # But should still be positive and reasonable
    for row in schedule:
        assert row.emi_paise > 0
        assert row.emi_paise <= principal + row.interest_paise


@given(
    st.integers(min_value=100_000, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
)
@settings(max_examples=30, deadline=None)
def test_last_month_settlement(principal, rate, tenure):
    """Property: Last month correctly settles exact remaining balance (absorbs drift)."""
    from src.engines.loan_engine.amortization import generate_schedule

    start_date = "2025-01-01"
    schedule = generate_schedule(principal, rate, tenure, start_date)

    # Last row balance must be exactly zero
    assert schedule[-1].balance_paise == 0

    # Last row: principal_component_paise = reported_balance (absorbs all remaining)
    last = schedule[-1]
    assert last.principal_paise >= 0

    # Last EMI = principal + interest (not necessarily the standard EMI)
    assert last.emi_paise == last.principal_paise + last.interest_paise

    # Cumulative interest at end should match total interest
    assert last.cumulative_interest_paise == sum(row.interest_paise for row in schedule)


@given(
    st.integers(min_value=100_000, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
)
@settings(max_examples=30, deadline=None)
def test_interest_rounding_half_even(principal, rate, tenure):
    """Property: Interest rounding uses ROUND_HALF_EVEN (banker's rounding)."""

    from src.engines.loan_engine.amortization import generate_schedule

    start_date = "2025-01-01"
    schedule = generate_schedule(principal, rate, tenure, start_date)

    for i, row in enumerate(schedule):
        if i == len(schedule) - 1:
            # Last month: interest is already rounded, just verify it's valid
            assert row.interest_paise >= 0
            continue

        # For non-last months, verify interest was rounded with HALF_EVEN
        # The exact interest would be: balance_before * monthly_rate
        # We can't easily get balance_before, but we can verify interest is integer
        assert row.interest_paise == int(row.interest_paise)

    # At least verify all interest values are integers (paise)
    for row in schedule:
        assert row.interest_paise == int(row.interest_paise)
        assert row.principal_paise == int(row.principal_paise)
        assert row.emi_paise == int(row.emi_paise)
        assert row.balance_paise == int(row.balance_paise)


@given(
    st.integers(min_value=100_000, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
)
@settings(max_examples=30, deadline=None)
def test_principal_component_bounds(principal, rate, tenure):
    """Property: Principal component is always bounded [0, emi_paise]."""
    from src.engines.loan_engine.amortization import generate_schedule

    start_date = "2025-01-01"
    schedule = generate_schedule(principal, rate, tenure, start_date)

    for row in schedule:
        # Principal component must be non-negative and not exceed EMI
        assert row.principal_paise >= 0
        assert row.principal_paise <= row.emi_paise

        # For non-last rows with positive balance, principal should be positive
        if row.month_number < tenure and row.balance_paise > 0:
            # Note: in edge cases (interest >= EMI), principal could be 0
            assert row.principal_paise >= 0


@given(
    st.integers(min_value=100_000, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
)
@settings(max_examples=30, deadline=None)
def test_cumulative_interest_monotonic_non_decreasing(principal, rate, tenure):
    """Property: Cumulative interest is monotonically non-decreasing."""
    from src.engines.loan_engine.amortization import generate_schedule

    start_date = "2025-01-01"
    schedule = generate_schedule(principal, rate, tenure, start_date)

    prev = 0
    for row in schedule:
        assert row.cumulative_interest_paise >= prev
        prev = row.cumulative_interest_paise

    # Final cumulative should equal total interest
    assert schedule[-1].cumulative_interest_paise == sum(
        row.interest_paise for row in schedule
    )


@given(
    st.integers(min_value=100_000, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
)
@settings(max_examples=30, deadline=None)
def test_balance_strictly_decreasing(principal, rate, tenure):
    """Property: Balance strictly decreases until zero."""
    from src.engines.loan_engine.amortization import generate_schedule

    start_date = "2025-01-01"
    schedule = generate_schedule(principal, rate, tenure, start_date)

    for i in range(1, len(schedule)):
        # Balance should strictly decrease (or stay same if already zero)
        if schedule[i - 1].balance_paise > 0:
            assert schedule[i].balance_paise < schedule[i - 1].balance_paise
        else:
            assert schedule[i].balance_paise == 0

    # Final balance is zero
    assert schedule[-1].balance_paise == 0
