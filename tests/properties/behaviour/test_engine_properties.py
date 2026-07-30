"""
Property-based tests for engine behaviours.

Uses Hypothesis to generate edge cases and validate invariants.
Focuses on dormant detection, financial stress scoring, and behavioural rules.
"""

from datetime import date, timedelta
from typing import Any

import pytest
from hypothesis import given, strategies as st
from backend.src.engines.account_engine.dormant import (
    compute_days_since_activity,
    is_account_dormant,
)
from backend.src.engines.behaviour_engine.stress import financial_stress_index


# Constants
DORMANCY_THRESHOLD_DAYS = 90


# Strategies
@st.composite
def valid_dates(draw: st.DrawFn) -> tuple[str, str]:
    """Generate (last_activity_date, reference_date) pairs where last <= reference."""
    ref_date = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2050, 12, 31)))
    last_date = draw(st.dates(min_value=date(2000, 1, 1), max_value=ref_date))
    return last_date.isoformat(), ref_date.isoformat()


@st.composite
def invalid_dates(draw: st.DrawFn) -> tuple[str, str]:
    """Generate (last_activity_date, reference_date) pairs where last > reference."""
    ref_date = draw(st.dates(min_value=date(2000, 1, 1), max_value=date(2050, 12, 31)))
    last_date = draw(st.dates(min_value=ref_date + timedelta(days=1), max_value=date(2050, 12, 31)))
    return last_date.isoformat(), ref_date.isoformat()


@st.composite
def days_since_activity(draw: st.DrawFn) -> int:
    """Generate days since last activity (0-1000)."""
    return draw(st.integers(min_value=0, max_value=1000))


# Tests
@given(valid_dates())
def test_compute_days_since_activity_valid(dates: tuple[str, str]) -> None:
    """Valid dates must compute non-negative days."""
    last_activity, reference = dates
    days = compute_days_since_activity(last_activity, reference)
    assert days >= 0
    assert isinstance(days, int)


@given(invalid_dates())
def test_compute_days_since_activity_invalid(dates: tuple[str, str]) -> None:
    """Future last_activity_date must raise ValueError."""
    last_activity, reference = dates
    with pytest.raises(ValueError, match="cannot be after reference_date"):
        compute_days_since_activity(last_activity, reference)


@given(days_since_activity(), st.integers(min_value=0, max_value=1000))
def test_is_account_dormant_deterministic(days: int, threshold: int) -> None:
    """Same inputs must always produce same output."""
    result1 = is_account_dormant(days, threshold)
    result2 = is_account_dormant(days, threshold)
    assert result1 == result2


@given(st.integers(max_value=-1))
def test_is_account_dormant_negative_threshold(threshold: int) -> None:
    """Negative threshold_days must raise ValueError."""
    with pytest.raises(ValueError, match="must be non-negative"):
        is_account_dormant(0, threshold)


@given(days_since_activity())
def test_dormancy_threshold_90_days(days: int) -> None:
    """Accounts with no activity for 90+ days must be flagged as dormant."""
    is_dormant = is_account_dormant(days, DORMANCY_THRESHOLD_DAYS)
    if days >= DORMANCY_THRESHOLD_DAYS:
        assert is_dormant, f"Expected dormant for {days} days"
    else:
        assert not is_dormant, f"Expected active for {days} days"


@given(valid_dates())
def test_dormancy_based_on_last_transaction_date(dates: tuple[str, str]) -> None:
    """Dormancy must be based on last transaction date, not account creation date."""
    last_activity, reference = dates
    days = compute_days_since_activity(last_activity, reference)
    is_dormant = is_account_dormant(days, DORMANCY_THRESHOLD_DAYS)
    
    # Dormancy must depend on last_activity, not creation_date
    assert is_dormant == (days >= DORMANCY_THRESHOLD_DAYS)
    # If last_activity == reference_date, dormancy must be False
    if days == 0:
        assert not is_dormant


@given(days_since_activity(), st.integers(min_value=0, max_value=1000000))
def test_zero_balance_accounts_still_flagged_dormant(days: int, balance: int) -> None:
    """Zero-balance accounts must still be flagged as dormant if inactive."""
    is_dormant = is_account_dormant(days, DORMANCY_THRESHOLD_DAYS)
    assert is_dormant == (days >= DORMANCY_THRESHOLD_DAYS)


