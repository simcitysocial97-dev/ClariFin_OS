"""Capability regression tests.

Verifies that a source change only selects the intended tests and does not
leak to unrelated capabilities.
"""

from __future__ import annotations

import pytest

from src.verification.intelligence.impact_engine import ImpactEngine


@pytest.fixture
def impact_engine() -> ImpactEngine:
    """Provide a fresh ImpactEngine instance."""
    return ImpactEngine()


class TestCapabilityRegression:
    """Verify that source changes only select intended tests."""

    def test_loan_engine_change_selects_debt_management(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Loan engine change must select debt_management, not credit_cards."""
        changed_files = ["backend/src/engines/loan_engine/amortization.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "debt_management" in affected_caps
        ), "Loan engine change should select debt_management capability"
        assert (
            "credit_cards" not in affected_caps
        ), "Loan engine change should NOT select credit_cards capability (leakage)"

    def test_credit_card_engine_change_selects_credit_cards(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Credit card engine change must select credit_cards, not debt_management."""
        changed_files = ["backend/src/engines/credit_card_engine/interest.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "credit_cards" in affected_caps
        ), "Credit card engine change should select credit_cards capability"
        assert (
            "debt_management" not in affected_caps
        ), "Credit card engine change should NOT select debt_management capability (leakage)"

    def test_cashflow_engine_change_selects_household_cashflow(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Cashflow engine change must select household_cashflow, not financial_health."""
        changed_files = ["backend/src/engines/cashflow_engine.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "household_cashflow" in affected_caps
        ), "Cashflow engine change should select household_cashflow capability"
        assert (
            "financial_health" not in affected_caps
        ), "Cashflow engine change should NOT select financial_health capability (leakage)"

    def test_reconciliation_engine_change_selects_reconciliation(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Reconciliation engine change must select reconciliation, not pattern_analysis."""
        changed_files = ["backend/src/engines/reconciliation_engine.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "reconciliation" in affected_caps
        ), "Reconciliation engine change should select reconciliation capability"
        assert (
            "pattern_analysis" not in affected_caps
        ), "Reconciliation engine change should NOT select pattern_analysis capability (leakage)"

    def test_account_engine_change_selects_account_management(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Account engine change must select account_management, not financial_health."""
        changed_files = ["backend/src/engines/account_engine/balance.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "account_management" in affected_caps
        ), "Account engine change should select account_management capability"
        assert (
            "financial_health" not in affected_caps
        ), "Account engine change should NOT select financial_health capability (leakage)"

    def test_behaviour_engine_change_selects_financial_health(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Behaviour engine change must select financial_health, not recommendations."""
        changed_files = ["backend/src/engines/behaviour_engine/cashflow.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "financial_health" in affected_caps
        ), "Behaviour engine change should select financial_health capability"
        assert (
            "recommendations" not in affected_caps
        ), "Behaviour engine change should NOT select recommendations capability (leakage)"

    def test_no_cross_capability_leakage_for_engines(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Engine changes should not leak to unrelated capabilities."""
        engine_files = [
            "backend/src/engines/loan_engine/amortization.py",
            "backend/src/engines/credit_card_engine/interest.py",
            "backend/src/engines/cashflow_engine.py",
            "backend/src/engines/reconciliation_engine.py",
            "backend/src/engines/account_engine/balance.py",
            "backend/src/engines/behaviour_engine/cashflow.py",
        ]

        for engine_file in engine_files:
            impact = impact_engine.analyze([engine_file])
            affected_caps = {c.id for c in impact.affected_capabilities}

            assert len(affected_caps) <= 6, (
                f"Engine file {engine_file} affects {len(affected_caps)} capabilities: "
                f"{affected_caps} - possible leakage"
            )

    def test_router_change_selects_correct_capability(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Router change should select the correct capability."""
        changed_files = ["backend/src/routers/loans.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "debt_management" in affected_caps
        ), "Loans router change should select debt_management capability"
        assert (
            "credit_cards" not in affected_caps
        ), "Loans router change should NOT select credit_cards capability (leakage)"

    def test_repository_change_selects_correct_capability(
        self, impact_engine: ImpactEngine
    ) -> None:
        """Repository change should select the correct capability."""
        changed_files = ["backend/src/repositories/loan_repository.py"]
        impact = impact_engine.analyze(changed_files)

        affected_caps = {c.id for c in impact.affected_capabilities}

        assert (
            "debt_management" in affected_caps
        ), "Loan repository change should select debt_management capability"
        assert (
            "credit_cards" not in affected_caps
        ), "Loan repository change should NOT select credit_cards capability (leakage)"
