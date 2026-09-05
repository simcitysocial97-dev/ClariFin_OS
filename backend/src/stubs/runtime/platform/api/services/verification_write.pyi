from __future__ import annotations

from typing import Any

__all__ = [
    "build_run_result",
    "build_recent_runs",
]

def build_run_result(
    *,
    capability_id: str | None = None,
    group: str | None = None,
    affected: bool = False,
    full: bool = False,
) -> dict[str, Any]: ...
def build_recent_runs(*, limit: int = 20) -> dict[str, Any]: ...
