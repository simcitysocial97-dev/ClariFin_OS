"""False Negative Rate Tests — Program 7B.5

Measures the rate at which the planner fails to detect downstream consumers.
Target: 0% false negative rate.
"""

from __future__ import annotations

import json
from pathlib import Path


from runtime.foundation.verification.planner import (
    CrossLayerImpactPlanner,
)


class TestFalseNegativeRate:
    """False negative rate benchmarks."""

    def test_dto_rename_detection(self, tmp_path: Path):
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
        planner = CrossLayerImpactPlanner(map_path=map_path)

        changed = ["backend/src/engines/loan_engine/amortization.py"]
        report = planner.analyze_cross_layer_impact(changed)

        assert "LoanService" in report.affected_services
        assert "GET /api/loans/{loan_id}/schedule" in report.affected_endpoints
        assert "useLoansCapability" in report.affected_capabilities
        assert "loansMapper" in report.affected_mappers
        assert "LoansWorkspace" in report.affected_workspaces
        assert "AmortizationTable" in report.affected_components

    def test_mapper_rename_detection(self, tmp_path: Path):
        map_data = {
            "backend/src/mappers/loans_mapper.py": {
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
        planner = CrossLayerImpactPlanner(map_path=map_path)

        changed = ["backend/src/mappers/loans_mapper.py"]
        report = planner.analyze_cross_layer_impact(changed)

        assert "LoanService" in report.affected_services
        assert "useLoansCapability" in report.affected_capabilities
        assert "loansMapper" in report.affected_mappers

    def test_capability_rename_detection(self, tmp_path: Path):
        map_data = {
            "frontend/lib/capabilities/useloanscapability.ts": {
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
        planner = CrossLayerImpactPlanner(map_path=map_path)

        changed = ["frontend/lib/capabilities/useloanscapability.ts"]
        report = planner.analyze_cross_layer_impact(changed)

        assert "useLoansCapability" in report.affected_capabilities
        assert "LoanService" in report.affected_services
        assert "LoansWorkspace" in report.affected_workspaces

    def test_router_endpoint_rename_detection(self, tmp_path: Path):
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
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                    "backend/tests/contract/generated/test_v1.py",
                ],
                "graphRenderers": [],
            }
        }
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")
        planner = CrossLayerImpactPlanner(map_path=map_path)

        changed = ["backend/src/routers/loans.py"]
        report = planner.analyze_cross_layer_impact(changed)

        assert "backend/src/routers/loans.py" in report.affected_routers
        assert "GET /api/loans/{loan_id}/schedule" in report.affected_endpoints
        assert "LoanService" in report.affected_services

    def test_workspace_registration_removal_detection(self, tmp_path: Path):
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
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data), encoding="utf-8")
        planner = CrossLayerImpactPlanner(map_path=map_path)

        changed = ["frontend/lib/workspaces/loansworspace.ts"]
        report = planner.analyze_cross_layer_impact(changed)

        assert "LoansWorkspace" in report.affected_workspaces
        assert "useLoansCapability" in report.affected_capabilities
        assert "app/loans/page.tsx" in report.affected_pages

    def test_false_negative_rate_calculation(self, tmp_path: Path):
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
        planner = CrossLayerImpactPlanner(map_path=map_path)

        changed = ["backend/src/engines/loan_engine/amortization.py"]
        report = planner.analyze_cross_layer_impact(changed)

        expected_consumers = [
            "LoanService",
            "GET /api/loans/{loan_id}/schedule",
            "useLoansCapability",
            "loansMapper",
            "LoansWorkspace",
            "AmortizationTable",
        ]
        chain = report.dependency_chains[0]
        missed = []
        for consumer in expected_consumers:
            found = False
            for key, values in chain.items():
                if isinstance(values, list) and consumer in values:
                    found = True
                    break
            if not found:
                missed.append(consumer)

        fn_rate = len(missed) / len(expected_consumers)
        assert fn_rate == 0.0, f"False negative rate is {fn_rate}, missed: {missed}"
