"""
Property-based tests for credit card engine EMI module.

These tests verify the mathematical invariants and business rules of the credit card
EMI calculations using property-based testing techniques.
"""

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.engines.credit_card_engine.emi import compute_emi_conversion

# Constants for testing
MAX_INTEREST_RATE_BPS = 3600  # 36% annual
MIN_INTEREST_RATE_BPS = 500   # 5% annual
MAX_TENURE_MONTHS = 24        # 24 months (2 years)
MIN_TENURE_MONTHS = 3         # 3 months
MAX_AMOUNT_PAISE = 10_000_000_00  # ₹10 lakh
MIN_AMOUNT_PAISE = 10_000         # ₹100

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS)
)
@settings(max_examples=50, deadline=None)
def test_compute_emi_conversion_invariants(amount, rate, tenure):
    """Property: compute_emi_conversion must satisfy all invariants."""
    # Compute EMI conversion
    result = compute_emi_conversion(amount, rate, tenure)

    # INVARIANT 1: Result is a dictionary with correct keys
    assert isinstance(result, dict)
    assert "emi_paise" in result
    assert "total_interest_paise" in result
    assert "total_repayment_paise" in result
    assert "monthly_interest_paise" in result

    # INVARIANT 2: All monetary values are non-negative
    assert result["emi_paise"] >= 0
    assert result["total_interest_paise"] >= 0
    assert result["total_repayment_paise"] >= 0
    assert result["monthly_interest_paise"] >= 0

    # INVARIANT 3: EMI is positive for positive amount
    if amount > 0:
        assert result["emi_paise"] > 0

    # INVARIANT 4: Total repayment equals EMI * tenure
    assert result["total_repayment_paise"] == result["emi_paise"] * tenure

    # INVARIANT 5: Total repayment equals principal + interest
    assert result["total_repayment_paise"] == amount + result["total_interest_paise"]

    # INVARIANT 6: Interest is non-negative
    assert result["total_interest_paise"] >= 0

    # INVARIANT 7: Interest is zero for zero rate
    if rate == 0:
        assert result["total_interest_paise"] == 0
        assert result["monthly_interest_paise"] == 0

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS)
)
@settings(max_examples=30, deadline=None)
def test_compute_emi_conversion_math_accuracy(amount, rate, tenure):
    """Property: compute_emi_conversion math must be accurate."""
    # Compute EMI conversion
    result = compute_emi_conversion(amount, rate, tenure)

    # Calculate expected values
    if amount == 0 or tenure == 0:
        expected_emi = 0
        expected_total_repayment = 0
        expected_total_interest = 0
        expected_monthly_interest = 0
    else:
        # Calculate expected EMI using loan engine formula
        monthly_rate = Decimal(rate) / Decimal(10000) / Decimal(12)
        if monthly_rate == 0:
            expected_emi = amount // tenure
        else:
            r = monthly_rate
            n = Decimal(tenure)
            p = Decimal(amount)

            numerator = p * r * ((1 + r) ** n)
            denominator = ((1 + r) ** n) - 1
            expected_emi = int(numerator / denominator)

        expected_total_repayment = expected_emi * tenure
        expected_total_interest = expected_total_repayment - amount

        # Calculate expected monthly interest
        expected_monthly_interest = int(Decimal(amount) * monthly_rate)

    # Verify calculations
    assert abs(result["emi_paise"] - expected_emi) <= 1
    assert abs(result["total_repayment_paise"] - expected_total_repayment) <= tenure
    assert abs(result["total_interest_paise"] - max(0, expected_total_interest)) <= tenure
    assert abs(result["emi_paise"] - expected_emi) <= 1

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS)
)
@settings(max_examples=30, deadline=None)
def test_emi_proportionality(amount, rate, tenure):
    """Property: EMI is proportional to amount and rate."""
    # Compute base EMI
    base_result = compute_emi_conversion(amount, rate, tenure)
    base_emi = base_result["emi_paise"]

    # Double the amount
    double_amount_result = compute_emi_conversion(amount * 2, rate, tenure)
    double_amount_emi = double_amount_result["emi_paise"]

    # Should be exactly double (for zero interest) or approximately double (for positive interest)
    if rate == 0:
        assert double_amount_emi == base_emi * 2
    else:
        # Allow for small rounding differences
        assert abs(double_amount_emi - base_emi * 2) <= 1

    # Double the rate
    if rate > 0:
        double_rate_result = compute_emi_conversion(amount, rate * 2, tenure)
        double_rate_emi = double_rate_result["emi_paise"]

        # Should be higher but not necessarily double
        assert double_rate_emi > base_emi

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS)
)
@settings(max_examples=30, deadline=None)
def test_emi_tenure_effects(amount, rate):
    """Property: EMI decreases with longer tenure."""
    # Compute EMI for different tenures
    short_tenure = MIN_TENURE_MONTHS
    long_tenure = MAX_TENURE_MONTHS

    short_result = compute_emi_conversion(amount, rate, short_tenure)
    long_result = compute_emi_conversion(amount, rate, long_tenure)

    # Longer tenure should have lower EMI
    assert long_result["emi_paise"] <= short_result["emi_paise"]

    # Longer tenure should have higher total interest
    assert long_result["total_interest_paise"] >= short_result["total_interest_paise"]

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS)
)
@settings(max_examples=20, deadline=None)
def test_zero_interest_emi(amount, tenure):
    """Property: Zero interest produces correct EMI."""
    result = compute_emi_conversion(amount, 0, tenure)

    # Match engine's ceiling division behavior for zero interest distribution
    expected_emi = (amount + tenure - 1) // tenure if tenure > 0 else 0
    assert result["emi_paise"] == expected_emi
    assert result["total_repayment_paise"] == amount
    assert result["total_interest_paise"] == 0
    assert result["monthly_interest_paise"] == 0

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS)
)
@settings(max_examples=20, deadline=None)
def test_short_tenure_emi(amount, rate):
    """Property: Short tenure produces correct EMI."""
    # Test with minimum tenure
    result = compute_emi_conversion(amount, rate, MIN_TENURE_MONTHS)

    # EMI should be large (short tenure)
    assert result["emi_paise"] >= amount // MIN_TENURE_MONTHS

    # For very small amounts, EMI should be at least 1 paise
    if amount > 0:
        assert result["emi_paise"] >= 1

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS)
)
@settings(max_examples=20, deadline=None)
def test_long_tenure_emi(amount, rate):
    """Property: Long tenure produces correct EMI."""
    # Test with maximum tenure
    result = compute_emi_conversion(amount, rate, MAX_TENURE_MONTHS)

    # EMI should be small (long tenure)
    assert result["emi_paise"] <= amount

    # EMI should be close to interest-only payment
    if amount > 0 and rate > 0:
        monthly_rate = Decimal(rate) / Decimal(10000) / Decimal(12)
        interest_only_payment = int(Decimal(amount) * monthly_rate)
        assert result["emi_paise"] >= interest_only_payment

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS)
)
@settings(max_examples=10, deadline=None)
def test_emi_consistency(amount, rate, tenure):
    """Property: EMI components are consistent."""
    # Compute EMI conversion
    result = compute_emi_conversion(amount, rate, tenure)

    # Principal + interest should equal EMI
    principal_component = result["emi_paise"] - result["monthly_interest_paise"]
    assert principal_component >= 0

    # Total repayment should equal EMI * tenure
    assert result["total_repayment_paise"] == result["emi_paise"] * tenure

    # Total interest should equal total repayment - principal
    assert result["total_interest_paise"] == result["total_repayment_paise"] - amount

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_INTEREST_RATE_BPS, max_value=MAX_INTEREST_RATE_BPS)
)
@settings(max_examples=10, deadline=None)
def test_emi_edge_cases(amount, rate):
    """Property: EMI handles edge cases correctly."""
    # Test with zero amount
    zero_result = compute_emi_conversion(0, rate, MIN_TENURE_MONTHS)
    assert zero_result["emi_paise"] == 0
    assert zero_result["total_interest_paise"] == 0
    assert zero_result["total_repayment_paise"] == 0
    assert zero_result["monthly_interest_paise"] == 0

    # Test with zero tenure (should raise error)
    with pytest.raises(ValueError):
        compute_emi_conversion(amount, rate, 0)

    # Test with negative amount (should raise error)
    with pytest.raises(ValueError):
        compute_emi_conversion(-1, rate, MIN_TENURE_MONTHS)

    # Test with negative rate (should raise error)
    with pytest.raises(ValueError):
        compute_emi_conversion(amount, -1, MIN_TENURE_MONTHS)

