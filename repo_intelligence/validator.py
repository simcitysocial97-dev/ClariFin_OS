"""Graph Validation Routines — Phase 6.

The validator checks for structural integrity and semantic correctness of the
canonical repository index without modifying the index itself. All validation
runs are deterministic and produce a report containing findings categorized into
ERROR, WARNING, and INFO levels (no failures), following the principle that
discovery should not block analysis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Dict, Set, Optional



class ValidationFinding:
    """A single validation finding with evidence explaining its existence."""

    def __init__(self, severity: str, code: str, message: str,
                 node_id: Optional[str] = None, related_nodes: Optional[List[str]] = None,
                 edge: Optional[Dict[str, str]] = None, evidence: str = "") -> None:
        self.severity = severity  # ERROR, WARNING, or INFO
        self.code = code          # e.g., "UNKNOWN_OWNERSHIP", "BROKEN_REFERENCE"
        self.message = message
        self.node_id = node_id
        self.related_nodes = related_nodes or []
        self.edge = edge or {}    # {"source": "...", "target": "...", "relationship": "..."}
        self.evidence = evidence  # Why this finding exists

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.node_id:
            result["node_id"] = self.node_id
        if self.related_nodes:
            result["related_nodes"] = self.related_nodes
        if self.edge:
            result["edge"] = self.edge
        if self.evidence:
            result["evidence"] = self.evidence
        return result


class Validator:
    """Deterministic structural and semantic checks on the canonical index."""

    def __init__(self, index_path: Path | None = None):
        self._index_path = index_path or Path(__file__).parent.parent / "repo_intelligence" / "index.json"
        self._data = None

    def load(self) -> None:
        """Load the index from disk."""
        with open(self._index_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def find_all(self) -> List[ValidationFinding]:
        """Run all validation checks and collect findings.

        Returns a list of ValidationFinding objects categorized by severity.
        """
        if self._data is None:
            self.load()

        findings: List[ValidationFinding] = []
        nodes = self._data.get("nodes", [])
        edges = self._data.get("edges", [])
        all_node_ids: Set[str] = {n["id"] for n in nodes}

        # --- ERROR-level: Critical structural issues ---

        # Duplicate node IDs (should never happen but validate anyway)
        seen_id: Dict[str, int] = {}
        for node in nodes:
            nid = node["id"]
            seen_id[nid] = seen_id.get(nid, 0) + 1
        for nid, count in seen_id.items():
            if count > 1:
                findings.append(ValidationFinding(
                    severity="ERROR",
                    code="DUPLICATE_NODE",
                    message=f"Node ID '{nid}' appears {count} times",
                    node_id=nid,
                    evidence=f"Count {count} in index nodes list, expected unique identifiers",
                ))

        # Broken references (edges pointing to non-existent nodes)
        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            rel = edge["relationship"]
            if src not in all_node_ids:
                findings.append(ValidationFinding(
                    severity="ERROR",
                    code="BROKEN_REFERENCE_SOURCE",
                    message=f"Edge source '{src}' does not exist in graph",
                    edge={"source": src, "target": tgt, "relationship": rel},
                    evidence=f"Source node '{src}' referenced by edge but absent from node list",
                ))
            if tgt not in all_node_ids:
                findings.append(ValidationFinding(
                    severity="ERROR",
                    code="BROKEN_REFERENCE_TARGET",
                    message=f"Edge target '{tgt}' does not exist in graph",
                    edge={"source": src, "target": tgt, "relationship": rel},
                    evidence=f"Target node '{tgt}' referenced by edge but absent from node list",
                ))

        # Missing capability canonical id field
        for node in nodes:
            if node["type"] == "capability":
                cap_props = node.get("properties", {})
                if not cap_props.get("id"):
                    findings.append(ValidationFinding(
                        severity="WARNING",
                        code="MISSING_CAPABILITY_ID",
                        message=f"Capability '{node['name']}' has no canonical identifier",
                        node_id=node["id"],
                        evidence="Capability node missing required 'id' property in properties dict",
                    ))

        # --- WARNING-level: Semantic/gap concerns ---

        # Unknown ownership modules
        for node in nodes:
            if node["type"] == "module" and node.get("ownership") == "unknown":
                findings.append(ValidationFinding(
                    severity="WARNING",
                    code="UNKNOWN_OWNERSHIP",
                    message=f"Module '{node['name']}' at {node['path']} has unknown ownership — requires classification",
                    node_id=node["id"],
                    evidence="No capability owns this module; no classifier assigned an ownership category",
                ))

        # Endpoints with no verification evidence
        verified_ep_ids: Set[str] = set()
        for edge in edges:
            if edge["relationship"] == "verifies" and edge["source"].startswith("capability:"):
                verified_ep_ids.add(edge["target"])
        for node in nodes:
            if node["type"] == "endpoint" and node["id"] not in verified_ep_ids:
                cap_id = node.get("properties", {}).get("capability", "unknown")
                findings.append(ValidationFinding(
                    severity="WARNING",
                    code="VERIFICATION_GAP",
                    message=f"Endpoint '{node['name']}' lacks verification evidence from any capability",
                    node_id=node["id"],
                    evidence="No 'verifies' edge points to this endpoint from a capability node",
                ))

        # Capabilities with no documentation evidence
        documented_cap_ids: Set[str] = set()
        for edge in edges:
            if edge["relationship"] == "documents":
                documented_cap_ids.add(edge["source"])
        for node in nodes:
            if node["type"] == "capability":
                cap_node_id = node["id"]
                if cap_node_id not in documented_cap_ids:
                    findings.append(ValidationFinding(
                        severity="WARNING",
                        code="DOCUMENTATION_GAP",
                        message=f"Capability '{node['name']}' lacks documentation evidence",
                        node_id=cap_node_id,
                        evidence="No 'documents' edge originates from this capability to documentation nodes",
                    ))

        # --- INFO-level: Observational data ---

        # Node type distribution summary
        type_counts: Dict[str, int] = {}
        for node in nodes:
            t = node["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        if type_counts:
            max_type = max(type_counts.keys(), key=lambda k: type_counts[k])
            findings.append(ValidationFinding(
                severity="INFO",
                code="LARGEST_NODE_TYPE",
                message=f"Largest node type category: {max_type} ({type_counts[max_type]} instances)",
                evidence="Category count exceeds all others in the repository index",
            ))

        # Edge relationship count summary
        edge_counts: Dict[str, int] = {}
        for edge in edges:
            r = edge["relationship"]
            edge_counts[r] = edge_counts.get(r, 0) + 1
        if edge_counts:
            max_rel = max(edge_counts.keys(), key=lambda r: edge_counts[r])
            findings.append(ValidationFinding(
                severity="INFO",
                code="MOST_COMMON_EDGE",
                message=f"Most frequent edge relationship: {max_rel} ({edge_counts[max_rel]} edges)",
                evidence="Relationship type appears more than any other in the graph",
            ))

        return findings

    def summarize(self) -> Dict[str, Any]:
        """Summarize findings by severity and code."""
        findings = self.find_all()

        errors: List[ValidationFinding] = [f for f in findings if f.severity == "ERROR"]
        warnings: List[ValidationFinding] = [f for f in findings if f.severity == "WARNING"]
        infos: List[ValidationFinding] = [f for f in findings if f.severity == "INFO"]

        # Group by code within each severity, converting findings to dicts first
        def group_by_code_items(items: List[ValidationFinding]) -> Dict[str, List[Dict[str, Any]]]:
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for item in items:
                grouped.setdefault(item.code, []).append(item.to_dict())
            return grouped

        return {
            "total_findings": len(findings),
            "errors": len(errors),
            "warnings": len(warnings),
            "infos": len(infos),
            "errors_by_code": group_by_code_items(errors),
            "warnings_by_code": group_by_code_items(warnings),
            "infos_by_code": group_by_code_items(infos),
            "findings": [f.to_dict() for f in findings],
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate a complete validation report."""
        summary = self.summarize()
        return {
            "validation_report": summary,
            "timestamp": __name__,  # placeholder
        }


def validate_index(index_path: Path | None = None) -> Dict[str, Any]:
    """Convenience function to validate the canonical repository index.

    Returns a dictionary containing findings distributed by severity, grouped
    by code, with full evidence for each finding.
    """
    validator = Validator(index_path)
    return validator.generate_report()


if __name__ == "__main__":
    report = validate_index()
    print(json.dumps(report, indent=2))

