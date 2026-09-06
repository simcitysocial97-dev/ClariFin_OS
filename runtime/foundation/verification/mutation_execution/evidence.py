# runtime/foundation/verification/mutation_execution/evidence.py
#
# M9-C44.17 — Backend-Agnostic Evidence Layer.
#
# Translates canonical MutationResult into the VEA-5 evidence contract
# so downstream systems (Diagnostic Agent, Strengthening Pipeline,
# Certification, CI) consume only the canonical contract.
#
# No downstream component depends on mutmut-specific result parsing.

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.evidence_contract import (
    EvidenceArtifactRef,
    ExecutionAttempt,
    UnitExecutionRecord,
)
from runtime.foundation.verification.measurement_truth import (
    EvidenceClassification,
    FailureClassification,
    MeasurementCompletionStatus,
    MeasurementKind,
    MeasurementTruthRecord,
    PopulationAccounting,
    classify_completion,
    set_evidence_fingerprint,
)
from runtime.foundation.verification.mutation_execution.domain_model import (
    MutationCampaign,
    MutationResult,
)

SCHEMA_VERSION = "m9-c44-mutation-evidence/v1"


def result_to_measurement_truth(
    campaign: MutationCampaign,
    result: MutationResult,
    *,
    command: str,
    requested_scope: str,
    actual_scope: str,
    artifact_paths: list[str],
    completion_status: str = MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value,
    failure_classification: str = FailureClassification.NONE.value,
    error: str | None = None,
    note: str = "",
) -> MeasurementTruthRecord:
    """Translate a canonical MutationResult into a MeasurementTruthRecord
    compatible with the M9-C47 measurement truth contract."""
    record = MeasurementTruthRecord(
        run_id=campaign.campaign_id,
        measurement_kind=MeasurementKind.MUTATION.value,
        repository_sha=campaign.repository_revision,
        tree_sha="",
        working_tree_fingerprint="",
        configuration_fingerprint=campaign.configuration_fingerprint,
        toolchain_fingerprint=f"{campaign.mutation_backend}:{campaign.backend_version}",
        environment_fingerprint=campaign.environment_fingerprint,
        command=command,
        requested_scope=requested_scope,
        actual_scope=actual_scope,
        population=PopulationAccounting(
            requested_generated=result.total_candidates,
            generated=result.total_candidates,
            killed=result.killed,
            survived=result.survived,
            timeout=result.timeout,
            no_tests=result.no_tests,
            suspicious=0,
            not_checked=result.unknown + result.not_executed,
        ),
        mutation_score=result.score,
        execution_status="PASS" if result.infrastructure_failures == 0 else "FAIL",
        completion_status=completion_status,
        failure_classification=failure_classification,
        duration_seconds=0.0,
        toolchain_versions={
            "python": "",
            "pytest": "",
            campaign.mutation_backend: campaign.backend_version,
        },
        artifact_paths=artifact_paths,
        evidence_classification=EvidenceClassification.AUTHORITATIVE.value,
        mode="full" if campaign.scope == "full (all engines)" else "target",
        target=None if campaign.scope == "full (all engines)" else campaign.scope,
        error=error,
        note=note,
    )
    set_evidence_fingerprint(record)
    record.completion_status = classify_completion(record=record)
    record.consumable_by_certification = (
        record.completion_status
        == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
        and record.evidence_classification == EvidenceClassification.AUTHORITATIVE.value
    )
    return record


