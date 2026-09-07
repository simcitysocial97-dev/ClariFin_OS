"""
M9-C42.27 — M27.5 / Phase 6-9 Evidence-Aware Planner

Given a change set, the planner now produces a *deterministic* plan
that answers:

    * what is affected
    * what evidence already exists
    * which evidence is reusable
    * which evidence is invalidated
    * which verification tasks must be (re-)executed
    * what remains uncertain

The plan is *explainable* — every selected task carries a cause, and
every excluded task carries a disposition drawn from a closed
vocabulary. The planner never silently expands scope.

This module is additive. The existing ``VerificationPlanner`` (in
``runtime/foundation/verification/planner/planner.py``) remains the
authoritative producer of ``VerificationPlan`` artefacts consumed by
the orchestrator. This module produces an *evidence-aware plan* that
sits alongside the existing one.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

import importlib.util

from runtime.foundation.verification.evidence_reuse import (  # noqa: E402
    Change,
    ComponentMeasurement,
    DerivedAggregate,
    EvidenceReuse,
    PopulationSnapshot,
    ReuseDisposition,
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
    decide_reuse,
)
from runtime.foundation.verification.graph_model import (  # noqa: E402
    VerificationGraph,
    capability_id,
)

_graph_module_path = (
    REPO_ROOT / "runtime" / "generated" / "m9-c42.27" / "m27_2_graph_inventory.py"
)
_spec = importlib.util.spec_from_file_location(
    "m27_2_graph_inventory", _graph_module_path
)
_graph_inventory = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
assert _spec and _spec.loader
sys.modules.setdefault("m27_2_graph_inventory", _graph_inventory)
_spec.loader.exec_module(_graph_inventory)  # type: ignore[union-attr]
ENGINE_TO_CAPABILITY = _graph_inventory.ENGINE_TO_CAPABILITY
_classify_source = _graph_inventory._classify_source
_src_fingerprint = _graph_inventory._fingerprint


# ---------------------------------------------------------------------------
# Plan model — explainable
# ---------------------------------------------------------------------------

TaskDisposition = Literal[
    "selected_fresh",
    "selected_revalidation",
    "selected_aggregate",
    "excluded_unaffected",
    "excluded_already_certified",
    "excluded_reusable_evidence",
    "excluded_outside_population",
    "excluded_deferred",
    "excluded_not_applicable",
    "blocked_by_drift",
]


@dataclass(frozen=True, slots=True)
class PlannedTask:
    """One task in the evidence-aware plan."""

    task_id: str
    task_kind: str
    target: str  # component, capability, or scope
    disposition: TaskDisposition
    cause: str  # why this task is selected/excluded
    evidence_id: str | None = None  # for selected_revalidation / aggregate
    invalidations: tuple[str, ...] = ()
    reuse_disposition: ReuseDisposition | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_kind": self.task_kind,
            "target": self.target,
            "disposition": self.disposition,
            "cause": self.cause,
            "evidence_id": self.evidence_id,
            "invalidations": list(self.invalidations),
            "reuse_disposition": self.reuse_disposition,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class EvidenceAwarePlan:
    """The complete evidence-aware plan."""

    plan_id: str
    generated_at: str
    repository_state: dict[str, Any]
    changed_files: tuple[str, ...]
    affected_sources: tuple[str, ...]
    affected_capabilities: tuple[str, ...]
    affected_components: tuple[str, ...]
    population_id: str
    population_fingerprint: str
    selected_tasks: tuple[PlannedTask, ...]
    excluded_tasks: tuple[PlannedTask, ...]
    reuses: tuple[EvidenceReuse, ...]
    derived_aggregates: tuple[DerivedAggregate, ...]
    drift_blockers: tuple[str, ...]
    certification_gaps: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "generated_at": self.generated_at,
            "repository_state": self.repository_state,
            "changed_files": list(self.changed_files),
            "affected_sources": list(self.affected_sources),
            "affected_capabilities": list(self.affected_capabilities),
            "affected_components": list(self.affected_components),
            "population_id": self.population_id,
            "population_fingerprint": self.population_fingerprint,
            "selected_tasks": [t.to_dict() for t in self.selected_tasks],
            "excluded_tasks": [t.to_dict() for t in self.excluded_tasks],
            "reuses": [r.to_dict() for r in self.reuses],
            "derived_aggregates": [a.to_dict() for a in self.derived_aggregates],
            "drift_blockers": list(self.drift_blockers),
            "certification_gaps": list(self.certification_gaps),
            "rationale": self.rationale,
        }


# ---------------------------------------------------------------------------
# Affected scope resolver
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChangeDescriptor:
    """A single change + its class."""

    path: str
    kind: str  # "source_change" | "test_change" | ...
    component: str | None
    capability: str | None


def describe_change(path: str) -> ChangeDescriptor:
    """Classify a single changed file into a ChangeDescriptor."""
    if path.startswith("backend/src/engines/"):
        kind = "source_change"
        comp = _extract_engine(path)
        cap = ENGINE_TO_CAPABILITY.get(comp or "", (comp or "").replace("_", "-"))
    elif path.startswith("backend/tests/"):
        if path.startswith("backend/tests/generated/"):
            return ChangeDescriptor(path, "excluded_generated", None, None)
        kind = "test_change"
        comp = _extract_engine(path)
        cap = ENGINE_TO_CAPABILITY.get(comp or "", (comp or "").replace("_", "-"))
    elif path == "pyproject.toml" or path.endswith(
        ("/pyproject.toml", "ruff.toml", ".coveragerc")
    ):
        kind = "config_change"
        comp = None
        cap = None
    elif path.startswith("backend/src/"):
        kind = "source_change"
        comp = _extract_engine(path) or _extract_service(path)
        cap = (
            ENGINE_TO_CAPABILITY.get(comp or "", (comp or "").replace("_", "-"))
            if comp
            else None
        )
    else:
        kind = "other"
        comp = None
        cap = None
    return ChangeDescriptor(path, kind, comp, cap)


def _extract_engine(path: str) -> str | None:
    parts = path.split("/")
    for p in parts:
        if p.endswith("_engine"):
            return p[: -len("_engine")]
    return None


def _extract_service(path: str) -> str | None:
    parts = path.split("/")
    if "services" in parts:
        i = parts.index("services")
        if i + 1 < len(parts):
            return parts[i + 1]
    return None


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------


class EvidenceAwarePlanner:
    """Plans verification proportionally to actual change impact."""

    def __init__(
        self,
        graph: VerificationGraph,
        population: PopulationSnapshot,
        measurements: list[ComponentMeasurement],
    ):
        self._graph = graph
        self._population = population
        self._measurements_by_component: dict[str, ComponentMeasurement] = {
            m.component: m for m in measurements
        }
        self._all_measurements = list(measurements)

    # ----- public API -----

    def plan(self, changed_files: Iterable[str]) -> EvidenceAwarePlan:
        files = tuple(changed_files)
        # 1. Describe each change
        descriptors = [describe_change(f) for f in files]
        # 2. Resolve affected capabilities + components
        affected_caps: list[str] = []
        affected_comps: list[str] = []
        for d in descriptors:
            if d.capability and d.capability not in affected_caps:
                affected_caps.append(d.capability)
            if d.component and d.component not in affected_comps:
                affected_comps.append(d.component)
        affected_cap_ids = tuple(
            capability_id(c)
            for c in affected_caps
            if capability_id(c) in self._graph.capabilities
        )

        # 3. Detect drift — a capability claims coverage that the
        # executable surface cannot actually reach. C42.24-style.
        drift = self._detect_drift(affected_cap_ids)

        # 4. Build change objects per affected component
        per_component_change: dict[str, Change] = {}
        for d in descriptors:
            if d.component is None:
                continue
            change_kind = "source_change" if d.kind == "source_change" else d.kind
            per_component_change.setdefault(
                d.component,
                Change(kind=change_kind, target=d.component),
            )

        # 5. Decide reuse + plan tasks for each affected component
        reuses: list[EvidenceReuse] = []
        selected: list[PlannedTask] = []
        excluded: list[PlannedTask] = []
        gaps: list[str] = []

        # Normalize per-component change map to use full engine names
        # (population keys are full names like 'credit_card_engine';
        # descriptors use short names like 'credit_card').
        per_component_change_norm: dict[str, Change] = {}
        for k, v in per_component_change.items():
            # Try the full _engine form first
            full = f"{k}_engine" if not k.endswith("_engine") else k
            per_component_change_norm[full] = Change(
                kind=v.kind,
                target=full,
                fingerprint_before=v.fingerprint_before,
                fingerprint_after=v.fingerprint_after,
            )

        # Always consider the entire 14-component population for the
        # *aggregate* question. Per-component decisions are independent.
        all_components = self._population.components
        for comp in all_components:
            change = per_component_change_norm.get(
                comp, Change(kind="no_change", target=comp)
            )
            measurement = self._measurements_by_component.get(comp)
            reuse = decide_reuse(comp, change, measurement, self._population)
            reuses.append(reuse)

            # Determine the task plan
            if reuse.disposition in (
                "invalidated_component",
                "invalidated_capability",
            ):
                # Component must be re-measured
                selected.append(
                    PlannedTask(
                        task_id=f"task::mutation::{comp}",
                        task_kind="mutation",
                        target=comp,
                        disposition="selected_fresh",
                        cause=(
                            f"component {comp} invalidated by change "
                            f"({', '.join(reuse.invalidations) or 'rule-set'}); "
                            "fresh measurement required"
                        ),
                        evidence_id=reuse.measurement_id,
                        invalidations=reuse.invalidations,
                        reuse_disposition=reuse.disposition,
                    )
                )
            elif reuse.disposition == "no_evidence":
                # New component
                if comp in self._population.components:
                    selected.append(
                        PlannedTask(
                            task_id=f"task::mutation::{comp}",
                            task_kind="mutation",
                            target=comp,
                            disposition="selected_fresh",
                            cause=(
                                f"newly admitted component {comp}; "
                                "no prior measurement exists"
                            ),
                        )
                    )
                gaps.append(f"missing measurement for {comp}")
            elif reuse.disposition == "reusable":
                excluded.append(
                    PlannedTask(
                        task_id=f"task::mutation::{comp}",
                        task_kind="mutation",
                        target=comp,
                        disposition="excluded_reusable_evidence",
                        cause=(
                            f"prior measurement for {comp} remains valid; "
                            "no invalidation triggered"
                        ),
                        evidence_id=reuse.measurement_id,
                        reuse_disposition=reuse.disposition,
                    )
                )
            elif reuse.disposition == "reusable_aggregate":
                # Two sub-cases:
                #   * The component itself is unchanged but the aggregate
                #     needs recomputation (population_id differs). This
                #     is *excluded* from new measurement, and the
                #     aggregate handles it.
                #   * The component was re-admitted and aggregate
                #     recomputation is required.
                if change.kind == "no_change":
                    excluded.append(
                        PlannedTask(
                            task_id=f"task::mutation::{comp}",
                            task_kind="mutation",
                            target=comp,
                            disposition="excluded_reusable_evidence",
                            cause=(
                                f"component {comp} unchanged; existing "
                                "measurement feeds the derived aggregate"
                            ),
                            evidence_id=reuse.measurement_id,
                            reuse_disposition=reuse.disposition,
                        )
                    )
                else:
                    selected.append(
                        PlannedTask(
                            task_id=f"task::mutation::{comp}",
                            task_kind="mutation",
                            target=comp,
                            disposition="selected_aggregate",
                            cause=(
                                f"component {comp} re-admitted into new "
                                "population; aggregate recomputation required"
                            ),
                            evidence_id=reuse.measurement_id,
                            reuse_disposition=reuse.disposition,
                        )
                    )
            elif reuse.disposition == "reusable_with_revalidation":
                selected.append(
                    PlannedTask(
                        task_id=f"task::mutation::{comp}",
                        task_kind="mutation",
                        target=comp,
                        disposition="selected_revalidation",
                        cause=(
                            f"prior measurement for {comp} exists but config "
                            "changed; revalidation recommended"
                        ),
                        evidence_id=reuse.measurement_id,
                        reuse_disposition=reuse.disposition,
                    )
                )
            elif reuse.disposition in (
                "invalidated_task",
                "invalidated_evidence_only",
            ):
                selected.append(
                    PlannedTask(
                        task_id=f"task::mutation::{comp}",
                        task_kind="mutation",
                        target=comp,
                        disposition="selected_revalidation",
                        cause=(
                            f"task-level invalidation for {comp} "
                            f"({', '.join(reuse.invalidations)})"
                        ),
                        evidence_id=reuse.measurement_id,
                        invalidations=reuse.invalidations,
                        reuse_disposition=reuse.disposition,
                    )
                )
            else:
                # Default safe behaviour
                selected.append(
                    PlannedTask(
                        task_id=f"task::mutation::{comp}",
                        task_kind="mutation",
                        target=comp,
                        disposition="selected_fresh",
                        cause=(
                            f"unhandled disposition {reuse.disposition}; "
                            "defaulting to fresh measurement"
                        ),
                        reuse_disposition=reuse.disposition,
                    )
                )

        # 6. Build derived aggregate (always — that's the point)
        derived = self._build_aggregate(reuses)

        # 7. Build plan rationale
        rationale = self._build_rationale(
            files, affected_caps, affected_comps, reuses, selected, excluded, drift
        )

        # 8. Plan id = hash of inputs
        plan_id = hashlib.sha256("\n".join(sorted(files)).encode()).hexdigest()[:12]

        return EvidenceAwarePlan(
            plan_id=plan_id,
            generated_at=datetime.now(UTC).isoformat(),
            repository_state={"population_id": self._population.population_id},
            changed_files=files,
            affected_sources=tuple(
                d.path for d in descriptors if d.kind != "excluded_generated"
            ),
            affected_capabilities=tuple(affected_caps),
            affected_components=tuple(affected_comps),
            population_id=self._population.population_id,
            population_fingerprint=self._population.fingerprint(),
            selected_tasks=tuple(selected),
            excluded_tasks=tuple(excluded),
            reuses=tuple(reuses),
            derived_aggregates=(derived,) if derived else (),
            drift_blockers=tuple(drift),
            certification_gaps=tuple(gaps),
            rationale=rationale,
        )

    # ----- drift detection (Phase 7 — C42.24 architectural regression) -----

    def _detect_drift(self, affected_cap_ids: tuple[str, ...]) -> list[str]:
        """Detect a C42.24-style drift.

        A drift is a declared capability whose executable test
        surface does not actually reach any source for that
        capability. The binding is by capability, not by path
        prefix: a source ``backend/src/.../x.py`` linked to
        ``cap::foo`` is reached by *any* surface also linked to
        ``cap::foo``, regardless of which directory tree the
        surface lives in. Path-prefix matching would falsely
        report drift for any test surface in ``backend/tests/``
        (which is exactly the C42.24 incident shape).
        """
        blockers: list[str] = []
        pop_caps: set[str] = set()
        for comp in self._population.components:
            cap_name = self._graph_capability_name(comp)
            if cap_name is not None:
                pop_caps.add(capability_id(cap_name))
        candidates = pop_caps | set(affected_cap_ids)
        for cap_id in candidates:
            cap = self._graph.capabilities.get(cap_id)
            if cap is None:
                blockers.append(
                    f"capability {cap_id} declared in population but "
                    "not present in verification graph"
                )
                continue
            surfaces = self._graph.surfaces_for_capability(cap_id)
            sources = [
                s
                for s in self._graph.sources.values()
                if cap_id in self._graph.source_to_capability.get(s.id, ())
            ]
            if not surfaces and not sources:
                # Out-of-population declaration; skip.
                continue
            if surfaces and not sources:
                blockers.append(
                    f"capability {cap_id} has surfaces but no source binding"
                )
            elif sources and not surfaces:
                blockers.append(
                    f"capability {cap_id} has source binding but no "
                    "executable test surface"
                )
            else:
                # Both present. The surface is considered to reach
                # the source iff at least one surface kind is
                # "unit"/"integration"/"property"/"invariant" — the
                # surface kinds the planner actually exercises. Any
                # other kind (e.g. "audit") is observation-only and
                # does not establish an executable binding.
                executable_kinds = {"unit", "integration", "property", "invariant"}
                has_executable = any(s.kind in executable_kinds for s in surfaces)
                if not has_executable:
                    blockers.append(
                        f"capability {cap_id} has no executable test "
                        "surface (only observation surfaces)"
                    )
        return blockers

    def _graph_capability_name(self, component: str) -> str | None:
        from runtime.foundation.verification.evidence_reuse import (
            ENGINE_TO_CAPABILITY as _MAP,
        )

        return _MAP.get(component, component.replace("_", "-"))

    def _build_aggregate(self, reuses: list[EvidenceReuse]) -> DerivedAggregate | None:
        """Build the derived aggregate using only *valid* measurements."""
        valid_components: list[ComponentMeasurement] = []
        for reuse in reuses:
            if reuse.disposition in (
                "reusable",
                "reusable_aggregate",
                "reusable_with_revalidation",
            ):
                m = self._measurements_by_component.get(reuse.scope_id)
                if m is not None:
                    valid_components.append(m)
        if not valid_components:
            return None
        scored = sum(int(m.summary.get("scored") or 0) for m in valid_components)
        killed = sum(int(m.summary.get("killed") or 0) for m in valid_components)
        pct = round(100.0 * killed / scored, 4) if scored else 0.0
        return DerivedAggregate(
            aggregate_id=f"agg::{self._population.population_id}::derived",
            scope_id=self._population.population_id,
            measurement_kind="mutation",
            population_id=self._population.population_id,
            component_measurement_ids=tuple(m.measurement_id for m in valid_components),
            formula="sum(killed)/sum(scored) * 100",
            result=pct,
            rationale=(
                "Derived aggregate from valid (reusable) component "
                "measurements. Invalidated components are excluded and "
                "must be re-measured before the aggregate can be "
                "promoted to authoritative."
            ),
        )

    def _build_rationale(
        self,
        files: tuple[str, ...],
        caps: list[str],
        comps: list[str],
        reuses: list[EvidenceReuse],
        selected: list[PlannedTask],
        excluded: list[PlannedTask],
        drift: list[str],
    ) -> str:
        reusable = sum(1 for r in reuses if r.disposition == "reusable")
        invalidated = sum(
            1
            for r in reuses
            if r.disposition in ("invalidated_component", "invalidated_capability")
        )
        no_evidence = sum(1 for r in reuses if r.disposition == "no_evidence")
        return (
            f"Inputs: {len(files)} file(s) changed. "
            f"Affected capabilities: {', '.join(caps) or 'none'}. "
            f"Affected components: {', '.join(comps) or 'none'}. "
            f"Decisions across {len(self._population.components)} "
            f"components: {reusable} reusable, {invalidated} invalidated, "
            f"{no_evidence} no-evidence. Selected tasks: "
            f"{len(selected)}; excluded tasks: {len(excluded)}; "
            f"drift blockers: {len(drift)}."
        )


# ---------------------------------------------------------------------------
# Convenience constructor
# ---------------------------------------------------------------------------


def default_planner() -> EvidenceAwarePlanner:
    """Construct a planner with the C42.26 baseline + graph inventory.

    Always re-reads the graph inventory file so test ordering and
    module reload do not produce stale results.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_graph_inv_fresh", _graph_module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load graph inventory module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    g, _manifest = mod.build_graph()
    pop = c42_26_population()
    measurements = c42_24_b_measurements() + c42_25_measurements()
    return EvidenceAwarePlanner(g, pop, measurements)


def main() -> int:
    planner = default_planner()
    # Demonstration plan against an empty change set
    plan = planner.plan(())
    out = REPO_ROOT / "runtime" / "generated" / "m9-c42.27" / "sample-plan-noop.json"
    out.write_text(json.dumps(plan.to_dict(), indent=2))
    print(f"Sample no-op plan: {out.relative_to(REPO_ROOT)}")
    print(f"Selected: {len(plan.selected_tasks)}; Excluded: {len(plan.excluded_tasks)}")
    print(
        f"Derived aggregate: {plan.derived_aggregates[0].result if plan.derived_aggregates else 'n/a'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
