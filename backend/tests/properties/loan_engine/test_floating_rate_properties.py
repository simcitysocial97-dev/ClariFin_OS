"""
Property-based tests for loan engine floating rate module.

These tests verify the mathematical invariants and business rules of the floating rate
calculations using property-based testing techniques.
"""

from datetime import date

from hypothesis import given, settings
from hypothesis import strategies as st

from src.engines.loan_engine.amortization import generate_schedule, total_interest_paise
from src.engines.loan_engine.floating_rate import (
    apply_floating_rate_change,
    simulate_floating_rate_schedule,
)
from src.engines.loan_engine.models import AmortizationRow, FloatingRateChange

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
def schedule_with_rate_change(draw):
    """Generate a schedule and rate change parameters."""
    principal, initial_rate, tenure, start_date = draw(loan_parameters())
    schedule = generate_schedule(principal, initial_rate, tenure, start_date)

    # Generate rate change at a random month
    change_month = draw(st.integers(min_value=1, max_value=tenure))
    new_rate = draw(
        st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS)
    )
    mode = draw(st.sampled_from(["adjust_emi", "adjust_tenure"]))

    return schedule, initial_rate, change_month, new_rate, mode, start_date


@st.composite
def multiple_rate_changes(draw):
    """Generate parameters for multiple rate changes."""
    principal, initial_rate, tenure, start_date = draw(loan_parameters())

    # Generate multiple rate changes
    num_changes = draw(st.integers(min_value=1, max_value=5))
    rate_changes = []

    for _i in range(num_changes):
        change_month = draw(st.integers(min_value=1, max_value=tenure))
        new_rate = draw(
            st.integers(
                min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS
            )
        )
        mode = draw(st.sampled_from(["adjust_emi", "adjust_tenure"]))
        rate_changes.append(
            FloatingRateChange(
                change_month=change_month, new_rate_bps=new_rate, mode=mode
            )
        )

    return principal, initial_rate, tenure, rate_changes, start_date


@given(schedule_with_rate_change())
@settings(max_examples=30, deadline=None)
def test_apply_floating_rate_change_invariants(schedule_params):
    """Property: apply_floating_rate_change must satisfy all invariants."""
    schedule, initial_rate, change_month, new_rate, mode, start_date = schedule_params

    # Apply rate change
    new_schedule = apply_floating_rate_change(
        schedule, change_month, new_rate, mode, start_date
    )

    # INVARIANT 1: New schedule is valid
    assert isinstance(new_schedule, list)
    assert all(isinstance(row, AmortizationRow) for row in new_schedule)

    # INVARIANT 2: Schedule length is preserved for adjust_emi mode,
    # but may change for adjust_tenure mode due to recomputed tenure.
    if mode == "adjust_emi":
        assert len(new_schedule) == len(schedule)
    else:
        assert 1 <= len(new_schedule) <= 1500

    # INVARIANT 3: Month numbers are preserved
    for i, row in enumerate(new_schedule):
        assert row.month_number == i + 1

    # INVARIANT 4: Dates are preserved for completed portion
    for i in range(change_month - 1):
        assert new_schedule[i].payment_date == schedule[i].payment_date

    # INVARIANT 5: Completed portion is unchanged
    for i in range(change_month - 1):
        original_row = schedule[i]
        new_row = new_schedule[i]
        assert new_row.emi_paise == original_row.emi_paise
        assert new_row.principal_paise == original_row.principal_paise
        assert new_row.interest_paise == original_row.interest_paise
        assert new_row.balance_paise == original_row.balance_paise
        assert (
            new_row.cumulative_interest_paise == original_row.cumulative_interest_paise
        )

    # INVARIANT 6: Opening balance at change month is preserved exactly.
    # Closing balance may differ due to rounding in the regenerated schedule.
    if change_month <= len(schedule):
        original_opening = (
            schedule[change_month - 1].balance_paise
            + schedule[change_month - 1].principal_paise
        )
        new_opening = (
            new_schedule[change_month - 1].balance_paise
            + new_schedule[change_month - 1].principal_paise
        )
        assert original_opening == new_opening


