"""Reference Engine — Program 11.

Resolves relationships between engineering entities.
Read-only. Never modifies artifacts.

Relationship chain:
Endpoint -> Capability -> Mapper -> ViewModel -> Workspace -> Components -> Tests
-> Verification Profile -> Integrity Rules -> Documentation
"""

from __future__ import annotations

from typing import Any

from runtime.foundation.knowledge.catalog import get_catalog
from runtime.foundation.knowledge.models import (
    EndpointEntry,
    KnowledgeEntry,
    RelationshipChain,
)


class ReferenceEngine:
    """Resolves relationships between engineering entities.

    Read-only. Consumes only the knowledge catalog.
    Never modifies artifacts.
    """

    def __init__(self, catalog: Any | None = None) -> None:
        self._catalog = catalog or get_catalog()

    def resolve_endpoint(self, path: str) -> list[RelationshipChain]:
        """Resolve all relationships for an endpoint."""
        chains: list[RelationshipChain] = []
        entry = self._catalog.endpoint_by_path(path)
        if entry is None:
            return chains
        ke = self._entry_to_knowledge_entry(entry, "endpoint")
        chains.extend(self._follow_capabilities(ke))
        return chains

    def resolve_capability(self, name: str) -> list[RelationshipChain]:
        """Resolve all relationships for a capability."""
        chains: list[RelationshipChain] = []
        entry = self._catalog.capability_by_name(name)
        if entry is None:
            return chains
        ke = self._entry_to_knowledge_entry(entry, "capability")
        chains.extend(self._follow_mappers(ke))
        return chains

    def resolve_mapper(self, name: str) -> list[RelationshipChain]:
        """Resolve all relationships for a mapper."""
        chains: list[RelationshipChain] = []
        for mp in self._catalog.mappers:
            if mp.name == name:
                ke = self._entry_to_knowledge_entry(mp, "mapper")
                chains.extend(self._follow_view_models(ke))
                break
        return chains

    def resolve_viewmodel(self, name: str) -> list[RelationshipChain]:
        """Resolve all relationships for a ViewModel."""
        chains: list[RelationshipChain] = []
        for vm in self._catalog.view_models:
            if vm.name == name:
                ke = self._entry_to_knowledge_entry(vm, "viewModel")
                chains.extend(self._follow_workspaces(ke))
                break
        return chains

    def resolve_workspace(self, name: str) -> list[RelationshipChain]:
        """Resolve all relationships for a workspace."""
        chains: list[RelationshipChain] = []
        entry = self._catalog.workspace_by_name(name)
        if entry is None:
            return chains
        ke = self._entry_to_knowledge_entry(entry, "workspace")
        chains.extend(self._follow_components(ke))
        return chains

    def resolve_component(self, name: str) -> list[RelationshipChain]:
        """Resolve all relationships for a component."""
        chains: list[RelationshipChain] = []
        entry = self._catalog.component_by_name(name)
        if entry is None:
            return chains
        ke = self._entry_to_knowledge_entry(entry, "component")
        chains.extend(self._follow_tests(ke))
        return chains

    def resolve_test(self, test_path: str) -> list[RelationshipChain]:
        """Resolve all relationships for a test."""
        chains: list[RelationshipChain] = []
        for ra in self._catalog.runtime_artifacts:
            if ra.path == test_path or test_path in str(ra.references):
                chains.append(
                    RelationshipChain(
                        source=test_path,
                        source_type="test",
                        target=ra.path,
                        target_type="runtimeArtifact",
                        relationship="references",
                        depth=1,
                    )
                )
        return chains

    def resolve_verification_profile(self, name: str) -> list[RelationshipChain]:
        """Resolve all relationships for a verification profile."""
        chains: list[RelationshipChain] = []
        for vp in self._catalog.verification_profiles:
            if vp.name == name:
                ke = self._entry_to_knowledge_entry(vp, "verificationProfile")
                chains.append(
                    RelationshipChain(
                        source=name,
                        source_type="verificationProfile",
                        target="verification",
                        target_type="process",
                        relationship="governs",
                        depth=1,
                    )
                )
                break
        return chains

    def resolve_integrity_rule(self, rule_id: str) -> list[RelationshipChain]:
        """Resolve all relationships for an integrity rule."""
        chains: list[RelationshipChain] = []
        entry = self._catalog.rule_by_id(rule_id)
        if entry is None:
            return chains
        ke = self._entry_to_knowledge_entry(entry, "integrityRule")
        chains.append(
            RelationshipChain(
                source=rule_id,
                source_type="integrityRule",
                target="architecture",
                target_type="domain",
                relationship="validates",
                depth=1,
            )
        )
        return chains

    def resolve_documentation(self, path: str) -> list[RelationshipChain]:
        """Resolve all relationships for a documentation file."""
        chains: list[RelationshipChain] = []
        for doc in self._catalog.documentation:
            if doc.path == path:
                chains.append(
                    RelationshipChain(
                        source=path,
                        source_type="documentation",
                        target="knowledgeBase",
                        target_type="index",
                        relationship="indexedBy",
                        depth=1,
                    )
                )
                break
        return chains

    def _entry_to_knowledge_entry(self, entry: Any, category: str) -> KnowledgeEntry:
        """Convert a specific entry type to a KnowledgeEntry."""
        if isinstance(entry, EndpointEntry):
            return KnowledgeEntry(
                id=entry.path,
                category=category,
                name=entry.path,
                references=entry.references,
                tags=entry.tags,
            )
        elif hasattr(entry, "name"):
            return KnowledgeEntry(
                id=entry.name,
                category=category,
                name=entry.name,
                references=entry.references,
                tags=entry.tags,
            )
        elif hasattr(entry, "rule_id"):
            return KnowledgeEntry(
                id=entry.rule_id,
                category=category,
                name=entry.rule_id,
                references=entry.references,
                tags=entry.tags,
            )
        else:
            return KnowledgeEntry(
                id=str(entry),
                category=category,
                name=str(entry),
                references=entry.references if hasattr(entry, "references") else {},
                tags=entry.tags if hasattr(entry, "tags") else (),
            )

    def _follow_capabilities(
        self, entry: KnowledgeEntry,
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for key, value in entry.references.items():
            if key.startswith("capability:"):
                cap_name = key.replace("capability:", "")
                chains.append(
                    RelationshipChain(
                        source=entry.id,
                        source_type=entry.category,
                        target=cap_name,
                        target_type="capability",
                        relationship="exposes",
                        depth=1,
                    )
                )
                chains.extend(self._follow_mappers_from_capability(cap_name, depth=2))
        return chains

    def _follow_mappers_from_capability(
        self, cap_name: str, depth: int
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for mp in self._catalog.mappers:
            if cap_name in str(mp.references):
                chains.append(
                    RelationshipChain(
                        source=cap_name,
                        source_type="capability",
                        target=mp.name,
                        target_type="mapper",
                        relationship="uses",
                        depth=depth,
                    )
                )
                chains.extend(self._follow_view_models_from_mapper(mp.name, depth=depth + 1))
        return chains

    def _follow_mappers(
        self, entry: KnowledgeEntry,
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for key, value in entry.references.items():
            if key.startswith("mapper:"):
                mapper_name = key.replace("mapper:", "")
                chains.append(
                    RelationshipChain(
                        source=entry.id,
                        source_type=entry.category,
                        target=mapper_name,
                        target_type="mapper",
                        relationship="transforms",
                        depth=1,
                    )
                )
                chains.extend(self._follow_view_models_from_mapper(mapper_name, depth=2))
        return chains

    def _follow_view_models_from_mapper(
        self, mapper_name: str, depth: int
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for vm in self._catalog.view_models:
            if mapper_name in str(vm.references):
                chains.append(
                    RelationshipChain(
                        source=mapper_name,
                        source_type="mapper",
                        target=vm.name,
                        target_type="viewModel",
                        relationship="feeds",
                        depth=depth,
                    )
                )
                chains.extend(self._follow_workspaces_from_viewmodel(vm.name, depth=depth + 1))
        return chains

    def _follow_view_models(
        self, entry: KnowledgeEntry,
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for key, value in entry.references.items():
            if key.startswith("viewModel:"):
                vm_name = key.replace("viewModel:", "")
                chains.append(
                    RelationshipChain(
                        source=entry.id,
                        source_type=entry.category,
                        target=vm_name,
                        target_type="viewModel",
                        relationship="renders",
                        depth=1,
                    )
                )
                chains.extend(self._follow_workspaces_from_viewmodel(vm_name, depth=2))
        return chains

    def _follow_workspaces_from_viewmodel(
        self, viewmodel_name: str, depth: int
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for ws in self._catalog.workspaces:
            if viewmodel_name in str(ws.references):
                chains.append(
                    RelationshipChain(
                        source=viewmodel_name,
                        source_type="viewModel",
                        target=ws.name,
                        target_type="workspace",
                        relationship="belongsTo",
                        depth=depth,
                    )
                )
                chains.extend(self._follow_components_from_workspace(ws.name, depth=depth + 1))
        return chains

    def _follow_workspaces(
        self, entry: KnowledgeEntry,
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for key, value in entry.references.items():
            if key.startswith("workspace:"):
                ws_name = key.replace("workspace:", "")
                chains.append(
                    RelationshipChain(
                        source=entry.id,
                        source_type=entry.category,
                        target=ws_name,
                        target_type="workspace",
                        relationship="hosts",
                        depth=1,
                    )
                )
                chains.extend(self._follow_components_from_workspace(ws_name, depth=2))
        return chains

    def _follow_components_from_workspace(
        self, workspace_name: str, depth: int
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for comp in self._catalog.components:
            if workspace_name in str(comp.references):
                chains.append(
                    RelationshipChain(
                        source=workspace_name,
                        source_type="workspace",
                        target=comp.name,
                        target_type="component",
                        relationship="contains",
                        depth=depth,
                    )
                )
                chains.extend(self._follow_tests_from_component(comp.name, depth=depth + 1))
        return chains

    def _follow_components(
        self, entry: KnowledgeEntry,
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for key, value in entry.references.items():
            if key.startswith("component:"):
                comp_name = key.replace("component:", "")
                chains.append(
                    RelationshipChain(
                        source=entry.id,
                        source_type=entry.category,
                        target=comp_name,
                        target_type="component",
                        relationship="uses",
                        depth=1,
                    )
                )
                chains.extend(self._follow_tests_from_component(comp_name, depth=2))
        return chains

    def _follow_tests(
        self, entry: KnowledgeEntry,
    ) -> list[RelationshipChain]:
        """Follow tests from a component or other entity."""
        chains: list[RelationshipChain] = []
        for ra in self._catalog.runtime_artifacts:
            if "test" in ra.tags and entry.name in str(ra.references):
                chains.append(
                    RelationshipChain(
                        source=entry.id,
                        source_type=entry.category,
                        target=ra.path,
                        target_type="runtimeArtifact",
                        relationship="testedBy",
                        depth=1,
                    )
                )
        return chains

    def _follow_tests_from_component(
        self, component_name: str, depth: int
    ) -> list[RelationshipChain]:
        chains: list[RelationshipChain] = []
        for ra in self._catalog.runtime_artifacts:
            if "test" in ra.tags and component_name in str(ra.references):
                chains.append(
                    RelationshipChain(
                        source=component_name,
                        source_type="component",
                        target=ra.path,
                        target_type="runtimeArtifact",
                        relationship="testedBy",
                        depth=depth,
                    )
                )
        return chains


def resolve_endpoint(path: str) -> list[RelationshipChain]:
    """Resolve all relationships for an endpoint."""
    return ReferenceEngine().resolve_endpoint(path)


def resolve_capability(name: str) -> list[RelationshipChain]:
    """Resolve all relationships for a capability."""
    return ReferenceEngine().resolve_capability(name)


def resolve_mapper(name: str) -> list[RelationshipChain]:
    """Resolve all relationships for a mapper."""
    return ReferenceEngine().resolve_mapper(name)


def resolve_viewmodel(name: str) -> list[RelationshipChain]:
    """Resolve all relationships for a ViewModel."""
    return ReferenceEngine().resolve_viewmodel(name)


def resolve_workspace(name: str) -> list[RelationshipChain]:
    """Resolve all relationships for a workspace."""
    return ReferenceEngine().resolve_workspace(name)


def resolve_component(name: str) -> list[RelationshipChain]:
    """Resolve all relationships for a component."""
    return ReferenceEngine().resolve_component(name)


def resolve_test(test_path: str) -> list[RelationshipChain]:
    """Resolve all relationships for a test."""
    return ReferenceEngine().resolve_test(test_path)


def resolve_verification_profile(name: str) -> list[RelationshipChain]:
    """Resolve all relationships for a verification profile."""
    return ReferenceEngine().resolve_verification_profile(name)


def resolve_integrity_rule(rule_id: str) -> list[RelationshipChain]:
    """Resolve all relationships for an integrity rule."""
    return ReferenceEngine().resolve_integrity_rule(rule_id)


def resolve_documentation(path: str) -> list[RelationshipChain]:
    """Resolve all relationships for a documentation file."""
    return ReferenceEngine().resolve_documentation(path)