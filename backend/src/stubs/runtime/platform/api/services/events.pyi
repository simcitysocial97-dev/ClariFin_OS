from __future__ import annotations

from typing import Any

__all__ = [
    "build_events_list",
    "build_events_stream_event",
]

def build_events_list(*, limit: int = 100) -> dict[str, Any]: ...
def build_events_stream_event(event: Any) -> dict[str, Any]: ...
