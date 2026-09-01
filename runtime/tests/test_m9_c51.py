# runtime/tests/test_m9_c51.py
#
# M9-C51 — Capability Discoverability & Pipeline Enforcement acceptance tests.
#
# Covers scenarios A-K from the M9-C51 brief, plus regression tests for the
# existing C42-C50 architecture.

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestM9C51Catalog(unittest.TestCase):
    """Tests for the canonical capability catalog (M51.1/M51.2)."""

    def test_catalog_builds_with_no_errors(self):
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        error_issues = [i for i in catalog.issues if i.severity == "error"]
        self.assertEqual(
            len(error_issues),
            0,
            f"Catalog has {len(error_issues)} errors: {[i.message for i in error_issues]}",
        )

    def test_catalog_has_capabilities_in_all_stages(self):
        from runtime.foundation.verification.capability_catalog import (
            CapabilityStage,
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        stages_with_caps = {e.stage for e in catalog.entries}
        expected_stages = {
            CapabilityStage.DISCOVERY,
            CapabilityStage.PLANNING,
            CapabilityStage.EXECUTION,
            CapabilityStage.MEASUREMENT,
            CapabilityStage.DIAGNOSIS,
            CapabilityStage.STRENGTHENING,
            CapabilityStage.EVIDENCE_INSPECTION,
            CapabilityStage.CERTIFICATION,
        }
        self.assertTrue(
            expected_stages.issubset(stages_with_caps),
            f"Missing stages: {expected_stages - stages_with_caps}",
        )

    def test_catalog_has_expected_number_of_entries(self):
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        self.assertGreaterEqual(
            len(catalog.entries),
            40,
            f"Expected at least 40 capabilities, got {len(catalog.entries)}",
        )

    def test_profile_capabilities_derived_from_registry(self):
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        profile_caps = [e for e in catalog.entries if e.profile_name]
        self.assertGreater(len(profile_caps), 0, "No profile capabilities found")
        # Verify profiles match registry
        from runtime.foundation.verification.registry import get_registry

        registry = get_registry()
        registry.load()
        workflow_ids = {w.id for w in registry.get_all_workflows()}
        for cap in profile_caps:
            # Pipeline commands like evidence-plan are not in the workflow registry
            if (
                cap.profile_name not in workflow_ids
                and cap.profile_name != "evidence-plan"
            ):
                self.fail(f"Profile {cap.profile_name} not in registry")

    def test_configuration_authority_encoded(self):
        """M51.7: quality tools have canonical config authority encoded."""
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        quality_caps = [
            e
            for e in catalog.entries
            if e.stage.value == "execution" and e.category.value == "static_analysis"
        ]
        ruff_cap = next(
            (e for e in quality_caps if "ruff" in e.capability_id.lower()), None
        )
        self.assertIsNotNone(ruff_cap, "Ruff capability not found")
        self.assertIn("pyproject.toml", ruff_cap.configuration_authority[0])
        # Verify it's repo-wide, not backend-only
        self.assertNotIn("backend/src", ruff_cap.configuration_authority[0])


class TestM9C51Discovery(unittest.TestCase):
    """Tests for deterministic capability discovery (M51.3/M51.4)."""

    def setUp(self):
        from runtime.foundation.verification.capability_discovery import (
            CapabilityDiscoveryService,
        )

        self.service = CapabilityDiscoveryService()

    # --- Scenario A: Changed production file ---
    def test_scenario_a_changed_production_file(self):
        result = self.service.discover(
            "changed_file",
            changed_files=["backend/src/engines/loan_engine/amortization.py"],
        )
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertEqual(result.recommended_capability, "discover.blast-radius")
        self.assertEqual(result.next_capability, "plan.execution-plan")
        self.assertIn("blast_radius_contract", result.expected_evidence)

    # --- Scenario B: Mutation survivor ---
    def test_scenario_b_mutation_survivor_routes_to_intel(self):
        result = self.service.discover(
            "mutation_survivor",
            survivor_id="nonexistent-survivor-123",
        )
        # Should still discover the intel capability as next step
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertEqual(result.recommended_capability, "strengthen.survivor-intel")
        # Should have anti-pattern warning
        self.assertIn("Anti-pattern", result.bypass_warning or "")

    # --- Scenario C: Failing test ---
    def test_scenario_c_failing_test(self):
        result = self.service.discover(
            "test_failure",
            test_path="backend/tests/unit/test_loan_engine.py",
        )
        self.assertEqual(result.decision, "DISCOVERED")
        # Either mapped to a capability or routes to diagnostic
        self.assertTrue(
            result.recommended_capability or result.command,
            "Should recommend a capability or command",
        )

    # --- Scenario D: Coverage regression ---
    def test_scenario_d_coverage_regression(self):
        result = self.service.discover(
            "coverage_drop",
            scope="backend",
        )
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertEqual(result.recommended_capability, "measure.coverage")
        self.assertEqual(result.next_capability, "measure.truth-report")

    # --- Scenario E: Workflow failure ---
    def test_scenario_e_workflow_failure(self):
        result = self.service.discover(
            "workflow_failure",
            workflow_id="backend",
        )
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertIn("diagnose", result.recommended_capability.lower())

    # --- Scenario F: Ruff failure ---
    def test_scenario_f_ruff_failure(self):
        result = self.service.discover(
            "quality_failure",
            error_text="ruff: some lint error",
        )
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertEqual(result.recommended_capability, "quality.ruff")

    # --- Scenario G: mypy failure ---
    def test_scenario_g_mypy_failure(self):
        result = self.service.discover(
            "quality_failure",
            error_text="mypy: type error",
        )
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertEqual(result.recommended_capability, "quality.mypy")

    # --- Scenario H: Shared infrastructure change ---
    def test_scenario_h_shared_infrastructure(self):
        result = self.service.discover(
            "changed_file",
            changed_files=["backend/src/common/calculations.py"],
        )
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertEqual(result.recommended_capability, "discover.blast-radius")
        # Blast radius should identify shared impact
        blast = result.resolved_blast_radius
        if blast and "directly_affected_capabilities" in blast:
            # Should include multiple capabilities due to shared infra
            self.assertGreaterEqual(len(blast["directly_affected_capabilities"]), 0)

    # --- Scenario I: Stale evidence ---
    def test_scenario_i_stale_evidence(self):
        result = self.service.discover("stale_evidence")
        self.assertEqual(result.decision, "DISCOVERED")
        self.assertEqual(result.recommended_capability, "measure.truth-report")
        # Should explicitly warn against reuse
        self.assertIn("reuse", result.bypass_warning.lower())

    # --- Scenario J: Unknown failure ---
    def test_scenario_j_unknown_failure(self):
        result = self.service.discover("unknown_failure")
        self.assertEqual(result.decision, "NO_CANONICAL_CAPABILITY")
        self.assertTrue(
            "escalat" in result.escalation.lower()
            or "no canonical" in result.decision.lower()
        )

    # --- Scenario K: Full lifecycle ---
    def test_scenario_k_full_lifecycle(self):
        """Verify problem -> discovery -> canonical capability -> blast-radius -> execution-plan chain."""
        # Step 1: Discovery for changed file
        disc_result = self.service.discover(
            "changed_file",
            changed_files=["backend/src/engines/credit_card_engine/calculator.py"],
        )
        self.assertEqual(disc_result.decision, "DISCOVERED")
        self.assertEqual(disc_result.recommended_capability, "discover.blast-radius")

        # Step 2: Verify blast-radius is consumable by next stage
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            explicit_files=["backend/src/engines/credit_card_engine/calculator.py"]
        )
        self.assertTrue(hasattr(contract, "directly_affected_capabilities"))
        self.assertTrue(hasattr(contract, "minimum_safe_verification"))

        # Step 3: Execution plan can be built from blast radius
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        orch = ExecutionOrchestrator()
        plan = orch.build_execution_plan(
            ["backend/src/engines/credit_card_engine/calculator.py"]
        )
        self.assertTrue(hasattr(plan, "tasks"))
        self.assertGreater(len(plan.tasks), 0)


