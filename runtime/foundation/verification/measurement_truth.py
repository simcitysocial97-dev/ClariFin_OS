# runtime/foundation/verification/measurement_truth.py
#
# M9-C47 — Measurement Truth contract.
#
# ONE authoritative, observable, durable and reproducible measurement path for
# coverage and mutation evidence. This module is the single machine-readable
# contract that answers the C47 completion question:
#
#     "Was this coverage/mutation result actually executed, over exactly what
#      scope, against exactly what repository/configuration/toolchain, did it
#      complete, where is the durable evidence, can it be reused, and is it
#      authoritative enough for certification?"
#
# Design invariants (M9-C47 governing constraints):
#  * Extends the existing C42.x evidence architecture — does NOT create a
#    parallel verification/evidence system.
#  * Coverage and mutation are explicitly SEPARATE measurements
#    (`measurement_kind`), sharing one record shape.
#  * A partial/timeout/corrupt/derived campaign can NEVER be labelled
#    `AUTHORITATIVE_COMPLETE` and can NEVER be consumed by certification.
#  * Authoritative vs derived is machine-readable and immutable.
#  * Reuses native environment fingerprints (env.py), not recreated ones.
#
# Pure logic + explicit filesystem reads only — no subprocess, importable by
# unit tests.

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Completion status vocabulary (Phase 5 — local/CI reconciliation).
# ---------------------------------------------------------------------------


class MeasurementCompletionStatus(str, Enum):
    """Exactly one authoritative completion classification per measurement.

    Only ``AUTHORITATIVE_COMPLETE`` may be consumed by certification. Every
    other state is a bounded, machine-readable reason that the measurement
    cannot certify.
    """

    AUTHORITATIVE_COMPLETE = "AUTHORITATIVE_COMPLETE"
    PARTIAL = "PARTIAL"
    TIMEOUT = "TIMEOUT"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    EVIDENCE_FAILURE = "EVIDENCE_FAILURE"
    INVALID_SCOPE = "INVALID_SCOPE"
    DERIVED_ONLY = "DERIVED_ONLY"
    UNKNOWN = "UNKNOWN"


# States that certification may NOT consume.
_NON_CERTIFIABLE = {
    MeasurementCompletionStatus.PARTIAL,
    MeasurementCompletionStatus.TIMEOUT,
    MeasurementCompletionStatus.INFRASTRUCTURE_FAILURE,
    MeasurementCompletionStatus.EVIDENCE_FAILURE,
    MeasurementCompletionStatus.INVALID_SCOPE,
    MeasurementCompletionStatus.DERIVED_ONLY,
}


class EvidenceClassification(str, Enum):
    """Authoritative vs derived, machine-readable and immutable."""

    AUTHORITATIVE = "authoritative"
    DERIVED = "derived"


class MeasurementKind(str, Enum):
    """Coverage and mutation MUST remain separate measurements."""

    COVERAGE = "coverage"
    MUTATION = "mutation"


class FailureClassification(str, Enum):
    """Failure taxonomy consistent with the existing executor FailureKind."""

    NONE = "none"
    INFRASTRUCTURE = "infrastructure"
    EVIDENCE = "evidence"
    SCOPE = "scope"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"


