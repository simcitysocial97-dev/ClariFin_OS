"""
Type stubs for runtime.platform.api.services.errors.

Aggregates live C50 EvidenceIntegrityReport and obligation set into the
Phase 1 PlatformErrors* contracts.
"""
from __future__ import annotations

from typing import Any

def build_errors_current() -> dict[str, Any]: ...
def build_errors_recent(window: str = ...) -> dict[str, Any]: ...
def build_errors_recurring() -> dict[str, Any]: ...
def build_errors_frequency() -> dict[str, Any]: ...
def build_errors_detail(error_id: str) -> dict[str, Any]: ...

__all__ = [
    "build_errors_current",
    "build_errors_recent",
    "build_errors_recurring",
    "build_errors_frequency",
    "build_errors_detail",
]
