"""Repository Graph Schema — Phase 2.

Canonical data structures for the repository intelligence graph.

Nodes represent repository artifacts (capabilities, modules, APIs, components,
etc.). Edges represent relationships between them (implements, imports,
depends_on, tests, documents, calls, owns, generates, consumes, belongs_to).

The graph is designed as pure data structures — no persistence, no
visualization, no AI logic. Scanners populate the graph; the query layer
reads it.

--- Semantic Ownership Model (Phase 2.1) ---

Every node has an ``ownership`` property that classifies who or what
is responsible for the node. The ownership model replaces the previous
"orphan module" concept with a richer classification:

- ``capability`` — nodes owned by a capability
- ``shared_infrastructure`` — shared helpers, utilities, cross-cutting modules
- ``generated`` — auto-generated artifacts
- ``framework`` — framework glue, configuration, bootstrap code
- ``utility`` — general-purpose utility modules
- ``external`` — third-party or external dependencies
- ``unknown`` — ownership not yet determined (the only condition reported as suspicious)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ===========================================================================
# Node Type Constants
# ===========================================================================

NODE_TYPES: frozenset[str] = frozenset(
    {
        "capability",
        "module",
        "package",
        "api",
        "endpoint",
        "frontend_route",
        "component",
        "hook",
        "database_table",
        "migration",
        "test_suite",
        "documentation",
        "workflow",
        "script",
        "generated_artifact",
        "package_json",
        "requirements",
        # Placeholder node types for future runtimes (Phase 3)
        "financial_object",
        "runtime",
        "workspace",
        "timeline",
        "context",
        "command",
        "evidence",
        "investigation",
        "decision",
        "simulation",
        "recommendation",
    }
)

# ===========================================================================
# Relationship Type Constants
# ===========================================================================

RELATIONSHIP_TYPES: frozenset[str] = frozenset(
    {
        "implements",
        "imports",
        "depends_on",
        "tests",
        "documents",
        "calls",
        "owns",
        "generates",
        "consumes",
        "belongs_to",
        "contains",
        "extends",
        "invokes",
        "verifies",
    }
)

# ===========================================================================
# Semantic Ownership Model (Phase 2.1)
# ===========================================================================

OWNERSHIP_CLASSES: frozenset[str] = frozenset(
    {
        "capability",
        "shared_infrastructure",
        "generated",
        "framework",
        "utility",
        "external",
        "unknown",
    }
)

# Canonical metadata source classifications (Phase 2.1)
# Each domain maps to its canonical source, projection, derived data, cache, or duplicate.
METADATA_CLASSIFICATION: dict[str, dict[str, str]] = {
    "capabilities": {
        "canonical_source": "backend/tests/generated/capability-registry.yaml",
        "generated_projection": "repo_intelligence/index.json (capability nodes)",
        "derived_data": "capability dependency edges, capability table ownership",
        "temporary_cache": "none",
        "duplicate": "none",
    },
    "api_endpoints": {
        "canonical_source": "backend/tests/generated/api-map.json",
        "generated_projection": "repo_intelligence/index.json (endpoint nodes, implements edges)",
        "derived_data": "endpoint-to-capability mapping, router-to-endpoint edges",
        "temporary_cache": "none",
        "duplicate": "frontend/api-schema.json (OpenAPI spec, same endpoints)",
    },
    "api_contracts": {
        "canonical_source": "backend/tests/generated/contract-registry.json",
        "generated_projection": "repo_intelligence/index.json (endpoint nodes with contract info)",
        "derived_data": "request/response schema enrichment on endpoint nodes",
        "temporary_cache": "none",
        "duplicate": "none",
    },
    "dependencies": {
        "canonical_source": "backend/tests/generated/dependency-map.json",
        "generated_projection": "repo_intelligence/index.json (depends_on, imports edges)",
        "derived_data": "cross-module dependency graph, capability dependency edges",
        "temporary_cache": "none",
        "duplicate": "backend/requirements.txt, frontend/package.json (package-level deps)",
    },
    "openapi_spec": {
        "canonical_source": "frontend/api-schema.json",
        "generated_projection": "repo_intelligence/index.json (api node, endpoint nodes)",
        "derived_data": "endpoint nodes from OpenAPI paths",
        "temporary_cache": "none",
        "duplicate": "backend/tests/generated/api-map.json (same endpoints, different source)",
    },
    "test_structure": {
        "canonical_source": "backend/tests/ directory layout",
        "generated_projection": "repo_intelligence/index.json (test_suite nodes, test modules)",
        "derived_data": "capability-to-test mappings, verification edges",
        "temporary_cache": "none",
        "duplicate": "none",
    },
    "documentation": {
        "canonical_source": "docs/ directory, memory-bank/, root .md files",
        "generated_projection": "repo_intelligence/index.json (documentation nodes, documents edges)",
        "derived_data": "keyword-based capability-to-documentation links",
        "temporary_cache": "none",
        "duplicate": "none",
    },
    "workflows": {
        "canonical_source": ".github/workflows/ directory",
        "generated_projection": "repo_intelligence/index.json (workflow nodes)",
        "derived_data": "workflow-to-script edges, trigger analysis",
        "temporary_cache": "none",
        "duplicate": "none",
    },
    "migrations": {
        "canonical_source": "backend/scripts/migration_*.py files",
        "generated_projection": "repo_intelligence/index.json (migration nodes, database_table nodes)",
        "derived_data": "table creation/alteration edges from migration content",
        "temporary_cache": "none",
        "duplicate": "none",
    },
    "frontend_api_client": {
        "canonical_source": "frontend/lib/api/client.ts",
        "generated_projection": "repo_intelligence/index.json (module nodes, consumes edges)",
        "derived_data": "endpoint consumption mapping from fetch calls",
        "temporary_cache": "none",
        "duplicate": "none",
    },
    "scripts": {
        "canonical_source": "scripts/, backend/scripts/, frontend/scripts/ directories",
        "generated_projection": "repo_intelligence/index.json (script nodes)",
        "derived_data": "script-type classification from file extensions",
        "temporary_cache": "none",
        "duplicate": "none",
    },
}

# ===========================================================================
# Node and Edge Data Structures
# ===========================================================================


@dataclass
class GraphNode:
    """A single node in the repository graph.

    Every node has a globally unique ``id`` of the form ``<type>:<path>``
    so that nodes from different scanners never collide.

    The ``ownership`` property classifies who or what is responsible for
    the node. See :data:`OWNERSHIP_CLASSES` for valid values.
    """

    id: str
    type: str
    name: str
    path: str
    source: str
    ownership: str = "unknown"
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "source": self.source,
            "ownership": self.ownership,
            "properties": self.properties,
        }


@dataclass
class GraphEdge:
    """A directed relationship between two nodes.

    ``source`` and ``target`` are node IDs. ``relationship`` is one of
    ``RELATIONSHIP_TYPES``. ``confidence`` is 0.0–1.0. ``evidence`` is a
    short string describing why the edge was created.
    """

    source: str
    target: str
    relationship: str
    confidence: float = 1.0
    evidence: str = ""
    ownership: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "ownership": self.ownership,
        }


@dataclass
class RepositoryGraph:
    """The complete repository graph: nodes + edges + metadata.

    ``generated_at`` is a content hash (not a timestamp) to keep the
    index deterministic.
    """

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    schema_version: str = "2.1"
    generated_at: str = ""
    repository_root: str = ""

    # -- construction helpers ------------------------------------------------

    def add_node(self, node: GraphNode) -> None:
        """Add a node if its ID is not already present."""
        if not any(n.id == node.id for n in self.nodes):
            self.nodes.append(node)

    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge (duplicates are allowed but de-duplicated on export)."""
        self.edges.append(edge)

    # -- query helpers -------------------------------------------------------

    def get_node(self, node_id: str) -> GraphNode | None:
        """Retrieve a node by ID."""
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def get_nodes_by_type(self, node_type: str) -> list[GraphNode]:
        """Retrieve all nodes of a given type."""
        return [n for n in self.nodes if n.type == node_type]

    def get_edges(
        self,
        source: str | None = None,
        target: str | None = None,
        relationship: str | None = None,
    ) -> list[GraphEdge]:
        """Retrieve edges matching the given criteria."""
        results = self.edges
        if source is not None:
            results = [e for e in results if e.source == source]
        if target is not None:
            results = [e for e in results if e.target == target]
        if relationship is not None:
            results = [e for e in results if e.relationship == relationship]
        return results

    def get_outgoing_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all edges where ``node_id`` is the source."""
        return [e for e in self.edges if e.source == node_id]

    def get_incoming_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all edges where ``node_id`` is the target."""
        return [e for e in self.edges if e.target == node_id]

    # -- serialization -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict with de-duplicated edges."""
        seen_edges: set[tuple[str, str, str]] = set()
        unique_edges: list[GraphEdge] = []
        for e in self.edges:
            key = (e.source, e.target, e.relationship)
            if key not in seen_edges:
                seen_edges.add(key)
                unique_edges.append(e)

        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "repository_root": self.repository_root,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in unique_edges],
        }

    def compute_hash(self) -> str:
        """Compute a deterministic content hash of the graph."""
        import hashlib
        import json

        data = self.to_dict()
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
