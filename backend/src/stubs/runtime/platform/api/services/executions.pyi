from __future__ import annotations

from typing import Any

__all__ = [
    "build_execution_detail",
    "build_execution_stream_event",
]

def build_execution_detail(execution_id: str) -> dict[str, Any] | None: ...
def build_execution_stream_event(execution_id: str, event: Any) -> dict[str, Any]: ...
