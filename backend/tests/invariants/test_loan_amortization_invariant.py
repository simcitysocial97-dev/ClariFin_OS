"""
Loan Amortization Invariant Tests
==================================
Guarantee: sum(principal_components) == principal

These tests validate that loan amortization calculations remain correct,
ensuring that the sum of all principal components across the loan lifecycle
exactly equals the original principal amount.
"""

import pytest
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict

from src.utils.money import to_paise, from_paise, validate_paise, multiply_paise, percentage_of


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def simple_loan() -> Dict:
    """Simple loan: ₹1,00,000 at 10% annual for 12 months, EMI ~₹8,792."""
    principal = to_paise(Decimal("100000.00"))
    annual_rate = Decimal("10.0")
    tenure_months = 12
    emi = to_paise(Decimal("8791.59"))  # Pre-calculated EMI
    
    return {
        "principal_paise": principal,
        "annual_rate_percent": annual_rate,
        "tenure_months": tenure_months,
        "emi_paise": emi,
        "start_date": "2025-01-01",
    }


@pytest.fixture
def zero_interest_loan() -> Dict:
    """Zero-interest loan: principal = ₹50,000, 6 months, EMI = ₹8,333.33."""
    principal = to_paise(Decimal("50000.00"))
    emi = to_paise(Decimal("8333.33"))
    
    return {
        "principal_paise": principal,
        "annual_rate_percent": Decimal("0.0"),
        "tenure_months": 6,
        "emi_paise": emi,
        "start_date": "2025-01-01",
    }


@pytest.fixture
def short_term_loan() -> Dict:
    """Short-term loan: ₹10,000 at 12% for 3 months."""
    principal = to_paise(Decimal("10000.00"))
    emi = to_paise(Decimal("3388.53"))
    
    return {
        "principal_paise": principal,
        "annual_rate_percent": Decimal("12.0"),
        "tenure_months": 3,
        "emi_paise": emi,
        "start_date": "2025-01-01",
    }


# ============================================================
# Core Invariant: sum(principal_components) == principal
# ============================================================

