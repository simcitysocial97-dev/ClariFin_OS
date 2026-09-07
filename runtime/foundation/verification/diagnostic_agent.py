"""
M9-C42.30 — Diagnostic & Forensic Agent Foundation (M30.x).

Builds the Diagnostic & Forensic Agent on top of the *existing*
architecture. It consumes only canonical framework outputs:

    * ForensicExecutionRecord   (C42.28 — the canonical causal chain)
    * Correlation               (C42.27)
    * EvidenceAwarePlan         (C42.27)
    * ReconciledVerificationState (C42.28)

No unrelated autonomous-agent architecture is introduced. The first
version is *diagnostic*: it observes evidence and reaches conclusions;
it never modifies production code.

Responsibilities — the nine canonical questions
-----------------------------------------------
Q1  What changed?
Q2  What is affected?
Q3  What evidence remains valid?
Q4  What must actually run?            (planner-derived; never invented)
Q5  What was actually executed?
Q6  What happened?                     (classified outcomes)
Q7  What was NOT tested?
Q8  What remains uncertain?            (first-class output)
Q9  Is the repository state certifiable?

Verdict vocabulary (closed):
    CERTIFIABLE | NOT_CERTIFIABLE | CERTIFICATION_BLOCKED |
    INSUFFICIENT_EVIDENCE

Determinism contract: identical inputs produce byte-identical reports
(no wall-clock enters any decision field).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

DIAGNOSTIC_REPORT_SCHEMA = "m9-diagnostic-report/v1"

Verdict = Literal[
    "CERTIFIABLE",
    "NOT_CERTIFIABLE",
    "CERTIFICATION_BLOCKED",
    "INSUFFICIENT_EVIDENCE",
]

VERDICTS: tuple[Verdict, ...] = (
    "CERTIFIABLE",
    "NOT_CERTIFIABLE",
    "CERTIFICATION_BLOCKED",
    "INSUFFICIENT_EVIDENCE",
)

# First-class uncertainty taxonomy.
UncertaintyKind = Literal[
    "nondeterministic_mutation",
    "equivalent_mutant",
    "insufficient_test_surface",
    "stale_evidence",
    "incomplete_ci_evidence",
    "unmapped_capability",
    "ambiguous_behavior",
]

UNCERTAINTY_KINDS: tuple[UncertaintyKind, ...] = (
    "nondeterministic_mutation",
    "equivalent_mutant",
    "insufficient_test_surface",
    "stale_evidence",
    "incomplete_ci_evidence",
    "unmapped_capability",
    "ambiguous_behavior",
)


# ===========================================================================
# Forensic record validation — no stage may silently disappear
# ===========================================================================

CAUSAL_CHAIN_STAGES: tuple[str, ...] = (
    "change",  # repository state -> detected changes
    "affected_graph_nodes",  # affected source/components/capabilities
    "invalidations",  # invalidated evidence
    "reused_evidence",  # reusable evidence
    "selected_tasks",  # planner decision
    "executed_tasks",  # executable/executed tasks
    "execution_results",  # execution results
    "new_evidence",  # fresh evidence
    "derived_evidence",  # derived evidence
    "failures",  # classified outcomes
    "uncertainties",  # unresolved uncertainty
    "certification_decision",  # certification conclusion
)

STAGE_NOTES: dict[str, str] = {
    "change": "detected changes (files/kinds)",
    "affected_graph_nodes": "affected sources/capabilities resolved via the graph",
    "invalidations": "evidence invalidated under the C42.27 rule set",
    "reused_evidence": "prior evidence reused after fingerprint validation",
    "selected_tasks": "the planner's minimum defensible selection",
    "executed_tasks": "tasks actually dispatched by the executor",
    "execution_results": "per-task execution outcomes",
    "new_evidence": "freshly measured evidence",
    "derived_evidence": "mathematically derived aggregates",
    "failures": "failures classified by the closed taxonomy",
    "uncertainties": "residual uncertainty (first-class)",
    "certification_decision": "final defensible verdict",
}


@dataclass(frozen=True, slots=True)
class StageValidation:
    stage: str
    present: bool
    explicitly_empty: bool
    detail: str


@dataclass(frozen=True, slots=True)
class RecordValidation:
    record_id: str
    stages: tuple[StageValidation, ...]
    complete: bool

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(s.stage for s in self.stages if not s.present)

    @property
    def silently_empty(self) -> tuple[str, ...]:
        """Stages present but empty without an explicit reason."""
        return tuple(
            s.stage
            for s in self.stages
            if s.present
            and not s.explicitly_empty
            and "without explicit reason" in s.detail
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "complete": self.complete,
            "missing": list(self.missing),
            "silently_empty": list(self.silently_empty),
            "stages": [
                {
                    "stage": s.stage,
                    "present": s.present,
                    "explicitly_empty": s.explicitly_empty,
                    "detail": s.detail,
                }
                for s in self.stages
            ],
        }


def _stage_has_content(value: Any) -> bool:
    if not isinstance(value, dict):
        return bool(value)
    for k, v in value.items():
        if k == "empty_because":
            continue
        if isinstance(v, (list, dict)) and len(v) > 0:
            return True
        if isinstance(v, (str, int, float, bool)) and v != "":
            return True
    return False


# Deterministic, stage-appropriate explanations injected when a stage is
# legitimately empty. This is the *promotion* of the C42.28 forensic
# record into the canonical agent I/O contract: no stage may silently
# disappear — absence must always be explained.
DEFAULT_EMPTY_REASONS: dict[str, str] = {
    "change": "no repository changes detected",
    "affected_graph_nodes": "no graph nodes affected by this change set",
    "invalidations": "no evidence was invalidated under the rule set",
    "reused_evidence": "no prior evidence was reused",
    "selected_tasks": "planner selected no tasks",
    "executed_tasks": "no tasks were dispatched for execution",
    "execution_results": "no task produced an execution result",
    "new_evidence": "no fresh evidence was measured",
    "derived_evidence": "no aggregate was derived",
    "failures": "nothing failed",
    "uncertainties": "no residual uncertainty was recorded",
    "certification_decision": "no decision was reached",
}


def canonicalize_forensic_record(record_dict: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical copy of a forensic record in which every stage
    is either populated or carries an explicit ``empty_because`` marker.

    The original record dict is never mutated. Missing stages are NOT
    fabricated — they remain absent so validation reports them.
    """
    out = dict(record_dict)
    for stage in CAUSAL_CHAIN_STAGES:
        if stage not in out:
            continue
        value = out[stage]
        if isinstance(value, dict) and not _stage_has_content(value):
            if not value.get("empty_because"):
                out[stage] = {
                    **value,
                    "empty_because": DEFAULT_EMPTY_REASONS.get(
                        stage, "nothing to record for this stage"
                    ),
                }
        elif not value:
            out[stage] = {
                "empty_because": DEFAULT_EMPTY_REASONS.get(
                    stage, "nothing to record for this stage"
                )
            }
    return out


