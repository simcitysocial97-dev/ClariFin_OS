"""Evidence Collectors — Base class and implementations for collecting verification evidence."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True, slots=True)
class EvidenceArtifact:
    """A single piece of evidence collected from the workspace."""

    artifact_type: (
        str  # e.g., "coverage", "mutation", "property-tests", "contract-tests"
    )
    name: str
    path: str
    metadata: Dict[str, Any]


class EvidenceCollector(ABC):
    """Abstract base class for evidence collectors.

    Each collector is responsible for finding, parsing, and normalizing
    a specific type of verification evidence artifact.
    """

    name: str = "base"
    artifact_type: str = "base"

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    @abstractmethod
    def collect(self) -> List[EvidenceArtifact]:
        """Collect evidence artifacts from the workspace.

        Returns:
            List of EvidenceArtifact objects representing collected evidence.
        """
        pass

    def _read_json(self, path: Path) -> Dict[str, Any] | None:
        """Safely read a JSON file."""
        try:
            if path.exists():
                return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
        return None


class CoverageCollector(EvidenceCollector):
    """Collects coverage evidence from backend test runs."""

    name = "coverage"
    artifact_type = "coverage"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        # Check backend coverage files
        backend_coverage = self.workspace_root / "backend" / "tests" / "generated"
        if backend_coverage.exists():
            # coverage.json
            coverage_json = backend_coverage / "coverage.json"
            if coverage_json.exists():
                data = self._read_json(coverage_json)
                if data:
                    artifacts.append(
                        EvidenceArtifact(
                            artifact_type=self.artifact_type,
                            name="backend-coverage",
                            path=str(coverage_json.relative_to(self.workspace_root)),
                            metadata={
                                "percentage": data.get(
                                    "total_coverage", data.get("coverage", 0)
                                ),
                                "covered_lines": data.get("covered_lines", 0),
                                "total_lines": data.get("total_lines", 0),
                                "gaps": data.get("gaps", []),
                                "source": "backend",
                            },
                        )
                    )

            # raw-coverage.json (pytest-cov format)
            raw_cov = backend_coverage / "raw-coverage.json"
            if raw_cov.exists():
                data = self._read_json(raw_cov)
                if data and "totals" in data:
                    totals = data["totals"]
                    artifacts.append(
                        EvidenceArtifact(
                            artifact_type=self.artifact_type,
                            name="backend-coverage-raw",
                            path=str(raw_cov.relative_to(self.workspace_root)),
                            metadata={
                                "percentage": totals.get("percent_covered", 0),
                                "covered_lines": totals.get("covered_lines", 0),
                                "total_lines": totals.get("num_statements", 0),
                                "gaps": [],
                                "source": "backend",
                            },
                        )
                    )

        return artifacts


class MutationCollector(EvidenceCollector):
    """Collects mutation testing evidence."""

    name = "mutation"
    artifact_type = "mutation"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        mutation_dir = (
            self.workspace_root / "backend" / "tests" / "generated" / "mutation"
        )
        if mutation_dir.exists():
            # mutation-summary.json
            summary = mutation_dir / "mutation-summary.json"
            if summary.exists():
                data = self._read_json(summary)
                if data:
                    artifacts.append(
                        EvidenceArtifact(
                            artifact_type=self.artifact_type,
                            name="mutation-summary",
                            path=str(summary.relative_to(self.workspace_root)),
                            metadata={
                                "score": data.get("mutation_score", 0),
                                "killed": data.get("killed", 0),
                                "survived": data.get("survived", 0),
                                "timeout": data.get("timeout", 0),
                                "error": data.get("error", 0),
                                "skipped": data.get("skipped", 0),
                                "survivor_details": data.get("survivors", []),
                                "source": "backend",
                            },
                        )
                    )

            # mutation-report.md for survivors
            if (mutation_dir / "mutation-report.md").exists():
                # Could parse for more details
                pass

        return artifacts


class PropertyTestCollector(EvidenceCollector):
    """Collects property-based testing evidence."""

    name = "property-tests"
    artifact_type = "property-tests"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        # Check for property test results
        property_dir = self.workspace_root / "backend" / "tests" / "generated"
        if property_dir.exists():
            # hypothesis results
            for hyp_file in property_dir.glob("**/hypothesis-*.json"):
                data = self._read_json(hyp_file)
                if data:
                    artifacts.append(
                        EvidenceArtifact(
                            artifact_type=self.artifact_type,
                            name=f"property-{hyp_file.stem}",
                            path=str(hyp_file.relative_to(self.workspace_root)),
                            metadata=data,
                        )
                    )

        return artifacts


class ContractTestCollector(EvidenceCollector):
    """Collects contract testing evidence."""

    name = "contract-tests"
    artifact_type = "contract-tests"

    def collect(self) -> List[EvidenceArtifact]:
        artifacts = []

        # Check backend contract tests
        contract_dir = self.workspace_root / "backend" / "tests" / "generated"
        if contract_dir.exists():
            contract_registry = contract_dir / "contract-registry.json"
            if contract_registry.exists():
                data = self._read_json(contract_registry)
                if data:
                    artifacts.append(
                        EvidenceArtifact(
                            artifact_type=self.artifact_type,
                            name="contract-registry",
                            path=str(
                                contract_registry.relative_to(self.workspace_root)
                            ),
                            metadata=data,
                        )
                    )

            contract_coverage = contract_dir / "contract-coverage.json"
            if contract_coverage.exists():
                data = self._read_json(contract_coverage)
                if data:
                    artifacts.append(
                        EvidenceArtifact(
                            artifact_type=self.artifact_type,
                            name="contract-coverage",
                            path=str(
                                contract_coverage.relative_to(self.workspace_root)
                            ),
                            metadata=data,
                        )
                    )

        return artifacts
