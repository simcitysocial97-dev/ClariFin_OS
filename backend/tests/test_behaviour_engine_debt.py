"""Tests for Behaviour Engine Phase 2 — Debt Intelligence metrics."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behaviour_engine import (
    compute_credit_dependency_ratio,
    compute_credit_revolver_ratio,
    compute_debt_cycle_score,
    compute_foir,
)

# ============================================================
# Tests: Credit Dependency Ratio
# ============================================================

class TestCreditDependencyRatio:
    """Tests for compute_credit_dependency_ratio."""

    def test_no_credit_dependency(self):
        """No credit-funded expenses should return 0 ratio."""
        result = compute_credit_dependency_ratio(0, 100000)
        assert result == Decimal('0')

    def test_full_credit_dependency(self):
        """All expenses credit-funded should return 1.0 ratio."""
        result = compute_credit_dependency_ratio(100000, 100000)
        assert result == Decimal('1.0')

    def test_partial_credit_dependency(self):
        """Partial credit dependency returns appropriate ratio."""
        result = compute_credit_dependency_ratio(25000, 100000)
        assert result == Decimal('0.25')

    def test_credit_exceeds_expenses(self):
        """Credit-funded exceeding total expenses returns > 1 ratio."""
        result = compute_credit_dependency_ratio(150000, 100000)
        assert result == Decimal('1.5')


# ============================================================
# Tests: Debt Cycle Score
# ============================================================

class TestDebtCycleScore:
    """Tests for compute_debt_cycle_score."""

    def test_no_debt_cycle(self):
        """No credit advances, no revolving, negative trend -> score 0."""
        result = compute_debt_cycle_score(0, 0, Decimal('-0.5'))
        assert result == 0

    def test_increasing_debt_low_advances(self):
        """Low advances but rising trend -> elevated score."""
        result = compute_debt_cycle_score(1, 1, Decimal('0.7'))
        # advance=10, revolve=20, trend=80 -> 0.3*10 + 0.3*20 + 0.4*80 = 3+6+32 = 41
        assert result == 41

    def test_high_credit_advances(self):
        """Multiple credit advances -> high score."""
        result = compute_debt_cycle_score(4, 0, Decimal('0'))
        # advance=60, revolve=0, trend=5 -> 0.3*60 + 0.3*0 + 0.4*5 = 18+0+2 = 20
        assert result == 20

    def test_revolving_behavior(self):
        """Heavy revolving -> elevated score."""
        result = compute_debt_cycle_score(0, 5, Decimal('0.2'))
        # advance=0, revolve=80, trend=20 -> 0.3*0 + 0.3*80 + 0.4*20 = 0+24+8 = 32
        assert result == 32

    def test_max_debt_cycle(self):
        """Maximum debt cycle behavior -> high score near 100."""
        result = compute_debt_cycle_score(6, 6, Decimal('0.9'))
        # advance=90, revolve=80, trend=80 -> 0.3*90 + 0.3*80 + 0.4*80 = 27+24+32 = 83
        assert result == 83


# ============================================================
# Tests: FOIR
# ============================================================

class TestFOIR:
    """Tests for compute_foir."""

    def test_no_obligations(self):
        """No obligations and no income -> healthy with 0 ratio."""
        ratio, band = compute_foir(0, 0, 0)
        assert ratio == Decimal('0')
        assert band == "HEALTHY"

    def test_healthy_foir(self):
        """FOIR under 30% -> healthy band."""
        ratio, band = compute_foir(2000000, 500000, 10000000)  # 25%
        assert ratio == Decimal('0.25')
        assert band == "HEALTHY"

    def test_moderate_foir(self):
        """FOIR 30-50% -> moderate band."""
        ratio, band = compute_foir(3500000, 1500000, 10000000)  # 50%
        assert ratio == Decimal('0.50')
        assert band == "MODERATE"

    def test_warning_foir(self):
        """FOIR 50-60% -> warning band."""
        ratio, band = compute_foir(5500000, 0, 10000000)  # 55% - in warning range
        assert ratio == Decimal('0.55')
        assert band == "WARNING"

    def test_critical_foir(self):
        """FOIR over 60% -> critical band."""
        ratio, band = compute_foir(7000000, 0, 10000000)  # 70% - in critical range
        assert ratio == Decimal('0.70')
        assert band == "CRITICAL"

    def test_foir_exactly_30(self):
        """FOIR exactly 30% -> healthy band is inclusive at 30%."""
        ratio, band = compute_foir(3000000, 0, 10000000)
        assert ratio == Decimal('0.30')
        assert band == "HEALTHY"

    def test_foir_above_30(self):
        """FOIR just above 30% -> moderate band."""
        ratio, band = compute_foir(3100000, 0, 10000000)  # 31%
        assert ratio == Decimal('0.31')
        assert band == "MODERATE"

    def test_emi_heavy_user(self):
        """EMI-heavy user with high FOIR -> critical band."""
        # Income ₹1L, EMI ₹70K, min due ₹5K = 75% FOIR
        ratio, band = compute_foir(7000000, 500000, 10000000)
        assert ratio == Decimal('0.75')
        assert band == "CRITICAL"


# ============================================================
# Tests: Credit Revolver Ratio
# ============================================================

class TestCreditRevolverRatio:
    """Tests for compute_credit_revolver_ratio."""

    def test_no_credit_activity(self):
        """No credit activity -> 0 ratio."""
        result = compute_credit_revolver_ratio(0, 0)
        assert result == Decimal('0')

    def test_full_revolver(self):
        """All active months with partial payment -> 1.0 ratio."""
        result = compute_credit_revolver_ratio(6, 6)
        assert result == Decimal('1.0')

    def test_partial_revolver(self):
        """Some revolving months -> partial ratio."""
        result = compute_credit_revolver_ratio(3, 6)
        assert result == Decimal('0.5')

    def test_no_revolving(self):
        """No partial payments -> 0 ratio."""
        result = compute_credit_revolver_ratio(0, 6)
        assert result == Decimal('0')


# ============================================================
# Tests: Determinism
# ============================================================

class TestDeterminism:
    """Tests to ensure deterministic behavior."""

    def test_foir_deterministic(self):
        """Same inputs should produce same outputs."""
        for _ in range(10):
            ratio, band = compute_foir(4000000, 1500000, 10000000)  # 55% - warning range
            assert ratio == Decimal('0.55')
            assert band == "WARNING"

    def test_debt_cycle_deterministic(self):
        """Debt cycle score should be deterministic."""
        result = compute_debt_cycle_score(3, 2, Decimal('0.25'))
        # advance=30, revolve=20, trend=20 -> 0.3*30 + 0.3*20 + 0.4*20 = 9+6+8 = 23
        assert result == 23
