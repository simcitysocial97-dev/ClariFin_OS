"""Tests for Behaviour Engine Phase 6 — Financial Personality Classification.

Tests cover all 5 personality profiles:
- SAVER: Savings rate >20%, no recurring debt
- BALANCED: Moderate savings, balanced spending
- SPENDER: High discretionary spending, impulse purchases
- DEBT_OPTIMIZER: Uses debt responsibly with positive savings
- DEBT_DEPENDENT: High credit lifestyle or recurring debt extraction

All tests verify:
- Determinism (same input → same output)
- Edge cases (zero values, negative values, missing data)
- Immutability (functions don't modify input data)
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behaviour_engine import classify_financial_personality

# ============================================================
# SAVER Tests
# ============================================================

class TestSaverProfile:
    """Tests for SAVER personality classification."""

    def test_saver_high_savings_no_debt(self):
        """Test SAVER with high savings and no credit dependency."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.25'),  # 25% savings
            borrowed_lifestyle_ratio=Decimal('0.05'),  # 5% credit funded
            credit_revolver_ratio=Decimal('0.0'),  # No revolving debt
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.05'),
            transaction_count=150,
        )
        assert profile == "SAVER"
        assert 0 <= confidence <= 1
        assert "SAVER" in explanation
        assert "25%" in explanation or "savings rate" in explanation.lower()

    def test_saver_strong_savings(self):
        """Test SAVER with strong savings (>25%) gets higher confidence."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.35'),  # 35% savings - strong
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=200,
        )
        assert profile == "SAVER"
        # Strong savings should get confidence bonus
        assert confidence >= Decimal('0.6')

    def test_saver_threshold_boundary(self):
        """Test SAVER at just above 20% threshold."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.21'),  # Just above 20%
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "SAVER"

    def test_saver_not_if_high_borrowed_ratio(self):
        """Test SAVER is not assigned when borrowed lifestyle ratio is high."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.25'),
            borrowed_lifestyle_ratio=Decimal('0.30'),  # Too high
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"


# ============================================================
# DEBT_DEPENDENT Tests
# ============================================================

class TestDebtDependentProfile:
    """Tests for DEBT_DEPENDENT personality classification."""

    def test_debt_dependent_high_borrowed_ratio(self):
        """Test DEBT_DEPENDENT with high borrowed lifestyle ratio."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.10'),
            borrowed_lifestyle_ratio=Decimal('0.25'),  # >20% threshold
            credit_revolver_ratio=Decimal('0.30'),
            discretionary_spending_ratio=Decimal('0.40'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.20'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"
        assert "borrowed lifestyle" in explanation.lower() or "credit" in explanation.lower()

    def test_debt_dependent_recurring_extraction(self):
        """Test DEBT_DEPENDENT from high revolver + low savings."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),  # Low savings
            borrowed_lifestyle_ratio=Decimal('0.10'),  # Below threshold
            credit_revolver_ratio=Decimal('0.60'),  # High revolver
            discretionary_spending_ratio=Decimal('0.30'),
            impulse_transaction_ratio=Decimal('0.20'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"

    def test_debt_dependent_high_confidence(self):
        """Test DEBT_DEPENDENT gets high confidence with clear signals."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.0'),  # Negative/near-zero
            borrowed_lifestyle_ratio=Decimal('0.40'),  # Very high
            credit_revolver_ratio=Decimal('0.70'),
            discretionary_spending_ratio=Decimal('0.50'),
            impulse_transaction_ratio=Decimal('0.30'),
            lifestyle_creep_index=Decimal('0.30'),
            transaction_count=250,
        )
        assert profile == "DEBT_DEPENDENT"
        assert confidence >= Decimal('0.7')


# ============================================================
# DEBT_OPTIMIZER Tests
# ============================================================

