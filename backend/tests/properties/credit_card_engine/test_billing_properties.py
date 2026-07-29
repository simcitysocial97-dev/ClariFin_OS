"""
Property-based tests for credit card engine billing module.

These tests verify the mathematical invariants and business rules of the credit card
billing calculations using property-based testing techniques.
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.engines.credit_card_engine.billing import (
    compute_due_date,
    compute_minimum_due,
    compute_next_statement_date,
    compute_statement_dates,
)

# Constants for testing
MAX_BALANCE_PAISE = 10_000_000_00  # ₹10 lakh
MIN_BALANCE_PAISE = 1_000         # ₹10
MAX_MIN_DUE_PCT_BPS = 10000       # 100%
MIN_MIN_DUE_PCT_BPS = 100         # 1%
MAX_FLOOR_PAISE = 100_000         # ₹1000
MIN_FLOOR_PAISE = 1_000           # ₹10


# Date strategies
@st.composite
def date_strategy(draw):
    """Generate valid dates for testing."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Use 28 to avoid month-end issues
    return date(year, month, day)


@given(
    date_strategy(),
    st.integers(min_value=0, max_value=60)  # 0-60 days offset
)
@settings(max_examples=30, deadline=None)
def test_compute_due_date_invariants(statement_date, due_day_offset):
    """Property: compute_due_date must satisfy all invariants."""
    due_date = compute_due_date(statement_date, due_day_offset)

    assert due_date >= statement_date

    expected_date = statement_date + timedelta(days=due_day_offset)
    assert due_date == expected_date

    if due_day_offset > 0:
        assert due_date > statement_date

    if due_day_offset == 0:
        assert due_date == statement_date


@given(
    st.integers(min_value=1, max_value=31),  # Billing day
    date_strategy(),                         # Reference date
    st.booleans()                            # Whether to provide last statement date
)
@settings(max_examples=50, deadline=None)
def test_compute_next_statement_date_invariants(billing_day, reference_date, has_last_statement):
    """Property: compute_next_statement_date must satisfy all invariants."""
    last_statement_date = None
    if has_last_statement:
        prev_month = reference_date.month - 1 if reference_date.month > 1 else 12
        prev_year = reference_date.year if reference_date.month > 1 else reference_date.year - 1
        _, max_prev_day = calendar.monthrange(prev_year, prev_month)
        
        last_statement_date = date(
            prev_year,
            prev_month,
            min(billing_day, max_prev_day)
        )

    next_statement = compute_next_statement_date(
        billing_day, reference_date, last_statement_date
    )

    assert next_statement >= reference_date

    _, target_max_day = calendar.monthrange(next_statement.year, next_statement.month)
    expected_day = min(billing_day, target_max_day)
    assert next_statement.day == expected_day, (
        f"Expected day {expected_day} for billing_day {billing_day} in {next_statement}, got {next_statement.day}"
    )

    if last_statement_date is not None:
        months_diff = (next_statement.year - last_statement_date.year) * 12 + (next_statement.month - last_statement_date.month)
        assert 1 <= months_diff <= 2, (
            f"Next statement {next_statement} is {months_diff} months after last statement {last_statement_date}, "
            f"expected 1-2 months"
        )


