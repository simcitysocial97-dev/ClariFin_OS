"""
Type stubs for the runtime.platform.api.envelope module.

The runtime is a separately installable Python package. The backend's
strict mypy boundary treats it as an external dependency: the canonical
dependency contract is declared in root pyproject.toml, and this stub
package mirrors the import surface used by the backend's platform router.

These stubs intentionally return `Any` from functions that return rich
Pydantic models — the runtime module is the source of truth, and the
backend treats its results as opaque envelopes.
"""
from __future__ import annotations

from typing import Any

def error_envelope(
    code: str | None = ...,
    layer: str | None = ...,
    message: str | None = ...,
    error: Any = ...,
    *,
    evidence_id: str | None = ...,
    capability_id: str | None = ...,
) -> dict[str, Any]: ...
def success_envelope(
    kind: str,
    data: Any,
    *,
    version: str = ...,
) -> dict[str, Any]: ...