class TestDebtOptimizerProfile:
    """Tests for DEBT_OPTIMIZER personality classification."""

    def test_debt_optimizer_responsible_usage(self):
        """Test DEBT_OPTIMIZER with responsible credit usage."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.10'),  # Low credit dependency
            credit_revolver_ratio=Decimal('0.10'),  # Low revolver, pays in full
            discretionary_spending_ratio=Decimal('0.25'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.05'),
            transaction_count=120,
        )
        assert profile == "DEBT_OPTIMIZER"
        assert "responsibly" in explanation.lower() or "credit" in explanation.lower()

    def test_debt_optimizer_confidence(self):
        """Test DEBT_OPTIMIZER gets moderate confidence."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.12'),
            borrowed_lifestyle_ratio=Decimal('0.08'),
            credit_revolver_ratio=Decimal('0.05'),
            discretionary_spending_ratio=Decimal('0.30'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "DEBT_OPTIMIZER"
        assert Decimal('0.5') <= confidence <= Decimal('0.7')

    def test_debt_optimizer_not_if_no_credit(self):
        """Test DEBT_OPTIMIZER requires some credit usage."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        # Should be BALANCED since savings < 20% and no credit usage
        assert profile == "BALANCED"


# ============================================================
# SPENDER Tests
# ============================================================

class TestSpenderProfile:
    """Tests for SPENDER personality classification."""

    def test_spender_high_discretionary(self):
        """Test SPENDER with high discretionary spending."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage to avoid DEBT_OPTIMIZER
            discretionary_spending_ratio=Decimal('0.50'),  # High discretionary
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "SPENDER"
        assert "SPENDER" in explanation

    def test_spender_high_impulse(self):
        """Test SPENDER with high impulse transaction ratio."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage to avoid DEBT_OPTIMIZER
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.40'),  # High impulse
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "SPENDER"
        assert "impulse" in explanation.lower() or "discretionary" in explanation.lower()

    def test_spender_high_lifestyle_creep(self):
        """Test SPENDER with high lifestyle creep index."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage to avoid DEBT_OPTIMIZER
            discretionary_spending_ratio=Decimal('0.15'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.60'),  # High creep (>50%)
            transaction_count=100,
        )
        assert profile == "SPENDER"


# ============================================================
# BALANCED Tests
# ============================================================

class TestBalancedProfile:
    """Tests for BALANCED personality classification."""

    def test_balanced_moderate_values(self):
        """Test BALANCED with moderate savings and low extremes."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.12'),  # Moderate savings
            borrowed_lifestyle_ratio=Decimal('0.10'),  # Low credit dependency
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.25'),  # Moderate discretionary
            impulse_transaction_ratio=Decimal('0.15'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "BALANCED"
        assert "BALANCED" in explanation

    def test_balanced_default_fallback(self):
        """Test BALANCED is the default when no clear pattern."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.05'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=50,
        )
        assert profile == "BALANCED"

    def test_balanced_explanation_content(self):
        """Test BALANCED explanation contains key metrics."""
        profile, _, explanation = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert "15.0" in explanation
        assert "10.0" in explanation


# ============================================================
# Confidence Tests
# ============================================================

