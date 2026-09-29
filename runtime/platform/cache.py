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
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SNAPSHOT_PATH = Path("runtime/generated/platform/snapshot.json")

#: Per-domain default TTL in seconds. Override with ``refresh_on_miss``
#: if you want a specific domain to always recompute.
#: Minimum ratio between a domain's TTL and its measured build cost. A TTL
#: shorter than a few builds means the cache spends a large fraction of every
#: window recomputing, and any request arriving just after an expiry pays the
#: full build. `health` is the motivating case: its snapshot runs the full
#: framework integrity scan (drift detection + artifact freshness + self-tests)
#: and measures ~13 s, so the previous 60 s TTL put the cache in a ~22 % rebuild
#: duty cycle and made the platform console's own data-readiness wait blow past
#: its budget on a large fraction of page loads.
_BUILD_COST_MULTIPLE = 20

#: Upper bound on a TTL, so a very expensive build cannot pin a stale value for
#: hours.
_MAX_TTL_SECONDS = 900

DEFAULT_TTL_SECONDS: dict[str, int] = {
    # health is the expensive one: ~13 s to build. 300 s amortises that to a
    # ~4 % rebuild duty cycle, and a consumer arriving during a rebuild waits at
    # most one build rather than a queue of them.
    "health": 300,
    "capabilities": 60,
    "tasks": 60,
    "events": 30,
    "change": 60,
    # errors_current costs ~6 s on a cold process (it scans the current error
    # state), so it needs a real TTL. The widened builder is only ever reached
    # through get_or_build, so the first caller pays and the rest are served.
    "errors_current": 300,
    # Architecture, history, errors, application are cheap — no hard TTL
    # needed. They invalidate when the snapshot file changes.
}

#: Measured build cost per domain, in seconds. Populated on first write so the
#: TTL can be sized from evidence rather than a guess.
_BUILD_COST_SECONDS: dict[str, float] = {}

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


def _effective_ttl(domain: str) -> int | None:
    """Return the TTL in seconds for a domain, or None for 'never'.

    An explicit ``SNAPSHOT_TTL_<DOMAIN>`` override wins. Otherwise the TTL is
    the configured default, widened so it stays at least
    ``_BUILD_COST_MULTIPLE`` times the domain's measured build cost (capped at
    ``_MAX_TTL_SECONDS``). Sizing the TTL from the measured cost is what keeps
    the cache serving: a TTL shorter than the work it is caching guarantees a
    large rebuild duty cycle.
    """

    override = os.environ.get(f"SNAPSHOT_TTL_{domain.upper()}")
    if override:
        try:
            value = int(override)
        except ValueError:
            logger.warning("Ignoring non-integer SNAPSHOT_TTL_%s=%r", domain, override)
        else:
            if value <= 0:
                return None
            return value

    base = DEFAULT_TTL_SECONDS.get(domain)
    if base is None:
        return None

    cost = _BUILD_COST_SECONDS.get(domain)
    if cost is None:
        return base
    return min(_MAX_TTL_SECONDS, max(base, int(cost * _BUILD_COST_MULTIPLE)))


def _record_build_cost(domain: str, seconds: float) -> None:
    """Record how long a domain's build took, so its TTL can be sized from it."""

    if seconds > 0:
        _BUILD_COST_SECONDS[domain] = seconds


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class _SnapshotCache:
    """In-process cache for Platform API responses."""

    def __init__(self) -> None:
        self._snap = _load_snapshot()
        self._last_refresh_ts = time.monotonic()
        self._domain_locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _lock_for(self, domain: str) -> threading.Lock:
        """Return the per-domain refresh lock, creating it on first use."""

        with self._locks_guard:
            lock = self._domain_locks.get(domain)
            if lock is None:
                lock = threading.Lock()
                self._domain_locks[domain] = lock
            return lock

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
        created = entry.get("_c")
        if not isinstance(created, (int, float)) or created <= 0:
            return True
        age = time.time() - created
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
            "_c": time.time(),
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

    def get_or_build(self, domain: str, builder, *, nocache: bool = False) -> Any:
        """Return a cached payload, computing it at most once per refresh.

        A console page resolves several domains in parallel, so a cold or
        expired TTL produced a thundering herd: every in-flight request ran
        the same expensive builder, and ``health`` alone costs ~12 s of
        repository scanning. Concurrent callers now block on one computation
        and all receive its result, which is what the cache's documented
        performance contract requires.
        """

        cached = self.get(domain, nocache=nocache)
        if cached is not None:
            return cached

        with self._lock_for(domain):
            # Another thread may have refreshed while this one waited. An
            # explicit ``nocache`` request must still recompute, so the
            # in-lock re-check is skipped for that caller.
            if not nocache:
                cached = self.get(domain)
                if cached is not None:
                    return cached
            started = time.monotonic()
            payload = builder()
            # Record the cost so _effective_ttl can size this domain's TTL from
            # measurement rather than from a guess that can be too short.
            _record_build_cost(domain, time.monotonic() - started)
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
