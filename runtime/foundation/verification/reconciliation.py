"""VEA-5 M4/M5 — Plan Reconciliation + CI Reconciliation Gate.

Closes the open risk identified in VEA-5 M0: when a developer's LOCAL plan
and the CI/PR plan are compared, the *legitimate* differences (tier policy,
environment) must be distinguished from *illegitimate* ones (a planning defect
that silently changed which units run). M5 extends this with a CI reconciliation
gate that consumes **persisted** plan + execution-evidence artifacts, so the gate
is deterministic and never reconstructs state from the end of a job.

The M4 invariant is deliberately NOT "local == PR plan always". The execution
model (docs/verification/VEA5_EXECUTION_MODEL.md §3-§6, §14) allows — by design —
local and PR to select different unit sets (e.g. PR selects targeted mutation for
a critical engine change while local keeps it behind the cost gate). What must
hold is:

    equivalent normalized inputs
        + equivalent tier policy
        -> deterministic equivalent plans (fingerprint-stable)

and any divergence between two plans must be *explainable* by exactly one
classified cause:

    * SAME_PLAN             — identical normalized fingerprints
    * EXPECTED_TIER_DIFFERENCE — only tier-eligible units differ; both plans are
                                 individually complete and internally valid
    * ENVIRONMENT_DIVERGENCE   — same plan, but execution/evidence diverged
    * PLANNING_DIVERGENCE      — an unexplained change in selected/excluded units
                                 (a real defect to investigate)

Reconciliation is structural only: it compares *plans* and *recorded results*.
It never re-derives a plan from git and never assumes a cached PASS (that is the
cache contract, M3). The output is a machine-readable ``ReconciliationReport``
that feeds the CI evidence identity spine:

    commit -> change-set fingerprint -> tier -> plan fingerprint
            -> unit_id -> provenance -> execution -> evidence
            -> failure -> attribution -> verdict
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from enum import Enum
from typing import Any

from runtime.foundation.verification.tier import (
    UNIT_CATALOG,
    TierPlan,
)

POLICY_VERSION = "vea5-tier-policy-v1"


# ---------------------------------------------------------------------------
# Change-set normalization + fingerprinting.
# ---------------------------------------------------------------------------


def normalize_change_set(changed_files: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Canonicalize a change set so that semantically identical sets of files
    produce identical normalized fingerprints regardless of order or duplicates.

    Only repository-relevant paths survive (the orchestrator's
    ``_filter_changed_files`` already performs this role upstream; this is a
    defensive re-normalization so reconciliation never diverges on ordering).
    """
    return tuple(sorted(set(changed_files or [])))


