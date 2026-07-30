"""Repository Builder — Phase 3.

Separates index construction from query/runtime logic. The builder is
responsible ONLY for:
- Running scanners
- Merging results
- Assigning ownership
- Detecting gaps
- Validating
- Generating the graph
- Writing the index

The builder does NOT perform any traversal, impact analysis, or metrics
computation. Those belong in separate consumers that use the
RepositoryGraphService interface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from repo_intelligence.schema import GraphNode, RepositoryGraph, OWNERSHIP_CLASSES
from repo_intelligence.scanner import (
    BackendScanner,
    DocsScanner,
    FrontendScanner,
    ApiScanner,
    TestScanner,
    WorkflowScanner,
    ScriptScanner,
    MigrationScanner,
    MetadataScanner,
)


class ValidationSummary:
    """Holds validation results after building the graph."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.node_count: int = 0
        self.edge_count: int = 0
        self.unknown_ownership_count: int = 0
        self.orphan_module_count: int = 0
        self.untested_endpoint_count: int = 0
        self.undocumented_cap_count: int = 0

    def is_valid(self) -> bool:
        return len(self.errors) == 0


class RepositoryBuilder:
    """Builds a canonical repository index from all scanner outputs.

    This class orchestrates the entire pipeline: scan → merge → classify
    → validate → hash → write. It produces a RepositoryGraph object and can
    serialize it to index.json with versioned metadata.
    """

    def __init__(self, repo_root: Path | None = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent
        else:
            repo_root = Path(repo_root)
        self.repo_root = repo_root
        self.graph = RepositoryGraph(repository_root=str(repo_root))
        self.gaps: Dict[str, Any] = {}

    def build(self) -> RepositoryGraph:
        """Run all scanners and merge results into a single graph.

        Returns:
            The fully populated and validated RepositoryGraph.
        """
        # Run all scanners in order
        scanners: list = [
            MetadataScanner(self.repo_root),
            BackendScanner(self.repo_root),
            FrontendScanner(self.repo_root),
            ApiScanner(self.repo_root),
            TestScanner(self.repo_root),
            DocsScanner(self.repo_root),
            WorkflowScanner(self.repo_root),
            ScriptScanner(self.repo_root),
            MigrationScanner(self.repo_root),
        ]

        for scanner in scanners:
            scan_result = scanner.scan()
            for node in scan_result.nodes:
                self.graph.add_node(node)
            for edge in scan_result.edges:
                self.graph.add_edge(edge)

        # Assign ownership to all nodes (Phase 2.1)
        self._assign_ownership()

        # Detect gaps before computing hash
        self.gaps = self._detect_gaps()

        # Compute deterministic content hash
        self.graph.generated_at = self.graph.compute_hash()

        return self.graph

    def _assign_ownership(self) -> None:
        """Classify ownership for all nodes in the graph using heuristics."""
        for node in self.graph.nodes:
            node.ownership = self._classify_ownership(node)

    def _classify_ownership(self, node: GraphNode) -> str:
        """Classify a single node into an ownership category."""
        node_type = node.type
        path = node.path
        properties = node.properties

        # Generated artifacts are owned by the generation process
        if node_type == "generated_artifact":
            return "generated"

        # Framework and configuration files
        if node_type == "package_json":
            return "framework"
        if node_type == "requirements":
            return "framework"
        if node_type == "workflow":
            return "framework"

        # Scripts are utility/infrastructure
        if node_type == "script":
            return "utility"

        # Migrations are framework-level infrastructure
        if node_type == "migration":
            return "framework"

        # Database tables are owned by capabilities
        if node_type == "database_table":
            return "capability"

        # Test suites are owned by capabilities
        if node_type == "test_suite":
            return "capability"

        # Documentation is owned by capabilities or shared if cross-cutting
        if node_type == "documentation":
            return "capability"

        # API nodes are generated projections
        if node_type == "api":
            return "generated"

        # Endpoints are owned by capabilities
        if node_type == "endpoint":
            cap = properties.get("capability", "")
            if cap and cap != "unknown":
                return "capability"
            return "unknown"

        # Modules: classify based on path and module_type
        if node_type == "module":
            module_type = properties.get("module_type", "")
            if module_type == "test":
                return "capability"
            if module_type in ("frontend", "api_client_function"):
                return "capability"
            if module_type in ("router", "service", "engine", "repository", "model"):
                return "capability"
            if module_type in ("common", "utils", "shared"):
                return "shared_infrastructure"
            if module_type in ("verification", "orchestration", "audits"):
                return "shared_infrastructure"
            if module_type == "extraction" or module_type == "report":
                return "utility"
            # Check generic patterns
            if any(seg in path for seg in ("/common/", "/utils/", "/shared/")):
                return "shared_infrastructure"
            return "unknown"

        # Packages: classify based on path under src/
        if node_type == "package":
            if "/common/" in path or "/utils/" in path or "/shared/" in path:
                return "shared_infrastructure"
            if any(seg in path for seg in ("/routers/", "/services/", "/engines/", "/repositories/", "/models/")):
                return "capability"
            if "/verification/" in path or "/orchestration/" in path:
                return "shared_infrastructure"
            return "unknown"

        # Components, hooks, frontend routes are owned by capabilities (frontend)
        if node_type in ("component", "hook", "frontend_route"):
            return "capability"

        # Everything else defaults to unknown
        return "unknown"

    def _detect_gaps(self) -> Dict[str, Any]:
        """Detect missing relationships and unknown files."""
        # Build sets for quick lookup
        all_node_ids: set[str] = {n.id for n in self.graph.nodes}
        capability_ids: set[str] = {
            n.properties.get("id", "")
            for n in self.graph.nodes
            if n.type == "capability"
        }
        capability_ids.discard("")

        # Find modules referenced by capabilities but not on disk
        missing_modules: list[str] = []
        for edge in self.graph.edges:
            if (
                edge.relationship == "implements"
                and edge.source.startswith("capability:")
            ):
                target_id = edge.target
                if target_id not in all_node_ids:
                    missing_modules.append(
                        f"{edge.source} -> {target_id}"
                    )

        # Find orphan modules (not referenced by any capability via implements)
        implemented_modules: set[str] = set()
        for edge in self.graph.edges:
            if (
                edge.relationship == "implements"
                and edge.source.startswith("capability:")
            ):
                implemented_modules.add(edge.target)

        orphan_modules: list[dict[str, str]] = []
        for node in self.graph.nodes:
            if node.type == "module" and node.id not in implemented_modules:
                # Skip test modules and frontend-only modules
                if node.properties.get("module_type") in (
                    "test",
                    "frontend",
                    "api_client_function",
                ):
                    continue
                orphan_modules.append(
                    {"id": node.id, "path": node.path, "name": node.name}
                )

        # Find endpoints with no verification evidence
        verified_endpoints: set[str] = set()
        for edge in self.graph.edges:
            if edge.relationship == "verifies" and edge.source.startswith("capability:"):
                verified_endpoints.add(edge.target)

        no_verification_evidence: list[dict[str, Any]] = []
        for node in self.graph.nodes:
            if node.type == "endpoint" and node.id not in verified_endpoints:
                no_verification_evidence.append(
                    {
                        "id": node.id,
                        "path": node.path,
                        "name": node.name,
                        "method": node.properties.get("method", ""),
                        "endpoint_path": node.properties.get("path", ""),
                        "capability": node.properties.get("capability", "unknown"),
                        "ownership": node.ownership,
                    }
                )

        # Find capabilities with no documentation evidence
        documented_cap_ids: set[str] = set()
        for edge in self.graph.edges:
            if edge.relationship == "documents":
                documented_cap_ids.add(edge.source)

        no_documentation_evidence: list[dict[str, Any]] = []
        for cap_id in sorted(capability_ids):
            if cap_id:
                cap_node_id = f"capability:{cap_id}"
                if cap_node_id not in documented_cap_ids:
                    no_documentation_evidence.append(
                        {"capability_id": cap_id, "ownership": "capability"}
                    )

        # Find modules with unknown ownership
        unknown_ownership_modules: list[dict[str, Any]] = []
        for node in self.graph.nodes:
            if node.type == "module" and node.ownership == "unknown":
                unknown_ownership_modules.append(
                    {
                        "id": node.id,
                        "path": node.path,
                        "name": node.name,
                        "module_type": node.properties.get("module_type", "unknown"),
                    }
                )

        # Find capability dependencies that don't resolve
        missing_dependencies: list[str] = []
        for edge in self.graph.edges:
            if (
                edge.relationship == "depends_on"
                and edge.source.startswith("capability:")
                and edge.target.startswith("capability:")
            ):
                if edge.target not in all_node_ids:
                    missing_dependencies.append(
                        f"{edge.source} depends_on {edge.target}"
                    )

        return {
            "missing_modules": sorted(set(missing_modules)),
            "orphan_modules": sorted(orphan_modules, key=lambda x: x["path"]),
            "no_verification_evidence": sorted(no_verification_evidence, key=lambda x: x["name"]),
            "no_documentation_evidence": no_documentation_evidence,
            "unknown_ownership_modules": sorted(unknown_ownership_modules, key=lambda x: x["path"]),
            "missing_dependencies": sorted(set(missing_dependencies)),
        }

    def validate(self) -> ValidationSummary:
        """Validate the built graph structure.

        Returns:
            A ValidationSummary object with errors, warnings, and counts.
        """
        summary = ValidationSummary()

        if self.graph is None:
            summary.errors.append("No graph to validate")
            return summary

        # Count unknown ownership nodes
        summary.unknown_ownership_count = sum(
            1 for n in self.graph.nodes if n.ownership == "unknown"
        )

        # Orphan count from gaps
        summary.orphan_module_count = len(self.gaps.get("orphan_modules", []))

        # Untested endpoint count
        summary.untested_endpoint_count = len(self.gaps.get("no_verification_evidence", []))

        # Undocumented capability count
        summary.undocumented_cap_count = len(self.gaps.get("no_documentation_evidence", []))

        # Structural checks
        node_ids: set[str] = set()
        for n in self.graph.nodes:
            if n.id in node_ids:
                summary.errors.append(f"Duplicate node ID: {n.id}")
            node_ids.add(n.id)

        seen_edges: set[tuple[str, str, str]] = set()
        for e in self.graph.edges:
            if e.source not in node_ids:
                summary.errors.append(f"Edge references missing source: {e.source}")
            if e.target not in node_ids:
                summary.errors.append(f"Edge references missing target: {e.target}")
            key = (e.source, e.target, e.relationship)
            if key in seen_edges:
                summary.warnings.append(f"Duplicate edge: {key}")
            seen_edges.add(key)

        summary.node_count = len(self.graph.nodes)
        summary.edge_count = len(self.graph.edges)
        summary.is_valid()

        return summary

    def to_index_dict(self, include_gaps: bool = True) -> Dict[str, Any]:
        """Build the full index dictionary including metadata and optionally gaps.

        Args:
            include_gaps: Whether to include the gaps section in the output.

        Returns:
            A dictionary suitable for JSON serialization.
        """
        # Compute per-type counts
        node_counts: Dict[str, int] = {}
        for n in self.graph.nodes:
            node_counts[n.type] = node_counts.get(n.type, 0) + 1

        edge_counts: Dict[str, int] = {}
        for e in self.graph.edges:
            edge_counts[e.relationship] = edge_counts.get(e.relationship, 0) + 1

        index_data = {
            "metadata": {
                "schema_version": "2.2",
                "generator_version": "1.0.0",
                "generated_at": self.graph.generated_at,
                "repository_root": self.graph.repository_root,
                "python_version": "3.11",  # Placeholder - should be system.version
                "scanner_versions": {
                    "MetadataScanner": "1.0",
                    "BackendScanner": "1.0",
                    "FrontendScanner": "1.0",
                    "ApiScanner": "1.0",
                    "TestScanner": "1.0",
                    "DocsScanner": "1.0",
                    "WorkflowScanner": "1.0",
                    "ScriptScanner": "1.0",
                    "MigrationScanner": "1.0",
                },
                "node_count": len(self.graph.nodes),
                "edge_count": len(self.graph.edges),
                "node_types": dict(sorted(node_counts.items())),
                "edge_relationships": dict(sorted(edge_counts.items())),
                "ownership_classes": list(sorted(OWNERSHIP_CLASSES)),
                "validation_summary": {
                    "total_nodes": len(self.graph.nodes),
                    "total_edges": len(self.graph.edges),
                    "unknown_ownership_nodes": sum(1 for n in self.graph.nodes if n.ownership == "unknown"),
                    "has_errors": False,  # Will be filled after validate() call
                },
            },
            "graph": {
                "nodes": [n.to_dict() for n in self.graph.nodes],
                "edges": self._unique_edges_as_dicts(),
            },
        }

        if include_gaps and self.gaps:
            index_data["gaps"] = self.gaps

        return index_data

    def _unique_edges_as_dicts(self) -> List[Dict[str, Any]]:
        """Return de-duplicated edges as dicts (source/target/relationship unique)."""
        seen: set[tuple[str, str, str]] = set()
        unique_edges: List[Dict[str, Any]] = []
        for e in self.graph.edges:
            key = (e.source, e.target, e.relationship)
            if key not in seen:
                seen.add(key)
                unique_edges.append(e.to_dict())
        return unique_edges

    def write_index(self, output_path: Path | None = None) -> Path:
        """Generate and write the index to disk.

        Args:
            output_path: Where to write the index (defaults to
                repo_intelligence/index.json relative to this file).

        Returns:
            The path where the index was written.
        """
        if self.graph is None:
            raise RuntimeError("Call build() first before writing index")

        if output_path is None:
            output_path = Path(__file__).parent / "index.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build full index dict with metadata
        index_data = self.to_index_dict(include_gaps=True)

        # Write formatted JSON
        output_path.write_text(
            json.dumps(index_data, indent=2, default=str),
            encoding="utf-8",
        )

        return output_path

    def get_builder_metrics(self) -> Dict[str, Any]:
        """Get summary statistics about what the builder discovered.

        Returns:
            Dictionary with node counts, edge counts, gap information,
            and ownership distribution.
        """
        if self.graph is None:
            return {"error": "No graph built yet"}

        # Ownership distribution
        ownership_dist: Dict[str, int] = {}
        for n in self.graph.nodes:
            ownership_dist[n.ownership] = ownership_dist.get(n.ownership, 0) + 1

        # Per-type node counts
        node_counts: Dict[str, int] = {}
        for n in self.graph.nodes:
            node_counts[n.type] = node_counts.get(n.type, 0) + 1

        # Per-edge relationship counts
        edge_counts: Dict[str, int] = {}
        for e in self.graph.edges:
            edge_counts[e.relationship] = edge_counts.get(e.relationship, 0) + 1

        return {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "node_types": dict(sorted(node_counts.items())),
            "edge_relationships": dict(sorted(edge_counts.items())),
            "ownership_distribution": dict(sorted(ownership_dist.items())),
            "gaps": {
                "missing_modules": len(self.gaps.get("missing_modules", [])),
                "orphan_modules": len(self.gaps.get("orphan_modules", [])),
                "no_verification_evidence": len(self.gaps.get("no_verification_evidence", [])),
                "no_documentation_evidence": len(self.gaps.get("no_documentation_evidence", [])),
                "unknown_ownership_modules": len(self.gaps.get("unknown_ownership_modules", [])),
                "missing_dependencies": len(self.gaps.get("missing_dependencies", [])),
            },
        }
