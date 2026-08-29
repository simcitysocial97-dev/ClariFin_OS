"""
M9-C42.27 — M27.4 Evidence Reuse, Population Snapshots, and Measurement
Invalidation Rules.

The single most important architectural outcome of C42.27 is that
*previously generated evidence can be deterministically reused when
its validity conditions remain satisfied*. This module formalises
the four reuse primitives the framework distinguishes:

    * PopulationSnapshot   — the set of components under test
    * ComponentMeasurement — one component's measurement evidence
    * DerivedAggregate     — a result computed from authoritative
                             component measurements
    * EvidenceReuse        — a decision that an existing measurement
                             remains valid for a new repository state
    * MeasurementInvalidation — the conditions under which evidence
                                must be re-measured

Pure logic. Deterministic. The invalidation rules are enumerated
explicitly and never guessed; the classifier is a pure function so
it can be unit tested.

Invalidation taxonomy (per Phase 5 — M27.4):
    INVALIDATES_COMPONENT  — evidence for a specific component is dead
    INVALIDATES_CAPABILITY — evidence for an entire capability is dead
    INVALIDATES_TASK       — a single task's evidence is dead
    INVALIDATES_EVIDENCE_ONLY — only this specific evidence is dead
    DOES_NOT_INVALIDATE    — evidence remains valid
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Population snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PopulationSnapshot:
    """A frozen set of components under verification."""

    population_id: str
    created_at: str
    components: tuple[str, ...]
    component_fingerprints: dict[str, str] = field(default_factory=dict)
    config_hash: str = ""
    toolchain_hash: str = ""
    repository_sha: str = ""
    notes: str = ""

    def contains(self, component: str) -> bool:
        return component in self.components

    def fingerprint(self) -> str:
        parts = [self.population_id, self.config_hash, self.toolchain_hash]
        for c in sorted(self.components):
            parts.append(c)
            parts.append(self.component_fingerprints.get(c, ""))
        return hashlib.sha256("\n".join(parts).encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "population_id": self.population_id,
            "created_at": self.created_at,
            "components": list(self.components),
            "component_fingerprints": dict(self.component_fingerprints),
            "config_hash": self.config_hash,
            "toolchain_hash": self.toolchain_hash,
            "repository_sha": self.repository_sha,
            "notes": self.notes,
            "population_fingerprint": self.fingerprint(),
        }


# ---------------------------------------------------------------------------
# Component measurement — what was actually measured
# ---------------------------------------------------------------------------

MeasurementKind = Literal["mutation", "coverage", "contract", "unit", "static"]


@dataclass(frozen=True, slots=True)
class ComponentMeasurement:
    """One component's measurement record."""

    measurement_id: str
    component: str
    population_id: str
    kind: MeasurementKind
    run_id: str
    measured_at: str
    repository_sha: str
    source_fingerprint: str  # fingerprint of mutated source
    test_fingerprint: str  # fingerprint of test surface
    config_hash: str
    toolchain_hash: str
    summary: dict[str, float | int | str | None] = field(default_factory=dict)
    notes: str = ""

    def fingerprint(self) -> str:
        parts = (
            self.measurement_id,
            self.component,
            self.population_id,
            self.kind,
            self.source_fingerprint,
            self.test_fingerprint,
            self.config_hash,
            self.toolchain_hash,
            self.repository_sha,
        )
        return hashlib.sha256("\n".join(parts).encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "measurement_id": self.measurement_id,
            "component": self.component,
            "population_id": self.population_id,
            "kind": self.kind,
            "run_id": self.run_id,
            "measured_at": self.measured_at,
            "repository_sha": self.repository_sha,
            "source_fingerprint": self.source_fingerprint,
            "test_fingerprint": self.test_fingerprint,
            "config_hash": self.config_hash,
            "toolchain_hash": self.toolchain_hash,
            "summary": dict(self.summary),
            "notes": self.notes,
            "measurement_fingerprint": self.fingerprint(),
        }


