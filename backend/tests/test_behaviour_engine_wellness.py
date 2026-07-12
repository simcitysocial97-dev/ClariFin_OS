"""
Behaviour Engine Phase 7 — Wellness Score Tests
===============================================

Tests for financial wellness scoring including:
- Composite wellness score calculation
- Wellness band classification
- Boundary conditions
- Determinism

All tests verify:
- Correct formula implementation
- Edge cases (zero values, boundary values)
- Determinism (same input → same output)
- Classification accuracy

Run: python -m pytest tests/test_behaviour_engine_wellness.py -v
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behaviour_engine.wellness import (
    classify_wellness_band,
    compute_wellness_score,
)

# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def perfect_scores() -> dict[str, Decimal | int]:
    """Fixture with perfect scores for all components."""
    return {
        "cashflow_stability": Decimal("1"),
        "debt_cycle_score": 0,  # Best possible debt score
        "savings_rate": Decimal("1"),  # 100% savings
        "resilience_index": Decimal("1"),
        "lifestyle_inflation": Decimal("-1"),  # Perfect lifestyle decrease
        "credit_revolver_ratio": Decimal("0"),  # No revolving credit
        "foir": Decimal("0"),  # No fixed obligations
    }

@pytest.fixture
def worst_scores() -> dict[str, Decimal | int]:
    """Fixture with worst scores for all components."""
    return {
        "cashflow_stability": Decimal("0"),
        "debt_cycle_score": 100,  # Worst possible debt score
        "savings_rate": Decimal("-1"),  # 100% overspending
        "resilience_index": Decimal("0"),
        "lifestyle_inflation": Decimal("2"),  # Extreme lifestyle inflation
        "credit_revolver_ratio": Decimal("1"),  # Always revolving
        "foir": Decimal("2"),  # Extreme fixed obligations
    }

@pytest.fixture
def average_scores() -> dict[str, Decimal | int]:
    """Fixture with average scores for all components."""
    return {
        "cashflow_stability": Decimal("0.5"),
        "debt_cycle_score": 50,
        "savings_rate": Decimal("0.2"),  # 20% savings
        "resilience_index": Decimal("0.5"),
        "lifestyle_inflation": Decimal("0.2"),  # 20% lifestyle inflation
        "credit_revolver_ratio": Decimal("0.3"),  # Some revolving
        "foir": Decimal("0.4"),  # Moderate fixed obligations
    }

# ============================================================
# Wellness Score Calculation Tests
# ============================================================

class TestWellnessScoreCalculation:
    """Tests for compute_wellness_score function."""

    def test_perfect_wellness_score(self, perfect_scores):
        """Test perfect scores result in 100."""
        result = compute_wellness_score(**perfect_scores)
        assert result == Decimal("100")

    def test_worst_wellness_score(self, worst_scores):
        """Test worst scores result in 0."""
        result = compute_wellness_score(**worst_scores)
        assert result == Decimal("0")

    def test_average_wellness_score(self, average_scores):
        """Test average scores result in expected value."""
        result = compute_wellness_score(**average_scores)
        # Expected calculation:
        # Cashflow: 0.5 * 0.30 = 0.15
        # Debt: (1 - 0.5) * 0.20 = 0.10
        # Savings: 0.2 * 0.15 = 0.03
        # Resilience: 0.5 * 0.20 = 0.10
        # Lifestyle: (1 - 0.2) * 0.10 = 0.08
        # Credit: 0.5*(1-0.3) + 0.5*(1-0.4) = 0.35 + 0.3 = 0.65 * 0.05 = 0.0325
        # Total: 0.15 + 0.10 + 0.03 + 0.10 + 0.08 + 0.0325 = 0.4925
        expected = Decimal("0.4925") * Decimal("100")
        assert result == expected

    def test_negative_savings_rate(self):
        """Test negative savings rate is clamped to 0."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("-0.5"),  # Negative savings
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        # Should be same as if savings_rate=0
        expected = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0"),  # Clamped to 0
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        assert result == expected

    def test_high_lifestyle_inflation(self):
        """Test lifestyle inflation > 1 is capped at 1."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("2"),  # Extreme inflation
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        # Should be same as if lifestyle_inflation=1
        expected = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("1"),  # Capped at 1
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        assert result == expected

    def test_high_foir(self):
        """Test FOIR > 1 is capped at 1."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("1.5"),  # Extreme FOIR
        )
        # Should be same as if foir=1
        expected = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("1"),  # Capped at 1
        )
        assert result == expected

    def test_boundary_scores(self):
        """Test boundary score values."""
        # Test 0
        result = compute_wellness_score(
            cashflow_stability=Decimal("0"),
            debt_cycle_score=100,
            savings_rate=Decimal("-1"),
            resilience_index=Decimal("0"),
            lifestyle_inflation=Decimal("1"),
            credit_revolver_ratio=Decimal("1"),
            foir=Decimal("1"),
        )
        assert result == Decimal("0")

        # Test 100
        result = compute_wellness_score(
            cashflow_stability=Decimal("1"),
            debt_cycle_score=0,
            savings_rate=Decimal("1"),
            resilience_index=Decimal("1"),
            lifestyle_inflation=Decimal("-1"),
            credit_revolver_ratio=Decimal("0"),
            foir=Decimal("0"),
        )
        assert result == Decimal("100")

    def test_debt_health_inversion(self):
        """Test that lower debt cycle score results in higher wellness score."""
        # Low debt score (good)
        result_low_debt = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=20,  # Good debt score
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )

        # High debt score (bad)
        result_high_debt = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=80,  # Bad debt score
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )

        assert result_low_debt > result_high_debt

    def test_deterministic(self):
        """Test that same inputs produce same outputs."""
        inputs = {
            "cashflow_stability": Decimal("0.5"),
            "debt_cycle_score": 50,
            "savings_rate": Decimal("0.2"),
            "resilience_index": Decimal("0.5"),
            "lifestyle_inflation": Decimal("0.2"),
            "credit_revolver_ratio": Decimal("0.3"),
            "foir": Decimal("0.4"),
        }

        result1 = compute_wellness_score(**inputs)
        result2 = compute_wellness_score(**inputs)
        assert result1 == result2

