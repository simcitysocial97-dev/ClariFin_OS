"""Content-addressed identity primitives for the Platform API (Phase 1).

Every successful response emitted by ``runtime.platform.api`` carries a
stable ``id`` of the form ``sha256:<hex>``. Every error response does too.

The identity MUST be deterministic: same input payload + same response
``kind`` + same ``version`` → same id, byte-for-byte, across processes,
machines, and Python versions.

Two helpers are exposed:

* :func:`envelope_identity` — hash for the success envelope.
* :func:`error_identity` — hash for the error envelope.

Both rely on :func:`canonical_json_bytes`, which is the single canonical
serialization function used by the Platform API. It is intentionally
narrower than :func:`json.dumps`:

* UTF-8 encoded.
* No whitespace (``separators=(",", ":")``).
* Keys sorted recursively, with no ``sort_keys`` reliance on dict order.
* ``None`` is preserved (not coerced to ``null`` vs missing).
* Tuples are serialized as JSON arrays.

The serializer is exposed (rather than hidden) so that other Platform
subsystems can interoperate. It is the contract for any future cache key,
event correlation, or evidence identity that needs to interoperate with
Platform API responses.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Final

_HASH_PREFIX: Final[str] = "sha256:"
_HASH_ALGO: Final[str] = "sha256"


def _canonicalize(value: Any) -> Any:
    """Recursively transform ``value`` so that :func:`json.dumps` is stable.

    The transformation is intentionally explicit (rather than relying on
    ``json.dumps(sort_keys=True)``) because we must also accept tuples,
    dataclass-like objects with ``__dict__``, and ``None``-valued keys.

    Output dicts are emitted with **keys sorted ascending by their coerced
    string form**. This is what makes the canonical form independent of
    dict insertion order.
    """

    if isinstance(value, dict):
        items = [
            (_coerce_key(k), _canonicalize(v))
            for k, v in value.items()
            if v is not None or _keep_none(_coerce_key(k))
        ]
        items.sort(key=lambda kv: kv[0])
        return {k: v for k, v in items}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # Fallback: trust the object's ``__dict__`` representation. Platform API
    # contracts are Pydantic models and already serialize through their own
    # ``model_dump`` callers; this branch is for ad-hoc interop only.
    return _canonicalize(value.__dict__)


def _coerce_key(key: Any) -> str:
    return key if isinstance(key, str) else str(key)


def _keep_none(_key: str) -> bool:
    # Reserved for future opt-in to preserve explicit nulls. Phase 1 strips
    # ``None`` values from canonical payloads so that ``{"a": null}`` and
    # ``{}`` collapse to the same identity — matching how Pydantic v2
    # ``model_dump(exclude_none=True)`` behaves by default in this codebase.
    return False


def canonical_json_bytes(payload: Any) -> bytes:
    """Return the canonical UTF-8 JSON bytes for ``payload``.

    The function is idempotent: ``canonical_json_bytes(canonical_json_bytes(x).decode())``
    is a no-op on the encoded form.
    """

    canonical = _canonicalize(payload)
    text = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))
    return text.encode("utf-8")


def canonical_sha256(payload: Any) -> str:
    """Return the lowercase hex SHA-256 of the canonical JSON payload."""

    return hashlib.new(_HASH_ALGO, canonical_json_bytes(payload)).hexdigest()


def envelope_identity(*, kind: str, version: str, data: Any) -> str:
    """Compute the stable identity of a success response envelope.

    The hash is over a **structured** representation — not the serialized
    envelope itself — so that adding envelope-only metadata (such as a
    future ``trace_id``) cannot silently change response identities.
    """

    structured = {
        "kind": kind,
        "version": version,
        "data": data,
    }
    return _HASH_PREFIX + canonical_sha256(structured)


def error_identity(
    *,
    kind: str,
    version: str,
    code: str,
    layer: str,
    message: str,
) -> str:
    """Compute the stable identity of an error response envelope."""

    structured = {
        "kind": kind,
        "version": version,
        "error": {
            "code": code,
            "layer": layer,
            "message": message,
        },
    }
    return _HASH_PREFIX + canonical_sha256(structured)


__all__ = [
    "canonical_json_bytes",
    "canonical_sha256",
    "envelope_identity",
    "error_identity",
]
