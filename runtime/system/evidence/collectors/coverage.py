"""Coverage Evidence Collector."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

from .base import EvidenceCollector, EvidenceArtifact


class CoverageCollector(EvidenceCollector):
    """Collects coverage evidence from coverage.json and coverage.xml files."""

    @property
    def artifact_type(self) -> str:
        return "coverage"

    @property
    def name(self) -> str:
        return "Coverage Report"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        # Primary coverage.json from backend
        coverage_json = self.workspace_root / "backend" / "tests" / "generated" / "coverage.json"
        if coverage_json.exists():
            data = self._read_json(coverage_json)
            if data:
                total = data.get("totals", {})
                covered = total.get("covered_lines", 0)
                total_lines = total.get("num_statements", 0)
                percentage = total.get("percent_covered", 0.0)

                artifacts.append(
                    self._artifact(
                        name="Backend Coverage",
                        path=coverage_json,
                        metadata={
                            "covered_lines": covered,
                            "total_lines": total_lines,
                            "percentage": percentage,
                            "files": data.get("files", {}),
                        },
                    )
                )

        # Check for coverage.xml (cobertura format)
        coverage_xml = self.workspace_root / "backend" / "tests" / "generated" / "coverage.xml"
        if coverage_xml.exists():
            artifacts.append(
                self._artifact(
                    name="Backend Coverage XML",
                    path=coverage_xml,
                    metadata={"format": "cobertura"},
                )
            )

        # Frontend coverage if exists
        frontend_coverage = self.workspace_root / "frontend" / "coverage" / "coverage-summary.json"
        if frontend_coverage.exists():
            data = self._read_json(frontend_coverage)
            if data and "total" in data:
                total = data["total"]
                artifacts.append(
                    self._artifact(
                        name="Frontend Coverage",
                        path=frontend_coverage,
                        metadata={
                            "covered_lines": total.get("lines", {}).get("covered", 0),
                            "total_lines": total.get("lines", {}).get("total", 0),
                            "percentage": total.get("lines", {}).get("pct", 0.0),
                        },
                    )
                )

        return artifacts