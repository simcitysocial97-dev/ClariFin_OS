from __future__ import annotations

from typing import Any

__all__ = [
    "build_capability_list",
    "build_capability_detail",
    "build_capability_graph",
]

def build_capability_list() -> dict[str, Any]: ...
def build_capability_detail(capability_id: str) -> dict[str, Any] | None: ...
def build_capability_graph(capability_id: str) -> dict[str, Any] | None: ...