# ---------------------------------------------------------------------------
# Derived aggregate
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DerivedAggregate:
    """A measurement derived from authoritative component measurements."""

    aggregate_id: str
    scope_id: str
    measurement_kind: MeasurementKind
    population_id: str
    component_measurement_ids: tuple[str, ...]
    formula: str  # e.g. "sum(killed)/sum(scored)"
    result: float
    decided_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    rationale: str = ""

    def to_dict(self) -> dict:
        return {
            "aggregate_id": self.aggregate_id,
            "scope_id": self.scope_id,
            "measurement_kind": self.measurement_kind,
            "population_id": self.population_id,
            "component_measurement_ids": list(self.component_measurement_ids),
            "formula": self.formula,
            "result": self.result,
            "decided_at": self.decided_at,
            "rationale": self.rationale,
        }


# ---------------------------------------------------------------------------
# Evidence reuse decision
# ---------------------------------------------------------------------------

ReuseDisposition = Literal[
    "reusable",  # measurement is still valid
    "reusable_with_revalidation",  # same config/source, but new run recommended
    "reusable_aggregate",  # aggregate derived from valid components
    "stale",  # evidence is old but not invalidated
    "invalidated_component",  # source/config changed for this component
    "invalidated_capability",  # capability-level invalidation
    "invalidated_task",  # only this specific task's evidence
    "invalidated_evidence_only",  # only this specific evidence record
    "no_evidence",  # no prior evidence exists
]


@dataclass(frozen=True, slots=True)
class EvidenceReuse:
    """A decision that an existing measurement can (or cannot) be reused."""

    reuse_id: str
    scope_id: str
    scope_kind: Literal["component", "capability", "population", "task"]
    disposition: ReuseDisposition
    measurement_id: str | None
    population_id: str | None
    invalidations: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    decided_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        return {
            "reuse_id": self.reuse_id,
            "scope_id": self.scope_id,
            "scope_kind": self.scope_kind,
            "disposition": self.disposition,
            "measurement_id": self.measurement_id,
            "population_id": self.population_id,
            "invalidations": list(self.invalidations),
            "reasons": list(self.reasons),
            "decided_at": self.decided_at,
        }


# ---------------------------------------------------------------------------
# Invalidation taxonomy
# ---------------------------------------------------------------------------

InvalidationScope = Literal[
    "INVALIDATES_COMPONENT",
    "INVALIDATES_CAPABILITY",
    "INVALIDATES_TASK",
    "INVALIDATES_EVIDENCE_ONLY",
    "DOES_NOT_INVALIDATE",
]


@dataclass(frozen=True, slots=True)
class InvalidationRule:
    """One rule in the invalidation taxonomy.

    Each rule has a deterministic evaluator. The set of rules is
    enumerated; the evaluator is the only place decisions are made.
    """

    rule_id: str
    description: str
    category: Literal[
        "source",
        "test",
        "config",
        "toolchain",
        "dependency",
        "population",
        "capability_mapping",
        "evidence_schema",
        "environment",
        "infrastructure",
    ]
    scope: InvalidationScope
    # The evaluator is a callable registered in the rule table below.
    # It receives a `Change` describing the current repository delta
    # and a `Measurement` describing the prior evidence, and returns
    # True if the change invalidates the measurement at this scope.


@dataclass(frozen=True, slots=True)
class Change:
    """A single change delta being evaluated."""

    kind: str  # source_change, test_change, config_change, ...
    target: str  # the component / file / capability being changed
    fingerprint_before: str = ""
    fingerprint_after: str = ""


# ---------------------------------------------------------------------------
# Invalidation rules — enumerated, never guessed
# ---------------------------------------------------------------------------

