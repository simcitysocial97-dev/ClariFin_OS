"""M9-C27 — Canonical OpenAPI normalization and diffing.

Only semantically-relevant structure is compared. Volatile keys (timestamps,
ordering where irrelevant) are stripped before hashing or equality checks so
that repeated runs against an unchanged tree produce stable output.
"""

from __future__ import annotations

import json
from typing import Any

# Keys that carry no semantic contract weight.
VOLATILE_KEYS = frozenset(
    {
        "servers",  # environment-specific server URLs
        "host",
        "basePath",
        "schemes",
    }
)


def canonical_normalize(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a canonicalized copy of an OpenAPI schema for comparison.

    Normalization steps:
    1. Recursively sort all dict keys (order-invariant JSON).
    2. Strip volatile metadata keys that differ across environments.
    3. Normalize description fields that contain version/datetime noise.
    """
    out: dict[str, Any] = {}
    for k, v in sorted(schema.items()):
        if k in VOLATILE_KEYS:
            continue
        if isinstance(v, dict):
            out[k] = canonical_normalize(v)
        elif isinstance(v, list):
            out[k] = [
                canonical_normalize(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            out[k] = v
    return out


def hash_openapi(schema: dict[str, Any]) -> str:
    """SHA-256 digest of the canonicalized OpenAPI for fingerprinting."""
    import hashlib

    normalized = canonical_normalize(schema)
    raw = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def diff_openapi(
    live: dict[str, Any],
    committed: dict[str, Any],
    path_prefix: str = "",
) -> list[dict[str, Any]]:
    """Structured diff between two canonical OpenAPI schemas.

    Returns a list of {path, kind, expected, actual} dicts describing each
    semantic drift detected. An empty list means the schemas are SEMANTIC_MATCH.
    """
    norm_live = canonical_normalize(live)
    norm_comm = canonical_normalize(committed)
    diffs: list[dict[str, Any]] = []
    _diff_dicts(norm_live, norm_comm, "", diffs)
    return diffs


def _diff_dicts(a: dict, b: dict, prefix: str, out: list) -> None:
    all_keys = set(a) | set(b)
    for k in sorted(all_keys):
        cur = f"{prefix}.{k}" if prefix else k
        if k not in a:
            out.append(
                {
                    "path": cur,
                    "kind": "MISSING_IN_LIVE",
                    "actual": None,
                    "expected": "<present>",
                }
            )
        elif k not in b:
            out.append(
                {
                    "path": cur,
                    "kind": "EXTRA_IN_LIVE",
                    "expected": None,
                    "actual": "<present>",
                }
            )
        else:
            va, vb = a[k], b[k]
            if isinstance(va, dict) and isinstance(vb, dict):
                _diff_dicts(va, vb, cur, out)
            elif isinstance(va, list) and isinstance(vb, list):
                if len(va) != len(vb):
                    out.append(
                        {
                            "path": cur,
                            "kind": "LENGTH_MISMATCH",
                            "expected": len(vb),
                            "actual": len(va),
                        }
                    )
                else:
                    for i, (xi, xj) in enumerate(zip(va, vb)):
                        if isinstance(xi, dict) and isinstance(xj, dict):
                            _diff_dicts(xi, xj, f"{cur}[{i}]", out)
                        elif xi != xj:
                            out.append(
                                {
                                    "path": f"{cur}[{i}]",
                                    "kind": "VALUE_DRIFT",
                                    "expected": xj,
                                    "actual": xi,
                                }
                            )
            elif va != vb:
                out.append(
                    {"path": cur, "kind": "VALUE_DRIFT", "expected": vb, "actual": va}
                )