def change_set_fingerprint(changed_files: list[str] | tuple[str, ...]) -> str:
    """Deterministic short fingerprint of a normalized change set."""
    normalized = normalize_change_set(changed_files)
    payload = "\n".join(normalized).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def change_set_diff(
    a: list[str] | tuple[str, ...], b: list[str] | tuple[str, ...]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (only_in_a, only_in_b) for two change sets."""
    na, nb = set(normalize_change_set(a)), set(normalize_change_set(b))
    return tuple(sorted(na - nb)), tuple(sorted(nb - na))


# ---------------------------------------------------------------------------
# Plan fingerprinting (identity of a TierPlan, independent of generated_at).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PlanFingerprint:
    """Compact deterministic identity of a TierPlan."""

    tier: str
    change_set: str  # normalized change-set fingerprint
    selected: tuple[str, ...]
    excluded: tuple[str, ...]
    estimated_seconds: int
    policy_version: str = POLICY_VERSION

    def digest(self) -> str:
        payload = json_dumps_ordered(
            {
                "tier": self.tier,
                "change_set": self.change_set,
                "selected": sorted(self.selected),
                "excluded": sorted(self.excluded),
                "estimated_seconds": self.estimated_seconds,
                "policy_version": self.policy_version,
            }
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]


def plan_fingerprint(plan: TierPlan) -> PlanFingerprint:
    """Derive a :class:`PlanFingerprint` from a TierPlan.

    Two plans with equivalent normalized inputs + equivalent tier policy yield
    identical fingerprints (the M4 determinism guarantee). ``base_ref`` is
    intentionally excluded from the fingerprint: a change-set-equal plan must be
    identical regardless of which *unrelated* base ref the tier ignored.
    """
    return PlanFingerprint(
        tier=plan.tier,
        change_set=change_set_fingerprint(plan.changed_files),
        selected=tuple(s.unit_id for s in plan.selected),
        excluded=tuple(e.unit_id for e in plan.excluded),
        estimated_seconds=plan.estimated_seconds,
    )


# ---------------------------------------------------------------------------
# Execution / evidence reconciliation.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class UnitExecution:
    """Recorded result of a single unit's execution (from evidence)."""

    unit_id: str
    status: str  # "pass" | "fail" | "skipped" | "cached"
    exit_code: int | None = None
    evidence_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ReconciliationClassification:
    """The verdict of comparing two plans + their recorded executions."""

    status: str  # see ReconciliationStatus
    reason: str
    diverging_units: tuple[str, ...] = ()
    tier_differs: bool = False
    environment_diverges: bool = False
    planning_diverges: bool = False


class ReconciliationStatus(str, Enum):
    SAME_PLAN = "same-plan"
    EXPECTED_TIER_DIFFERENCE = "expected-tier-difference"
    ENVIRONMENT_DIVERGENCE = "environment-divergence"
    PLANNING_DIVERGENCE = "planning-divergence"


@dataclass
class ReconciliationReport:
    """Full machine-readable reconciliation result (CI evidence artifact)."""

    classification: ReconciliationClassification
    local_fingerprint: PlanFingerprint
    ci_fingerprint: PlanFingerprint
    change_set_local: str
    change_set_ci: str
    policy_version: str = POLICY_VERSION
    evidence_identity: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "vea5-reconciliation/v1",
            "policy_version": self.policy_version,
            "classification": asdict(self.classification),
            "local_fingerprint": {
                "tier": self.local_fingerprint.tier,
                "change_set": self.local_fingerprint.change_set,
                "selected": list(self.local_fingerprint.selected),
                "excluded": list(self.local_fingerprint.excluded),
                "estimated_seconds": self.local_fingerprint.estimated_seconds,
                "digest": self.local_fingerprint.digest(),
            },
            "ci_fingerprint": {
                "tier": self.ci_fingerprint.tier,
                "change_set": self.ci_fingerprint.change_set,
                "selected": list(self.ci_fingerprint.selected),
                "excluded": list(self.ci_fingerprint.excluded),
                "estimated_seconds": self.ci_fingerprint.estimated_seconds,
                "digest": self.ci_fingerprint.digest(),
            },
            "change_set_local": self.change_set_local,
            "change_set_ci": self.change_set_ci,
            "evidence_identity": self.evidence_identity,
        }


# ---------------------------------------------------------------------------
# Internal comparison helpers.
# ---------------------------------------------------------------------------


def _tier_eligible_unit_ids() -> tuple[str, ...]:
    """Units whose selection legitimately depends on tier policy alone.

    These are the units the tier policy matrix (M1 §8) allows to differ between
    LOCAL and PR without it being a planning defect.
    """
    eligible = []
    for u in UNIT_CATALOG:
        # mutation / golden are tier-gated by cost + criticality policy.
        if u["category"] in ("mutation", "golden"):
            eligible.append(u["id"])
    return tuple(eligible)


def _compare_execution(
    local_results: dict[str, UnitExecution],
    ci_results: dict[str, UnitExecution],
) -> bool:
    """True if both sides recorded the same per-unit status+exit for every unit
    present in either side."""
    all_ids = set(local_results) | set(ci_results)
    for uid in all_ids:
        lr = local_results.get(uid)
        cr = ci_results.get(uid)
        if lr is None or cr is None:
            return False
        if lr.status != cr.status:
            return False
        if (lr.exit_code or 0) != (cr.exit_code or 0):
            return False
    return True


def _only_tier_eligible_differ(
    local_sel: set[str], ci_sel: set[str], local_exc: set[str], ci_exc: set[str]
) -> bool:
    tier_eligible = set(_tier_eligible_unit_ids())
    selected_only_local = local_sel - ci_sel
    selected_only_ci = ci_sel - local_sel
    excluded_only_local = local_exc - ci_exc
    excluded_only_ci = ci_exc - local_exc
    diff_units = (
        selected_only_local | selected_only_ci | excluded_only_local | excluded_only_ci
    )
    return bool(diff_units) and diff_units <= tier_eligible


