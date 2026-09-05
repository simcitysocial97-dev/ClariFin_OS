from __future__ import annotations

from typing import Any

__all__ = ["build_cancel_result"]

def build_cancel_result(*, task_id: str) -> dict[str, Any] | None: ...