def validate_forensic_record(record_dict: dict[str, Any]) -> RecordValidation:
    """Validate the complete causal chain of a ForensicExecutionRecord.

    Every stage in CAUSAL_CHAIN_STAGES must be present. A stage may be
    legitimately empty (e.g. no failures), but then it must carry the
    explicit marker ``{"empty_because": "<reason>"}`` — silent absence
    is a violation.
    """
    validations: list[StageValidation] = []
    for stage in CAUSAL_CHAIN_STAGES:
        if stage not in record_dict:
            validations.append(
                StageValidation(stage, False, False, "stage missing from record")
            )
            continue
        value = record_dict[stage]
        if isinstance(value, dict):
            marker = value.get("empty_because")
            has_content = _stage_has_content(value)
            if has_content:
                validations.append(
                    StageValidation(stage, True, False, STAGE_NOTES[stage])
                )
            elif marker:
                validations.append(
                    StageValidation(stage, True, True, f"explicitly empty: {marker}")
                )
            else:
                validations.append(
                    StageValidation(
                        stage,
                        True,
                        False,
                        "stage present but empty without explicit reason",
                    )
                )
        elif value:
            validations.append(StageValidation(stage, True, False, STAGE_NOTES[stage]))
        else:
            validations.append(StageValidation(stage, True, False, "falsy stage value"))
    missing = tuple(v.stage for v in validations if not v.present)
    silent = tuple(
        v.stage
        for v in validations
        if v.present
        and not v.explicitly_empty
        and "without explicit reason" in v.detail
    )
    return RecordValidation(
        record_id=str(record_dict.get("record_id", "")),
        stages=tuple(validations),
        complete=not missing and not silent,
    )


