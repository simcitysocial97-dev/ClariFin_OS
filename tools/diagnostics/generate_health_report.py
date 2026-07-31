#!/usr/bin/env python3
"""Repository Health Report generator for Program 2.2 Phase 7.

Produces a comprehensive health summary including:
- Node/edge counts
- Validation results (errors/warnings/infos)
- Coverage metrics
- Top structural insights
"""

import json
from pathlib import Path
from repo_intelligence.validator import Validator
from repo_intelligence.metrics import calculate_metrics
from repo_intelligence.index import RepositoryIndexer


def main() -> None:
    repo_root = Path(__file__).parent
    index_path = repo_root / "repo_intelligence" / "index.json"

    # Ensure index is up-to-date
    if not index_path.exists():
        print("Index not found. Generating...")
        indexer = RepositoryIndexer(repo_root)
        indexer.write_index()
    else:
        print(f"Using existing index: {index_path}")

    # Load data
    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Calculate metrics
    metrics = calculate_metrics(data)

    # Run validation
    validator = Validator(index_path)
    validation_report = validator.summarize()

    # Build the health report
    report = {
        "generated_at": "ClariFin_OS Repository Intelligence Runtime",
        "schema_version": metrics.get("schema_version", "unknown"),
        "index_generation_timestamp": metrics.get("generated_at", "unknown"),
        "repository_root": str(repo_root),
        "summary": {
            "total_nodes": metrics["total_nodes"],
            "total_edges": metrics["total_edges"],
            "validation_errors": validation_report.get("errors", 0),
            "validation_warnings": validation_report.get("warnings", 0),
            "validation_infos": validation_report.get("infos", 0),
            "total_findings": validation_report["total_findings"],
        },
        "coverage": {
            "ownership_coverage_percent": metrics.get("ownership_coverage_percent", 0),
            "verification_coverage_percent": metrics.get("verification_coverage_percent", 0),
            "documentation_coverage_percent": metrics.get("documentation_coverage_percent", 0),
        },
        "structural_insights": {
            "largest_capability": metrics.get("largest_capability"),
            "largest_capability_scope": metrics.get("largest_capability_scope_edges"),
            "top_10_fan_out": metrics.get("top_10_fan_out_nodes", []),
            "top_10_fan_in": metrics.get("top_10_fan_in_nodes", []),
            "dead_nodes_count": len(metrics.get("dead_nodes", [])),
            "orphan_module_percentage": metrics.get("orphan_module_percentage", 0),
            "graph_density": metrics.get("graph_density", 0),
        },
        "top_orphan_modules": get_top_orphans(data)[:10],
        "top_dependency_chains": metrics.get("longest_dependency_chain", []),
        "validation_findings_by_severity": {
            "errors": validation_report["errors_by_code"],
            "warnings": validation_report["warnings_by_code"],
            "infos": validation_report["infos_by_code"],
        },
    }

    # Print as JSON (machine-readable)
    print(json.dumps(report, indent=2, default=str))


def get_top_orphans(data: dict, limit: int = 10) -> list[dict]:
    """Return top orphan modules from gaps."""
    gaps = data.get("gaps", {})
    orphans = gaps.get("orphan_modules", [])
    # Sort by path for determinism
    return sorted(orphans, key=lambda x: x.get("path", ""))[:limit]


if __name__ == "__main__":
    main()
