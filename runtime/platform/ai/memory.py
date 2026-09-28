"""AI Memory (Phase 13).

Operational and episodic memory for AI runs. Local-only, no external
storage. Provides session context and cross-run learning.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["AIMemory", "AI_MEMORY_INSTANCE"]


class AIMemory:
    """Local memory for AI runs - operational and episodic."""

    def __init__(self, base_dir: str | Path = "runtime/generated/ai-memory") -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)
        self._episodic_file = self._base / "episodic.json"
        self._operational_file = self._base / "operational.json"

        self._episodic = self._load_json(self._episodic_file, {"entries": []})
        self._operational = self._load_json(self._operational_file, {"facts": {}})

    def _load_json(self, path: Path, default: dict[str, Any]) -> dict[str, Any]:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception as exc:
                logger.warning("Failed to load %s: %s", path, exc)
        return default

    def _save_json(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, default=str))

    # Episodic memory (run-specific events)
    def add_episodic(
        self,
        *,
        run_id: str,
        event_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "id": f"ep-{len(self._episodic['entries']) + 1}",
            "run_id": run_id,
            "event_type": event_type,
            "content": content,
            "metadata": metadata or {},
        }
        self._episodic["entries"].append(entry)
        self._save_json(self._episodic_file, self._episodic)

    def get_episodic(
        self, run_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        entries = self._episodic["entries"]
        if run_id:
            entries = [e for e in entries if e["run_id"] == run_id]
        return entries[-limit:]

    # Operational memory (cross-run facts)
    def set_fact(self, key: str, value: Any, *, run_id: str | None = None) -> None:
        fact = {"value": value}
        if run_id:
            fact["run_id"] = run_id
        self._operational["facts"][key] = fact
        self._save_json(self._operational_file, self._operational)

    def get_fact(self, key: str) -> Any | None:
        fact = self._operational["facts"].get(key)
        return fact["value"] if fact else None

    def get_facts(self, *, prefix: str = "") -> dict[str, Any]:
        return {
            k: v["value"]
            for k, v in self._operational["facts"].items()
            if k.startswith(prefix)
        }

    def clear(self) -> None:
        self._episodic = {"entries": []}
        self._operational = {"facts": {}}
        self._save_json(self._episodic_file, self._episodic)
        self._save_json(self._operational_file, self._operational)


# Singleton instance
AI_MEMORY_INSTANCE = AIMemory()
