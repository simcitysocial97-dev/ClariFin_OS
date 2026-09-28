"""Immutable models for the Engineering Knowledge Base (Program 11).

No execution logic. Data models only. All dataclasses are frozen with slots,
matching the conventions of the Engineering Runtime.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    """A single knowledge catalog entry.

    Stores only references to existing artifacts.
    No duplicated metadata.
    """

    id: str
    category: str
    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EndpointEntry:
    """Catalog entry for an API endpoint."""

    path: str
    method: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapabilityEntry:
    """Catalog entry for a frontend capability."""

    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MapperEntry:
    """Catalog entry for a data mapper."""

    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ViewModelEntry:
    """Catalog entry for a ViewModel."""

    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkspaceEntry:
    """Catalog entry for a workspace."""

    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComponentEntry:
    """Catalog entry for a UI component."""

    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GraphRendererEntry:
    """Catalog entry for a graph renderer."""

    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VerificationProfileEntry:
    """Catalog entry for a verification profile."""

    name: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IntegrityRuleEntry:
    """Catalog entry for an integrity rule."""

    rule_id: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimeArtifactEntry:
    """Catalog entry for a runtime artifact."""

    path: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DocumentationEntry:
    """Catalog entry for an engineering document."""

    title: str
    path: str
    references: dict[str, str]
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KnowledgeIndex:
    """Complete knowledge index.

    Immutable and deterministic for a given set of source artifacts.
    """

    endpoints: tuple[EndpointEntry, ...]
    capabilities: tuple[CapabilityEntry, ...]
    mappers: tuple[MapperEntry, ...]
    view_models: tuple[ViewModelEntry, ...]
    workspaces: tuple[WorkspaceEntry, ...]
    components: tuple[ComponentEntry, ...]
    graph_renderers: tuple[GraphRendererEntry, ...]
    verification_profiles: tuple[VerificationProfileEntry, ...]
    integrity_rules: tuple[IntegrityRuleEntry, ...]
    runtime_artifacts: tuple[RuntimeArtifactEntry, ...]
    documentation: tuple[DocumentationEntry, ...]
    indexed_at: str
    source_artifacts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QueryResult:
    """Result of a knowledge query."""

    entry: KnowledgeEntry
    ownership: dict[str, str]
    dependencies: tuple[str, ...]
    verification_profile: str | None
    integrity_rules: tuple[str, ...]
    documentation_references: tuple[str, ...]
    related_artifacts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RelationshipChain:
    """A resolved relationship chain from the reference engine."""

    source: str
    source_type: str
    target: str
    target_type: str
    relationship: str
    depth: int
