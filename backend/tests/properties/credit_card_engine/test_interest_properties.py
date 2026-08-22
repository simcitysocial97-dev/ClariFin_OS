"""
Property-based tests for credit card engine interest module.

These tests verify the mathematical invariants and business rules of the credit card
interest calculations using property-based testing techniques.
"""

from datetime import date, timedelta
from decimal import Decimal

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.engines.credit_card_engine.interest import (
    bps_to_daily_rate,
    compute_daily_interest,
    compute_monthly_interest_charge,
    compute_monthly_interest_simple,
)

# Constants for testing
MAX_INTEREST_RATE_BPS = 4800  # 48% annual (max for credit cards)
MIN_INTEREST_RATE_BPS = 1200  # 12% annual (min for credit cards)
MAX_BALANCE_PAISE = 10_000_000_00  # ₹10 lakh
MIN_BALANCE_PAISE = 1_000  # ₹10
MAX_DAYS_IN_CYCLE = 31
MIN_DAYS_IN_CYCLE = 28


@given(st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS))
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_bps_to_daily_rate_invariants(rate_bps):
    """Property: bps_to_daily_rate must satisfy all invariants."""
    # Compute daily rate
    daily_rate = bps_to_daily_rate(rate_bps)

    # INVARIANT 1: Daily rate is positive
    assert daily_rate > 0

    # INVARIANT 2: Daily rate is less than annual rate
    annual_rate = Decimal(rate_bps) / Decimal(10000)
    assert daily_rate < annual_rate

    # INVARIANT 3: Daily rate equals annual rate / 365
    expected_daily_rate = annual_rate / Decimal(365)
    assert daily_rate == expected_daily_rate


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_compute_daily_interest_invariants(balance_paise, rate_bps):
    """Property: compute_daily_interest must satisfy all invariants."""
    # Compute daily interest
    interest = compute_daily_interest(balance_paise, rate_bps)

    # INVARIANT 1: Interest is non-negative
    assert interest >= 0

    # INVARIANT 2: Zero balance produces zero interest
    if balance_paise == 0:
        assert interest == 0

    # INVARIANT 3: Zero rate produces zero interest
    if rate_bps == 0:
        assert interest == 0

    # INVARIANT 4: Interest increases with balance
    if balance_paise > 0 and rate_bps > 0:
        lower_balance_interest = compute_daily_interest(balance_paise - 1, rate_bps)
        assert interest >= lower_balance_interest

    # INVARIANT 5: Interest increases with rate
    if balance_paise > 0 and rate_bps > MIN_INTEREST_RATE_BPS:
        lower_rate_interest = compute_daily_interest(balance_paise, rate_bps - 100)
        assert interest >= lower_rate_interest


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_compute_daily_interest_math_accuracy(balance_paise, rate_bps):
    """Property: compute_daily_interest math must be accurate."""
    # Compute daily interest
    interest = compute_daily_interest(balance_paise, rate_bps)

    # Calculate expected interest using the formula
    if balance_paise == 0 or rate_bps == 0:
        expected_interest = 0
    else:
        daily_rate = Decimal(rate_bps) / Decimal(3650000)
        expected_interest_decimal = Decimal(balance_paise) * daily_rate
        expected_interest = int(
            expected_interest_decimal.quantize(Decimal(1), rounding="ROUND_HALF_EVEN")
        )

    # Verify calculation
    assert interest == expected_interest


@st.composite
def daily_balances_strategy(draw):
    """Generate valid daily balances for testing."""
    num_days = draw(
        st.integers(min_value=MIN_DAYS_IN_CYCLE, max_value=MAX_DAYS_IN_CYCLE)
    )
    start_date = date(2025, 1, 1)

    # Generate daily balances with some variation
    balances = []
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        balance = draw(
            st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE)
        )
        balances.append((current_date.isoformat(), balance))

    return balances