# ===========================================================================
# Diagnostic report — the nine canonical questions
# ===========================================================================


@dataclass(frozen=True, slots=True)
class Uncertainty:
    kind: UncertaintyKind
    subject: str
    detail: str
    gates_certification: bool
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "subject": self.subject,
            "detail": self.detail,
            "gates_certification": self.gates_certification,
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True, slots=True)
class Explainability:
    """Mandatory answers attached to every certification decision."""

    why_did_you_run_this: str
    why_did_you_not_run_that: str
    which_evidence_did_you_reuse: str
    why_was_that_evidence_still_valid: str
    what_evidence_became_invalid: str
    what_failed: str
    was_the_failure_actually_a_verification_failure: str
    what_remains_unverified: str
    what_prevents_certification: str

    def to_dict(self) -> dict[str, str]:
        return {
            "why_did_you_run_this": self.why_did_you_run_this,
            "why_did_you_not_run_that": self.why_did_you_not_run_that,
            "which_evidence_did_you_reuse": self.which_evidence_did_you_reuse,
            "why_was_that_evidence_still_valid": self.why_was_that_evidence_still_valid,
            "what_evidence_became_invalid": self.what_evidence_became_invalid,
            "what_failed": self.what_failed,
            "was_the_failure_actually_a_verification_failure": (
                self.was_the_failure_actually_a_verification_failure
            ),
            "what_remains_unverified": self.what_remains_unverified,
            "what_prevents_certification": self.what_prevents_certification,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticReport:
    """The agent's complete, deterministic answer set."""

    schema: str
    report_id: str
    source_record_id: str
    repository_sha: str
    generated_at: str

    q1_what_changed: dict[str, Any]
    q2_what_is_affected: dict[str, Any]
    q3_valid_evidence: dict[str, Any]
    q4_required_execution: dict[str, Any]
    q5_actual_execution: dict[str, Any]
    q6_what_happened: dict[str, Any]
    q7_what_was_not_tested: dict[str, Any]
    q8_uncertainties: tuple[Uncertainty, ...]
    q9_verdict: dict[str, Any]

    record_validation: RecordValidation
    explainability: Explainability

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "report_id": self.report_id,
            "source_record_id": self.source_record_id,
            "repository_sha": self.repository_sha,
            "generated_at": self.generated_at,
            "q1_what_changed": self.q1_what_changed,
            "q2_what_is_affected": self.q2_what_is_affected,
            "q3_valid_evidence": self.q3_valid_evidence,
            "q4_required_execution": self.q4_required_execution,
            "q5_actual_execution": self.q5_actual_execution,
            "q6_what_happened": self.q6_what_happened,
            "q7_what_was_not_tested": self.q7_what_was_not_tested,
            "q8_uncertainties": [u.to_dict() for u in self.q8_uncertainties],
            "q9_verdict": self.q9_verdict,
            "record_validation": self.record_validation.to_dict(),
            "explainability": self.explainability.to_dict(),
        }

    def decision_fingerprint(self) -> str:
        """Deterministic identity of every *decision* field."""
        d = self.to_dict()
        d.pop("generated_at", None)
        d.pop("report_id", None)
        return hashlib.sha256(
            json.dumps(d, sort_keys=True, default=str).encode()
        ).hexdigest()


