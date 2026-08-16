"""Phase 4 — Engineering Risk Engine.

Scores seven independent risk dimensions, each backed by explicit evidence
drawn from provider state, the blast radius and the verification plan.

Design rule: a dimension may only raise risk when it can cite a concrete
fact. There are no free-floating "feels risky" weights — every contribution
appends an evidence string that names the entities responsible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from runtime.foundation.intelligence.platform.blast import BlastRadius
from runtime.foundation.intelligence.platform.change import ChangeIntelligence
from runtime.foundation.intelligence.platform.optimizer import VerificationPlanIntel
from runtime.foundation.intelligence.platform.resolver import (
    EntityResolver,
    get_resolver,
)

__all__ = ["RiskDimension", "EngineeringRisk", "assess_risk"]

_LEVELS = ("Low", "Medium", "High")


def _level(score: int) -> str:
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


@dataclass(frozen=True, slots=True)
class RiskDimension:
    name: str
    level: str
    score: int
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "score": self.score,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class EngineeringRisk:
    generated_at: str
    dimensions: tuple[RiskDimension, ...]
    overall_level: str
    overall_score: int
    confidence: float
    confidence_basis: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "engineering-risk/v1",
            "generated_at": self.generated_at,
            "provider": "runtime.foundation.architecture.get_architecture",
            "overall": {
                "level": self.overall_level,
                "score": self.overall_score,
                "aggregation": (
                    "mean of dimension scores, floored by the worst dimension "
                    "level so a single High dimension is never masked"
                ),
                "confidence": self.confidence,
                "confidence_basis": list(self.confidence_basis),
            },
            "dimensions": [d.to_dict() for d in self.dimensions],
            "levels": list(_LEVELS),
        }


def assess_risk(
    change: ChangeIntelligence,
    blast: BlastRadius,
    plan: VerificationPlanIntel,
    resolver: EntityResolver | None = None,
    memory: dict[str, Any] | None = None,
) -> EngineeringRisk:
    """Compute the seven engineering risk dimensions with evidence."""
    res = resolver or get_resolver()
    arch = res.arch
    kinds = blast.kinds()
    dims: list[RiskDimension] = []

    # 1. Architectural risk — engines/ownership roots touched.
    arch_score = 0
    arch_ev: list[str] = []
    engines_changed = change.entities.get("engines", ())
    if engines_changed:
        arch_score += min(50, 15 * len(engines_changed))
        arch_ev.append(
            f"{len(engines_changed)} engine ownership root(s) changed: "
            + ", ".join(r.key for r in engines_changed[:5])
        )
    entry_changes = [
        f.path
        for f in change.changeset.files
        if any(
            e.entry_point == f.path or e.path == f.path
            for e in arch.engines.values()
        )
    ]
    if entry_changes:
        arch_score += 25
        arch_ev.append(
            f"{len(entry_changes)} engine entry point(s) / public API changed: "
            + ", ".join(sorted(entry_changes)[:5])
        )
    if not arch_ev:
        arch_ev.append("no engine ownership root or entry point changed")
    dims.append(RiskDimension("Architectural Risk", _level(arch_score), arch_score, tuple(arch_ev)))

    # 2. Regression risk — breadth of indirect impact.
    indirect = len(blast.indirect)
    reg_score = min(80, indirect * 2)
    reg_ev = [
        f"{indirect} entities are indirectly impacted across "
        f"{len(blast.traversal_stats.get('graphs_traversed', []))} canonical graphs",
        f"impact by kind: {kinds}",
    ]
    deep = [n for n in blast.indirect if n.depth >= 3]
    if deep:
        reg_score += 10
        reg_ev.append(f"{len(deep)} entities impacted at propagation depth >= 3")
    reg_score = min(100, reg_score)
    dims.append(RiskDimension("Regression Risk", _level(reg_score), reg_score, tuple(reg_ev)))

    # 3. Dependency risk — fan-in of changed entities in dependency graph.
    dep_score = 0
    dep_ev: list[str] = []
    dep_graph = arch.dependency
    dependents: dict[str, int] = {}
    for ref in change.all_entities:
        node_ids = res.node_ids_for(ref)
        count = sum(1 for e in dep_graph.edges if e.target in node_ids)
        if count:
            dependents[ref.ref] = count
    if dependents:
        worst = max(dependents.values())
        dep_score = min(80, worst * 8)
        top = sorted(dependents.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        dep_ev.extend(f"{ref} has {n} direct dependent(s)" for ref, n in top)
    else:
        dep_ev.append("changed entities have no recorded dependents in the dependency graph")
    dims.append(RiskDimension("Dependency Risk", _level(dep_score), dep_score, tuple(dep_ev)))

    # 4. Coverage risk — impacted engines lacking provider-recorded tests.
    cov_score = 0
    cov_ev: list[str] = []
    untested = []
    for node in blast.all_impacted:
        if node.ref.kind != "engine":
            continue
        engine = arch.engines.get(node.ref.key)
        if engine is not None and not engine.tests:
            untested.append(engine.name)
    if untested:
        cov_score = min(90, 30 * len(untested))
        cov_ev.append(
            f"{len(untested)} impacted engine(s) have no provider-recorded tests: "
            + ", ".join(sorted(untested)[:5])
        )
    else:
        cov_ev.append("every impacted engine has at least one recorded test")
    if not blast.verification:
        if plan.selected:
            cov_ev.append(
                "no engine-level test targets, but "
                f"{len(plan.selected)} suite-level verification unit(s) cover "
                "this change: " + ", ".join(u.id for u in plan.selected)
            )
        else:
            cov_score = max(cov_score, 60)
            cov_ev.append(
                "verification impact is empty and no suite was selected: "
                "nothing verifies this change"
            )
    dims.append(RiskDimension("Coverage Risk", _level(cov_score), cov_score, tuple(cov_ev)))

    # 5. Ownership risk — changed paths with no provider owner.
    own_score = 0
    own_ev: list[str] = []
    if change.unmapped_paths:
        own_score = min(85, 20 * len(change.unmapped_paths))
        own_ev.append(
            f"{len(change.unmapped_paths)} changed path(s) have no provider owner: "
            + ", ".join(change.unmapped_paths[:5])
        )
    else:
        own_ev.append("every changed path resolves to a canonical owner")
    if blast.unresolved_nodes:
        own_score = min(100, own_score + 10)
        own_ev.append(
            f"{len(blast.unresolved_nodes)} graph node(s) are not registered in "
            "provider entity tables: " + ", ".join(blast.unresolved_nodes[:5])
        )
    dims.append(RiskDimension("Ownership Risk", _level(own_score), own_score, tuple(own_ev)))

    # 6. Contract risk — endpoint / API surface movement.
    con_score = 0
    con_ev: list[str] = []
    route_changes = sorted(
        {r for f in change.changeset.files for r in f.changed_routes}
    )
    if route_changes:
        con_score += min(70, 25 * len(route_changes))
        con_ev.append(
            f"{len(route_changes)} route declaration(s) edited: "
            + ", ".join(route_changes[:5])
        )
    endpoint_impact = kinds.get("endpoint", 0)
    if endpoint_impact:
        con_score += min(30, endpoint_impact)
        con_ev.append(f"{endpoint_impact} endpoint(s) in blast radius")
    if not con_ev:
        con_ev.append("no endpoint or route declaration affected")
    con_score = min(100, con_score)
    dims.append(RiskDimension("Contract Risk", _level(con_score), con_score, tuple(con_ev)))

    # 7. CI risk — historical CI instability for the impacted surface.
    ci_score = 0
    ci_ev: list[str] = []
    mem = memory or {}
    recurring_ci = mem.get("recurring_ci_failures") or []
    if recurring_ci:
        ci_score = min(75, 15 * len(recurring_ci))
        ci_ev.extend(
            f"recurring CI failure: {item.get('signature', 'unknown')} "
            f"(x{item.get('occurrences', 0)})"
            for item in recurring_ci[:5]
        )
    else:
        ci_ev.append("no recurring CI failure recorded in engineering memory")
    flaky = mem.get("recurring_test_failures") or []
    if flaky:
        ci_score = min(100, ci_score + 10)
        ci_ev.append(f"{len(flaky)} recurring test failure signature(s) known")
    dims.append(RiskDimension("CI Risk", _level(ci_score), ci_score, tuple(ci_ev)))

    # Overall level must never under-report a dimension. Averaging alone would
    # let a single High dimension hide behind six Low ones, so the worst
    # dimension acts as a floor on the reported level.
    overall_score = round(sum(d.score for d in dims) / len(dims))
    mean_level = _level(overall_score)
    worst_level = max((d.level for d in dims), key=_LEVELS.index)
    overall_level = max(mean_level, worst_level, key=_LEVELS.index)

    # Confidence reflects how much of the change the provider could explain.
    # Platform (runtime/) files are excluded from the denominator: they are
    # out of the production architecture's scope by construction, so counting
    # them as "unexplained" would understate confidence.
    total_paths = len(change.changeset.files)
    in_scope = max(0, total_paths - len(change.platform_paths))
    mapped = max(0, in_scope - len(change.unmapped_paths))
    confidence = round(mapped / in_scope, 3) if in_scope else 1.0
    basis = [
        f"{mapped}/{in_scope} in-scope changed paths resolved to canonical entities",
        f"{len(change.platform_paths)} platform (runtime/) path(s) excluded from scope",
        f"{len(blast.unresolved_nodes)} unresolved graph node(s) during propagation",
        f"{len(plan.selected)} verification unit(s) selected from evidence",
    ]
    if change.changeset.source == "unavailable":
        confidence = 0.0
        basis.append("git unavailable: no change input could be observed")

    return EngineeringRisk(
        generated_at=datetime.now(timezone.utc).isoformat(),
        dimensions=tuple(dims),
        overall_level=overall_level,
        overall_score=overall_score,
        confidence=confidence,
        confidence_basis=tuple(basis),
    )