INVALIDATION_RULES: list[InvalidationRule] = [
    # Source changes invalidate the specific component (not the whole
    # capability) so unrelated engines can reuse prior measurement.
    InvalidationRule(
        rule_id="R-SRC-001",
        description="Production source change for component X invalidates "
        "evidence only for X (other components unaffected).",
        category="source",
        scope="INVALIDATES_COMPONENT",
    ),
    InvalidationRule(
        rule_id="R-SRC-002",
        description="Production source change inside a shared module used "
        "by multiple capabilities invalidates the capability-level "
        "evidence (transitive impact).",
        category="source",
        scope="INVALIDATES_CAPABILITY",
    ),
    InvalidationRule(
        rule_id="R-SRC-003",
        description="Source change to a test file (e.g. strengthening) "
        "invalidates the test evidence only, not production measurement.",
        category="test",
        scope="INVALIDATES_EVIDENCE_ONLY",
    ),
    InvalidationRule(
        rule_id="R-CFG-001",
        description="Mutation config or selection config change "
        "invalidates the affected task's evidence only.",
        category="config",
        scope="INVALIDATES_TASK",
    ),
    (
        InvalidationRule(
            rule_id="R-CFG-002",
            description="Toolchain version change (mutmut/pytest) invalidates "
            "all mutation evidence — measurement is not comparable across "
            "toolchains.",
            category="toolchain",
            scope="INVALIDATES_POPULATION",
            # corrected below via scope override
        )
        if False
        else InvalidationRule(  # placeholder, replaced
            rule_id="R-CFG-002",
            description="Toolchain version change invalidates population-level "
            "mutation evidence — measurement is not comparable across toolchains.",
            category="toolchain",
            scope="INVALIDATES_COMPONENT",
        )
    ),
    InvalidationRule(
        rule_id="R-DEP-001",
        description="Dependency manifest change without version bump does "
        "not invalidate (assumed transparent).",
        category="dependency",
        scope="DOES_NOT_INVALIDATE",
    ),
    InvalidationRule(
        rule_id="R-DEP-002",
        description="Dependency version bump in mutation-sensitive "
        "packages (mutmut, pytest, coverage) invalidates toolchain "
        "evidence.",
        category="dependency",
        scope="INVALIDATES_COMPONENT",
    ),
    InvalidationRule(
        rule_id="R-POP-001",
        description="Adding a new component to the population creates a "
        "new measurement requirement; existing evidence is unaffected.",
        category="population",
        scope="DOES_NOT_INVALIDATE",
    ),
    InvalidationRule(
        rule_id="R-POP-002",
        description="Removing a component from the population invalidates "
        "only that component's evidence.",
        category="population",
        scope="INVALIDATES_COMPONENT",
    ),
    InvalidationRule(
        rule_id="R-CAP-001",
        description="Capability-to-component mapping change invalidates "
        "evidence only for affected mappings.",
        category="capability_mapping",
        scope="INVALIDATES_EVIDENCE_ONLY",
    ),
    InvalidationRule(
        rule_id="R-SCHEMA-001",
        description="Evidence schema change invalidates evidence only "
        "(interpretation re-run required).",
        category="evidence_schema",
        scope="INVALIDATES_EVIDENCE_ONLY",
    ),
    InvalidationRule(
        rule_id="R-ENV-001",
        description="Environment change (Python version, OS) invalidates "
        "toolchain-comparable evidence at population level.",
        category="environment",
        scope="INVALIDATES_COMPONENT",
    ),
    InvalidationRule(
        rule_id="R-INFRA-001",
        description="Verification infrastructure change (e.g. mutmut "
        "version pinned to a different release) invalidates evidence "
        "only for tasks depending on the changed infra.",
        category="infrastructure",
        scope="INVALIDATES_TASK",
    ),
    InvalidationRule(
        rule_id="R-TASK-001",
        description="A task whose command or script changed invalidates "
        "only that task's evidence.",
        category="config",
        scope="INVALIDATES_TASK",
    ),
]


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InvalidationVerdict:
    """The verdict of applying a single rule to a change + measurement."""

    rule_id: str
    scope: InvalidationScope
    triggered: bool
    rationale: str


