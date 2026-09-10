"""M28.6 — Evidence reconciliation and labelled aggregate computation.

Produces the reconciled verification state and the labelled
AUTHORITATIVE_MEASURED / AUTHORITATIVE_TARGETED /
MATHEMATICALLY_RECONCILED aggregate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from runtime.foundation.verification.evidence_planner import EvidenceAwarePlan
from runtime.foundation.verification.evidence_reuse import (
    ComponentMeasurement,
    PopulationSnapshot,
)
from runtime.foundation.verification.execution.classification import FailureKind
from runtime.foundation.verification.execution.evidence import ExecutionEvidence


@dataclass(frozen=True, slots=True)
class ReconciledComponent:
    component: str
    source: (
        str  # "fresh_measured" | "reused" | "derived" | "invalidated" | "no_evidence"
    )
    evidence: ExecutionEvidence | None
    prior_measurement: ComponentMeasurement | None

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "source": self.source,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "prior_measurement": (
                self.prior_measurement.to_dict() if self.prior_measurement else None
            ),
        }


@dataclass(frozen=True, slots=True)
class LabelledAggregate:
    """An aggregate whose label is never collapsed into a generic score."""

    label: Literal[
        "AUTHORITATIVE_MEASURED",
        "AUTHORITATIVE_TARGETED",
        "MATHEMATICALLY_RECONCILED",
    ]
    result: float
    numerator: int  # sum(killed)
    denominator: int  # sum(scored)
    scope: str  # population_id or selected components
    decided_at: str
    rationale: str

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "result": self.result,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "scope": self.scope,
            "decided_at": self.decided_at,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ReconciledVerificationState:
    plan_id: str
    generated_at: str
    components: tuple[ReconciledComponent, ...]
    aggregate: LabelledAggregate | None
    certifiable: bool
    rationale: str

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "generated_at": self.generated_at,
            "components": [c.to_dict() for c in self.components],
            "aggregate": self.aggregate.to_dict() if self.aggregate else None,
            "certifiable": self.certifiable,
            "rationale": self.rationale,
        }


def reconcile(
    plan: EvidenceAwarePlan,
    fresh: dict[str, ExecutionEvidence],
    prior_by_component: dict[str, ComponentMeasurement],
    population: PopulationSnapshot,
    *,
    freshness_authority: str = "all_fresh_measured",
) -> ReconciledVerificationState:
    """Reconcile fresh + reusable + derived evidence into a verified state.

    Components in the planner's plan that were *selected* but did not
    produce a fresh ExecutionEvidence are invalidated (cannot be
    certified from prior evidence alone when the planner said they
    must be re-measured). Components the planner *excluded* as
    reusable keep their prior measurement.
    """
    components: list[ReconciledComponent] = []
    reuses = {r.scope_id: r for r in plan.reuses}
    selected = {t.target: t for t in plan.selected_tasks}
    excluded = {t.target: t for t in plan.excluded_tasks}

    for comp in population.components:
        sel_task = selected.get(comp)
        exc_task = excluded.get(comp)
        reuse = reuses.get(comp)
        evidence = fresh.get(comp)
        prior = prior_by_component.get(comp)

        if evidence is not None:
            if evidence.failure_kind in (
                FailureKind.INFRASTRUCTURE,
                FailureKind.SCOPE,
                FailureKind.CONFIGURATION,
                FailureKind.EVIDENCE,
                FailureKind.VERIFICATION,
            ):
                # Any failure means the component is invalidated — the
                # prior measurement is no longer authoritative for
                # certification until a subsequent fresh_measured
                # succeeds.
                components.append(
                    ReconciledComponent(comp, "invalidated", evidence, prior)
                )
            else:
                components.append(
                    ReconciledComponent(comp, "fresh_measured", evidence, prior)
                )
            continue
        if sel_task is not None:
            # Planner said re-measure, but we have no fresh evidence.
            components.append(ReconciledComponent(comp, "invalidated", None, prior))
            continue
        if exc_task is not None and reuse is not None and prior is not None:
            # Planner excluded this component but there is a reuse record
            # from a prior run — honour the reuse.
            components.append(ReconciledComponent(comp, "reused", None, prior))
            continue
        if exc_task is not None:
            # Planner excluded and no reuse — no evidence needed.
            components.append(ReconciledComponent(comp, "no_evidence", None, prior))
            continue
        # Component not mentioned by planner and not in population — skip.
        continue

    aggregate = _compute_labelled_aggregate(
        tuple(components), population, freshness_authority=freshness_authority
    )
    certifiable = all(
        c.source not in ("invalidated", "no_evidence") for c in components
    ) and aggregate is not None and aggregate.denominator > 0
    rationale = (
        f"Reconciled {len(components)} component(s) from plan "
        f"{plan.plan_id!r} against population {population.population_id!r}. "
        f"{sum(1 for c in components if c.source == 'fresh_measured')} fresh, "
        f"{sum(1 for c in components if c.source == 'reused')} reused, "
        f"{sum(1 for c in components if c.source == 'invalidated')} invalidated, "
        f"{sum(1 for c in components if c.source == 'no_evidence')} no-evidence."
    )

    return ReconciledVerificationState(
        plan_id=plan.plan_id,
        generated_at=datetime.now(UTC).isoformat(),
        components=tuple(components),
        aggregate=aggregate,
        certifiable=certifiable,
        rationale=rationale,
    )


def _compute_labelled_aggregate(
    components: tuple[ReconciledComponent, ...],
    population: PopulationSnapshot,
    *,
    freshness_authority: str = "all_fresh_measured",
) -> LabelledAggregate:
    """Compute a labelled aggregate without ever collapsing categories.

    Label rules:
      * AUTHORITATIVE_MEASURED — every component in the population has
        a fresh, non-invalidated ExecutionEvidence (i.e. a full mutation
        campaign was just run by this executor).
      * AUTHORITATIVE_TARGETED — at least one component has fresh
        evidence and the rest are *reused*; the score is computed over
        fresh+reused components but only the fresh subset is considered
        *measured* (the rest are derived from prior artifacts).
      * MATHEMATICALLY_RECONCILED — no fresh evidence at all; every
        component is reused. The score is the deterministic
        re-derivation of the C42.27 aggregate.
    """
    fresh = [c for c in components if c.source == "fresh_measured"]
    reused = [c for c in components if c.source == "reused"]

    def _score_for(c: ReconciledComponent) -> tuple[int, int] | None:
        if c.evidence is not None and c.evidence.counts:
            k = c.evidence.counts.get("killed", 0)
            g = c.evidence.counts.get("generated", 0)
            return k, g
        if c.prior_measurement is not None:
            k = int(c.prior_measurement.summary.get("killed") or 0)
            g = int(c.prior_measurement.summary.get("scored") or 0)
            return k, g
        return None

    def _agg(scope: list[ReconciledComponent]) -> tuple[int, int]:
        n = 0
        d = 0
        for c in scope:
            sc = _score_for(c)
            if sc is None:
                continue
            n += sc[0]
            d += sc[1]
        return n, d

    now = datetime.now(UTC).isoformat()
    if not fresh and not reused:
        return LabelledAggregate(
            label="MATHEMATICALLY_RECONCILED",
            result=0.0,
            numerator=0,
            denominator=0,
            scope=population.population_id,
            decided_at=now,
            rationale="no fresh or reused evidence; aggregate is 0/0",
        )
    if not fresh and reused:
        n, d = _agg(reused)
        pct = round(100.0 * n / d, 4) if d else 0.0
        return LabelledAggregate(
            label="MATHEMATICALLY_RECONCILED",
            result=pct,
            numerator=n,
            denominator=d,
            scope=population.population_id,
            decided_at=now,
            rationale=(
                f"derived from {len(reused)} reused component(s) over "
                f"population {population.population_id}; no fresh measurement"
            ),
        )
    if fresh and not reused:
        n, d = _agg(fresh)
        pct = round(100.0 * n / d, 4) if d else 0.0
        return LabelledAggregate(
            label="AUTHORITATIVE_MEASURED",
            result=pct,
            numerator=n,
            denominator=d,
            scope=population.population_id,
            decided_at=now,
            rationale=(
                f"every component in population {population.population_id} "
                "was freshly measured by this executor"
            ),
        )
    # Fresh + reused
    n, d = _agg(list(fresh) + list(reused))
    pct = round(100.0 * n / d, 4) if d else 0.0
    return LabelledAggregate(
        label="AUTHORITATIVE_TARGETED",
        result=pct,
        numerator=n,
        denominator=d,
        scope=population.population_id,
        decided_at=now,
        rationale=(
            f"{len(fresh)} component(s) freshly measured + {len(reused)} "
            "reused; only the fresh subset is directly measured, the rest "
            "are derived from prior certified artifacts"
        ),
    )