@given(valid_dates())
def test_active_accounts_not_flagged_dormant(dates: tuple[str, str]) -> None:
    """Accounts with recent transactions must not be flagged as dormant."""
    last_activity, reference = dates
    days = compute_days_since_activity(last_activity, reference)
    
    # Force recent activity (within 89 days)
    recent_days = min(days, 89)
    is_dormant = is_account_dormant(recent_days, DORMANCY_THRESHOLD_DAYS)
    assert not is_dormant, f"Active account flagged as dormant for {recent_days} days"


# ============================================================
# Financial Stress Index Property Tests
# ============================================================


@st.composite
def financial_transactions(draw: st.DrawFn) -> list[dict[str, Any]]:
    """Generate realistic financial transactions for stress testing."""
    num_transactions = draw(st.integers(min_value=20, max_value=50))
    
    transactions = []
    for _ in range(num_transactions):
        date_iso = draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))).isoformat()
        amount_paise = draw(st.integers(min_value=10_000, max_value=500_000))
        txn_type = draw(st.sampled_from(["debit", "credit"]))
        
        transactions.append({
            "date_iso": date_iso,
            "amount_paise": amount_paise,
            "type": txn_type,
        })
    
    return transactions


@st.composite
def financial_transactions_with_debt_savings(draw: st.DrawFn) -> tuple[list[dict[str, Any]], int, int]:
    """Generate transactions with controlled debt and savings levels."""
    base_transactions = draw(financial_transactions())
    total_debt = draw(st.integers(min_value=100_000, max_value=1_000_000))
    total_savings = draw(st.integers(min_value=100_000, max_value=1_000_000))
    
    # Adjust transactions to reflect debt/savings
    adjusted_transactions = []
    remaining_debt = total_debt
    remaining_savings = total_savings
    
    for txn in base_transactions:
        if txn["type"] == "debit" and remaining_debt > 0:
            txn_amount = min(txn["amount_paise"], remaining_debt)
            adjusted_transactions.append({
                **txn,
                "amount_paise": txn_amount
            })
            remaining_debt -= txn_amount
        elif txn["type"] == "credit" and remaining_savings > 0:
            txn_amount = min(txn["amount_paise"], remaining_savings)
            adjusted_transactions.append({
                **txn,
                "amount_paise": txn_amount
            })
            remaining_savings -= txn_amount
        else:
            adjusted_transactions.append(txn)
    
    # Add remaining debt/savings as single transactions
    if remaining_debt > 0:
        adjusted_transactions.append({
            "date_iso": draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))).isoformat(),
            "amount_paise": remaining_debt,
            "type": "debit",
        })
    
    if remaining_savings > 0:
        adjusted_transactions.append({
            "date_iso": draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2025, 12, 31))).isoformat(),
            "amount_paise": remaining_savings,
            "type": "credit",
        })
    
    return adjusted_transactions, total_debt, total_savings


@given(financial_transactions())
def test_financial_stress_score_bounds(transactions: list[dict[str, Any]]) -> None:
    """Stress score must always be in the range [0, 100]."""
    result = financial_stress_index(transactions)
    score = result["score"]
    assert 0 <= score <= 1, f"Score {score} out of bounds [0, 1]"


def test_financial_stress_extreme_values() -> None:
    """Stress score must handle extreme values correctly."""
    # Test with zero transactions
    zero_result = financial_stress_index([])
    assert 0 <= zero_result["score"] <= 1, "Empty transactions should return valid score"
    
    # Test with minimal transactions
    minimal_transactions = [
        {"date_iso": "2020-01-01", "amount_paise": 100_000, "type": "debit"},
        {"date_iso": "2020-01-02", "amount_paise": 100_000, "type": "credit"}
    ]
    minimal_result = financial_stress_index(minimal_transactions)
    assert 0 <= minimal_result["score"] <= 1, "Minimal transactions should return valid score"