# ============================================================
# Wellness Band Classification Tests
# ============================================================

class TestWellnessBandClassification:
    """Tests for classify_wellness_band function."""

    def test_excellent_band(self):
        """Test scores in excellent range (90-100)."""
        assert classify_wellness_band(Decimal("90")) == "Excellent"
        assert classify_wellness_band(Decimal("95")) == "Excellent"
        assert classify_wellness_band(Decimal("100")) == "Excellent"

    def test_healthy_band(self):
        """Test scores in healthy range (75-89)."""
        assert classify_wellness_band(Decimal("75")) == "Healthy"
        assert classify_wellness_band(Decimal("80")) == "Healthy"
        assert classify_wellness_band(Decimal("89.99")) == "Healthy"

    def test_developing_band(self):
        """Test scores in developing range (50-74)."""
        assert classify_wellness_band(Decimal("50")) == "Developing"
        assert classify_wellness_band(Decimal("60")) == "Developing"
        assert classify_wellness_band(Decimal("74.99")) == "Developing"

    def test_risk_band(self):
        """Test scores in risk range (25-49)."""
        assert classify_wellness_band(Decimal("25")) == "Risk"
        assert classify_wellness_band(Decimal("30")) == "Risk"
        assert classify_wellness_band(Decimal("49.99")) == "Risk"

    def test_critical_band(self):
        """Test scores in critical range (<25)."""
        assert classify_wellness_band(Decimal("0")) == "Critical"
        assert classify_wellness_band(Decimal("10")) == "Critical"
        assert classify_wellness_band(Decimal("24.99")) == "Critical"

    def test_boundary_values(self):
        """Test boundary values between bands."""
        assert classify_wellness_band(Decimal("89.999")) == "Healthy"
        assert classify_wellness_band(Decimal("90")) == "Excellent"

        assert classify_wellness_band(Decimal("74.999")) == "Developing"
        assert classify_wellness_band(Decimal("75")) == "Healthy"

        assert classify_wellness_band(Decimal("49.999")) == "Risk"
        assert classify_wellness_band(Decimal("50")) == "Developing"

        assert classify_wellness_band(Decimal("24.999")) == "Critical"
        assert classify_wellness_band(Decimal("25")) == "Risk"

