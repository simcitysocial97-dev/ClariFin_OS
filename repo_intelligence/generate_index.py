#!/usr/bin/env python3
"""Convenience script to generate the canonical repository index.

Usage::

    python repo_intelligence/generate_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the package is importable when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from repo_intelligence.index import RepositoryIndexer


def main() -> int:
    indexer = RepositoryIndexer()
    output_path = indexer.write_index()
    print(f"Index generated: {output_path}")
    metadata = indexer.to_index_dict().get("metadata", {})
    print(f"  Total nodes: {metadata.get('total_nodes', '?')}")
    print(f"  Total edges: {metadata.get('total_edges', '?')}")
    node_counts = metadata.get("node_counts", {})
    for ntype, count in sorted(node_counts.items()):
        print(f"  {ntype}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