@given(
    daily_balances_strategy(),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_compute_monthly_interest_charge_invariants(daily_balances, rate_bps):
    """Property: compute_monthly_interest_charge must satisfy all invariants."""
    # Compute monthly interest
    interest = compute_monthly_interest_charge(daily_balances, rate_bps)

    # INVARIANT 1: Interest is non-negative
    assert interest >= 0

    # INVARIANT 2: Zero rate produces zero interest
    if rate_bps == 0:
        assert interest == 0

    # INVARIANT 3: Empty balances produce zero interest
    if not daily_balances:
        assert interest == 0

    # INVARIANT 4: Interest increases with balance
    if daily_balances and rate_bps > 0:
        # Create a version with lower balances
        lower_balances = [
            (date, max(0, balance - 1000)) for date, balance in daily_balances
        ]
        lower_interest = compute_monthly_interest_charge(lower_balances, rate_bps)
        assert interest >= lower_interest

    # INVARIANT 5: Interest increases with rate
    if daily_balances and rate_bps > MIN_INTEREST_RATE_BPS:
        lower_rate_interest = compute_monthly_interest_charge(
            daily_balances, rate_bps - 100
        )
        assert interest >= lower_rate_interest


@given(
    daily_balances_strategy(),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_compute_monthly_interest_charge_math_accuracy(daily_balances, rate_bps):
    """Property: compute_monthly_interest_charge math must be accurate."""
    # Compute monthly interest
    interest = compute_monthly_interest_charge(daily_balances, rate_bps)

    # Calculate expected interest by summing daily interest
    expected_interest = 0
    for _date_iso, balance in daily_balances:
        expected_interest += compute_daily_interest(balance, rate_bps)

    # Verify calculation
    assert interest == expected_interest


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_DAYS_IN_CYCLE, max_value=MAX_DAYS_IN_CYCLE),
)
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_compute_monthly_interest_simple_invariants(
    avg_balance, rate_bps, days_in_cycle
):
    """Property: compute_monthly_interest_simple must satisfy all invariants."""
    # Compute monthly interest
    interest = compute_monthly_interest_simple(avg_balance, rate_bps, days_in_cycle)

    # INVARIANT 1: Interest is non-negative
    assert interest >= 0

    # INVARIANT 2: Zero balance produces zero interest
    if avg_balance == 0:
        assert interest == 0

    # INVARIANT 3: Zero rate produces zero interest
    if rate_bps == 0:
        assert interest == 0

    # INVARIANT 4: Zero days produces zero interest
    if days_in_cycle == 0:
        assert interest == 0

    # INVARIANT 5: Interest increases with balance
    if avg_balance > 0 and rate_bps > 0 and days_in_cycle > 0:
        lower_balance_interest = compute_monthly_interest_simple(
            avg_balance - 1, rate_bps, days_in_cycle
        )
        assert interest >= lower_balance_interest

    # INVARIANT 6: Interest increases with rate
    if avg_balance > 0 and rate_bps > MIN_INTEREST_RATE_BPS and days_in_cycle > 0:
        lower_rate_interest = compute_monthly_interest_simple(
            avg_balance, rate_bps - 100, days_in_cycle
        )
        assert interest >= lower_rate_interest

    # INVARIANT 7: Interest increases with days
    if avg_balance > 0 and rate_bps > 0 and days_in_cycle > MIN_DAYS_IN_CYCLE:
        fewer_days_interest = compute_monthly_interest_simple(
            avg_balance, rate_bps, days_in_cycle - 1
        )
        assert interest >= fewer_days_interest


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_DAYS_IN_CYCLE, max_value=MAX_DAYS_IN_CYCLE),
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_compute_monthly_interest_simple_math_accuracy(
    avg_balance, rate_bps, days_in_cycle
):
    """Property: compute_monthly_interest_simple math must be accurate."""
    # Compute monthly interest
    interest = compute_monthly_interest_simple(avg_balance, rate_bps, days_in_cycle)

    # Calculate expected interest using the formula
    if avg_balance == 0 or rate_bps == 0 or days_in_cycle == 0:
        expected_interest = 0
    else:
        daily_interest = compute_daily_interest(avg_balance, rate_bps)
        expected_interest = daily_interest * days_in_cycle

    # Verify calculation
    assert interest == expected_interest


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_DAYS_IN_CYCLE, max_value=MAX_DAYS_IN_CYCLE),
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_interest_methods_consistency(avg_balance, rate_bps, days_in_cycle):
    """Property: Simple and detailed interest methods are consistent for constant balance."""
    # Create daily balances with constant balance
    start_date = date(2025, 1, 1)
    daily_balances = [
        ((start_date + timedelta(days=i)).isoformat(), avg_balance)
        for i in range(days_in_cycle)
    ]

    # Compute interest using both methods
    detailed_interest = compute_monthly_interest_charge(daily_balances, rate_bps)
    simple_interest = compute_monthly_interest_simple(
        avg_balance, rate_bps, days_in_cycle
    )

    # Should be equal for constant balance
    assert detailed_interest == simple_interest


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_zero_interest_scenarios(balance, rate_bps):
    """Property: Zero interest scenarios produce correct results."""
    # Zero rate
    assert compute_daily_interest(balance, 0) == 0
    assert compute_monthly_interest_simple(balance, 0, 30) == 0

    # Zero balance
    assert compute_daily_interest(0, rate_bps) == 0
    assert compute_monthly_interest_simple(0, rate_bps, 30) == 0

    # Empty daily balances
    assert compute_monthly_interest_charge([], rate_bps) == 0


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_rounding_consistency(balance, rate_bps):
    """Property: Rounding is consistent across calculations."""
    # Compute daily interest
    daily_interest = compute_daily_interest(balance, rate_bps)

    # Compute monthly interest for 30 days
    monthly_interest = compute_monthly_interest_simple(balance, rate_bps, 30)

    # Should be exactly 30 times daily interest
    assert monthly_interest == daily_interest * 30


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_interest_proportionality(balance, rate_bps):
    """Property: Interest is approximately proportional to balance and rate."""
    base_interest = compute_daily_interest(balance, rate_bps)

    # Double the balance - check within a safe integer drift range of [-3, +3]
    double_balance_interest = compute_daily_interest(balance * 2, rate_bps)
    if base_interest == 0:
        assert double_balance_interest in (0, 1, 2)
    else:
        assert double_balance_interest in range(
            base_interest * 2 - 3, base_interest * 2 + 4
        )

    # Double the rate - check within a safe integer drift range of [-3, +3]
    double_rate_interest = compute_daily_interest(balance, rate_bps * 2)
    if base_interest == 0:
        assert double_rate_interest in (0, 1, 2)
    else:
        assert double_rate_interest in range(
            base_interest * 2 - 3, base_interest * 2 + 4
        )


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_DAYS_IN_CYCLE, max_value=MAX_DAYS_IN_CYCLE),
)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_large_balance_scenarios(balance, rate_bps, days_in_cycle):
    """Property: Monthly interest is exactly daily interest multiplied by days."""
    interest = compute_monthly_interest_simple(balance, rate_bps, days_in_cycle)
    daily = compute_daily_interest(balance, rate_bps)
    assert interest == daily * days_in_cycle


@given(
    st.integers(min_value=MIN_BALANCE_PAISE, max_value=MAX_BALANCE_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.differing_executors],
)
def test_edge_case_rates(balance, rate_bps):
    """Property: Edge case rates produce correct results."""
    # Test minimum rate
    min_rate_interest = compute_daily_interest(balance, MIN_INTEREST_RATE_BPS)
    assert min_rate_interest >= 0

    # Test maximum rate
    max_rate_interest = compute_daily_interest(balance, MAX_INTEREST_RATE_BPS)
    assert max_rate_interest >= 0

    # Test rate in the middle
    mid_rate_interest = compute_daily_interest(
        balance, (MIN_INTEREST_RATE_BPS + MAX_INTEREST_RATE_BPS) // 2
    )
    assert mid_rate_interest >= 0
    assert mid_rate_interest <= max_rate_interest
