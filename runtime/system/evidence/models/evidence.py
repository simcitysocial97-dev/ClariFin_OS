"""Evidence Models — Structured dataclasses for verification evidence.

DEPRECATED: This module now re-exports all evidence types from the canonical
location ``runtime.foundation.verification.evidence_schema``. The original
definitions have been consolidated there to eliminate duplication.

All original import paths continue to work unchanged.
"""
from __future__ import annotations

# Re-export all evidence types from the unified schema for backward compatibility.
from runtime.foundation.verification.evidence_schema import (  # noqa: F401,F403
    ContractEvidence,
    CoverageEvidence,
    EvidenceCollectionResult,
    MutationEvidence,
    TestResultEvidence,
    VerificationEvidence,
)

__all__ = [
    "CoverageEvidence",
    "MutationEvidence",
    "TestResultEvidence",
    "ContractEvidence",
    "VerificationEvidence",
    "EvidenceCollectionResult",
]
