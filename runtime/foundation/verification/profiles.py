"""
Verification Profiles — Program 7B

Immutable verification profiles that expand into deterministic tasks.
Each profile maps to a specific set of verification commands.
No profile may contain duplicated commands.
"""

from __future__ import annotations

from dataclasses import dataclass

from runtime.foundation.verification.models import (
    VerificationCategory,
    VerificationScope,
    VerificationTask,
)


@dataclass(frozen=True, slots=True)
class VerificationProfile:
    """Immutable verification profile."""

    name: str
    scope: VerificationScope
    description: str
    tasks: tuple[VerificationTask, ...]

    def expand_tasks(self) -> tuple[VerificationTask, ...]:
        """Return the deterministic task list for this profile."""
        return self.tasks

    def task_ids(self) -> tuple[str, ...]:
        """Return all task IDs for this profile."""
        return tuple(t.id for t in self.tasks)

    def command_count(self) -> int:
        """Return the total number of commands across all tasks."""
        return sum(len(t.commands) for t in self.tasks)


_VERIFY_QUICK_TASKS = (
    VerificationTask(
        id="quick-ruff",
        name="Ruff lint check",
        profile="quick",
        commands=["python3 -m ruff check backend/src/"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.QUICK,
        estimated_duration_seconds=30,
    ),
    VerificationTask(
        id="quick-mypy",
        name="MyPy type check",
        profile="quick",
        commands=["python3 -m mypy backend/src/ --ignore-missing-imports"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.QUICK,
        estimated_duration_seconds=60,
    ),
    VerificationTask(
        id="quick-unit",
        name="Quick unit tests",
        profile="quick",
        commands=["python3 -m pytest backend/tests/unit/ -x --tb=short -q"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.QUICK,
        estimated_duration_seconds=120,
    ),
)

_VERIFY_BACKEND_TASKS = (
    VerificationTask(
        id="backend-ruff",
        name="Ruff lint check",
        profile="backend",
        commands=["python3 -m ruff check backend/src/"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.BACKEND,
        estimated_duration_seconds=30,
    ),
    VerificationTask(
        id="backend-mypy",
        name="MyPy type check",
        profile="backend",
        commands=["python3 -m mypy backend/src/ --ignore-missing-imports"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.BACKEND,
        estimated_duration_seconds=60,
    ),
    VerificationTask(
        id="backend-unit",
        name="Backend unit tests",
        profile="backend",
        commands=["python3 -m pytest backend/tests/unit/ -x --tb=short -q"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.BACKEND,
        estimated_duration_seconds=120,
    ),
    VerificationTask(
        id="backend-integration",
        name="Backend integration tests",
        profile="backend",
        commands=["python3 -m pytest backend/tests/integration/ -x --tb=short -q"],
        category=VerificationCategory.INTEGRATION,
        scope=VerificationScope.BACKEND,
        estimated_duration_seconds=180,
    ),
    VerificationTask(
        id="backend-schemathesis",
        name="Schemathesis contract tests",
        profile="backend",
        commands=["python3 -m schemathesis run --hypothesis-max-examples=50 backend/tests/contract/"],
        category=VerificationCategory.CONTRACT,
        scope=VerificationScope.BACKEND,
        estimated_duration_seconds=180,
    ),
    VerificationTask(
        id="backend-aggregate",
        name="Aggregate evidence",
        profile="backend",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.BACKEND,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_FRONTEND_TASKS = (
    VerificationTask(
        id="frontend-lint",
        name="Frontend lint check",
        profile="frontend",
        commands=["npx eslint frontend/src/ --ext .ts,.tsx"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FRONTEND,
        estimated_duration_seconds=30,
    ),
    VerificationTask(
        id="frontend-typecheck",
        name="Frontend type check",
        profile="frontend",
        commands=["cd frontend && npx tsc --noEmit"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FRONTEND,
        estimated_duration_seconds=60,
    ),
    VerificationTask(
        id="frontend-unit",
        name="Frontend unit tests",
        profile="frontend",
        commands=["cd frontend && npx vitest run"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FRONTEND,
        estimated_duration_seconds=120,
    ),
    VerificationTask(
        id="frontend-build",
        name="Frontend build",
        profile="frontend",
        commands=["cd frontend && npm run build"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FRONTEND,
        estimated_duration_seconds=60,
    ),
    VerificationTask(
        id="frontend-aggregate",
        name="Aggregate evidence",
        profile="frontend",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FRONTEND,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_CONTRACTS_TASKS = (
    VerificationTask(
        id="contracts-schemathesis",
        name="Schemathesis contract validation",
        profile="contracts",
        commands=["python3 -m schemathesis run --hypothesis-max-examples=50 backend/tests/contract/"],
        category=VerificationCategory.CONTRACT,
        scope=VerificationScope.CONTRACTS,
        estimated_duration_seconds=180,
    ),
    VerificationTask(
        id="contracts-backend-unit",
        name="Backend unit tests for contracts",
        profile="contracts",
        commands=["python3 -m pytest backend/tests/unit/ -x --tb=short -q -k contract"],
        category=VerificationCategory.CONTRACT,
        scope=VerificationScope.CONTRACTS,
        estimated_duration_seconds=120,
    ),
    VerificationTask(
        id="contracts-aggregate",
        name="Aggregate contract evidence",
        profile="contracts",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.CONTRACTS,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_GRAPH_TASKS = (
    VerificationTask(
        id="graph-integrity",
        name="Graph integrity check",
        profile="graph",
        commands=["python3 -c 'from runtime.foundation.repository.graph.graph_service import RepositoryGraphService; s=RepositoryGraphService(); s.load()'"],
        category=VerificationCategory.ARCHITECTURAL,
        scope=VerificationScope.REPOSITORY,
        estimated_duration_seconds=30,
    ),
    VerificationTask(
        id="graph-cross-layer",
        name="Cross-layer map validation",
        profile="graph",
        commands=["python3 -c 'import json; json.load(open(\"runtime/generated/cross-layer-map.json\"))'"],
        category=VerificationCategory.ARCHITECTURAL,
        scope=VerificationScope.REPOSITORY,
        estimated_duration_seconds=10,
    ),
    VerificationTask(
        id="graph-aggregate",
        name="Aggregate graph evidence",
        profile="graph",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.REPOSITORY,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_FULL_TASKS = (
    VerificationTask(
        id="full-ruff",
        name="Ruff lint check",
        profile="full",
        commands=["python3 -m ruff check backend/src/"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=30,
    ),
    VerificationTask(
        id="full-mypy",
        name="MyPy type check",
        profile="full",
        commands=["python3 -m mypy backend/src/ --ignore-missing-imports"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=60,
    ),
    VerificationTask(
        id="full-backend-unit",
        name="Backend unit tests",
        profile="full",
        commands=["python3 -m pytest backend/tests/unit/ -x --tb=short -q"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=120,
    ),
    VerificationTask(
        id="full-backend-integration",
        name="Backend integration tests",
        profile="full",
        commands=["python3 -m pytest backend/tests/integration/ -x --tb=short -q"],
        category=VerificationCategory.INTEGRATION,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=180,
    ),
    VerificationTask(
        id="full-schemathesis",
        name="Schemathesis contract tests",
        profile="full",
        commands=["python3 -m schemathesis run --hypothesis-max-examples=50 backend/tests/contract/"],
        category=VerificationCategory.CONTRACT,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=180,
    ),
    VerificationTask(
        id="full-frontend-lint",
        name="Frontend lint check",
        profile="full",
        commands=["npx eslint frontend/src/ --ext .ts,.tsx"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=30,
    ),
    VerificationTask(
        id="full-frontend-typecheck",
        name="Frontend type check",
        profile="full",
        commands=["cd frontend && npx tsc --noEmit"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=60,
    ),
    VerificationTask(
        id="full-frontend-unit",
        name="Frontend unit tests",
        profile="full",
        commands=["cd frontend && npx vitest run"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=120,
    ),
    VerificationTask(
        id="full-frontend-build",
        name="Frontend build",
        profile="full",
        commands=["cd frontend && npm run build"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=60,
    ),
    VerificationTask(
        id="full-graph",
        name="Graph integrity check",
        profile="full",
        commands=["python3 -c 'from runtime.foundation.repository.graph.graph_service import RepositoryGraphService; s=RepositoryGraphService(); s.load()'"],
        category=VerificationCategory.ARCHITECTURAL,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=30,
    ),
    VerificationTask(
        id="full-aggregate",
        name="Aggregate evidence",
        profile="full",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.FULL,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_MUTATION_TASKS = (
    VerificationTask(
        id="mutation-run",
        name="Selective mutation testing",
        profile="mutation",
        commands=["bash .github/scripts/run_mutation_selective.sh"],
        category=VerificationCategory.MUTATION,
        scope=VerificationScope.MUTATION,
        estimated_duration_seconds=600,
    ),
    VerificationTask(
        id="mutation-aggregate",
        name="Aggregate mutation evidence",
        profile="mutation",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.MUTATION,
        scope=VerificationScope.MUTATION,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_RUNTIME_TASKS = (
    VerificationTask(
        id="runtime-self-test",
        name="Runtime self-verification",
        profile="runtime",
        commands=["bash .github/scripts/run_runtime_verification.sh"],
        category=VerificationCategory.ARCHITECTURAL,
        scope=VerificationScope.RUNTIME,
        estimated_duration_seconds=120,
    ),
    VerificationTask(
        id="runtime-aggregate",
        name="Aggregate runtime evidence",
        profile="runtime",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.ARCHITECTURAL,
        scope=VerificationScope.RUNTIME,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_GOLDEN_TASKS = (
    VerificationTask(
        id="golden-regression",
        name="Golden dataset regression",
        profile="golden",
        commands=["bash .github/scripts/run_golden_tests.sh"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.GOLDEN,
        estimated_duration_seconds=600,
    ),
    VerificationTask(
        id="golden-aggregate",
        name="Aggregate golden evidence",
        profile="golden",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.CAPABILITY,
        scope=VerificationScope.GOLDEN,
        estimated_duration_seconds=30,
    ),
)

_VERIFY_PLAYWRIGHT_TASKS = (
    VerificationTask(
        id="playwright-e2e",
        name="Playwright end-to-end tests",
        profile="playwright",
        commands=["cd frontend && npx playwright test"],
        category=VerificationCategory.INTEGRATION,
        scope=VerificationScope.PLAYWRIGHT,
        estimated_duration_seconds=1800,
    ),
    VerificationTask(
        id="playwright-aggregate",
        name="Aggregate e2e evidence",
        profile="playwright",
        commands=["python3 -c 'from runtime.system.evidence.aggregator import EvidenceAggregator; EvidenceAggregator(\".\").aggregate()'"],
        category=VerificationCategory.INTEGRATION,
        scope=VerificationScope.PLAYWRIGHT,
        estimated_duration_seconds=30,
    ),
)

_PROFILES: dict[str, VerificationProfile] = {
    "quick": VerificationProfile(
        name="quick",
        scope=VerificationScope.QUICK,
        description="Fast local checks (lint, typecheck, fast tests)",
        tasks=_VERIFY_QUICK_TASKS,
    ),
    "backend": VerificationProfile(
        name="backend",
        scope=VerificationScope.BACKEND,
        description="Full backend verification suite",
        tasks=_VERIFY_BACKEND_TASKS,
    ),
    "frontend": VerificationProfile(
        name="frontend",
        scope=VerificationScope.FRONTEND,
        description="Full frontend verification suite",
        tasks=_VERIFY_FRONTEND_TASKS,
    ),
    "contracts": VerificationProfile(
        name="contracts",
        scope=VerificationScope.CONTRACTS,
        description="Contract tests for all capabilities",
        tasks=_VERIFY_CONTRACTS_TASKS,
    ),
    "graph": VerificationProfile(
        name="graph",
        scope=VerificationScope.REPOSITORY,
        description="Graph integrity and cross-layer validation",
        tasks=_VERIFY_GRAPH_TASKS,
    ),
    "full": VerificationProfile(
        name="full",
        scope=VerificationScope.FULL,
        description="Complete verification suite",
        tasks=_VERIFY_FULL_TASKS,
    ),
    "mutation": VerificationProfile(
        name="mutation",
        scope=VerificationScope.MUTATION,
        description="Selective mutation testing for critical modules",
        tasks=_VERIFY_MUTATION_TASKS,
    ),
    "runtime": VerificationProfile(
        name="runtime",
        scope=VerificationScope.RUNTIME,
        description="Engineering Runtime self-verification",
        tasks=_VERIFY_RUNTIME_TASKS,
    ),
    "golden": VerificationProfile(
        name="golden",
        scope=VerificationScope.GOLDEN,
        description="Golden dataset regression tests",
        tasks=_VERIFY_GOLDEN_TASKS,
    ),
    "playwright": VerificationProfile(
        name="playwright",
        scope=VerificationScope.PLAYWRIGHT,
        description="End-to-end Playwright browser tests",
        tasks=_VERIFY_PLAYWRIGHT_TASKS,
    ),
}


def get_profile(name: str) -> VerificationProfile:
    """Get a verification profile by name."""
    if name not in _PROFILES:
        raise ValueError(
            f"Unknown verification profile: '{name}'. "
            f"Available profiles: {', '.join(sorted(_PROFILES.keys()))}"
        )
    return _PROFILES[name]


def list_profiles() -> tuple[VerificationProfile, ...]:
    """Return all available verification profiles."""
    return tuple(_PROFILES.values())


def profile_names() -> tuple[str, ...]:
    """Return all available profile names."""
    return tuple(sorted(_PROFILES.keys()))