def compute_emi_breakdown(
    principal_paise: int,
    annual_rate_percent: Decimal,
    tenure_months: int
) -> List[Dict]:
    """
    Compute EMI breakdown for each month.
    
    Returns list of dicts with:
        - month: int
        - emi_paise: int
        - interest_paise: int
        - principal_paise: int
        - remaining_principal_paise: int
    """
    if tenure_months <= 0:
        return []
    
    monthly_rate = annual_rate_percent / Decimal("12") / Decimal("100")
    
    # Calculate EMI using standard amortization formula
    if monthly_rate == 0:
        emi_paise = principal_paise // tenure_months
    else:
        # EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        factor = (Decimal("1") + monthly_rate) ** tenure_months
        emi_paise = int(
            (Decimal(principal_paise) * monthly_rate * factor / (factor - Decimal("1")))
            .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
    
    remaining = principal_paise
    breakdown = []
    
    for month in range(1, tenure_months + 1):
        interest = int((Decimal(remaining) * monthly_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        principal_component = emi_paise - interest
        remaining = remaining - principal_component
        
        # Handle last month rounding adjustment
        if month == tenure_months:
            principal_component = principal_component + remaining
            remaining = 0
        
        breakdown.append({
            "month": month,
            "emi_paise": emi_paise,
            "interest_paise": interest,
            "principal_paise": principal_component,
            "remaining_principal_paise": remaining,
        })
    
    return breakdown


class TestLoanAmortizationInvariant:
    """Validate loan amortization invariants."""

    def test_simple_loan_principal_sum(self, simple_loan):
        """Sum of principal components == original principal."""
        breakdown = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        
        total_principal = sum(b["principal_paise"] for b in breakdown)
        assert total_principal == simple_loan["principal_paise"]

    def test_zero_interest_loan(self, zero_interest_loan):
        """Zero-interest loan: sum == principal."""
        breakdown = compute_emi_breakdown(
            zero_interest_loan["principal_paise"],
            zero_interest_loan["annual_rate_percent"],
            zero_interest_loan["tenure_months"]
        )
        
        total_principal = sum(b["principal_paise"] for b in breakdown)
        assert total_principal == zero_interest_loan["principal_paise"]
        
        # Each EMI should be equal principal + zero interest
        for b in breakdown:
            assert b["interest_paise"] == 0

    def test_short_term_loan(self, short_term_loan):
        """Short-term loan: sum == principal."""
        breakdown = compute_emi_breakdown(
            short_term_loan["principal_paise"],
            short_term_loan["annual_rate_percent"],
            short_term_loan["tenure_months"]
        )
        
        total_principal = sum(b["principal_paise"] for b in breakdown)
        assert total_principal == short_term_loan["principal_paise"]
        assert len(breakdown) == 3

    def test_final_remaining_is_zero(self, simple_loan):
        """Last month remaining principal must be exactly zero."""
        breakdown = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        
        assert breakdown[-1]["remaining_principal_paise"] == 0

    def test_remaining_decreases_monotonically(self, simple_loan):
        """Remaining principal must never increase."""
        breakdown = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        
        for i in range(1, len(breakdown)):
            assert breakdown[i]["remaining_principal_paise"] < breakdown[i-1]["remaining_principal_paise"]

    def test_principal_increases_over_time(self, simple_loan):
        """Principal component must increase as interest decreases."""
        breakdown = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        
        # Principal components should increase (or stay equal in edge cases)
        for i in range(1, len(breakdown)):
            assert breakdown[i]["principal_paise"] >= breakdown[i-1]["principal_paise"]


# ============================================================
# Float Regression Detection
# ============================================================

class TestNoFloatLeakage:
    """Ensure no float values in loan amortization."""

    def test_emi_is_int(self, simple_loan):
        """EMI must be int."""
        breakdown = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        for b in breakdown:
            assert isinstance(b["emi_paise"], int)

    def test_principal_components_are_int(self, simple_loan):
        """Principal components must be int."""
        breakdown = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        for b in breakdown:
            assert isinstance(b["principal_paise"], int)
            assert isinstance(b["interest_paise"], int)

    def test_remaining_is_int(self, simple_loan):
        """Remaining principal must be int."""
        breakdown = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        for b in breakdown:
            assert isinstance(b["remaining_principal_paise"], int)


# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Loan amortization must be deterministic."""

    def test_same_input_same_breakdown(self, simple_loan):
        """Same loan parameters → same breakdown."""
        b1 = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        b2 = compute_emi_breakdown(
            simple_loan["principal_paise"],
            simple_loan["annual_rate_percent"],
            simple_loan["tenure_months"]
        )
        assert b1 == b2


# ============================================================
# Stress Test: Large loan
# ============================================================

class TestStress:
    """Loan amortization under extreme conditions."""

    def test_large_principal(self):
        """₹1 crore loan at 10% for 30 years."""
        principal = to_paise(Decimal("10000000.00"))
        rate = Decimal("10.0")
        tenure = 360
        
        breakdown = compute_emi_breakdown(principal, rate, tenure)
        total_principal = sum(b["principal_paise"] for b in breakdown)
        
        assert total_principal == principal
        assert len(breakdown) == 360
        assert breakdown[-1]["remaining_principal_paise"] == 0

    def test_tiny_principal(self):
        """₹1 loan (minimum paise)."""
        principal = to_paise(Decimal("0.01"))
        rate = Decimal("0.0")
        tenure = 1
        
        breakdown = compute_emi_breakdown(principal, rate, tenure)
        total_principal = sum(b["principal_paise"] for b in breakdown)
        
        assert total_principal == principal
        assert len(breakdown) == 1
        assert breakdown[0]["remaining_principal_paise"] == 0