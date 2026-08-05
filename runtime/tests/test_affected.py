"""Tests for AffectedTestPlanner — Program 8."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.foundation.intelligence.affected import AffectedTestPlanner
from runtime.foundation.intelligence.models import AffectedTestPlan


SAMPLE_MAP = {
    "backend/src/engines/loan_engine/amortization.py": {
        "engine": "backend/src/engines/loan_engine/amortization.py",
        "services": ["LoanService"],
        "routers": ["backend/src/routers/loans.py"],
        "endpoints": ["GET /api/loans/{id}/schedule"],
        "capabilities": ["useLoansCapability"],
        "mappers": ["loansMapper"],
        "viewModels": ["LoansViewModel"],
        "pages": ["app/loans/page.tsx"],
        "workspace": ["LoansWorkspace"],
        "components": ["AmortizationSchedule"],
        "tests": [
            "backend/tests/unit/engines/loan/test_amortization.py",
        ],
        "graphRenderers": [],
    }
}


@pytest.fixture
def sample_map_path(tmp_path: Path) -> Path:
    import json

    map_path = tmp_path / "cross-layer-map.json"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(SAMPLE_MAP), encoding="utf-8")
    return map_path


class TestAffectedTestPlanner:
    def test_build_test_plan_returns_plan(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        assert isinstance(plan, AffectedTestPlan)

    def test_build_test_plan_has_backend_tests(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        assert len(plan.backend_tests) > 0

    def test_build_test_plan_has_frontend_tests(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        assert len(plan.frontend_tests) > 0

    def test_build_test_plan_has_runtime_tests(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        assert len(plan.runtime_tests) > 0

    def test_build_test_plan_has_contracts(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        assert len(plan.contracts) > 0

    def test_build_test_plan_total_count_matches(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        expected = (
            len(plan.backend_tests)
            + len(plan.frontend_tests)
            + len(plan.runtime_tests)
            + len(plan.playwright)
            + len(plan.contracts)
        )
        assert plan.total_count == expected

    def test_build_test_plan_no_related_files(
        self,
        tmp_path: Path,
    ) -> None:
        import json

        empty_map = {}
        map_path = tmp_path / "empty-map.json"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(empty_map), encoding="utf-8")

        planner = AffectedTestPlanner()
        plan = planner.build_test_plan([])

        assert plan.total_count == 0

    def test_build_test_plan_deterministic(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan1 = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        plan2 = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )

        assert plan1.backend_tests == plan2.backend_tests
        assert plan1.frontend_tests == plan2.frontend_tests
        assert plan1.total_count == plan2.total_count

    def test_build_test_plan_excludes_unrelated(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )

        unrelated = ("credit_card", "ledger", "reconciliation", "payment", "saving", "card")
        for test in plan.backend_tests:
            assert not any(kw in test.lower() for kw in unrelated)

    def test_plan_immutable(self, sample_map_path: Path) -> None:
        planner = AffectedTestPlanner()
        plan = planner.build_test_plan(
            ["backend/src/engines/loan_engine/amortization.py"],
        )

        with pytest.raises(AttributeError):
            plan.backend_tests = ()  # type: ignore[misc]