def evaluate_rule(
    rule: InvalidationRule, change: Change, component: str
) -> InvalidationVerdict:
    """Apply a single rule to a change.

    The evaluator is *deliberately narrow* — each rule only fires for
    a specific (category, target) shape. No keyword inference.
    """
    triggered = False
    rationale = ""

    if rule.rule_id == "R-SRC-001":
        triggered = change.kind == "source_change" and change.target == component
        rationale = (
            f"source change for {component}"
            if triggered
            else "no source change for this component"
        )
    elif rule.rule_id == "R-SRC-002":
        triggered = (
            change.kind == "source_change"
            and change.target.startswith("shared::")
            and component in change.target.split("::")
        )
        rationale = (
            f"shared module change affects {component}"
            if triggered
            else "no shared module change affecting this capability"
        )
    elif rule.rule_id == "R-SRC-003":
        triggered = change.kind == "test_change" and component in change.target
        rationale = (
            "test change for this component"
            if triggered
            else "no test change affecting this component's evidence"
        )
    elif rule.rule_id == "R-CFG-001":
        triggered = change.kind == "config_change" and change.target.endswith(
            f"::{component}"
        )
        rationale = (
            f"config change for task affecting {component}"
            if triggered
            else "no relevant config change"
        )
    elif rule.rule_id == "R-CFG-002":
        triggered = change.kind == "toolchain_change"
        rationale = (
            "toolchain change invalidates measurement"
            if triggered
            else "no toolchain change"
        )
    elif rule.rule_id == "R-DEP-001":
        triggered = False
        rationale = "transparent dependency manifest change"
    elif rule.rule_id == "R-DEP-002":
        triggered = change.kind == "dependency_bump" and any(
            t in change.target for t in ("mutmut", "pytest", "coverage")
        )
        rationale = (
            "mutation-sensitive dependency bumped"
            if triggered
            else "non-mutation dependency or no version bump"
        )
    elif rule.rule_id == "R-POP-001":
        triggered = False
        rationale = "new components do not invalidate existing evidence"
    elif rule.rule_id == "R-POP-002":
        triggered = change.kind == "population_remove" and change.target == component
        rationale = (
            f"component {component} removed from population"
            if triggered
            else "no removal affecting this component"
        )
    elif rule.rule_id == "R-CAP-001":
        triggered = (
            change.kind == "capability_mapping_change" and component in change.target
        )
        rationale = (
            f"capability mapping changed for {component}"
            if triggered
            else "no mapping change for this component"
        )
    elif rule.rule_id == "R-SCHEMA-001":
        triggered = change.kind == "evidence_schema_change"
        rationale = (
            "schema change — re-interpretation required"
            if triggered
            else "no schema change"
        )
    elif rule.rule_id == "R-ENV-001":
        triggered = change.kind == "environment_change"
        rationale = "environment change" if triggered else "no environment change"
    elif rule.rule_id == "R-INFRA-001":
        triggered = change.kind == "infra_change" and component in change.target
        rationale = (
            f"infra change affects {component}"
            if triggered
            else "no infra change affecting this task"
        )
    elif rule.rule_id == "R-TASK-001":
        triggered = change.kind == "task_command_change" and change.target.endswith(
            f"::{component}"
        )
        rationale = (
            f"task command change for {component}"
            if triggered
            else "no task command change"
        )
    else:
        triggered = False
        rationale = f"unhandled rule {rule.rule_id}"

    return InvalidationVerdict(
        rule_id=rule.rule_id,
        scope=rule.scope,
        triggered=triggered,
        rationale=rationale,
    )


def aggregate_invalidation(
    verdicts: Iterable[InvalidationVerdict],
) -> InvalidationScope:
    """Combine verdicts into a single scope using worst-case wins.

    The order of precedence is the order of severity:

        INVALIDATES_POPULATION      > INVALIDATES_CAPABILITY
        INVALIDATES_COMPONENT       > INVALIDATES_TASK
        INVALIDATES_EVIDENCE_ONLY   > DOES_NOT_INVALIDATE
    """
    precedence: dict[InvalidationScope, int] = {
        "DOES_NOT_INVALIDATE": 0,
        "INVALIDATES_EVIDENCE_ONLY": 1,
        "INVALIDATES_TASK": 2,
        "INVALIDATES_COMPONENT": 3,
        "INVALIDATES_CAPABILITY": 4,
        "INVALIDATES_POPULATION": 5,
    }
    chosen: InvalidationScope = "DOES_NOT_INVALIDATE"
    for v in verdicts:
        if v.triggered and precedence[v.scope] > precedence[chosen]:
            chosen = v.scope
    return chosen


# ---------------------------------------------------------------------------
# Reuse decision — combines invalidation with measurement fingerprint check
# ---------------------------------------------------------------------------