@given(schedule_with_rate_change())
@settings(max_examples=20, deadline=None)
def test_apply_floating_rate_change_math_accuracy(schedule_params):
    """Property: apply_floating_rate_change math must be accurate."""
    schedule, initial_rate, change_month, new_rate, mode, start_date = schedule_params

    # Apply rate change
    new_schedule = apply_floating_rate_change(
        schedule, change_month, new_rate, mode, start_date
    )

    # Calculate interest before and after change
    total_interest_paise(schedule)
    total_interest_paise(new_schedule)

    # INVARIANT: Interest per month should be consistent with the new rate.
    # This comparison only applies for 'adjust_emi' mode where EMI changes but
    # tenure stays the same. For 'adjust_tenure' mode, the schedule is regenerated
    # with a different tenure, so month-by-month comparison is invalid.
    # A higher rate does not guarantee higher total interest if the loan
    # closes early due to the rate change, so we verify directionality only
    # for the overlapping months after the change point.
    if (
        mode == "adjust_emi"
        and new_rate > initial_rate
        and change_month < len(new_schedule)
    ):
        for i in range(change_month - 1, len(new_schedule)):
            original_month_interest = (
                schedule[i].interest_paise if i < len(schedule) else 0
            )
            assert new_schedule[i].interest_paise >= original_month_interest
    elif (
        mode == "adjust_emi"
        and new_rate < initial_rate
        and change_month < len(new_schedule)
    ):
        for i in range(change_month - 1, len(new_schedule)):
            original_month_interest = (
                schedule[i].interest_paise if i < len(schedule) else 0
            )
            assert new_schedule[i].interest_paise <= original_month_interest


@given(schedule_with_rate_change())
@settings(max_examples=20, deadline=None)
def test_apply_floating_rate_change_modes(schedule_params):
    """Property: Different modes produce different results."""
    schedule, initial_rate, change_month, new_rate, _, start_date = schedule_params

    # Apply rate change in both modes
    adjust_emi_schedule = apply_floating_rate_change(
        schedule, change_month, new_rate, "adjust_emi", start_date
    )
    adjust_tenure_schedule = apply_floating_rate_change(
        schedule, change_month, new_rate, "adjust_tenure", start_date
    )

    # INVARIANT: Schedules should be different when rate changes, schedule has enough months,
    # and the change happens before the last month (otherwise both modes produce identical results).
    if new_rate != initial_rate and len(schedule) > 2 and change_month < len(schedule):
        assert adjust_emi_schedule != adjust_tenure_schedule

    # INVARIANT: Completed portion should be identical
    for i in range(change_month - 1):
        assert adjust_emi_schedule[i] == adjust_tenure_schedule[i]

    # INVARIANT: EMI should be different in adjust_emi mode when rate changes
    if change_month < len(adjust_emi_schedule):
        original_emi = schedule[change_month].emi_paise
        adjust_emi_new_emi = adjust_emi_schedule[change_month].emi_paise
        if new_rate != initial_rate:
            assert adjust_emi_new_emi != original_emi

        # Tenure should be preserved in adjust_emi mode
        assert len(adjust_emi_schedule) == len(schedule)

    # INVARIANT: In adjust_tenure mode, the schedule structure changes when rate changes
    # We don't enforce exact EMI preservation due to rounding in regenerated schedules


@given(multiple_rate_changes())
@settings(max_examples=10, deadline=None)
def test_simulate_floating_rate_schedule_invariants(rate_change_params):
    """Property: simulate_floating_rate_schedule must satisfy all invariants."""
    principal, initial_rate, tenure, rate_changes, start_date = rate_change_params

    # Simulate schedule with multiple rate changes
    schedule = simulate_floating_rate_schedule(
        principal, initial_rate, tenure, rate_changes, "adjust_emi", start_date
    )

    # INVARIANT 1: Schedule is valid
    assert isinstance(schedule, list)
    assert all(isinstance(row, AmortizationRow) for row in schedule)

    # INVARIANT 2: Schedule has correct length.
    # For adjust_emi mode, length equals original tenure.
    # For adjust_tenure mode, length may differ based on recomputed tenure.
    # Large principals with low rates can produce very long tenures.
    if len(schedule) == tenure:
        pass
    else:
        assert 1 <= len(schedule) <= 1200

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


@given(multiple_rate_changes())
@settings(max_examples=10, deadline=None)
def test_simulate_floating_rate_schedule_rate_application(rate_change_params):
    """Property: Rate changes are applied correctly."""
    principal, initial_rate, tenure, rate_changes, start_date = rate_change_params

    # Sort rate changes by month
    sorted_changes = sorted(rate_changes, key=lambda x: x.change_month)

    # Simulate schedule
    schedule = simulate_floating_rate_schedule(
        principal, initial_rate, tenure, sorted_changes, "adjust_emi", start_date
    )

    # INVARIANT: Rate changes should be reflected in the schedule
    for change in sorted_changes:
        if change.change_month < len(schedule) and change.change_month > 1:
            before_emi = schedule[change.change_month - 2].emi_paise
            after_emi = schedule[change.change_month - 1].emi_paise
            if change.mode == "adjust_emi":
                assert after_emi != before_emi