# ===========================================================================
# The agent
# ===========================================================================


class DiagnosticForensicAgent:
    """Consumes canonical artifacts; produces deterministic diagnoses.

    The agent NEVER invents verification scope: Q4 is answered strictly
    from the planner decisions captured in the forensic record.
    """

    def __init__(
        self,
        *,
        population_components: tuple[str, ...] = (),
    ) -> None:
        if not population_components:
            from runtime.foundation.verification.evidence_reuse import (
                C42_26_COMPONENTS,
            )

            population_components = C42_26_COMPONENTS
        self._population = tuple(population_components)

    # -- main entry -------------------------------------------------------

    def diagnose(
        self,
        record: dict[str, Any],
        *,
        ci_correlation: dict[str, Any] | None = None,
    ) -> DiagnosticReport:
        """Produce the nine-question report from a ForensicExecutionRecord.

        ``ci_correlation`` optionally carries validated CI evidence
        (ingested records + reuse decisions) produced by C42.29; it
        feeds Q3/Q5/Q8 exactly like local evidence.
        """
        record = canonicalize_forensic_record(record)
        validation = validate_forensic_record(record)

        q1 = self._answer_q1(record)
        q2 = self._answer_q2(record)
        q3 = self._answer_q3(record, ci_correlation=ci_correlation)
        q4 = self._answer_q4(record)
        q5 = self._answer_q5(record, ci_correlation=ci_correlation)
        q6 = self._answer_q6(record, ci_correlation=ci_correlation)
        q7 = self._answer_q7(record, q3=q3, q4=q4, q5=q5)
        q8 = self._answer_q8(record, q3=q3, q6=q6, ci_correlation=ci_correlation)
        q9, explain = self._answer_q9(
            record,
            validation=validation,
            q3=q3,
            q4=q4,
            q5=q5,
            q6=q6,
            q7=q7,
            q8=q8,
            q1=q1,
            q2=q2,
        )

        rid_src = "|".join(
            [
                str(record.get("record_id", "")),
                q9["verdict"],
                str(len(q8)),
            ]
        )
        return DiagnosticReport(
            schema=DIAGNOSTIC_REPORT_SCHEMA,
            report_id=f"diag::{hashlib.sha256(rid_src.encode()).hexdigest()[:12]}",
            source_record_id=str(record.get("record_id", "")),
            repository_sha=str(record.get("repository_sha", "")),
            generated_at=datetime.now(UTC).isoformat(),
            q1_what_changed=q1,
            q2_what_is_affected=q2,
            q3_valid_evidence=q3,
            q4_required_execution=q4,
            q5_actual_execution=q5,
            q6_what_happened=q6,
            q7_what_was_not_tested=q7,
            q8_uncertainties=tuple(q8),
            q9_verdict=q9,
            record_validation=validation,
            explainability=explain,
        )

    # -- Q1 ----------------------------------------------------------------

    def _answer_q1(self, record: dict[str, Any]) -> dict[str, Any]:
        change = record.get("change", {})
        files = change.get("changed_files", [])
        kinds = {
            "source": [f for f in files if f.startswith("backend/src/")],
            "test": [f for f in files if f.startswith("backend/tests/")],
            "config": [
                f
                for f in files
                if f.endswith(".toml") or f.endswith(".cfg") or ".github/" in f
            ],
            "verification_infrastructure": [
                f
                for f in files
                if f.startswith("runtime/foundation/verification/")
                or f.startswith(".github/workflows/")
            ],
            "dependency_toolchain": [
                f
                for f in files
                if f in ("pyproject.toml", "backend/pyproject.toml")
                or "requirements" in f
            ],
            "other": [
                f
                for f in files
                if not f.startswith(
                    ("backend/src/", "backend/tests/", "runtime/", ".github/")
                )
                and not f.endswith((".toml", ".cfg"))
            ],
        }
        return {
            "file_count": len(files),
            "files_by_kind": kinds,
            "changed_components": change.get("affected_components", []),
            "changed_capabilities": change.get("affected_capabilities", []),
        }

    # -- Q2 ----------------------------------------------------------------

    def _answer_q2(self, record: dict[str, Any]) -> dict[str, Any]:
        affected = record.get("affected_graph_nodes", {})
        change = record.get("change", {})
        return {
            "sources": affected.get("sources", []),
            "components": change.get("affected_components", []),
            "capabilities": change.get("affected_capabilities", []),
            "affected_verification_tasks": record.get("selected_tasks", {}).get(
                "components", []
            ),
            "affected_evidence": sorted(
                (record.get("invalidations", {}).get("by_component", {}) or {}).keys()
            ),
        }

    # -- Q3 ----------------------------------------------------------------

    def _answer_q3(
        self,
        record: dict[str, Any],
        *,
        ci_correlation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        invalidations = (record.get("invalidations", {}) or {}).get("by_component", {})
        invalidated = sorted(k for k, v in invalidations.items() if v)
        reused = (record.get("reused_evidence", {}) or {}).get("components", [])
        fresh = (record.get("new_evidence", {}) or {}).get("components", [])

        revalidated = []
        for comp, ev in (
            (record.get("execution_results", {}) or {}).get("by_component", {}).items()
        ):
            if ev.get("failure_kind") is None and ev.get("exit_code") == 0:
                revalidated.append(comp)

        ci_reused: list[str] = []
        ci_unavailable: list[dict[str, str]] = []
        if ci_correlation:
            for entry in ci_correlation.get("records", []):
                if entry.get("disposition") == "reusable":
                    ci_reused.append(
                        entry.get("component") or entry.get("record_id", "")
                    )
                elif entry.get("reusable") is False:
                    ci_unavailable.append(
                        {
                            "record_id": entry.get("record_id", ""),
                            "reason": "; ".join(entry.get("reasons", [])),
                        }
                    )

        known = set(reused) | set(fresh) | set(invalidated) | set(ci_reused)
        unavailable = [c for c in self._population if c not in known]
        return {
            "reused": reused,
            "revalidated": sorted(set(revalidated)),
            "invalidated": invalidated,
            "unavailable": unavailable,
            "ci_reused": ci_reused,
            "ci_unavailable": ci_unavailable,
        }

    # -- Q4 ----------------------------------------------------------------

    def _answer_q4(self, record: dict[str, Any]) -> dict[str, Any]:
        selected = record.get("selected_tasks", {})
        excluded = record.get("_excluded_tasks", {})
        return {
            "authority": "EvidenceAwarePlanner (C42.27) — agent never invents scope",
            "required_tasks": selected.get("components", []),
            "task_count": selected.get("count", 0),
            "excluded_by_planner": (
                excluded.get("components", []) if isinstance(excluded, dict) else []
            ),
        }

    # -- Q5 ----------------------------------------------------------------

    def _answer_q5(
        self,
        record: dict[str, Any],
        *,
        ci_correlation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        executed = record.get("executed_tasks", {})
        results = (record.get("execution_results", {}) or {}).get("by_component", {})

        planned = set(record.get("selected_tasks", {}).get("components", []))
        executed_set = set(executed.get("components", []))
        failed = sorted(c for c, ev in results.items() if ev.get("failure_kind"))
        skipped = sorted(planned - executed_set - set(failed))

        blocked = sorted(
            c
            for c, ev in results.items()
            if ev.get("failure_kind") in ("scope_failure", "configuration_failure")
        )
        ci_executed = []
        if ci_correlation:
            ci_executed = [
                r.get("component") or r.get("record_id", "")
                for r in ci_correlation.get("records", [])
                if r.get("executed")
            ]
        return {
            "planned_count": len(planned),
            "executable_count": record.get("executed_tasks", {}).get("count", 0),
            "executed": sorted(executed_set),
            "skipped": skipped,
            "blocked": blocked,
            "failed": failed,
            "ci_executed": ci_executed,
        }

    # -- Q6 ----------------------------------------------------------------

    def _answer_q6(
        self,
        record: dict[str, Any],
        *,
        ci_correlation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        failures = record.get("failures", {}) or {}
        by_component = failures.get("by_component", {})
        by_kind: dict[str, list[str]] = {}
        for comp, info in by_component.items():
            kind = info.get("kind") or "unclassified"
            by_kind.setdefault(kind, []).append(comp)
        if ci_correlation:
            for entry in ci_correlation.get("records", []):
                fk = entry.get("failure_classification")
                if fk:
                    subj = entry.get("component") or entry.get("record_id", "")
                    by_kind.setdefault(fk, []).append(subj)
        return {
            "failure_count": failures.get("count", 0)
            + sum(len(v) for v in by_kind.values())
            - failures.get("count", 0),
            "by_kind": by_kind,
            "machine_readable_distinctions": {
                "verification_failure": "verification ran and found a defect",
                "infrastructure_failure": "verification could not execute correctly",
                "evidence_failure": "execution occurred but evidence could not be captured",
                "scope_failure": "executor exceeded authorized scope",
                "configuration_failure": "task not representable under current configuration",
                "certification_failure": "criteria unsatisfied despite complete evidence",
            },
        }

    # -- Q7 ----------------------------------------------------------------

    def _answer_q7(
        self,
        record: dict[str, Any],
        *,
        q3: dict[str, Any],
        q4: dict[str, Any],
        q5: dict[str, Any],
    ) -> dict[str, Any]:
        executed_and_selected = (
            set(q5["executed"]) | set(q3["reused"]) | set(q3["revalidated"])
        )
        outside_population = sorted(
            set(record.get("selected_tasks", {}).get("components", []))
            - set(self._population)
        )
        deferred = sorted(set(q5["skipped"]))
        blocked = sorted(set(q5["blocked"]))
        return {
            "excluded_capabilities": q4.get("excluded_by_planner", []),
            "covered_by_reused_evidence": q3["reused"] + q3["ci_reused"],
            # M9-C46: wire the previously-dead `executed_and_selected` set into
            # the Q7 answer (incomplete integration — the set was computed but
            # never surfaced). Additive key; existing consumers unaffected.
            "executed_and_selected_components": sorted(executed_and_selected),
            "unavailable_evidence": q3["unavailable"]
            + [u.get("record_id") for u in q3["ci_unavailable"]],
            "deferred_components": deferred,
            "outside_population_components": outside_population,
            "blocked_tasks": blocked,
        }

    # -- Q8 ----------------------------------------------------------------

    def _answer_q8(
        self,
        record: dict[str, Any],
        *,
        q3: dict[str, Any],
        q6: dict[str, Any],
        ci_correlation: dict[str, Any] | None = None,
    ) -> list[Uncertainty]:
        found: list[Uncertainty] = []

        rec_unc = record.get("uncertainties", {}) or {}
        for comp in rec_unc.get("no_evidence", []):
            found.append(
                Uncertainty(
                    "insufficient_test_surface",
                    comp,
                    "no prior measurement and no fresh evidence exists",
                    gates_certification=True,
                    recommendation="measure the component before certifying",
                )
            )
        for comp in rec_unc.get("invalidated", []):
            found.append(
                Uncertainty(
                    "stale_evidence",
                    comp,
                    "prior evidence invalidated and not yet replaced by fresh measurement",
                    gates_certification=True,
                    recommendation="run the planner-selected targeted verification",
                )
            )
        for blocker in rec_unc.get("drift_blockers", []):
            found.append(
                Uncertainty(
                    "unmapped_capability",
                    blocker,
                    "graph-level drift: declared coverage unreachable by executable surface",
                    gates_certification=True,
                    recommendation="repair the capability mapping before certification",
                )
            )

        results = (record.get("execution_results", {}) or {}).get("by_component", {})
        for comp, ev in results.items():
            counts = ev.get("counts") or {}
            no_tests = int(counts.get("no_tests", 0) or 0)
            suspicious = int(counts.get("suspicious", 0) or 0)
            notes = str(ev.get("notes", ""))
            if no_tests:
                found.append(
                    Uncertainty(
                        "insufficient_test_surface",
                        comp,
                        f"{no_tests} mutant(s) had no covering test",
                        gates_certification=False,
                        recommendation=(
                            "behavioral gap: consider evidence-driven test "
                            "strengthening (C42.31); do NOT chase score blindly"
                        ),
                    )
                )
            if "equivalent" in notes.lower():
                found.append(
                    Uncertainty(
                        "equivalent_mutant",
                        comp,
                        "survivor(s) classified equivalent/observable-equivalent",
                        gates_certification=False,
                        recommendation="preserve; do not target artificially",
                    )
                )
            if suspicious:
                found.append(
                    Uncertainty(
                        "nondeterministic_mutation",
                        comp,
                        f"{suspicious} suspicious outcome(s) — possible nondeterminism",
                        gates_certification=False,
                        recommendation="re-run the specific mutants before interpreting",
                    )
                )

        if ci_correlation:
            for entry in ci_correlation.get("records", []):
                if (
                    not entry.get("reusable", True)
                    and entry.get("failure_classification") == "evidence_failure"
                ):
                    found.append(
                        Uncertainty(
                            "incomplete_ci_evidence",
                            entry.get("record_id", ""),
                            "; ".join(entry.get("reasons", []))
                            or "CI artifact unusable",
                            gates_certification=True,
                            recommendation="repair CI artifact capture before relying on it",
                        )
                    )

        # Deterministic ordering.
        found.sort(key=lambda u: (u.kind, u.subject))
        return found

    # -- Q9 ----------------------------------------------------------------

    def _answer_q9(
        self,
        record: dict[str, Any],
        *,
        validation: RecordValidation,
        q1: dict[str, Any],
        q2: dict[str, Any],
        q3: dict[str, Any],
        q4: dict[str, Any],
        q5: dict[str, Any],
        q6: dict[str, Any],
        q7: dict[str, Any],
        q8: list[Uncertainty],
    ) -> tuple[dict[str, Any], Explainability]:
        decision = record.get("certification_decision", {}) or {}
        reasons: list[str] = []

        gating = [u for u in q8 if u.gates_certification]
        ver_failures = q6["by_kind"].get("verification_failure", [])
        infra_failures = q6["by_kind"].get("infrastructure_failure", [])
        evidence_failures = q6["by_kind"].get("evidence_failure", [])
        scope_failures = q6["by_kind"].get("scope_failure", [])

        drift_blockers = [u for u in q8 if u.kind == "unmapped_capability"]

        if not validation.complete:
            verdict: Verdict = "INSUFFICIENT_EVIDENCE"
            reasons.append(
                "forensic record is incomplete: missing="
                f"{list(validation.missing)} silently_empty={list(validation.silently_empty)}"
            )
        elif drift_blockers:
            verdict = "CERTIFICATION_BLOCKED"
            reasons.append(
                f"{len(drift_blockers)} discovery-drift blocker(s): "
                + "; ".join(b.subject for b in drift_blockers[:3])
            )
        elif scope_failures:
            verdict = "CERTIFICATION_BLOCKED"
            reasons.append("scope enforcement blocked execution")
        elif ver_failures:
            # A genuine verification failure is definitive: defects were
            # detected. This outranks residual insufficiency.
            verdict = "NOT_CERTIFIABLE"
            reasons.append(f"verification failure(s) in {', '.join(ver_failures)}")
        elif evidence_failures:
            verdict = "NOT_CERTIFIABLE"
            reasons.append(
                f"evidence could not be captured/reconciled for {', '.join(evidence_failures)}"
            )
        elif gating:
            verdict = "INSUFFICIENT_EVIDENCE"
            reasons.extend(f"{u.subject}: {u.detail}" for u in gating[:5])
        elif infra_failures:
            verdict = "INSUFFICIENT_EVIDENCE"
            reasons.append(
                "infrastructure failure prevented verification of "
                f"{', '.join(infra_failures)}; repair infrastructure and re-plan"
            )
        else:
            verdict = "CERTIFIABLE"
            reasons.append(decision.get("rationale") or "all required evidence valid")

        # Explainability — mandatory answers.
        explain = Explainability(
            why_did_you_run_this=(
                f"planner selected {q4['task_count']} task(s): "
                + ", ".join(q4["required_tasks"])
                + "; these were invalidated by the change or lacked evidence"
                if q4["task_count"]
                else "nothing required execution; every component had valid evidence"
            ),
            why_did_you_not_run_that=(
                f"{len(q3['reused'])} component(s) had reusable evidence with "
                "intact fingerprints; running them would violate the "
                "minimum-defensible-execution principle"
            ),
            which_evidence_did_you_reuse=(
                ", ".join(q3["reused"] + q3["ci_reused"]) or "none"
            ),
            why_was_that_evidence_still_valid=(
                "no invalidation rule fired: source/test/config/toolchain/"
                "population fingerprints unchanged since measurement"
                if (q3["reused"] or q3["ci_reused"])
                else "n/a"
            ),
            what_evidence_became_invalid=(", ".join(q3["invalidated"]) or "none"),
            what_failed=(
                "; ".join(
                    f"{kind}: {', '.join(components)}"
                    for kind, components in q6["by_kind"].items()
                )
                or "nothing failed"
            ),
            was_the_failure_actually_a_verification_failure=(
                (
                    f"mixed — verification failures in {', '.join(ver_failures)}; "
                    "the remaining failures are infrastructure/evidence "
                    "problems, not product defects"
                )
                if ver_failures and (infra_failures or evidence_failures)
                else (
                    "yes — verification executed and detected defects"
                    if ver_failures
                    else (
                        "no — infrastructure/evidence problem, not a product defect"
                        if (infra_failures or evidence_failures)
                        else "no failures occurred"
                    )
                )
            ),
            what_remains_unverified=(
                "; ".join(
                    filter(
                        None,
                        [
                            ", ".join(q7["deferred_components"])
                            and f"deferred: {', '.join(q7['deferred_components'])}",
                            ", ".join(q7["unavailable_evidence"])
                            and f"no evidence: {', '.join(map(str, q7['unavailable_evidence']))}",
                        ],
                    )
                )
                or "nothing within scope remains unverified"
            ),
            what_prevents_certification=(
                "; ".join(reasons) if verdict != "CERTIFIABLE" else "nothing"
            ),
        )

        return (
            {
                "verdict": verdict,
                "rationale": "; ".join(reasons),
                "prior_decision": decision,
                "aggregate_label": decision.get("aggregate_label"),
                "aggregate_result": decision.get("aggregate_result"),
                "deterministic": True,
            },
            explain,
        )


__all__ = [
    "CAUSAL_CHAIN_STAGES",
    "DEFAULT_EMPTY_REASONS",
    "DIAGNOSTIC_REPORT_SCHEMA",
    "DiagnosticForensicAgent",
    "DiagnosticReport",
    "Explainability",
    "RecordValidation",
    "UNCERTAINTY_KINDS",
    "Uncertainty",
    "UncertaintyKind",
    "VERDICTS",
    "canonicalize_forensic_record",
    "validate_forensic_record",
]
