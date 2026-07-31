"""Repository Index Generator — Phase 3.

Orchestrates scanning and building, then writes the canonical repository index.

This module uses :class:`RepositoryBuilder` to separate concerns from the
query runtime. The builder runs scanners, merges results, assigns ownership,
detects gaps, validates, generates the graph, and writes the index.

All query modules must use :class:`RepositoryGraphService` (see
:mod:`repo_intelligence.graph_service`) rather than accessing graph internals
directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from runtime.foundation.repository.builder import RepositoryBuilder, ValidationSummary
from runtime.foundation.repository.graph.schema import RepositoryGraph


class RepositoryIndexer:
    """Compatibility wrapper over RepositoryBuilder for existing code.

    This maintains backward compatibility with code that imports
    RepositoryIndexer while delegating to the separated builder.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self._builder = RepositoryBuilder(repo_root)

    def build(self) -> RepositoryGraph:
        """Run all scanners and merge results into a single graph.

        Returns:
            The fully built RepositoryGraph.
        """
        return self._builder.build()

    def to_index_dict(self) -> Dict[str, Any]:
        """Build the full index dictionary including metadata and gaps.

        This method provides backward compatibility with the old index.py API.
        It delegates to RepositoryBuilder.to_index_dict().
        """
        # We need to access the builder's gaps; they are set after build()
        if not hasattr(self._builder, 'graph') or self._builder.graph is None:
            self._builder.build()
        return self._builder.to_index_dict(include_gaps=True)

    def write_index(self, output_path: Path | None = None) -> Path:
        """Generate the index and write it to ``index.json``."""
        if len(self._builder.graph.nodes) == 0:
            self.build()
        return self._builder.write_index(output_path)

    def get_metrics(self) -> Dict[str, Any]:
        """Get summary statistics from the builder.

        Returns:
            Dictionary containing node counts, edge counts, gap info, and
            ownership distribution.
        """
        if len(self._builder.graph.nodes) == 0:
            self.build()
        return self._builder.get_builder_metrics()

    def validate(self) -> ValidationSummary:
        """Validate the constructed graph.

        Returns:
            A ValidationSummary object.
        """
        if len(self._builder.graph.nodes) == 0:
            self.build()
        return self._builder.validate()


# Backward compatibility: expose the new classes directly
__all__ = [
    "RepositoryIndexer",
    "RepositoryBuilder",
    "ValidationSummary",
]
