from __future__ import annotations

from typing import Any

__all__ = [
    "build_task_list",
    "build_task_detail",
]

def build_task_list() -> dict[str, Any]: ...
def build_task_detail(task_id: str) -> dict[str, Any] | None: ...
