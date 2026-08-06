"""Phase 2 — Blast Radius Engine.

Propagates a change across the canonical graphs to answer "what else is
affected?".

Propagation direction
---------------------
Canonical edges point from *consumer to provider*::

    service -> engine            (service uses engine)
    capability -> endpoint -> router
    engine -> module             (ownership)

Therefore impact flows along **reverse** edges: if an engine changed, its
dependents (services, capabilities, endpoints) are impacted. Forward ownership
edges are followed separately, but only to collect owned tests, because an
engine owning a test means the test verifies it.

Every propagation step records the edge that justified it, so the resulting
blast radius is evidence-backed and reproducible rather than asserted.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from runtime.foundation.intelligence.platform.change import ChangeIntelligence
from runtime.foundation.intelligence.platform.resolver import (
    EntityRef,
    EntityResolver,
    get_resolver,
)

__all__ = ["BlastRadius", "ImpactNode", "compute_blast_radius", "DEFAULT_MAX_DEPTH"]

DEFAULT_MAX_DEPTH = 6

# Which impacted entity kinds are visible to end users vs. developers.
_USER_VISIBLE_KINDS = {"endpoint", "capability", "workspace", "component", "view_model"}
_DEVELOPER_KINDS = {
    "engine",
    "engine_module",
    "detector",
    "service",
    "repository",
    "mapper",
    "dto",
    "facade",
    "router",
}


@dataclass(frozen=True, slots=True)
class ImpactNode:
    """One impacted entity plus the evidence chain that reached it."""

    ref: EntityRef
    depth: int
    graph: str
    via: str
    relation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ref": self.ref.ref,
            "kind": self.ref.kind,
            "key": self.ref.key,
            "path": self.ref.path,
            "depth": self.depth,
            "evidence": {
                "graph": self.graph,
                "via": self.via,
                "relation": self.relation,
            },
        }


@dataclass(frozen=True, slots=True)
class BlastRadius:
    generated_at: str
    seeds: tuple[EntityRef, ...]
    direct: tuple[ImpactNode, ...]
    indirect: tuple[ImpactNode, ...]
    verification: tuple[EntityRef, ...]
    user_visible: tuple[ImpactNode, ...]
    developer: tuple[ImpactNode, ...]
    unresolved_nodes: tuple[str, ...]
    max_depth: int
    traversal_stats: dict[str, Any] = field(default_factory=dict)

    @property
    def impacted_engines(self) -> tuple[EntityRef, ...]:
        seen = {
            n.ref.ref: n.ref
            for n in (*self.direct, *self.indirect)
            if n.ref.kind == "engine"
        }
        return tuple(sorted(seen.values(), key=lambda r: r.ref))

    @property
    def all_impacted(self) -> tuple[ImpactNode, ...]:
        return tuple(self.direct) + tuple(self.indirect)

    def kinds(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for node in self.all_impacted:
            counts[node.ref.kind] = counts.get(node.ref.kind, 0) + 1
        return dict(sorted(counts.items()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "blast-radius/v1",
            "generated_at": self.generated_at,
            "provider": "runtime.foundation.architecture.get_architecture",
            "graphs": ["ownership", "execution", "dependency"],
            "propagation": "reverse edges (dependents), evidence-backed",
            "max_depth": self.max_depth,
            "seeds": [r.to_dict() for r in self.seeds],
            "direct_impact": [n.to_dict() for n in self.direct],
            "indirect_impact": [n.to_dict() for n in self.indirect],
            "verification_impact": [r.to_dict() for r in self.verification],
            "user_visible_impact": [n.to_dict() for n in self.user_visible],
            "developer_impact": [n.to_dict() for n in self.developer],
            "counts": {
                "seeds": len(self.seeds),
                "direct": len(self.direct),
                "indirect": len(self.indirect),
                "verification": len(self.verification),
                "user_visible": len(self.user_visible),
                "developer": len(self.developer),
                "by_kind": self.kinds(),
            },
            "unresolved_nodes": list(self.unresolved_nodes),
            "traversal": self.traversal_stats,
        }


def _reverse_index(graph: Any) -> dict[str, list[Any]]:
    index: dict[str, list[Any]] = {}
    for edge in graph.edges:
        index.setdefault(edge.target, []).append(edge)
    return index


def _forward_index(graph: Any) -> dict[str, list[Any]]:
    index: dict[str, list[Any]] = {}
    for edge in graph.edges:
        index.setdefault(edge.source, []).append(edge)
    return index


def compute_blast_radius(
    change: ChangeIntelligence,
    resolver: EntityResolver | None = None,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> BlastRadius:
    """Deterministically propagate ``change`` across the canonical graphs."""
    res = resolver or get_resolver()
    graphs = res.graphs()

    seeds = change.all_entities
    seed_refs = {r.ref for r in seeds}

    # Seed node ids: every graph id form that maps back to a seed entity.
    frontier: deque[tuple[str, int, str, str, str]] = deque()
    visited: dict[str, int] = {}
    for ref in seeds:
        for node_id in res.node_ids_for(ref):
            if node_id not in visited:
                visited[node_id] = 0
                frontier.append((node_id, 0, "seed", "seed", "seed"))

    reverse = {name: _reverse_index(g) for name, g in graphs.items()}
    forward = {name: _forward_index(g) for name, g in graphs.items()}

    impacted: dict[str, ImpactNode] = {}
    unresolved: set[str] = set()
    edges_followed = 0

    while frontier:
        node_id, depth, graph_name, via, relation = frontier.popleft()

        entity = res.resolve_node(node_id)
        if entity is None:
            unresolved.add(node_id)
        elif depth > 0:
            existing = impacted.get(entity.ref)
            if existing is None or depth < existing.depth:
                impacted[entity.ref] = ImpactNode(
                    ref=entity,
                    depth=depth,
                    graph=graph_name,
                    via=via,
                    relation=relation,
                )

        if depth >= max_depth:
            continue

        for name, index in reverse.items():
            for edge in index.get(node_id, ()):
                edges_followed += 1
                nxt = edge.source
                if nxt in visited and visited[nxt] <= depth + 1:
                    continue
                visited[nxt] = depth + 1
                frontier.append((nxt, depth + 1, name, node_id, edge.relation))

    # Verification impact: tests the provider says verify an impacted engine.
    verification: dict[str, EntityRef] = {}
    engine_candidates = {
        r.ref: r
        for r in list(seeds) + [n.ref for n in impacted.values()]
        if r.kind == "engine"
    }
    for ref in engine_candidates.values():
        engine = res.arch.engines.get(ref.key)
        if engine is None:
            continue
        for test_path in engine.tests:
            test_ref = res.resolve_node(f"test:{test_path}")
            if test_ref is not None:
                verification[test_ref.ref] = test_ref

    # Ownership forward edges also record Test nodes directly.
    ownership_forward = forward["ownership"]
    for ref in engine_candidates.values():
        for node_id in res.node_ids_for(ref):
            for edge in ownership_forward.get(node_id, ()):
                target = res.resolve_node(edge.target)
                if target is not None and target.kind == "test":
                    verification[target.ref] = target

    # Tests explicitly changed are always verification-relevant.
    for ref in seeds:
        if ref.kind == "test":
            verification[ref.ref] = ref

    direct = tuple(
        sorted(
            (
                ImpactNode(ref=r, depth=0, graph="change", via="changed", relation="changed")
                for r in seeds
            ),
            key=lambda n: n.ref.ref,
        )
    )
    indirect = tuple(
        sorted(
            (n for n in impacted.values() if n.ref.ref not in seed_refs),
            key=lambda n: (n.depth, n.ref.ref),
        )
    )
    user_visible = tuple(
        n for n in (*direct, *indirect) if n.ref.kind in _USER_VISIBLE_KINDS
    )
    developer = tuple(
        n for n in (*direct, *indirect) if n.ref.kind in _DEVELOPER_KINDS
    )

    return BlastRadius(
        generated_at=datetime.now(timezone.utc).isoformat(),
        seeds=seeds,
        direct=direct,
        indirect=indirect,
        verification=tuple(sorted(verification.values(), key=lambda r: r.ref)),
        user_visible=user_visible,
        developer=developer,
        unresolved_nodes=tuple(sorted(unresolved)),
        max_depth=max_depth,
        traversal_stats={
            "nodes_visited": len(visited),
            "edges_followed": edges_followed,
            "graphs_traversed": sorted(graphs),
        },
    )
