"""VEA-5 M6 — Deep Verification & Evidence Contract.

Establishes the deterministic, machine-readable evidence contract that extends
M5's persisted-artifact model into a scalable full-system verification
architecture. M6 implements workstreams **A** (finer per-unit evidence
correlation) and **B** (Deep tier contract) first, and defines the evidence
*interfaces* for C/D/E (test-quality signals, full-system surfaces, evidence →
diagnostic pipeline) as versioned, pluggable schemas — not a full implementation
batch.

Why a new schema version (A)
----------------------------
M5's ``vea5-execution-evidence/v1`` correlated a selected unit to a single
overall status/exit/evidence_ref. That is sufficient for the M5 reconciliation
gate but NOT for the Phase-3 objective: there must be an *unambiguous path*

    unit_id -> execution record -> evidence artifact

for every selected unit. M6 introduces ``vea5-execution-evidence/v2`` with one or
more *execution attempts* per unit, each carrying command, start/end, duration,
exit code, stdout/stderr evidence, and per-signal artifact references
(test report, coverage, mutation, screenshots/video). The exact shape of the
artifact references was derived from the repository's real verification surfaces
(backend unit/integration/property/contract, frontend unit/typecheck/build,
mutation, golden, Playwright) — not invented in advance.

Hard invariant (A)
------------------
For every selected unit there is an unambiguous path
``unit_id -> execution attempt -> evidence artifact``. ``reconcile`` continues to
consume the persisted artifact; v2 is backward-compatible with v1 (``load``
accepts both).

The Deep tier contract (B)
--------------------------
Tier 3 (DEEP) becomes an explicit, first-class execution profile that *owns* the
expensive, change-independent verification. The critical distinction:

    PR   -> "what does THIS change require?"
    DEEP -> "is the ENTIRE system still healthy?"

DEEP owns, and categorizes, the verification surfaces under functional
verification, regression, test effectiveness, UI, performance and security. The
contract does NOT say "run everything blindly"; it enumerates *ownership* so each
surface is pluggable, schedulable, measurable and attributable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.foundation.verification.tier import UNIT_CATALOG, TierPlan

EVIDENCE_V2_SCHEMA = "vea5-execution-evidence/v2"
POLICY_VERSION = "vea5-tier-policy-v2"

# Back-compat: v1 artifact schema is still loadable.
EVIDENCE_V1_SCHEMA = "vea5-execution-evidence/v1"


# ---------------------------------------------------------------------------
# M6-A — Fine per-unit evidence correlation (v2 schema).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EvidenceArtifactRef:
    """A single referenced evidence artifact for one execution attempt.

    ``kind`` classifies the evidence (test-report, coverage, mutation,
    screenshots, video, log, ...); ``ref`` is a stable, resolvable path/uri. This
    is the leaf of the unit_id -> attempt -> artifact path.
    """

    kind: str  # "test-report" | "coverage" | "mutation" | "screenshots" | "video" | "log" | ...
    ref: str
    checksum: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ref": self.ref,
            "checksum": self.checksum,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EvidenceArtifactRef:
        return cls(
            kind=d.get("kind", "unknown"),
            ref=d.get("ref", ""),
            checksum=d.get("checksum"),
            metadata=d.get("metadata", {}),
        )


@dataclass(frozen=True, slots=True)
class ExecutionAttempt:
    """One attempt to run a verification unit.

    Carries command, timing, exit code and the evidence artifact references that
    make the attempt's result unambiguous and machine-navigable.
    """

    attempt_index: int
    command: str
    started_at: str | None
    ended_at: str | None
    duration_seconds: float
    exit_code: int
    status: str  # "pass" | "fail" | "error" | "skipped"
    stdout_ref: str | None = None
    stderr_ref: str | None = None
    artifacts: tuple[EvidenceArtifactRef, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_index": self.attempt_index,
            "command": self.command,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
            "status": self.status,
            "stdout_ref": self.stdout_ref,
            "stderr_ref": self.stderr_ref,
            "artifacts": [a.to_dict() for a in self.artifacts],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExecutionAttempt:
        return cls(
            attempt_index=int(d.get("attempt_index", 0)),
            command=d.get("command", ""),
            started_at=d.get("started_at"),
            ended_at=d.get("ended_at"),
            duration_seconds=float(d.get("duration_seconds", 0.0)),
            exit_code=int(d.get("exit_code", 0)),
            status=d.get("status", "unknown"),
            stdout_ref=d.get("stdout_ref"),
            stderr_ref=d.get("stderr_ref"),
            artifacts=tuple(
                EvidenceArtifactRef(
                    kind=a.get("kind", "unknown"),
                    ref=a.get("ref", ""),
                    checksum=a.get("checksum"),
                    metadata=a.get("metadata", {}),
                )
                for a in d.get("artifacts", [])
            ),
        )


@dataclass(frozen=True, slots=True)
class UnitExecutionRecord:
    """M6-A fine-grained execution record for a single selected verification unit.

    The hard invariant: unit_id -> (one or more) ExecutionAttempt -> artifacts.
    Provenance is carried so the record links back to the plan's selection reason.
    """

    unit_id: str
    provenance: dict[str, Any]
    attempts: tuple[ExecutionAttempt, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "provenance": self.provenance,
            "attempts": [a.to_dict() for a in self.attempts],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> UnitExecutionRecord:
        return cls(
            unit_id=d["unit_id"],
            provenance=d.get("provenance", {}),
            attempts=tuple(
                ExecutionAttempt.from_dict(a) for a in d.get("attempts", [])
            ),
        )

    def primary_status(self) -> str:
        """Status used by reconcile: pass only if the last attempt passed."""
        if not self.attempts:
            return "unknown"
        return self.attempts[-1].status

    def primary_exit_code(self) -> int:
        if not self.attempts:
            return 0
        return self.attempts[-1].exit_code


@dataclass
class ExecutionEvidenceV2:
    """Persisted M6-A evidence artifact (v2 schema).

    One artifact per verification run, containing a fine-grained execution record
    for every selected unit. ``reconcile`` consumes this deterministically — it
    never reconstructs from live job state.
    """

    tier: str
    plan_fingerprint: str
    commit: str
    units: tuple[UnitExecutionRecord, ...]
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": EVIDENCE_V2_SCHEMA,
            "policy_version": POLICY_VERSION,
            "tier": self.tier,
            "plan_fingerprint": self.plan_fingerprint,
            "commit": self.commit,
            "generated_at": self.generated_at,
            "units": [u.to_dict() for u in self.units],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExecutionEvidenceV2:
        return cls(
            tier=d.get("tier", "unknown"),
            plan_fingerprint=d.get("plan_fingerprint", ""),
            commit=d.get("commit", "unknown"),
            units=tuple(UnitExecutionRecord.from_dict(u) for u in d.get("units", [])),
            generated_at=d.get("generated_at", ""),
        )


def save_execution_evidence_v2(evidence: ExecutionEvidenceV2, path: Path | str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(evidence.to_dict(), indent=2) + "\n", encoding="utf-8")
    return p


def load_execution_evidence_v2(path: Path | str) -> ExecutionEvidenceV2:
    return ExecutionEvidenceV2.from_dict(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def build_unit_execution_record(
    *,
    unit_id: str,
    provenance: dict[str, Any],
    command: str,
    status: str,
    exit_code: int,
    duration_seconds: float = 0.0,
    started_at: str | None = None,
    ended_at: str | None = None,
    stdout_ref: str | None = None,
    stderr_ref: str | None = None,
    artifacts: list[EvidenceArtifactRef] | None = None,
    attempt_index: int = 0,
) -> UnitExecutionRecord:
    """Convenience constructor for one unit with a single attempt."""
    attempt = ExecutionAttempt(
        attempt_index=attempt_index,
        command=command,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration_seconds,
        exit_code=exit_code,
        status=status,
        stdout_ref=stdout_ref,
        stderr_ref=stderr_ref,
        artifacts=tuple(artifacts or ()),
    )
    return UnitExecutionRecord(
        unit_id=unit_id,
        provenance=provenance,
        attempts=(attempt,),
    )


def execution_evidence_v2_from_plan(
    *,
    plan: TierPlan,
    commit: str,
    records: dict[str, UnitExecutionRecord],
) -> ExecutionEvidenceV2:
    """Assemble a v2 artifact from a plan + per-unit records.

    Every selected unit must have a record (hard invariant: unambiguous
    unit_id -> attempt -> artifact path). Units missing from ``records`` are
    recorded with an explicit 'no-evidence' attempt so the gap is visible rather
    than silent.
    """
    out: list[UnitExecutionRecord] = []
    for sel in plan.selected:
        if sel.unit_id in records:
            out.append(records[sel.unit_id])
        else:
            out.append(
                UnitExecutionRecord(
                    unit_id=sel.unit_id,
                    provenance={
                        "category": sel.category,
                        "source": sel.source,
                        "capabilities": list(sel.capabilities),
                        "impact_kinds": list(sel.impact_kinds),
                    },
                    attempts=(
                        ExecutionAttempt(
                            attempt_index=0,
                            command=sel.command,
                            started_at=None,
                            ended_at=None,
                            duration_seconds=0.0,
                            exit_code=-1,
                            status="no-evidence",
                        ),
                    ),
                )
            )
    from runtime.foundation.verification.reconciliation import plan_fingerprint

    return ExecutionEvidenceV2(
        tier=plan.tier,
        plan_fingerprint=plan_fingerprint(plan).digest(),
        commit=commit,
        units=tuple(out),
    )


# Backward compatibility: load either v1 or v2, normalize to v2.
def load_execution_evidence_any(path: Path | str) -> ExecutionEvidenceV2:
    """Load a persisted evidence artifact, accepting v1 or v2, normalized to v2.

    v1 records (single status/exit/evidence_ref) become a single attempt whose
    artifacts list one 'report' reference. This preserves old M5 artifacts while
    the contract moves to v2.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") == EVIDENCE_V1_SCHEMA:
        units = []
        for u in data.get("units", []):
            artifact = EvidenceArtifactRef(
                kind="report", ref=u.get("evidence_ref") or ""
            )
            attempt = ExecutionAttempt(
                attempt_index=0,
                command="",
                started_at=None,
                ended_at=None,
                duration_seconds=0.0,
                exit_code=int(u.get("exit_code") or 0),
                status=u.get("status", "unknown"),
                artifacts=(artifact,) if artifact.ref else (),
            )
            units.append(
                UnitExecutionRecord(
                    unit_id=u["unit_id"],
                    provenance={},
                    attempts=(attempt,),
                )
            )
        return ExecutionEvidenceV2(
            tier=data.get("tier", "unknown"),
            plan_fingerprint=data.get("plan_fingerprint", ""),
            commit=data.get("commit", "unknown"),
            units=tuple(units),
            generated_at="",
        )
    return ExecutionEvidenceV2.from_dict(data)


