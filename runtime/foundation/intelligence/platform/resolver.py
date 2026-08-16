"""Canonical entity resolution for the Engineering Intelligence Layer.

Every intelligence subsystem needs to answer three questions:

1. "Which architectural entity owns this repository path?"
2. "Which graph nodes represent this entity?"
3. "Which entity does this graph node id refer to?"

All three are answered here, once, from provider state. Without this module
each phase would be tempted to re-derive ownership from filenames, which the
constitution forbids.

Why an ID reconciler is required
--------------------------------
The canonical graphs do not use a single ID form for the same entity. For
example a capability appears as ``capability:useAccountsCapability`` in the
execution graph but as
``capability:frontend/lib/capabilities/use-accounts-capability.ts`` in the
dependency graph. Rather than guessing, this resolver registers *every* ID
form that provider state itself justifies (provider id, ``kind:key``,
``kind:path``, ``kind:name``) and maps them all back to one canonical
:class:`EntityRef`. Any graph node whose id cannot be justified by provider
state is reported as unresolved rather than silently invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from runtime.foundation.architecture import Architecture, get_architecture

__all__ = ["EntityRef", "EntityResolver", "get_resolver", "reset_resolver"]


@dataclass(frozen=True, slots=True)
class EntityRef:
    """A canonical reference to one architectural entity."""

    kind: str
    key: str
    id: str
    name: str = ""
    path: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "key": self.key,
            "id": self.id,
            "name": self.name,
            "path": self.path,
        }

    @property
    def ref(self) -> str:
        """Stable cross-artifact reference string."""
        return f"{self.kind}:{self.key}"


# Kinds that own repository paths, ordered most specific first. Ownership of a
# path is resolved against provider state only.
_PATH_KINDS = (
    "engine_module",
    "detector",
    "router",
    "service",
    "capability",
    "workspace",
    "component",
    "mapper",
    "dto",
    "view_model",
    "facade",
    "test",
    "artifact",
    "engine",
)


class EntityResolver:
    """Read-only index over provider state. Performs no discovery."""

    def __init__(self, architecture: Architecture | None = None) -> None:
        self.arch: Architecture = architecture or get_architecture()
        self._by_ref: dict[str, EntityRef] = {}
        self._by_path: dict[str, list[EntityRef]] = {}
        self._by_node_id: dict[str, EntityRef] = {}
        self._tests: dict[str, EntityRef] = {}
        self._build()

    # -- construction -----------------------------------------------------

    def _register(
        self,
        kind: str,
        key: str,
        entity_id: str,
        name: str = "",
        path: str = "",
        aliases: Iterable[str] = (),
    ) -> EntityRef:
        ref = EntityRef(kind=kind, key=key, id=entity_id, name=name, path=path)
        self._by_ref[ref.ref] = ref
        if path:
            self._by_path.setdefault(path, []).append(ref)

        # Register every ID form that provider state justifies.
        forms = {entity_id, f"{kind}:{key}"}
        if path:
            forms.add(f"{kind}:{path}")
        if name:
            forms.add(f"{kind}:{name}")
        forms.update(aliases)
        for form in forms:
            # First registration wins; identical entities never conflict.
            self._by_node_id.setdefault(form, ref)
        return ref

    def _build(self) -> None:
        arch = self.arch

        for key, eng in arch.engines.items():
            self._register(
                "engine",
                key,
                eng.id,
                name=eng.name,
                path=eng.path,
                aliases={
                    f"engine:{eng.name}",
                    f"{eng.id}:entry",
                    f"engine:{eng.entry_point}",
                },
            )
            # An engine also owns its entry point path.
            if eng.entry_point:
                self._by_path.setdefault(eng.entry_point, []).append(
                    self._by_ref[f"engine:{key}"]
                )
            for test in eng.tests:
                self._tests[test] = self._register(
                    "test", test, f"test:{test}", path=test
                )

        for key, mod in arch.engine_modules.items():
            self._register("engine_module", key, mod.id, name=mod.name, path=mod.path,
                           aliases={f"module:{mod.path}"})
        for key, det in arch.detectors.items():
            self._register("detector", key, det.id, name=det.name, path=det.path,
                           aliases={f"module:{det.path}", f"detector:{det.path}"})
        for key, fac in arch.facades.items():
            self._register("facade", key, fac.id, path=fac.path)
        for key, cap in arch.capabilities.items():
            self._register("capability", key, cap.id, name=cap.name, path=cap.path)
        for key, rt in arch.routers.items():
            self._register("router", key, rt.id, name=rt.name, path=rt.path)
        for key, ep in arch.endpoints.items():
            self._register("endpoint", key, ep.id, name=ep.signature,
                           aliases={f"endpoint:{ep.signature}"})
        for key, svc in arch.services.items():
            self._register("service", key, svc.id, name=svc.name, path=svc.path)
        for key, repo in arch.repositories.items():
            self._register("repository", key, repo.id, name=repo.name, path=repo.path)
        for key, ws in arch.workspaces.items():
            self._register("workspace", key, ws.id, name=ws.name, path=ws.path)
        for key, comp in arch.components.items():
            self._register("component", key, comp.id, name=comp.name, path=comp.path)
        for key, mp in arch.mappers.items():
            self._register("mapper", key, mp.id, name=mp.name, path=mp.path)
        for key, dto in arch.dtos.items():
            self._register("dto", key, dto.id, name=dto.name, path=dto.path)
        for key, vm in arch.view_models.items():
            self._register("view_model", key, vm.id, name=vm.name, path=vm.path)
        for key, art in arch.artifacts.items():
            self._register("artifact", key, art.id, path=art.path)

    # -- lookups ----------------------------------------------------------

    @property
    def tests(self) -> dict[str, EntityRef]:
        """All test paths known to the provider, keyed by path."""
        return dict(self._tests)

    def by_ref(self, ref: str) -> EntityRef | None:
        return self._by_ref.get(ref)

    def resolve_node(self, node_id: str) -> EntityRef | None:
        """Map a graph node id to its canonical entity, or ``None``."""
        return self._by_node_id.get(node_id)

    def entities_for_path(self, path: str) -> list[EntityRef]:
        """All entities the provider associates with ``path``."""
        norm = (path or "").replace("\\", "/").strip()
        if not norm:
            return []
        return list(self._by_path.get(norm, []))

    def owning_engine(self, path: str) -> EntityRef | None:
        """Provider-resolved owning engine for ``path`` (never a heuristic)."""
        engine = self.arch.engine_for_path(path)
        if engine is None:
            return None
        return self._by_ref.get(f"engine:{engine.path}") or self._by_ref.get(
            f"engine:{engine.name}"
        )

    def classify_path(self, path: str) -> list[EntityRef]:
        """Resolve ``path`` to every canonical entity that claims it.

        Order is deterministic and specificity-ranked. If the provider
        records no direct entity, the owning engine is used, because engine
        ownership is itself provider evidence.
        """
        direct = self.entities_for_path(path)
        if direct:
            order = {kind: i for i, kind in enumerate(_PATH_KINDS)}
            return sorted(
                direct, key=lambda r: (order.get(r.kind, len(_PATH_KINDS)), r.ref)
            )
        test = self._tests.get(path.replace("\\", "/"))
        if test is not None:
            return [test]
        owner = self.owning_engine(path)
        return [owner] if owner is not None else []

    def graphs(self) -> dict[str, Any]:
        return {
            "ownership": self.arch.ownership,
            "execution": self.arch.execution,
            "dependency": self.arch.dependency,
        }

    def node_ids_for(self, ref: EntityRef) -> set[str]:
        """Every graph node id that resolves back to ``ref``."""
        return {
            node_id
            for node_id, target in self._by_node_id.items()
            if target.ref == ref.ref
        }


_RESOLVER: dict[int, EntityResolver] = {}


def get_resolver(architecture: Architecture | None = None) -> EntityResolver:
    """Cached resolver, one per Architecture instance."""
    arch = architecture or get_architecture()
    key = id(arch)
    resolver = _RESOLVER.get(key)
    if resolver is None:
        resolver = EntityResolver(arch)
        _RESOLVER.clear()
        _RESOLVER[key] = resolver
    return resolver


def reset_resolver() -> None:
    _RESOLVER.clear()
