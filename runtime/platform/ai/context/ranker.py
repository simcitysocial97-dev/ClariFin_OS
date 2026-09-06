"""Ranker (Phase 14).

Priority scoring for context pack components. Higher scores indicate
higher relevance to the diagnostic intent.
"""

from __future__ import annotations

from typing import Any


# Priority weights by source type
PRIORITY_WEIGHTS: dict[str, int] = {
    "failing_evidence": 100,
    "recent_change": 80,
    "capability": 70,
    "recent_run": 60,
    "knowledge": 50,
    "adjacent_capability": 30,
    "architecture": 20,
    "documentation": 10,
    "repository_file": 10,
    "historical_delta": 90,
}


class RankedComponent:
    """A context pack component with priority score."""

    def __init__(
        self,
        component_type: str,
        source_kind: str,
        data: dict[str, Any],
        provenance_ref: str,
        token_estimate: int,
        relevance_score: float | None = None,
    ):
        self.component_type = component_type
        self.source_kind = source_kind
        self.data = data
        self.provenance_ref = provenance_ref
        self.token_estimate = token_estimate
        self.relevance_score = relevance_score or PRIORITY_WEIGHTS.get(source_kind, 50)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.component_type,
            "source_kind": self.source_kind,
            "data": self.data,
            "provenance_ref": self.provenance_ref,
            "token_estimate": self.token_estimate,
            "relevance_score": self.relevance_score,
        }


class Ranker:
    """Sorts context components by priority for ordered assembly."""

    def rank(
        self,
        components: list[RankedComponent],
    ) -> list[RankedComponent]:
        """Sort components by relevance_score descending."""
        return sorted(components, key=lambda c: c.relevance_score, reverse=True)

    def select_top(
        self,
        components: list[RankedComponent],
        budget: int,
        *,
        keep_minimum: bool = True,
    ) -> tuple[list[RankedComponent], list[RankedComponent]]:
        """Select components within budget. Returns (kept, omitted).

        If budget is exceeded, kept components are those with highest
        relevance scores. Omitted components retain their scores for
        reporting.
        """
        ranked = self.rank(components)
        kept: list[RankedComponent] = []
        omitted: list[RankedComponent] = []
        used_tokens = 0

        for comp in ranked:
            if used_tokens + comp.token_estimate <= budget:
                kept.append(comp)
                used_tokens += comp.token_estimate
            else:
                omitted.append(comp)

        return kept, omitted


# Singleton instance
RANKER_INSTANCE = Ranker()