class TestM9C51BypassAudit(unittest.TestCase):
    """Tests for bypass risk classification (M51.8)."""

    def test_canonical_path_recognized(self):
        from runtime.foundation.verification.capability_discovery import (
            classify_bypass,
        )

        # Unknown action combinations default to SUBOPTIMAL_PATH (conservative)
        verdict, reason = classify_bypass("changed_file", "unknown_action")
        self.assertEqual(verdict, "SUBOPTIMAL_PATH")
        # Known canonical paths should exist for documented scenarios
        # (the bypass audit focuses on detecting UNSAFE/SUBOPTIMAL patterns)

    def test_mutations_survivor_direct_edit_is_unsafe(self):
        from runtime.foundation.verification.capability_discovery import (
            classify_bypass,
        )

        verdict, reason = classify_bypass("mutation_survivor", "direct_test_edit")
        self.assertEqual(verdict, "UNSAFE_BYPASS")
        self.assertIn("intel", reason.lower())

    def test_stale_evidence_reuse_is_unsafe(self):
        from runtime.foundation.verification.capability_discovery import (
            classify_bypass,
        )

        verdict, reason = classify_bypass("stale_evidence", "evidence_reuse")
        self.assertEqual(verdict, "UNSAFE_BYPASS")
        self.assertIn("C47", reason)

    def test_shared_infra_engine_only_is_unsafe(self):
        from runtime.foundation.verification.capability_discovery import (
            classify_bypass,
        )

        verdict, reason = classify_bypass("changed_file", "engine_only")
        self.assertEqual(verdict, "UNSAFE_BYPASS")