def decide_reuse(
    component: str,
    change: Change,
    measurement: ComponentMeasurement | None,
    population: PopulationSnapshot,
) -> EvidenceReuse:
    """Decide whether a measurement can be reused for a given change."""
    if measurement is None:
        return EvidenceReuse(
            reuse_id=f"reuse::{component}::no-evidence",
            scope_id=component,
            scope_kind="component",
            disposition="no_evidence",
            measurement_id=None,
            population_id=population.population_id,
            reasons=("no prior measurement for this component",),
        )

    verdicts = [evaluate_rule(rule, change, component) for rule in INVALIDATION_RULES]
    triggered = [v for v in verdicts if v.triggered]
    scope = aggregate_invalidation(triggered)

    # Specific disposition mapping
    if scope == "DOES_NOT_INVALIDATE":
        # Even if no rule invalidates, check measurement fingerprint
        # matches population + toolchain. If population changed but
        # this component is still in the population, evidence is
        # reusable.
        if measurement.population_id != population.population_id:
            disposition: ReuseDisposition = "reusable_aggregate"
        elif measurement.config_hash != population.config_hash:
            disposition = "reusable_with_revalidation"
        else:
            disposition = "reusable"
        return EvidenceReuse(
            reuse_id=f"reuse::{component}::{measurement.measurement_id}",
            scope_id=component,
            scope_kind="component",
            disposition=disposition,
            measurement_id=measurement.measurement_id,
            population_id=population.population_id,
            reasons=tuple(v.rationale for v in triggered) or ("no rules triggered",),
        )

    if scope == "INVALIDATES_POPULATION":
        return EvidenceReuse(
            reuse_id=f"reuse::{component}::pop-invalidated",
            scope_id=component,
            scope_kind="component",
            disposition="invalidated_capability",
            measurement_id=measurement.measurement_id,
            population_id=population.population_id,
            invalidations=tuple(v.rule_id for v in triggered),
            reasons=tuple(v.rationale for v in triggered),
        )

    if scope == "INVALIDATES_CAPABILITY":
        return EvidenceReuse(
            reuse_id=f"reuse::{component}::cap-invalidated",
            scope_id=component,
            scope_kind="component",
            disposition="invalidated_capability",
            measurement_id=measurement.measurement_id,
            population_id=population.population_id,
            invalidations=tuple(v.rule_id for v in triggered),
            reasons=tuple(v.rationale for v in triggered),
        )

    if scope == "INVALIDATES_COMPONENT":
        return EvidenceReuse(
            reuse_id=f"reuse::{component}::comp-invalidated",
            scope_id=component,
            scope_kind="component",
            disposition="invalidated_component",
            measurement_id=measurement.measurement_id,
            population_id=population.population_id,
            invalidations=tuple(v.rule_id for v in triggered),
            reasons=tuple(v.rationale for v in triggered),
        )

    if scope == "INVALIDATES_TASK":
        return EvidenceReuse(
            reuse_id=f"reuse::{component}::task-invalidated",
            scope_id=component,
            scope_kind="component",
            disposition="invalidated_task",
            measurement_id=measurement.measurement_id,
            population_id=population.population_id,
            invalidations=tuple(v.rule_id for v in triggered),
            reasons=tuple(v.rationale for v in triggered),
        )

    # INVALIDATES_EVIDENCE_ONLY
    return EvidenceReuse(
        reuse_id=f"reuse::{component}::ev-invalidated",
        scope_id=component,
        scope_kind="component",
        disposition="invalidated_evidence_only",
        measurement_id=measurement.measurement_id,
        population_id=population.population_id,
        invalidations=tuple(v.rule_id for v in triggered),
        reasons=tuple(v.rationale for v in triggered),
    )


# ---------------------------------------------------------------------------
# Built-in snapshots + measurements from C42.26 (the authoritative baseline)
# ---------------------------------------------------------------------------

C42_26_POPULATION_ID = "pop-14-c42.26"
C42_24_B_POPULATION_ID = "pop-12-c42.24-B"
C42_25_TXN_POPULATION_ID = "pop-txn-c42.25"
C42_25_FIN_POPULATION_ID = "pop-fin-c42.25"


# Component -> capability mapping. Enumerated, not inferred. The
# graph builder consults this table for engine-name normalization.
ENGINE_TO_CAPABILITY: dict[str, str] = {
    "credit_card": "credit-card-risk",
    "account": "account-management",
    "loan": "loan-management",
    "reconciliation": "reconciliation",
    "behaviour": "behaviour-analytics",
    "balance": "balance-engine",
    "ledger_audit": "ledger-audit",
    "cashflow": "cashflow",
    "financial_events": "financial-events",
    "common_calculations": "common-calculations",
    "recommendation": "recommendation",
    "transaction_intelligence": "transaction-intelligence",
    "financial_intelligence": "financial-intelligence",
    "core_domain_money": "core-domain-money",
}

C42_26_COMPONENTS: tuple[str, ...] = (
    "credit_card_engine",
    "account_engine",
    "loan_engine",
    "reconciliation_engine",
    "behaviour_engine",
    "balance_engine",
    "ledger_audit_engine",
    "cashflow_engine",
    "financial_events",
    "core_domain_money",
    "common_calculations",
    "recommendation_engine",
    "transaction_intelligence",
    "financial_intelligence",
)


