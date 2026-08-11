"""
Verification Model — Phase 2

Immutable dataclasses for verification runtime.
No execution logic. Data models only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class VerificationCategory(str, Enum):
    """Categories of verification."""

    CONTRACT = "contract"
    PROPERTY = "property"
    INVARIANT = "invariant"
    CAPABILITY = "capability"
    MUTATION = "mutation"
    INTEGRATION = "integration"
    MIGRATION = "migration"
    CONTRACT_FRONTEND = "contract_frontend"
    CONTRACT_BACKEND = "contract_backend"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ARCHITECTURAL = "architectural"


class VerificationSeverity(str, Enum):
    """Severity levels for verification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VerificationStatus(str, Enum):
    """Status of a verification step or plan."""

    PENDING = "pending"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class VerificationScope(str, Enum):
    """Verification scope levels."""

    QUICK = "quick"
    BACKEND = "backend"
    FRONTEND = "frontend"
    CONTRACTS = "contracts"
    PROPERTY = "property"
    MUTATION = "mutation"
    INTEGRATION = "integration"
    MIGRATION = "migration"
    REPOSITORY = "repository"
    RUNTIME = "runtime"
    GOLDEN = "golden"
    PLAYWRIGHT = "playwright"
    FULL = "full"


@dataclass(frozen=True, slots=True)
class VerificationDependency:
    """A dependency between verification targets."""

    target_id: str
    dependency_type: str = "requires"
    reason: str = ""


@dataclass(frozen=True, slots=True)
class VerificationRequirement:
    """A single verification requirement."""

    id: str
    category: VerificationCategory
    severity: VerificationSeverity
    description: str
    scope: VerificationScope
    module: str | None = None
    capability: str | None = None
    workflow: str | None = None
    script: str | None = None
    evidence_required: list[str] = field(default_factory=list)
    depends_on: list[VerificationDependency] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationTarget:
    """A target to be verified."""

    id: str
    name: str
    category: VerificationCategory
    scope: VerificationScope
    module: str | None = None
    capability: str | None = None
    file_path: str | None = None
    function_name: str | None = None
    class_name: str | None = None
    requirements: list[VerificationRequirement] = field(default_factory=list)
    dependencies: list[VerificationDependency] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass(frozen=True, slots=True)
class VerificationStep:
    """A single step in a verification plan.

    Identity note (VEA-2 Phase 2, M1):
        ``id`` is positional (``step-0001``) and is *reassigned* during command
        deduplication in the planner. It is therefore unstable across runs and MUST NOT
        be used as a join key between planning, execution and evidence. It remains valid
        only as an internal ordering handle.

        ``unit_id`` is the stable join key. It names the owning ``VerificationUnit`` from
        the intelligence pipeline and is what carries through to ``ExecutionResult`` and
        on into evidence.
    """

    id: str
    target: VerificationTarget
    order: int
    command: str | None = None
    workflow: str | None = None
    script: str | None = None
    estimated_duration_seconds: int = 0
    required_evidence: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: VerificationStatus = VerificationStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
    # --- VEA-2 Phase 2 identity spine -------------------------------------------------
    # Optional and defaulted so every pre-existing construction site keeps working
    # unchanged. ``None`` is a legitimate, visible outcome meaning "no unit mapped"
    # (surfaced as UNMAPPED in the run manifest) — it is never inferred away.
    unit_id: str | None = None
    # Mirrors the C11 provenance shape emitted by VerificationUnit.to_dict()["provenance"]:
    # {"capabilities": [...], "impact_kinds": [...], "source": "..."}
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    """Evidence produced by a verification step."""

    step_id: str
    target_id: str
    type: str
    content: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    status: VerificationStatus = VerificationStatus.UNKNOWN
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Result of a verification step (placeholder - no execution logic)."""

    step_id: str
    target_id: str
    status: VerificationStatus
    evidence: list[VerificationEvidence] = field(default_factory=list)
    error: str | None = None
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationTask:
    """A discrete verification task within a profile."""

    id: str
    name: str
    profile: str
    commands: list[str]
    category: VerificationCategory
    scope: VerificationScope
    dependencies: list[str] = field(default_factory=list)
    estimated_duration_seconds: int = 0
    required_evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Result of executing a single verification command.

    Identity note (VEA-2 Phase 2, M1):
        ``unit_id`` and ``provenance`` are copied verbatim from the originating
        ``VerificationStep`` by the orchestrator. They are what allow a failure observed
        at execution time to be joined back to the impact analysis that justified running
        the command in the first place.
    """

    task_id: str
    command: str
    status: VerificationStatus
    exit_code: int
    duration_seconds: float
    stdout_path: str
    stderr_path: str
    error: str | None = None
    # --- VEA-2 Phase 2 identity spine -------------------------------------------------
    # Optional and defaulted; all 5 pre-existing construction sites keep working unchanged.
    unit_id: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationSummary:
    """Summary of a completed verification run."""

    profile: str
    total_tasks: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    report_path: str
    cache_path: str
    changed_files: list[str] = field(default_factory=list)
    dependency_chains: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    overall_status: VerificationStatus = VerificationStatus.PASSED


@dataclass(frozen=True, slots=True)
class VerificationPlan:
    """A complete verification plan."""

    id: str
    name: str
    scope: VerificationScope
    created_at: datetime = field(default_factory=datetime.utcnow)
    targets: list[VerificationTarget] = field(default_factory=list)
    steps: list[VerificationStep] = field(default_factory=list)
    required_workflows: list[str] = field(default_factory=list)
    required_scripts: list[str] = field(default_factory=list)
    estimated_duration_seconds: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_target(self, target_id: str) -> VerificationTarget | None:
        """Get a target by ID."""
        for target in self.targets:
            if target.id == target_id:
                return target
        return None

    def get_step(self, step_id: str) -> VerificationStep | None:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_steps_for_target(self, target_id: str) -> list[VerificationStep]:
        """Get all steps for a target."""
        return [step for step in self.steps if step.target.id == target_id]
