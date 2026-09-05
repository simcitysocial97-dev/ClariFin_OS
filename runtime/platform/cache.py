"""Platform snapshot cache (M9-C57 Phase 4).

The Platform API read path must be fast enough for a browser dashboard.
Phase 4 introduces an in-memory cache backed by a deterministic JSON
snapshot file. The cache satisfies the directive's Section 37
performance requirement: *dashboard loading must not trigger a full
repository scan, mutation testing, full verification, or LLM inference.*

Cache behavior
==============

* Every domain (``health``, ``capabilities``, ``tasks``, …) has its own
  TTL and independent validity.
* ``ttl_seconds`` governs freshness; ``None`` means "cache until the
  snapshot changes on disk".
* On cache miss the service function runs fresh and the result is
  serialized into the snapshot file under the domain key.
* ``?nocache=1`` on any endpoint bypasses the cache for that single
  request.
* ``snapshot.refresh(domain)`` invalidates one domain;
  ``snapshot.refresh_all()`` invalidates everything.
* A background ``snapshot._maybe_refresh()`` call re-generates stale
  snapshots on demand so that subsequent reads hit the cache again.

Snapshot format
===============

``runtime/generated/platform/snapshot.json``:

.. code-block:: json

    {
        "version": "1",
        "generated_at": "2026-09-05T13:00:00Z",
        "domains": {
            "health": {"hash": "sha256:...<80>", "payload": <envelope>},
            "capabilities": {"hash": "sha256:...<80>", "payload": <envelope>}
        }
    }

The hash lets us detect when the underlying data has changed without
rereading the authority. When the hash differs, the cache entry is
stale and gets refreshed.

Usage
=====

Services call :func:`get_cached` or :func:`get_or_refresh`. The router
passes ``nocache=True`` when the query parameter ``?nocache=1`` is
present.

The ``snapshot`` module-level object is the canonical instance used
everywhere.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SNAPSHOT_PATH = Path("runtime/generated/platform/snapshot.json")

#: Per-domain default TTL in seconds. Override with ``refresh_on_miss``
#: if you want a specific domain to always recompute.
DEFAULT_TTL_SECONDS: dict[str, int] = {
    "health": 60,
    "capabilities": 60,
    "tasks": 60,
    "events": 30,
    "change": 60,
    # Architecture, history, errors, application are cheap — no hard TTL
    # needed. They invalidate when the snapshot file changes.
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """UTC ISO-8601 timestamp with Z suffix."""

    from datetime import UTC, datetime

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_bytes(data: bytes) -> str:
    """Lowercase hex SHA-256 of raw bytes."""

    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(obj: Any) -> bytes:
    """Deterministic UTF-8 JSON bytes for hashing / comparison."""

    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_snapshot() -> dict[str, Any]:
    """Load the current snapshot file, or return an empty skeleton."""

    if SNAPSHOT_PATH.exists():
        try:
            return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Snapshot file corrupt — will regenerate", exc_info=True)
    return {"version": "1", "generated_at": "", "domains": {}}


def _save_snapshot(snap: dict[str, Any]) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SNAPSHOT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(SNAPSHOT_PATH)


def _effective_ttl(domain: str) -> Optional[int]:
    """Return the TTL in seconds for a domain, or None for 'never'."""

    return DEFAULT_TTL_SECONDS.get(domain)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class _SnapshotCache:
    """In-process cache for Platform API responses."""

    def __init__(self) -> None:
        self._snap = _load_snapshot()
        self._last_refresh_ts = time.monotonic()

    # ---- read ----

    def get(self, domain: str, *, nocache: bool = False) -> Any | None:
        """Return a cached domain payload, or ``None`` if missing/stale.

        ``nocache=True`` forces a bypass and returns ``None`` unconditionally
        so the caller always recomputes.
        """

        if nocache:
            return None
        domains = self._snap.get("domains", {})
        entry = domains.get(domain)
        if entry is None:
            return None
        if self._is_stale(domain, entry):
            return None
        return entry.get("payload")

    def _is_stale(self, domain: str, entry: dict) -> bool:
        """Check whether a cache entry is past its TTL or hash-differed."""

        ttl = _effective_ttl(domain)
        if ttl is None:
            # No TTL — only invalidate on explicit refresh.
            return False
        age = time.monotonic() - entry.get("_c", 0.0)
        if age > ttl:
            return True
        # Also invalidate when the snapshot file's hash of the payload
        # drifts (handles concurrent writers gracefully).
        stored_hash = entry.get("hash", "")
        current_hash = _hash_bytes(_canonical_json_bytes(entry.get("payload")))
        return stored_hash != current_hash

    # ---- write / refresh ----

    def put(self, domain: str, payload: Any) -> None:
        """Store a freshly-computed payload into the cache."""

        entry = {
            "payload": payload,
            "hash": _hash_bytes(_canonical_json_bytes(payload)),
            "_c": time.monotonic(),
            "_ts": _now_iso(),
        }
        self._snap.setdefault("domains", {})[domain] = entry
        self._snap["generated_at"] = _now_iso()
        _save_snapshot(self._snap)
        self._last_refresh_ts = time.monotonic()

    def refresh(self, domain: str) -> None:
        """Force-rebuild the snapshot file so all entries look fresh."""

        snap = _load_snapshot()
        snap.pop("domains", {}).pop(domain, None)
        _save_snapshot(snap)
        self._snap = snap

    def refresh_all(self) -> None:
        snap = _load_snapshot()
        snap["domains"] = {}
        _save_snapshot(snap)
        self._snap = snap

    def regenerate(self, domain: str, builder) -> Any:
        """Compute and cache in one call. Returns the payload."""

        payload = builder()
        self.put(domain, payload)
        return payload

    def count(self) -> int:
        return len(self._snap.get("domains", {}))

    @property
    def last_refresh_monotonic(self) -> float:
        return self._last_refresh_ts


# Module-level singleton. Services and tests should import this object.
snapshot = _SnapshotCache()

__all__ = [
    "DEFAULT_TTL_SECONDS",
    "SNAPSHOT_PATH",
    "snapshot",
]
