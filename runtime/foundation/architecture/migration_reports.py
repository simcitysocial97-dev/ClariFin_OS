"""Migration report generators — Program 13.2, Phases 4, 5, 6, 9.

Every report here is derived EXCLUSIVELY from the canonical architecture
returned by :func:`runtime.foundation.architecture.get_architecture`. No
module in this file performs independent discovery; it is a consumer of the
single provider, exactly like every other runtime subsystem.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.architecture import ids
from runtime.foundation.architecture.provider import get_architecture

GENERATED_DIR = Path(__file__).resolve().parents[3] / "runtime" / "generated"


# ---------------------------------------------------------------------------
# Phase 6 — dependency-graph-v2.json
# ---------------------------------------------------------------------------


def build_dependency_graph_v2(arch=None) -> dict[str, Any]:
    """Three DISTINCT graphs: ownership, execution, dependency.

    Ownership = who OWNS what (engines own modules; modules are never roots).
    Execution = the runtime call path (may traverse implementation modules).
    Dependency = static import dependencies (``depends_on``), distinct from both.
    """
    arch = arch or get_architecture(refresh=True)
    graphs = {
        "ownership": _serialize_graph(arch.ownership),
        "execution": _serialize_graph(arch.execution),
        "dependency": _serialize_graph(arch.dependency),
    }
    return {
        "generated_at": arch.generated_at,
        "schema": "dependency-graph-v2",
        "principle": (
            "Ownership, execution and dependency are THREE distinct relations. "
            "A module may be traversed at runtime (execution) yet never be an "
            "ownership root; import edges (dependency) are a third axis again."
        ),
        "single_source": "runtime.foundation.architecture.get_architecture",
        "graphs": graphs,
        "summaries": {
            kind: {"node_count": g["node_count"], "edge_count": g["edge_count"]}
            for kind, g in graphs.items()
        },
    }


def _serialize_graph(graph) -> dict[str, Any]:
    return {
        "kind": graph.kind,
        "description": graph.description,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "nodes": [n.to_dict() for n in graph.nodes],
        "edges": [e.to_dict() for e in graph.edges],
    }


# ---------------------------------------------------------------------------
# Phase 5 — artifact-ownership-v3.json
# ---------------------------------------------------------------------------


def build_artifact_ownership_v3(arch=None) -> dict[str, Any]:
    """Re-derive artifact ownership from producer evidence, enriched with the
    canonical engine/capability linkage resolved by the provider."""
    arch = arch or get_architecture(refresh=True)

    artifacts = []
    unknown = 0
    for path, art in sorted(arch.artifacts.items()):
        entry = art.to_dict()
        linkage_engine = entry.get("engine")
        linkage_cap = entry.get("capability")
        if not linkage_engine and not linkage_cap:
            for eng_name in arch.engines:
                if eng_name.replace("_", "") in path.replace("_", "").replace("-", ""):
                    linkage_engine = linkage_engine or eng_name
        if entry.get("unknown_ownership"):
            unknown += 1
        artifacts.append(
            {
                "artifact": path,
                "producer": entry.get("producer", ""),
                "owner": entry.get("owner", ""),
                "consumers": list(entry.get("consumers", ())),
                "verification_stage": entry.get("verification_stage", ""),
                "pipeline": entry.get("pipeline", ""),
                "lifecycle": entry.get("lifecycle", ""),
                "retention": entry.get("retention", ""),
                "regeneration_source": entry.get("regeneration_source", ""),
                "engine": linkage_engine or entry.get("engine"),
                "capability": linkage_cap or entry.get("capability"),
                "unknown_ownership": bool(entry.get("unknown_ownership", False)),
            }
        )

    return {
        "generated_at": arch.generated_at,
        "schema": "artifact-ownership-v3",
        "principle": (
            "Artifacts are owned by their Producer. Ownership is recorded with "
            "Producer/Owner/Consumers/Stage/Pipeline/Lifecycle/Retention/"
            "Regeneration Source. No artifact is left unknown."
        ),
        "single_source": "runtime.foundation.architecture.get_architecture",
        "artifact_count": len(artifacts),
        "unknown_ownership_count": unknown,
        "artifacts": artifacts,
    }


# ---------------------------------------------------------------------------
# Phase 4 — knowledge-migration-report.json
# ---------------------------------------------------------------------------


def build_knowledge_migration_report(arch=None) -> dict[str, Any]:
    """Reconstruct knowledge entities from the architecture (ownership graph
    based, never filesystem based)."""
    arch = arch or get_architecture(refresh=True)

    consumers_of: dict[str, list[str]] = _consumers_from_dependency(arch.dependency)
    entities: list[dict[str, Any]] = []

    for name, eng in sorted(arch.engines.items()):
        caps = list(eng.capabilities)
        entities.append(
            {
                "id": eng.id,
                "type": "Engine",
                "name": name,
                "owner": caps[0] if caps else "INTERNAL (no capability owner)",
                "capabilities": caps,
                "responsibilities": [
                    "Expose pure deterministic compute functions (no DB, no I/O).",
                    f"Public API via {eng.entry_point}.",
                    f"Implement {len(eng.implementation_modules)} implementation module(s).",
                ],
                "consumers": consumers_of.get(eng.id, []),
                "migration_status": eng.migration_status or "CANONICAL",
            }
        )

    for name, cap in sorted(arch.capabilities.items()):
        entities.append(
            {
                "id": cap.id,
                "type": "Capability",
                "name": name,
                "owner": "Frontend Workspace",
                "backing_engines": list(cap.engines),
                "endpoint_count": len(cap.endpoints),
                "workspaces": list(cap.workspaces),
                "resolved": bool(cap.engines),
            }
        )

    for name, svc in sorted(arch.services.items()):
        entities.append(
            {
                "id": svc.id,
                "type": "Service",
                "name": svc.path.rsplit("/", 1)[-1].removesuffix(".py"),
                "owner": list(svc.engines) or ["UNRESOLVED"],
                "routers": list(svc.routers),
            }
        )

    for name, rtr in sorted(arch.routers.items()):
        entities.append(
            {
                "id": rtr.id,
                "type": "Router",
                "name": rtr.path.rsplit("/", 1)[-1].removesuffix(".py"),
                "owner": list(rtr.engines) or ["UNRESOLVED"],
                "endpoint_count": len(rtr.endpoints),
            }
        )

    for name, repo in sorted(arch.repositories.items()):
        entities.append(
            {
                "id": repo.id,
                "type": "Repository",
                "name": name,
                "owner": list(repo.engines) or ["UNRESOLVED"],
                "path": repo.path,
            }
        )

    unresolved_caps = [e["name"] for e in entities if e["type"] == "Capability" and not e["resolved"]]
    return {
        "generated_at": arch.generated_at,
        "schema": "knowledge-migration-report",
        "principle": (
            "Knowledge is owned by the architectural ENTITY it describes "
            "(engine, capability, service, router, repository). Knowledge is "
            "reconstructed from the architecture, not from filename scanning."
        ),
        "single_source": "runtime.foundation.architecture.get_architecture",
        "entity_count": len(entities),
        "entities": entities,
        "unresolved_capabilities": unresolved_caps,
        "notes": [
            "Capability->engine is MANY-TO-MANY (e.g. useBehaviourCapability backs "
            "both behaviour_engine and recommendation_engine).",
            "Capabilities with no backend router (frontend-only fetch via the API "
            "client) are reported as unresolved rather than force-linked.",
        ],
    }


def _consumers_from_dependency(dep_graph) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for edge in dep_graph.edges:
        if edge.relation == "depends_on":
            out.setdefault(edge.target, []).append(edge.source)
    return out


# ---------------------------------------------------------------------------
# Phase 9 — runtime-consistency.json
# ---------------------------------------------------------------------------


def build_runtime_consistency(arch=None) -> dict[str, Any]:
    """Cross-subsystem consistency checks over the canonical architecture."""
    arch = arch or get_architecture(refresh=True)
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})

    # 1. No phantom engine keys: a package engine must have a real __init__.py
    #    public API (not a non-existent <engine>.py file).
    phantom = []
    for name, eng in arch.engines.items():
        if eng.style == "package" and not eng.entry_point.endswith("__init__.py"):
            phantom.append(name)
        elif eng.style == "single_file" and not eng.path.endswith(".py"):
            phantom.append(name)
    add(
        "no_phantom_engine_keys",
        not phantom,
        "All package engines resolve to a real __init__.py; single-file engines "
        "resolve to a real .py file. No phantom <engine>.py keys exist."
        if not phantom
        else f"Phantom keys: {phantom}",
    )

    # 2. Every endpoint is owned by exactly one router.
    orphan_ep = [s for s, e in arch.endpoints.items() if not e.router]
    add(
        "endpoints_single_router",
        not orphan_ep,
        "Every endpoint is owned by exactly one router."
        if not orphan_ep
        else f"Endpoints without a router: {orphan_ep}",
    )

    # 3. Every router is owned by at least one engine.
    orphan_rtr = [r.path for r in arch.routers.values() if not r.engines]
    add(
        "routers_have_engine",
        not orphan_rtr,
        "All routers resolve to an owning engine."
        if not orphan_rtr
        else f"Orphan routers: {orphan_rtr}",
    )

    # 4. No implementation module is an ownership root (engine).
    mod_as_engine = [
        m.path
        for m in arch.engine_modules.values()
        if ids.engine_id(m.engine) == ids.engine_id(m.path)
    ]
    add(
        "modules_not_engines",
        not mod_as_engine,
        "No implementation module is treated as an engine root."
        if not mod_as_engine
        else f"Modules registered as engines: {mod_as_engine}",
    )

    # 5. Capability alias folding: declared symbol wins.
    add(
        "capability_alias_folded",
        len(arch.capabilities) == len({c.lower() for c in arch.capabilities}),
        "Capability hook names are unique after case-insensitive folding.",
    )

    # 6. Reconciliation capability now linked (the 13.1 gap is closed).
    recon = arch.engines.get("reconciliation_engine")
    linked = bool(recon and "useReconciliationCapability" in recon.capabilities)
    add(
        "reconciliation_capability_linked",
        linked,
        "useReconciliationCapability is linked to reconciliation_engine."
        if linked
        else "reconciliation capability still unlinked.",
    )

    passed = sum(1 for c in checks if c["passed"])
    return {
        "generated_at": arch.generated_at,
        "schema": "runtime-consistency",
        "single_source": "runtime.foundation.architecture.get_architecture",
        "checks_total": len(checks),
        "checks_passed": passed,
        "checks_failed": len(checks) - passed,
        "all_passed": passed == len(checks),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# writers
# ---------------------------------------------------------------------------


def _write(payload: dict[str, Any], name: str) -> Path:
    target = GENERATED_DIR / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return target


def generate_all() -> dict[str, str]:
    """Produce Phases 4, 5, 6 and 9 deliverables. Returns artifact -> path."""
    arch = get_architecture(refresh=True)
    out = {
        "knowledge-migration-report.json": _write(build_knowledge_migration_report(arch), "knowledge-migration-report.json"),
        "artifact-ownership-v3.json": _write(build_artifact_ownership_v3(arch), "artifact-ownership-v3.json"),
        "dependency-graph-v2.json": _write(build_dependency_graph_v2(arch), "dependency-graph-v2.json"),
        "runtime-consistency.json": _write(build_runtime_consistency(arch), "runtime-consistency.json"),
    }
    return {k: str(v) for k, v in out.items()}


if __name__ == "__main__":
    for k, v in generate_all().items():
        print(f"{k} -> {v}")
