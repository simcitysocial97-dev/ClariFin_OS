from __future__ import annotations

from typing import Any

__all__ = [
    "build_verification_run_request",
    "build_verification_run_result",
    "build_verification_recommendation",
]

def build_verification_run_request(
    *,
    capability_id: str,
    group: str | None = None,
    authorization_token: str | None = None,
) -> dict[str, Any]: ...
def build_verification_run_result(
    *,
    capability_id: str,
    status_value: Any,
    task_id: str | None = None,
    execution_id: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    duration_ms: int | None = None,
    message: str,
) -> dict[str, Any]: ...
def build_verification_recommendation() -> dict[str, Any]: ...