def result_to_evidence_artifact(
    campaign: MutationCampaign,
    result: MutationResult,
    workspace: Path,
) -> dict[str, Any]:
    """Produce a VEA-5 compatible evidence artifact from a MutationResult."""
    artifacts = []

    # Reference the campaign manifest.
    artifacts.append(
        EvidenceArtifactRef(
            kind="mutation-campaign-manifest",
            ref=str(workspace / "manifest.json"),
        )
    )

    # Reference aggregated results.
    evidence_path = workspace / "evidence" / "mutation-result.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result.to_dict(), indent=2) + "\n")
    artifacts.append(
        EvidenceArtifactRef(
            kind="mutation-result",
            ref=str(
                evidence_path.relative_to(
                    workspace.root if hasattr(workspace, "root") else workspace
                )
            ),
        )
    )

    # Reference per-execution logs.
    exec_dir = workspace / "executions"
    if exec_dir.exists():
        for ef in sorted(exec_dir.glob("*.json"))[:100]:  # cap at 100 refs
            artifacts.append(
                EvidenceArtifactRef(
                    kind="mutation-execution",
                    ref=str(ef),
                )
            )

    # Build unit execution records for each candidate.
    units = []
    for i, art in enumerate(artifacts[:50]):  # limit units
        units.append(
            UnitExecutionRecord(
                unit_id=f"mutation-{i}",
                provenance={
                    "campaign_id": campaign.campaign_id,
                    "scope": campaign.scope,
                    "backend": campaign.mutation_backend,
                },
                attempts=(
                    ExecutionAttempt(
                        attempt_index=0,
                        command=f"mutmut run --target {campaign.scope}",
                        started_at=campaign.creation_timestamp,
                        ended_at=datetime.now(UTC).isoformat(),
                        duration_seconds=0.0,
                        exit_code=0 if result.reconcile() else 1,
                        status="pass" if result.reconcile() else "fail",
                        artifacts=(art,),
                    ),
                ),
            )
        )

    return {
        "schema": SCHEMA_VERSION,
        "campaign_id": campaign.campaign_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "result": result.to_dict(),
        "measurement_truth": result_to_measurement_truth(
            campaign,
            result,
            command=f"verify.py mutation --target {campaign.scope}",
            requested_scope=campaign.scope,
            actual_scope=campaign.scope,
            artifact_paths=[str(evidence_path)],
        ).to_dict(),
        "evidence_artifacts": [a.to_dict() for a in artifacts],
        "units": [u.to_dict() for u in units],
    }


def normalize_backend_results(
    raw_results: dict[str, Any],
    backend_name: str,
) -> MutationResult:
    """Normalize raw backend results into a canonical MutationResult.

    Handles mutmut-specific formats, Cosmic Ray formats, etc.
    """
    if backend_name == "mutmut":
        return _normalize_mutmut(raw_results)
    raise ValueError(f"Unknown backend normalization: {backend_name}")


def _normalize_mutmut(raw: dict[str, Any]) -> MutationResult:
    """Normalize mutmut CLI output format to canonical MutationResult."""
    killed = int(raw.get("killed", 0))
    survived = int(raw.get("survived", 0))
    no_tests = int(raw.get("no_tests", 0))
    timeout = int(raw.get("timeout", 0))
    suspicious = int(raw.get("suspicious", 0))
    not_checked = int(raw.get("not_checked", 0))

    return MutationResult(
        campaign_id=raw.get("run_id", "unknown"),
        total_candidates=killed
        + survived
        + no_tests
        + timeout
        + suspicious
        + not_checked,
        killed=killed,
        survived=survived,
        no_tests=no_tests,
        timeout=timeout,
        execution_error=suspicious + not_checked,  # suspicious/not-checked -> error
    )


def merge_shard_results(
    shards: list[tuple[MutationCampaign, MutationResult]],
) -> MutationResult:
    """Merge results from multiple shards into one authoritative result."""
    merged = MutationResult(
        campaign_id=shards[0][0].campaign_id if shards else "merged"
    )
    for _camp, result in shards:
        merged.total_candidates += result.total_candidates
        merged.killed += result.killed
        merged.survived += result.survived
        merged.equivalent += result.equivalent
        merged.no_tests += result.no_tests
        merged.timeout += result.timeout
        merged.execution_error += result.execution_error
        merged.invalid_mutant += result.invalid_mutant
        merged.not_executed += result.not_executed
        merged.cancelled += result.cancelled
        merged.unknown += result.unknown
        merged.total_executions += result.total_executions
        merged.successful_executions += result.successful_executions
        merged.infrastructure_failures += result.infrastructure_failures
        merged.timeouts += result.timeouts
        merged.retries_total += result.retries_total
    return merged


__all__ = [
    "result_to_measurement_truth",
    "result_to_evidence_artifact",
    "normalize_backend_results",
    "merge_shard_results",
    "SCHEMA_VERSION",
]