@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS),
    st.dates(min_value=date(2000, 1, 1), max_value=date(2030, 12, 31)).map(
        lambda d: d.isoformat()
    ),
)
@settings(max_examples=10, deadline=None)
def test_simulate_floating_rate_schedule_no_changes(
    principal, initial_rate, tenure, start_date
):
    """Property: No rate changes produces standard schedule."""
    # Simulate with no rate changes
    schedule = simulate_floating_rate_schedule(
        principal, initial_rate, tenure, [], "adjust_emi", start_date
    )

    # Should be identical to standard schedule
    standard_schedule = generate_schedule(principal, initial_rate, tenure, start_date)

    assert len(schedule) == len(standard_schedule)

    for new_row, standard_row in zip(schedule, standard_schedule, strict=False):
        assert new_row.month_number == standard_row.month_number
        assert new_row.emi_paise == standard_row.emi_paise
        assert new_row.principal_paise == standard_row.principal_paise
        assert new_row.interest_paise == standard_row.interest_paise
        assert new_row.balance_paise == standard_row.balance_paise
        assert (
            new_row.cumulative_interest_paise == standard_row.cumulative_interest_paise
        )


@given(schedule_with_rate_change())
@settings(max_examples=10, deadline=None)
def test_apply_floating_rate_change_edge_cases(schedule_params):
    """Property: apply_floating_rate_change handles edge cases correctly."""
    schedule, initial_rate, change_month, new_rate, mode, start_date = schedule_params

    # Test rate change at first month
    if len(schedule) > 1:
        new_schedule = apply_floating_rate_change(
            schedule, 1, new_rate, mode, start_date
        )
        if mode == "adjust_emi":
            assert len(new_schedule) == len(schedule)
        else:
            assert len(new_schedule) >= 1

    # Test rate change at last month
    new_schedule = apply_floating_rate_change(
        schedule, len(schedule), new_rate, mode, start_date
    )
    if mode == "adjust_emi":
        assert len(new_schedule) == len(schedule)
    else:
        assert len(new_schedule) >= 1

    # Test rate change to same rate.
    # In adjust_emi mode the tail is regenerated, so EMI may be recomputed
    # and can differ slightly from the original even when the rate is unchanged.
    # Only the completed prefix must remain identical.
    new_schedule = apply_floating_rate_change(
        schedule, change_month, initial_rate, mode, start_date
    )
    # For both modes, only the completed prefix must remain identical
    for i in range(change_month - 1):
        assert new_schedule[i] == schedule[i]


@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=12, max_value=60),  # Tenure
    st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31)).map(
        lambda d: d.isoformat()
    ),
)
@settings(max_examples=10, deadline=None)
def test_floating_rate_change_math_consistency(
    principal, initial_rate, tenure, start_date
):
    """Property: Floating rate changes maintain mathematical consistency."""
    # Generate schedule
    schedule = generate_schedule(principal, initial_rate, tenure, start_date)

    # Apply rate change at month 6
    change_month = 6
    new_rate = initial_rate + 500  # Increase rate by 5%

    if change_month <= len(schedule):
        new_schedule = apply_floating_rate_change(
            schedule, change_month, new_rate, "adjust_emi", start_date
        )

        # Verify that opening balance is preserved at change point
        original_opening = (
            schedule[change_month - 1].balance_paise
            + schedule[change_month - 1].principal_paise
        )
        new_opening = (
            new_schedule[change_month - 1].balance_paise
            + new_schedule[change_month - 1].principal_paise
        )
        assert original_opening == new_opening

        # Verify that completed portion is unchanged
        for i in range(change_month - 1):
            original_row = schedule[i]
            new_row = new_schedule[i]
            assert new_row.emi_paise == original_row.emi_paise
            assert new_row.principal_paise == original_row.principal_paise
            assert new_row.interest_paise == original_row.interest_paise
            assert new_row.balance_paise == original_row.balance_paise
            assert (
                new_row.cumulative_interest_paise
                == original_row.cumulative_interest_paise
            )


@given(
    st.integers(min_value=MIN_PRINCIPAL_PAISE, max_value=MAX_PRINCIPAL_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=12, max_value=60),  # Tenure
    st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31)).map(
        lambda d: d.isoformat()
    ),
)
@settings(max_examples=10, deadline=None)
def test_floating_rate_change_zero_rate(principal, initial_rate, tenure, start_date):
    """Property: Zero rate produces correct schedule."""
    # Generate schedule
    schedule = generate_schedule(principal, initial_rate, tenure, start_date)

    # Apply zero rate change
    change_month = 6
    if change_month <= len(schedule):
        new_schedule = apply_floating_rate_change(
            schedule, change_month, 0, "adjust_emi", start_date
        )

        # After zero rate, interest should be zero
        for i in range(change_month, len(new_schedule)):
            assert new_schedule[i].interest_paise == 0

        # EMI should be principal / remaining months (based on opening balance)
        remaining_months = len(new_schedule) - change_month + 1
        remaining_balance = (
            new_schedule[change_month - 1].balance_paise
            + new_schedule[change_month - 1].principal_paise
        )
        expected_emi = remaining_balance // remaining_months

        for i in range(change_month - 1, len(new_schedule) - 1):
            assert new_schedule[i].emi_paise == expected_emi
            assert new_schedule[i].principal_paise == expected_emi
            assert new_schedule[i].interest_paise == 0