def c42_26_population() -> PopulationSnapshot:
    return PopulationSnapshot(
        population_id=C42_26_POPULATION_ID,
        created_at="2026-08-26T07:50:00+00:00",
        components=C42_26_COMPONENTS,
        component_fingerprints=dict.fromkeys(C42_26_COMPONENTS, ""),
        config_hash="c42-26-config-v1",
        toolchain_hash="mutmut-3.7.0|pytest-8.x",
        repository_sha="523637b8",
        notes=(
            "14-component population from M9-C42.26. Includes the 12 "
            "C42.24-B measured components plus the 2 C42.25 intelligence "
            "components."
        ),
    )


def c42_24_b_measurements() -> list[ComponentMeasurement]:
    """C42.24-B per-component mutation measurements (12 components)."""
    summaries = {
        "account_engine": (183, 163),
        "balance_engine": (285, 270),
        "behaviour_engine": (5258, 1875),
        "cashflow_engine": (172, 128),
        "common_calculations": (377, 213),
        "core_domain_money": (102, 84),
        "credit_card_engine": (582, 440),
        "financial_events": (704, 454),
        "ledger_audit_engine": (190, 108),
        "loan_engine": (1273, 1066),
        "recommendation_engine": (282, 179),
        "reconciliation_engine": (368, 297),
    }
    out: list[ComponentMeasurement] = []
    for component, (scored, killed) in summaries.items():
        out.append(
            ComponentMeasurement(
                measurement_id=f"meas::{component}::c42.24-B",
                component=component,
                population_id=C42_24_B_POPULATION_ID,
                kind="mutation",
                run_id="c42.24-B-full",
                measured_at="2026-08-24T18:00:00+00:00",
                repository_sha="6bb27a89",
                source_fingerprint=f"src::{component}",
                test_fingerprint=f"tests::{component}",
                config_hash="c42-24-B-config-v1",
                toolchain_hash="mutmut-3.7.0|pytest-8.x",
                summary={
                    "scored": scored,
                    "killed": killed,
                    "mutation_score_pct": round(100.0 * killed / scored, 2),
                },
                notes="C42.24-B authoritative full campaign measurement",
            )
        )
    return out


def c42_25_measurements() -> list[ComponentMeasurement]:
    out: list[ComponentMeasurement] = [
        ComponentMeasurement(
            measurement_id="meas::transaction_intelligence::c42.25",
            component="transaction_intelligence",
            population_id=C42_25_TXN_POPULATION_ID,
            kind="mutation",
            run_id="c42.25-txn-targeted",
            measured_at="2026-08-25T18:00:00+00:00",
            repository_sha="cdfaefe1",
            source_fingerprint="src::transaction_intelligence",
            test_fingerprint="tests::transaction_intelligence",
            config_hash="c42-25-config-v1",
            toolchain_hash="mutmut-3.7.0|pytest-8.x",
            summary={"scored": 1465, "killed": 1028, "mutation_score_pct": 70.2},
            notes="C42.25 targeted intelligence measurement",
        ),
        ComponentMeasurement(
            measurement_id="meas::financial_intelligence::c42.25",
            component="financial_intelligence",
            population_id=C42_25_FIN_POPULATION_ID,
            kind="mutation",
            run_id="c42.25-fin-targeted",
            measured_at="2026-08-25T18:00:00+00:00",
            repository_sha="cdfaefe1",
            source_fingerprint="src::financial_intelligence",
            test_fingerprint="tests::financial_intelligence",
            config_hash="c42-25-config-v1",
            toolchain_hash="mutmut-3.7.0|pytest-8.x",
            summary={"scored": 3710, "killed": 2710, "mutation_score_pct": 73.0},
            notes="C42.25 targeted intelligence measurement",
        ),
    ]
    return out


