"""
Scope Resolution — Phase 5

Deterministic scope resolution from file paths.
Given a file path, determine which scopes are affected and WHY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.foundation.verification.models.model import VerificationCategory, VerificationScope


@dataclass(frozen=True, slots=True)
class ScopeReason:
    """Reason a scope is affected by a file."""

    scope: VerificationScope
    reason: str
    category: VerificationCategory | None = None
    module: str | None = None
    capability: str | None = None


@dataclass(frozen=True, slots=True)
class ScopeResolution:
    """Result of scope resolution for a file."""

    file_path: str
    scopes: list[VerificationScope]
    reasons: list[ScopeReason]
    modules: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)


class ScopeResolver:
    """
    Deterministic scope resolver.

    Given a file path, determines which verification scopes are affected and WHY.
    """

    # Module to capability mapping
    MODULE_CAPABILITIES = {
        "backend/src/loan_engine": ["loan-engine"],
        "backend/src/reconciliation": ["reconciliation"],
        "backend/src/ledger": ["ledger"],
        "backend/src/accounting": ["accounting"],
        "backend/src/reporting": ["reporting"],
        "backend/src/instruments": ["instruments"],
        "backend/src/risk": ["risk"],
        "backend/src/compliance": ["compliance"],
        "backend/src/api": ["api"],
        "backend/src/auth": ["auth"],
        "backend/src/migrations": ["migrations"],
        "frontend/src/components": ["frontend"],
        "frontend/src/pages": ["frontend"],
        "frontend/src/services": ["frontend"],
    }

    # Category to scope mapping
    CATEGORY_SCOPES = {
        VerificationCategory.CONTRACT: [VerificationScope.CONTRACTS],
        VerificationCategory.PROPERTY: [VerificationScope.PROPERTY],
        VerificationCategory.INVARIANT: [VerificationScope.CONTRACTS],
        VerificationCategory.CAPABILITY: [VerificationScope.BACKEND, VerificationScope.FRONTEND],
        VerificationCategory.MUTATION: [VerificationScope.MUTATION],
        VerificationCategory.INTEGRATION: [VerificationScope.INTEGRATION],
        VerificationCategory.MIGRATION: [VerificationScope.MIGRATION],
        VerificationCategory.ARCHITECTURAL: [VerificationScope.REPOSITORY],
        VerificationCategory.PERFORMANCE: [VerificationScope.INTEGRATION, VerificationScope.REPOSITORY],
        VerificationCategory.SECURITY: [VerificationScope.REPOSITORY],
    }

    def resolve_file(self, file_path: str) -> ScopeResolution:
        """Resolve scopes for a single file path."""
        norm_path = file_path.replace("\\", "/")
        reasons = []
        scopes = set()
        modules = set()
        capabilities = set()

        # Backend source files
        if norm_path.startswith("backend/src/"):
            scopes.add(VerificationScope.BACKEND)
            scopes.add(VerificationScope.CONTRACTS)
            reasons.append(ScopeReason(
                scope=VerificationScope.BACKEND,
                reason="Backend source file",
                category=VerificationCategory.CAPABILITY,
            ))
            reasons.append(ScopeReason(
                scope=VerificationScope.CONTRACTS,
                reason="Backend code requires contract verification",
                category=VerificationCategory.CONTRACT,
            ))

            # Extract module
            parts = norm_path.split("/")
            if len(parts) >= 3:
                module = "/".join(parts[:3])
                modules.add(module)

                # Check for specific capabilities
                if "loan_engine" in norm_path:
                    scopes.add(VerificationScope.PROPERTY)
                    reasons.append(ScopeReason(
                        scope=VerificationScope.PROPERTY,
                        reason="Loan engine requires property-based testing",
                        category=VerificationCategory.PROPERTY,
                        module=module,
                        capability="loan-engine",
                    ))
                    capabilities.add("loan-engine")

                if "reconciliation" in norm_path:
                    scopes.add(VerificationScope.PROPERTY)
                    reasons.append(ScopeReason(
                        scope=VerificationScope.PROPERTY,
                        reason="Reconciliation engine requires property-based testing",
                        category=VerificationCategory.PROPERTY,
                        module=module,
                        capability="reconciliation",
                    ))
                    capabilities.add("reconciliation")

                if "ledger" in norm_path or "accounting" in norm_path:
                    reasons.append(ScopeReason(
                        scope=VerificationScope.CONTRACTS,
                        reason="Ledger/accounting code requires invariant verification",
                        category=VerificationCategory.INVARIANT,
                        module=module,
                        capability="ledger" if "ledger" in norm_path else "accounting",
                    ))
                    capabilities.add("ledger" if "ledger" in norm_path else "accounting")

                if "api" in norm_path or "routes" in norm_path:
                    scopes.add(VerificationScope.INTEGRATION)
                    reasons.append(ScopeReason(
                        scope=VerificationScope.INTEGRATION,
                        reason="API routes require integration testing",
                        category=VerificationCategory.INTEGRATION,
                        module=module,
                        capability="api",
                    ))
                    capabilities.add("api")

                if "migrations" in norm_path or "alembic" in norm_path:
                    scopes.add(VerificationScope.MIGRATION)
                    reasons.append(ScopeReason(
                        scope=VerificationScope.MIGRATION,
                        reason="Database migration changes require migration verification",
                        category=VerificationCategory.MIGRATION,
                        module=module,
                        capability="migrations",
                    ))
                    capabilities.add("migrations")

                if "risk" in norm_path or "compliance" in norm_path:
                    scopes.add(VerificationScope.INTEGRATION)
                    reasons.append(ScopeReason(
                        scope=VerificationScope.INTEGRATION,
                        reason="Risk/compliance modules require integration verification",
                        category=VerificationCategory.INTEGRATION,
                        module=module,
                        capability="risk" if "risk" in norm_path else "compliance",
                    ))
                    capabilities.add("risk" if "risk" in norm_path else "compliance")

        # Frontend source files
        elif norm_path.startswith("frontend/src/"):
            scopes.add(VerificationScope.FRONTEND)
            scopes.add(VerificationScope.CONTRACTS)
            reasons.append(ScopeReason(
                scope=VerificationScope.FRONTEND,
                reason="Frontend source file",
                category=VerificationCategory.CAPABILITY,
            ))
            reasons.append(ScopeReason(
                scope=VerificationScope.CONTRACTS,
                reason="Frontend changes may affect API contracts",
                category=VerificationCategory.CONTRACT_FRONTEND,
            ))

            parts = norm_path.split("/")
            if len(parts) >= 3:
                module = "/".join(parts[:3])
                modules.add(module)
                capabilities.add("frontend")

        # Test files
        elif norm_path.startswith("backend/tests/"):
            if "property" in norm_path:
                scopes.add(VerificationScope.PROPERTY)
                reasons.append(ScopeReason(
                    scope=VerificationScope.PROPERTY,
                    reason="Property test file",
                    category=VerificationCategory.PROPERTY,
                ))
            elif "contract" in norm_path:
                scopes.add(VerificationScope.CONTRACTS)
                reasons.append(ScopeReason(
                    scope=VerificationScope.CONTRACTS,
                    reason="Contract test file",
                    category=VerificationCategory.CONTRACT,
                ))
            elif "invariant" in norm_path:
                scopes.add(VerificationScope.CONTRACTS)
                reasons.append(ScopeReason(
                    scope=VerificationScope.CONTRACTS,
                    reason="Invariant test file",
                    category=VerificationCategory.INVARIANT,
                ))
            elif "mutation" in norm_path:
                scopes.add(VerificationScope.MUTATION)
                reasons.append(ScopeReason(
                    scope=VerificationScope.MUTATION,
                    reason="Mutation test file",
                    category=VerificationCategory.MUTATION,
                ))
            elif "integration" in norm_path or "e2e" in norm_path:
                scopes.add(VerificationScope.INTEGRATION)
                reasons.append(ScopeReason(
                    scope=VerificationScope.INTEGRATION,
                    reason="Integration test file",
                    category=VerificationCategory.INTEGRATION,
                ))
            else:
                scopes.add(VerificationScope.BACKEND)
                reasons.append(ScopeReason(
                    scope=VerificationScope.BACKEND,
                    reason="Backend test file",
                    category=VerificationCategory.CAPABILITY,
                ))

        elif norm_path.startswith("frontend/tests/"):
            scopes.add(VerificationScope.FRONTEND)
            scopes.add(VerificationScope.CONTRACTS)
            reasons.append(ScopeReason(
                scope=VerificationScope.FRONTEND,
                reason="Frontend test file",
                category=VerificationCategory.CAPABILITY,
            ))

        # Config files affect full repo
        elif any(norm_path.endswith(ext) for ext in (".yaml", ".yml", ".toml", ".ini")):
            if any(norm_path.endswith(f) for f in ("pyproject.toml", "package.json", "tsconfig.json", "requirements.txt", "setup.py", "setup.cfg")):
                scopes.add(VerificationScope.REPOSITORY)
                reasons.append(ScopeReason(
                    scope=VerificationScope.REPOSITORY,
                    reason="Root configuration file affects entire repository",
                    category=VerificationCategory.ARCHITECTURAL,
                ))

        # Scripts and workflows
        elif norm_path.startswith(".github/workflows/") or norm_path.startswith(".github/scripts/"):
            scopes.add(VerificationScope.REPOSITORY)
            reasons.append(ScopeReason(
                scope=VerificationScope.REPOSITORY,
                reason="CI/CD workflow or script affects entire verification pipeline",
                category=VerificationCategory.ARCHITECTURAL,
            ))

        return ScopeResolution(
            file_path=file_path,
            scopes=list(scopes),
            reasons=reasons,
            modules=list(modules),
            capabilities=list(capabilities),
        )

    def resolve_files(self, file_paths: list[str]) -> list[ScopeResolution]:
        """Resolve scopes for multiple files."""
        return [self.resolve_file(f) for f in file_paths]

    def get_affected_scopes(self, file_paths: list[str]) -> list[VerificationScope]:
        """Get all affected scopes for a list of files."""
        all_scopes = set()
        for f in file_paths:
            res = self.resolve_file(f)
            all_scopes.update(res.scopes)
        return list(all_scopes)

    def get_affected_capabilities(self, file_paths: list[str]) -> list[str]:
        """Get all affected capabilities for a list of files."""
        all_caps = set()
        for f in file_paths:
            res = self.resolve_file(f)
            all_caps.update(res.capabilities)
        return list(all_caps)

    def get_affected_modules(self, file_paths: list[str]) -> list[str]:
        """Get all affected modules for a list of files."""
        all_modules = set()
        for f in file_paths:
            res = self.resolve_file(f)
            all_modules.update(res.modules)
        return list(all_modules)

    def explain_scope(self, scope: VerificationScope, file_paths: list[str]) -> str:
        """Explain why a scope is affected by given files."""
        lines = [f"Scope: {scope.value}"]
        lines.append("=" * 50)
        lines.append("")

        for f in file_paths:
            res = self.resolve_file(f)
            if scope in res.scopes:
                lines.append(f"File: {f}")
                for reason in res.reasons:
                    if reason.scope == scope:
                        lines.append(f"  - {reason.reason}")
                        if reason.category:
                            lines.append(f"    Category: {reason.category.value}")
                        if reason.module:
                            lines.append(f"    Module: {reason.module}")
                        if reason.capability:
                            lines.append(f"    Capability: {reason.capability}")
                lines.append("")

        if len(lines) == 3:  # Only header
            lines.append(f"No files directly affect scope {scope.value}")

        return "\n".join(lines)

    def get_scope_dependencies(self, scope: VerificationScope) -> list[VerificationScope]:
        """Get scopes that must run before the given scope."""
        hierarchy = {
            VerificationScope.QUICK: [],
            VerificationScope.BACKEND: [VerificationScope.QUICK],
            VerificationScope.FRONTEND: [VerificationScope.QUICK],
            VerificationScope.CONTRACTS: [VerificationScope.QUICK],
            VerificationScope.PROPERTY: [VerificationScope.QUICK, VerificationScope.BACKEND, VerificationScope.CONTRACTS],
            VerificationScope.MUTATION: [VerificationScope.QUICK, VerificationScope.BACKEND],
            VerificationScope.INTEGRATION: [VerificationScope.QUICK, VerificationScope.BACKEND, VerificationScope.CONTRACTS],
            VerificationScope.MIGRATION: [VerificationScope.QUICK, VerificationScope.BACKEND],
            VerificationScope.REPOSITORY: [
                VerificationScope.QUICK,
                VerificationScope.BACKEND,
                VerificationScope.FRONTEND,
                VerificationScope.CONTRACTS,
                VerificationScope.PROPERTY,
                VerificationScope.MUTATION,
                VerificationScope.INTEGRATION,
                VerificationScope.MIGRATION,
            ],
            VerificationScope.FULL: list(VerificationScope),
        }
        return hierarchy.get(scope, [])


# Global resolver instance
_resolver: ScopeResolver | None = None


def get_scope_resolver() -> ScopeResolver:
    """Get the global scope resolver."""
    global _resolver
    if _resolver is None:
        _resolver = ScopeResolver()
    return _resolver


def reset_scope_resolver() -> None:
    """Reset the global resolver (for testing)."""
    global _resolver
    _resolver = None


SCOPE_EXPLANATIONS = {
    VerificationScope.QUICK: "Fast local checks (lint, typecheck, fast tests)",
    VerificationScope.BACKEND: "Backend unit/contract tests, API tests",
    VerificationScope.FRONTEND: "Frontend unit tests, component tests",
    VerificationScope.CONTRACTS: "Contract tests (API schemas, invariants)",
    VerificationScope.PROPERTY: "Property-based testing (loan engine, reconciliation)",
    VerificationScope.MUTATION: "Mutation testing (backend)",
    VerificationScope.INTEGRATION: "Integration/E2E tests",
    VerificationScope.MIGRATION: "Database migration verification",
    VerificationScope.REPOSITORY: "Full repository verification (all scopes)",
    VerificationScope.FULL: "Complete verification including performance/security",
}


def explain_loan_engine() -> str:
    """Example: why loan engine affects multiple scopes."""
    return """
Loan Engine (backend/src/loan_engine/) affects:

1. BACKEND - Core backend module
2. CONTRACTS - API contracts for loan operations
3. PROPERTY - Mathematical properties of loan calculations (interest, amortization)
4. INTEGRATION - End-to-end loan workflows
5. REPOSITORY - Critical financial component affects whole repo

Reason: Loan engine handles financial calculations that must satisfy
mathematical properties (rounding, amortization schedules, interest
accrual) AND integrate with ledger/accounting invariants.
"""


def explain_frontend_api_change() -> str:
    """Example: frontend API change."""
    return """
Frontend API service change (frontend/src/services/api.ts) affects:

1. FRONTEND - Frontend code change
2. CONTRACTS - May change API contract expectations
3. INTEGRATION - Frontend-backend integration tests
4. REPOSITORY - Cross-cutting change

Reason: Frontend service layer changes can affect both UI behavior
and API contract expectations.
"""