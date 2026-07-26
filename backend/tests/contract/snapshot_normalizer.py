"""Snapshot normalization utilities for contract tests."""

from __future__ import annotations

import json
import re
from typing import Any


def normalize_response(data: dict[str, Any] | list[Any] | str) -> str:
    """Normalize response for snapshot comparison.

    Handles:
    - UUIDs -> [UUID]
    - Timestamps -> [TIMESTAMP]
    - Generated IDs -> [ID]
    - Version numbers -> [VERSION]
    """
    if isinstance(data, str):
        return _normalize_string(data)

    if isinstance(data, dict):
        result = {}
        for k, v in sorted(data.items()):
            result[k] = normalize_response(v)
        return json.dumps(result, sort_keys=True)

    if isinstance(data, list):
        result = [normalize_response(item) for item in data]
        return json.dumps(result, sort_keys=True)

    return str(data)


def _normalize_string(s: str) -> str:
    """Normalize a string value."""
    # Normalize ISO timestamps
    s = re.sub(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
        "[TIMESTAMP]",
        s,
    )
    # Normalize date-only strings
    s = re.sub(r"\d{4}-\d{2}-\d{2}", "[DATE]", s)
    # Normalize UUIDs
    s = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "[UUID]",
        s,
        flags=re.IGNORECASE,
    )
    # Normalize version numbers (semver)
    s = re.sub(r"\d+\.\d+\.\d+", "[VERSION]", s)
    # Normalize integer IDs (standalone numbers that look like DB IDs)
    s = re.sub(r'"id":\s*(\d{4,})', '"id": "[ID]"', s)
    return s


def save_snapshot(
    snapshot_dir: Any, router_name: str, endpoint_name: str, data: str
) -> None:
    """Save normalized snapshot to file."""
    from pathlib import Path

    router_dir = Path(snapshot_dir) / router_name
    router_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = router_dir / f"{endpoint_name}.snapshot.json"
    with open(snapshot_path, "w") as f:
        f.write(data)


def load_snapshot(
    snapshot_dir: Any, router_name: str, endpoint_name: str
) -> str | None:
    """Load existing snapshot if present."""
    from pathlib import Path

    snapshot_path = Path(snapshot_dir) / router_name / f"{endpoint_name}.snapshot.json"
    if snapshot_path.exists():
        with open(snapshot_path) as f:
            return f.read()
