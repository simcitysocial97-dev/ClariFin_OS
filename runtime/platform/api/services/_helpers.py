"""Shared helpers for Phase 2 service adapters.

The Platform API services are deliberately thin. They:

1. Read from a real authority module (C50, observability, knowledge, …).
2. Project that authority's state into a typed Phase 1 contract payload.
3. Wrap the payload in the canonical envelope.

This module holds the *projection* utilities that every service reuses:

* :func:`now_iso` — current UTC ISO-8601 timestamp with ``Z`` suffix,
  validated against the Phase 1 ``Timestamp`` contract primitive.
* :func:`envelope` — convenience wrapper around
  :func:`runtime.platform.api.envelope.success_envelope` that fixes the
  ``kind`` and ``version`` for a given contract module.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from runtime.platform.api.contracts._primitives import Timestamp
from runtime.platform.api.envelope import success_envelope

__all__ = [
    "envelope",
    "now_iso",
]


def now_iso() -> Timestamp:
    """Return current UTC time as an ISO-8601 ``Z`` string.

    Validates against the Phase 1 ``Timestamp`` contract primitive so
    that any envelope that embeds this value passes contract validation.
    """

    return Timestamp(datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))


def envelope(*, kind: str, data: Any) -> dict[str, Any]:
    """Wrap ``data`` in the canonical success envelope.

    Identical to :func:`runtime.platform.api.envelope.success_envelope`
    but exposed under this module so that service modules have a single,
    stable import path.
    """

    return success_envelope(kind=kind, data=data)
