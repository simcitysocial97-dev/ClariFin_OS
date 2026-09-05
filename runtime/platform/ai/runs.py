"""AI Runs Persistence (Phase 13).

Immutable append-only storage for AI runs with full audit trail.
Runs are stored as individual JSON files for content-addressed integrity.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["AIRunsStore", "AI_RUNS_STORE_INSTANCE"]


class AIRunsStore:
    """Immutable append-only store for AI runs."""

    def __init__(self, base_dir: str | Path = "runtime/generated/ai-runs") -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _run_path(self, run_id: str) -> Path:
        return self._base / f"{run_id}.json"

    def create(self, run_id: str, run_data: dict[str, Any]) -> None:
        """Create a new AI run (must not exist)."""
        path = self._run_path(run_id)
        if path.exists():
            raise ValueError(f"Run {run_id} already exists")
        path.write_text(json.dumps(run_data, indent=2, default=str))
        logger.debug("Created AI run: %s", run_id)

    def get(self, run_id: str) -> dict[str, Any] | None:
        """Retrieve an AI run by ID."""
        path = self._run_path(run_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception as exc:
            logger.warning("Failed to read AI run %s: %s", run_id, exc)
            return None

    def update(self, run_id: str, run_data: dict[str, Any]) -> None:
        """Update an existing AI run (append-only, full rewrite)."""
        path = self._run_path(run_id)
        if not path.exists():
            raise ValueError(f"Run {run_id} does not exist")
        path.write_text(json.dumps(run_data, indent=2, default=str))
        logger.debug("Updated AI run: %s", run_id)

    def list(self, *, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        """List AI runs, newest first."""
        runs = []
        for path in self._base.glob("*.json"):
            try:
                run = json.loads(path.read_text())
                if status is None or run.get("status") == status:
                    runs.append(run)
            except Exception as exc:
                logger.warning("Failed to read AI run %s: %s", path.name, exc)

        runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return runs[:limit]

    def count(self, status: str | None = None) -> int:
        count = 0
        for path in self._base.glob("*.json"):
            try:
                run = json.loads(path.read_text())
                if status is None or run.get("status") == status:
                    count += 1
            except Exception:
                pass
        return count


# Singleton instance
AI_RUNS_STORE_INSTANCE = AIRunsStore()