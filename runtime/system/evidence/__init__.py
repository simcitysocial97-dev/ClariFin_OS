"""Evidence Runtime — Structured evidence collection and aggregation."""

from __future__ import annotations

__version__ = "0.1.0"

from .aggregator import EvidenceAggregator, EvidenceSummary  # noqa: E402

__all__ = [
    "EvidenceAggregator",
    "EvidenceSummary",
]
