"""Evidence Runtime API — Main entry point for evidence collection and verification."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.system.evidence.collectors import (
    CoverageCollector,
    MutationCollector,
    PropertyTestCollector,
    ContractTestCollector,
)
from runtime.system.evidence.models import (
    CoverageEvidence,
    MutationEvidence,
    VerificationEvidence,
    EvidenceCollectionResult,
)

# All available collectors
COLLECTORS = [
    CoverageCollector,
    MutationCollector,
    PropertyTestCollector,
    ContractTestCollector,
]


def collect_all_evidence(workspace_root: Path) -> EvidenceCollectionResult:
    """Collect all evidence from the workspace using all registered collectors.

    Args:
        workspace_root: Root directory of the workspace/repository.

    Returns:
        EvidenceCollectionResult with all collected artifacts and collector metadata.
    """
    artifacts = []
    collectors_metadata = {}

    for collector_cls in COLLECTORS:
        collector = collector_cls(workspace_root)
        collected = collector.collect_artifacts()

        artifact_dicts = [asdict(a) for a in collected]
        artifacts.extend(artifact_dicts)

        collectors_metadata[collector.artifact_type] = {
            "name": collector.name,
            "artifacts_found": len(collected),
        }

    return EvidenceCollectionResult(
        workspace_root=str(workspace_root),
        collected_at=datetime.utcnow().isoformat() + "Z",
        artifacts=artifacts,
        collectors=collectors_metadata,
    )


def extract_coverage_evidence(
    artifacts: List[Dict[str, Any]],
) -> Optional[CoverageEvidence]:
    """Extract CoverageEvidence from collected artifacts."""
    for artifact in artifacts:
        if artifact.get("artifact_type") == "coverage":
            metadata = artifact.get("metadata", {})
            return CoverageEvidence(
                percentage=metadata.get("percentage", 0.0),
                covered_lines=metadata.get("covered_lines", 0),
                total_lines=metadata.get("total_lines", 0),
                gaps=metadata.get("gaps", []),
                source=metadata.get("source", "backend"),
                artifact_path=artifact.get("path", ""),
            )
    return None


def extract_mutation_evidence(
    artifacts: List[Dict[str, Any]],
) -> Optional[MutationEvidence]:
    """Extract MutationEvidence from collected artifacts."""
    for artifact in artifacts:
        if artifact.get("artifact_type") == "mutation":
            metadata = artifact.get("metadata", {})
            if "score" in metadata:
                return MutationEvidence(
                    score=metadata.get("score", 0.0),
                    killed=metadata.get("killed", 0),
                    survived=metadata.get("survived", 0),
                    timeout=metadata.get("timeout", 0),
                    error=metadata.get("error", 0),
                    skipped=metadata.get("skipped", 0),
                    survivor_details=metadata.get("survivor_details", []),
                    source=metadata.get("source", "backend"),
                    artifact_path=artifact.get("path", ""),
                )
    return None


def build_verification_evidence(
    commit_sha: str,
    branch: str,
    artifacts: List[Dict[str, Any]],
    property_tests: Dict[str, Any] | None = None,
    contract_tests: Dict[str, Any] | None = None,
    status: str = "partial",
) -> VerificationEvidence:
    """Build a VerificationEvidence object from collected artifacts.

    Args:
        commit_sha: Git commit SHA.
        branch: Git branch name.
        artifacts: List of artifact dictionaries from collect_all_evidence.
        property_tests: Optional property test results.
        contract_tests: Optional contract test results.
        status: Overall verification status ("pass", "fail", "partial").

    Returns:
        VerificationEvidence object.
    """
    coverage = extract_coverage_evidence(artifacts)
    mutation = extract_mutation_evidence(artifacts)

    # Determine overall status based on evidence
    if status == "partial":
        if coverage and coverage.percentage >= 80.0:
            if mutation and mutation.score >= 80.0:
                status = "pass"
            else:
                status = "partial"
        else:
            status = "fail"

    return VerificationEvidence(
        commit_sha=commit_sha,
        branch=branch,
        timestamp=datetime.utcnow().isoformat() + "Z",
        status=status,
        coverage=coverage,
        mutation=mutation,
        property_tests=property_tests or {},
        contract_tests=contract_tests or {},
        artifacts=artifacts,
    )


def write_verification_summary(
    evidence: VerificationEvidence,
    output_path: Path,
) -> None:
    """Write verification evidence to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(evidence.to_json())


def run_verification_pipeline(
    workspace_root: Path,
    commit_sha: str,
    branch: str,
    output_path: Path,
) -> VerificationEvidence:
    """Run the complete verification evidence pipeline.

    Args:
        workspace_root: Root of the workspace to collect evidence from.
        commit_sha: Git commit SHA.
        branch: Git branch name.
        output_path: Path to write the verification summary JSON.

    Returns:
        The built VerificationEvidence object.
    """
    # Collect all evidence
    collection_result = collect_all_evidence(workspace_root)

    # Build verification evidence
    evidence = build_verification_evidence(
        commit_sha=commit_sha,
        branch=branch,
        artifacts=collection_result.artifacts,
    )

    # Write output
    write_verification_summary(evidence, output_path)

    return evidence
