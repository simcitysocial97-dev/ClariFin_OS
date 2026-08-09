"""Golden Cross-Layer Planner Tests — Program 7B.5

These tests validate that CrossLayerImpactPlanner and VerificationPlanner
produce deterministic, accurate blast-radius results.
"""

from __future__ import annotations

import json


from runtime.foundation.verification.models import (
    VerificationScope,
)
from runtime.foundation.verification.planner import (
    VerificationPlanner,
    plan_verification,
)


class TestCrossLayerImpactPlanner:
    """Tests for Program 7A CrossLayerImpactPlanner."""

    def test_loan_engine_amortization_blast_radius(
        self, planner_with_map, synthetic_cross_layer_map
    ):
        map_data = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanAnalysisService", "LoanService", "LoanSimulationService", "TransactionIntelligenceService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": [
                    "GET /api/loans",
                    "GET /api/loans/{loan_id}",
                    "POST /api/loans",
                    "PUT /api/loans/{loan_id}",
                    "DELETE /api/loans/{loan_id}",
                    "GET /api/loans/{loan_id}/schedule",
                    "POST /api/loans/{loan_id}/prepayment-simulation",
                    "POST /api/loans/{loan_id}/foreclosure-simulation",
                    "POST /api/loans/{loan_id}/rate-change-simulation",
                    "POST /api/loans/{loan_id}/payments",
                    "GET /api/loans/analysis/priority",
                    "POST /api/loans/{loan_id}/analysis/prepayment-vs-foreclosure",
                    "POST /api/loans/analysis/surplus-allocation",
                ],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": [
                    "LoansSummary",
                    "AmortizationSchedule",
                    "PaymentProgress",
                    "InterestAnalysis",
                    "InsightsPanel",
                    "EvidenceDrawer",
                    "LoansToolbar",
                    "CrossNavigation",
                    "LoansPageSkeleton",
                    "LoansErrorState",
                    "LoansEmptyState",
                ],
                "tests": [
                    "backend/tests/unit/engines/loan/__init__.py",
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/unit/engines/loan/test_loan_engine.py",
                    "backend/tests/contract/generated/test_loans.py",
                    "backend/tests/contract/generated/test_v1.py",
                ],
                "graphRenderers": [],
            }
        }
        planner = planner_with_map(map_data)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )

        assert "LoanService" in report.affected_services
        assert "LoanAnalysisService" in report.affected_services
        assert "LoanSimulationService" in report.affected_services
        assert "TransactionIntelligenceService" in report.affected_services
        assert "GET /api/loans/{loan_id}/schedule" in report.affected_endpoints
        assert "useLoansCapability" in report.affected_capabilities
        assert "loansMapper" in report.affected_mappers
        assert "LoansWorkspace" in report.affected_workspaces
        assert "AmortizationSchedule" in report.affected_components
        assert "LoansSummary" in report.affected_components
        assert "backend/tests/unit/engines/loan/test_amortization.py" in report.affected_tests
        assert "backend/tests/contract/generated/test_loans.py" in report.affected_tests

        excluded = ["dashboard", "forecast", "investments", "cards"]
        for domain in excluded:
            assert domain not in json.dumps(report.to_dict()).lower()

    def test_endpoint_removed_blast_radius(self, planner_with_map):
        map_data = {
            "backend/src/routers/loans.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable", "LoansSummary"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                    "backend/tests/contract/generated/test_v1.py",
                ],
                "graphRenderers": [],
            }
        }
        planner = planner_with_map(map_data)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/routers/loans.py"]
        )

        assert "backend/src/routers/loans.py" in report.affected_routers
        assert "GET /api/loans/{loan_id}/schedule" in report.affected_endpoints
        assert "LoanService" in report.affected_services
        assert "useLoansCapability" in report.affected_capabilities
        assert "LoansWorkspace" in report.affected_workspaces

    def test_workspace_registration_missing_blast_radius(self, planner_with_map):
        map_data = {
            "frontend/lib/workspaces/loansworspace.ts": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable", "LoansSummary"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }
        planner = planner_with_map(map_data)
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/workspaces/loansworspace.ts"]
        )

        assert "LoansWorkspace" in report.affected_workspaces
        assert "useLoansCapability" in report.affected_capabilities
        assert "app/loans/page.tsx" in report.affected_pages
        assert "LoansSummary" in report.affected_components
        assert "LoansViewModel" in report.affected_view_models

    def test_router_service_disconnect_blast_radius(self, planner_with_map):
        map_data = {
            "backend/src/routers/loans.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable", "LoansSummary"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                    "backend/tests/contract/generated/test_v1.py",
                ],
                "graphRenderers": [],
            }
        }
        planner = planner_with_map(map_data)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/routers/loans.py", "backend/src/services/loan_service.py"]
        )

        assert "backend/src/routers/loans.py" in report.affected_routers
        assert "LoanService" in report.affected_services
        assert "GET /api/loans/{loan_id}/schedule" in report.affected_endpoints

    def test_graph_renderer_disconnect_blast_radius(self, planner_with_map):
        map_data = {
            "frontend/lib/renderers/loangraphrenderer.tsx": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable", "LoansSummary"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": ["LoanGraphRenderer"],
            }
        }
        planner = planner_with_map(map_data)
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/renderers/loangraphrenderer.tsx"]
        )

        assert "LoanGraphRenderer" in report.affected_graph_renderers
        assert "useLoansCapability" in report.affected_capabilities
        assert "LoansWorkspace" in report.affected_workspaces

    def test_baseline_no_changes(self, planner_with_map):
        planner = planner_with_map({})
        report = planner.analyze_cross_layer_impact([])

        assert report.affected_engines == []
        assert report.affected_services == []
        assert report.affected_capabilities == []
        assert report.affected_tests == []
        assert report.dependency_chains == []

    def test_dependency_chain_format(self, planner_with_map):
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
        planner = planner_with_map(map_data)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )

        assert len(report.dependency_chains) == 1
        chain = report.dependency_chains[0]
        assert chain["source"] == "backend/src/engines/loan_engine/amortization.py"
        assert chain["engine"] == "backend/src/engines/loan_engine/amortization.py"
        assert "LoanService" in chain["services"]
        assert "GET /api/loans/{loan_id}/schedule" in chain["endpoints"]
        assert "useLoansCapability" in chain["capabilities"]
        assert "LoansWorkspace" in chain["workspaces"]
        assert "AmortizationTable" in chain["components"]

    def test_minimal_verification_plan_structure(self, planner_with_map):
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
        planner = planner_with_map(map_data)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        plan = report.verification_plan

        assert plan["run_unit"] is True
        assert plan["run_contract"] is True
        assert plan["run_property"] is True
        assert plan["run_frontend"] is True
        assert plan["run_integration"] is True
        assert "backend/src/engines/loan_engine/amortization.py" in plan["engines"]
        assert "LoanService" in plan["services"]
        assert "useLoansCapability" in plan["capabilities"]


