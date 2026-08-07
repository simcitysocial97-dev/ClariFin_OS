"""Hypothesis profiles and settings fixture for property-based testing.

Profiles:
- dev: 50 examples (default local development)
- ci: 500 examples (continuous integration)
- fast: 20 examples (rapid iteration)
- normal: 150 examples (extended CI)
- deep: 1000 examples (nightly)

The active profile is selected via the HYPOTHESIS_PROFILE environment variable
(default: dev).
"""

from __future__ import annotations

import os

import pytest
from hypothesis import Phase, settings

# Register built-in profiles at module load time so they are active
# before any test collection or execution occurs.
settings.register_profile("ci", max_examples=500, deadline=None)
settings.register_profile("dev", max_examples=50, deadline=1000)
settings.register_profile(
    "fast", max_examples=20, deadline=5000, phases=[Phase.generate]
)
settings.register_profile(
    "normal",
    max_examples=150,
    deadline=10000,
    phases=[Phase.generate, Phase.shrink],
)
settings.register_profile(
    "deep",
    max_examples=1000,
    deadline=30000,
    phases=[Phase.generate, Phase.shrink, Phase.explain],
)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


@pytest.fixture
def hypothesis_settings() -> settings:
    """Provide the currently active Hypothesis settings for tests."""
    return settings.get_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