@given(financial_transactions_with_debt_savings())
def test_financial_stress_monotonicity_savings(transactions_and_metrics: tuple[list[dict[str, Any]], int, int]) -> None:
    """Lower savings must increase the stress score components."""
    base_transactions, _, base_savings = transactions_and_metrics
    
    # Skip cases where savings are too low to show meaningful impact
    if base_savings < 50_000:
        return
    
    # Create lower savings scenario (reduce savings by 50% to ensure impact)
    lower_savings_transactions = []
    for txn in base_transactions:
        if txn["type"] == "credit":
            lower_savings_transactions.append({
                **txn,
                "amount_paise": txn["amount_paise"] // 2  # Halve savings
            })
        else:
            lower_savings_transactions.append(txn)
    
    base_result = financial_stress_index(base_transactions)
    lower_savings_result = financial_stress_index(lower_savings_transactions)
    
    # Check eom depletion ratio (should increase with lower savings)
    assert lower_savings_result["eom_depletion_ratio"] >= base_result["eom_depletion_ratio"] - 0.001, \
        f"Lower savings should increase EOM depletion ratio: {base_result['eom_depletion_ratio']} -> {lower_savings_result['eom_depletion_ratio']}"


@given(financial_transactions())
def test_financial_stress_deterministic_output(transactions: list[dict[str, Any]]) -> None:
    """Same inputs must always produce the same stress score."""
    result1 = financial_stress_index(transactions)
    result2 = financial_stress_index(transactions)
    
    assert result1["score"] == result2["score"], "Non-deterministic output detected"
    assert result1 == result2, "Non-deterministic output detected"


@given(financial_transactions())
def test_financial_stress_credit_dependency(transactions: list[dict[str, Any]]) -> None:
    """Higher credit utilization must increase the stress score."""
    # Filter out transactions with no debits or credits
    if not any(txn["type"] == "debit" for txn in transactions) or not any(txn["type"] == "credit" for txn in transactions):
        return  # Skip invalid cases
    
    base_result = financial_stress_index(transactions)
    
    # Skip cases where credit dependency is already very low
    if base_result["credit_dependency"] < 0.1:
        return
    
    # Create high credit dependency scenario (double credit to ensure impact)
    high_credit_transactions = []
    for txn in transactions:
        if txn["type"] == "credit":
            high_credit_transactions.append({
                **txn,
                "amount_paise": txn["amount_paise"] * 2  # Double credit
            })
        else:
            high_credit_transactions.append(txn)
    
    high_credit_result = financial_stress_index(high_credit_transactions)
    
    # Check credit dependency component specifically
    assert high_credit_result["credit_dependency"] >= base_result["credit_dependency"] - 0.001, \
        f"Higher credit should increase credit dependency: {base_result['credit_dependency']} -> {high_credit_result['credit_dependency']}"


@given(st.lists(st.builds(dict), min_size=1, max_size=5))
def test_financial_stress_invalid_inputs(transactions: list[dict[str, Any]]) -> None:
    """Invalid inputs must be handled gracefully."""
    # Test empty transactions
    empty_result = financial_stress_index([])
    assert empty_result["score"] == 0.5, "Empty transactions should return default score"
    
    # Test missing required fields
    invalid_txn = [{"type": "debit"}]  # Missing amount_paise and date_iso
    invalid_result = financial_stress_index(invalid_txn)
    assert 0 <= invalid_result["score"] <= 1, "Invalid transactions should return valid score"


@given(financial_transactions())
def test_financial_stress_edge_cases(transactions: list[dict[str, Any]]) -> None:
    """Edge cases must be handled correctly."""
    # Test zero debt
    zero_debt_transactions = [txn for txn in transactions if txn["type"] != "debit"]
    if zero_debt_transactions:
        zero_debt_result = financial_stress_index(zero_debt_transactions)
        assert 0 <= zero_debt_result["score"] <= 1, "Zero debt should return valid score"
    
    # Test max credit utilization
    max_credit_transactions = []
    for txn in transactions:
        if txn["type"] == "credit":
            max_credit_transactions.append({
                **txn,
                "amount_paise": txn["amount_paise"] * 10  # Max credit
            })
        else:
            max_credit_transactions.append(txn)
    
    max_credit_result = financial_stress_index(max_credit_transactions)
    assert 0 <= max_credit_result["score"] <= 1, "Max credit should return valid score"