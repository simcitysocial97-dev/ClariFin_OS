"""Cross-Layer Impact service — Phase J.

Exposes the canonical cross-layer graph (from C60/C61) through
the Platform API. No second graph is introduced.

Data source: runtime/generated/cross-layer-graph.json +
runtime/foundation/verification/cross_layer_graph.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.platform.api.contracts._primitives import Timestamp
from runtime.platform.api.services._helpers import envelope, now_iso

__all__ = [
    "build_cross_layer_graph",
    "build_cross_layer_capability",
]

_GRAPH_PATH = Path("runtime/generated/cross-layer-graph.json")


def _load_graph() -> dict[str, Any] | None:
    """Load the canonical cross-layer graph from disk."""
    if not _GRAPH_PATH.exists():
        return None
    try:
        return json.loads(_GRAPH_PATH.read_text())
    except Exception:
        return None


def build_cross_layer_graph() -> dict[str, Any]:
    """Expose the full cross-layer graph as a canonical Platform API response."""

    graph = _load_graph()
    if graph is None:
        return envelope(kind="platform.cross_layer_graph", data={
            "count": 0,
            "edges": [],
            "frontend_capabilities": {},
            "contract_drifts": [],
            "unmapped_frontend": [],
            "metadata": {"source": "cross-layer-graph.json", "available": False},
        })

    return envelope(kind="platform.cross_layer_graph", data={
        "count": len(graph.get("edges", [])),
        "edges": graph.get("edges", []),
        "frontend_capabilities": graph.get("frontend_capabilities", {}),
        "contract_drifts": graph.get("contract_drifts", []),
        "unmapped_frontend": graph.get("unmapped_frontend", []),
        "metadata": {
            "source": "cross-layer-graph.json",
            "available": True,
            "generated_at": _GRAPH_PATH.stat().st_mtime,
        },
    })


def build_cross_layer_capability(capability_id: str) -> dict[str, Any] | None:
    """Expose cross-layer details for a specific capability."""

    graph = _load_graph()
    if graph is None:
        return None

    capabilities = graph.get("frontend_capabilities", {})
    if capability_id not in capabilities:
        return None

    cap = capabilities[capability_id]
    edges = graph.get("edges", [])
    related_edges = [e for e in edges if e.get("source_id") == capability_id]

    return envelope(kind="platform.cross_layer_capability", data={
        "capability_id": capability_id,
        "name": cap.get("name", capability_id),
        "kind": cap.get("kind", "unknown"),
        "domain": cap.get("domain", "unknown"),
        "files": cap.get("files", []),
        "backend_capabilities": cap.get("backend_capabilities", []),
        "backend_endpoints": cap.get("backend_endpoints", []),
        "status": cap.get("status", "UNMAPPED"),
        "related_edges": related_edges,
        "blast_radius": {
            "affected_tests": [e.get("target_id", "") for e in related_edges],
            "affected_capabilities": list(set(e.get("target_id", "") for e in related_edges)),
        },
        "verification_obligations": [],
    })