def build_evidence_identity(
    *,
    commit: str,
    change_set: str,
    tier: str,
    plan_digest: str,
    unit_executions: list[UnitExecution] | None = None,
) -> dict[str, Any]:
    """Construct the evidence identity spine node for one plan's execution.

    commit -> change-set -> tier -> plan fingerprint -> unit_ids -> provenance
    -> execution -> evidence -> failure -> attribution -> verdict.
    """
    units = []
    for ex in unit_executions or []:
        units.append(
            {
                "unit_id": ex.unit_id,
                "status": ex.status,
                "exit_code": ex.exit_code,
                "evidence_ref": ex.evidence_ref,
            }
        )
    return {
        "commit": commit,
        "change_set_fingerprint": change_set,
        "tier": tier,
        "plan_fingerprint": plan_digest,
        "units": units,
    }


# ---------------------------------------------------------------------------
# Public reconciliation entry point.
# ---------------------------------------------------------------------------


def reconcile(
    local_plan: TierPlan,
    ci_plan: TierPlan,
    *,
    local_results: dict[str, UnitExecution] | None = None,
    ci_results: dict[str, UnitExecution] | None = None,
    commit: str | None = None,
    change_set_local: str | None = None,
    change_set_ci: str | None = None,
) -> ReconciliationReport:
    """Compare a LOCAL plan against a CI/PR plan and classify the relationship.

    Returns a :class:`ReconciliationReport` whose ``classification.status`` is one
    of :class:`ReconciliationStatus`. The classification is *explainable*: every
    divergence is attributed to a single classified cause.
    """
    local_fp = plan_fingerprint(local_plan)
    ci_fp = ci_fingerprint_from(ci_plan)
    local_results = local_results or {}
    ci_results = ci_results or {}

    lf = change_set_local or local_fp.change_set
    cf = change_set_ci or ci_fp.change_set

    # 1. Identical normalized fingerprints.
    if local_fp.digest() == ci_fp.digest():
        # Plans are structurally equal. If recorded execution/evidence diverged
        # for the same plan, that is an environment divergence, not a clean
        # match.
        if not _compare_execution(local_results, ci_results):
            classification = ReconciliationClassification(
                status=ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value,
                reason="same plan but recorded execution/evidence diverged",
                environment_diverges=True,
            )
        else:
            classification = ReconciliationClassification(
                status=ReconciliationStatus.SAME_PLAN.value,
                reason="identical normalized plan fingerprints",
            )
    # 2. Same plan structurally but execution/evidence diverged.
    elif (
        local_fp.tier == ci_fp.tier
        and local_fp.change_set == ci_fp.change_set
        and local_fp.selected == ci_fp.selected
        and local_fp.excluded == ci_fp.excluded
    ):
        env_div = not _compare_execution(local_results, ci_results)
        classification = ReconciliationClassification(
            status=ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value,
            reason=(
                "structurally identical plans but recorded execution diverged"
                if env_div
                else "structurally identical plans (results unavailable)"
            ),
            environment_diverges=env_div,
        )
    # 3. Different tier, only tier-eligible units differ -> expected.
    elif local_fp.tier != ci_fp.tier and _only_tier_eligible_differ(
        set(local_fp.selected),
        set(ci_fp.selected),
        set(local_fp.excluded),
        set(ci_fp.excluded),
    ):
        only_local = tuple(
            sorted(
                (set(local_fp.selected) - set(ci_fp.selected))
                | (set(local_fp.excluded) - set(ci_fp.excluded))
            )
        )
        only_ci = tuple(
            sorted(
                (set(ci_fp.selected) - set(local_fp.selected))
                | (set(ci_fp.excluded) - set(local_fp.excluded))
            )
        )
        classification = ReconciliationClassification(
            status=ReconciliationStatus.EXPECTED_TIER_DIFFERENCE.value,
            reason=(
                "tiers differ and only tier-eligible units "
                f"({', '.join(_tier_eligible_unit_ids())}) differ"
            ),
            diverging_units=tuple(sorted(set(only_local) | set(only_ci))),
            tier_differs=True,
        )
    # 4. Otherwise: an unexplained change in selected/excluded units.
    else:
        only_local = tuple(
            sorted(
                (set(local_fp.selected) - set(ci_fp.selected))
                | (set(local_fp.excluded) - set(ci_fp.excluded))
            )
        )
        only_ci = tuple(
            sorted(
                (set(ci_fp.selected) - set(local_fp.selected))
                | (set(ci_fp.excluded) - set(local_fp.excluded))
            )
        )
        classification = ReconciliationClassification(
            status=ReconciliationStatus.PLANNING_DIVERGENCE.value,
            reason="unexplained change in selected/excluded units",
            diverging_units=tuple(sorted(set(only_local) | set(only_ci))),
            planning_diverges=True,
        )

    evidence_identity = build_evidence_identity(
        commit=commit or "unknown",
        change_set=lf,
        tier=local_fp.tier,
        plan_digest=local_fp.digest(),
        unit_executions=list(local_results.values()),
    )

    return ReconciliationReport(
        classification=classification,
        local_fingerprint=local_fp,
        ci_fingerprint=ci_fp,
        change_set_local=lf,
        change_set_ci=cf,
        evidence_identity=evidence_identity,
    )


