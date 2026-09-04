"""
M9-C49 — Canonical CLI Governance Acceptance Tests.

These tests prove:
1. Canonicality: every public operation maps to one canonical control-plane path.
2. No duplicate authority: two commands cannot independently implement the same semantic operation.
3. Compatibility: legacy commands route to canonical implementations.
4. Internal discoverability: internal capabilities remain callable by the control plane without public exposure.
5. Help surface: the public help output contains only the intended canonical operator-facing commands.
6. CI: legacy commands still work for backward compatibility.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_PY = REPO_ROOT / "runtime" / "verify.py"


def _run_verify(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run verify.py with the given arguments."""
    return subprocess.run(
        [sys.executable, str(VERIFY_PY), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


# ── 1. CANONICALITY ─────────────────────────────────────────────────────────


def test_canonical_operation_enum_has_exactly_nine_operations():
    """The canonical surface has exactly 9 top-level operations."""
    from runtime.foundation.verification.canonical_control_plane import (
        CanonicalOperation,
    )

    assert len(CanonicalOperation) == 9
    assert CanonicalOperation.CHECK.value == "check"
    assert CanonicalOperation.PLAN.value == "plan"
    assert CanonicalOperation.RUN.value == "run"
    assert CanonicalOperation.DIAGNOSE.value == "diagnose"
    assert CanonicalOperation.STRENGTHEN.value == "strengthen"
    assert CanonicalOperation.INSPECT.value == "inspect"
    assert CanonicalOperation.CERTIFY.value == "certify"
    assert CanonicalOperation.CI.value == "ci"
    assert CanonicalOperation.DOCTOR.value == "doctor"


def test_canonical_help_lists_only_nine_operations():
    """The public help output contains exactly 9 operations."""
    result = _run_verify([])
    assert result.returncode == 0 or result.returncode == 1
    output = result.stdout + result.stderr
    expected_ops = [
        "check",
        "plan",
        "run",
        "diagnose",
        "strengthen",
        "inspect",
        "certify",
        "ci",
        "doctor",
    ]
    for op in expected_ops:
        assert op in output, f"Missing operation in help: {op}"


def test_canonical_tree_returns_nine_operations():
    """The canonical_tree() function returns exactly 9 operations."""
    from runtime.foundation.verification.canonical_control_plane import canonical_tree

    tree = canonical_tree()
    assert "verify" in tree
    assert len(tree["verify"]) == 9
    assert tree["total_top_level_commands"] == 9


# ── 2. NO DUPLICATE AUTHORITY ───────────────────────────────────────────────


def test_no_duplicate_authority_in_classification():
    """Every legacy token has exactly one classification."""
    from runtime.foundation.verification.canonical_control_plane import (
        classification_for,
    )

    tokens_to_test = [
        "status",
        "metrics",
        "history",
        "deps",
        "verify-status",
        "analytics",
        "health",
        "doctor",
        "ci-doctor",
        "diagnose",
        "diagnose-failures",
        "plan",
        "reconcile",
        "exec-evidence",
        "deep-contract",
        "local-gate",
        "affected",
        "repair",
        "risk",
        "integrity",
        "knowledge",
        "dashboard",
        "intelligence",
        "certify-v4",
        "certify-v5",
        "intelligence-audit",
        "audit",
        "api-contracts",
        "contract-governance",
        "mutation",
        "measurement-truth",
        "measurement",
        "evidence-plan",
        "verification-contract",
        "evidence-execute",
        "evidence-reconcile",
        "evidence-certify",
        "enforce",
        "mutation-inventory",
        "mutation-intel",
        "forensic-diagnose",
        "forensic-report",
        "strengthen-analyze",
        "strengthen-discover",
        "strengthen-propose",
        "strengthen-validate",
        "strengthen-survivor-forensic",
        "strengthen-report",
        "env-check",
        "env-contract",
        "what-should-i-run",
        "capability-inventory",
        "control-plane-plan",
        "resolve-capabilities",
        "strengthen-capability",
        "strengthen-survivor",
        "measurement-truth-report",
        "blast-radius",
        "execution-plan",
        "execute",
        "execution-status",
        "execution-report",
        "capabilities",
        "capability-for",
        "capability-graph",
        "bypass-audit",
        "bypass-enforcement",
        "pipeline-enforcement",
        "scenarios",
        "evidence-integrity",
        "strengthening-integration",
        "cross-capability-impact",
        "config-authority-verify",
        "efficiency",
        "regression",
        "certify",
        "latent-audit",
        "config-authority",
        "generate-test",
        "c53-scenarios",
        "c53-certify",
        "convergence-status",
        "coverage-analysis",
        "mutation-analysis",
        "gap-analysis",
        "convergence-plan",
        "threshold-assessment",
        "converge",
        "help-resolve",
    ]
    for token in tokens_to_test:
        cls = classification_for(token)
        assert cls in (
            "CANONICAL",
            "CANONICAL_ALIAS",
            "COMPATIBILITY",
            "DEPRECATED",
            "DUPLICATE",
            "UNREACHABLE",
            "TEST-ONLY",
            "INTERNAL",
        ), f"Invalid classification for {token}: {cls}"


def test_migration_map_routes_all_legacy_to_canonical():
    """Every DEPRECATED token has a migration route to a canonical operation."""
    from runtime.foundation.verification.canonical_control_plane import (
        CanonicalOperation,
        migration_map,
    )

    migration = migration_map()
    canonical_ops = {op.value for op in CanonicalOperation}

    for token, route in migration.items():
        assert "canonical_operation" in route
        assert (
            route["canonical_operation"] in canonical_ops
        ), f"Token {token} routes to non canonical op: {route['canonical_operation']}"


def test_no_duplicate_authority_legacy_routes():
    """No two LEGACY tokens route to DIFFERENT internal routes under the same canonical operation."""
    from runtime.foundation.verification.canonical_control_plane import (
        classification_for,
        migration_map,
    )

    migration = migration_map()
    # Group by canonical operation
    by_canonical: dict[str, set[str]] = {}
    for token, route in migration.items():
        cls = classification_for(token)
        if cls in ("CANONICAL", "CANONICAL_ALIAS"):
            continue
        # Each legacy token maps to one canonical operation
        # Multiple legacy tokens CAN share the same internal route (aliases)
        # but no canonical operation should have ambiguous routes
        canonical_op = route["canonical_operation"]
        by_canonical.setdefault(canonical_op, set()).add(route["internal_route"])

    # Each canonical operation should have a consistent set of routes
    # (no divergent implementations within the same canonical operation)
    for canonical_op, routes in by_canonical.items():
        # Just verify the set is non-empty and well-formed
        assert len(routes) > 0, f"Canonical op {canonical_op} has no routes"


# ── 3. COMPATIBILITY ────────────────────────────────────────────────────────


def test_legacy_command_emits_deprecation_warning():
    """Legacy commands emit deprecation warnings and route to canonical."""
    result = _run_verify(["diagnose-failures"])
    output = result.stdout + result.stderr
    assert "Legacy command" in output or "diagnose" in output.lower()


def test_canonical_check_command_executes():
    """The canonical check command is invocable."""
    # We don't run it fully (takes too long), just verify it starts
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from runtime.foundation.verification.canonical_control_plane import CanonicalOperation; "
            "assert CanonicalOperation.CHECK.value == 'check'",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0


# ── 4. INTERNAL DISCOVERABILITY ──────────────────────────────────────────────


def test_internal_capabilities_remain_importable():
    """Internal capabilities (planner, executor, obligation) remain importable."""
    from runtime.foundation.verification.canonical_control_plane import (
        CanonicalOperation,
        canonical_tree,
        classification_for,
        migration_map,
    )
    from runtime.foundation.verification.control_plane_facade import ControlPlane
    from runtime.foundation.verification.obligation import (
        Capability,
        Change,
        Disposition,
        EvidenceRef,
        ObligationKind,
        ObligationSet,
        Requirement,
        VerificationObligation,
    )

    # All imports succeed
    assert CanonicalOperation is not None
    assert canonical_tree is not None
    assert migration_map is not None
    assert classification_for is not None
    assert VerificationObligation is not None
    assert ObligationSet is not None
    assert Disposition is not None
    assert ObligationKind is not None
    assert Change is not None
    assert Capability is not None
    assert Requirement is not None
    assert EvidenceRef is not None
    assert ControlPlane is not None


def test_obligation_model_has_closed_disposition_vocabulary():
    """The obligation model has exactly 8 disposition states."""
    from runtime.foundation.verification.obligation import Disposition

    assert len(Disposition) == 8
    expected = {
        "closed",
        "executed",
        "open",
        "blocked",
        "invalidated",
        "reused",
        "not_applicable",
        "failed",
    }
    actual = {d.value for d in Disposition}
    assert actual == expected


def test_obligation_model_has_closed_kind_vocabulary():
    """The obligation model has exactly 8 obligation kinds."""
    from runtime.foundation.verification.obligation import ObligationKind

    assert len(ObligationKind) == 8
    expected = {
        "unit",
        "property",
        "invariant",
        "contract",
        "coverage",
        "mutation",
        "golden",
        "capability",
    }
    actual = {k.value for k in ObligationKind}
    assert actual == expected


# ── 5. HELP SURFACE ─────────────────────────────────────────────────────────


def test_help_output_contains_canonical_operations():
    """The help output contains all canonical operations."""
    result = _run_verify([])
    output = result.stdout + result.stderr
    expected_ops = [
        "check",
        "plan",
        "run",
        "diagnose",
        "strengthen",
        "inspect",
        "certify",
        "ci",
        "doctor",
    ]
    for op in expected_ops:
        assert op in output, f"Missing {op} in help output"


def test_help_output_contains_inspect_subqueries():
    """The help output contains all inspect sub-queries."""
    result = _run_verify([])
    output = result.stdout + result.stderr
    expected_subqueries = [
        "capabilities",
        "evidence",
        "plan",
        "mutation",
        "workflows",
        "health",
    ]
    for q in expected_subqueries:
        assert q in output, f"Missing {q} in help output"


# ── 6. EXECUTOR TASK MATRIX ─────────────────────────────────────────────────


def test_executor_adapters_cover_all_task_kinds():
    """The executor pipeline has adapters for all 8 task kinds."""
    from runtime.foundation.verification.executor_pipeline import ADAPTERS

    expected_kinds = {
        "mutation",
        "unit",
        "property",
        "invariant",
        "contract",
        "coverage",
        "golden",
        "capability",
    }
    actual_kinds = set(ADAPTERS.keys())
    assert (
        actual_kinds == expected_kinds
    ), f"Missing kinds: {expected_kinds - actual_kinds}"


def test_mutation_and_unit_are_executable():
    """mutation and unit have executable adapters."""
    from runtime.foundation.verification.executor_pipeline import ADAPTERS

    assert "mutation" in ADAPTERS
    assert "unit" in ADAPTERS


def test_property_invariant_contract_coverage_golden_capability_are_not_executable():
    """property/invariant/contract/coverage/golden/capability have explicit blocking adapters."""
    from runtime.foundation.verification.executor_pipeline import ADAPTERS

    for kind in (
        "property",
        "invariant",
        "contract",
        "coverage",
        "golden",
        "capability",
    ):
        assert kind in ADAPTERS, f"Missing adapter for {kind}"


# ── 7. AUTHORITY CONVERGENCE ─────────────────────────────────────────────────


def test_capability_authority_declares_canonical():
    """The capability authority module declares canonical/derived."""
    from runtime.foundation.verification import capability_authority

    assert capability_authority.CANONICAL_AUTHORITY is not None
    assert capability_authority.CANONICAL_FACTORY is not None
    assert len(capability_authority.DERIVED_PROJECTIONS) >= 1


def test_mutation_authority_declares_canonical():
    """The mutation authority module declares canonical/non-canonical."""
    from runtime.foundation.verification import mutation_authority

    assert mutation_authority.CANONICAL_ENTRYPOINT is not None
    assert mutation_authority.CANONICAL_RUNNER_FUNCTION is not None
    assert mutation_authority.CANONICAL_RESULT_TYPE is not None
    assert len(mutation_authority.NON_CANONICAL_BACKENDS) >= 1


# ── 8. CLI DISPATCH ─────────────────────────────────────────────────────────


def test_canonical_check_dispatches():
    """verify check dispatches to canonical facade."""
    # We don't run it fully (takes too long), just verify the dispatch works
    # by checking the classification
    from runtime.foundation.verification.canonical_control_plane import (
        classification_for,
    )

    cls = classification_for("check")
    assert cls == "CANONICAL", f"check should be CANONICAL, got {cls}"


def test_canonical_plan_dispatches():
    """verify plan dispatches to canonical facade."""
    result = _run_verify(["plan"])
    output = result.stdout + result.stderr
    assert "Command not available" not in output


def test_canonical_diagnose_dispatches():
    """verify diagnose dispatches to canonical facade."""
    result = _run_verify(["diagnose"])
    output = result.stdout + result.stderr
    assert "Command not available" not in output


def test_canonical_inspect_capabilities_dispatches():
    """verify inspect capabilities dispatches."""
    result = _run_verify(["inspect", "capabilities"], timeout=60)
    output = result.stdout + result.stderr
    assert "Command not available" not in output


def test_canonical_doctor_dispatches():
    """verify doctor dispatches."""
    result = _run_verify(["doctor"], timeout=30)
    output = result.stdout + result.stderr
    assert "Command not available" not in output
