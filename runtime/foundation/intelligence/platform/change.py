"""Phase 1 — Engineering Change Intelligence.

Turns a raw :class:`ChangeSet` (files/symbols/imports) into *architectural*
change facts: which engines, modules, capabilities, routers, endpoints,
workspaces, components and tests actually changed.

Every mapping is provider-resolved. A path becomes an engine because
``Architecture.engine_for_path`` says so, never because it looks like one.
Paths the provider does not recognise are reported under ``unmapped`` rather
than being force-fitted into a category.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from runtime.foundation.intelligence.platform.changeset import (
    ChangeSet,
    collect_changeset,
)
from runtime.foundation.intelligence.platform.resolver import (
    EntityRef,
    EntityResolver,
    get_resolver,
)

__all__ = ["ChangeIntelligence", "analyze_changes"]

# Categories reported in change-intelligence.json, mapped from entity kinds.
_CATEGORY_BY_KIND = {
    "engine": "engines",
    "engine_module": "modules",
    "detector": "modules",
    "facade": "modules",
    "capability": "capabilities",
    "router": "routers",
    "endpoint": "endpoints",
    "service": "services",
    "repository": "repositories",
    "workspace": "workspaces",
    "component": "components",
    "mapper": "mappers",
    "dto": "dtos",
    "view_model": "view_models",
    "test": "tests",
    "artifact": "artifacts",
}

_CATEGORIES = (
    "engines",
    "modules",
    "capabilities",
    "routers",
    "endpoints",
    "services",
    "repositories",
    "workspaces",
    "components",
    "mappers",
    "dtos",
    "view_models",
    "tests",
    "artifacts",
)


@dataclass(frozen=True, slots=True)
class ChangeIntelligence:
    generated_at: str
    changeset: ChangeSet
    entities: dict[str, tuple[EntityRef, ...]]
    owning_engines: tuple[EntityRef, ...]
    changed_endpoints: tuple[EntityRef, ...]
    unmapped_paths: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]
    platform_paths: tuple[str, ...] = ()

    @property
    def all_entities(self) -> tuple[EntityRef, ...]:
        seen: dict[str, EntityRef] = {}
        for refs in self.entities.values():
            for ref in refs:
                seen[ref.ref] = ref
        return tuple(sorted(seen.values(), key=lambda r: r.ref))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "change-intelligence/v1",
            "generated_at": self.generated_at,
            "provider": "runtime.foundation.architecture.get_architecture",
            "discovery": "none (provider-resolved)",
            "changeset": self.changeset.to_dict(),
            "changed": {
                category: [r.to_dict() for r in self.entities.get(category, ())]
                for category in _CATEGORIES
            },
            "counts": {
                category: len(self.entities.get(category, ()))
                for category in _CATEGORIES
            },
            "owning_engines": [r.to_dict() for r in self.owning_engines],
            "changed_endpoints": [r.to_dict() for r in self.changed_endpoints],
            "unmapped_paths": list(self.unmapped_paths),
            "platform_paths": list(self.platform_paths),
            "path_scopes": {
                "note": (
                    "the canonical provider models PRODUCTION architecture; "
                    "Engineering Runtime files under runtime/ are the platform "
                    "itself and are out of that scope by construction, so they "
                    "are reported separately from genuinely unowned paths"
                ),
                "platform": len(self.platform_paths),
                "unmapped": len(self.unmapped_paths),
            },
            "evidence": list(self.evidence),
        }


def _is_platform_path(path: str) -> bool:
    """True for Engineering Runtime files.

    The provider deliberately models production architecture only, so runtime/
    files having no production owner is expected, not a defect. Reporting them
    as "unowned" would inflate ownership risk with false positives.
    """
    return path.startswith("runtime/") or path.startswith("tools/")


def _endpoints_for(
    resolver: EntityResolver, refs: list[EntityRef], routes: set[str]
) -> list[EntityRef]:
    """Endpoints touched, via router ownership plus literal route edits."""
    arch = resolver.arch
    found: dict[str, EntityRef] = {}

    for ref in refs:
        if ref.kind == "router":
            router = arch.routers.get(ref.key)
            if router is not None:
                for ep_key in router.endpoints:
                    endpoint = arch.endpoints.get(ep_key)
                    if endpoint is not None:
                        resolved = resolver.resolve_node(endpoint.id)
                        if resolved is not None:
                            found[resolved.ref] = resolved
        elif ref.kind == "engine":
            engine = arch.engines.get(ref.key)
            if engine is not None:
                for ep_key in engine.endpoints:
                    endpoint = arch.endpoints.get(ep_key)
                    if endpoint is not None:
                        resolved = resolver.resolve_node(endpoint.id)
                        if resolved is not None:
                            found[resolved.ref] = resolved

    for signature in routes:
        resolved = resolver.resolve_node(f"endpoint:{signature}")
        if resolved is not None:
            found[resolved.ref] = resolved

    return sorted(found.values(), key=lambda r: r.ref)


def analyze_changes(
    changeset: ChangeSet | None = None,
    resolver: EntityResolver | None = None,
    paths: list[str] | None = None,
) -> ChangeIntelligence:
    """Deterministically map a change set onto canonical architecture."""
    res = resolver or get_resolver()
    cs = changeset if changeset is not None else collect_changeset(paths=paths)

    buckets: dict[str, dict[str, EntityRef]] = {c: {} for c in _CATEGORIES}
    owning: dict[str, EntityRef] = {}
    unmapped: list[str] = []
    platform_paths: list[str] = []
    evidence: list[dict[str, Any]] = []
    routes: set[str] = set()
    direct_refs: list[EntityRef] = []

    for changed in cs.files:
        routes.update(changed.changed_routes)
        refs = res.classify_path(changed.path)
        if not refs:
            if _is_platform_path(changed.path):
                platform_paths.append(changed.path)
                evidence.append(
                    {
                        "path": changed.path,
                        "resolution": "platform",
                        "reason": (
                            "Engineering Runtime file; outside the production "
                            "architecture the provider models"
                        ),
                    }
                )
            else:
                unmapped.append(changed.path)
                evidence.append(
                    {
                        "path": changed.path,
                        "resolution": "unmapped",
                        "reason": "no provider entity or engine owns this path",
                    }
                )
            continue

        direct_refs.extend(refs)
        for ref in refs:
            category = _CATEGORY_BY_KIND.get(ref.kind)
            if category:
                buckets[category][ref.ref] = ref

        engine = res.owning_engine(changed.path)
        if engine is not None:
            owning[engine.ref] = engine
            buckets["engines"][engine.ref] = engine

        evidence.append(
            {
                "path": changed.path,
                "status": changed.status,
                "resolution": "provider",
                "entities": [r.ref for r in refs],
                "owning_engine": engine.ref if engine else None,
                "changed_symbols": list(changed.changed_symbols),
                "changed_imports": list(changed.changed_imports),
                "changed_routes": list(changed.changed_routes),
            }
        )

    endpoints = _endpoints_for(res, direct_refs, routes)
    for endpoint in endpoints:
        buckets["endpoints"][endpoint.ref] = endpoint

    # Tests that the provider associates with a changed engine are themselves
    # part of the change surface.
    for engine_ref in list(buckets["engines"].values()):
        engine = res.arch.engines.get(engine_ref.key)
        if engine is None:
            continue
        for test_path in engine.tests:
            test_ref = res.resolve_node(f"test:{test_path}")
            if test_ref is not None:
                buckets["tests"].setdefault(test_ref.ref, test_ref)

    entities = {
        category: tuple(sorted(refs.values(), key=lambda r: r.ref))
        for category, refs in buckets.items()
    }

    return ChangeIntelligence(
        generated_at=datetime.now(timezone.utc).isoformat(),
        changeset=cs,
        entities=entities,
        owning_engines=tuple(sorted(owning.values(), key=lambda r: r.ref)),
        changed_endpoints=tuple(endpoints),
        unmapped_paths=tuple(sorted(unmapped)),
        platform_paths=tuple(sorted(platform_paths)),
        evidence=tuple(evidence),
    )
