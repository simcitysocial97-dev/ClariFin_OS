"""Provider-backed chain projection — Program 13.3, Phase 2.

Runtime subsystems (planner, workspace, evidence, integrity, observability)
historically read ``runtime/generated/cross-layer-map.json`` from disk. That
file is now only an OPTIONAL EXPORT artifact; it must never be an operational
runtime dependency.

This module gives those consumers the same *shape* of data, but computed
in-memory from the single canonical architecture provider
(:func:`runtime.foundation.architecture.get_architecture`). There is no file
read, no rediscovery, no ownership invention: every field is a projection of
provider state.

The projection is cached per-Architecture-instance, so the provider still
initialises exactly once and all consumers share one structure.
"""

from __future__ import annotations

import json
from typing import Any

from runtime.foundation.architecture.models import Architecture
from runtime.foundation.architecture.provider import GENERATED_DIR, get_architecture

__all__ = ["build_chain_map", "get_chain_map", "chain_for_path", "reset_cache"]

_CACHE: dict[int, dict[str, dict[str, Any]]] = {}


def _engine_key(engine: Any) -> str:
    """Canonical chain key: the engine's ownership root path.

    Package engines key on the package directory, single-file engines on the
    file. This is provider state, never a filename heuristic.
    """
    return engine.path


def _inventory_imports(arch: Architecture, path: str) -> list[str]:
    """Imports recorded for a frontend module by the discovery pipeline.

    Source of truth is the canonical architecture-inventory artifact, not a
    filename heuristic.
    """
    cache = getattr(_inventory_imports, "_cache", None)
    if cache is None:
        inventory_path = GENERATED_DIR / "architecture-inventory.json"
        try:
            data = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {"modules": []}
        cache = {m["path"]: m.get("imports", []) for m in data.get("modules", [])}
        _inventory_imports._cache = cache  # type: ignore[attr-defined]
    return cache.get(path, [])


def _frontend_projection(
    arch: Architecture, capabilities: tuple[str, ...]
) -> dict[str, list[str]]:
    workspaces: set[str] = set()
    components: set[str] = set()
    pages: set[str] = set()
    graph_renderers: set[str] = set()
    mappers: set[str] = set()
    view_models: set[str] = set()

    for cap_name in capabilities:
        cap = arch.capabilities.get(cap_name)
        if cap is None:
            continue
        if cap.path:
            for imp in _inventory_imports(arch, cap.path):
                if "/mappers/" in imp:
                    mappers.add(imp.removeprefix("@/"))
                if "view-model" in imp or imp.endswith("ViewModel"):
                    view_models.add(imp.removeprefix("@/"))
        for ws_name in cap.workspaces:
            ws = arch.workspaces.get(ws_name)
            if ws is None:
                continue
            workspaces.add(ws_name)
            if ws.path:
                pages.add(ws.path)
            for comp in ws.components:
                components.add(comp)
                if "/graph/" in comp or comp.endswith("graph-renderer"):
                    graph_renderers.add(f"frontend/{comp}.tsx")

    return {
        "workspace": sorted(workspaces),
        "pages": sorted(pages),
        "components": sorted(components),
        "graphRenderers": sorted(graph_renderers),
        "mappers": sorted(mappers),
        "viewModels": sorted(view_models),
    }


def build_chain_map(arch: Architecture | None = None) -> dict[str, dict[str, Any]]:
    """Build the flat chain map (engine root path -> chain) from the provider."""
    architecture = arch or get_architecture()
    chains: dict[str, dict[str, Any]] = {}

    for engine in architecture.engines.values():
        key = _engine_key(engine)
        frontend = _frontend_projection(architecture, engine.capabilities)
        chains[key] = {
            "engine": key,
            "engineId": engine.id,
            "engineName": engine.name,
            "engineStyle": engine.style,
            "entryPoint": engine.entry_point,
            "internal": engine.internal,
            "modules": list(engine.implementation_modules),
            "detectors": list(engine.detectors),
            "services": list(engine.services),
            "routers": list(engine.routers),
            "repositories": list(engine.repositories),
            "endpoints": list(engine.endpoints),
            "capabilities": list(engine.capabilities),
            "mappers": [],
            "viewModels": [],
            "tests": list(engine.tests),
            "artifacts": list(engine.artifacts),
            **frontend,
        }

    return chains


def get_chain_map(arch: Architecture | None = None) -> dict[str, dict[str, Any]]:
    """Cached provider-derived chain map. Shared by every runtime consumer."""
    architecture = arch or get_architecture()
    key = id(architecture)
    cached = _CACHE.get(key)
    if cached is None:
        cached = build_chain_map(architecture)
        _CACHE.clear()
        _CACHE[key] = cached
    return cached


def chain_for_path(
    path: str, arch: Architecture | None = None
) -> dict[str, Any] | None:
    """Resolve the chain owning ``path`` via provider ownership (no heuristics)."""
    architecture = arch or get_architecture()
    engine = architecture.engine_for_path(path)
    if engine is None:
        return None
    return get_chain_map(architecture).get(_engine_key(engine))


def reset_cache() -> None:
    _CACHE.clear()
