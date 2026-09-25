from __future__ import annotations

from typing import Protocol

class CapabilityCatalog(Protocol):
    entries: list[object]

def get_capability_catalog() -> CapabilityCatalog: ...