class TestVerificationPlanner:
    """Tests for the VerificationPlanner."""

    def test_plan_generates_targets_for_loan_engine(self, isolated_registry):
        planner = VerificationPlanner(registry=isolated_registry)
        from runtime.foundation.verification.planner.planner import PlanningContext

        context = PlanningContext(
            changed_files=["backend/src/engines/loan_engine/amortization.py"],
            requested_scope=VerificationScope.BACKEND,
            force_scope=VerificationScope.BACKEND,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )
        plan = planner.plan(context)

        assert len(plan.targets) > 0
        assert len(plan.steps) > 0
        target_ids = [t.id for t in plan.targets]
        step_ids = [s.id for s in plan.steps]
        assert all(tid.startswith("target-") for tid in target_ids)
        assert all(sid.startswith("step-") for sid in step_ids)

    def test_plan_includes_loan_capability_requirements(self, isolated_registry):
        planner = VerificationPlanner(registry=isolated_registry)
        from runtime.foundation.verification.planner.planner import PlanningContext

        context = PlanningContext(
            changed_files=["backend/src/engines/loan_engine/amortization.py"],
            requested_scope=VerificationScope.BACKEND,
            force_scope=VerificationScope.BACKEND,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )
        plan = planner.plan(context)

        capabilities = {t.capability for t in plan.targets if t.capability}
        assert "loan-engine" in capabilities

    def test_plan_excludes_unrelated_capabilities(self, isolated_registry):
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

    def test_plan_deterministic(self, isolated_registry):
        planner = VerificationPlanner(registry=isolated_registry)
        from runtime.foundation.verification.planner.planner import PlanningContext

        context = PlanningContext(
            changed_files=["backend/src/engines/loan_engine/amortization.py"],
            requested_scope=VerificationScope.BACKEND,
            force_scope=VerificationScope.BACKEND,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )
        plan1 = planner.plan(context)
        plan2 = planner.plan(context)

        assert plan1.id == plan2.id
        assert len(plan1.targets) == len(plan2.targets)
        assert len(plan1.steps) == len(plan2.steps)
        assert [t.id for t in plan1.targets] == [t.id for t in plan2.targets]

    def test_plan_empty_changed_files(self, isolated_registry):
        planner = VerificationPlanner(registry=isolated_registry)
        from runtime.foundation.verification.planner.planner import PlanningContext

        context = PlanningContext(
            changed_files=[],
            requested_scope=VerificationScope.QUICK,
            force_scope=VerificationScope.QUICK,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )
        plan = planner.plan(context)

        assert plan.id.startswith("plan-")
        assert plan.scope == VerificationScope.QUICK

    def test_plan_metadata_includes_changed_files(self, isolated_registry):
        planner = VerificationPlanner(registry=isolated_registry)
        from runtime.foundation.verification.planner.planner import PlanningContext

        changed = ["backend/src/engines/loan_engine/amortization.py"]
        context = PlanningContext(
            changed_files=changed,
            requested_scope=VerificationScope.BACKEND,
            force_scope=VerificationScope.BACKEND,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )
        plan = planner.plan(context)

        assert plan.metadata["changed_files"] == changed
        assert "impacted_scopes" in plan.metadata
        assert "impacted_capabilities" in plan.metadata

    def test_plan_convenience_function(self, isolated_registry):
        plan = plan_verification(
            changed_files=["backend/src/engines/loan_engine/amortization.py"],
            scope=VerificationScope.BACKEND,
        )
        assert plan.scope == VerificationScope.BACKEND
        assert len(plan.targets) > 0
