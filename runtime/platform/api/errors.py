"""Platform API error taxonomy (M9-C57 Phase 1).

This module owns the **Platform-level** error taxonomy. It is the canonical
error contract for the Platform API. It deliberately does **not** replace
``backend.src.errors``: request-level errors raised by application routers
remain owned by the backend. Platform-level errors are the errors emitted
when a client calls the Platform API and the Platform API itself fails.

The taxonomy covers three classes of failure:

* ``MALFORMED_REQUEST`` — the client sent something the contracts cannot
  parse. The platform cannot meaningfully respond.
* ``NOT_FOUND`` — the requested resource does not exist (capability,
  task, execution, evidence).
* ``AUTHORIZATION_DENIED`` — the request was rejected by an authority
  (see ``authorization_boundary.py``).
* ``INTERNAL`` — a non-recoverable internal failure. The error envelope
  carries ``layer`` so that the GUI and AI can surface the responsible
  subsystem.
* ``UNAVAILABLE`` — a downstream authority is missing or disabled
  (e.g. AI provider unavailable — Phase 15+ territory, but reserved now).

The error envelope (see :mod:`runtime.platform.api.envelope`) carries:

* ``kind`` = ``platform.error``
* ``error.code``
* ``error.layer``
* ``error.message``
* optional ``error.evidence_id`` (Phase 1 reserves the field, but the
  authoritative evidence_id is produced only after C50 evidence runs).
* optional ``error.capability_id`` (the C50 capability that triggered
  the error, if any).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PlatformErrorCode(str, Enum):
    """Canonical Platform API error codes.

    These codes are the public contract for clients. New codes may be
    added in future phases, but existing codes MUST NOT change meaning.
    """

    MALFORMED_REQUEST = "MALFORMED_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    INTERNAL = "INTERNAL"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class PlatformError:
    """A structured Platform-level error.

    ``layer`` identifies the subsystem that produced the error
    (``platform.tasks``, ``platform.verification``, ``platform.ai``, …).
    ``code`` is one of :class:`PlatformErrorCode`.
    ``message`` is a human-readable explanation and MUST NOT contain
    secrets, credentials, or stack traces — those belong in server-side
    logs only.
    """

    code: PlatformErrorCode
    layer: str
    message: str
    capability_id: Optional[str] = None
    evidence_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.layer or not isinstance(self.layer, str):
            raise ValueError("PlatformError.layer must be a non-empty string")
        if not self.message or not isinstance(self.message, str):
            raise ValueError("PlatformError.message must be a non-empty string")
        if not isinstance(self.code, PlatformErrorCode):
            raise ValueError(
                f"PlatformError.code must be a PlatformErrorCode, got {self.code!r}"
            )


__all__ = [
    "PlatformError",
    "PlatformErrorCode",
]
