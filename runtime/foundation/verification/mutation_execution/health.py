# runtime/foundation/verification/mutation_execution/health.py
#
# M9-C44.24 + M44.25 — Mutation Health Dashboard + Failure Budget.
#
# Produces structured metrics for campaign observability and defines
# acceptable failure-rate thresholds that must be met for certification.

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from runtime.foundation.verification.mutation_execution.domain_model import (
    MutationResult,
)


@dataclass
class CampaignHealth:
    """Structured health metrics for a mutation campaign."""
    campaign_id: str
    execution_reliability: float | None
    mutation_completeness: float | None
    worker_failure_rate: float | None
    timeout_rate: float | None
    retry_rate: float | None
    cache_hit_rate: float | None
    false_execution_rate: float | None
    backend_error_rate: float | None
    throughput: float | None  # mutants per minute
    estimated_remaining_minutes: float | None


@dataclass
class FailureBudget:
    """Maximum acceptable failure rates for campaign certification."""

    max_infrastructure_failure_rate: float = 0.05      # 5%
    max_unexplained_timeout_rate: float = 0.03         # 3%
    max_invalid_execution_rate: float = 0.02           # 2%
    max_retry_exhaustion_rate: float = 0.01            # 1%
    max_worker_crash_rate: float = 0.01                # 1%
    max_stale_cache_rate: float = 0.0                  # 0% (cache must never be stale)
    max_unclassified_result_rate: float = 0.02         # 2%

    def check(self, result: MutationResult) -> tuple[bool, list[str]]:
        """Check whether the result stays within the failure budget."""
        total = result.total_executions or result.total_candidates or 1
        violations = []

        infra_rate = result.infrastructure_failures / total
        if infra_rate > self.max_infrastructure_failure_rate:
            violations.append(
                f"infrastructure_failure_rate={infra_rate:.2%} > {self.max_infrastructure_failure_rate:.0%}"
            )

        timeout_rate = result.timeout / total
        if timeout_rate > self.max_unexplained_timeout_rate:
            violations.append(
                f"timeout_rate={timeout_rate:.2%} > {self.max_unexplained_timeout_rate:.0%}"
            )

        invalid_rate = result.invalid_mutant / total
        if invalid_rate > self.max_invalid_execution_rate:
            violations.append(
                f"invalid_execution_rate={invalid_rate:.2%} > {self.max_invalid_execution_rate:.0%}"
            )

        unknown_rate = result.unknown / total
        if unknown_rate > self.max_unclassified_result_rate:
            violations.append(
                f"unclassified_rate={unknown_rate:.2%} > {self.max_unclassified_result_rate:.0%}"
            )

        passed = len(violations) == 0
        return passed, violations

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_health_metrics(result: MutationResult) -> CampaignHealth:
    """Compute health dashboard metrics from a MutationResult."""
    total = result.total_executions or 1
    scored = result.scored_total

    return CampaignHealth(
        campaign_id=result.campaign_id,
        execution_reliability=result.execution_reliability,
        mutation_completeness=(
            round(scored * 100.0 / result.total_candidates, 1)
            if result.total_candidates > 0 else 0.0
        ),
        worker_failure_rate=round(result.infrastructure_failures / total, 4),
        timeout_rate=round(result.timeout / total, 4),
        retry_rate=round(result.retries_total / total, 4),
        cache_hit_rate=None,  # requires cache instrumentation
        false_execution_rate=round(result.execution_error / total, 4),
        backend_error_rate=round(result.execution_error / total, 4),
        throughput=None,  # requires timing data
        estimated_remaining_minutes=None,
    )


def certification_check(result: MutationResult, budget: FailureBudget | None = None) -> dict[str, Any]:
    """M44.26: Determine whether a campaign passes certification gates."""
    if budget is None:
        budget = FailureBudget()

    budget_ok, budget_violations = budget.check(result)
    reconciled = result.reconcile()
    has_score = result.score is not None
    reliability_ok = (
        result.execution_reliability is not None
        and result.execution_reliability >= 95.0
    )

    return {
        "campaign_id": result.campaign_id,
        "mutation_score": result.score,
        "score_threshold": 80,
        "score_pass": (result.score or 0) >= 80,
        "reconciled": reconciled,
        "has_score": has_score,
        "execution_reliability": result.execution_reliability,
        "reliability_above_95": reliability_ok,
        "failure_budget_pass": budget_ok,
        "failure_budget_violations": budget_violations,
        "certifiable": reconciled and has_score and budget_ok and reliability_ok,
        "verdict": (
            "CERTIFIED"
            if reconciled and has_score and budget_ok and reliability_ok and (result.score or 0) >= 80
            else "NOT_CERTIFIED"
        ),
    }


__all__ = [
    "CampaignHealth",
    "FailureBudget",
    "compute_health_metrics",
    "certification_check",
]
