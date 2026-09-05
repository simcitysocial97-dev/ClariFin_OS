"""Platform diagnostics package — M9-C57 Phase 11.

Deterministic diagnostic engine with failure signatures, rules, and
recommendations. No LLM required.
"""

from __future__ import annotations

from runtime.platform.diagnostics.engine import (  # noqa: F401
    diagnose,
    build_diagnostic_recommendation,
    register_signature,
    bump_signature_occurrence,
)
from runtime.platform.diagnostics.rules import evaluate as evaluate_rules  # noqa: F401

__all__ = [
    "diagnose",
    "build_diagnostic_recommendation",
    "register_signature",
    "bump_signature_occurrence",
    "evaluate_rules",
]
