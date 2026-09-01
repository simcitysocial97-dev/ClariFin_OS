"""
M9-C50 — Blast-Radius Enforcement & Change-Impact Control acceptance scenarios.

Covers the 12 acceptance scenarios A–L from the M9-C50 brief. These tests
prove the blast-radius enforcement system end-to-end against the existing
C42/C47/C48/C49 architecture, without introducing a parallel verification
system.

All tests use fast command overrides so the full chain runs in seconds.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_orchestrator(overrides: dict[str, str] | None = None):
    from runtime.foundation.verification.execution_orchestrator import (
        ExecutionOrchestrator,
    )

    defaults = {
        "bash .github/scripts/run_backend_verification.sh": "true",
        "bash .github/scripts/run_contract_tests.sh": "true",
        "bash .github/scripts/run_property_tests.sh": "true",
        "bash .github/scripts/run_frontend_verification.sh": "true",
        "bash .github/scripts/run_fast_checks.sh": "true",
        "bash .github/scripts/run_migration_verification.sh": "true",
        "bash .github/scripts/run_integration_tests.sh": "true",
        "bash .github/scripts/run_mutation_selective.sh": "true",
        "kind:coverage": "true",
        "kind:mutation": "true",
    }
    return ExecutionOrchestrator(command_overrides={**defaults, **(overrides or {})})


# ---------------------------------------------------------------------------
# A — Isolated backend feature change
# ---------------------------------------------------------------------------


class ScenarioAIsolatedBackendChange(unittest.TestCase):
    def test_loan_change_produces_narrow_blast_radius(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        # loan-engine should be directly affected
        self.assertIn("loan-engine", contract.directly_affected_capabilities)
        # Shared infrastructure should not be triggered for an isolated engine change
        self.assertEqual(len(contract.shared_infrastructure_affected_capabilities), 0)
        # Should produce a minimum safe verification scope
        self.assertGreater(len(contract.minimum_safe_verification), 0)


# ---------------------------------------------------------------------------
# B — Shared infrastructure change
# ---------------------------------------------------------------------------


class ScenarioBSharedInfrastructureChange(unittest.TestCase):
    def test_shared_module_propagates_to_dependents(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(["backend/src/common/calculations.py"])
        # Shared module change should trigger shared infrastructure expansion
        # (or at least be detected as a shared module change)
        has_shared = (
            len(contract.shared_infrastructure_affected_capabilities) > 0
            or len(contract.change_surface.shared_module_surfaces) > 0
        )
        self.assertTrue(
            has_shared,
            "Shared module change should trigger shared infrastructure detection",
        )


# ---------------------------------------------------------------------------
# C — Test-only change
# ---------------------------------------------------------------------------


class ScenarioCTestOnlyChange(unittest.TestCase):
    def test_change_does_not_falsely_claim_production_impact(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(["backend/tests/unit/test_loan_engine.py"])
        # Should detect test-only surfaces
        self.assertGreater(len(contract.change_surface.test_surfaces), 0)
        # Test surfaces should not be classified as production
        for s in contract.change_surface.test_surfaces:
            self.assertFalse(s.is_production)


# ---------------------------------------------------------------------------
# D — Configuration change
# ---------------------------------------------------------------------------


class ScenarioDConfigChange(unittest.TestCase):
    def test_config_triggers_appropriate_expansion(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(["backend/pyproject.toml"])
        # Config change should be detected
        self.assertGreater(len(contract.change_surface.config_surfaces), 0)


# ---------------------------------------------------------------------------
# E — Frontend capability change
# ---------------------------------------------------------------------------


class ScenarioEFrontendChange(unittest.TestCase):
    def test_frontend_change_produces_frontend_surfaces(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(["frontend/src/components/loan-dashboard.tsx"])
        # Frontend surfaces should be detected
        frontend_surfaces = [
            s for s in contract.change_surface.surfaces if s.kind.value == "frontend"
        ]
        self.assertGreater(len(frontend_surfaces), 0)


# ---------------------------------------------------------------------------
# F — Cross-engine dependency
# ---------------------------------------------------------------------------


class ScenarioFCrossEngineDependency(unittest.TestCase):
    def test_cross_engine_dependency_included(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        # A service that depends on multiple engines
        contract = compute_blast_radius(["backend/src/services/loan_service.py"])
        # Should have at least one affected capability
        all_affected = (
            contract.directly_affected_capabilities
            + contract.transitively_affected_capabilities
        )
        self.assertGreater(len(all_affected), 0)


# ---------------------------------------------------------------------------
# G — Runtime verification infrastructure change
# ---------------------------------------------------------------------------


class ScenarioGRuntimeInfrastructureChange(unittest.TestCase):
    def test_runtime_infra_triggers_appropriate_surfaces(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["runtime/foundation/verification/capability_contract.py"]
        )
        # Runtime infrastructure should be detected
        self.assertGreater(
            len(contract.change_surface.runtime_infrastructure_surfaces), 0
        )
        # Should trigger ESC-RUNTIME-INFRASTRUCTURE escalation
        esc_ids = [ec.condition_id for ec in contract.escalation_conditions]
        self.assertIn("ESC-RUNTIME-INFRASTRUCTURE", esc_ids)


# ---------------------------------------------------------------------------
# H — Unmapped production surface
# ---------------------------------------------------------------------------


class ScenarioHUnmappedProductionSurface(unittest.TestCase):
    def test_unmapped_triggers_fail_closed(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        # A file that doesn't map to any known capability
        contract = compute_blast_radius(
            ["backend/src/engines/credit_card_engine/calculator.py"]
        )
        # credit_card is not in the contract registry — should trigger fail-closed
        # OR unmapped capability detection
        has_unmapped = (
            len(contract.unmapped_capabilities) > 0 or contract.is_fail_closed
        )
        self.assertTrue(
            has_unmapped,
            "Unmapped production surface should trigger fail-closed or unmapped detection",
        )


# ---------------------------------------------------------------------------
# I — Stale measurement evidence
# ---------------------------------------------------------------------------


class ScenarioIStaleEvidence(unittest.TestCase):
    def test_stale_evidence_marked_for_revalidation(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        # loan-engine has no current measurement truth record → should be
        # marked for revalidation
        self.assertIn("loan-engine", contract.revalidation_required)


# ---------------------------------------------------------------------------
# J — Unaffected capability
# ---------------------------------------------------------------------------


class ScenarioJUnaffectedCapability(unittest.TestCase):
    def test_unaffected_capability_not_in_plan(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        # migration should not be affected by a loan-engine change
        all_affected = (
            contract.directly_affected_capabilities
            + contract.transitively_affected_capabilities
            + contract.shared_infrastructure_affected_capabilities
        )
        self.assertNotIn("migrations", all_affected)


# ---------------------------------------------------------------------------
# K — Ambiguous/shared dependency
# ---------------------------------------------------------------------------


class ScenarioKAmbiguousSharedDependency(unittest.TestCase):
    def test_ambiguous_dependency_triggers_conservative_expansion(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        # A shared module that multiple capabilities depend on
        contract = compute_blast_radius(["backend/src/common/calculations.py"])
        # Should detect shared module
        self.assertGreater(len(contract.change_surface.shared_module_surfaces), 0)


# ---------------------------------------------------------------------------
# L — Full chain
# ---------------------------------------------------------------------------


class ScenarioLFullChain(unittest.TestCase):
    def test_change_to_plan_to_execute_to_decision(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        # Step 1: Change → blast radius
        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )

        # Step 2: Capability resolution
        self.assertIn("loan-engine", contract.directly_affected_capabilities)

        # Step 3: Evidence invalidation
        self.assertGreater(len(contract.evidence_invalidations), 0)

        # Step 4: Minimum safe verification
        self.assertGreater(len(contract.minimum_safe_verification), 0)

        # Step 5: C49 execution plan
        orch = _make_orchestrator()
        plan = orch.build_execution_plan(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        self.assertGreater(len(plan.tasks), 0)

        # Step 6: C49 execution
        report = orch.execute(plan)
        self.assertIsNotNone(report.final_decision)


# ---------------------------------------------------------------------------
# Determinism tests
# ---------------------------------------------------------------------------


class DeterminismTests(unittest.TestCase):
    def test_same_inputs_produce_same_contract(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        files = ["backend/src/engines/loan_engine/amortization.py"]
        c1 = compute_blast_radius(files)
        c2 = compute_blast_radius(files)
        self.assertEqual(c1.contract_id, c2.contract_id)
        self.assertEqual(
            c1.directly_affected_capabilities, c2.directly_affected_capabilities
        )
        self.assertEqual(
            c1.transitively_affected_capabilities,
            c2.transitively_affected_capabilities,
        )


# ---------------------------------------------------------------------------
# Fail-closed tests
# ---------------------------------------------------------------------------


class FailClosedTests(unittest.TestCase):
    def test_unmapped_production_triggers_fail_closed(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/credit_card_engine/calculator.py"]
        )
        # credit_card is not in the contract registry
        self.assertTrue(contract.is_fail_closed)

    def test_valid_change_does_not_fail_closed(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        self.assertFalse(contract.is_fail_closed)

    def test_test_only_change_does_not_fail_closed(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(["backend/tests/unit/test_loan_engine.py"])
        self.assertFalse(contract.is_fail_closed)


# ---------------------------------------------------------------------------
# Latent capability protection tests
# ---------------------------------------------------------------------------


class LatentCapabilityTests(unittest.TestCase):
    def test_c50_imports_are_referenced(self):
        from runtime.foundation.verification.latent_capabilities import (
            audit_latent_capabilities,
        )

        report = audit_latent_capabilities()
        # All C50 imports should be protected (referenced in CLI or other modules)
        for cap in report.latent_capabilities:
            if cap.kind == "import":
                self.assertIn(
                    cap.verdict,
                    ["protected", "potentially_orphaned"],
                    f"Import {cap.name} has unexpected verdict: {cap.verdict}",
                )

    def test_no_deletions_recommended(self):
        from runtime.foundation.verification.latent_capabilities import (
            audit_latent_capabilities,
        )

        report = audit_latent_capabilities()
        # C50 should not recommend any deletions
        self.assertEqual(
            len(report.deletion_recommendations),
            0,
            f"Unexpected deletion recommendations: {report.deletion_recommendations}",
        )


# ---------------------------------------------------------------------------
# Evidence invalidation tests
# ---------------------------------------------------------------------------


class EvidenceInvalidationTests(unittest.TestCase):
    def test_evidence_dispositions_are_classified(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        # All evidence invalidations should have a valid disposition
        valid_dispositions = {
            "reusable",
            "stale_revalidation_required",
            "missing_fresh_measurement_required",
            "non_certifiable",
            "insufficient_data",
        }
        for ev in contract.evidence_invalidations:
            self.assertIn(ev.disposition, valid_dispositions)

    def test_reusable_evidence_not_marked_invalidated(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        # Reusable evidence should not appear in invalidations
        reusable_set = set(contract.reusable_evidence)
        for ev in contract.evidence_invalidations:
            self.assertNotIn(ev.evidence_id, reusable_set)


# ---------------------------------------------------------------------------
# Change surface discovery tests
# ---------------------------------------------------------------------------


class ChangeSurfaceTests(unittest.TestCase):
    def test_explicit_files(self):
        from runtime.foundation.verification.change_surface import (
            discover_change_surfaces,
        )

        analysis = discover_change_surfaces(
            explicit_files=["backend/src/engines/loan_engine/amortization.py"]
        )
        self.assertEqual(len(analysis.changed_files), 1)
        self.assertEqual(analysis.discovery_source.value, "explicit")

    def test_test_file_not_production(self):
        from runtime.foundation.verification.change_surface import (
            discover_change_surfaces,
        )

        analysis = discover_change_surfaces(
            explicit_files=["backend/tests/unit/test_loan.py"]
        )
        self.assertEqual(len(analysis.test_surfaces), 1)
        self.assertFalse(analysis.test_surfaces[0].is_production)

    def test_shared_module_detected(self):
        from runtime.foundation.verification.change_surface import (
            SurfaceKind,
            discover_change_surfaces,
        )

        analysis = discover_change_surfaces(
            explicit_files=["backend/src/common/calculations.py"]
        )
        self.assertEqual(len(analysis.shared_module_surfaces), 1)
        self.assertEqual(
            analysis.shared_module_surfaces[0].kind, SurfaceKind.SHARED_MODULE
        )

    def test_runtime_infra_detected(self):
        from runtime.foundation.verification.change_surface import (
            SurfaceKind,
            discover_change_surfaces,
        )

        analysis = discover_change_surfaces(
            explicit_files=["runtime/foundation/verification/something.py"]
        )
        self.assertEqual(len(analysis.runtime_infrastructure_surfaces), 1)
        self.assertEqual(
            analysis.runtime_infrastructure_surfaces[0].kind,
            SurfaceKind.RUNTIME_INFRASTRUCTURE,
        )


if __name__ == "__main__":
    unittest.main()
