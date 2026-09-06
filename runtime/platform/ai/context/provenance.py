"""Provenance tracking (Phase 14).

Every component in a Context Pack must trace back to a known source.
This module provides content-addressed provenance entries that track
the origin, path, and lineage of every byte in a context pack.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ProvenanceKind(str, Enum):
    KNOWLEDGE = "knowledge"
    HISTORY = "history"
    EVIDENCE = "evidence"
    EVENT = "event"
    ERROR = "error"
    ARCHITECTURE = "architecture"
    POLICY = "policy"
    MEMORY = "memory"
    REPOSITORY = "repository"
    RUNTIME = "runtime"


@dataclass(frozen=True)
class ProvenanceEntry:
    """A single provenance entry tracing one byte/component back to its source."""

    kind: ProvenanceKind
    id: str
    path: Optional[str] = None
    symbol: Optional[str] = None
    line_range: Optional[tuple[int, int]] = None
    fingerprint: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    @property
    def source_ref(self) -> str:
        """Content-addressed reference for this provenance entry."""
        parts = [self.kind.value, self.id]
        if self.path:
            parts.append(self.path)
        if self.symbol:
            parts.append(self.symbol)
        return ":".join(parts)

    def fingerprint_bytes(self) -> bytes:
        """Canonical bytes for SHA-256 computation."""
        canonical = {
            "kind": self.kind.value,
            "id": self.id,
            "path": self.path or "",
            "symbol": self.symbol or "",
            "line_start": self.line_range[0] if self.line_range else 0,
            "line_end": self.line_range[1] if self.line_range else 0,
            "fingerprint": self.fingerprint or "",
        }
        return hashlib.sha256(
            str(sorted(canonical.items())).encode()
        ).digest()


class ProvenanceTracker:
    """Tracks provenance for context pack components."""

    def __init__(self) -> None:
        self._entries: list[ProvenanceEntry] = []

    def add(self, entry: ProvenanceEntry) -> str:
        """Add a provenance entry and return its reference ID."""
        self._entries.append(entry)
        return entry.source_ref

    def get(self, ref: str) -> ProvenanceEntry | None:
        """Look up a provenance entry by reference."""
        for e in self._entries:
            if e.source_ref == ref:
                return e
        return None

    def list_entries(self) -> list[ProvenanceEntry]:
        return list(self._entries)

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()


def build_provenance(
    kind: str,
    id_: str,
    *,
    path: str | None = None,
    symbol: str | None = None,
    line_range: tuple[int, int] | None = None,
    fingerprint: str | None = None,
    **metadata: Any,
) -> ProvenanceEntry:
    """Convenience constructor for provenance entries."""
    return ProvenanceEntry(
        kind=ProvenanceKind(kind),
        id=id_,
        path=path,
        symbol=symbol,
        line_range=line_range,
        fingerprint=fingerprint,
        metadata=metadata,
    )


# Singleton instance
PROVENANCE_TRACKER_INSTANCE = ProvenanceTracker()