@given(
    st.integers(min_value=MIN_AMOUNT_PAISE, max_value=MAX_AMOUNT_PAISE),
    st.integers(min_value=MIN_TENURE_MONTHS, max_value=MAX_TENURE_MONTHS)
)
@settings(max_examples=10, deadline=None)
def test_emi_rounding_consistency(amount, tenure):
    """Property: EMI rounding is consistent and monotonic with respect to interest."""
    result = compute_emi_conversion(amount, 0, tenure)

    expected_emi = (amount + tenure - 1) // tenure if tenure > 0 else 0
    assert abs(result["emi_paise"] - expected_emi) <= 1
    assert result["total_repayment_paise"] == amount

    # Test with very small interest rate (1 bps)
    small_rate_result = compute_emi_conversion(amount, 1, tenure)
    
    # Monotonicity invariant: interest cannot decrease EMI
    assert small_rate_result["emi_paise"] >= result["emi_paise"] - 1
    
    # Mathematical upper bound: 1 bps over short/long tenure on any principal 
    # cannot add more than 0.1% (10 basis points) of the principal to the total EMI.
    max_reasonable_emi = result["emi_paise"] + max(1, int(result["emi_paise"] * 0.001))
    assert small_rate_result["emi_paise"] <= max_reasonable_emi
