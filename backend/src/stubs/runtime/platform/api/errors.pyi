from __future__ import annotations

from enum import Enum

class PlatformErrorCode(str, Enum):
    MALFORMED_REQUEST = "MALFORMED_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    POLICY_DENIED = "POLICY_DENIED"
    INTERNAL = "INTERNAL"
    UNAVAILABLE = "UNAVAILABLE"

class PlatformError:
    code: PlatformErrorCode
    layer: str
    message: str
    capability_id: str | None
    evidence_id: str | None
    def __init__(
        self,
        code: PlatformErrorCode | str,
        layer: str,
        message: str,
        capability_id: str | None = ...,
        evidence_id: str | None = ...,
    ) -> None: ...

__all__ = ["PlatformError", "PlatformErrorCode"]
