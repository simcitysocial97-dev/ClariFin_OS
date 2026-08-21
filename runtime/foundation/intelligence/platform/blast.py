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


def _enrich_dto_mapper_impact(
    impacted: dict,
    seeds: tuple,
    seed_refs: set,
    reverse: dict,
    res: Any,
    frontier: Any,
    visited: dict,
    max_depth: int = 3,
) -> None:
    """Bridge DTO → mapper → frontend capability gaps.

    The dependency graph links DTOs to other DTOs (init re-exports) but does
    not link DTOs to consuming mappers across backend/frontend layers. The
    canonical chain map (``backend/src/engines/<e>``) records which
    ``mappers`` and ``viewModels`` a DTO's engine consumes. This function
    uses that bridge to add frontend-side entities when a backend DTO is
    impacted, then lets the normal reverse-edge traversal continue.
    """
    try:
        from runtime.foundation.architecture.chains import get_chain_map
    except Exception:
        return

    chain_map = get_chain_map()
    impacted_refs = {n.ref for n in impacted.values()} | set(seeds)
    dto_nodes = [r for r in impacted_refs if r.kind == "dto"]
    if not dto_nodes:
        return

    for dto_ref in dto_nodes:
        engine_for_dto = res.arch.engine_for_path(dto_ref.path)
        chain = None
        if engine_for_dto is not None:
            chain = chain_map.get(engine_for_dto.path)

        if chain is None:
            engine_name = _infer_engine_from_dto(dto_ref, chain_map)
            for eng_path, cm_chain in chain_map.items():
                if cm_chain.get("engineName") == engine_name:
                    chain = cm_chain
                    break

        if chain is None:
            continue

        for mapper_path in chain.get("mappers", []):
            if not mapper_path.startswith("frontend/"):
                mapper_path = f"frontend/{mapper_path}"
            mapper_full = _resolve_frontend_path(res, mapper_path)
            mapper_ref = _resolve_frontend_entity(res, mapper_full, "mapper")
            if mapper_ref is not None and mapper_ref.ref not in impacted:
                impacted[mapper_ref.ref] = ImpactNode(
                    ref=mapper_ref,
                    depth=1,
                    graph="chain-map",
                    via=dto_ref.ref,
                    relation="consumed-by",
                )
                for node_id in res.node_ids_for(mapper_ref):
                    if node_id not in visited:
                        visited[node_id] = 1
                        frontier.append(
                            (node_id, 1, "chain-map", dto_ref.ref, "consumed-by")
                        )

        for vm_path in chain.get("viewModels", []):
            if not vm_path.startswith("frontend/"):
                vm_path = f"frontend/{vm_path}"
            vm_full = _resolve_frontend_path(res, vm_path)
            vm_ref = _resolve_frontend_entity(res, vm_full, "view_model")
            if vm_ref is not None and vm_ref.ref not in impacted:
                impacted[vm_ref.ref] = ImpactNode(
                    ref=vm_ref,
                    depth=1,
                    graph="chain-map",
                    via=dto_ref.ref,
                    relation="view-model",
                )


def _enrich_backend_bridge_impact(
    impacted: dict,
    seeds: tuple,
    res: Any,
    visited: dict,
    frontier: Any,
) -> None:
    """C4 — propagate standalone backend mapper / router changes to the frontend.

    When a backend ``mapper`` or ``router`` changes, the same chain-map
    relationships that drive ``_enrich_dto_mapper_impact`` record which
    frontend ``mappers`` / ``viewModels`` the owning engine consumes. Those
    frontend entities must also be flagged, exactly as they are for a DTO
    change. Without this, a backend transport/mapping change can silently
    miss the frontend consumer that depends on the exact shape it emits.
    """
    try:
        from runtime.foundation.architecture.chains import get_chain_map
    except Exception:
        return

    chain_map = get_chain_map()
    candidate_refs = {n.ref for n in impacted.values()} | set(seeds)

    def _is_backend_bridge(ref: Any) -> bool:
        if ref.kind not in ("mapper", "router"):
            return False
        return ref.path.startswith("backend/")

    for ref in candidate_refs:
        if not _is_backend_bridge(ref):
            continue

        engine_path = res.arch.engine_for_path(ref.path)
        chain = chain_map.get(engine_path.path) if engine_path is not None else None

        if chain is None:
            engine_name = _infer_engine_from_dto(ref, chain_map)
            if engine_name is not None:
                for eng_path, cm_chain in chain_map.items():
                    if cm_chain.get("engineName") == engine_name:
                        chain = cm_chain
                        break

        if chain is None:
            continue

        for mapper_path in chain.get("mappers", []):
            if not mapper_path.startswith("frontend/"):
                mapper_path = f"frontend/{mapper_path}"
            mapper_full = _resolve_frontend_path(res, mapper_path)
            mapper_ref = _resolve_frontend_entity(res, mapper_full, "mapper")
            if mapper_ref is not None and mapper_ref.ref not in impacted:
                impacted[mapper_ref.ref] = ImpactNode(
                    ref=mapper_ref,
                    depth=1,
                    graph="chain-map",
                    via=ref.ref,
                    relation="consumed-by",
                )
                for node_id in res.node_ids_for(mapper_ref):
                    if node_id not in visited:
                        visited[node_id] = 1
                        frontier.append(
                            (node_id, 1, "chain-map", ref.ref, "consumed-by")
                        )

        for vm_path in chain.get("viewModels", []):
            if not vm_path.startswith("frontend/"):
                vm_path = f"frontend/{vm_path}"
            vm_full = _resolve_frontend_path(res, vm_path)
            vm_ref = _resolve_frontend_entity(res, vm_full, "view_model")
            if vm_ref is not None and vm_ref.ref not in impacted:
                impacted[vm_ref.ref] = ImpactNode(
                    ref=vm_ref,
                    depth=1,
                    graph="chain-map",
                    via=ref.ref,
                    relation="view-model",
                )


