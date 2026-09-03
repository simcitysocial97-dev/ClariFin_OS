# runtime/foundation/verification/mutation_execution/domain_model.py
#
# M9-C44.1 — Canonical Mutation Domain Model.
#
# Repository-owned data types that define the mutation execution contract
# independently of any third-party tool.  Consumers (runner, adapter,
# evidence, certification) MUST use these types; no downstream component may
# depend on mutmut-specific identifiers or status names.
#
# Schema: m9-c44-mutation-domain/v1

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# =========================================================================
# Canonical result states (M44.1 — must cover every observable outcome).
# =========================================================================

class MutationResultState(str, Enum):
    """Canonical mutation execution outcomes. No backend may introduce an
    undocumented state; unknown backend states map here explicitly."""

    KILLED = "KILLED"           # targeted tests failed because of the mutation
    SURVIVED = "SURVIVED"       # selected tests passed despite the mutation
    EQUIVALENT = "EQUIVALENT"   # mutation cannot affect externally observable behaviour
    NO_TESTS = "NO_TESTS"       # no valid selected test exercised the mutation
    TIMEOUT = "TIMEOUT"         # execution exceeded defined timeout
    EXECUTION_ERROR = "EXECUTION_ERROR"  # test process crashed / infrastructure failed
    INVALID_MUTANT = "INVALID_MUTANT"    # mutated source identical to baseline or unapplyable
    NOT_EXECUTED = "NOT_EXECUTED"        # scheduled but never attempted (e.g. campaign cancelled)
    CANCELLED = "CANCELLED"      # explicitly cancelled by operator or campaign policy
    UNKNOWN = "UNKNOWN"          # truly unclassifiable after exhaustive diagnostics


# =========================================================================
# Timeout taxonomy (M44.8).
# =========================================================================

class TimeoutKind(str, Enum):
    TEST_TIMEOUT = "test_timeout"
    WORKER_TIMEOUT = "worker_timeout"
    CAMPAIGN_TIMEOUT = "campaign_timeout"
    INFRASTRUCTURE_TIMEOUT = "infrastructure_timeout"
    CLEANUP_TIMEOUT = "cleanup_timeout"


# =========================================================================
# Failure taxonomy (for infrastructure/retry tracking).
# =========================================================================

class InfrastructureFailureKind(str, Enum):
    NONE = "none"
    SUBPROCESS_CRASH = "subprocess_crash"
    IMPORT_PATH_FAILURE = "import_path_failure"
    CACHE_CONTAMINATION = "cache_contamination"
    STALE_CACHE_REUSE = "stale_cache_reuse"
    EDITABLE_INSTALL_FAILURE = "editable_install_failure"
    TEMP_DIR_FAILURE = "temp_dir_failure"
    WORKSPACE_CORRUPTION = "workspace_corruption"
    CONCURRENCY_COLLISION = "concurrency_collision"
    TOOL_CRASH = "tool_crash"
    TIMEOUT = "timeout"
    SIGNAL_KILL = "signal_kill"
    UNKNOWN = "unknown"


# =========================================================================
# MutationCampaign — top-level execution context (M44.1).
# =========================================================================

@dataclass(frozen=True, slots=True)
class MutationCampaign:
    campaign_id: str
    repository_revision: str           # git HEAD sha
    environment_fingerprint: str       # from env.resolve_environment()
    mutation_backend: str              # "mutmut" | "cosmic_ray" | ...
    backend_version: str               # e.g. "3.7.0"
    scope: str                         # "full" | engine name
    test_selection: str                # compact description of selected tests
    configuration_fingerprint: str     # M44.11 hash
    execution_policy: str              # serial | parallel | shard:<N>
    creation_timestamp: str            # ISO 8601
    status: str = "PENDING"            # PENDING | INITIALIZED | RUNNING | PAUSED | COMPLETED | FAILED | CANCELLED
    resumed_from: str | None = None    # parent campaign_id if this is a resume
    worker_count: int = 1
    shard_index: int | None = None
    shard_total: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["worker_count"] = self.worker_count
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MutationCampaign:
        return cls(
            campaign_id=d["campaign_id"],
            repository_revision=d["repository_revision"],
            environment_fingerprint=d["environment_fingerprint"],
            mutation_backend=d["mutation_backend"],
            backend_version=d["backend_version"],
            scope=d["scope"],
            test_selection=d["test_selection"],
            configuration_fingerprint=d["configuration_fingerprint"],
            execution_policy=d["execution_policy"],
            creation_timestamp=d["creation_timestamp"],
            status=d.get("status", "PENDING"),
            resumed_from=d.get("resumed_from"),
            worker_count=int(d.get("worker_count", 1)),
            shard_index=d.get("shard_index"),
            shard_total=d.get("shard_total"),
        )


