from __future__ import annotations

from typing import Any

__all__ = [
    "build_evidence_list",
    "build_evidence_detail",
    "build_evidence_compare",
]

def build_evidence_list() -> dict[str, Any]: ...
def build_evidence_detail(evidence_id: str) -> dict[str, Any] | None: ...
def build_evidence_by_execution(execution_id: str) -> dict[str, Any] | None: ...
def build_evidence_compare(left_id: str, right_id: str) -> dict[str, Any] | None: ...
