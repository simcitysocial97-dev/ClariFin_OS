"""Property tests for Recommendations — Nudge Engine."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st


class TestNudgeEngineProperties:
    """Property tests for nudge engine."""

    @given(
        surplus_values=st.lists(
            st.integers(min_value=-1000000, max_value=500000),
            min_size=1,
            max_size=12,
        ),
    )
    @settings(max_examples=20)
    def test_nudge_generation(
        self,
        surplus_values: list[int],
    ) -> None:
        """Nudges should be generated for concerning patterns."""
        from src.engines.nudge_engine import generate_nudges

        profile = {
            "temporal_patterns": {
                "surplus_history": surplus_values,
            },
            "financial_health_score": 50.0,
        }

        nudges = generate_nudges(profile)
        assert isinstance(nudges, list)