# ---------------------------------------------------------------------------
# M6-B — Deep tier contract (explicit, categorized ownership).
# ---------------------------------------------------------------------------


class DeepVerificationDomain(str, Enum):
    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    TEST_EFFECTIVENESS = "test-effectiveness"
    UI = "ui"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass(frozen=True, slots=True)
class DeepVerificationSurface:
    """One expensive, change-independent verification surface owned by DEEP.

    A surface is *pluggable*: it declares its domain, the catalog unit(s) it
    backs, the command that executes it, and the trigger cadence it belongs to.
    DEEP does not "run everything blindly" — it enumerates ownership so each
    surface is schedulable, measurable and attributable.
    """

    surface_id: str
    domain: str
    description: str
    command: str
    catalog_units: tuple[str, ...]
    trigger: tuple[str, ...]  # "schedule" | "manual" | "release" | "merge"
    evidence_kinds: tuple[str, ...]
    workflow: str | None = None  # GitHub workflow file (for GitHub-native surfaces)

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "domain": self.domain,
            "description": self.description,
            "command": self.command,
            "catalog_units": list(self.catalog_units),
            "trigger": list(self.trigger),
            "evidence_kinds": list(self.evidence_kinds),
            "workflow": self.workflow,
        }


# DEEP ownership contract. Derived from the repository's real verification
# surfaces (backend unit/integration/property/contract, frontend unit/typecheck/
# build, mutation, golden, Playwright) plus the security/performance domains the
# architecture must eventually own. Trigger cadence intentionally excludes
# per-PR execution for the heavy surfaces — those are PR/LOCAL scoped or
# scheduled.
DEEP_VERIFICATION_SURFACES: tuple[DeepVerificationSurface, ...] = (
    # --- Functional verification ------------------------------------------
    DeepVerificationSurface(
        surface_id="deep-backend-suite",
        domain=DeepVerificationDomain.FUNCTIONAL.value,
        description="complete backend suite (unit + integration + property + contract)",
        command="bash .github/scripts/run_backend_verification.sh",
        catalog_units=("backend-unit", "backend-integration", "contracts-schemathesis"),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("test-report", "coverage", "property", "contract"),
    ),
    DeepVerificationSurface(
        surface_id="deep-runtime-suite",
        domain=DeepVerificationDomain.FUNCTIONAL.value,
        description="complete Engineering Runtime self-test suite",
        command="python3 runtime/verify.py runtime",
        catalog_units=("runtime-self-test",),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("test-report", "coverage"),
    ),
    DeepVerificationSurface(
        surface_id="deep-frontend-suite",
        domain=DeepVerificationDomain.FUNCTIONAL.value,
        description="complete frontend suite (unit + typecheck + build)",
        command="bash .github/scripts/run_frontend_verification.sh",
        catalog_units=("frontend-unit", "frontend-typecheck-build"),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("test-report", "typecheck", "build"),
    ),
    # --- Regression ---------------------------------------------------------
    DeepVerificationSurface(
        surface_id="deep-golden-regression",
        domain=DeepVerificationDomain.REGRESSION.value,
        description="golden dataset comparison across the system",
        command="bash .github/scripts/run_golden_tests.sh",
        catalog_units=("golden-regression",),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("golden", "report"),
    ),
    DeepVerificationSurface(
        surface_id="deep-large-dataset-regression",
        domain=DeepVerificationDomain.REGRESSION.value,
        description="large/cross-engine regression corpus execution",
        command="python3 runtime/verify.py deep --surface large-dataset",
        catalog_units=("golden-regression",),
        trigger=("schedule", "manual"),
        evidence_kinds=("report", "dataset-diff"),
    ),
    DeepVerificationSurface(
        surface_id="deep-cross-engine-regression",
        domain=DeepVerificationDomain.REGRESSION.value,
        description="historical regression corpus across all engines",
        command="python3 runtime/verify.py deep --surface cross-engine",
        catalog_units=("golden-regression",),
        trigger=("schedule", "manual"),
        evidence_kinds=("report", "regression-corpus"),
    ),
    # --- Test effectiveness ------------------------------------------------
    DeepVerificationSurface(
        surface_id="deep-mutation-testing",
        domain=DeepVerificationDomain.TEST_EFFECTIVENESS.value,
        description="mutation testing + surviving-mutant reporting",
        command="bash .github/scripts/run_mutation_selective.sh",
        catalog_units=("mutation-run",),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("mutation", "mutation-survivors", "report"),
    ),
    DeepVerificationSurface(
        surface_id="deep-coverage-analysis",
        domain=DeepVerificationDomain.TEST_EFFECTIVENESS.value,
        description="line/branch coverage measurement and delta analysis",
        command="python3 -m pytest --cov=backend --cov-report=json",
        catalog_units=("backend-unit", "backend-integration"),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("coverage",),
    ),
    # --- UI -----------------------------------------------------------------
    DeepVerificationSurface(
        surface_id="deep-playwright-e2e",
        domain=DeepVerificationDomain.UI.value,
        description="Playwright interaction verification + navigation flows",
        command="bash .github/scripts/run_playwright_tests.sh",
        catalog_units=("playwright-e2e",),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("test-report", "screenshots", "video"),
    ),
    DeepVerificationSurface(
        surface_id="deep-visual-ux-regression",
        domain=DeepVerificationDomain.UI.value,
        description="visual/UX regression where technically supported",
        command="python3 runtime/verify.py deep --surface visual-ux",
        catalog_units=("playwright-e2e",),
        trigger=("schedule", "manual"),
        evidence_kinds=("screenshots", "video", "visual-diff"),
    ),
    # --- Performance ---------------------------------------------------------
    DeepVerificationSurface(
        surface_id="deep-performance-regression",
        domain=DeepVerificationDomain.PERFORMANCE.value,
        description="execution duration, critical-path latency, resource consumption, regression thresholds",
        command="python3 runtime/verify.py deep --surface performance",
        catalog_units=("backend-unit", "playwright-e2e"),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("performance", "latency", "resource"),
    ),
    # --- Security ------------------------------------------------------------
    DeepVerificationSurface(
        surface_id="deep-codeql",
        domain=DeepVerificationDomain.SECURITY.value,
        description=(
            "CodeQL security analysis — GitHub-native via github/codeql-action. "
            "PR-visible findings (pull_request) plus scheduled default-branch "
            "scans (push to main == 'merge' cadence, schedule, manual re-scan). "
            "Languages: python (backend/runtime) + javascript/TypeScript (frontend)."
        ),
        command="github/codeql-action/analyze",
        workflow=".github/workflows/security-codeql.yml",
        catalog_units=(),
        trigger=("schedule", "manual", "release", "merge"),
        evidence_kinds=("codeql", "security"),
    ),
    DeepVerificationSurface(
        surface_id="deep-dependency-security",
        domain=DeepVerificationDomain.SECURITY.value,
        description="dependency / security checks",
        command="bash .github/scripts/run_dependency_checks.sh",
        catalog_units=(),
        trigger=("schedule", "manual", "release"),
        evidence_kinds=("dependency", "security"),
    ),
)


