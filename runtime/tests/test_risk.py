"""Tests for RiskAnalyzer — Program 8."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.foundation.intelligence.models import Severity
from runtime.foundation.intelligence.risk import RiskAnalyzer
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
        "tests": ["backend/tests/unit/loan/test_amortization.py"],
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


class TestRiskAnalyzer:
    def test_analyze_returns_risk_report(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        assert risk.score >= 0
        assert risk.score <= 100
        assert isinstance(risk.severity, Severity)

    def test_analyze_score_is_deterministic(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk1 = analyzer.analyze(report)
        risk2 = analyzer.analyze(report)

        assert risk1.score == risk2.score

    def test_analyze_severity_classification(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        if risk.score >= 80:
            assert risk.severity == Severity.CRITICAL
        elif risk.score >= 60:
            assert risk.severity == Severity.HIGH
        elif risk.score >= 30:
            assert risk.severity == Severity.MEDIUM
        else:
            assert risk.severity == Severity.LOW

    def test_analyze_has_reasons(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        assert len(risk.reasons) > 0

    def test_analyze_changed_layers(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        assert "engine" in risk.changed_layers

    def test_analyze_cross_layer_depth(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        assert risk.cross_layer_depth > 0

    def test_analyze_factors_contains_expected_keys(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        assert "changed_engines" in risk.factors
        assert "changed_capabilities" in risk.factors
        assert "changed_endpoints" in risk.factors

    def test_empty_report_low_score(
        self,
        tmp_path: Path,
    ) -> None:
        import json

        empty_map = {}
        map_path = tmp_path / "empty-map.json"
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(json.dumps(empty_map), encoding="utf-8")

        planner = CrossLayerImpactPlanner(map_path=map_path)
        report = planner.analyze_cross_layer_impact([])
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        assert risk.score == 0
        assert risk.severity == Severity.LOW

    def test_risk_report_immutable(
        self,
        sample_map_path: Path,
    ) -> None:
        planner = CrossLayerImpactPlanner(map_path=sample_map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"],
        )
        analyzer = RiskAnalyzer()
        risk = analyzer.analyze(report)

        with pytest.raises(AttributeError):
            risk.score = 0  # type: ignore[misc]