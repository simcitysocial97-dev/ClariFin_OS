"""Tests for DeveloperDiagnostics — Program 8."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.foundation.intelligence.diagnostics import DeveloperDiagnostics
from runtime.foundation.intelligence.models import DiagnosticReport
from runtime.foundation.verification.planner.planner import (
    CrossLayerImpactPlanner,
)


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
        "components": ["AmortizationTable"],
        "tests": [
            "backend/tests/unit/loan/test_amortization.py",
        ],
        "graphRenderers": [],
    }
}


@pytest.fixture
def sample_changed_files() -> list[str]:
    return ["backend/src/engines/loan_engine/amortization.py"]


@pytest.fixture
def planner_with_sample_map(tmp_path: Path) -> CrossLayerImpactPlanner:
    map_path = tmp_path / "cross-layer-map.json"
    import json

    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(SAMPLE_MAP), encoding="utf-8")
    return CrossLayerImpactPlanner(map_path=map_path)


class TestDeveloperDiagnostics:
    def test_diagnose_returns_report(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert isinstance(report, DiagnosticReport)
        assert report.changed_files == tuple(sample_changed_files)

    def test_diagnose_identifies_capabilities(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert "useLoansCapability" in report.affected_capabilities

    def test_diagnose_identifies_workspaces(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert "LoansWorkspace" in report.affected_workspaces

    def test_diagnose_identifies_endpoints(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert "GET /api/loans/{id}/schedule" in report.affected_endpoints

    def test_diagnose_identifies_tests(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert len(report.affected_tests) > 0

    def test_diagnose_suggests_verification_profile(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert report.suggested_verification_profile in (
            "quick",
            "backend",
            "contracts",
            "full",
        )

    def test_diagnose_has_repair_suggestions(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert len(report.repair_suggestions) > 0

    def test_diagnose_risk_score_is_int(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert isinstance(report.risk_score_reference, int)
        assert 0 <= report.risk_score_reference <= 100

    def test_diagnose_estimate_positive(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert report.verification_estimate_local_seconds > 0
        assert report.verification_estimate_ci_minutes > 0

    def test_diagnose_dependency_chain_not_empty(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        assert len(report.dependency_chain) > 0

    def test_diagnose_immutable_report(
        self,
        sample_changed_files: list[str],
        planner_with_sample_map: CrossLayerImpactPlanner,
    ) -> None:
        diagnostics = DeveloperDiagnostics(
            cross_layer_planner=planner_with_sample_map,
        )
        report = diagnostics.diagnose(sample_changed_files)

        with pytest.raises(
            AttributeError,
        ):
            report.changed_files = ()  # type: ignore[misc]