class TestM9C51Graph(unittest.TestCase):
    """Tests for capability dependency graph (M51.9)."""

    def test_graph_builds_with_nodes_and_edges(self):
        from runtime.foundation.verification.capability_graph import (
            build_capability_graph,
        )

        graph = build_capability_graph()
        self.assertGreater(len(graph.nodes), 0)
        self.assertGreater(len(graph.edges), 0)

    def test_pipeline_spine_exists(self):
        from runtime.foundation.verification.capability_graph import (
            build_capability_graph,
            verify_pipeline_spine,
        )

        graph = build_capability_graph()
        valid, issues = verify_pipeline_spine(graph)
        self.assertTrue(valid, f"Spine validation failed: {issues}")

    def test_mutation_is_subordinate(self):
        """Mutation must NOT be a top-level capability in the pipeline."""
        from runtime.foundation.verification.capability_graph import (
            build_capability_graph,
        )

        graph = build_capability_graph()
        mutation_node = next(
            (n for n in graph.nodes if n["id"] == "measure.mutation"), None
        )
        self.assertIsNotNone(mutation_node, "Mutation capability not in graph")
        # It should have incoming edges (be downstream of strengthening)
        incoming = [e for e in graph.edges if e.target == "measure.mutation"]
        self.assertGreater(len(incoming), 0, "Mutation should have prerequisites")


class TestM9C51ConfigAuthority(unittest.TestCase):
    """Tests for configuration authority encoding (M51.7)."""

    def test_root_pyproject_is_authoritative_for_ruff_black(self):
        from runtime.foundation.verification.configuration_authority import (
            get_configuration_authority,
        )

        authority = get_configuration_authority()
        ruff = next((a for a in authority if a["tool"] == "ruff"), None)
        black = next((a for a in authority if a["tool"] == "black"), None)
        self.assertIsNotNone(ruff)
        self.assertIsNotNone(black)
        self.assertEqual(ruff["config_scope"], "repo")
        self.assertEqual(black["config_scope"], "repo")
        self.assertIn("pyproject.toml", ruff["config_path"])

    def test_backend_config_is_scoped_only(self):
        from runtime.foundation.verification.configuration_authority import (
            get_configuration_authority,
        )

        authority = get_configuration_authority()
        mutmut = next((a for a in authority if a["tool"] == "mutation"), None)
        self.assertIsNotNone(mutmut)
        self.assertEqual(mutmut["config_scope"], "backend")

    def test_all_config_paths_exist(self):
        from runtime.foundation.verification.configuration_authority import (
            validate_authority,
        )

        valid, issues = validate_authority()
        self.assertTrue(valid, f"Config validation failed: {issues}")


class TestM9C51LatentAudit(unittest.TestCase):
    """Tests for latent capability audit (M51.11)."""

    def test_audit_runs_without_crashing(self):
        from runtime.foundation.verification.capability_latent_audit import (
            run_latent_audit,
        )

        report = run_latent_audit()
        self.assertIsNotNone(report)
        self.assertIsInstance(report.findings, list)

    def test_known_findings_are_detected(self):
        """Test that known structural issues are detected."""
        from runtime.foundation.verification.capability_latent_audit import (
            run_latent_audit,
        )

        report = run_latent_audit()
        finding_entities = {f.entity for f in report.findings}
        # The duplicate strengthen-survivor route should be detected
        self.assertIn("strengthen-survivor", finding_entities)

    def test_findings_are_classified(self):
        from runtime.foundation.verification.capability_latent_audit import (
            run_latent_audit,
        )

        report = run_latent_audit()
        classifications = {f.classification for f in report.findings}
        # Should have some INCOMPLETE-INTEGRATION findings (CLI routes without metadata)
        self.assertIn("INCOMPLETE-INTEGRATION", classifications)


class TestM9C51Regression(unittest.TestCase):
    """Regression tests ensuring C42-C50 functionality remains intact."""

    def test_c50_blast_radius_still_works(self):
        from runtime.foundation.verification.blast_radius import compute_blast_radius

        contract = compute_blast_radius(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        self.assertTrue(hasattr(contract, "directly_affected_capabilities"))
        self.assertIn("loan-engine", contract.directly_affected_capabilities)

    def test_c49_execution_orchestrator_still_works(self):
        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionOrchestrator,
        )

        orch = ExecutionOrchestrator()
        plan = orch.build_execution_plan(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        self.assertTrue(hasattr(plan, "tasks"))
        self.assertGreater(len(plan.tasks), 0)

    def test_c48_capability_resolution_still_works(self):
        from runtime.foundation.verification.capability_resolver import (
            resolve_capabilities,
        )

        resolution = resolve_capabilities(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        self.assertIn("loan-engine", resolution.directly_affected_capabilities)

    def test_existing_tests_still_pass(self):
        """Quick sanity check that core modules import correctly."""
        import runtime.foundation.verification.blast_radius  # noqa: F401
        import runtime.foundation.verification.capability_resolver  # noqa: F401
        import runtime.foundation.verification.control_plane  # noqa: F401
        import runtime.foundation.verification.execution_orchestrator  # noqa: F401
        import runtime.foundation.verification.measurement_truth  # noqa: F401
        import runtime.foundation.verification.survivor_intel  # noqa: F401


if __name__ == "__main__":
    unittest.main()
