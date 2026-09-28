from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

SNAPSHOT_PATH: Path
DEFAULT_TTL_SECONDS: dict[str, int]

__all__ = [
    "DEFAULT_TTL_SECONDS",
    "SNAPSHOT_PATH",
    "snapshot",
]

class _SnapshotCache:
    def __init__(self) -> None: ...
    def get(self, domain: str, *, nocache: bool = False) -> Any | None: ...
    def put(self, domain: str, payload: Any) -> None: ...
    def refresh(self, domain: str) -> None: ...
    def refresh_all(self) -> None: ...
    def regenerate(self, domain: str, builder: Callable[[], Any]) -> Any: ...
    def count(self) -> int: ...
    @property
    def last_refresh_monotonic(self) -> float: ...

snapshot: _SnapshotCache
