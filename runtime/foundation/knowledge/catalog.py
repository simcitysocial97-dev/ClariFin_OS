"""Knowledge Catalog — Program 11.

Immutable catalog entries for all engineering entity types.
Every catalog entry stores references only. No duplicated metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.foundation.knowledge.models import (
    ComponentEntry,
    DocumentationEntry,
    EndpointEntry,
    GraphRendererEntry,
    IntegrityRuleEntry,
    KnowledgeEntry,
    MapperEntry,
    RuntimeArtifactEntry,
    VerificationProfileEntry,
    ViewModelEntry,
    WorkspaceEntry,
)


class KnowledgeCatalog:
    """Immutable catalog of engineering knowledge entries.

    Consumes only existing runtime artifacts.
    Never generates new engineering facts.
    Never performs AI reasoning.
    Never duplicates runtime calculations.
    """

    def __init__(
        self,
        endpoints: tuple[EndpointEntry, ...] = (),
        capabilities: tuple[Any, ...] = (),
        mappers: tuple[MapperEntry, ...] = (),
        view_models: tuple[ViewModelEntry, ...] = (),
        workspaces: tuple[WorkspaceEntry, ...] = (),
        components: tuple[ComponentEntry, ...] = (),
        graph_renderers: tuple[GraphRendererEntry, ...] = (),
        verification_profiles: tuple[VerificationProfileEntry, ...] = (),
        integrity_rules: tuple[IntegrityRuleEntry, ...] = (),
        runtime_artifacts: tuple[RuntimeArtifactEntry, ...] = (),
        documentation: tuple[DocumentationEntry, ...] = (),
    ) -> None:
        self._endpoints = endpoints
        self._capabilities = capabilities
        self._mappers = mappers
        self._view_models = view_models
        self._workspaces = workspaces
        self._components = components
        self._graph_renderers = graph_renderers
        self._verification_profiles = verification_profiles
        self._integrity_rules = integrity_rules
        self._runtime_artifacts = runtime_artifacts
        self._documentation = documentation

    @property
    def endpoints(self) -> tuple[EndpointEntry, ...]:
        return self._endpoints

    @property
    def capabilities(self) -> tuple[Any, ...]:
        return self._capabilities

    @property
    def mappers(self) -> tuple[MapperEntry, ...]:
        return self._mappers

    @property
    def view_models(self) -> tuple[ViewModelEntry, ...]:
        return self._view_models

    @property
    def workspaces(self) -> tuple[WorkspaceEntry, ...]:
        return self._workspaces

    @property
    def components(self) -> tuple[ComponentEntry, ...]:
        return self._components

    @property
    def graph_renderers(self) -> tuple[GraphRendererEntry, ...]:
        return self._graph_renderers

    @property
    def verification_profiles(self) -> tuple[VerificationProfileEntry, ...]:
        return self._verification_profiles

    @property
    def integrity_rules(self) -> tuple[IntegrityRuleEntry, ...]:
        return self._integrity_rules

    @property
    def runtime_artifacts(self) -> tuple[RuntimeArtifactEntry, ...]:
        return self._runtime_artifacts

    @property
    def documentation(self) -> tuple[DocumentationEntry, ...]:
        return self._documentation

    def endpoint_by_path(self, path: str) -> EndpointEntry | None:
        for ep in self._endpoints:
            if ep.path == path:
                return ep
        return None

    def capability_by_name(self, name: str) -> Any | None:
        for cap in self._capabilities:
            if getattr(cap, "name", None) == name:
                return cap
        return None

    def workspace_by_name(self, name: str) -> WorkspaceEntry | None:
        for ws in self._workspaces:
            if ws.name == name:
                return ws
        return None

    def rule_by_id(self, rule_id: str) -> IntegrityRuleEntry | None:
        for rule in self._integrity_rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def component_by_name(self, name: str) -> ComponentEntry | None:
        for comp in self._components:
            if comp.name == name:
                return comp
        return None

    def to_index(self) -> dict[str, Any]:
        return {
            "endpoints": [
                {
                    "path": ep.path,
                    "method": ep.method,
                    "references": ep.references,
                    "tags": list(ep.tags),
                }
                for ep in self._endpoints
            ],
            "capabilities": [
                {
                    "name": getattr(cap, "name", str(cap)),
                    "references": getattr(cap, "references", {}),
                    "tags": list(getattr(cap, "tags", ())),
                }
                for cap in self._capabilities
            ],
            "mappers": [
                {
                    "name": mp.name,
                    "references": mp.references,
                    "tags": list(mp.tags),
                }
                for mp in self._mappers
            ],
            "view_models": [
                {
                    "name": vm.name,
                    "references": vm.references,
                    "tags": list(vm.tags),
                }
                for vm in self._view_models
            ],
            "workspaces": [
                {
                    "name": ws.name,
                    "references": ws.references,
                    "tags": list(ws.tags),
                }
                for ws in self._workspaces
            ],
            "components": [
                {
                    "name": comp.name,
                    "references": comp.references,
                    "tags": list(comp.tags),
                }
                for comp in self._components
            ],
            "graph_renderers": [
                {
                    "name": gr.name,
                    "references": gr.references,
                    "tags": list(gr.tags),
                }
                for gr in self._graph_renderers
            ],
            "verification_profiles": [
                {
                    "name": vp.name,
                    "references": vp.references,
                    "tags": list(vp.tags),
                }
                for vp in self._verification_profiles
            ],
            "integrity_rules": [
                {
                    "rule_id": rule.rule_id,
                    "references": rule.references,
                    "tags": list(rule.tags),
                }
                for rule in self._integrity_rules
            ],
            "runtime_artifacts": [
                {
                    "path": ra.path,
                    "references": ra.references,
                    "tags": list(ra.tags),
                }
                for ra in self._runtime_artifacts
            ],
            "documentation": [
                {
                    "title": doc.title,
                    "path": doc.path,
                    "references": doc.references,
                    "tags": list(doc.tags),
                }
                for doc in self._documentation
            ],
        }


_catalog_instance: KnowledgeCatalog | None = None


def get_catalog() -> KnowledgeCatalog:
    """Return the singleton knowledge catalog instance."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = KnowledgeCatalog()
    return _catalog_instance


def set_catalog(catalog: KnowledgeCatalog) -> None:
    """Set the singleton knowledge catalog instance."""
    global _catalog_instance
    _catalog_instance = catalog