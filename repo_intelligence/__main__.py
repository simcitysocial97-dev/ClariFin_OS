"""CLI entry point for the Repository Intelligence Runtime.

Usage::

    python -m repo_intelligence                    # generate index + print summary
    python -m repo_intelligence --generate         # generate index only
    python -m repo_intelligence --query reconciliation  # show capability
    python -m repo_intelligence --orphan-modules   # list orphan modules
    python -m repo_intelligence --untested          # list untested endpoints
"""

from __future__ import annotations

import argparse
import json
import sys

from repo_intelligence.index import RepositoryIndexer
from repo_intelligence.query import RepositoryIndex


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repository Intelligence Runtime — ClariFin_OS"
    )
    parser.add_argument(
        "--generate", action="store_true", help="Generate the canonical index"
    )
    parser.add_argument(
        "--query",
        metavar="CAPABILITY_ID",
        help="Show information about a capability",
    )
    parser.add_argument(
        "--orphan-modules",
        action="store_true",
        help="List modules not referenced by any capability",
    )
    parser.add_argument(
        "--untested",
        action="store_true",
        help="List endpoints without test coverage",
    )
    parser.add_argument(
        "--undocumented",
        action="store_true",
        help="List capabilities without documentation",
    )
    parser.add_argument(
        "--owner",
        metavar="ROUTER",
        help="Find the capability that owns a router",
    )
    parser.add_argument(
        "--tests-for",
        metavar="MODULE",
        help="Find tests for a given module",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print index statistics",
    )
    parser.add_argument(
        "--impact",
        metavar="FILE_PATH",
        help="Compute impact analysis for a file",
    )
    parser.add_argument(
        "--trace",
        metavar="NODE_ID",
        help="Trace all graph paths from a node",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Show repository health metrics",
    )
    parser.add_argument(
        "--why",
        metavar="PATH",
        help="Explain all relationships for a node/path",
    )
    parser.add_argument(
        "--search",
        metavar="TEXT",
        help="Search across entities by text term",
    )
    parser.add_argument(
        "--no-verification-evidence",
        action="store_true",
        help="List endpoints with no verification evidence (replaces --untested)",
    )
    parser.add_argument(
        "--no-documentation-evidence",
        action="store_true",
        help="List capabilities with no documentation evidence (replaces --undocumented)",
    )
    parser.add_argument(
        "--unknown-ownership",
        action="store_true",
        help="List modules with unknown ownership",
    )
    args = parser.parse_args()

    if args.generate or not any(
        [args.query, args.orphan_modules, args.untested, args.undocumented,
         args.no_verification_evidence, args.no_documentation_evidence,
         args.unknown_ownership, args.owner, args.tests_for, args.stats,
         args.impact, args.trace, args.health, args.why, args.search]
    ):
        # Generate index
        indexer = RepositoryIndexer()
        output_path = indexer.write_index()
        print(f"Index generated: {output_path}")
        metadata = indexer.to_index_dict().get("metadata", {})
        print(f"  Total nodes: {metadata.get('total_nodes', '?')}")
        print(f"  Total edges: {metadata.get('total_edges', '?')}")
        node_counts = metadata.get("node_counts", {})
        for ntype, count in sorted(node_counts.items()):
            print(f"  {ntype}: {count}")

    if args.query:
        idx = RepositoryIndex()
        result = idx.show_capability(args.query)
        if result is None:
            print(f"Capability '{args.query}' not found")
            return 1
        print(json.dumps(result, indent=2, default=str))

    if args.orphan_modules:
        idx = RepositoryIndex()
        orphans = idx.list_orphan_modules()
        print(f"Orphan modules: {len(orphans)}")
        for m in orphans:
            print(f"  {m['path']} ({m['name']})")

    if args.untested:
        idx = RepositoryIndex()
        untested = idx.list_untested_endpoints()
        print(f"Untested endpoints: {len(untested)}")
        for ep in untested:
            print(f"  {ep['name']}")

    if args.undocumented:
        idx = RepositoryIndex()
        undocumented = idx.list_undocumented_apis()
        print(f"Undocumented capabilities: {len(undocumented)}")
        for cap in undocumented:
            print(f"  {cap['capability_id']}")

    # New evidence-based queries (Phase 4)
    if args.no_verification_evidence:
        idx = RepositoryIndex()
        untested = idx.list_endpoints_with_no_verification_evidence()
        print(f"Endpoints with no verification evidence: {len(untested)}")
        for ep in untested:
            print(f"  {ep['name']} ({ep['method']} {ep.get('endpoint_path', '')})")

    if args.no_documentation_evidence:
        idx = RepositoryIndex()
        docs_no_evidence = idx.list_capabilities_with_no_documentation_evidence()
        print(f"Capabilities with no documentation evidence: {len(docs_no_evidence)}")
        for cap in docs_no_evidence:
            print(f"  {cap['capability_id']}")

    if args.unknown_ownership:
        idx = RepositoryIndex()
        unknown = idx.list_nodes_by_ownership("unknown")
        modules = [m for m in unknown if m["type"] == "module"]
        print(f"Modules with unknown ownership: {len(modules)}")
        for m in sorted(modules, key=lambda x: x.get("path", "")):
            print(f"  {m['path']} ({m['name']})")

    if args.owner:
        idx = RepositoryIndex()
        result = idx.find_owner_of_router(args.owner)
        if result is None:
            print(f"Router '{args.owner}' not found")
            return 1
        print(json.dumps(result, indent=2, default=str))

    if args.tests_for:
        idx = RepositoryIndex()
        tests = idx.find_tests_for_module(args.tests_for)
        print(f"Tests for {args.tests_for}: {len(tests)}")
        for t in tests:
            print(f"  {t.get('path', t.get('id', '?'))}")

    if args.stats:
        idx = RepositoryIndex()
        metadata = idx._data.get("metadata", {})
        print(f"Total nodes: {metadata.get('total_nodes', 0)}")
        print(f"Total edges: {metadata.get('total_edges', 0)}")
        for ntype, count in sorted(metadata.get("node_counts", {}).items()):
            print(f"  {ntype}: {count}")
        for rtype, count in sorted(metadata.get("edge_counts", {}).items()):
            print(f"  edge[{rtype}]: {count}")

    # New Phase 2.2 CLI commands
    if args.impact:
        idx = RepositoryIndex()
        from repo_intelligence.impact import compute_impact
        result = compute_impact(args.impact, max_depth=8)
        print(json.dumps(result, indent=2, default=str))

    if args.trace:
        idx = RepositoryIndex()
        paths = idx.trace(args.trace, max_depth=6)
        print(json.dumps(paths, indent=2, default=str))

    if args.health:
        idx = RepositoryIndex()
        metrics_result = idx.health()
        print(json.dumps(metrics_result, indent=2, default=str))

    if args.why:
        idx = RepositoryIndex()
        explanation = idx.why(args.why)
        print(json.dumps(explanation, indent=2, default=str))

    if args.search:
        idx = RepositoryIndex()
        results = idx.search(args.search)
        print(json.dumps(results, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
