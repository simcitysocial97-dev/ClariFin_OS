"""Base scanner infrastructure.

All scanners inherit from :class:`BaseScanner` and implement :meth:`scan`.
The ``scan`` method returns a :class:`ScanResult` containing nodes and edges
that are merged into the repository graph by the indexer.
"""

from __future__ import annotations

import ast
import hashlib
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from repo_intelligence.schema import GraphEdge, GraphNode


class ScanResult:
    """Container for a scanner's output: nodes + edges."""

    def __init__(self) -> None:
        self.nodes: list[GraphNode] = []
        self.edges: list[GraphEdge] = []

    def add_node(
        self,
        node_type: str,
        name: str,
        path: str,
        source: str,
        properties: dict[str, Any] | None = None,
        node_id: str | None = None,
    ) -> GraphNode:
        """Create and store a node, returning it for edge construction.

        If ``node_id`` is provided it overrides the default ``<type>:<path>``
        scheme, allowing multiple nodes of the same type to share a path
        (e.g. capabilities all referencing the registry file).
        """
        if node_id is None:
            node_id = f"{node_type}:{path}"
        node = GraphNode(
            id=node_id,
            type=node_type,
            name=name,
            path=path,
            source=source,
            properties=properties or {},
        )
        self.nodes.append(node)
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        confidence: float = 1.0,
        evidence: str = "",
    ) -> None:
        """Create and store an edge."""
        self.edges.append(
            GraphEdge(
                source=source_id,
                target=target_id,
                relationship=relationship,
                confidence=confidence,
                evidence=evidence,
            )
        )

    def get_node(self, node_id: str) -> GraphNode | None:
        """Retrieve a node by ID."""
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def merge(self, other: ScanResult) -> None:
        """Merge another ScanResult into this one."""
        self.nodes.extend(other.nodes)
        self.edges.extend(other.edges)


class BaseScanner(ABC):
    """Abstract base class for all repository scanners.

    Scanners receive the repository root and produce ``ScanResult`` objects.
    They must be deterministic and must not execute repository code.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.backend_dir = repo_root / "backend"
        self.frontend_dir = repo_root / "frontend"
        self.src_dir = self.backend_dir / "src"
        self.tests_dir = self.backend_dir / "tests"
        self.generated_dir = self.tests_dir / "generated"

    @abstractmethod
    def scan(self) -> ScanResult:
        """Run the scanner and return discovered nodes + edges."""

    # -- shared helpers ------------------------------------------------------

    @staticmethod
    def safe_read(path: Path) -> str | None:
        """Read a file safely, returning None on any error."""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    @staticmethod
    def safe_parse_ast(path: Path) -> ast.Module | None:
        """Parse a Python file with AST, returning None on syntax errors."""
        content = BaseScanner.safe_read(path)
        if content is None:
            return None
        try:
            return ast.parse(content)
        except SyntaxError:
            return None

    @staticmethod
    def safe_read_json(path: Path) -> dict[str, Any] | None:
        """Read and parse a JSON file, returning None on error."""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def safe_read_yaml(path: Path) -> dict[str, Any] | None:
        """Read and parse a YAML file, returning None on error."""
        try:
            import yaml

            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def rel_path(path: Path, base: Path) -> str:
        """Get a path relative to base, as a forward-slash string."""
        try:
            return str(path.relative_to(base)).replace("\\", "/")
        except ValueError:
            return str(path)

    @staticmethod
    def content_hash(content: str) -> str:
        """Compute a short SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