def ci_fingerprint_from(plan: TierPlan) -> PlanFingerprint:
    """Alias so callers can express both sides symmetrically."""
    return plan_fingerprint(plan)


# ---------------------------------------------------------------------------
# Persisted evidence artifacts.
#
# M5 hard gate: reconciliation must consume *persisted* evidence artifacts, not
# reconstruct state from "whatever happens to exist at the end of a job". The
# functions below read/write the artifacts deterministically so the reconciliation
# gate is reproducible and never a source of nondeterminism.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    """The persisted per-run execution artifact (M5-C).

    One artifact per verification run, containing every selected unit's recorded
    execution result. This is what ``verify.py reconcile`` reads — never the live
    process tree or the tail of a job log.
    """

    tier: str
    plan_fingerprint: str  # digest() of the plan this evidence corresponds to
    commit: str
    units: tuple[UnitExecution, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "vea5-execution-evidence/v1",
            "policy_version": POLICY_VERSION,
            "tier": self.tier,
            "plan_fingerprint": self.plan_fingerprint,
            "commit": self.commit,
            "units": [
                {
                    "unit_id": u.unit_id,
                    "status": u.status,
                    "exit_code": u.exit_code,
                    "evidence_ref": u.evidence_ref,
                }
                for u in self.units
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionEvidence:
        return cls(
            tier=data.get("tier", "unknown"),
            plan_fingerprint=data.get("plan_fingerprint", ""),
            commit=data.get("commit", "unknown"),
            units=tuple(
                UnitExecution(
                    unit_id=u["unit_id"],
                    status=u.get("status", "unknown"),
                    exit_code=u.get("exit_code"),
                    evidence_ref=u.get("evidence_ref"),
                )
                for u in data.get("units", [])
            ),
        )


def save_execution_evidence(evidence: ExecutionEvidence, path: Path | str) -> Path:
    """Persist the execution-evidence artifact so reconciliation can read it."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(evidence.to_dict(), indent=2) + "\n", encoding="utf-8")
    return p


