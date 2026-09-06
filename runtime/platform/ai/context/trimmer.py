"""Trimmer (Phase 14).

Token budget enforcement for context packs. Never silently truncates —
produces status="incomplete" with omitted components when budget is exceeded.
"""

from __future__ import annotations

from typing import Any

from runtime.platform.ai.context.ranker import RankedComponent, Ranker


class TrimmerResult:
    """Result of token budget trimming."""

    def __init__(
        self,
        kept_components: list[RankedComponent],
        omitted_components: list[RankedComponent],
        total_tokens: int,
        budget: int,
        status: str,
    ):
        self.kept_components = kept_components
        self.omitted_components = omitted_components
        self.total_tokens = total_tokens
        self.budget = budget
        self.status = status  # "complete" or "incomplete"

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tokens": self.total_tokens,
            "budget": self.budget,
            "status": self.status,
            "kept_count": len(self.kept_components),
            "omitted_count": len(self.omitted_components),
            "omitted_types": [o.component_type for o in self.omitted_components],
        }


class Trimmer:
    """Enforces token budgets on context packs."""

    def __init__(self, ranker: Ranker | None = None) -> None:
        self.ranker = ranker or Ranker()

    def trim(
        self,
        components: list[RankedComponent],
        budget: int,
    ) -> TrimmerResult:
        """Apply token budget. Never silently truncates.

        Returns result with status="complete" if all fit, or
        status="incomplete" with omitted components listed.
        """
        if budget <= 0:
            return TrimmerResult([], components, 0, budget, "incomplete")

        kept, omitted = self.ranker.select_top(components, budget)
        total = sum(c.token_estimate for c in kept)
        status = "complete" if not omitted else "incomplete"

        return TrimmerResult(kept, omitted, total, budget, status)

    def check_budget(self, components: list[RankedComponent], budget: int) -> str:
        """Quick check whether components fit within budget."""
        total = sum(c.token_estimate for c in components)
        return "complete" if total <= budget else "incomplete"


# Singleton instance
TRIMMER_INSTANCE = Trimmer()
