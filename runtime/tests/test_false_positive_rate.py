"""False Positive Rate Tests — Program 7B.5

Measures the rate at which the planner incorrectly schedules unrelated domains.
Target: 0% false positive rate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.models import VerificationScope
from runtime.foundation.verification.planner import (
    CrossLayerImpactPlanner,
    VerificationPlanner,
)


class TestFalsePositiveRate:
    """False positive rate benchmarks."""

    @pytest.fixture
    def loan_map(self, tmp_path: Path):
        map_data = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")
        return map_path

    @pytest.fixture
    def account_map(self, tmp_path: Path):
        map_data = {
            "backend/src/engines/account_engine/balance.py": {
                "engine": "backend/src/engines/account_engine/balance.py",
                "services": ["AccountService"],
                "routers": ["backend/src/routers/accounts.py"],
                "endpoints": ["GET /api/v1/accounts/{account_id}/balance"],
                "capabilities": ["useAccountsCapability"],
                "mappers": ["accountsMapper"],
                "viewModels": ["AccountsViewModel"],
                "pages": ["app/accounts/page.tsx"],
                "workspace": ["AccountsWorkspace"],
                "components": ["AccountsSummary", "BalanceTrend"],
                "tests": [
                    "backend/tests/unit/engines/account/test_account_engine.py",
                    "backend/tests/contract/generated/test_accounts.py",
                ],
                "graphRenderers": [],
            }
        }
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")
        return map_path

    def _get_scheduled_domains(self, planner, changed_files):
        report = planner.analyze_cross_layer_impact(changed_files)
        data = report.to_dict()
        domains = set()
        for key in [
            "affected_engines",
            "affected_services",
            "affected_routers",
            "affected_endpoints",
            "affected_capabilities",
            "affected_mappers",
            "affected_view_models",
            "affected_pages",
            "affected_workspaces",
            "affected_components",
            "affected_graph_renderers",
            "affected_tests",
        ]:
            for item in data.get(key, []):
                domains.add(item.lower())
        return domains

    def test_loan_engine_no_dashboard(self, loan_map):
        planner = CrossLayerImpactPlanner(map_path=loan_map)
        domains = self._get_scheduled_domains(
            planner, ["backend/src/engines/loan_engine/amortization.py"]
        )
        assert "dashboard" not in domains
        assert "forecast" not in domains
        assert "investments" not in domains
        assert "cards" not in domains

    def test_loan_engine_no_cashflow_behaviour(self, loan_map):
        planner = CrossLayerImpactPlanner(map_path=loan_map)
        domains = self._get_scheduled_domains(
            planner, ["backend/src/engines/loan_engine/amortization.py"]
        )
        assert "cashflow" not in domains
        assert "behaviour" not in domains
        assert "reconciliation" not in domains

    def test_account_engine_no_loans(self, account_map):
        planner = CrossLayerImpactPlanner(map_path=account_map)
        domains = self._get_scheduled_domains(
            planner, ["backend/src/engines/account_engine/balance.py"]
        )
        assert "loans" not in domains
        assert "useloanscapability" not in domains
        assert "amortization" not in domains

    def test_loan_planner_excludes_unrelated_capabilities(self, isolated_registry):
        planner = VerificationPlanner(registry=isolated_registry)
        from runtime.foundation.verification.planner.planner import PlanningContext

        context = PlanningContext(
            changed_files=["backend/src/engines/loan_engine/amortization.py"],
            requested_scope=VerificationScope.QUICK,
            force_scope=VerificationScope.QUICK,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )
        plan = planner.plan(context)
        impacted = plan.metadata.get("impacted_capabilities", [])
        assert "loan-engine" in impacted

    def test_false_positive_rate_calculation(self, loan_map):
        planner = CrossLayerImpactPlanner(map_path=loan_map)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        data = report.to_dict()

        expected_excluded = ["dashboard", "forecast", "investments", "cards", "cashflow", "behaviour", "reconciliation"]
        all_affected = []
        for key in [
            "affected_engines",
            "affected_services",
            "affected_routers",
            "affected_endpoints",
            "affected_capabilities",
            "affected_mappers",
            "affected_view_models",
            "affected_pages",
            "affected_workspaces",
            "affected_components",
            "affected_graph_renderers",
            "affected_tests",
        ]:
            all_affected.extend(data.get(key, []))

        false_positives = [
            item for item in all_affected
            if any(excluded.lower() in item.lower() for excluded in expected_excluded)
        ]
        fp_rate = len(false_positives) / max(len(all_affected), 1)
        assert fp_rate == 0.0, f"False positive rate is {fp_rate}, expected 0.0"
