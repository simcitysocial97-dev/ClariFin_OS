# runtime/foundation/verification/mutation_result_unified.py
#
# M9-C48 A3 — Unified MutationResult projection (GAP-003).
#
# Two `MutationResult` types historically co-existed:
#   * runtime.foundation.verification.mutation_contract.MutationResult
#     — canonical 6-bucket public serialization (KILLED / SURVIVED /
#       NO_TESTS / TIMEOUT / SUSPICIOUS / NOT_CHECKED), three-gate
#       classification, evidence spine (run_id, repository_sha, …).
#       This is what every evidence file ships.
#   * runtime.foundation.verification.mutation_execution.domain_model.MutationResult
#     — orchestrator internal aggregation (10 buckets including EQUIVALENT,
#       EXECUTION_ERROR, INVALID_MUTANT, CANCELLED, NOT_EXECUTED, UNKNOWN).
#
# This module does NOT collapse them into one dataclass (each has a
# legitimate, distinct purpose) but it DOES establish a single semantic
# projection so that:
#
#   1. Canonical evidence serialization remains mutation_contract.MutationResult.
#   2. Any future orchestrator output can be projected INTO it without loss
#      of the rich failure taxonomy (the rich fields are recorded as
#      auxiliary fields on the canonical result, see `orchestrator_provenance`).
#   3. All certification logic consumes the same semantic model.
#
# This module is pure logic — no I/O. Importable by tests and by the
# mutation_runner (for projecting orchestrator output if/when wired).

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Status buckets from the orchestrator (richer) that map into the canonical
# 6-bucket vocabulary. Anything outside this map is recorded as orchestrator
# auxiliary provenance.
_ORCH_TO_CANON: dict[str, str] = {
    "killed": "killed",
    "survived": "survived",
    "equivalent": "survived",          # equivalent → behaves as survived for scoring
    "no_tests": "no_tests",
    "timeout": "timeout",
    "execution_error": "not_checked",  # infra failure → not_checked (excluded from score)
    "invalid_mutant": "suspicious",
    "not_executed": "not_checked",
    "cancelled": "not_checked",
    "unknown": "not_checked",
}


@dataclass(frozen=True, slots=True)
class UnifiedMutationProjection:
    """A canonical-evidence view derived from a rich orchestrator result.

    `canonical` is the mutation_contract.MutationResult that downstream
    evidence should record. `orchestrator_provenance` carries the rich
    10-bucket taxonomy as auxiliary evidence so the orchestrator's extra
    classification is not lost when collapsing to the canonical schema.
    """

    canonical: Any  # mutation_contract.MutationResult
    orchestrator_provenance: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical": self.canonical.to_dict(),
            "orchestrator_provenance": self.orchestrator_provenance,
            "projection": "m9-c48/mutation-result-unified@1",
        }


def project_orchestrator_to_canonical(
    *,
    orchestrator_result: Any,
    run_id: str,
    repository_sha: str,
    tree_sha: str,
    python_version: str,
    pytest_version: str,
    mutmut_version: str,
    config_hash: str,
    mode: str = "full",
    target: str | None = None,
    duration_seconds: int = 0,
    mutmut_rc: int | None = None,
    error: str | None = None,
    note: str = "",
    selected_test_scope: str = "",
    source_scope: str = "",
    selection_method: str = "",
    execution_path: str = "VERIFICATION_CONTROL_PLANE",
    threshold_percent: int = 80,
) -> UnifiedMutationProjection:
    """Project a mutation_execution.domain_model.MutationResult into a canonical
    mutation_contract.MutationResult, retaining the rich taxonomy in
    orchestrator_provenance.

    Pure function; no I/O. The caller may then persist `projection.canonical`
    as evidence.
    """
    # Local import to avoid a hard dependency at module import time (the
    # contract module is the canonical one and may already be loaded).
    from runtime.foundation.verification.mutation_contract import MutationResult

    rich = {
        "killed": int(getattr(orchestrator_result, "killed", 0)),
        "survived": int(getattr(orchestrator_result, "survived", 0)),
        "equivalent": int(getattr(orchestrator_result, "equivalent", 0)),
        "no_tests": int(getattr(orchestrator_result, "no_tests", 0)),
        "timeout": int(getattr(orchestrator_result, "timeout", 0)),
        "execution_error": int(getattr(orchestrator_result, "execution_error", 0)),
        "invalid_mutant": int(getattr(orchestrator_result, "invalid_mutant", 0)),
        "not_executed": int(getattr(orchestrator_result, "not_executed", 0)),
        "cancelled": int(getattr(orchestrator_result, "cancelled", 0)),
        "unknown": int(getattr(orchestrator_result, "unknown", 0)),
    }
    # Collapse into the canonical 6-bucket view.
    buckets = {
        "killed": 0,
        "survived": 0,
        "no_tests": 0,
        "timeout": 0,
        "suspicious": 0,
        "not_checked": 0,
    }
    for rich_name, count in rich.items():
        canon = _ORCH_TO_CANON[rich_name]
        buckets[canon] += count

    # Determine gate states.
    infra_failed = rich["execution_error"] > 0 and sum(
        v for k, v in rich.items() if k != "execution_error"
    ) == 0
    execution_status = "INFRASTRUCTURE_FAILURE" if infra_failed else "PASS"
    evidence_complete = True  # orchestrator always records per-mutant artifacts
    # Score (canonical scoring only includes scored statuses).
    denom = buckets["killed"] + buckets["survived"] + buckets["timeout"]
    score = round(buckets["killed"] * 100.0 / denom, 2) if denom > 0 else None

    if infra_failed:
        classification_status = "FAIL"
    else:
        classification_status = "PASS"

    canonical = MutationResult(
        run_id=run_id,
        repository_sha=repository_sha,
        tree_sha=tree_sha,
        python_version=python_version,
        pytest_version=pytest_version,
        mutmut_version=mutmut_version,
        config_hash=config_hash,
        killed=buckets["killed"],
        survived=buckets["survived"],
        no_tests=buckets["no_tests"],
        timeout=buckets["timeout"],
        suspicious=buckets["suspicious"],
        not_checked=buckets["not_checked"],
        threshold_percent=threshold_percent,
        execution_status=execution_status,
        classification_status=classification_status,
        evidence_complete=evidence_complete,
        mutation_score=score,
        mode=mode,
        target=target,
        duration_seconds=duration_seconds,
        mutmut_rc=mutmut_rc,
        error=error,
        note=note,
        selected_test_scope=selected_test_scope,
        source_scope=source_scope,
        selection_method=selection_method,
        execution_path=execution_path,
    )
    return UnifiedMutationProjection(
        canonical=canonical, orchestrator_provenance=rich
    )


__all__ = [
    "UnifiedMutationProjection",
    "project_orchestrator_to_canonical",
    "_ORCH_TO_CANON",
]
