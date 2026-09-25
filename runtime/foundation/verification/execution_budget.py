"""M9-C65 — Execution budget model.

Replaces ambiguous timeout/exit-124 semantics with a structured
execution-budget model that reports:

    Phase, Completed obligations, Elapsed time,
    Estimated remaining, Current obligation,
    Termination reason, Resume support, Result classification.

This is consumed by the check command to produce truthful boundary
reports instead of bare exit codes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class BudgetPhase(str, Enum):
    """Execution phases with associated budgets."""

    PLANNING = "planning"
    EXECUTION = "execution"
    MEASUREMENT = "measurement"
    CERTIFICATION = "certification"
    DIAGNOSTIC = "diagnostic"


class TerminationReason(str, Enum):
    """Why execution terminated."""

    COMPLETED = "completed"
    EXTERNAL_BUDGET = "external_budget"
    INTERNAL_TIMEOUT = "internal_timeout"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    BLOCKED = "blocked"


class ResultClassification(str, Enum):
    """Machine-readable result classification."""

    PASS = "PASS"
    PASS_WITH_WARNING = "PASS_WITH_WARNING"
    PASS_WITH_NOTES = "PASS_WITH_NOTES"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"
    EXTERNAL_BOUNDARY = "EXTERNAL_BOUNDARY"
    ENVIRONMENT_BOUNDARY = "ENVIRONMENT_BOUNDARY"
    GITHUB_ONLY = "GITHUB_ONLY"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    """Budget allocation per phase."""

    planning_budget_seconds: int = 120
    execution_budget_seconds: int = 4200
    measurement_budget_seconds: int = 1800
    certification_budget_seconds: int = 600
    diagnostic_budget_seconds: int = 120

    def total_budget_seconds(self) -> int:
        return (
            self.planning_budget_seconds
            + self.execution_budget_seconds
            + self.measurement_budget_seconds
            + self.certification_budget_seconds
            + self.diagnostic_budget_seconds
        )

    def for_phase(self, phase: BudgetPhase) -> int:
        return {
            BudgetPhase.PLANNING: self.planning_budget_seconds,
            BudgetPhase.EXECUTION: self.execution_budget_seconds,
            BudgetPhase.MEASUREMENT: self.measurement_budget_seconds,
            BudgetPhase.CERTIFICATION: self.certification_budget_seconds,
            BudgetPhase.DIAGNOSTIC: self.diagnostic_budget_seconds,
        }[phase]


@dataclass
class ExecutionBoundaryReport:
    """Structured report for when execution hits a boundary."""

    phase: BudgetPhase
    completed_obligations: int
    total_obligations: int
    elapsed_seconds: float
    estimated_remaining_seconds: float
    current_obligation: str | None = None
    termination_reason: TerminationReason = TerminationReason.COMPLETED
    resume_supported: bool = False
    result_classification: ResultClassification = ResultClassification.PASS
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "schema": "m9-c65-execution-boundary/v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "phase": self.phase.value,
            "completed_obligations": self.completed_obligations,
            "total_obligations": self.total_obligations,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "estimated_remaining_seconds": round(self.estimated_remaining_seconds, 2),
            "current_obligation": self.current_obligation,
            "termination_reason": self.termination_reason.value,
            "resume_supported": self.resume_supported,
            "result_classification": self.result_classification.value,
            "details": self.details,
        }

    def format_text(self) -> str:
        lines = []
        lines.append("EXECUTION_BOUNDARY")
        lines.append(f"  Phase:            {self.phase.value}")
        lines.append(
            f"  Completed:        {self.completed_obligations} / {self.total_obligations} obligations"
        )
        lines.append(f"  Elapsed:          {self.elapsed_seconds:.1f}s")
        lines.append(
            f"  Estimated remaining: {self.estimated_remaining_seconds:.0f}s"
        )
        if self.current_obligation:
            lines.append(f"  Current:          {self.current_obligation}")
        lines.append(f"  Termination:      {self.termination_reason.value}")
        lines.append(f"  Resume supported: {self.resume_supported}")
        lines.append(f"  Result:           {self.result_classification.value}")
        return "\n".join(lines)


def classify_boundary(
    elapsed: float,
    budget: ExecutionBudget,
    completed: int,
    total: int,
    external_timeout: bool = False,
    interrupted: bool = False,
    failed: bool = False,
    current_task: str | None = None,
) -> ExecutionBoundaryReport:
    """Produce a structured boundary report from execution state."""
    if interrupted:
        return ExecutionBoundaryReport(
            phase=BudgetPhase.EXECUTION,
            completed_obligations=completed,
            total_obligations=total,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=max(0, budget.total_budget_seconds() - elapsed),
            current_obligation=current_task,
            termination_reason=TerminationReason.INTERRUPTED,
            resume_supported=True,
            result_classification=ResultClassification.INCOMPLETE,
        )

    if external_timeout:
        return ExecutionBoundaryReport(
            phase=BudgetPhase.EXECUTION,
            completed_obligations=completed,
            total_obligations=total,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=max(
                0, budget.execution_budget_seconds - elapsed
            ),
            current_obligation=current_task,
            termination_reason=TerminationReason.EXTERNAL_BUDGET,
            resume_supported=False,
            result_classification=ResultClassification.EXTERNAL_BOUNDARY,
            details={
                "external_timeout_seconds": int(elapsed),
                "execution_budget_seconds": budget.execution_budget_seconds,
            },
        )

    if failed:
        return ExecutionBoundaryReport(
            phase=BudgetPhase.EXECUTION,
            completed_obligations=completed,
            total_obligations=total,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=0,
            current_obligation=current_task,
            termination_reason=TerminationReason.FAILED,
            resume_supported=False,
            result_classification=ResultClassification.FAILED,
        )

    # Normal completion
    return ExecutionBoundaryReport(
        phase=BudgetPhase.EXECUTION,
        completed_obligations=completed,
        total_obligations=total,
        elapsed_seconds=elapsed,
        estimated_remaining_seconds=0,
        termination_reason=TerminationReason.COMPLETED,
        resume_supported=False,
        result_classification=ResultClassification.PASS,
    )


if __name__ == "__main__":
    # Demo
    budget = ExecutionBudget()
    report = classify_boundary(
        elapsed=120.4,
        budget=budget,
        completed=27,
        total=64,
        external_timeout=True,
        current_task="task-credit-card-tests",
    )
    print(report.format_text())
    print()
    import json

    print(json.dumps(report.to_dict(), indent=2))