def load_execution_evidence(path: Path | str) -> ExecutionEvidence:
    """Load a persisted execution-evidence artifact (deterministic input)."""
    return ExecutionEvidence.from_dict(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def execution_evidence_from_units(
    *,
    tier: str,
    plan_fingerprint_digest: str,
    commit: str,
    units: list[UnitExecution],
) -> ExecutionEvidence:
    return ExecutionEvidence(
        tier=tier,
        plan_fingerprint=plan_fingerprint_digest,
        commit=commit,
        units=tuple(units),
    )


def reconcile_from_artifacts(
    *,
    local_plan_path: Path | str,
    ci_plan_path: Path | str,
    local_evidence_path: Path | str | None = None,
    ci_evidence_path: Path | str | None = None,
    commit: str | None = None,
) -> ReconciliationReport:
    """Reconcile purely from persisted artifacts (the M5 CI path).

    No plan is generated and no execution result is reconstructed from the live
    job. Both plans and (optionally) execution evidence are read from files that
    were written by earlier, explicit steps. This keeps the gate deterministic.
    """
    local_plan = _load_plan_from_manifest(local_plan_path)
    ci_plan = _load_plan_from_manifest(ci_plan_path)

    local_results: dict[str, UnitExecution] = {}
    ci_results: dict[str, UnitExecution] = {}
    if local_evidence_path is not None:
        local_results = _unit_results_from_any_evidence(local_evidence_path)
    if ci_evidence_path is not None:
        ci_results = _unit_results_from_any_evidence(ci_evidence_path)

    return reconcile(
        local_plan,
        ci_plan,
        local_results=local_results,
        ci_results=ci_results,
        commit=commit,
    )


def validate_ci_artifacts(
    *,
    ci_plan_path: Path | str,
    ci_evidence_path: Path | str | None = None,
    commit: str | None = None,
) -> ReconciliationReport:
    """Validate a CI/PR plan against its own persisted execution evidence.

    Option A (the M5 CI gate): when no LOCAL side is supplied (``verify.py
    reconcile --plan X --evidence Y``), the gate must NOT produce
    ``environment-divergence`` merely because ``--local`` was omitted. Instead it
    validates the CI plan + evidence *internally*, deterministically:

      1. evidence fingerprint matches the supplied plan (else planning-divergence);
      2. every selected unit has an explicit evidence record (missing -> no-evidence);
      3. execution failures are preserved (status ``fail`` / ``exit_code != 0``);
      4. otherwise -> ``same-plan`` (exit 0).

    Missing evidence is never silently converted to PASS, and a genuine execution
    failure is never made to look successful. Malformed evidence is rejected
    (non-zero), not treated as PASS.
    """
    ci_plan = _load_plan_from_manifest(ci_plan_path)
    fp = plan_fingerprint(ci_plan)

    results: dict[str, UnitExecution] = {}
    if ci_evidence_path is not None:
        try:
            results = _unit_results_from_any_evidence(ci_evidence_path)
        except (
            Exception
        ) as exc:  # malformed / unreadable evidence -> reject, never PASS
            return _ci_report(
                ReconciliationClassification(
                    status=ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value,
                    reason=(
                        f"execution-evidence artifact is malformed or unreadable: {exc}"
                    ),
                    environment_diverges=True,
                ),
                fp,
                commit,
                {},
            )

    # 1. Evidence belongs to this plan (fingerprint consistency).
    if ci_evidence_path is not None:
        ev_fp = _evidence_plan_fingerprint(ci_evidence_path)
        if ev_fp and ev_fp != fp.digest():
            return _ci_report(
                ReconciliationClassification(
                    status=ReconciliationStatus.PLANNING_DIVERGENCE.value,
                    reason=(
                        "plan/evidence fingerprint mismatch: evidence was recorded for "
                        f"plan {ev_fp!r}, but the supplied plan is {fp.digest()!r}"
                    ),
                    planning_diverges=True,
                ),
                fp,
                commit,
                results,
            )

    # 2. Every selected unit has an explicit evidence record.
    missing = sorted(
        sel.unit_id for sel in ci_plan.selected if sel.unit_id not in results
    )
    no_evidence = sorted(
        sel.unit_id
        for sel in ci_plan.selected
        if sel.unit_id in results and results[sel.unit_id].status == "no-evidence"
    )
    if missing or no_evidence:
        gap_units = sorted(set(missing) | set(no_evidence))
        return _ci_report(
            ReconciliationClassification(
                status=ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value,
                reason=(
                    "CI plan selected units with no recorded evidence "
                    f"({', '.join(gap_units)}); no-evidence is explicit, never silently dropped"
                ),
                diverging_units=tuple(gap_units),
                environment_diverges=True,
            ),
            fp,
            commit,
            results,
        )

    # 3. Preserve execution failures.
    failed = sorted(
        sel.unit_id
        for sel in ci_plan.selected
        if results[sel.unit_id].status == "fail"
        or (results[sel.unit_id].exit_code or 0) != 0
    )
    if failed:
        return _ci_report(
            ReconciliationClassification(
                status=ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value,
                reason=(
                    "CI execution recorded failure for selected units ("
                    f"{', '.join(failed)})"
                ),
                diverging_units=tuple(failed),
                environment_diverges=True,
            ),
            fp,
            commit,
            results,
        )

    # 4. All selected units pass (or none are selected) -> success.
    return _ci_report(
        ReconciliationClassification(
            status=ReconciliationStatus.SAME_PLAN.value,
            reason="CI plan is consistent with complete passing execution evidence",
        ),
        fp,
        commit,
        results,
    )


def _ci_report(
    classification: ReconciliationClassification,
    fp: PlanFingerprint,
    commit: str | None,
    results: dict[str, UnitExecution],
) -> ReconciliationReport:
    """Build a ReconciliationReport for the CI-only (single-plan) path."""
    return ReconciliationReport(
        classification=classification,
        local_fingerprint=fp,
        ci_fingerprint=fp,
        change_set_local=fp.change_set,
        change_set_ci=fp.change_set,
        evidence_identity=build_evidence_identity(
            commit=commit or "unknown",
            change_set=fp.change_set,
            tier=fp.tier,
            plan_digest=fp.digest(),
            unit_executions=list(results.values()),
        ),
    )


def _load_plan_from_manifest(path: Path | str) -> TierPlan:
    """Load a TierPlan from the M2 manifest written by ``verify.py plan``."""
    from runtime.foundation.verification.tier import ExcludedUnit, SelectedUnit

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return TierPlan(
        tier=data["tier"],
        base_ref=data.get("base_ref"),
        head_ref=data["head_ref"],
        changed_files=tuple(data["changed_files"]),
        selected=tuple(SelectedUnit(**s) for s in data["selected"]),
        excluded=tuple(ExcludedUnit(**e) for e in data["excluded"]),
        estimated_seconds=data["estimated_seconds"],
        planner_version=data["planner_version"],
        framework_version=data["framework_version"],
    )


def save_reconciliation_report(report: ReconciliationReport, path: Path | str) -> Path:
    """Persist the reconciliation report (M5 evidence artifact)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")
    return p


def _unit_results_from_any_evidence(
    evidence_path: Path | str,
) -> dict[str, UnitExecution]:
    """Load a v1 or v2 evidence artifact and reduce it to the per-unit
    ``UnitExecution`` map that ``reconcile`` compares.

    M6: v2 artifacts carry fine-grained ``UnitExecutionRecord`` per unit; we take
    the primary status/exit of the last attempt. v1 artifacts already map
    one-to-one. This keeps reconciliation deterministic and backward-compatible.
    """
    from runtime.foundation.verification.evidence_contract import (
        load_execution_evidence_any,
    )

    ev = load_execution_evidence_any(evidence_path)
    # v2 artifact exposes records; v1 falls back to a flat units list via to_dict.
    units = ev.to_dict().get("units", [])
    results: dict[str, UnitExecution] = {}
    for u in units:
        if "attempts" in u:
            attempts = u["attempts"]
            last = attempts[-1]
            results[u["unit_id"]] = UnitExecution(
                unit_id=u["unit_id"],
                status=last.get("status", "unknown"),
                exit_code=last.get("exit_code"),
                evidence_ref=_first_artifact_ref(last),
            )
        else:
            results[u["unit_id"]] = UnitExecution(
                unit_id=u["unit_id"],
                status=u.get("status", "unknown"),
                exit_code=u.get("exit_code"),
                evidence_ref=u.get("evidence_ref"),
            )
    return results


def _evidence_plan_fingerprint(evidence_path: Path | str) -> str | None:
    """Return the plan digest recorded inside an evidence artifact, or None.

    Returns None when the artifact has no fingerprint (legacy) or cannot be read
    as evidence — in which case the consistency check is skipped defensively
    rather than failing on an unverifiable field.
    """
    from runtime.foundation.verification.evidence_contract import (
        load_execution_evidence_any,
    )

    try:
        ev = load_execution_evidence_any(evidence_path)
    except Exception:
        return None
    value = (getattr(ev, "plan_fingerprint", None) or "").strip()
    return value or None


def _first_artifact_ref(attempt: dict[str, Any]) -> str | None:
    for a in attempt.get("artifacts", []):
        if a.get("ref"):
            return a["ref"]
    return attempt.get("stdout_ref") or attempt.get("stderr_ref")


# ---------------------------------------------------------------------------
# JSON helper (order-stable).
# ---------------------------------------------------------------------------


def json_dumps_ordered(obj: Any) -> str:
    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


__all__ = [
    "POLICY_VERSION",
    "normalize_change_set",
    "change_set_fingerprint",
    "change_set_diff",
    "PlanFingerprint",
    "plan_fingerprint",
    "UnitExecution",
    "ExecutionEvidence",
    "ReconciliationClassification",
    "ReconciliationStatus",
    "ReconciliationReport",
    "build_evidence_identity",
    "reconcile",
    "reconcile_from_artifacts",
    "validate_ci_artifacts",
    "ci_fingerprint_from",
    "save_execution_evidence",
    "load_execution_evidence",
    "execution_evidence_from_units",
    "save_reconciliation_report",
]