# =========================================================================
# MutationCandidate — one source-level mutation (M44.1 + M44.2).
# =========================================================================

@dataclass(frozen=True, slots=True)
class MutationCandidate:
    canonical_mutant_id: str          # deterministic, backend-agnostic identifier
    source_file: str                  # relative to repo root
    source_hash: str                  # sha256 of baseline source file
    function: str                     # fully qualified function/method name
    line: int | None = None
    column: int | None = None
    operator: str = ""                # e.g. "arithmetic_operator", "comparison_operator"
    original_expression: str = ""
    mutated_expression: str = ""
    capability: str = ""              # from Verification Graph capability resolution
    component: str = ""               # engine / module group name
    risk: str = "medium"              # low | medium | high | critical
    selected_tests: tuple[str, ...] = ()
    backend_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MutationCandidate:
        st = d.get("selected_tests", ())
        return cls(
            canonical_mutant_id=d["canonical_mutant_id"],
            source_file=d["source_file"],
            source_hash=d["source_hash"],
            function=d["function"],
            line=d.get("line"),
            column=d.get("column"),
            operator=d.get("operator", ""),
            original_expression=d.get("original_expression", ""),
            mutated_expression=d.get("mutated_expression", ""),
            capability=d.get("capability", ""),
            component=d.get("component", ""),
            risk=d.get("risk", "medium"),
            selected_tests=tuple(st) if isinstance(st, list) else st,
            backend_metadata=d.get("backend_metadata", {}),
        )


