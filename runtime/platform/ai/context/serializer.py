"""Serializer (Phase 14).

Canonical JSON serialization for context packs enabling content-addressing
via SHA-256. Deterministic output guarantees reproducible pack identities.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical_value(obj: Any) -> Any:
    """Recursively normalize a value for deterministic serialization."""
    if isinstance(obj, dict):
        return {k: _canonical_value(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_canonical_value(item) for item in obj]
    if isinstance(obj, bool):
        return int(obj)
    if isinstance(obj, (int, float)):
        return obj
    if obj is None:
        return None
    return str(obj)


def serialize_context_pack(pack: dict[str, Any]) -> str:
    """Serialize a context pack to canonical JSON string.

    Output is deterministic: same inputs always produce same bytes.
    """
    normalized = _canonical_value(pack)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def compute_pack_id(pack: dict[str, Any]) -> str:
    """Compute SHA-256 identity for a context pack.

    Excludes timestamp fields to ensure reproducibility: same inputs
    always produce the same pack_id regardless of when it was built.
    """
    # Create a copy without temporal fields for hashing
    compact = {
        k: v
        for k, v in pack.items()
        if k not in ("generated_at", "checksum", "pack_id")
    }
    serialized = serialize_context_pack(compact)
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    return f"ctx-{digest[:16]}"


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


def compute_pack_checksum(pack: dict[str, Any]) -> str:
    """Full SHA-256 checksum of the entire pack for verification."""
    serialized = serialize_context_pack(pack)
    return hashlib.sha256(serialized.encode()).hexdigest()