# ============================================================
# Integration Tests with DEBT_DEPENDENT Profile
# ============================================================

class TestDebtDependentIntegration:
    """Test wellness score for DEBT_DEPENDENT profile characteristics."""

    def test_debt_dependent_profile(self):
        """Test wellness score for typical debt-dependent profile."""
        # Characteristics of DEBT_DEPENDENT:
        # - High credit revolver ratio
        # - High FOIR
        # - Low savings rate
        # - High debt cycle score
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.3"),  # Unstable cashflow
            debt_cycle_score=80,  # High debt cycle score
            savings_rate=Decimal("-0.1"),  # Negative savings
            resilience_index=Decimal("0.2"),  # Low resilience
            lifestyle_inflation=Decimal("0.5"),  # High lifestyle inflation
            credit_revolver_ratio=Decimal("0.8"),  # High revolver ratio
            foir=Decimal("0.7"),  # High fixed obligations
        )

        # Should be in Risk or Critical band
        band = classify_wellness_band(result)
        assert band in ["Risk", "Critical"]
        assert result < Decimal("50")

# ============================================================
# Edge Cases and Boundary Conditions
# ============================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_all_zero_inputs(self):
        """Test all zero inputs."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0"),
            debt_cycle_score=0,  # Best debt score
            savings_rate=Decimal("0"),
            resilience_index=Decimal("0"),
            lifestyle_inflation=Decimal("0"),
            credit_revolver_ratio=Decimal("0"),
            foir=Decimal("0"),
        )
        # Debug: print actual result
        print(f"Actual result: {result}")
        # Debt component: 20% of 1.0 = 0.20
        # Credit component: 0.5*(1-0) + 0.5*(1-0) = 1.0 * 0.05 = 0.05
        # Lifestyle component: (1 - 0) * 0.10 = 0.10
        # Total: 0.20 + 0.05 + 0.10 = 0.35 → 35
        expected = Decimal("35")
        assert result == expected

    def test_extreme_values(self):
        """Test with extreme values."""
        # Very high cashflow stability should not exceed 100
        result = compute_wellness_score(
            cashflow_stability=Decimal("1"),
            debt_cycle_score=0,
            savings_rate=Decimal("1"),
            resilience_index=Decimal("1"),
            lifestyle_inflation=Decimal("-1"),
            credit_revolver_ratio=Decimal("0"),
            foir=Decimal("0"),
        )
        assert result == Decimal("100")

        # Very low values should not go below 0
        result = compute_wellness_score(
            cashflow_stability=Decimal("0"),
            debt_cycle_score=100,
            savings_rate=Decimal("-1"),
            resilience_index=Decimal("0"),
            lifestyle_inflation=Decimal("2"),
            credit_revolver_ratio=Decimal("1"),
            foir=Decimal("2"),
        )
        assert result == Decimal("0")

# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Verify all functions are deterministic."""

    def test_wellness_score_deterministic(self):
        """Test compute_wellness_score is deterministic."""
        inputs = {
            "cashflow_stability": Decimal("0.7"),
            "debt_cycle_score": 30,
            "savings_rate": Decimal("0.35"),
            "resilience_index": Decimal("0.6"),
            "lifestyle_inflation": Decimal("0.1"),
            "credit_revolver_ratio": Decimal("0.2"),
            "foir": Decimal("0.3"),
        }

        for _ in range(3):
            result1 = compute_wellness_score(**inputs)
            result2 = compute_wellness_score(**inputs)
            assert result1 == result2

    def test_classify_wellness_band_deterministic(self):
        """Test classify_wellness_band is deterministic."""
        score = Decimal("65.4321")
        for _ in range(3):
            result1 = classify_wellness_band(score)
            result2 = classify_wellness_band(score)
            assert result1 == result2

# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])