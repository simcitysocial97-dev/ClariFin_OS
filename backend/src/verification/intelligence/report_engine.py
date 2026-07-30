"""Report Engine.

Generates machine-readable reports for CI integration:
- dependency-map.json
- change-impact.json
- verification-evidence.json
- architectural-coverage.json
- risk-map.json
- verification-summary.json

Reports integrate with existing generated artifacts and avoid duplication.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


class ReportEngine:
    """Generates all verification intelligence reports."""

    def __init__(self) -> None:
        self._generated_dir = GENERATED_DIR
        self._generated_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self) -> dict[str, Any]:
        """Generate all reports and return a summary."""
        results: dict[str, Any] = {}

        results["dependency_map"] = self._generate_dependency_map()
        results["change_impact"] = self._generate_change_impact()
        results["verification_evidence"] = self._generate_verification_evidence()
        results["architectural_coverage"] = self._generate_architectural_coverage()
        results["risk_map"] = self._generate_risk_map()
        results["verification_summary"] = self._generate_verification_summary(results)

        return results

    def _write_report(self, filename: str, data: dict[str, Any]) -> Path:
        """Write a report to the generated artifacts directory."""
        path = self._generated_dir / filename
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def _generate_dependency_map(self) -> dict[str, Any]:
        """Generate dependency-map.json."""
        from src.verification.intelligence.dependency_engine import DependencyEngine

        engine = DependencyEngine()
        graph = engine.discover()
        data = graph.to_dict()

        path = self._write_report("dependency-map.json", data)
        return {
            "file": str(path),
            "edge_count": len(graph.edges),
            "capability_count": len(graph.capabilities),
            "generated_at": data["generated_at"],
        }

    def _generate_change_impact(self) -> dict[str, Any]:
        """Generate change-impact.json."""
        from src.verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()
        impact = engine.analyze([])
        data = impact.to_dict()

        path = self._write_report("change-impact.json", data)
        return {
            "file": str(path),
            "strategy": data["strategy"],
            "overall_risk": data["overall_risk"],
            "generated_at": data["generated_at"],
        }

    def _generate_verification_evidence(self) -> dict[str, Any]:
        """Generate verification-evidence.json."""
        from src.verification.intelligence.evidence_engine import EvidenceEngine

        engine = EvidenceEngine()
        summary = engine.generate_all()
        data = summary.to_dict()

        path = self._write_report("verification-evidence.json", data)
        return {
            "file": str(path),
            "total_capabilities": data["total_capabilities"],
            "fully_verified": data["fully_verified"],
            "partial": data["partial"],
            "missing": data["missing"],
            "generated_at": data["generated_at"],
        }

    def _generate_architectural_coverage(self) -> dict[str, Any]:
        """Generate architectural-coverage.json."""
        from src.verification.intelligence.coverage_engine import CoverageEngine

        engine = CoverageEngine()
        coverage = engine.generate_all()
        data = coverage.to_dict()

        path = self._write_report("architectural-coverage.json", data)
        return {
            "file": str(path),
            "summary": data["summary"],
            "generated_at": data["generated_at"],
        }

    def _generate_risk_map(self) -> dict[str, Any]:
        """Generate risk-map.json."""
        from src.verification.intelligence.risk_engine import RiskEngine

        engine = RiskEngine()
        risk_map = engine.classify_all()
        data = risk_map.to_dict()

        path = self._write_report("risk-map.json", data)
        return {
            "file": str(path),
            "entry_count": len(data["entries"]),
            "generated_at": data["generated_at"],
        }

    def _generate_verification_summary(
        self, all_reports: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate verification-summary.json combining all reports."""
        summary: dict[str, Any] = {
            "generated_at": datetime.now(UTC).isoformat(),
            "version": "1.0.0",
            "reports": {},
        }

        for report_name, report_data in all_reports.items():
            summary["reports"][report_name] = {
                k: v for k, v in report_data.items() if k != "file"
            }

        path = self._write_report("verification-summary.json", summary)
        return {
            "file": str(path),
            "report_count": len(all_reports),
            "generated_at": summary["generated_at"],
        }

    def generate_single_report(self, report_name: str) -> dict[str, Any] | None:
        """Generate a single report by name."""
        generators: dict[str, Callable[..., dict[str, Any]]] = {
            "dependency-map": self._generate_dependency_map,
            "change-impact": self._generate_change_impact,
            "verification-evidence": self._generate_verification_evidence,
            "architectural-coverage": self._generate_architectural_coverage,
            "risk-map": self._generate_risk_map,
            "verification-summary": self._generate_verification_summary,
        }

        generator = generators.get(report_name)
        if generator is None:
            return None

        return generator()


def generate_all_reports() -> dict[str, Any]:
    """Convenience function to generate all reports."""
    engine = ReportEngine()
    return engine.generate_all()


def generate_report(report_name: str) -> dict[str, Any] | None:
    """Convenience function to generate a single report."""
    engine = ReportEngine()
    return engine.generate_single_report(report_name)