def _resolve_frontend_entity(res: Any, path: str, kind: str) -> Any:
    """Resolve a frontend path to an EntityRef of the given kind."""
    refs = res.entities_for_path(path)
    for ref in refs:
        if ref.kind == kind:
            return ref
    return None


def _resolve_frontend_path(res: Any, partial_path: str) -> str:
    """Resolve a partial frontend path (from chain map) to a concrete file path.

    Chain-map entries store paths like ``lib/mappers/loans-mapper`` or
    ``types/loans-view-model`` (without extension or even the ``frontend/``
    prefix). This function tries common extensions to find the actual file
    registered with the provider.
    """
    if res.entities_for_path(partial_path):
        return partial_path
    for ext in (".ts", ".tsx"):
        candidate = f"{partial_path}{ext}"
        if res.entities_for_path(candidate):
            return candidate
    return partial_path


_DTO_ENGINE_HINTS = [
    ("loan", "loan_engine"),
    ("account", "account_engine"),
    ("behaviour", "behaviour_engine"),
    ("behavior", "behaviour_engine"),
    ("cashflow", "behaviour_engine"),
    ("credit_card", "credit_card_engine"),
    ("creditcard", "credit_card_engine"),
    ("reconciliation", "behaviour_engine"),
    ("forecast", "financial_intelligence"),
    ("investment", "financial_intelligence"),
    ("networth", "behaviour_engine"),
    ("dashboard", "behaviour_engine"),
    ("transaction", "transaction_intelligence"),
    ("statement", "account_engine"),
]


def _infer_engine_from_dto(dto_ref: Any, chain_map: dict) -> str | None:
    """Infer the owning engine from a DTO file path.

    Provider evidence: a DTO is consumed by the engine whose services/routers
    reference that DTO. When direct engine resolution is unavailable (DTOs
    are not registered as engine modules), infer the engine by matching the
    DTO's module name against known engine module names and capability
    mappings.
    """
    dto_path_lower = dto_ref.path.lower()

    for eng_path, chain in chain_map.items():
        eng_name = chain.get("engineName", "")
        if eng_name and eng_name.lower() in dto_path_lower:
            return eng_name
        for svc in chain.get("services", []):
            svc_stem = svc.split("/")[-1].replace(".py", "").lower()
            if svc_stem and svc_stem in dto_path_lower:
                return eng_name

    dto_name = dto_ref.path.split("/")[-1].replace("_dto.py", "").lower()
    for keyword, eng_name in _DTO_ENGINE_HINTS:
        if keyword in dto_name:
            return eng_name

    return None


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

    # GAP-004 enrichment: propagate DTO → mapper → frontend/mapper chain.
    # The provider dependency graph does not directly link DTOs to their
    # consuming mappers across layers, so chain-map relationships from the
    # canonical architecture provider are used to bridge that gap.
    _enrich_dto_mapper_impact(
        impacted, seeds, seed_refs, reverse, res, frontier, visited, max_depth
    )
    # C4: standalone backend mapper / router changes must propagate to the
    # frontend entities the same chain records.
    _enrich_backend_bridge_impact(impacted, seeds, res, visited, frontier)

    direct = tuple(
        sorted(
            (
                ImpactNode(
                    ref=r, depth=0, graph="change", via="changed", relation="changed"
                )
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
    developer = tuple(n for n in (*direct, *indirect) if n.ref.kind in _DEVELOPER_KINDS)

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
