"""Property tests for Behaviour Engine using Hypothesis."""

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


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

        # Should return a list (may be empty)
        assert isinstance(nudges, list)


class TestCreditUtilizationProperties:
    """Property tests for credit utilization calculations."""

    @given(
        outstanding_paise=st.integers(min_value=0, max_value=100000000),
        credit_limit_paise=st.integers(min_value=100000, max_value=10000000),
    )
    @settings(max_examples=20)
    def test_utilization_bps_bounds(
        self,
        outstanding_paise: int,
        credit_limit_paise: int,
    ) -> None:
        """Utilization must be between 0 and 10000 basis points."""
        from src.engines.credit_card_engine.utilization import compute_utilization

        util = compute_utilization(outstanding_paise, credit_limit_paise)

        # Utilization is in basis points (0-10000)
        assert 0 <= util <= 10000, f"Utilization {util} out of bps bounds for {outstanding_paise}/{credit_limit_paise}"