def deep_surfaces_by_domain(domain: str) -> list[DeepVerificationSurface]:
    return [s for s in DEEP_VERIFICATION_SURFACES if s.domain == domain]


def deep_catalog_coverage() -> set[str]:
    """Catalog units that DEEP owns at least one surface for."""
    covered: set[str] = set()
    for s in DEEP_VERIFICATION_SURFACES:
        covered.update(s.catalog_units)
    return covered


def deep_contract_manifest() -> dict[str, Any]:
    """Machine-readable DEEP ownership contract (evidence artifact)."""
    return {
        "schema": "vea5-deep-contract/v1",
        "policy_version": POLICY_VERSION,
        "question": "is the entire system still healthy?",
        "pr_question": "what does this change require?",
        "domains": [d.value for d in DeepVerificationDomain],
        "surfaces": [s.to_dict() for s in DEEP_VERIFICATION_SURFACES],
        "catalog_coverage": sorted(deep_catalog_coverage()),
        "catalog_size": len(UNIT_CATALOG),
    }


# ---------------------------------------------------------------------------
# M6-C/D/E — Evidence *interfaces* (versioned schemas; measured, not imposed).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TestQualitySignal:
    """M6-C — a single point in the test-quality evidence hierarchy.

    Hierarchy (strongest last):
        TEST EXECUTION -> COVERAGE -> PROPERTY/CONTRACT -> MUTATION
        -> GOLDEN REGRESSION -> LARGE DATASET REGRESSION
    Each signal records a measured value + the evidence ref; thresholds are NOT
    imposed here — the framework first measures reality (per M6-C directive).
    """

    __test__ = False  # not a pytest test class

    level: str  # "execution" | "coverage" | "property" | "contract" | "mutation" | "golden" | "large-dataset"
    metric: str
    value: float | str
    evidence_ref: str
    unit: str = ""


