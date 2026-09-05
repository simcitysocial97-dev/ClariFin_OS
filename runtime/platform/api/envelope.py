"""Platform API request/response envelopes (M9-C57 Phase 1).

Every Platform API response — success or failure — is wrapped in a
canonical envelope. The envelope has a fixed shape and is the only thing
clients need to parse.

Success envelope
================

.. code-block:: json

    {
        "kind": "platform.health_snapshot",
        "version": "1.0.0",
        "generated_at": "2026-09-05T03:59:00Z",
        "id": "sha256:<hex>",
        "data": { ... }
    }

Error envelope
==============

.. code-block:: json

    {
        "kind": "platform.error",
        "version": "1.0.0",
        "generated_at": "...",
        "id": "sha256:<hex>",
        "error": {
            "code": "TASK_NOT_FOUND",
            "layer": "platform.tasks",
            "message": "No task with id obl-xxx",
            "evidence_id": null,
            "capability_id": null
        }
    }

Invariants
==========

* ``kind`` is a dotted string: ``platform.<domain>_<noun>``. Clients can
  dispatch on ``kind`` without parsing the URL.
* ``version`` is the API major version (``"1.0.0"`` in Phase 1). Breaking
  changes require ``2.0.0`` and a new ``/platform/v2/*`` route mount.
* ``generated_at`` is an ISO-8601 UTC timestamp (``Z`` suffix).
* ``id`` is ``sha256:<hex>`` — see :mod:`runtime.platform.api.identity`.
* ``data`` is the domain payload. It MUST NOT be ``None``.

Error envelope invariants
=========================

* ``error.code`` is one of :class:`~runtime.platform.api.errors.PlatformErrorCode`.
* ``error.layer`` is a dotted subsystem name (``platform.tasks``, …).
* ``error.message`` is human-readable and contains no secrets.

The envelope is intentionally **not** a Pydantic model of its own: it is
constructed by the contract layer (see :mod:`runtime.platform.api.contracts`)
which holds the typed ``data`` model. The envelope exists as a thin
container so that Phase 2 service code can reuse it without having to
re-import every contract model.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Final

from runtime.platform.api.errors import PlatformError
from runtime.platform.api.identity import envelope_identity, error_identity

API_VERSION: Final[str] = "1.0.0"


def _utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 with ``Z`` suffix."""

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def success_envelope(*, kind: str, data: Any) -> dict[str, Any]:
    """Build a success envelope around ``data``.

    The ``id`` is computed from the structured payload (kind, version,
    data) — never from the wall-clock ``generated_at``, so that the
    envelope is reproducible for caching, snapshotting, and AI context
    assembly.
    """

    if data is None:
        raise ValueError("success_envelope requires non-None data")

    return {
        "kind": kind,
        "version": API_VERSION,
        "generated_at": _utc_now_iso(),
        "id": envelope_identity(kind=kind, version=API_VERSION, data=data),
        "data": data,
    }


def error_envelope(*, error: PlatformError) -> dict[str, Any]:
    """Build an error envelope around a :class:`PlatformError`."""

    return {
        "kind": "platform.error",
        "version": API_VERSION,
        "generated_at": _utc_now_iso(),
        "id": error_identity(
            kind="platform.error",
            version=API_VERSION,
            code=error.code.value,
            layer=error.layer,
            message=error.message,
        ),
        "error": {
            "code": error.code.value,
            "layer": error.layer,
            "message": error.message,
            "evidence_id": error.evidence_id,
            "capability_id": error.capability_id,
        },
    }


__all__ = [
    "API_VERSION",
    "error_envelope",
    "success_envelope",
]
