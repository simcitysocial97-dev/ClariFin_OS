"""Evidence Ingestion — Pipelines for ingesting evidence from CI artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class IngestConfig:
    """Configuration for evidence ingestion."""

    artifact_dirs: List[str] = field(
        default_factory=lambda: [
            "backend/tests/generated",
            "frontend/coverage",
            "runtime/generated",
        ]
    )
    output_dir: str = "runtime/generated/evidence"
    commit_sha: str = ""
    branch: str = ""


class EvidenceIngestionPipeline:
    """Pipeline for ingesting CI artifacts into structured evidence."""

    def __init__(self, config: IngestConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def discover_artifacts(self, workspace_root: Path) -> List[Path]:
        """Discover all relevant artifact files."""
        artifacts = []
        for artifact_dir in self.config.artifact_dirs:
            dir_path = workspace_root / artifact_dir
            if dir_path.exists():
                artifacts.extend(dir_path.rglob("*.json"))
                artifacts.extend(dir_path.rglob("*.xml"))
                artifacts.extend(dir_path.rglob("*.md"))
        return artifacts

    def ingest_coverage(self, artifacts: List[Path]) -> Dict[str, Any]:
        """Extract and normalize coverage data."""
        coverage_data = {
            "backend": None,
            "frontend": None,
            "combined": None,
        }

        for artifact in artifacts:
            if "coverage" in artifact.name.lower() and artifact.suffix == ".json":
                try:
                    data = json.loads(artifact.read_text())
                    if "backend" in str(artifact):
                        coverage_data["backend"] = self._normalize_coverage(
                            data, "backend"
                        )
                    elif "frontend" in str(artifact):
                        coverage_data["frontend"] = self._normalize_coverage(
                            data, "frontend"
                        )
                except Exception:
                    pass

        # Combine
        if coverage_data["backend"] or coverage_data["frontend"]:
            coverage_data["combined"] = self._combine_coverage(
                coverage_data["backend"], coverage_data["frontend"]
            )

        return coverage_data

    def _normalize_coverage(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize coverage data to standard format."""
        if "totals" in data:  # pytest-cov raw format
            totals = data["totals"]
            return {
                "source": source,
                "total_coverage": totals.get("percent_covered", 0),
                "lines_covered": totals.get("covered_lines", 0),
                "lines_total": totals.get("num_statements", 0),
                "files": data.get("files", {}),
            }
        elif "total_coverage" in data:  # Already normalized
            return {"source": source, **data}
        return {
            "source": source,
            "total_coverage": 0,
            "lines_covered": 0,
            "lines_total": 0,
        }

    def _combine_coverage(self, backend: Dict, frontend: Dict) -> Dict:
        """Combine backend and frontend coverage."""
        b_cov = backend.get("total_coverage", 0) if backend else 0
        f_cov = frontend.get("total_coverage", 0) if frontend else 0

        return {
            "source": "combined",
            "total_coverage": round((b_cov + f_cov) / 2, 2) if (b_cov or f_cov) else 0,
            "backend_coverage": b_cov,
            "frontend_coverage": f_cov,
        }

    def ingest_mutation(self, artifacts: List[Path]) -> Dict[str, Any]:
        """Extract and normalize mutation testing data."""
        mutation_data = {
            "score": 0.0,
            "killed": 0,
            "survived": 0,
            "timeout": 0,
            "error": 0,
            "skipped": 0,
        }

        for artifact in artifacts:
            if "mutation" in str(artifact).lower() and artifact.suffix == ".json":
                try:
                    data = json.loads(artifact.read_text())
                    if "mutation_score" in data:
                        mutation_data.update(
                            {
                                "score": data.get("mutation_score", 0),
                                "killed": data.get("killed", 0),
                                "survived": data.get("survived", 0),
                                "timeout": data.get("timeout", 0),
                                "error": data.get("error", 0),
                                "skipped": data.get("skipped", 0),
                            }
                        )
                except Exception:
                    pass

        return mutation_data

    def ingest_contract_tests(self, artifacts: List[Path]) -> Dict[str, Any]:
        """Extract contract test evidence."""
        contract_data = {
            "total_contracts": 0,
            "passed": 0,
            "failed": 0,
            "coverage": 0.0,
        }

        for artifact in artifacts:
            if "contract" in artifact.name.lower() and artifact.suffix == ".json":
                try:
                    data = json.loads(artifact.read_text())
                    if "contracts" in data:
                        contract_data["total_contracts"] = len(data["contracts"])
                    if "coverage" in data:
                        contract_data["coverage"] = data["coverage"]
                except Exception:
                    pass

        return contract_data

    def ingest_property_tests(self, artifacts: List[Path]) -> Dict[str, Any]:
        """Extract property-based testing evidence."""
        property_data = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "hypothesis_examples": 0,
        }

        for artifact in artifacts:
            if "property" in artifact.name.lower() and artifact.suffix == ".json":
                try:
                    data = json.loads(artifact.read_text())
                    property_data["total_tests"] = data.get("total", 0)
                    property_data["passed"] = data.get("passed", 0)
                    property_data["failed"] = data.get("failed", 0)
                except Exception:
                    pass

        return property_data

    def run(self, workspace_root: Path) -> Dict[str, Any]:
        """Run the full ingestion pipeline."""
        print(f"Discovering artifacts in {workspace_root}...")
        artifacts = self.discover_artifacts(workspace_root)
        print(f"Found {len(artifacts)} artifact files")

        print("Ingesting coverage...")
        coverage = self.ingest_coverage(artifacts)

        print("Ingesting mutation...")
        mutation = self.ingest_mutation(artifacts)

        print("Ingesting contract tests...")
        contracts = self.ingest_contract_tests(artifacts)

        print("Ingesting property tests...")
        property_tests = self.ingest_property_tests(artifacts)

        # Build verification evidence
        evidence = {
            "commit": self.config.commit_sha,
            "branch": self.config.branch,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "coverage": coverage.get("combined", coverage.get("backend", {})),
            "mutation": mutation,
            "contracts": contracts,
            "property_tests": property_tests,
            "artifacts": [str(a) for a in artifacts],
        }

        # Write output
        output_path = self.output_dir / "verification-evidence.json"
        output_path.write_text(json.dumps(evidence, indent=2))
        print(f"Evidence written to {output_path}")

        return evidence
