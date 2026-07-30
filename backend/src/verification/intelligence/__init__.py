"""Verification Intelligence Layer for ClariFin_OS.

Provides architecture-aware verification capabilities:
- Dependency Intelligence: auto-discovery of component relationships
- Change Impact Analysis: determines what verification is needed
- Risk Classification: lightweight risk metadata for components
- Verification Evidence: evidence model for why capabilities are verified
- Architectural Coverage: capability-level verification gap analysis
- Selective Execution: intelligence-driven CI job selection
- Self-Validation: extended meta verification of the intelligence layer
- Reporting: machine-readable JSON artifacts for CI integration

This layer sits on top of the existing Registry-driven Verification Runtime
and does not replace or redesign any existing component.
"""

from __future__ import annotations

__version__ = "1.0.0"
__all__ = [
    "DependencyEngine",
    "ImpactEngine",
    "RiskEngine",
    "EvidenceEngine",
    "CoverageEngine",
    "SelectiveEngine",
    "SelfValidationEngine",
    "ReportEngine",
]