@dataclass(frozen=True, slots=True)
class FailureNormalizationNode:
    """M6-E — the unit_id -> ... -> failure normalization path node.

    failure -> unit_id -> verification provenance -> capability -> impact kind
    -> dependency -> affected verification units -> execution evidence
    -> failure normalization
    This is the pluggable evidence shape the later attribution layer consumes.
    """

    failure_id: str
    unit_id: str
    capability: str | None
    impact_kind: str | None
    dependency_ref: str | None
    affected_units: tuple[str, ...]
    execution_evidence_ref: str | None
    normalized_signature: str | None


__all__ = [
    "EVIDENCE_V2_SCHEMA",
    "EVIDENCE_V1_SCHEMA",
    "POLICY_VERSION",
    "EvidenceArtifactRef",
    "ExecutionAttempt",
    "UnitExecutionRecord",
    "ExecutionEvidenceV2",
    "save_execution_evidence_v2",
    "load_execution_evidence_v2",
    "load_execution_evidence_any",
    "build_unit_execution_record",
    "execution_evidence_v2_from_plan",
    "DeepVerificationDomain",
    "DeepVerificationSurface",
    "DEEP_VERIFICATION_SURFACES",
    "deep_surfaces_by_domain",
    "deep_catalog_coverage",
    "deep_contract_manifest",
    "TestQualitySignal",
    "FailureNormalizationNode",
]
