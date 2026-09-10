"""
M9-C54 — Workflow failure semantics (Q8).

Standalone module that defines the expected failure semantics for all
failure types without depending on workflow inventory.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FailureSemantics:
    failure_type: str
    expected_classification: str
    expected_certification_effect: str
    evidence_required: bool
    fail_closed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "expected_classification": self.expected_classification,
            "expected_certification_effect": self.expected_certification_effect,
            "evidence_required": self.evidence_required,
            "fail_closed": self.fail_closed,
        }


def build_failure_semantics() -> list[FailureSemantics]:
    """Define the expected failure semantics for all failure types."""
    return [
        FailureSemantics("unit_test_failure", "TEST_FAILURE", "BLOCKED", True, True),
        FailureSemantics(
            "integration_test_failure", "TEST_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics("coverage_failure", "COMMAND_FAILURE", "BLOCKED", True, True),
        FailureSemantics("mutation_failure", "COMMAND_FAILURE", "BLOCKED", True, True),
        FailureSemantics("mutation_timeout", "TIMEOUT", "BLOCKED", True, True),
        FailureSemantics("lint_failure", "COMMAND_FAILURE", "BLOCKED", True, True),
        FailureSemantics("typecheck_failure", "COMMAND_FAILURE", "BLOCKED", True, True),
        FailureSemantics("missing_artifact", "ARTIFACT_FAILURE", "BLOCKED", True, True),
        FailureSemantics(
            "malformed_artifact", "ARTIFACT_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics("stale_artifact", "ARTIFACT_FAILURE", "BLOCKED", True, True),
        FailureSemantics(
            "sha_mismatch", "RECONCILIATION_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics(
            "config_mismatch", "RECONCILIATION_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics(
            "toolchain_mismatch", "RECONCILIATION_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics(
            "workflow_step_skip", "UNKNOWN_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics(
            "continue_on_error_failure", "UNKNOWN_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics(
            "missing_ci_evidence", "ARTIFACT_FAILURE", "BLOCKED", True, True
        ),
        FailureSemantics(
            "contradictory_evidence", "RECONCILIATION_FAILURE", "BLOCKED", True, True
        ),
    ]
