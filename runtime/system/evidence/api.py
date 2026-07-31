"""Evidence Runtime API — Main entry point for evidence collection and aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.system.evidence.collectors.base import EvidenceArtifact, EvidenceCollector
from runtime.system.evidence.collectors.coverage import CoverageCollector
from runtime.system.evidence.collectors.mutation import MutationCollector
from runtime.system.evidence.collectors.property_tests import PropertyTestCollector
from runtime.system.evidence.collectors.contract_tests import ContractTestCollector


@dataclass
class CoverageEvidence:
    """Coverage evidence model."""

    percentage: float
    covered_lines: int
    total_lines: int
    gaps: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_artifacts(cls, artifacts: List[EvidenceArtifact]) -> "CoverageEvidence":
        """Build coverage evidence from collected artifacts."""
        backend_coverage = None
        frontend_coverage = None

        for artifact in artifacts:
            if artifact.artifact_type == "coverage":
                if artifact.metadata.get("source") == "backend":
                    backend_coverage = artifact.metadata
                elif artifact.metadata.get("source") == "frontend":
                    frontend_coverage = artifact.metadata

        # Combine or use backend as primary
        primary = backend_coverage or frontend_coverage or {}

        return cls(
            percentage=primary.get("total_coverage", 0.0),
            covered_lines=primary.get("lines_covered", 0),
            total_lines=primary.get("lines_total", 0),
        )


@dataclass
class MutationEvidence:
    """Mutation testing evidence model."""

    score: float
    killed: int
    survived: int
    timeout: int = 0
    error: int = 0
    skipped: int = 0

    @classmethod
    def from_artifacts(cls, artifacts: List[EvidenceArtifact]) -> "MutationEvidence":
        """Build mutation evidence from collected artifacts."""
        for artifact in artifacts:
            if artifact.artifact_type == "mutation":
                return cls(
                    score=artifact.metadata.get("mutation_score", 0.0),
                    killed=artifact.metadata.get("killed", 0),
                    survived=artifact.metadata.get("survived", 0),
                    timeout=artifact.metadata.get("timeout", 0),
                    error=artifact.metadata.get("error", 0),
                    skipped=artifact.metadata.get("skipped", 0),
                )
        return cls(score=0.0, killed=0, survived=0)


@dataclass
class VerificationEvidence:
    """Complete verification evidence for a commit."""

    commit_sha: str
    branch: str
    timestamp: str
    status: str  # pass, fail, partial
    coverage: Optional[CoverageEvidence] = None
    mutation: Optional[MutationEvidence] = None
    artifacts: List[EvidenceArtifact] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "commit": self.commit_sha,
            "branch": self.branch,
            "timestamp": self.timestamp,
            "status": self.status,
            "coverage": self.coverage.__dict__ if self.coverage else None,
            "mutation": self.mutation.__dict__ if self.mutation else None,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)


@dataclass
class CollectionResult:
    """Result of evidence collection."""

    artifacts: List[EvidenceArtifact]
    collector_status: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifacts": [a.to_dict() for a in self.artifacts],
            "collector_status": self.collector_status,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2)


COLLECTORS: List[type[EvidenceCollector]] = [
    CoverageCollector,
    MutationCollector,
    PropertyTestCollector,
    ContractTestCollector,
]


def collect_all_evidence(workspace_root: Path) -> CollectionResult:
    """Run all collectors and aggregate evidence artifacts."""
    all_artifacts = []
    collector_results = {}

    for collector_cls in COLLECTORS:
        collector = collector_cls()
        if collector.validate_inputs(workspace_root):
            artifacts = collector.collect(workspace_root)
            all_artifacts.extend(artifacts)
            collector_results[collector.artifact_type] = {
                "status": "success",
                "artifacts_collected": len(artifacts),
            }
        else:
            collector_results[collector.artifact_type] = {
                "status": "skipped",
                "reason": "required artifacts not found",
            }

    return CollectionResult(
        artifacts=all_artifacts,
        collector_status=collector_results,
    )


def build_verification_evidence(
    commit_sha: str,
    branch: str,
    artifacts: List[EvidenceArtifact],
    status: str = "partial",
) -> VerificationEvidence:
    """Build complete verification evidence from collected artifacts."""
    coverage = CoverageEvidence.from_artifacts(artifacts)
    mutation = MutationEvidence.from_artifacts(artifacts)

    return VerificationEvidence(
        commit_sha=commit_sha,
        branch=branch,
        timestamp=datetime.utcnow().isoformat() + "Z",
        status=status,
        coverage=coverage,
        mutation=mutation,
        artifacts=artifacts,
    )


def write_verification_summary(evidence: VerificationEvidence, output_path: Path) -> None:
    """Write verification summary JSON to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(evidence.to_json())