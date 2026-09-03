# runtime/foundation/verification/mutation_execution/cache.py
#
# M9-C44.12 — ClariFin_OS Mutation Evidence Cache.
#
# Canonical cache keyed by (canonical_mutant_id, configuration_fingerprint,
# source_hash).  Stale entries are INVALIDATED rather than silently reused.
#
# Never depends on mutmut's .mutmut-cache as the authoritative cache.
# The mutmut cache may be used as a discovery hint but never as the result store.

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from runtime.foundation.verification.mutation_execution.config_fingerprint import (
    build_full_fingerprint,
)
from runtime.foundation.verification.mutation_execution.domain_model import (
    MutationCandidate,
    MutationExecution,
    MutationResultState,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CACHE_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c44" / "cache"


@dataclass
class CacheEntry:
    canonical_mutant_id: str
    source_file: str
    source_hash: str
    configuration_fingerprint: str
    result_state: str
    execution: dict[str, Any] | None = None
    discovered_at: str = ""
    last_verified_at: str = ""
    verified: bool = False
    invalidation_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CacheEntry:
        return cls(
            canonical_mutant_id=d["canonical_mutant_id"],
            source_file=d["source_file"],
            source_hash=d["source_hash"],
            configuration_fingerprint=d["configuration_fingerprint"],
            result_state=d["result_state"],
            execution=d.get("execution"),
            discovered_at=d.get("discovered_at", ""),
            last_verified_at=d.get("last_verified_at", ""),
            verified=bool(d.get("verified", False)),
            invalidation_reason=d.get("invalidation_reason"),
        )


class MutationCache:
    """Repository-owned mutation evidence cache.

    Entries are keyed by canonical_mutant_id within a configuration fingerprint.
    An entry is VALID only if:
      1. configuration_fingerprint matches current run
      2. source_hash matches current source
      3. entry is not marked invalid
    """

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self._index_path = self.cache_dir / "index.json"
        self._entries: dict[str, CacheEntry] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if self._index_path.exists():
            try:
                data = json.loads(self._index_path.read_text())
                self._entries = {
                    k: CacheEntry.from_dict(v)
                    for k, v in data.items()
                }
            except Exception:
                self._entries = {}
        self._loaded = True

    def _persist(self) -> None:
        self._index_path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._entries.items()}, indent=2) + "\n"
        )

    def get(self, mutant_id: str, config_fp: str, source_hash: str) -> CacheEntry | None:
        """Lookup a cached result. Returns None if miss or invalidated."""
        self._ensure_loaded()
        entry = self._entries.get(mutant_id)
        if entry is None:
            return None
        if entry.invalidation_reason is not None:
            return None
        if entry.configuration_fingerprint != config_fp:
            return None
        if entry.source_hash != source_hash:
            return None
        return entry

    def put(
        self,
        candidate: MutationCandidate,
        config_fp: str,
        result_state: MutationResultState,
        execution: MutationExecution | None = None,
        verified: bool = False,
    ) -> None:
        """Store a result in the cache."""
        self._ensure_loaded()
        entry = CacheEntry(
            canonical_mutant_id=candidate.canonical_mutant_id,
            source_file=candidate.source_file,
            source_hash=candidate.source_hash,
            configuration_fingerprint=config_fp,
            result_state=result_state.value,
            discovered_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            last_verified_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            verified=verified,
        )
        if execution:
            entry.execution = execution.to_dict()
        self._entries[candidate.canonical_mutant_id] = entry
        self._persist()

    def invalidate(
        self,
        mutant_id: str,
        reason: str,
    ) -> None:
        """Mark a cache entry as invalidated with explicit reason."""
        self._ensure_loaded()
        entry = self._entries.get(mutant_id)
        if entry is None:
            return
        entry.invalidation_reason = reason
        entry.last_verified_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._persist()

    def invalidate_all(self, reason: str) -> int:
        """Invalidate all entries with a reason. Returns count invalidated."""
        self._ensure_loaded()
        count = 0
        for entry in self._entries.values():
            if entry.invalidation_reason is None:
                entry.invalidation_reason = reason
                count += 1
        if count > 0:
            self._persist()
        return count

    def invalidate_by_source(self, source_file: str, reason: str) -> int:
        """Invalidate entries for a specific source file."""
        self._ensure_loaded()
        count = 0
        for entry in self._entries.values():
            if entry.source_file == source_file and entry.invalidation_reason is None:
                entry.invalidation_reason = reason
                count += 1
        if count > 0:
            self._persist()
        return count

    def clear(self) -> None:
        """Clear the entire cache."""
        self._entries.clear()
        if self._index_path.exists():
            self._index_path.unlink()

    def stats(self) -> dict[str, Any]:
        self._ensure_loaded()
        total = len(self._entries)
        valid = sum(1 for e in self._entries.values() if e.invalidation_reason is None)
        invalid = total - valid
        verified = sum(1 for e in self._entries.values() if e.verified)
        return {
            "total_entries": total,
            "valid": valid,
            "invalidated": invalid,
            "verified": verified,
            "cache_dir": str(self.cache_dir.relative_to(REPO_ROOT)),
        }

    def get_or_skip(
        self,
        candidate: MutationCandidate,
        config_fp: str,
        result_state: MutationResultState,
        execution: MutationExecution | None = None,
        verified: bool = False,
    ) -> tuple[bool, CacheEntry | None]:
        """Get from cache, or store and return (was_cached, entry)."""
        self._ensure_loaded()
        existing = self.get(candidate.canonical_mutant_id, config_fp, candidate.source_hash)
        if existing is not None:
            return True, existing
        self.put(candidate, config_fp, result_state, execution, verified)
        return False, self._entries.get(candidate.canonical_mutant_id)


def build_cache_key(candidate: MutationCandidate, config_fp: str) -> str:
    """Derive the cache lookup key for a candidate."""
    return candidate.canonical_mutant_id


def build_fingerprint_for_run(
    *,
    backend: str,
    backend_version: str,
    source_paths: list[str],
    test_selection: list[str],
    timeout_seconds: int,
    worker_count: int,
) -> dict[str, str]:
    return build_full_fingerprint(
        backend=backend,
        backend_version=backend_version,
        source_paths=source_paths,
        test_selection=test_selection,
        timeout_seconds=timeout_seconds,
        worker_count=worker_count,
    )


__all__ = [
    "MutationCache",
    "CacheEntry",
    "build_cache_key",
    "build_fingerprint_for_run",
]