@given(
    st.integers(min_value=1, max_value=31),  # Billing day
    st.integers(min_value=0, max_value=60),  # Due day offset
    date_strategy(),                         # Reference date
    st.booleans()                            # Whether to provide last statement date
)
@settings(max_examples=30, deadline=None)
def test_compute_statement_dates_invariants(billing_day, due_day_offset, reference_date, has_last_statement):
    """Property: compute_statement_dates must satisfy all invariants."""
    last_statement_date = None
    if has_last_statement:
        last_statement_date = date(
            reference_date.year - 1 if reference_date.month == 1 else reference_date.year,
            reference_date.month - 1 if reference_date.month > 1 else 12,
            min(billing_day, 28)
        )

    dates = compute_statement_dates(
        billing_day, due_day_offset, reference_date, last_statement_date
    )

    assert isinstance(dates, dict)
    assert "statement_date" in dates
    assert "due_date" in dates

    statement_date = date.fromisoformat(dates["statement_date"])
    due_date = date.fromisoformat(dates["due_date"])

    assert due_date >= statement_date
    assert statement_date >= reference_date

    expected_due_date = statement_date + timedelta(days=due_day_offset)
    assert due_date == expected_due_date


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_MIN_DUE_PCT_BPS, max_value=MAX_MIN_DUE_PCT_BPS),
    st.integers(min_value=MIN_FLOOR_PAISE, max_value=MAX_FLOOR_PAISE)
)
@settings(max_examples=50, deadline=None)
def test_compute_minimum_due_invariants(total_outstanding, min_due_pct, floor_paise):
    """Property: compute_minimum_due must satisfy all invariants."""
    min_due = compute_minimum_due(total_outstanding, min_due_pct, floor_paise)

    assert min_due >= 0

    if total_outstanding == 0:
        assert min_due == 0

    assert min_due <= total_outstanding

    if floor_paise <= total_outstanding:
        assert min_due >= floor_paise
    else:
        assert min_due == total_outstanding

    pct_amount = int((Decimal(total_outstanding) * Decimal(min_due_pct) / Decimal(10000)).quantize(Decimal(1)))
    expected = min(max(floor_paise, pct_amount), total_outstanding)
    assert min_due == expected


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_MIN_DUE_PCT_BPS, max_value=MAX_MIN_DUE_PCT_BPS),
    st.integers(min_value=MIN_FLOOR_PAISE, max_value=MAX_FLOOR_PAISE)
)
@settings(max_examples=30, deadline=None)
def test_compute_minimum_due_math_accuracy(total_outstanding, min_due_pct, floor_paise):
    """Property: compute_minimum_due math must be accurate."""
    min_due = compute_minimum_due(total_outstanding, min_due_pct, floor_paise)

    if total_outstanding == 0:
        expected_min_due = 0
    else:
        pct_amount = (
            Decimal(total_outstanding) * Decimal(min_due_pct) / Decimal(10000)
        )
        pct_amount_paise = int(pct_amount.quantize(Decimal(1), rounding="ROUND_HALF_EVEN"))
        expected_min_due = min(max(floor_paise, pct_amount_paise), total_outstanding)

    assert min_due == expected_min_due


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_MIN_DUE_PCT_BPS, max_value=MAX_MIN_DUE_PCT_BPS)
)
@settings(max_examples=30, deadline=None)
def test_minimum_due_proportionality(total_outstanding, min_due_pct):
    """Property: Minimum due is proportional to outstanding balance."""
    pct_amount = int((Decimal(total_outstanding) * Decimal(min_due_pct) / Decimal(10000)).quantize(Decimal(1)))
    base_min_due = compute_minimum_due(total_outstanding, min_due_pct, 10000)

    double_outstanding = total_outstanding * 2
    double_min_due = compute_minimum_due(double_outstanding, min_due_pct, 10000)

    if base_min_due > 10000 and pct_amount > 10000:
        expected_double_base = int((Decimal(double_outstanding) * Decimal(min_due_pct) / Decimal(10000)).quantize(Decimal(1)))
        expected_double = min(max(10000, expected_double_base), double_outstanding)
        assert double_min_due == expected_double


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_FLOOR_PAISE, max_value=MAX_FLOOR_PAISE)
)
@settings(max_examples=20, deadline=None)
def test_minimum_due_floor_effects(total_outstanding, floor_paise):
    """Property: Minimum due respects floor amount."""
    min_due = compute_minimum_due(total_outstanding, 100, floor_paise)

    assert min_due >= min(floor_paise, total_outstanding)

    if total_outstanding < floor_paise * 100:
        assert min_due == min(floor_paise, total_outstanding)


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_MIN_DUE_PCT_BPS, max_value=MAX_MIN_DUE_PCT_BPS)
)
@settings(max_examples=20, deadline=None)
def test_minimum_due_percentage_effects(total_outstanding, min_due_pct):
    """Property: Minimum due respects percentage amount."""
    min_due = compute_minimum_due(total_outstanding, min_due_pct, 1000)

    pct_amount = int((Decimal(total_outstanding) * Decimal(min_due_pct) / Decimal(10000)).quantize(Decimal(1)))

    if total_outstanding > 100000:
        assert min_due == pct_amount


@given(
    date_strategy(),
    st.integers(min_value=1, max_value=31)  # Billing day
)
@settings(max_examples=20, deadline=None)
def test_statement_date_month_end_safety(reference_date, billing_day):
    """Property: Statement dates handle month-end correctly."""
    next_statement = compute_next_statement_date(billing_day, reference_date)

    last_day_of_month = (next_statement.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    assert next_statement.day <= last_day_of_month.day

    if billing_day <= 28:
        assert next_statement.day == billing_day


@given(
    date_strategy(),
    st.integers(min_value=0, max_value=60)  # Due day offset
)
@settings(max_examples=20, deadline=None)
def test_due_date_cross_month_boundary(statement_date, due_day_offset):
    """Property: Due dates handle month boundaries correctly."""
    due_date = compute_due_date(statement_date, due_day_offset)

    expected_date = statement_date + timedelta(days=due_day_offset)
    assert due_date == expected_date

    if statement_date.month != due_date.month:
        assert due_date.year >= statement_date.year
        if due_date.year == statement_date.year:
            assert due_date.month > statement_date.month


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_MIN_DUE_PCT_BPS, max_value=MAX_MIN_DUE_PCT_BPS)
)
@settings(max_examples=10, deadline=None)
def test_minimum_due_edge_cases(total_outstanding, min_due_pct):
    """Property: Minimum due handles edge cases correctly."""
    assert compute_minimum_due(0, min_due_pct, 10000) == 0
    assert compute_minimum_due(total_outstanding, 0, 10000) == min(10000, total_outstanding)
    assert compute_minimum_due(total_outstanding, 10000, 10000) == total_outstanding

    min_due = compute_minimum_due(total_outstanding, min_due_pct, 0)
    assert min_due >= 0
    if total_outstanding > 0:
        assert min_due > 0