# ---------------------------------------------------------------------------
# Population accounting.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PopulationAccounting:
    """Mutation population arithmetic (mutation measurement only).

    ``generated`` is the requested population; ``actually_scored`` is the number
    of mutants that were actually executed and decided (killed + survived +
    timeout). A partial campaign must have ``actually_processed < generated``
    and be classified ``PARTIAL``, never authoritative.
    """

    requested_generated: int = 0
    generated: int = 0
    killed: int = 0
    survived: int = 0
    timeout: int = 0
    no_tests: int = 0
    suspicious: int = 0
    not_checked: int = 0

    @property
    def actually_scored(self) -> int:
        return self.killed + self.survived + self.timeout

    @property
    def actually_processed(self) -> int:
        return (
            self.killed
            + self.survived
            + self.timeout
            + self.no_tests
            + self.suspicious
            + self.not_checked
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "requested_generated": self.requested_generated,
            "generated": self.generated,
            "killed": self.killed,
            "survived": self.survived,
            "timeout": self.timeout,
            "no_tests": self.no_tests,
            "suspicious": self.suspicious,
            "not_checked": self.not_checked,
            "actually_scored": self.actually_scored,
            "actually_processed": self.actually_processed,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PopulationAccounting:
        return cls(
            requested_generated=int(d.get("requested_generated", 0)),
            generated=int(d.get("generated", 0)),
            killed=int(d.get("killed", 0)),
            survived=int(d.get("survived", 0)),
            timeout=int(d.get("timeout", 0)),
            no_tests=int(d.get("no_tests", 0)),
            suspicious=int(d.get("suspicious", 0)),
            not_checked=int(d.get("not_checked", 0)),
        )


# ---------------------------------------------------------------------------
# The single measurement-truth record.
# ---------------------------------------------------------------------------


@dataclass
class CoverageResult:
    """Coverage-specific result fields (measurement_kind == coverage)."""

    lines_total: int = 0
    lines_covered: int = 0
    line_percent: float | None = None
    branches_total: int = 0
    branches_covered: int = 0
    branch_percent: float | None = None

    @property
    def coverage_percent(self) -> float | None:
        return self.line_percent

    def as_dict(self) -> dict[str, Any]:
        return {
            "lines_total": self.lines_total,
            "lines_covered": self.lines_covered,
            "line_percent": self.line_percent,
            "branches_total": self.branches_total,
            "branches_covered": self.branches_covered,
            "branch_percent": self.branch_percent,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CoverageResult:
        return cls(
            lines_total=int(d.get("lines_total", 0)),
            lines_covered=int(d.get("lines_covered", 0)),
            line_percent=d.get("line_percent"),
            branches_total=int(d.get("branches_total", 0)),
            branches_covered=int(d.get("branches_covered", 0)),
            branch_percent=d.get("branch_percent"),
        )


@dataclass
class MeasurementTruthRecord:
    """One canonical, durable, machine-readable measurement record.

    Captures every Phase-2 truth field for BOTH coverage and mutation, kept
    explicitly separate via ``measurement_kind`` while sharing one durable
    shape that local and CI can reconcile through the existing C42 evidence
    architecture.
    """

    # ── Identity ─────────────────────────────────────────────────────────
    run_id: str
    measurement_kind: str  # MeasurementKind
    repository_sha: str
    tree_sha: str
    working_tree_fingerprint: str = ""
    configuration_fingerprint: str = ""
    toolchain_fingerprint: str = ""
    environment_fingerprint: str = ""
    # ── Command & scope (requested vs actual) ────────────────────────────
    command: str = ""
    requested_scope: str = ""
    actual_scope: str = ""
    scope_invalid_reason: str = ""
    # ── Result ───────────────────────────────────────────────────────────
    population: PopulationAccounting = field(default_factory=PopulationAccounting)
    coverage: CoverageResult = field(default_factory=CoverageResult)
    mutation_score: float | None = None
    coverage_result_percent: float | None = None
    # ── Execution state ──────────────────────────────────────────────────
    execution_status: str = "UNKNOWN"  # PASS | FAIL | UNKNOWN
    completion_status: str = "UNKNOWN"  # MeasurementCompletionStatus
    failure_classification: str = "none"  # FailureClassification
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float = 0.0
    toolchain_versions: dict[str, str] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)
    # ── Classification (authoritative vs derived) ────────────────────────
    evidence_classification: str = EvidenceClassification.DERIVED.value
    evidence_fingerprint: str = ""
    consumable_by_certification: bool = False
    # ── Meta ─────────────────────────────────────────────────────────────
    mode: str = "full"  # full | smoke | target | coverage
    target: str | None = None
    error: str | None = None
    note: str = ""
    derived_from: list[str] = field(default_factory=list)
    schema: str = "m9-c47-measurement-truth/v1"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # ── Native mutmut reconstruction reuse ───────────────────────────────
    # When measurement_kind == mutation and native mutmut meta files / results
    # were durable-preserved, reference the durable artifact (i.e. the survivor
    # intel / survivors catalog) so individual-mutant investigation does NOT
    # depend on temporary folders.
    durable_survivor_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "measurement_kind": self.measurement_kind,
            "repository_sha": self.repository_sha,
            "tree_sha": self.tree_sha,
            "working_tree_fingerprint": self.working_tree_fingerprint,
            "configuration_fingerprint": self.configuration_fingerprint,
            "toolchain_fingerprint": self.toolchain_fingerprint,
            "environment_fingerprint": self.environment_fingerprint,
            "command": self.command,
            "requested_scope": self.requested_scope,
            "actual_scope": self.actual_scope,
            "scope_invalid_reason": self.scope_invalid_reason,
            "population": self.population.as_dict(),
            "coverage": self.coverage.as_dict(),
            "mutation_score": self.mutation_score,
            "coverage_result_percent": self.coverage_result_percent,
            "execution_status": self.execution_status,
            "completion_status": self.completion_status,
            "failure_classification": self.failure_classification,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "toolchain_versions": dict(self.toolchain_versions),
            "artifact_paths": list(self.artifact_paths),
            "evidence_classification": self.evidence_classification,
            "evidence_fingerprint": self.evidence_fingerprint,
            "consumable_by_certification": self.consumable_by_certification,
            "mode": self.mode,
            "target": self.target,
            "error": self.error,
            "note": self.note,
            "derived_from": list(self.derived_from),
            "durable_survivor_evidence": list(self.durable_survivor_evidence),
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MeasurementTruthRecord:
        return cls(
            run_id=d.get("run_id", ""),
            measurement_kind=d.get("measurement_kind", MeasurementKind.MUTATION.value),
            repository_sha=d.get("repository_sha", ""),
            tree_sha=d.get("tree_sha", ""),
            working_tree_fingerprint=d.get("working_tree_fingerprint", ""),
            configuration_fingerprint=d.get("configuration_fingerprint", ""),
            toolchain_fingerprint=d.get("toolchain_fingerprint", ""),
            environment_fingerprint=d.get("environment_fingerprint", ""),
            command=d.get("command", ""),
            requested_scope=d.get("requested_scope", ""),
            actual_scope=d.get("actual_scope", ""),
            scope_invalid_reason=d.get("scope_invalid_reason", ""),
            population=PopulationAccounting.from_dict(d.get("population", {})),
            coverage=CoverageResult.from_dict(d.get("coverage", {})),
            mutation_score=d.get("mutation_score"),
            coverage_result_percent=d.get("coverage_result_percent"),
            execution_status=d.get("execution_status", "UNKNOWN"),
            completion_status=d.get("completion_status", "UNKNOWN"),
            failure_classification=d.get("failure_classification", "none"),
            start_time=d.get("start_time"),
            end_time=d.get("end_time"),
            duration_seconds=float(d.get("duration_seconds", 0.0)),
            toolchain_versions=d.get("toolchain_versions", {}),
            artifact_paths=d.get("artifact_paths", []),
            evidence_classification=d.get(
                "evidence_classification", EvidenceClassification.DERIVED.value
            ),
            evidence_fingerprint=d.get("evidence_fingerprint", ""),
            consumable_by_certification=bool(
                d.get("consumable_by_certification", False)
            ),
            mode=d.get("mode", "full"),
            target=d.get("target"),
            error=d.get("error"),
            note=d.get("note", ""),
            derived_from=d.get("derived_from", []),
            durable_survivor_evidence=d.get("durable_survivor_evidence", []),
            generated_at=d.get("generated_at", ""),
        )


# ---------------------------------------------------------------------------
# Classification of completion & certification eligibility (pure logic).
# ---------------------------------------------------------------------------


def classify_completion(*, record: MeasurementTruthRecord) -> str:
    """Derive the single authoritative completion status for a raw run state.

    Pure decision table. Guarantees:
    * timeout  -> TIMEOUT
    * infra error / non-execution -> INFRASTRUCTURE_FAILURE
    * execution ran but evidence corrupt/incomplete -> EVIDENCE_FAILURE
    * requested scope != actual scope -> INVALID_SCOPE
    * partially processed population -> PARTIAL
    * derived evidence (reused/reconciled aggregates) -> DERIVED_ONLY
    * only otherwise -> AUTHORITATIVE_COMPLETE

    Partial/timeout/corrupt/derived NEVER produce AUTHORITATIVE_COMPLETE.
    """
    failure = record.failure_classification
    execution = record.execution_status

    # Timeout dominates over generic infra failure.
    if (
        failure == FailureClassification.TIMEOUT.value
        or record.completion_status == MeasurementCompletionStatus.TIMEOUT.value
    ):
        return MeasurementCompletionStatus.TIMEOUT.value

    # Scope mismatch is always INVALID_SCOPE.
    if record.scope_invalid_reason:
        return MeasurementCompletionStatus.INVALID_SCOPE.value

    # Explicit scope-unreachable on the raw record.
    if record.completion_status == MeasurementCompletionStatus.INVALID_SCOPE.value:
        return MeasurementCompletionStatus.INVALID_SCOPE.value

    # Execution did not complete cleanly.
    if (
        execution != "PASS"
        or failure == FailureClassification.INFRASTRUCTURE.value
        or failure == FailureClassification.INTERRUPTED.value
    ):
        return MeasurementCompletionStatus.INFRASTRUCTURE_FAILURE.value

    # Derived evidence can never be authoritative.
    if record.evidence_classification == EvidenceClassification.DERIVED.value:
        return MeasurementCompletionStatus.DERIVED_ONLY.value

    # Evidence corrupt / incomplete enforcement.
    if record.evidence_fingerprint == "" and record.population.actually_processed > 0:
        return MeasurementCompletionStatus.EVIDENCE_FAILURE.value

    # Partial population: requested generated vs actually processed.
    if (
        record.measurement_kind == MeasurementKind.MUTATION.value
        and record.population.requested_generated > 0
        and record.population.actually_processed < record.population.requested_generated
    ):
        return MeasurementCompletionStatus.PARTIAL.value

    # A mutation measurement must have processed a non-empty population that
    # satisfies the arithmetic invariant to be complete.
    if record.measurement_kind == MeasurementKind.MUTATION.value:
        accounting = record.population
        if accounting.actually_processed == 0:
            return MeasurementCompletionStatus.EVIDENCE_FAILURE.value
        if not reconcile_population(accounting):
            return MeasurementCompletionStatus.EVIDENCE_FAILURE.value

    return MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value


def reconcile_population(accounting: PopulationAccounting) -> bool:
    """Arithmetic invariant: requested_generated == sum(processed buckets).

    For mutation, the requested population must equal the fully processed
    population for the record to be arithmetically complete.
    """
    if accounting.requested_generated == 0:
        # Nothing requested: only complete if nothing to reconcile either.
        return accounting.actually_processed == 0
    return accounting.requested_generated == accounting.actually_processed


def certification_gate(record: MeasurementTruthRecord) -> bool:
    """Whether certification may consume this measurement.

    Rules (Phase 7):
    * completion must be AUTHORITATIVE_COMPLETE,
    * evidence classification must be authoritative,
    * the record must be durable (have a fingerprint),
    * coverage and mutation must not be conflated (authoritative only for the
      exact kind measured).

    The completion status is recomputed from the current record state so a
    stale stored status can never certify a partial/timeout/corrupt run.
    """
    record.completion_status = classify_completion(record=record)
    if (
        record.completion_status
        != MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
    ):
        return False
    if record.evidence_classification != EvidenceClassification.AUTHORITATIVE.value:
        return False
    if not record.evidence_fingerprint:
        return False
    return record.measurement_kind in (
        MeasurementKind.MUTATION.value,
        MeasurementKind.COVERAGE.value,
    )


def assert_authoritative_classification(record: MeasurementTruthRecord) -> None:
    """Mint an authoritative record: recompute completion + fingerprint."""
    record.completion_status = classify_completion(record=record)
    record.consumable_by_certification = certification_gate(record)


# ---------------------------------------------------------------------------
# Fingerprinting (reuses env.py fingerprints, never recreated).
# ---------------------------------------------------------------------------


def fingerprint_record(record: MeasurementTruthRecord, components: list[str]) -> str:
    """Deterministic evidence fingerprint over the durable truth fields."""
    import hashlib

    payload = "\n".join(
        [
            record.schema,
            record.run_id,
            record.measurement_kind,
            record.repository_sha,
            record.tree_sha,
            record.working_tree_fingerprint,
            record.configuration_fingerprint,
            record.toolchain_fingerprint,
            record.command,
            record.requested_scope,
            record.actual_scope,
            str(record.population.as_dict()),
            str(record.coverage.as_dict()),
            record.completion_status,
            record.evidence_classification,
            "|".join(sorted(components)),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def set_evidence_fingerprint(record: MeasurementTruthRecord) -> str:
    record.evidence_fingerprint = fingerprint_record(
        record, components=sorted(record.artifact_paths)
    )
    return record.evidence_fingerprint


# ---------------------------------------------------------------------------
# Persistence.
# ---------------------------------------------------------------------------


def save_measurement_truth(record: MeasurementTruthRecord, path: Path | str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record.to_dict(), indent=2) + "\n", encoding="utf-8")
    return p


def load_measurement_truth(path: Path | str) -> MeasurementTruthRecord:
    return MeasurementTruthRecord.from_dict(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


# ---------------------------------------------------------------------------
# Operator-facing truth summary (Phase 6 canonical reporting).
# ---------------------------------------------------------------------------


def operator_report(record: MeasurementTruthRecord) -> dict[str, Any]:
    """Answer the six operator questions explicitly."""
    # Ensure completion + certification are authoritative.
    recomputed_status = classify_completion(record=record)
    certifiable = (
        recomputed_status == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
        and record.evidence_classification == EvidenceClassification.AUTHORITATIVE.value
        and bool(record.evidence_fingerprint)
    )
    return {
        "requested": {
            "measurement_kind": record.measurement_kind,
            "command": record.command,
            "requested_scope": record.requested_scope,
            "mode": record.mode,
        },
        "actually_ran": {
            "actual_scope": record.actual_scope,
            "execution_status": record.execution_status,
            "completion_status": recomputed_status,
            "failure_classification": record.failure_classification,
            "duration_seconds": record.duration_seconds,
        },
        "evidence_produced": {
            "artifact_paths": list(record.artifact_paths),
            "evidence_fingerprint": record.evidence_fingerprint,
            "durable_survivor_evidence": list(record.durable_survivor_evidence),
        },
        "is_authoritative": (
            record.evidence_classification == EvidenceClassification.AUTHORITATIVE.value
        ),
        "may_certification_consume": certifiable,
        "run_next": _recommend_next(recomputed_status, record),
    }


def _recommend_next(status: str, record: MeasurementTruthRecord) -> str:
    if (
        status == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
        and record.consumable_by_certification
    ):
        return "none — measurement is authoritative and certifiable"
    if status == MeasurementCompletionStatus.PARTIAL.value:
        return "re-run the full requested scope; partial population cannot certify"
    if status == MeasurementCompletionStatus.TIMEOUT.value:
        return "re-run with a higher --max-runtime; the run timed out"
    if status == MeasurementCompletionStatus.INFRASTRUCTURE_FAILURE.value:
        return "diagnose infrastructure (env-check); the run did not complete cleanly"
    if status == MeasurementCompletionStatus.EVIDENCE_FAILURE.value:
        return "re-check evidence artifacts/fingerprints; evidence is corrupt or incomplete"
    if status == MeasurementCompletionStatus.INVALID_SCOPE.value:
        return "align requested and actual scope; currently invalid scope"
    if status == MeasurementCompletionStatus.DERIVED_ONLY.value:
        return "run a fresh authoritative measurement; derived evidence cannot certify"
    return "inspect the record — completion status is unknown"


__all__ = [
    "MeasurementCompletionStatus",
    "EvidenceClassification",
    "MeasurementKind",
    "FailureClassification",
    "PopulationAccounting",
    "CoverageResult",
    "MeasurementTruthRecord",
    "classify_completion",
    "reconcile_population",
    "certification_gate",
    "assert_authoritative_classification",
    "fingerprint_record",
    "set_evidence_fingerprint",
    "save_measurement_truth",
    "load_measurement_truth",
    "operator_report",
]
