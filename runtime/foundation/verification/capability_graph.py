# runtime/foundation/verification/capability_graph.py
#
# M9-C51 — Capability dependency graph (M51.9).
#
# Builds a machine-readable graph showing relationships between verification
# capabilities: prerequisites, successors, evidence dependencies,
# authorization boundaries, and escalation edges.
#
# The canonical pipeline spine is:
#   changed-file -> blast-radius -> capability-resolution -> execution-plan
#     -> execute -> measurement-truth -> diagnostic -> strengthening
#       -> targeted-revalidation -> certification
#
# Mutation appears as a SUBORDINATE MEASUREMENT capability, not top-level.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

from runtime.foundation.verification.capability_catalog import (
    get_capability_catalog,
)


class GraphEdgeType(str, Enum):
    PREREQUISITE = "prerequisite"
    SUCCESSOR = "successor"
    EVIDENCE_DEPENDENCY = "evidence_dependency"
    AUTHORIZATION_BOUNDARY = "authorization_boundary"
    ESCALATION = "escalation"


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    edge_type: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityGraph:
    """The capability dependency graph."""

    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "m9-c51-capability-graph/v1",
            "generated_at": self.generated_at,
            "nodes": self.nodes,
            "edges": [e.to_dict() for e in self.edges],
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


def build_capability_graph() -> CapabilityGraph:
    """Build the capability dependency graph from the catalog."""
    catalog = get_capability_catalog()
    graph = CapabilityGraph()

    # Add nodes
    for entry in catalog.entries:
        graph.nodes.append(
            {
                "id": entry.capability_id,
                "stage": entry.stage.value,
                "command": entry.command,
                "authorization": entry.authorization.value,
            }
        )

    # Build index for quick lookups
    ids = {e.capability_id for e in catalog.entries}

    # Add edges based on metadata
    for entry in catalog.entries:
        # Prerequisite edges
        for pre in entry.preconditions:
            if pre in ids:
                graph.edges.append(
                    GraphEdge(
                        source=entry.capability_id,
                        target=pre,
                        edge_type=GraphEdgeType.PREREQUISITE.value,
                        reason=f"{entry.capability_id} requires {pre}",
                    )
                )

        # Authorization boundary edges
        if entry.authorization.value in ("human", "ci_only"):
            graph.edges.append(
                GraphEdge(
                    source=entry.capability_id,
                    target=entry.capability_id,
                    edge_type=GraphEdgeType.AUTHORIZATION_BOUNDARY.value,
                    reason=f"{entry.capability_id} requires {entry.authorization.value} authorization",
                )
            )

    # Add evidence dependency edges (producer -> consumer)
    coverage_producers = catalog.producers_of("coverage_measurement")
    coverage_consumers = catalog.consumers_of("coverage_measurement")
    for prod_entry in coverage_producers:
        for cons_entry in coverage_consumers:
            if cons_entry.capability_id != prod_entry.capability_id:
                graph.edges.append(
                    GraphEdge(
                        source=prod_entry.capability_id,
                        target=cons_entry.capability_id,
                        edge_type=GraphEdgeType.EVIDENCE_DEPENDENCY.value,
                        reason="Evidence kind: coverage_measurement",
                    )
                )

    # Add canonical pipeline spine edges (hardcoded for verification)
    spine_edges = [
        ("discover.blast-radius", "plan.execution-plan", GraphEdgeType.SUCCESSOR),
        ("plan.execution-plan", "exec.orchestrator", GraphEdgeType.SUCCESSOR),
        ("exec.orchestrator", "measure.truth-report", GraphEdgeType.SUCCESSOR),
        (
            "measure.truth-report",
            "diagnose.failure-attribution",
            GraphEdgeType.SUCCESSOR,
        ),
        (
            "diagnose.failure-attribution",
            "strengthen.survivor-intel",
            GraphEdgeType.SUCCESSOR,
        ),
        (
            "strengthen.survivor-intel",
            "strengthen.capability-pipeline",
            GraphEdgeType.SUCCESSOR,
        ),
        (
            "strengthen.capability-pipeline",
            "measure.mutation",
            GraphEdgeType.ESCALATION,
        ),
        ("measure.mutation", "certify.contract-governance", GraphEdgeType.SUCCESSOR),
    ]
    for src, tgt, etype in spine_edges:
        if src in ids and tgt in ids:
            graph.edges.append(
                GraphEdge(
                    source=src,
                    target=tgt,
                    edge_type=etype.value,
                    reason="Canonical pipeline spine",
                )
            )

    return graph


def verify_pipeline_spine(graph: CapabilityGraph) -> tuple[bool, list[str]]:
    """Verify the canonical pipeline spine exists in the graph."""
    issues: list[str] = []
    required_edges = [
        ("discover.blast-radius", "plan.execution-plan"),
        ("plan.execution-plan", "exec.orchestrator"),
        ("exec.orchestrator", "measure.truth-report"),
    ]
    edge_pairs = [(e.source, e.target) for e in graph.edges]
    for src, tgt in required_edges:
        if (src, tgt) not in edge_pairs:
            issues.append(f"Missing spine edge: {src} -> {tgt}")

    # Mutation must NOT be a top-level capability (it should be subordinate)
    mutation_cap = next((n for n in graph.nodes if n["id"] == "measure.mutation"), None)
    if mutation_cap:
        stages_before_mutation = [
            n["stage"]
            for n in graph.nodes
            if any(
                e.source == n["id"] and e.target == "measure.mutation"
                for e in graph.edges
            )
        ]
        if not stages_before_mutation or "certification" in stages_before_mutation:
            issues.append("Mutation appears at wrong stage position")

    return len(issues) == 0, issues


def cmd_capability_graph(argv: list[str]) -> int:
    """verify.py capability-graph — display the capability dependency graph."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py capability-graph", add_help=False)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    graph = build_capability_graph()
    valid, issues = verify_pipeline_spine(graph)

    output = graph.to_json() if args.json else _format_graph(graph, valid, issues)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Written to {args.out}")
    else:
        print(output)
    return 0 if valid else 1


def _format_graph(graph: CapabilityGraph, valid: bool, issues: list[str]) -> str:
    lines = ["CAPABILITY DEPENDENCY GRAPH (M9-C51)", "=" * 60]
    lines.append(f"Nodes: {len(graph.nodes)}  Edges: {len(graph.edges)}")
    lines.append(f"Spine valid: {'YES' if valid else 'NO'}")
    if not valid:
        for i in issues:
            lines.append(f"  ISSUE: {i}")
    lines.append("")
    lines.append("NODES BY STAGE:")
    by_stage: dict[str, list[str]] = {}
    for n in graph.nodes:
        by_stage.setdefault(n["stage"], []).append(n["id"])
    for stage in sorted(by_stage.keys()):
        lines.append(f"\n  {stage.upper()} ({len(by_stage[stage])})")
        for nid in sorted(by_stage[stage]):
            lines.append(f"    • {nid}")
    lines.append("")
    lines.append("KEY EDGES:")
    for e in graph.edges[:30]:
        lines.append(f"  {e.source} --[{e.edge_type}]--> {e.target}")
    if len(graph.edges) > 30:
        lines.append(f"  ... and {len(graph.edges) - 30} more edges")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    sys.exit(cmd_capability_graph(sys.argv[1:]))
