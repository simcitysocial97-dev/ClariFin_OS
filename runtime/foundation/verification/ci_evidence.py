"""
M9-C42.29 — CI Evidence Fingerprinting & Correlation (M29.1–M29.5).

Turns the CI system from a place that merely produces pass/fail
results into an *evidence-producing execution surface* that can
participate in the Verification Graph.

C42.27 mapped the CI boundary; C42.29 implements the binding.

The question this module answers:

    When CI ran a verification task, what exact evidence did it
    produce, for what repository state, population, component,
    capability, toolchain, configuration and verification task —
    and can that evidence safely be reused later?

Sub-modules
-----------
M29.1  CIEvidenceRecord — the canonical CI evidence contract. It does
       NOT create a parallel evidence model: it reuses the C42.27
       fingerprint conventions (TaskFingerprints, PopulationSnapshot),
       the C42.28 FailureKind taxonomy and the ReuseDisposition
       vocabulary.
M29.2  CI→Verification Graph binding. Every workflow/job/step that
       executes a verification command is bound into the graph with a
       documented derivation source (workflow file + job + step index +
       literal command). Relationships are never inferred from job
       names alone — only from the actual ``run:`` commands matched
       against an enumerated command-matcher table.
M29.3  Deterministic fingerprint validation detecting repository,
       source, test, configuration, toolchain, population and
       task-definition drift plus artifact corruption. A green
       workflow is never sufficient for reuse: validity requires
       fingerprint identity under the C42.27 invalidation model.
M29.4  The smallest practical ingestion boundary: a CI record is
       converted into the *same* canonical representation local
       execution produces (ExecutionEvidence / ComponentMeasurement),
       so downstream correlation/reconciliation needs no second engine.
M29.5  Local/CI semantic-equivalence checking across six dimensions
       (identity, scope, execution, result, validity, reuse
       disposition). Byte-identical artifacts are NOT required.

Pure logic + explicit filesystem reads. No subprocess except git SHA.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.evidence_reuse import (  # noqa: E402
    C42_26_COMPONENTS,
    Change,
    ComponentMeasurement,
    PopulationSnapshot,
    ReuseDisposition,
    evaluate_rule,
    INVALIDATION_RULES,
    aggregate_invalidation,
)
from runtime.foundation.verification.executor_pipeline import (  # noqa: E402
    ExecutionEvidence,
    FailureKind,
    TaskFingerprints,
)

CI_EVIDENCE_SCHEMA = "m9-ci-evidence/v1"

ExecutionMode = Literal["authoritative", "targeted", "derived", "observational"]

CertificationDisposition = ReuseDisposition


# ===========================================================================
# M29.1 — Canonical CI evidence contract
# ===========================================================================


@dataclass(frozen=True, slots=True)
class CIEvidenceRecord:
    """One CI verification task's canonical evidence record.

    Every field below is part of the record's *identity*: two records
    with identical field values are the same evidence. The fingerprint
    covers all semantic fields (never wall-clock timestamps alone).
    """

    record_id: str
    repository_sha: str
    workflow: str  # e.g. "mutation.yml"
    job: str  # e.g. "mutation"
    step: str  # step index or step name
    verification_task: str  # enumerated task id, e.g. "task::mutation::full"
    component: str | None  # full population component or None
    capability: str | None
    evidence_kind: str  # "mutation-summary", "test-report", ...
    execution_mode: ExecutionMode
    source_fingerprint: str
    test_fingerprint: str
    configuration_fingerprint: str
    toolchain_fingerprint: str
    population_fingerprint: str
    evidence_artifact_fingerprint: str  # sha256 of the artifact bytes ("" if none)
    artifact_path: str  # repo-relative path ("" if none)
    started_at: str
    ended_at: str
    exit_status: int  # 0 == success
    failure_classification: str | None  # FailureKind value or None
    certification_disposition: CertificationDisposition | None = None
    summary: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    # -- identity ---------------------------------------------------------

    def semantic_identity(self) -> str:
        """Deterministic identity over all semantic fields."""
        parts = (
            self.repository_sha,
            self.workflow,
            self.job,
            self.step,
            self.verification_task,
            self.component or "",
            self.capability or "",
            self.evidence_kind,
            self.execution_mode,
            self.source_fingerprint,
            self.test_fingerprint,
            self.configuration_fingerprint,
            self.toolchain_fingerprint,
            self.population_fingerprint,
            self.evidence_artifact_fingerprint,
            str(self.exit_status),
            self.failure_classification or "",
        )
        return hashlib.sha256("\n".join(parts).encode()).hexdigest()

    def fingerprint(self) -> str:
        return self.semantic_identity()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CI_EVIDENCE_SCHEMA,
            "record_id": self.record_id,
            "repository_sha": self.repository_sha,
            "workflow": self.workflow,
            "job": self.job,
            "step": self.step,
            "verification_task": self.verification_task,
            "component": self.component,
            "capability": self.capability,
            "evidence_kind": self.evidence_kind,
            "execution_mode": self.execution_mode,
            "source_fingerprint": self.source_fingerprint,
            "test_fingerprint": self.test_fingerprint,
            "configuration_fingerprint": self.configuration_fingerprint,
            "toolchain_fingerprint": self.toolchain_fingerprint,
            "population_fingerprint": self.population_fingerprint,
            "evidence_artifact_fingerprint": self.evidence_artifact_fingerprint,
            "artifact_path": self.artifact_path,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "exit_status": self.exit_status,
            "failure_classification": self.failure_classification,
            "certification_disposition": self.certification_disposition,
            "summary": dict(self.summary),
            "notes": self.notes,
            "identity_fingerprint": self.semantic_identity(),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CIEvidenceRecord:
        return cls(
            record_id=d["record_id"],
            repository_sha=d.get("repository_sha", ""),
            workflow=d.get("workflow", ""),
            job=d.get("job", ""),
            step=d.get("step", ""),
            verification_task=d.get("verification_task", ""),
            component=d.get("component"),
            capability=d.get("capability"),
            evidence_kind=d.get("evidence_kind", ""),
            execution_mode=d.get("execution_mode", "observational"),
            source_fingerprint=d.get("source_fingerprint", ""),
            test_fingerprint=d.get("test_fingerprint", ""),
            configuration_fingerprint=d.get("configuration_fingerprint", ""),
            toolchain_fingerprint=d.get("toolchain_fingerprint", ""),
            population_fingerprint=d.get("population_fingerprint", ""),
            evidence_artifact_fingerprint=d.get("evidence_artifact_fingerprint", ""),
            artifact_path=d.get("artifact_path", ""),
            started_at=d.get("started_at", ""),
            ended_at=d.get("ended_at", ""),
            exit_status=int(d.get("exit_status", -1)),
            failure_classification=d.get("failure_classification"),
            certification_disposition=d.get("certification_disposition"),
            summary=d.get("summary", {}),
            notes=d.get("notes", ""),
        )


def save_ci_evidence(records: Iterable[CIEvidenceRecord], path: Path | str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = [r.to_dict() for r in records]
    p.write_text(json.dumps(payload, indent=2))
    return p


def load_ci_evidence(path: Path | str) -> list[CIEvidenceRecord]:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict):
        payload = [payload]
    return [CIEvidenceRecord.from_dict(d) for d in payload]


# ===========================================================================
# M29.2 — Command matchers (enumerated; no name-based inference)
# ===========================================================================
# Each matcher maps a normalized ``run:`` command onto the verification
# semantics of the task it executes. Matchers are evaluated in order;
# the first match wins. A command that matches nothing is explicitly
# recorded as a non-verification step — never guessed into a binding.


@dataclass(frozen=True, slots=True)
class CommandSemantics:
    task_kind: str  # graph TaskKind vocabulary
    verification_task: str  # stable task id template
    evidence_kind: str
    execution_mode: ExecutionMode
    reusable_evidence: bool  # can produce reusable measurement evidence
    scope: Literal[
        "population",  # whole 14-component population
        "component",  # one component (--target)
        "capability_all",  # all capabilities' test surface (behavioral suite)
        "surface_only",  # exercises a test surface, no measurement claim
        "infra_health",  # environment/infrastructure probe, not evidence
    ]
    depends_on_config: bool  # semantics depend on mutation/config files
    description: str


def _sem(
    task_kind: str,
    task: str,
    evidence: str,
    mode: ExecutionMode,
    reusable: bool,
    scope: str,
    cfg: bool,
    desc: str,
) -> CommandSemantics:
    return CommandSemantics(
        task_kind=task_kind,
        verification_task=task,
        evidence_kind=evidence,
        execution_mode=mode,
        reusable_evidence=reusable,
        scope=scope,  # type: ignore[arg-type]
        depends_on_config=cfg,
        description=desc,
    )


# Ordered most-specific-first. Matching is on normalized command text.
COMMAND_MATCHERS: tuple[tuple[str, CommandSemantics], ...] = (
    (
        "verify.py mutation --smoke",
        _sem(
            "mutation",
            "task::mutation::smoke",
            "mutation-smoke-summary",
            "observational",
            False,
            "infra_health",
            True,
            "bounded mutation infrastructure health check",
        ),
    ),
    (
        "run_mutation_selective.sh",
        _sem(
            "mutation",
            "task::mutation::full",
            "mutation-summary",
            "authoritative",
            True,
            "population",
            True,
            "authoritative full/selective mutation campaign",
        ),
    ),
    (
        "verify.py mutation --target",
        _sem(
            "mutation",
            "task::mutation::targeted",
            "mutation-summary",
            "targeted",
            True,
            "component",
            True,
            "planner-selected single-component mutation measurement",
        ),
    ),
    (
        "verify.py mutation",
        _sem(
            "mutation",
            "task::mutation::full",
            "mutation-summary",
            "authoritative",
            True,
            "population",
            True,
            "authoritative full mutation campaign",
        ),
    ),
    (
        "run_backend_verification.sh",
        _sem(
            "unit",
            "task::unit::backend-suite",
            "test-report",
            "observational",
            True,
            "capability_all",
            False,
            "backend behavioral suite (unit/integration/property/contract)",
        ),
    ),
    (
        "verify.py backend",
        _sem(
            "unit",
            "task::unit::backend-suite",
            "test-report",
            "observational",
            True,
            "capability_all",
            False,
            "backend behavioral suite via verify.py profile",
        ),
    ),
    (
        "run_frontend_verification.sh",
        _sem(
            "static",
            "task::static::frontend-suite",
            "test-report",
            "observational",
            True,
            "surface_only",
            False,
            "frontend unit/typecheck/build suite",
        ),
    ),
    (
        "verify.py frontend",
        _sem(
            "static",
            "task::static::frontend-suite",
            "test-report",
            "observational",
            True,
            "surface_only",
            False,
            "frontend suite via verify.py profile",
        ),
    ),
    (
        "run_playwright_tests.sh",
        _sem(
            "e2e",
            "task::e2e::playwright",
            "test-report",
            "observational",
            True,
            "surface_only",
            False,
            "Playwright interaction verification",
        ),
    ),
    (
        "run_golden_tests.sh",
        _sem(
            "golden",
            "task::golden::regression",
            "golden",
            "observational",
            True,
            "surface_only",
            False,
            "golden dataset regression comparison",
        ),
    ),
    (
        "codeql-action/analyze",
        _sem(
            "static",
            "task::static::codeql",
            "security-scan",
            "observational",
            False,
            "surface_only",
            False,
            "CodeQL security analysis (GitHub-native action)",
        ),
    ),
    (
        "verify.py env-check",
        _sem(
            "static",
            "task::static::env-check",
            "environment-fingerprint",
            "observational",
            False,
            "infra_health",
            False,
            "canonical environment fingerprint check",
        ),
    ),
    (
        "verify.py status",
        _sem(
            "static",
            "task::static::status-summary",
            "status-summary",
            "observational",
            False,
            "infra_health",
            False,
            "engineering runtime status summary (not evidence)",
        ),
    ),
)


def resolve_command_semantics(command: str) -> CommandSemantics | None:
    """Resolve a run-command to its verification semantics.

    Returns None when the command is not a verification task (build,
    checkout, upload, bootstrap, ...). Never guesses.
    """
    norm = " ".join(command.split())
    for pattern, sem in COMMAND_MATCHERS:
        if pattern in norm:
            return sem
    return None


def normalize_component(short: str | None) -> str | None:
    """Resolve an engine short-name to a full population component."""
    if short is None:
        return None
    if short in C42_26_COMPONENTS:
        return short
    if f"{short}_engine" in C42_26_COMPONENTS:
        return f"{short}_engine"
    return None


# ---------------------------------------------------------------------------
# Workflow parsing + binding construction
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CIBinding:
    """A documented binding of one CI job step into the graph."""

    binding_id: str
    workflow: str
    job: str
    step_index: int
    command: str  # literal command text (derivation source)
    derivation: str  # "<workflow>#jobs.<job>.steps[<i>].run"
    semantics: CommandSemantics | None  # None => explicitly non-verification
    component: str | None
    capability: str | None
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "workflow": self.workflow,
            "job": self.job,
            "step_index": self.step_index,
            "command": self.command,
            "derivation": self.derivation,
            "semantics": (
                {
                    "task_kind": self.semantics.task_kind,
                    "verification_task": self.semantics.verification_task,
                    "evidence_kind": self.semantics.evidence_kind,
                    "execution_mode": self.semantics.execution_mode,
                    "reusable_evidence": self.semantics.reusable_evidence,
                    "scope": self.semantics.scope,
                    "depends_on_config": self.semantics.depends_on_config,
                    "description": self.semantics.description,
                }
                if self.semantics
                else None
            ),
            "component": self.component,
            "capability": self.capability,
            "rationale": self.rationale,
        }


def _extract_target_engine(command: str) -> str | None:
    """Extract the component from '--target <engine>' style commands."""
    norm = " ".join(command.split())
    if "--target" not in norm:
        return None
    after = norm.split("--target", 1)[1].strip()
    token = after.split(" ")[0].strip() if after else ""
    return normalize_component(token.strip("'\"")) or (token or None)


def build_ci_bindings(
    workflow_dir: Path | None = None,
) -> list[CIBinding]:
    """Parse every workflow and bind verification steps into bindings.

    Every returned binding carries its derivation source (file + job +
    step index + literal command). Steps whose commands resolve to no
    known verification semantics are emitted with semantics=None so the
    inventory shows they were considered and deliberately excluded.
    """
    import yaml

    wf_dir = Path(workflow_dir) if workflow_dir else REPO_ROOT / ".github" / "workflows"
    bindings: list[CIBinding] = []
    if not wf_dir.exists():
        return bindings
    for wf_file in sorted(wf_dir.glob("*.yml")):
        try:
            doc = yaml.safe_load(wf_file.read_text())
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        jobs = doc.get("jobs") or {}
        for job_id, job in sorted((jobs or {}).items()):
            if not isinstance(job, dict):
                continue
            steps = job.get("steps") or []
            for idx, step in enumerate(steps):
                if not isinstance(step, dict):
                    continue
                run = step.get("run")
                uses = step.get("uses")
                raw_cmd = (run or uses or "").strip()
                if not raw_cmd:
                    continue
                sem = resolve_command_semantics(raw_cmd)
                comp = _extract_target_engine(raw_cmd) if sem is not None else None
                cap = None
                if comp:
                    from runtime.foundation.verification.evidence_reuse import (
                        ENGINE_TO_CAPABILITY,
                    )

                    cap = ENGINE_TO_CAPABILITY.get(comp)
                bindings.append(
                    CIBinding(
                        binding_id=f"bind::{wf_file.name}::{job_id}::{idx}",
                        workflow=wf_file.name,
                        job=str(job_id),
                        step_index=idx,
                        command=raw_cmd,
                        derivation=(
                            f".github/workflows/{wf_file.name}"
                            f"#jobs.{job_id}.steps[{idx}]"
                        ),
                        semantics=sem,
                        component=comp,
                        capability=cap,
                        rationale=(
                            sem.description
                            if sem
                            else "non-verification step (build/bootstrap/upload)"
                        ),
                    )
                )
    return bindings


def verification_bindings(bindings: Iterable[CIBinding]) -> list[CIBinding]:
    return [b for b in bindings if b.semantics is not None]


# ---------------------------------------------------------------------------
# Graph binding — add CI tasks into the VerificationGraph
# ---------------------------------------------------------------------------


def bind_into_graph(graph, bindings: Iterable[CIBinding]):
    """Bind CI verification steps into an existing VerificationGraph.

    Adds a VerificationTaskNode per distinct verification_task and links
    it to the test surfaces already present for the touched capability.
    Existing nodes/edges are never duplicated. Returns the same graph
    object mutated in place (the graph is the single authority).
    """
    from runtime.foundation.verification.graph_model import (
        VerificationTaskNode,
        task_id as _task_id,
    )

    added: set[str] = set()
    for b in bindings:
        if b.semantics is None:
            continue
        tid = b.semantics.verification_task
        if tid in added:
            continue
        node = VerificationTaskNode(
            id=tid,
            kind=b.semantics.task_kind,  # type: ignore[arg-type]
            command=None,
            script=f".github/workflows/{b.workflow}",
            description=(
                f"CI-bound: {b.workflow}#{b.job} " f"({b.semantics.description})"
            ),
            capability_ids=(b.capability,) if b.capability else (),
            estimated_duration_seconds=0,
            metadata={
                "origin": "ci-binding",
                "execution_mode": b.semantics.execution_mode,
                "scope": b.semantics.scope,
                "reusable_evidence": str(b.semantics.reusable_evidence),
            },
        )
        if node.id not in graph.tasks:
            graph.add_task(node)
            added.add(tid)
        # Link task -> surfaces of the capability it touches (if any).
        if b.capability:
            cap_key = f"cap::{b.capability}"
            surfaces = graph.capability_to_surface.get(cap_key, ())
            for s in surfaces:
                graph.link_surface_task(s, tid)
    return graph


# ===========================================================================
# M29.3 — Deterministic fingerprint validation
# ===========================================================================

DriftKind = Literal[
    "repository_drift",
    "source_drift",
    "test_drift",
    "configuration_drift",
    "toolchain_drift",
    "population_drift",
    "task_definition_drift",
    "artifact_corruption",
]

DRIFT_KINDS: tuple[DriftKind, ...] = (
    "repository_drift",
    "source_drift",
    "test_drift",
    "configuration_drift",
    "toolchain_drift",
    "population_drift",
    "task_definition_drift",
    "artifact_corruption",
)


@dataclass(frozen=True, slots=True)
class CIRepositoryContext:
    """Current repository state a CI record is validated against.

    All fingerprints follow the C42.28 conventions produced by
    ``collect_repo_fingerprints`` (component-scoped source/test dirs +
    backend/pyproject.toml config + toolchain triple).
    """

    repository_sha: str
    component_source_fingerprints: dict[str, str] = field(default_factory=dict)
    component_test_fingerprints: dict[str, str] = field(default_factory=dict)
    configuration_fingerprint: str = ""
    toolchain_fingerprint: str = ""
    population_fingerprint: str = ""
    task_definitions: dict[str, str] = field(
        default_factory=dict
    )  # task_id -> definition hash

    @classmethod
    def capture(
        cls,
        *,
        components: Iterable[str] = (),
        population_fingerprint: str = "",
        repository_sha: str | None = None,
    ) -> CIRepositoryContext:
        from runtime.foundation.verification.executor_pipeline import (
            collect_repo_fingerprints,
        )

        comps = tuple(components) or C42_26_COMPONENTS
        src: dict[str, str] = {}
        tst: dict[str, str] = {}
        for c in comps:
            fps = collect_repo_fingerprints(c)
            src[c] = fps.source
            tst[c] = fps.test
        if not repository_sha:
            from runtime.foundation.verification.executor_pipeline import _git_sha

            repository_sha = _git_sha()
        pop_fp = population_fingerprint
        if not pop_fp:
            from runtime.foundation.verification.evidence_reuse import (
                c42_26_population,
            )

            pop_fp = c42_26_population().fingerprint()
        return cls(
            repository_sha=repository_sha or "",
            component_source_fingerprints=src,
            component_test_fingerprints=tst,
            configuration_fingerprint=(
                collect_repo_fingerprints(comps[0]).config if comps else ""
            ),
            toolchain_fingerprint=(
                collect_repo_fingerprints(comps[0]).toolchain if comps else ""
            ),
            population_fingerprint=pop_fp,
        )


@dataclass(frozen=True, slots=True)
class DetectedDrift:
    drift_kind: DriftKind
    detail: str
    rule_id: str | None = None  # C42.27 invalidation rule that covers it


@dataclass(frozen=True, slots=True)
class CIDriftReport:
    record_id: str
    drifts: tuple[DetectedDrift, ...]
    artifact_state: Literal["present", "missing", "corrupt", "absent_by_design"]
    exit_status: int

    @property
    def has_identity_drift(self) -> bool:
        return any(d.drift_kind != "artifact_corruption" for d in self.drifts)

    @property
    def artifact_ok(self) -> bool:
        return self.artifact_state in ("present", "absent_by_design")

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "drifts": [
                {"kind": d.drift_kind, "detail": d.detail, "rule_id": d.rule_id}
                for d in self.drifts
            ],
            "artifact_state": self.artifact_state,
            "exit_status": self.exit_status,
        }


INFRASTRUCTURE_MARKERS: tuple[str, ...] = (
    "runner lost power",
    "timed out",
    "timeout exceeded",
    "out of memory",
    "oom",
    "checkout failed",
    "bootstrap failed",
    "action failed",
    "service unavailable",
    "disk space",
    "segmentation fault",
    "killed",
)


def classify_ci_failure(
    record: CIEvidenceRecord,
    *,
    artifact_state: str = "present",
) -> FailureKind:
    """Classify why a CI record is not-green.

    Deterministic precedence:
      1. corrupt/missing artifact           -> EVIDENCE failure
      2. infrastructure markers / signals    -> INFRASTRUCTURE failure
      3. non-zero exit with intact artifact  -> VERIFICATION failure
    """
    if artifact_state in ("missing", "corrupt"):
        return FailureKind.EVIDENCE
    notes = (
        (record.notes or "").lower()
        + " "
        + (record.summary or {}).get("error", "").lower()
        if isinstance(record.summary, dict)
        else (record.notes or "").lower()
    )
    if record.exit_status in (-1, -9, -15) or any(
        m in notes for m in INFRASTRUCTURE_MARKERS
    ):
        return FailureKind.INFRASTRUCTURE
    return FailureKind.VERIFICATION


def validate_ci_evidence(
    record: CIEvidenceRecord,
    context: CIRepositoryContext,
    *,
    expected_artifact_bytes: bytes | None = None,
) -> CIDriftReport:
    """Validate a CI record's evidence identity against current state.

    Detects every drift class in DRIFT_KINDS. Artifact corruption is
    checked when the record declares an artifact fingerprint: pass the
    artifact bytes (or let them be read from disk when the path exists).
    """
    drifts: list[DetectedDrift] = []

    # Repository drift
    if (
        record.repository_sha
        and context.repository_sha
        and (record.repository_sha != context.repository_sha)
    ):
        drifts.append(
            DetectedDrift(
                "repository_drift",
                f"record sha {record.repository_sha[:12]} != current {context.repository_sha[:12]}",
            )
        )

    # Source drift (component-scoped; global sha differences alone do
    # not invalidate component evidence — only the component's own
    # source fingerprint does, per R-SRC-001.)
    if record.component and record.source_fingerprint:
        current = context.component_source_fingerprints.get(record.component)
        if current is not None and current != record.source_fingerprint:
            drifts.append(
                DetectedDrift(
                    "source_drift",
                    f"source fingerprint changed for {record.component}",
                    rule_id="R-SRC-001",
                )
            )

    # Test drift (component-scoped test surface, per R-SRC-003)
    if record.test_fingerprint:
        current_t = (
            context.component_test_fingerprints.get(record.component or "")
            if record.component
            else None
        )
        if current_t is not None and current_t != record.test_fingerprint:
            drifts.append(
                DetectedDrift(
                    "test_drift",
                    (
                        f"test surface fingerprint changed for "
                        f"{record.component or 'surface'}"
                    ),
                    rule_id="R-SRC-003",
                )
            )
        elif record.component is None:
            # Surface-scoped record (e.g. whole-suite run): its test
            # fingerprint must match at least one currently-known
            # component test surface; otherwise the exercised surface
            # has drifted since measurement.
            if context.component_test_fingerprints and (
                record.test_fingerprint
                not in context.component_test_fingerprints.values()
            ):
                drifts.append(
                    DetectedDrift(
                        "test_drift",
                        "suite test fingerprint matches no current test surface",
                        rule_id="R-SRC-003",
                    )
                )

    # Configuration drift — only for evidence whose semantics depend on it
    if (
        record.configuration_fingerprint
        and context.configuration_fingerprint
        and record.configuration_fingerprint != context.configuration_fingerprint
    ):
        sem_dependent = record.evidence_kind.startswith("mutation") or (
            record.verification_task.startswith("task::mutation")
        )
        if sem_dependent:
            drifts.append(
                DetectedDrift(
                    "configuration_drift",
                    "mutation configuration fingerprint changed",
                    rule_id="R-CFG-001",
                )
            )
        elif record.execution_mode == "authoritative":
            # Authoritative population evidence treats any config drift
            # as task-definition relevant.
            drifts.append(
                DetectedDrift(
                    "configuration_drift",
                    "authoritative evidence configuration fingerprint changed",
                    rule_id="R-TASK-001",
                )
            )

    # Toolchain drift (R-CFG-002 — measurement not comparable across
    # toolchains; applies to mutation-kind evidence)
    if (
        record.toolchain_fingerprint
        and context.toolchain_fingerprint
        and record.toolchain_fingerprint != context.toolchain_fingerprint
    ):
        if record.evidence_kind.startswith("mutation"):
            drifts.append(
                DetectedDrift(
                    "toolchain_drift",
                    "mutmut/pytest toolchain changed; measurement not comparable",
                    rule_id="R-CFG-002",
                )
            )

    # Population drift
    if (
        record.population_fingerprint
        and context.population_fingerprint
        and record.population_fingerprint != context.population_fingerprint
    ):
        drifts.append(
            DetectedDrift(
                "population_drift",
                "population snapshot fingerprint changed; aggregate recomputation required",
                rule_id="R-POP-001",
            )
        )

    # Task-definition drift (R-TASK-001): the task's command/script
    # definition changed since the record was produced.
    if record.verification_task in context.task_definitions:
        current_def = context.task_definitions[record.verification_task]
        record_def = hashlib.sha256(
            f"{record.workflow}|{record.job}|{record.verification_task}".encode()
        ).hexdigest()
        if current_def != record_def:
            drifts.append(
                DetectedDrift(
                    "task_definition_drift",
                    f"definition of {record.verification_task} changed since measurement",
                    rule_id="R-TASK-001",
                )
            )

    # Artifact corruption / incompleteness
    artifact_state: Literal["present", "missing", "corrupt", "absent_by_design"] = (
        "absent_by_design"
    )
    if record.artifact_path or record.evidence_artifact_fingerprint:
        resolved = (
            REPO_ROOT / record.artifact_path
            if record.artifact_path and not Path(record.artifact_path).is_absolute()
            else Path(record.artifact_path)
        )
        blob: bytes | None = expected_artifact_bytes
        if blob is None and record.artifact_path and resolved.exists():
            blob = resolved.read_bytes()
        if blob is None:
            artifact_state = "missing"
            drifts.append(
                DetectedDrift(
                    "artifact_corruption",
                    f"declared artifact missing: {record.artifact_path}",
                )
            )
        else:
            actual = hashlib.sha256(blob).hexdigest()
            if (
                record.evidence_artifact_fingerprint
                and actual != record.evidence_artifact_fingerprint
            ):
                artifact_state = "corrupt"
                drifts.append(
                    DetectedDrift(
                        "artifact_corruption",
                        "artifact checksum mismatch (corrupt or incomplete)",
                    )
                )
            else:
                artifact_state = "present"

    return CIDriftReport(
        record_id=record.record_id,
        drifts=tuple(drifts),
        artifact_state=artifact_state,
        exit_status=record.exit_status,
    )


# ---------------------------------------------------------------------------
# Reuse decision — green is never sufficient
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CIReuseDecision:
    record_id: str
    disposition: CertificationDisposition
    reusable: bool
    failure_classification: str | None
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "disposition": self.disposition,
            "reusable": self.reusable,
            "failure_classification": self.failure_classification,
            "reasons": list(self.reasons),
        }


_DISPOSITION_ORDER: dict[str, int] = {
    "reusable": 0,
    "reusable_with_revalidation": 1,
    "reusable_aggregate": 1,
    "stale": 2,
    "invalidated_evidence_only": 3,
    "invalidated_task": 4,
    "invalidated_component": 5,
    "invalidated_capability": 6,
    "no_evidence": 7,
}


def ci_reuse_decision(
    record: CIEvidenceRecord,
    drift_report: CIDriftReport,
    *,
    semantics: CommandSemantics | None = None,
) -> CIReuseDecision:
    """Decide whether CI evidence may be reused, deterministically.

    Rules (in precedence order):
      1. Artifact corruption/missing  -> evidence_failure, not reusable.
      2. Non-zero exit                -> verification_failure (or infra),
                                         not reusable.
      3. Infra-health probes          -> observational, never reusable.
      4. Identity drift mapped through the C42.27 invalidation taxonomy
         (worst-case wins).
      5. Otherwise                    -> reusable.
    """
    reasons: list[str] = []

    if not drift_report.artifact_ok:
        fk = FailureKind.EVIDENCE.value
        reasons.append(
            f"artifact state={drift_report.artifact_state}; evidence_failure"
        )
        return CIReuseDecision(
            record.record_id,
            "invalidated_evidence_only",
            False,
            fk,
            tuple(reasons),
        )

    if drift_report.exit_status != 0:
        fk = classify_ci_failure(record, artifact_state=drift_report.artifact_state)
        reasons.append(f"exit_status={drift_report.exit_status}; classified {fk.value}")
        return CIReuseDecision(
            record.record_id,
            "invalidated_evidence_only",
            False,
            fk.value,
            tuple(reasons),
        )

    if semantics is not None and not semantics.reusable_evidence:
        reasons.append(
            f"task {semantics.verification_task} is {semantics.scope}; "
            "observational evidence is not reusable measurement"
        )
        return CIReuseDecision(record.record_id, "stale", False, None, tuple(reasons))

    # Repository drift is an inherent invalidation: the code at
    # measurement time differs from the code now, regardless of which
    # component-level rule fires. (CI-A "unchanged" => same SHA.)
    if any(d.drift_kind == "repository_drift" for d in drift_report.drifts):
        reasons.append(
            "repository_sha changed since measurement; evidence is not "
            "reusable for the current SHA"
        )
        return CIReuseDecision(
            record.record_id,
            "invalidated_evidence_only",
            False,
            None,
            tuple(reasons),
        )

    # Map identity drift through the invalidation rules.
    verdicts = []
    for d in drift_report.drifts:
        if d.rule_id:
            rule = next((r for r in INVALIDATION_RULES if r.rule_id == d.rule_id), None)
            if rule is not None:
                change = _change_for_drift(d, record)
                comp = record.component or record.verification_task
                verdicts.append(evaluate_rule(rule, change, comp))
    if verdicts:
        scope = aggregate_invalidation(verdicts)
        disposition_map: dict[str, CertificationDisposition] = {
            "DOES_NOT_INVALIDATE": "reusable",
            "INVALIDATES_EVIDENCE_ONLY": "invalidated_evidence_only",
            "INVALIDATES_TASK": "invalidated_task",
            "INVALIDATES_COMPONENT": "invalidated_component",
            "INVALIDATES_CAPABILITY": "invalidated_capability",
            "INVALIDATES_POPULATION": "invalidated_capability",
        }
        disp = disposition_map[scope]
        if disp != "reusable":
            reasons.extend(d.detail for d in drift_report.drifts)
            return CIReuseDecision(record.record_id, disp, False, None, tuple(reasons))
        reasons.append("drift present but rules do not invalidate")

    # No drift, green, reusable task kind.
    reasons.append("identity intact; exit 0; task produces reusable evidence")
    return CIReuseDecision(record.record_id, "reusable", True, None, tuple(reasons))


def _change_for_drift(d: DetectedDrift, record: CIEvidenceRecord) -> Change:
    """Build the Change shape each rule's evaluator expects.

    The C42.27 evaluators match on specific (kind, target) shapes —
    e.g. R-CFG-001 requires ``target.endswith('::<component>')``. The
    mapping below constructs exactly those shapes so CI drift is judged
    by the same rules as local drift. No new rules are invented here.
    """
    comp = record.component or record.verification_task
    if d.drift_kind in ("configuration_drift", "task_definition_drift"):
        return Change(
            kind=(
                "config_change"
                if d.drift_kind == "configuration_drift"
                else "task_command_change"
            ),
            target=f"task::{record.verification_task}::{comp}",
        )
    if d.drift_kind == "test_drift":
        return Change(kind="test_change", target=f"tests::{comp}")
    if d.drift_kind == "population_drift":
        return Change(kind="population_remove", target=comp)
    return Change(
        kind=_drift_change_kind(d.drift_kind),
        target=comp,
    )


def _drift_change_kind(kind: DriftKind) -> str:
    return {
        "repository_drift": "repository_change",
        "source_drift": "source_change",
        "test_drift": "test_change",
        "configuration_drift": "config_change",
        "toolchain_drift": "toolchain_change",
        "population_drift": "population_change",
        "task_definition_drift": "task_command_change",
        "artifact_corruption": "artifact_corruption",
    }[kind]


def validate_and_decide(
    record: CIEvidenceRecord,
    context: CIRepositoryContext,
    *,
    semantics: CommandSemantics | None = None,
    expected_artifact_bytes: bytes | None = None,
) -> tuple[CIDriftReport, CIReuseDecision]:
    report = validate_ci_evidence(
        record, context, expected_artifact_bytes=expected_artifact_bytes
    )
    decision = ci_reuse_decision(record, report, semantics=semantics)
    return report, decision


# ===========================================================================
# M29.4 — Ingestion into the canonical local representation
# ===========================================================================


def ingest_ci_evidence(
    record: CIEvidenceRecord,
    *,
    decision: CIReuseDecision | None = None,
) -> ExecutionEvidence:
    """Convert a CI record into the canonical ExecutionEvidence used by
    local targeted execution (C42.28). The CI system executes; the
    verification framework interprets and correlates — one model only.
    """
    fk: FailureKind | None = None
    if record.failure_classification:
        try:
            fk = FailureKind(record.failure_classification)
        except ValueError:
            fk = FailureKind.EVIDENCE
    elif record.exit_status != 0:
        fk = FailureKind.VERIFICATION
    return ExecutionEvidence(
        execution_id=record.record_id,
        task_id=record.verification_task,
        component=record.component or "",
        capability=record.capability or "",
        verification_kind=(
            "mutation"
            if record.evidence_kind.startswith("mutation")
            else (
                record.verification_task.split("::")[1]
                if "::" in record.verification_task
                else "unknown"
            )
        ),
        started_at=record.started_at,
        completed_at=record.ended_at,
        duration_seconds=max(
            0.0,
            _iso_diff_seconds(record.started_at, record.ended_at),
        ),
        command=f"ci:{record.workflow}/{record.job}#{record.step}",
        exit_code=record.exit_status,
        failure_kind=fk,
        failure_message=(
            decision.reasons[0] if decision and decision.reasons else record.notes
        ),
        counts=(
            dict(record.summary.get("counts", {}))
            if isinstance(record.summary, dict)
            else {}
        ),
        coverage=(
            record.summary.get("coverage") if isinstance(record.summary, dict) else None
        ),
        test_count=(
            record.summary.get("test_count")
            if isinstance(record.summary, dict)
            else None
        ),
        source_fingerprint=record.source_fingerprint,
        test_fingerprint=record.test_fingerprint,
        config_fingerprint=record.configuration_fingerprint,
        toolchain_fingerprint=record.toolchain_fingerprint,
        repository_sha=record.repository_sha,
        artifact_paths=(record.artifact_path,) if record.artifact_path else (),
        notes=f"ingested from CI ({record.workflow}/{record.job}); "
        f"disposition={decision.disposition if decision else 'unevaluated'}",
    )


def ci_measurement(
    record: CIEvidenceRecord,
    *,
    population_id: str,
) -> ComponentMeasurement | None:
    """Promote a CI mutation record into a ComponentMeasurement so it can
    participate in derived aggregates. Only mutation-kind records with
    kill/scored counts qualify; everything else returns None."""
    if not record.evidence_kind.startswith("mutation"):
        return None
    summary = record.summary if isinstance(record.summary, dict) else {}
    counts = summary.get("counts") or {}
    scored = int(counts.get("generated", 0) or 0)
    killed = int(counts.get("killed", 0) or 0)
    if not scored:
        return None
    return ComponentMeasurement(
        measurement_id=f"meas::ci::{record.record_id}",
        component=record.component or "",
        population_id=population_id,
        kind="mutation",
        run_id=f"ci::{record.workflow}/{record.job}",
        measured_at=record.ended_at or record.started_at,
        repository_sha=record.repository_sha,
        source_fingerprint=record.source_fingerprint,
        test_fingerprint=record.test_fingerprint,
        config_hash=record.configuration_fingerprint,
        toolchain_hash=record.toolchain_fingerprint,
        summary={
            "scored": scored,
            "killed": killed,
            "mutation_score_pct": round(100.0 * killed / scored, 2) if scored else 0.0,
        },
        notes=f"promoted from CI record {record.record_id}",
    )


def _iso_diff_seconds(start: str, end: str) -> float:
    try:
        s = datetime.fromisoformat(start)
        e = datetime.fromisoformat(end)
        return (e - s).total_seconds()
    except Exception:
        return 0.0


# ===========================================================================
# M29.5 — Local/CI semantic equivalence
# ===========================================================================

EQUIVALENCE_DIMENSIONS: tuple[str, ...] = (
    "identity",
    "scope",
    "execution",
    "result",
    "validity",
    "reuse_disposition",
)


@dataclass(frozen=True, slots=True)
class EquivalenceDimension:
    dimension: str
    equivalent: bool
    detail: str


@dataclass(frozen=True, slots=True)
class EquivalenceReport:
    local_execution_id: str
    ci_record_id: str
    dimensions: tuple[EquivalenceDimension, ...]

    @property
    def semantically_equivalent(self) -> bool:
        return all(d.equivalent for d in self.dimensions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_execution_id": self.local_execution_id,
            "ci_record_id": self.ci_record_id,
            "semantically_equivalent": self.semantically_equivalent,
            "dimensions": [
                {
                    "dimension": d.dimension,
                    "equivalent": d.equivalent,
                    "detail": d.detail,
                }
                for d in self.dimensions
            ],
        }


def semantic_equivalence(
    local: ExecutionEvidence,
    ci_record: CIEvidenceRecord,
    ingested: ExecutionEvidence,
    *,
    local_decision: CIReuseDecision | None = None,
    ci_decision: CIReuseDecision | None = None,
) -> EquivalenceReport:
    """Check semantic equivalence (not byte equality) between a locally
    executed task's evidence and an ingested CI record's evidence."""
    dims: list[EquivalenceDimension] = []

    # Identity: same fingerprint quad.
    ident = (
        local.source_fingerprint == ingested.source_fingerprint
        and local.test_fingerprint == ingested.test_fingerprint
        and local.config_fingerprint == ingested.config_fingerprint
        and local.toolchain_fingerprint == ingested.toolchain_fingerprint
    )
    dims.append(
        EquivalenceDimension(
            "identity",
            ident,
            "four fingerprints match" if ident else "fingerprint quad differs",
        )
    )

    # Scope: same component/capability/verification kind.
    scope_eq = (
        local.component == ingested.component
        and local.verification_kind == ingested.verification_kind
    )
    dims.append(
        EquivalenceDimension(
            "scope",
            scope_eq,
            f"component={local.component!r} kind={local.verification_kind!r}"
            + ("" if scope_eq else " differs from CI ingestion"),
        )
    )

    # Execution: both carry command + timing + exit code shape.
    exec_eq = all(
        [
            bool(local.command),
            bool(ingested.command),
            local.completed_at is not None,
            ingested.completed_at is not None,
            isinstance(local.exit_code, int),
            isinstance(ingested.exit_code, int),
        ]
    )
    dims.append(
        EquivalenceDimension(
            "execution",
            exec_eq,
            (
                "command/timing/exit shape present on both sides"
                if exec_eq
                else "execution shape incomplete"
            ),
        )
    )

    # Result: success/failure agreement (semantic, not byte-level).
    local_ok = local.failure_kind is None and local.exit_code == 0
    ingested_ok = ingested.failure_kind is None and ingested.exit_code == 0
    result_eq = local_ok == ingested_ok
    dims.append(
        EquivalenceDimension(
            "result",
            result_eq,
            f"outcome agreement (local_ok={local_ok}, ci_ok={ingested_ok})",
        )
    )

    # Validity: same repository identity spine.
    validity_eq = local.repository_sha == ingested.repository_sha
    dims.append(
        EquivalenceDimension(
            "validity",
            validity_eq,
            f"repository_sha {'match' if validity_eq else 'mismatch'}",
        )
    )

    # Reuse disposition: same verdict under the same invalidation model.
    if local_decision is not None and ci_decision is not None:
        disp_eq = (
            local_decision.reusable == ci_decision.reusable
            and _DISPOSITION_ORDER.get(local_decision.disposition, 99)
            == _DISPOSITION_ORDER.get(ci_decision.disposition, 99)
        )
        detail = (
            f"dispositions aligned ({local_decision.disposition})"
            if disp_eq
            else f"local={local_decision.disposition} vs ci={ci_decision.disposition}"
        )
    else:
        disp_eq = local.notes.startswith("ingested from CI") or (
            local.source_fingerprint == ingested.source_fingerprint
        )
        detail = "decisions not supplied; structural alignment used"
    dims.append(EquivalenceDimension("reuse_disposition", disp_eq, detail))

    return EquivalenceReport(
        local_execution_id=local.execution_id,
        ci_record_id=ci_record.record_id,
        dimensions=tuple(dims),
    )


__all__ = [
    "CI_EVIDENCE_SCHEMA",
    "CIEvidenceRecord",
    "CIRepositoryContext",
    "CIDriftReport",
    "DetectedDrift",
    "DRIFT_KINDS",
    "CIReuseDecision",
    "CIBinding",
    "CommandSemantics",
    "COMMAND_MATCHERS",
    "EquivalenceDimension",
    "EquivalenceReport",
    "EQUIVALENCE_DIMENSIONS",
    "ExecutionMode",
    "build_ci_bindings",
    "bind_into_graph",
    "classify_ci_failure",
    "ci_measurement",
    "ci_reuse_decision",
    "ingest_ci_evidence",
    "load_ci_evidence",
    "normalize_component",
    "resolve_command_semantics",
    "save_ci_evidence",
    "semantic_equivalence",
    "validate_and_decide",
    "validate_ci_evidence",
    "verification_bindings",
]
