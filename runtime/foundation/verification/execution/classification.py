"""M28.9 — Failure classification taxonomy.

Closed taxonomy of execution outcomes used throughout the executor pipeline.
"""

from __future__ import annotations

from enum import Enum


class FailureKind(str, Enum):
    """Closed taxonomy of execution outcomes.

    Verification failure   — verification actually ran and found a defect.
    Infrastructure failure — verification could not execute correctly.
    Evidence failure       — execution occurred but required evidence could
                             not be captured or reconciled.
    Scope failure          — executor attempted to exceed planner-authorized
                             scope.
    Configuration failure  — requested task cannot be represented or
                             executed under current configuration.
    Certification failure  — all required evidence exists but the
                             certification criteria are not satisfied.
    """

    VERIFICATION = "verification_failure"
    INFRASTRUCTURE = "infrastructure_failure"
    EVIDENCE = "evidence_failure"
    SCOPE = "scope_failure"
    CONFIGURATION = "configuration_failure"
    CERTIFICATION = "certification_failure"
