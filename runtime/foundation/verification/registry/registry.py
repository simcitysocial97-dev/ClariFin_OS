"""
Verification Registry — Phase 3

Loads verification.yaml and registers verification capabilities.
Deterministic lookup only. No execution logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from runtime.foundation.verification.models import (
    VerificationCategory,
    VerificationScope,
    VerificationSeverity,
    VerificationRequirement,
)


@dataclass(frozen=True, slots=True)
class VerificationWorkflow:
    """A registered verification workflow."""

    id: str
    name: str
    description: str
    category: VerificationCategory
    scope: VerificationScope
    command: str | None = None
    script: str | None = None
    estimated_duration_seconds: int = 0
    required_evidence: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    scopes: list[VerificationScope] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationScript:
    """A registered verification script."""

    id: str
    name: str
    path: str
    description: str
    category: VerificationCategory
    scope: VerificationScope
    capabilities: list[str] = field(default_factory=list)
    estimated_duration_seconds: int = 0
    required_evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VerificationCapability:
    """A registered verification capability."""

    id: str
    name: str
    description: str
    category: VerificationCategory
    scopes: list[VerificationScope]
    requirements: list[VerificationRequirement] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class VerificationRegistry:
    """
    Verification Registry - deterministic registry for verification artifacts.

    Loads verification.yaml and registers:
    - Verification categories
    - Verification commands/workflows
    - Verification scripts
    - Verification capabilities

    Supports lookup by: capability, module, workflow, script, verification type.
    """

    def __init__(self, config_path: Path | None = None):
        self._config_path = (
            config_path or Path(__file__).parent.parent / "verification.yaml"
        )
        self._config: dict[str, Any] = {}
        self._workflows: dict[str, VerificationWorkflow] = {}
        self._scripts: dict[str, VerificationScript] = {}
        self._capabilities: dict[str, VerificationCapability] = {}
        self._requirements: dict[str, VerificationRequirement] = {}
        self._categories: dict[VerificationCategory, dict[str, Any]] = {}
        self._scopes: dict[VerificationScope, dict[str, Any]] = {}
        self._modules: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load verification.yaml and register all artifacts."""
        if self._loaded:
            return

        if not self._config_path.exists():
            raise FileNotFoundError(
                f"Verification config not found: {self._config_path}"
            )

        with open(self._config_path) as f:
            self._config = yaml.safe_load(f) or {}

        self._register_categories()
        self._register_scopes()
        self._register_modules()
        self._register_workflows()
        self._register_scripts()
        self._register_capabilities()

        self._loaded = True

    def _register_categories(self) -> None:
        """Register verification categories from config."""
        categories_config = self._config.get("categories", {})
        for cat_name, cat_config in categories_config.items():
            try:
                category = VerificationCategory(cat_name)
                self._categories[category] = cat_config
            except ValueError:
                pass  # Skip unknown categories

        # Register default categories if not in config
        for cat in VerificationCategory:
            if cat not in self._categories:
                self._categories[cat] = {"enabled": True}

    def _register_scopes(self) -> None:
        """Register verification scopes from config."""
        scopes_config = self._config.get("scopes", {})
        for scope_name, scope_config in scopes_config.items():
            try:
                scope = VerificationScope(scope_name)
                self._scopes[scope] = scope_config
            except ValueError:
                pass

        # Register default scopes
        for scope in VerificationScope:
            if scope not in self._scopes:
                self._scopes[scope] = {"enabled": True}

    def _register_modules(self) -> None:
        """Register modules from config."""
        modules_config = self._config.get("modules", {})
        for module_name, module_config in modules_config.items():
            self._modules[module_name] = module_config

        # Add defaults from backend/frontend paths
        backend_config = self._config.get("backend", {})
        if backend_config.get("paths", {}).get("source"):
            self._modules["backend"] = {
                "source": backend_config["paths"]["source"],
                "tests": backend_config["paths"].get("tests", ""),
                "category": VerificationCategory.CAPABILITY,
            }

        frontend_config = self._config.get("frontend", {})
        if frontend_config.get("paths", {}).get("source"):
            self._modules["frontend"] = {
                "source": frontend_config["paths"]["source"],
                "tests": frontend_config["paths"].get("tests", ""),
                "category": VerificationCategory.CONTRACT_FRONTEND,
            }

    def _register_workflows(self) -> None:
        """Register verification workflows from config and defaults."""
        workflows_config = self._config.get("workflows", {})

        # Built-in workflows
        default_workflows = {
            "quick": VerificationWorkflow(
                id="quick",
                name="Quick Verification",
                description="Fast local checks (lint, typecheck, unit tests)",
                category=VerificationCategory.CAPABILITY,
                scope=VerificationScope.QUICK,
                command="bash .github/scripts/run_fast_checks.sh",
                estimated_duration_seconds=60,
                scopes=[VerificationScope.QUICK],
            ),
            "backend": VerificationWorkflow(
                id="backend",
                name="Backend Verification",
                description="Full backend verification suite",
                category=VerificationCategory.CAPABILITY,
                scope=VerificationScope.BACKEND,
                command="bash .github/scripts/run_backend_verification.sh",
                estimated_duration_seconds=300,
                scopes=[
                    VerificationScope.BACKEND,
                    VerificationScope.CONTRACTS,
                    VerificationScope.PROPERTY,
                ],
            ),
            "frontend": VerificationWorkflow(
                id="frontend",
                name="Frontend Verification",
                description="Full frontend verification suite",
                category=VerificationCategory.CONTRACT_FRONTEND,
                scope=VerificationScope.FRONTEND,
                command="bash .github/scripts/run_frontend_verification.sh",
                estimated_duration_seconds=180,
                scopes=[VerificationScope.FRONTEND, VerificationScope.CONTRACTS],
            ),
            "contracts": VerificationWorkflow(
                id="contracts",
                name="Contract Verification",
                description="Contract tests for all capabilities",
                category=VerificationCategory.CONTRACT,
                scope=VerificationScope.CONTRACTS,
                command="bash .github/scripts/run_contract_tests.sh",
                estimated_duration_seconds=180,
                scopes=[VerificationScope.CONTRACTS],
            ),
            "property": VerificationWorkflow(
                id="property",
                name="Property Testing",
                description="Property-based testing for loan engine",
                category=VerificationCategory.PROPERTY,
                scope=VerificationScope.PROPERTY,
                command="bash .github/scripts/run_property_tests.sh",
                estimated_duration_seconds=300,
                scopes=[VerificationScope.PROPERTY],
                capabilities=["loan-engine", "reconciliation"],
            ),
            "mutation": VerificationWorkflow(
                id="mutation",
                name="Mutation Testing",
                description="Mutation testing for critical modules",
                category=VerificationCategory.MUTATION,
                scope=VerificationScope.MUTATION,
                command="bash .github/scripts/run_mutation_selective.sh",
                estimated_duration_seconds=600,
                scopes=[VerificationScope.MUTATION],
            ),
            "integration": VerificationWorkflow(
                id="integration",
                name="Integration Tests",
                description="End-to-end integration tests",
                category=VerificationCategory.INTEGRATION,
                scope=VerificationScope.INTEGRATION,
                command="bash .github/scripts/run_integration_tests.sh",
                estimated_duration_seconds=600,
                scopes=[VerificationScope.INTEGRATION],
            ),
            "migration": VerificationWorkflow(
                id="migration",
                name="Migration Verification",
                description="Database migration verification",
                category=VerificationCategory.MIGRATION,
                scope=VerificationScope.MIGRATION,
                command="bash .github/scripts/run_migration_verification.sh",
                estimated_duration_seconds=120,
                scopes=[VerificationScope.MIGRATION],
            ),
            "repository": VerificationWorkflow(
                id="repository",
                name="Repository Verification",
                description="Full repository verification",
                category=VerificationCategory.ARCHITECTURAL,
                scope=VerificationScope.REPOSITORY,
                command="bash .github/scripts/run_full_verification.sh",
                estimated_duration_seconds=1800,
                scopes=[VerificationScope.REPOSITORY],
            ),
            "full": VerificationWorkflow(
                id="full",
                name="Full Verification",
                description="Complete verification suite",
                category=VerificationCategory.ARCHITECTURAL,
                scope=VerificationScope.FULL,
                command="bash .github/scripts/run_full_verification.sh",
                estimated_duration_seconds=3600,
                scopes=[VerificationScope.FULL],
            ),
            "runtime": VerificationWorkflow(
                id="runtime",
                name="Runtime Verification",
                description="Engineering Runtime self-verification",
                category=VerificationCategory.ARCHITECTURAL,
                scope=VerificationScope.RUNTIME,
                command="bash .github/scripts/run_runtime_verification.sh",
                estimated_duration_seconds=120,
                scopes=[VerificationScope.RUNTIME],
            ),
            "golden": VerificationWorkflow(
                id="golden",
                name="Golden Regression",
                description="Golden dataset regression tests",
                category=VerificationCategory.CAPABILITY,
                scope=VerificationScope.GOLDEN,
                command="bash .github/scripts/run_golden_tests.sh",
                estimated_duration_seconds=600,
                scopes=[VerificationScope.GOLDEN],
            ),
            "playwright": VerificationWorkflow(
                id="playwright",
                name="Playwright E2E",
                description="End-to-end browser tests",
                category=VerificationCategory.INTEGRATION,
                scope=VerificationScope.PLAYWRIGHT,
                command="bash .github/scripts/run_playwright_tests.sh",
                estimated_duration_seconds=1800,
                scopes=[VerificationScope.PLAYWRIGHT],
            ),
        }

        # Register defaults
        for wf in default_workflows.values():
            self._workflows[wf.id] = wf

        # Override with config
        for wf_id, wf_config in workflows_config.items():
            if wf_id in self._workflows:
                # Merge config
                wf = self._workflows[wf_id]
                merged = VerificationWorkflow(
                    id=wf.id,
                    name=wf_config.get("name", wf.name),
                    description=wf_config.get("description", wf.description),
                    category=VerificationCategory(
                        wf_config.get("category", wf.category.value)
                    ),
                    scope=VerificationScope(wf_config.get("scope", wf.scope.value)),
                    command=wf_config.get("command", wf.command),
                    script=wf_config.get("script", wf.script),
                    estimated_duration_seconds=wf_config.get(
                        "estimated_duration_seconds", wf.estimated_duration_seconds
                    ),
                    required_evidence=wf_config.get(
                        "required_evidence", wf.required_evidence
                    ),
                    capabilities=wf_config.get("capabilities", wf.capabilities),
                    scopes=[
                        VerificationScope(s)
                        for s in wf_config.get("scopes", [s.value for s in wf.scopes])
                    ],
                    dependencies=wf_config.get("dependencies", wf.dependencies),
                    metadata=wf_config.get("metadata", wf.metadata),
                )
                self._workflows[wf_id] = merged
            else:
                # New workflow from config
                self._workflows[wf_id] = VerificationWorkflow(
                    id=wf_id,
                    name=wf_config.get("name", wf_id),
                    description=wf_config.get("description", ""),
                    category=VerificationCategory(
                        wf_config.get("category", "capability")
                    ),
                    scope=VerificationScope(wf_config.get("scope", "quick")),
                    command=wf_config.get("command"),
                    script=wf_config.get("script"),
                    estimated_duration_seconds=wf_config.get(
                        "estimated_duration_seconds", 0
                    ),
                    required_evidence=wf_config.get("required_evidence", []),
                    capabilities=wf_config.get("capabilities", []),
                    scopes=[VerificationScope(s) for s in wf_config.get("scopes", [])],
                    dependencies=wf_config.get("dependencies", []),
                    metadata=wf_config.get("metadata", {}),
                )

    def _register_scripts(self) -> None:
        """Register verification scripts from config and defaults."""
        scripts_config = self._config.get("scripts", {})

        default_scripts = {
            "run_fast_checks": VerificationScript(
                id="run_fast_checks",
                name="Fast Checks",
                path=".github/scripts/run_fast_checks.sh",
                description="Fast lint, typecheck, and unit tests",
                category=VerificationCategory.CAPABILITY,
                scope=VerificationScope.QUICK,
                estimated_duration_seconds=60,
            ),
            "run_contract_tests": VerificationScript(
                id="run_contract_tests",
                name="Contract Tests",
                path=".github/scripts/run_contract_tests.sh",
                description="Contract tests for all capabilities",
                category=VerificationCategory.CONTRACT,
                scope=VerificationScope.CONTRACTS,
                estimated_duration_seconds=180,
            ),
            "run_property_tests": VerificationScript(
                id="run_property_tests",
                name="Property Tests",
                path=".github/scripts/run_property_tests.sh",
                description="Property-based tests for loan engine",
                category=VerificationCategory.PROPERTY,
                scope=VerificationScope.PROPERTY,
                estimated_duration_seconds=300,
                capabilities=["loan-engine", "reconciliation"],
            ),
            "run_mutation_selective": VerificationScript(
                id="run_mutation_selective",
                name="Selective Mutation Testing",
                path=".github/scripts/run_mutation_selective.sh",
                description="Mutation testing for critical modules",
                category=VerificationCategory.MUTATION,
                scope=VerificationScope.MUTATION,
                estimated_duration_seconds=600,
            ),
            "run_backend_verification": VerificationScript(
                id="run_backend_verification",
                name="Backend Verification",
                path=".github/scripts/run_backend_verification.sh",
                description="Contract, invariant and property tests for the backend",
                category=VerificationCategory.CONTRACT,
                scope=VerificationScope.BACKEND,
                estimated_duration_seconds=300,
            ),
            "run_frontend_verification": VerificationScript(
                id="run_frontend_verification",
                name="Frontend Verification",
                path=".github/scripts/run_frontend_verification.sh",
                description="ESLint, TypeScript typecheck and Vitest for the frontend",
                category=VerificationCategory.CONTRACT_FRONTEND,
                scope=VerificationScope.FRONTEND,
                estimated_duration_seconds=180,
            ),
            "run_migration_verification": VerificationScript(
                id="run_migration_verification",
                name="Migration Verification",
                path=".github/scripts/run_migration_verification.sh",
                description="Database migration integrity checks",
                category=VerificationCategory.MIGRATION,
                scope=VerificationScope.MIGRATION,
                estimated_duration_seconds=120,
            ),
            "run_integration_tests": VerificationScript(
                id="run_integration_tests",
                name="Integration Tests",
                path=".github/scripts/run_integration_tests.sh",
                description="API integration tests",
                category=VerificationCategory.INTEGRATION,
                scope=VerificationScope.INTEGRATION,
                estimated_duration_seconds=600,
            ),
            "run_full_verification": VerificationScript(
                id="run_full_verification",
                name="Full Verification",
                path=".github/scripts/run_full_verification.sh",
                description="Complete backend test suite",
                category=VerificationCategory.ARCHITECTURAL,
                scope=VerificationScope.REPOSITORY,
                estimated_duration_seconds=1800,
            ),
            "run_runtime_verification": VerificationScript(
                id="run_runtime_verification",
                name="Runtime Verification",
                path=".github/scripts/run_runtime_verification.sh",
                description="Engineering Runtime self-verification",
                category=VerificationCategory.ARCHITECTURAL,
                scope=VerificationScope.RUNTIME,
                estimated_duration_seconds=120,
            ),
            "run_golden_tests": VerificationScript(
                id="run_golden_tests",
                name="Golden Regression Tests",
                path=".github/scripts/run_golden_tests.sh",
                description="Golden dataset regression tests",
                category=VerificationCategory.CAPABILITY,
                scope=VerificationScope.GOLDEN,
                estimated_duration_seconds=600,
            ),
            "run_playwright_tests": VerificationScript(
                id="run_playwright_tests",
                name="Playwright E2E Tests",
                path=".github/scripts/run_playwright_tests.sh",
                description="End-to-end Playwright browser tests",
                category=VerificationCategory.INTEGRATION,
                scope=VerificationScope.PLAYWRIGHT,
                estimated_duration_seconds=1800,
            ),
            "run_integration_tests": VerificationScript(
                id="run_integration_tests",
                name="Integration Tests",
                path=".github/scripts/run_integration_tests.sh",
                description="End-to-end integration tests",
                category=VerificationCategory.INTEGRATION,
                scope=VerificationScope.INTEGRATION,
                estimated_duration_seconds=600,
            ),
            "run_migration_verification": VerificationScript(
                id="run_migration_verification",
                name="Migration Verification",
                path=".github/scripts/run_migration_verification.sh",
                description="Database migration verification",
                category=VerificationCategory.MIGRATION,
                scope=VerificationScope.MIGRATION,
                estimated_duration_seconds=120,
            ),
            "run_full_verification": VerificationScript(
                id="run_full_verification",
                name="Full Verification",
                path=".github/scripts/run_full_verification.sh",
                description="Complete verification suite",
                category=VerificationCategory.ARCHITECTURAL,
                scope=VerificationScope.FULL,
                estimated_duration_seconds=3600,
            ),
            "run_backend_verification": VerificationScript(
                id="run_backend_verification",
                name="Backend Verification",
                path=".github/scripts/run_backend_verification.sh",
                description="Full backend verification",
                category=VerificationCategory.CAPABILITY,
                scope=VerificationScope.BACKEND,
                estimated_duration_seconds=300,
            ),
            "run_frontend_verification": VerificationScript(
                id="run_frontend_verification",
                name="Frontend Verification",
                path=".github/scripts/run_frontend_verification.sh",
                description="Full frontend verification",
                category=VerificationCategory.CONTRACT_FRONTEND,
                scope=VerificationScope.FRONTEND,
                estimated_duration_seconds=180,
            ),
        }

        for script in default_scripts.values():
            self._scripts[script.id] = script

        for script_id, script_config in scripts_config.items():
            if script_id in self._scripts:
                script = self._scripts[script_id]
                merged = VerificationScript(
                    id=script.id,
                    name=script_config.get("name", script.name),
                    path=script_config.get("path", script.path),
                    description=script_config.get("description", script.description),
                    category=VerificationCategory(
                        script_config.get("category", script.category.value)
                    ),
                    scope=VerificationScope(
                        script_config.get("scope", script.scope.value)
                    ),
                    capabilities=script_config.get("capabilities", script.capabilities),
                    estimated_duration_seconds=script_config.get(
                        "estimated_duration_seconds", script.estimated_duration_seconds
                    ),
                    required_evidence=script_config.get(
                        "required_evidence", script.required_evidence
                    ),
                    metadata=script_config.get("metadata", script.metadata),
                )
                self._scripts[script_id] = merged
            else:
                self._scripts[script_id] = VerificationScript(
                    id=script_id,
                    name=script_config.get("name", script_id),
                    path=script_config.get("path", ""),
                    description=script_config.get("description", ""),
                    category=VerificationCategory(
                        script_config.get("category", "capability")
                    ),
                    scope=VerificationScope(script_config.get("scope", "quick")),
                    capabilities=script_config.get("capabilities", []),
                    estimated_duration_seconds=script_config.get(
                        "estimated_duration_seconds", 0
                    ),
                    required_evidence=script_config.get("required_evidence", []),
                    metadata=script_config.get("metadata", {}),
                )

    def _register_capabilities(self) -> None:
        """Register capabilities from config and defaults."""
        capabilities_config = self._config.get("capabilities", {})

        default_capabilities = {
            "loan-engine": VerificationCapability(
                id="loan-engine",
                name="Loan Engine",
                description="Core loan calculation engine",
                category=VerificationCategory.CAPABILITY,
                scopes=[
                    VerificationScope.BACKEND,
                    VerificationScope.PROPERTY,
                    VerificationScope.CONTRACTS,
                    VerificationScope.INTEGRATION,
                    VerificationScope.REPOSITORY,
                ],
                requirements=[
                    VerificationRequirement(
                        id="loan-engine-property",
                        category=VerificationCategory.PROPERTY,
                        severity=VerificationSeverity.CRITICAL,
                        description="Property-based tests for loan calculations",
                        scope=VerificationScope.PROPERTY,
                        module="backend/src/loan_engine",
                        capability="loan-engine",
                    ),
                    VerificationRequirement(
                        id="loan-engine-contract",
                        category=VerificationCategory.CONTRACT,
                        severity=VerificationSeverity.CRITICAL,
                        description="Contract tests for loan engine API",
                        scope=VerificationScope.CONTRACTS,
                        module="backend/src/loan_engine",
                        capability="loan-engine",
                    ),
                ],
                workflows=["property", "contracts", "backend"],
                scripts=[
                    "run_property_tests",
                    "run_contract_tests",
                    "run_backend_verification",
                ],
                modules=["backend/src/loan_engine"],
            ),
            "reconciliation": VerificationCapability(
                id="reconciliation",
                name="Reconciliation Engine",
                description="Financial reconciliation engine",
                category=VerificationCategory.CAPABILITY,
                scopes=[
                    VerificationScope.BACKEND,
                    VerificationScope.PROPERTY,
                    VerificationScope.CONTRACTS,
                    VerificationScope.INTEGRATION,
                    VerificationScope.REPOSITORY,
                ],
                requirements=[
                    VerificationRequirement(
                        id="reconciliation-property",
                        category=VerificationCategory.PROPERTY,
                        severity=VerificationSeverity.CRITICAL,
                        description="Property-based tests for reconciliation",
                        scope=VerificationScope.PROPERTY,
                        module="backend/src/reconciliation",
                        capability="reconciliation",
                    ),
                    VerificationRequirement(
                        id="reconciliation-contract",
                        category=VerificationCategory.CONTRACT,
                        severity=VerificationSeverity.CRITICAL,
                        description="Contract tests for reconciliation API",
                        scope=VerificationScope.CONTRACTS,
                        module="backend/src/reconciliation",
                        capability="reconciliation",
                    ),
                ],
                workflows=["property", "contracts", "backend"],
                scripts=[
                    "run_property_tests",
                    "run_contract_tests",
                    "run_backend_verification",
                ],
                modules=["backend/src/reconciliation"],
            ),
            "ledger": VerificationCapability(
                id="ledger",
                name="Ledger Service",
                description="General ledger and accounting",
                category=VerificationCategory.CAPABILITY,
                scopes=[
                    VerificationScope.BACKEND,
                    VerificationScope.CONTRACTS,
                    VerificationScope.INTEGRATION,
                    VerificationScope.REPOSITORY,
                ],
                requirements=[
                    VerificationRequirement(
                        id="ledger-invariant",
                        category=VerificationCategory.INVARIANT,
                        severity=VerificationSeverity.CRITICAL,
                        description="Invariant tests for ledger consistency",
                        scope=VerificationScope.CONTRACTS,
                        module="backend/src/ledger",
                        capability="ledger",
                    ),
                    VerificationRequirement(
                        id="ledger-contract",
                        category=VerificationCategory.CONTRACT,
                        severity=VerificationSeverity.HIGH,
                        description="Contract tests for ledger API",
                        scope=VerificationScope.CONTRACTS,
                        module="backend/src/ledger",
                        capability="ledger",
                    ),
                ],
                workflows=["contracts", "backend", "integration"],
                scripts=[
                    "run_contract_tests",
                    "run_backend_verification",
                    "run_integration_tests",
                ],
                modules=["backend/src/ledger"],
            ),
            "api-contracts": VerificationCapability(
                id="api-contracts",
                name="API Contracts",
                description="OpenAPI contract verification",
                category=VerificationCategory.CONTRACT,
                scopes=[
                    VerificationScope.CONTRACTS,
                    VerificationScope.FRONTEND,
                    VerificationScope.BACKEND,
                    VerificationScope.REPOSITORY,
                ],
                requirements=[
                    VerificationRequirement(
                        id="api-contract-frontend",
                        category=VerificationCategory.CONTRACT_FRONTEND,
                        severity=VerificationSeverity.HIGH,
                        description="Frontend contract compliance",
                        scope=VerificationScope.FRONTEND,
                        module="frontend/src",
                        capability="api-contracts",
                    ),
                    VerificationRequirement(
                        id="api-contract-backend",
                        category=VerificationCategory.CONTRACT_BACKEND,
                        severity=VerificationSeverity.HIGH,
                        description="Backend contract compliance",
                        scope=VerificationScope.BACKEND,
                        module="backend/src",
                        capability="api-contracts",
                    ),
                ],
                workflows=["contracts", "frontend", "backend"],
                scripts=[
                    "run_contract_tests",
                    "run_frontend_verification",
                    "run_backend_verification",
                ],
                modules=["backend/src", "frontend/src"],
            ),
            "migrations": VerificationCapability(
                id="migrations",
                name="Database Migrations",
                description="Database migration verification",
                category=VerificationCategory.MIGRATION,
                scopes=[
                    VerificationScope.MIGRATION,
                    VerificationScope.BACKEND,
                    VerificationScope.REPOSITORY,
                ],
                requirements=[
                    VerificationRequirement(
                        id="migration-up-down",
                        category=VerificationCategory.MIGRATION,
                        severity=VerificationSeverity.CRITICAL,
                        description="Migration up/down verification",
                        scope=VerificationScope.MIGRATION,
                        module="backend/src/migrations",
                        capability="migrations",
                    ),
                ],
                workflows=["migration"],
                scripts=["run_migration_verification"],
                modules=["backend/src/migrations"],
            ),
            "quick": VerificationCapability(
                id="quick",
                name="Quick Quality Gate",
                description="Fast lint, typecheck, format, unit, architecture and meta checks",
                category=VerificationCategory.CAPABILITY,
                scopes=[VerificationScope.QUICK],
                requirements=[
                    VerificationRequirement(
                        id="quick-run",
                        category=VerificationCategory.CAPABILITY,
                        severity=VerificationSeverity.HIGH,
                        description="Run the fast quality gate (ruff, black, mypy, unit, architecture, meta)",
                        scope=VerificationScope.QUICK,
                        module="backend/src",
                        capability="quick",
                    ),
                ],
                workflows=["quick"],
                scripts=["run_fast_checks"],
                modules=[],
            ),
            "runtime-verification": VerificationCapability(
                id="runtime-verification",
                name="Runtime Verification",
                description="Engineering Runtime self-verification",
                category=VerificationCategory.ARCHITECTURAL,
                scopes=[VerificationScope.RUNTIME],
                requirements=[
                    VerificationRequirement(
                        id="runtime-self-test",
                        category=VerificationCategory.ARCHITECTURAL,
                        severity=VerificationSeverity.HIGH,
                        description="Runtime unit and self-validation tests",
                        scope=VerificationScope.RUNTIME,
                        module="runtime",
                        capability="runtime-verification",
                    ),
                ],
                workflows=["runtime"],
                scripts=["run_runtime_verification"],
                modules=[],
            ),
            "golden-regression": VerificationCapability(
                id="golden-regression",
                name="Golden Regression",
                description="Golden dataset regression",
                category=VerificationCategory.CAPABILITY,
                scopes=[VerificationScope.GOLDEN],
                requirements=[
                    VerificationRequirement(
                        id="golden-regression-test",
                        category=VerificationCategory.CAPABILITY,
                        severity=VerificationSeverity.HIGH,
                        description="Golden dataset regression tests",
                        scope=VerificationScope.GOLDEN,
                        module="backend/tests/golden",
                        capability="golden-regression",
                    ),
                ],
                workflows=["golden"],
                scripts=["run_golden_tests"],
                modules=[],
            ),
            "mutation-analysis": VerificationCapability(
                id="mutation-analysis",
                name="Mutation Analysis",
                description="Mutation testing for critical modules",
                category=VerificationCategory.MUTATION,
                scopes=[VerificationScope.MUTATION],
                requirements=[
                    VerificationRequirement(
                        id="mutation-run",
                        category=VerificationCategory.MUTATION,
                        severity=VerificationSeverity.MEDIUM,
                        description="Selective mutation testing on critical modules",
                        scope=VerificationScope.MUTATION,
                        module="backend/src/engines",
                        capability="mutation-analysis",
                    ),
                ],
                workflows=["mutation"],
                scripts=["run_mutation_selective"],
                modules=[],
            ),
            "e2e-tests": VerificationCapability(
                id="e2e-tests",
                name="End-to-End Tests",
                description="End-to-end browser tests",
                category=VerificationCategory.INTEGRATION,
                scopes=[VerificationScope.PLAYWRIGHT],
                requirements=[
                    VerificationRequirement(
                        id="e2e-playwright",
                        category=VerificationCategory.INTEGRATION,
                        severity=VerificationSeverity.HIGH,
                        description="Playwright E2E browser tests",
                        scope=VerificationScope.PLAYWRIGHT,
                        module="frontend/e2e",
                        capability="e2e-tests",
                    ),
                ],
                workflows=["playwright"],
                scripts=["run_playwright_tests"],
                modules=[],
            ),
        }

        for cap in default_capabilities.values():
            self._capabilities[cap.id] = cap

        for cap_id, cap_config in capabilities_config.items():
            if cap_id in self._capabilities:
                cap = self._capabilities[cap_id]
                merged = VerificationCapability(
                    id=cap.id,
                    name=cap_config.get("name", cap.name),
                    description=cap_config.get("description", cap.description),
                    category=VerificationCategory(
                        cap_config.get("category", cap.category.value)
                    ),
                    scopes=[
                        VerificationScope(s)
                        for s in cap_config.get("scopes", [s.value for s in cap.scopes])
                    ],
                    requirements=cap.requirements,
                    workflows=cap_config.get("workflows", cap.workflows),
                    scripts=cap_config.get("scripts", cap.scripts),
                    modules=cap_config.get("modules", cap.modules),
                    metadata=cap_config.get("metadata", cap.metadata),
                )
                self._capabilities[cap_id] = merged
            else:
                self._capabilities[cap_id] = VerificationCapability(
                    id=cap_id,
                    name=cap_config.get("name", cap_id),
                    description=cap_config.get("description", ""),
                    category=VerificationCategory(
                        cap_config.get("category", "capability")
                    ),
                    scopes=[
                        VerificationScope(s)
                        for s in cap_config.get("scopes", ["quick"])
                    ],
                    requirements=[],
                    workflows=cap_config.get("workflows", []),
                    scripts=cap_config.get("scripts", []),
                    modules=cap_config.get("modules", []),
                    metadata=cap_config.get("metadata", {}),
                )

    # Lookup methods

    def get_workflow(self, workflow_id: str) -> VerificationWorkflow | None:
        """Get workflow by ID."""
        self.load()
        return self._workflows.get(workflow_id)

    def get_workflows_by_scope(
        self, scope: VerificationScope
    ) -> list[VerificationWorkflow]:
        """Get all workflows for a scope."""
        self.load()
        return [wf for wf in self._workflows.values() if scope in wf.scopes]

    def get_workflows_by_capability(
        self, capability_id: str
    ) -> list[VerificationWorkflow]:
        """Get all workflows for a capability."""
        self.load()
        return [
            wf for wf in self._workflows.values() if capability_id in wf.capabilities
        ]

    def get_workflows_by_category(
        self, category: VerificationCategory
    ) -> list[VerificationWorkflow]:
        """Get all workflows for a category."""
        self.load()
        return [wf for wf in self._workflows.values() if wf.category == category]

    def get_script(self, script_id: str) -> VerificationScript | None:
        """Get script by ID."""
        self.load()
        return self._scripts.get(script_id)

    def get_scripts_by_scope(
        self, scope: VerificationScope
    ) -> list[VerificationScript]:
        """Get all scripts for a scope."""
        self.load()
        return [s for s in self._scripts.values() if s.scope == scope]

    def get_scripts_by_capability(self, capability_id: str) -> list[VerificationScript]:
        """Get all scripts for a capability."""
        self.load()
        return [s for s in self._scripts.values() if capability_id in s.capabilities]

    def get_scripts_by_category(
        self, category: VerificationCategory
    ) -> list[VerificationScript]:
        """Get all scripts for a category."""
        self.load()
        return [s for s in self._scripts.values() if s.category == category]

    def get_capability(self, capability_id: str) -> VerificationCapability | None:
        """Get capability by ID."""
        self.load()
        return self._capabilities.get(capability_id)

    def get_capabilities_by_scope(
        self, scope: VerificationScope
    ) -> list[VerificationCapability]:
        """Get all capabilities for a scope."""
        self.load()
        return [c for c in self._capabilities.values() if scope in c.scopes]

    def get_capabilities_by_category(
        self, category: VerificationCategory
    ) -> list[VerificationCapability]:
        """Get all capabilities for a category."""
        self.load()
        return [c for c in self._capabilities.values() if c.category == category]

    def get_capabilities_by_module(self, module: str) -> list[VerificationCapability]:
        """Get all capabilities for a module."""
        self.load()
        return [c for c in self._capabilities.values() if module in c.modules]

    def get_requirement(self, requirement_id: str) -> VerificationRequirement | None:
        """Get requirement by ID."""
        self.load()
        return self._requirements.get(requirement_id)

    def get_requirements_by_capability(
        self, capability_id: str
    ) -> list[VerificationRequirement]:
        """Get all requirements for a capability."""
        self.load()
        cap = self._capabilities.get(capability_id)
        if cap:
            return cap.requirements
        return []

    def get_requirements_by_scope(
        self, scope: VerificationScope
    ) -> list[VerificationRequirement]:
        """Get all requirements for a scope."""
        self.load()
        result = []
        for cap in self._capabilities.values():
            for req in cap.requirements:
                if req.scope == scope:
                    result.append(req)
        return result

    def get_requirements_by_category(
        self, category: VerificationCategory
    ) -> list[VerificationRequirement]:
        """Get all requirements for a category."""
        self.load()
        result = []
        for cap in self._capabilities.values():
            for req in cap.requirements:
                if req.category == category:
                    result.append(req)
        return result

    def get_all_workflows(self) -> list[VerificationWorkflow]:
        """Get all registered workflows."""
        self.load()
        return list(self._workflows.values())

    def get_all_scripts(self) -> list[VerificationScript]:
        """Get all registered scripts."""
        self.load()
        return list(self._scripts.values())

    def get_all_capabilities(self) -> list[VerificationCapability]:
        """Get all registered capabilities."""
        self.load()
        return list(self._capabilities.values())

    def get_all_categories(self) -> list[VerificationCategory]:
        """Get all registered categories."""
        self.load()
        return list(self._categories.keys())

    def get_all_scopes(self) -> list[VerificationScope]:
        """Get all registered scopes."""
        self.load()
        return list(self._scopes.keys())

    def get_all_modules(self) -> list[str]:
        """Get all registered modules."""
        self.load()
        return list(self._modules.keys())

    def validate(self) -> list[str]:
        """Validate registry consistency. Returns list of issues."""
        self.load()
        issues = []

        # Check for duplicate IDs
        workflow_ids = list(self._workflows.keys())
        if len(workflow_ids) != len(set(workflow_ids)):
            issues.append("Duplicate workflow IDs found")

        script_ids = list(self._scripts.keys())
        if len(script_ids) != len(set(script_ids)):
            issues.append("Duplicate script IDs found")

        capability_ids = list(self._capabilities.keys())
        if len(capability_ids) != len(set(capability_ids)):
            issues.append("Duplicate capability IDs found")

        # Check workflows reference valid scripts
        for wf in self._workflows.values():
            if wf.script and wf.script not in self._scripts:
                issues.append(
                    f"Workflow '{wf.id}' references unknown script '{wf.script}'"
                )

        # Check capabilities reference valid workflows/scripts
        for cap in self._capabilities.values():
            for wf_id in cap.workflows:
                if wf_id not in self._workflows:
                    issues.append(
                        f"Capability '{cap.id}' references unknown workflow '{wf_id}'"
                    )
            for script_id in cap.scripts:
                if script_id not in self._scripts:
                    issues.append(
                        f"Capability '{cap.id}' references unknown script '{script_id}'"
                    )

        # Check scopes referenced by workflows exist
        for wf in self._workflows.values():
            for scope in wf.scopes:
                if scope not in self._scopes:
                    issues.append(
                        f"Workflow '{wf.id}' references unknown scope '{scope.value}'"
                    )

        return issues

    def get_config(self) -> dict[str, Any]:
        """Get raw config."""
        self.load()
        return self._config.copy()


# Global registry instance
_registry: VerificationRegistry | None = None


def get_registry(config_path: Path | None = None) -> VerificationRegistry:
    """Get the global verification registry."""
    global _registry
    if _registry is None:
        _registry = VerificationRegistry(config_path)
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None