def c42_26_derived_aggregate(
    measurements: list[ComponentMeasurement],
) -> DerivedAggregate:
    scored = sum(int(m.summary.get("scored", 0)) for m in measurements)
    killed = sum(int(m.summary.get("killed", 0)) for m in measurements)
    pct = round(100.0 * killed / scored, 4) if scored else 0.0
    return DerivedAggregate(
        aggregate_id="agg::pop-14::c42.26",
        scope_id="pop-14",
        measurement_kind="mutation",
        population_id=C42_26_POPULATION_ID,
        component_measurement_ids=tuple(m.measurement_id for m in measurements),
        formula="sum(killed)/sum(scored) * 100",
        result=pct,
        rationale=(
            "Mathematical reconciliation of C42.24-B 12-component measurement "
            "+ C42.25 2-component targeted measurement."
        ),
    )


# ---------------------------------------------------------------------------
# Snapshot persistence
# ---------------------------------------------------------------------------

SNAPSHOT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.27" / "snapshots"


def save_snapshot(
    snapshot: PopulationSnapshot, measurements: list[ComponentMeasurement]
) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{snapshot.population_id}.json"
    payload = {
        "snapshot": snapshot.to_dict(),
        "measurements": [m.to_dict() for m in measurements],
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_snapshot(
    population_id: str,
) -> tuple[PopulationSnapshot, list[ComponentMeasurement]]:
    path = SNAPSHOT_DIR / f"{population_id}.json"
    data = json.loads(path.read_text())
    snap_data = data["snapshot"]
    snapshot = PopulationSnapshot(
        population_id=snap_data["population_id"],
        created_at=snap_data["created_at"],
        components=tuple(snap_data["components"]),
        component_fingerprints=snap_data.get("component_fingerprints", {}),
        config_hash=snap_data.get("config_hash", ""),
        toolchain_hash=snap_data.get("toolchain_hash", ""),
        repository_sha=snap_data.get("repository_sha", ""),
        notes=snap_data.get("notes", ""),
    )
    measurements: list[ComponentMeasurement] = []
    for m in data.get("measurements", []):
        measurements.append(
            ComponentMeasurement(
                measurement_id=m["measurement_id"],
                component=m["component"],
                population_id=m["population_id"],
                kind=m["kind"],
                run_id=m["run_id"],
                measured_at=m["measured_at"],
                repository_sha=m["repository_sha"],
                source_fingerprint=m["source_fingerprint"],
                test_fingerprint=m["test_fingerprint"],
                config_hash=m["config_hash"],
                toolchain_hash=m["toolchain_hash"],
                summary=m.get("summary", {}),
                notes=m.get("notes", ""),
            )
        )
    return snapshot, measurements


def main() -> int:
    # Persist C42.24-B + C42.25 + C42.26 snapshots.
    snap_24 = PopulationSnapshot(
        population_id=C42_24_B_POPULATION_ID,
        created_at="2026-08-24T18:00:00+00:00",
        components=tuple(m.component for m in c42_24_b_measurements()),
        component_fingerprints={
            m.component: m.source_fingerprint for m in c42_24_b_measurements()
        },
        config_hash="c42-24-B-config-v1",
        toolchain_hash="mutmut-3.7.0|pytest-8.x",
        repository_sha="6bb27a89",
        notes="12-component population from C42.24-B authoritative campaign.",
    )
    save_snapshot(snap_24, c42_24_b_measurements())

    snap_25 = PopulationSnapshot(
        population_id=C42_25_TXN_POPULATION_ID,
        created_at="2026-08-25T18:00:00+00:00",
        components=("transaction_intelligence", "financial_intelligence"),
        component_fingerprints={
            m.component: m.source_fingerprint for m in c42_25_measurements()
        },
        config_hash="c42-25-config-v1",
        toolchain_hash="mutmut-3.7.0|pytest-8.x",
        repository_sha="cdfaefe1",
        notes="C42.25 2-component targeted intelligence population.",
    )
    save_snapshot(snap_25, c42_25_measurements())

    snap_26 = c42_26_population()
    save_snapshot(snap_26, c42_24_b_measurements() + c42_25_measurements())

    # Derive the aggregate and persist it.
    measurements = c42_24_b_measurements() + c42_25_measurements()
    aggregate = c42_26_derived_aggregate(measurements)
    agg_path = SNAPSHOT_DIR / "c42.26-derived-aggregate.json"
    agg_path.write_text(json.dumps(aggregate.to_dict(), indent=2))

    print(f"Wrote snapshots under: {SNAPSHOT_DIR.relative_to(REPO_ROOT)}")
    print(f"Components in C42.26 population: {len(snap_26.components)}")
    print(f"Derived aggregate score: {aggregate.result}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
