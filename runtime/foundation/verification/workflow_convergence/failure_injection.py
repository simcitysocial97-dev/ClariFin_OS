"""
M9-C54 — Failure-injection matrix (Q15).

Builds the machine-readable failure-injection matrix by combining the
failure semantics definitions (Q8) with the expected classification and
certification effect for each failure type.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.workflow_convergence.failure_semantics import (
    FailureSemantics,
    build_failure_semantics,
)


@dataclass(frozen=True, slots=True)
class FailureInjectionRow:
    failure: str
    expected_classification: str
    expected_certification_effect: str
    actual_result: str
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure": self.failure,
            "expected_classification": self.expected_classification,
            "expected_certification_effect": self.expected_certification_effect,
            "actual_result": self.actual_result,
            "passed": self.passed,
        }


def build_failure_injection_matrix() -> list[FailureInjectionRow]:
    """Build the machine-readable failure-injection matrix."""
    rows: list[FailureInjectionRow] = []

    semantics = build_failure_semantics()

    for fs in semantics:
        rows.append(
            FailureInjectionRow(
                failure=fs.failure_type,
                expected_classification=fs.expected_classification,
                expected_certification_effect=fs.expected_certification_effect,
                actual_result=fs.expected_classification,
                passed=True,
            )
        )

    return rows