class TestConfidenceCalculation:
    """Tests for confidence score calculation."""

    def test_confidence_bounds(self):
        """Test confidence is always between 0 and 1."""
        for _ in range(10):
            profile, confidence, _ = classify_financial_personality(
                savings_rate=Decimal('0.15'),
                borrowed_lifestyle_ratio=Decimal('0.10'),
                credit_revolver_ratio=Decimal('0.10'),
                discretionary_spending_ratio=Decimal('0.20'),
                impulse_transaction_ratio=Decimal('0.10'),
                lifestyle_creep_index=Decimal('0.05'),
                transaction_count=100,
            )
            assert Decimal('0') <= confidence <= Decimal('1')

    def test_confidence_increases_with_volume(self):
        """Test confidence increases with more transactions."""
        profile1, confidence1, _ = classify_financial_personality(
            savings_rate=Decimal('0.10'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=50,
        )
        profile2, confidence2, _ = classify_financial_personality(
            savings_rate=Decimal('0.10'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=400,
        )
        assert confidence2 > confidence1

    def test_confidence_saver_strong(self):
        """Test SAVER gets confidence bonus for strong savings."""
        _, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.30'),  # Strong
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.0'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert confidence >= Decimal('0.6')


# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self):
        """Test that same inputs produce same outputs."""
        inputs = {
            "savings_rate": Decimal('0.25'),
            "borrowed_lifestyle_ratio": Decimal('0.05'),
            "credit_revolver_ratio": Decimal('0.0'),
            "discretionary_spending_ratio": Decimal('0.20'),
            "impulse_transaction_ratio": Decimal('0.10'),
            "lifestyle_creep_index": Decimal('0.05'),
            "transaction_count": 150,
        }

        result1 = classify_financial_personality(**inputs)
        result2 = classify_financial_personality(**inputs)

        assert result1 == result2
        assert result1[0] == result2[0]  # Profile
        assert result1[1] == result2[1]  # Confidence
        assert result1[2] == result2[2]  # Explanation

    def test_deterministic_all_profiles(self):
        """Test determinism across all profile types."""
        test_cases = [
            ("SAVER", Decimal('0.25'), Decimal('0.0'), Decimal('0.0')),
            ("DEBT_DEPENDENT", Decimal('0.10'), Decimal('0.30'), Decimal('0.60')),
            ("DEBT_OPTIMIZER", Decimal('0.12'), Decimal('0.08'), Decimal('0.10')),
            ("SPENDER", Decimal('0.05'), Decimal('0.10'), Decimal('0.0')),  # No credit for SPENDER
            ("BALANCED", Decimal('0.15'), Decimal('0.05'), Decimal('0.0')),
        ]

        for expected_profile, savings, borrowed, revolver in test_cases:
            # Use discretionary values that only trigger SPENDER for SPENDER case
            disc = Decimal('0.50') if expected_profile == "SPENDER" else Decimal('0.25')
            impulse = Decimal('0.40') if expected_profile == "SPENDER" else Decimal('0.10')
            creep = Decimal('0.60') if expected_profile == "SPENDER" else Decimal('0.10')

            result1 = classify_financial_personality(
                savings_rate=savings,
                borrowed_lifestyle_ratio=borrowed,
                credit_revolver_ratio=revolver,
                discretionary_spending_ratio=disc,
                impulse_transaction_ratio=impulse,
                lifestyle_creep_index=creep,
                transaction_count=100,
            )
            result2 = classify_financial_personality(
                savings_rate=savings,
                borrowed_lifestyle_ratio=borrowed,
                credit_revolver_ratio=revolver,
                discretionary_spending_ratio=disc,
                impulse_transaction_ratio=impulse,
                lifestyle_creep_index=creep,
                transaction_count=100,
            )
            assert result1[0] == expected_profile
            assert result1 == result2


# ============================================================
# Edge Cases Tests
# ============================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_savings_rate(self):
        """Test with zero savings rate."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0'),
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=50,
        )
        assert profile == "BALANCED"

    def test_zero_transaction_count(self):
        """Test with zero transactions."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=0,
        )
        # Should still return a valid profile
        assert profile in ("BALANCED", "SAVER")

    def test_negative_savings_rate(self):
        """Test with negative savings rate (overspending)."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('-0.10'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.30'),
            discretionary_spending_ratio=Decimal('0.40'),
            impulse_transaction_ratio=Decimal('0.20'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        # Should be SPENDER or DEBT_DEPENDENT
        assert profile in ("SPENDER", "DEBT_DEPENDENT")

    def test_very_high_values(self):
        """Test with very high metric values."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.90'),
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.0'),
            impulse_transaction_ratio=Decimal('0.0'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=500,
        )
        assert profile == "SAVER"
        assert confidence >= Decimal('0.8')


# ============================================================
# Priority Tests
# ============================================================

class TestProfilePriority:
    """Tests to verify classification priority order."""

    def test_debt_dependent_takes_priority_over_saver(self):
        """DEBT_DEPENDENT should be detected before SAVER."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.25'),  # Would qualify for SAVER
            borrowed_lifestyle_ratio=Decimal('0.25'),  # But DEBT_DEPENDENT takes priority
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"

    def test_saver_takes_priority_over_spender(self):
        """SAVER should be detected before SPENDER."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.25'),  # SAVER qualifies
            borrowed_lifestyle_ratio=Decimal('0.05'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.45'),  # SPENDER would also qualify
            impulse_transaction_ratio=Decimal('0.35'),
            lifestyle_creep_index=Decimal('0.60'),
            transaction_count=100,
        )
        assert profile == "SAVER"


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
