"""Repository Intelligence Runtime for ClariFin_OS.

A deterministic, repository-wide intelligence layer that discovers structure,
cross-references canonical metadata sources, and exposes a query API for
answering questions about capabilities, modules, APIs, components, tests,
documentation, dependencies, and change impact.

This package is analysis infrastructure only — no AI planning, orchestration,
workflow generation, or autonomous execution.
"""

from repo_intelligence.schema import (
    GraphNode,
    GraphEdge,
    RepositoryGraph,
    NODE_TYPES,
    RELATIONSHIP_TYPES,
    OWNERSHIP_CLASSES,
    METADATA_CLASSIFICATION,
)
from repo_intelligence.builder import RepositoryBuilder, ValidationSummary
from repo_intelligence.graph_service import (
    RepositoryGraphService,
    build_graph_service,
    load_graph_service,
)
from repo_intelligence.index import RepositoryIndexer  # for backward compatibility
from repo_intelligence.query import RepositoryIndex

__all__ = [
    "GraphNode",
    "GraphEdge",
    "RepositoryGraph",
    "NODE_TYPES",
    "RELATIONSHIP_TYPES",
    "OWNERSHIP_CLASSES",
    "METADATA_CLASSIFICATION",
    "RepositoryBuilder",
    "ValidationSummary",
    "RepositoryGraphService",
    "build_graph_service",
    "load_graph_service",
    "RepositoryIndexer",
    "RepositoryIndex",
]

__version__ = "1.0.0"