def derive_canonical_mutant_id(
    *,
    repository_revision: str,
    source_file: str,
    source_hash: str,
    function: str,
    line: int | None,
    operator: str,
    original_expression: str,
    mutated_expression: str,
) -> str:
    """M44.2 — Deterministic mutation identity independent of mutmut.

    Derives from stable semantic information. Same revision + mutation => same id.
    """
    payload = "|".join([
        repository_revision,
        source_file,
        source_hash,
        function or "",
        str(line) if line is not None else "",
        operator,
        original_expression,
        mutated_expression,
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


# =========================================================================
# MutationExecution — per-mutant execution record (M44.1).
# =========================================================================

@dataclass
class MutationExecution:
    execution_id: str
    campaign_id: str
    mutant_id: str
    worker_id: str
    start_time: str | None = None
    end_time: str | None = None
    duration_seconds: float = 0.0
    process_id: int | None = None
    exit_status: int | None = None
    test_result: str = "UNKNOWN"     # pytest-style result for reference
    timeout: TimeoutKind | None = None
    infrastructure_failure: InfrastructureFailureKind = InfrastructureFailureKind.NONE
    mutation_result: MutationResultState = MutationResultState.UNKNOWN
    stdout_ref: str | None = None
    stderr_ref: str | None = None
    retry_count: int = 0
    workspace_id: str | None = None
    verification_passed: bool = False  # M44.15 — was mutated source actually active?

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "campaign_id": self.campaign_id,
            "mutant_id": self.mutant_id,
            "worker_id": self.worker_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "process_id": self.process_id,
            "exit_status": self.exit_status,
            "test_result": self.test_result,
            "timeout": self.timeout.value if self.timeout else None,
            "infrastructure_failure": self.infrastructure_failure.value,
            "mutation_result": self.mutation_result.value,
            "stdout_ref": self.stdout_ref,
            "stderr_ref": self.stderr_ref,
            "retry_count": self.retry_count,
            "workspace_id": self.workspace_id,
            "verification_passed": self.verification_passed,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MutationExecution:
        return cls(
            execution_id=d["execution_id"],
            campaign_id=d["campaign_id"],
            mutant_id=d["mutant_id"],
            worker_id=d["worker_id"],
            start_time=d.get("start_time"),
            end_time=d.get("end_time"),
            duration_seconds=float(d.get("duration_seconds", 0.0)),
            process_id=d.get("process_id"),
            exit_status=d.get("exit_status"),
            test_result=d.get("test_result", "UNKNOWN"),
            timeout=(
                TimeoutKind(d["timeout"]) if d.get("timeout") else None
            ),
            infrastructure_failure=InfrastructureFailureKind(
                d.get("infrastructure_failure", "none")
            ),
            mutation_result=MutationResultState(d.get("mutation_result", "UNKNOWN")),
            stdout_ref=d.get("stdout_ref"),
            stderr_ref=d.get("stderr_ref"),
            retry_count=int(d.get("retry_count", 0)),
            workspace_id=d.get("workspace_id"),
            verification_passed=bool(d.get("verification_passed", False)),
        )


# =========================================================================
# MutationResult — aggregated campaign outcome (M44.1).
# =========================================================================

@dataclass
class MutationResult:
    """Canonical aggregated mutation result, independent of any backend."""

    campaign_id: str
    total_candidates: int = 0
    killed: int = 0
    survived: int = 0
    equivalent: int = 0
    no_tests: int = 0
    timeout: int = 0
    execution_error: int = 0
    invalid_mutant: int = 0
    not_executed: int = 0
    cancelled: int = 0
    unknown: int = 0

    # Execution reliability metrics (M44.24)
    total_executions: int = 0
    successful_executions: int = 0
    infrastructure_failures: int = 0
    timeouts: int = 0
    retries_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "total_candidates": self.total_candidates,
            "killed": self.killed,
            "survived": self.survived,
            "equivalent": self.equivalent,
            "no_tests": self.no_tests,
            "timeout": self.timeout,
            "execution_error": self.execution_error,
            "invalid_mutant": self.invalid_mutant,
            "not_executed": self.not_executed,
            "cancelled": self.cancelled,
            "unknown": self.unknown,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "infrastructure_failures": self.infrastructure_failures,
            "timeouts": self.timeouts,
            "retries_total": self.retries_total,
            "mutation_score": self.score,
            "execution_reliability": self.execution_reliability,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MutationResult:
        return cls(
            campaign_id=d["campaign_id"],
            total_candidates=int(d.get("total_candidates", 0)),
            killed=int(d.get("killed", 0)),
            survived=int(d.get("survived", 0)),
            equivalent=int(d.get("equivalent", 0)),
            no_tests=int(d.get("no_tests", 0)),
            timeout=int(d.get("timeout", 0)),
            execution_error=int(d.get("execution_error", 0)),
            invalid_mutant=int(d.get("invalid_mutant", 0)),
            not_executed=int(d.get("not_executed", 0)),
            cancelled=int(d.get("cancelled", 0)),
            unknown=int(d.get("unknown", 0)),
            total_executions=int(d.get("total_executions", 0)),
            successful_executions=int(d.get("successful_executions", 0)),
            infrastructure_failures=int(d.get("infrastructure_failures", 0)),
            timeouts=int(d.get("timeouts", 0)),
            retries_total=int(d.get("retries_total", 0)),
        )

    @property
    def score(self) -> float | None:
        denom = self.killed + self.survived + self.timeout
        if denom == 0:
            return None
        return round(self.killed * 100.0 / denom, 2)

    @property
    def execution_reliability(self) -> float | None:
        """M44.24: % of executions producing a valid authoritative result."""
        if self.total_executions == 0:
            return None
        return round(
            self.successful_executions * 100.0 / self.total_executions, 2
        )

    @property
    def scored_total(self) -> int:
        return self.killed + self.survived + self.timeout

    @property
    def processed_total(self) -> int:
        return (
            self.killed
            + self.survived
            + self.equivalent
            + self.no_tests
            + self.timeout
            + self.execution_error
            + self.invalid_mutant
        )

    def reconcile(self) -> bool:
        """M44.14: every candidate must be accounted for."""
        accounted = self.processed_total + self.not_executed + self.cancelled + self.unknown
        return self.total_candidates == accounted

    def classification_summary(self) -> dict[str, Any]:
        return {
            "state_counts": {s.value: getattr(self, s.name.lower())
                             for s in MutationResultState
                             if s != MutationResultState.UNKNOWN},
            "unknown": self.unknown,
            "total_candidates": self.total_candidates,
            "score": self.score,
            "execution_reliability": self.execution_reliability,
            "reconciled": self.reconcile(),
        }


# =========================================================================
# Persistence helpers.
# =========================================================================

def save_campaign_manifest(campaign: MutationCampaign, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(campaign.to_dict(), indent=2) + "\n")
    return path


def load_campaign_manifest(path: Path) -> MutationCampaign:
    return MutationCampaign.from_dict(json.loads(path.read_text()))


def save_candidate_list(candidates: list[MutationCandidate], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([c.to_dict() for c in candidates], indent=2) + "\n")
    return path


def load_candidate_list(path: Path) -> list[MutationCandidate]:
    return [MutationCandidate.from_dict(d) for d in json.loads(path.read_text())]


def save_execution_record(execution: MutationExecution, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(execution.to_dict(), indent=2) + "\n")
    return path


def load_execution_record(path: Path) -> MutationExecution:
    return MutationExecution.from_dict(json.loads(path.read_text()))


def append_execution_log(log_path: Path, execution: MutationExecution) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(execution.to_dict()) + "\n")


__all__ = [
    "MutationResultState",
    "TimeoutKind",
    "InfrastructureFailureKind",
    "MutationCampaign",
    "MutationCandidate",
    "MutationExecution",
    "MutationResult",
    "derive_canonical_mutant_id",
    "save_campaign_manifest",
    "load_campaign_manifest",
    "save_candidate_list",
    "load_candidate_list",
    "save_execution_record",
    "load_execution_record",
    "append_execution_log",
]
