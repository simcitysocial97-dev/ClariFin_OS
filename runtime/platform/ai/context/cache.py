"""Context Pack Cache (Phase 14).

Content-addressed cache for context packs. Same inputs produce same id,
enabling reuse across runs. TTL-based invalidation by source fingerprint.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["ContextPackCache", "CONTEXT_PACK_CACHE_INSTANCE"]


class ContextPackCache:
    """In-memory cache with disk persistence for context packs."""

    def __init__(self, base_dir: str | Path = "runtime/generated/ai-context-packs") -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, dict[str, Any]] = {}

    def get(self, pack_id: str) -> dict[str, Any] | None:
        """Get a cached context pack by ID."""
        if pack_id in self._memory:
            return self._memory[pack_id]

        path = self._pack_path(pack_id)
        if path.exists():
            try:
                pack = json.loads(path.read_text())
                self._memory[pack_id] = pack
                return pack
            except Exception as exc:
                logger.warning("Failed to load context pack %s: %s", pack_id, exc)

        return None

    def put(self, pack: dict[str, Any]) -> None:
        """Cache a context pack by its id."""
        pack_id = pack.get("pack_id") or pack.get("id")
        if not pack_id:
            return

        self._memory[pack_id] = pack
        path = self._pack_path(pack_id)
        try:
            path.write_text(json.dumps(pack, indent=2, default=str))
        except Exception as exc:
            logger.warning("Failed to persist context pack %s: %s", pack_id, exc)

    def invalidate(self, pack_id: str) -> bool:
        """Remove a pack from cache."""
        if pack_id in self._memory:
            del self._memory[pack_id]

        path = self._pack_path(pack_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> None:
        """Clear all cached packs."""
        self._memory.clear()
        for path in self._base.glob("*.json"):
            try:
                path.unlink()
            except Exception:
                pass

    def count(self) -> int:
        return len(self._memory)

    def _pack_path(self, pack_id: str) -> Path:
        return self._base / f"{pack_id}.json"


# Singleton instance
CONTEXT_PACK_CACHE_INSTANCE = ContextPackCache()
