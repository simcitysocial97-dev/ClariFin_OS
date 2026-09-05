from __future__ import annotations

from typing import Any

__all__ = [
    "build_history_runs",
    "build_history_run",
    "build_history_baselines",
]

HISTORY_ARTIFACT_CANDIDATES: tuple[str, ...]

def build_history_runs(*, page: int = 1, page_size: int = 20) -> dict[str, Any]: ...
def build_history_run(run_id: str) -> dict[str, Any] | None: ...
def build_history_baselines() -> dict[str, Any]: ...
