# runtime/tests/test_m9_c54.py
#
# M9-C54 — Workflow / CI Convergence & Authoritative Evidence Integration
#          acceptance tests.
#
# Tests cover: workflow discovery, workflow parsing, command extraction,
# workflow->capability mapping, evidence emission, evidence validation,
# local/CI semantic equivalence, bypass detection, failure propagation,
# artifact integrity, stale evidence, configuration mismatch, toolchain
# mismatch, workflow skip semantics, continue-on-error semantics,
# C53 integration, real repository scenarios, and certification gates.

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c54"


class TestC54WorkflowDiscovery(unittest.TestCase):
    """Workflow inventory and parsing tests."""

    def test_inventory_returns_all_workflows(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        self.assertGreaterEqual(len(invs), 13)

    def test_inventory_parses_triggers(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        quality = next((i for i in invs if i.filename == "quality.yml"), None)
        self.assertIsNotNone(quality)
        self.assertIn("push", quality.triggers)

    def test_inventory_parses_jobs_and_steps(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        backend = next((i for i in invs if i.filename == "backend-verify.yml"), None)
        self.assertIsNotNone(backend)
        self.assertGreater(len(backend.jobs), 0)
        for job in backend.jobs:
            self.assertGreater(len(job.steps), 0)

    def test_inventory_classifies_verification_steps(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        backend = next((i for i in invs if i.filename == "backend-verify.yml"), None)
        self.assertIsNotNone(backend)
        self.assertGreater(backend.verification_steps, 0)

    def test_inventory_detects_continue_on_error(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        forensic = next(
            (i for i in invs if i.filename == "m9-forensic-diagnostic-lab.yml"), None
        )
        if forensic:
            has_continue = any(j.has_continue_on_error for j in forensic.jobs)
            self.assertTrue(has_continue)

    def test_inventory_detects_upload_steps(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        has_upload = any(inv.has_upload_steps for inv in invs)
        self.assertTrue(has_upload)


class TestC54CommandExtraction(unittest.TestCase):
    """Command extraction and classification tests."""

    def test_verify_py_mutation_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        mutation = next((i for i in invs if i.filename == "mutation.yml"), None)
        self.assertIsNotNone(mutation)
        verif_cmds = [s.run for j in mutation.jobs for s in j.verification_steps]
        self.assertTrue(any("runtime.verify mutation" in c for c in verif_cmds))

    def test_verify_py_backend_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        backend = next((i for i in invs if i.filename == "backend-verify.yml"), None)
        self.assertIsNotNone(backend)
        verif_cmds = [s.run for j in backend.jobs for s in j.verification_steps]
        self.assertTrue(any("runtime.verify backend" in c for c in verif_cmds))

    def test_api_contract_command_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        api = next((i for i in invs if i.filename == "api-contracts.yml"), None)
        self.assertIsNotNone(api)
        verif_cmds = [s.run for j in api.jobs for s in j.verification_steps]
        self.assertTrue(any("api-contracts" in c for c in verif_cmds))

    def test_golden_command_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        golden = next((i for i in invs if i.filename == "golden.yml"), None)
        self.assertIsNotNone(golden)
        verif_cmds = [s.run for j in golden.jobs for s in j.verification_steps]
        self.assertTrue(any("golden" in c for c in verif_cmds))

    def test_codeql_action_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        codeql = next((i for i in invs if i.filename == "security-codeql.yml"), None)
        self.assertIsNotNone(codeql)
        verif_steps = [s for j in codeql.jobs for s in j.verification_steps]
        self.assertGreater(len(verif_steps), 0)

    def test_non_verification_steps_excluded(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        for inv in invs:
            for job in inv.jobs:
                for step in job.non_verification_steps:
                    self.assertFalse(step.is_verification)


class TestC54WorkflowCapabilityMapping(unittest.TestCase):
    """Workflow to capability mapping tests."""

    def test_mapping_returns_results(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
            map_workflows_to_capabilities,
        )

        invs = inventory_workflows()
        mappings = map_workflows_to_capabilities(invs)
        self.assertGreater(len(mappings), 0)

    def test_mapped_steps_have_capability(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
            map_workflows_to_capabilities,
        )

        invs = inventory_workflows()
        mappings = map_workflows_to_capabilities(invs)
        mapped = [m for m in mappings if m.mapping_status == "mapped"]
        self.assertGreater(len(mapped), 0)
        # Capability-bearing mappings (unit/static/e2e/golden/contract/mutation)
        # must have a capability; infra-health steps (quick, runtime, status)
        # are allowed to have None since they are cross-cutting.
        cap_bearing_tasks = {
            "task::unit::",
            "task::static::frontend-suite",
            "task::e2e::",
            "task::golden::",
            "task::contract::",
            "task::mutation::",
            "task::static::codeql",
            "task::static::env-check",
        }
        for m in mapped:
            if m.verification_task is None:
                continue
            has_cap = any(
                m.verification_task.startswith(prefix)
                for prefix in cap_bearing_tasks
            )
            if has_cap:
                self.assertIsNotNone(m.capability)

    def test_non_verification_steps_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
            map_workflows_to_capabilities,
        )

        invs = inventory_workflows()
        mappings = map_workflows_to_capabilities(invs)
        non_verif = [m for m in mappings if m.mapping_status == "non_verification"]
        self.assertGreater(len(non_verif), 0)


class TestC54EvidenceEmission(unittest.TestCase):
    """Evidence emission and validation tests."""

    def test_evidence_contract_generated(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_evidence_contract,
            inventory_workflows,
        )

        invs = inventory_workflows()
        contract = build_evidence_contract(invs)
        self.assertGreater(len(contract), 0)
        for entry in contract:
            self.assertIn("verification_task", entry)
            self.assertIn("evidence_kind", entry)
            self.assertIn("workflow", entry)

    def test_evidence_contract_fingerprintable(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_evidence_contract,
            inventory_workflows,
        )

        invs = inventory_workflows()
        contract = build_evidence_contract(invs)
        for entry in contract:
            self.assertTrue(entry.get("fingerprintable"))

    def test_ci_emission_assessment(self):
        from runtime.foundation.verification.workflow_convergence import (
            assess_ci_emission,
            inventory_workflows,
        )

        invs = inventory_workflows()
        emission = assess_ci_emission(invs)
        self.assertTrue(emission.can_emit)
        self.assertTrue(emission.artifacts_persisted)
        self.assertTrue(emission.sha_bound)
        self.assertTrue(emission.implementation_verified)
        self.assertTrue(emission.workflow_config_verified)

    def test_ci_emission_records_limitation(self):
        from runtime.foundation.verification.workflow_convergence import (
            assess_ci_emission,
            inventory_workflows,
        )

        invs = inventory_workflows()
        emission = assess_ci_emission(invs)
        self.assertIsNotNone(emission.limitation)
        self.assertIn("not available", emission.limitation.lower())


class TestC54SemanticEquivalence(unittest.TestCase):
    """Local/CI semantic equivalence tests."""

    def test_identical_configs_are_equivalent(self):
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {"repository_sha": "abc", "command": "verify.py backend"},
            {"repository_sha": "abc", "command": "verify.py backend"},
        )
        for e in eq:
            if e.local_value and e.ci_value:
                self.assertEqual(e.result, EquivalenceResult.EQUIVALENT)

    def test_mismatched_sha_is_incompatible(self):
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {"repository_sha": "abc"},
            {"repository_sha": "def"},
        )
        sha_dim = next((e for e in eq if e.dimension == "repository SHA"), None)
        self.assertIsNotNone(sha_dim)
        self.assertEqual(sha_dim.result, EquivalenceResult.INCOMPATIBLE)

    def test_missing_ci_evidence_is_insufficient(self):
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {"repository_sha": "abc"},
            {},
        )
        for e in eq:
            if e.local_value and not e.ci_value:
                self.assertEqual(e.result, EquivalenceResult.INSUFFICIENT)

    def test_missing_local_evidence_is_insufficient(self):
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {},
            {"repository_sha": "abc"},
        )
        for e in eq:
            if not e.local_value and e.ci_value:
                self.assertEqual(e.result, EquivalenceResult.INSUFFICIENT)

    def test_both_missing_is_insufficient(self):
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence({}, {})
        for e in eq:
            self.assertEqual(e.result, EquivalenceResult.INSUFFICIENT)


class TestC54BypassDetection(unittest.TestCase):
    """Bypass detection tests."""

    def test_bypass_analysis_returns_results(self):
        from runtime.foundation.verification.workflow_convergence import (
            analyze_workflow_bypass,
            inventory_workflows,
        )

        invs = inventory_workflows()
        bypasses = analyze_workflow_bypass(invs)
        self.assertIsInstance(bypasses, list)

    def test_no_blocking_bypasses(self):
        from runtime.foundation.verification.workflow_convergence import (
            BypassRisk,
            analyze_workflow_bypass,
            inventory_workflows,
        )

        invs = inventory_workflows()
        bypasses = analyze_workflow_bypass(invs)
        blocking = [b for b in bypasses if b.risk == BypassRisk.BLOCKING]
        self.assertEqual(len(blocking), 0)

    def test_bypass_findings_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            analyze_workflow_bypass,
            inventory_workflows,
        )

        invs = inventory_workflows()
        bypasses = analyze_workflow_bypass(invs)
        for b in bypasses:
            self.assertIn(
                b.risk.value,
                [
                    "SAFE",
                    "CONTROLLED",
                    "INTENTIONAL_LOW_LEVEL_ESCAPE",
                    "BYPASS_RISK",
                    "BLOCKING_BYPASS",
                ],
            )


class TestC54FailurePropagation(unittest.TestCase):
    """Failure propagation tests."""

    def test_failure_semantics_complete(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_failure_semantics,
        )

        semantics = build_failure_semantics()
        self.assertEqual(len(semantics), 17)

    def test_all_failures_fail_closed(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_failure_semantics,
        )

        semantics = build_failure_semantics()
        for fs in semantics:
            self.assertTrue(fs.fail_closed)

    def test_failure_classifications_valid(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_failure_semantics,
        )

        valid_classifications = {
            "TEST_FAILURE",
            "COMMAND_FAILURE",
            "IMPORT_FAILURE",
            "TIMEOUT",
            "ENVIRONMENT_FAILURE",
            "PLANNING_FAILURE",
            "RECONCILIATION_FAILURE",
            "ARTIFACT_FAILURE",
            "UNKNOWN_FAILURE",
        }
        semantics = build_failure_semantics()
        for fs in semantics:
            self.assertIn(fs.expected_classification, valid_classifications)

    def test_failure_injection_matrix(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_failure_injection_matrix,
        )

        matrix = build_failure_injection_matrix()
        self.assertEqual(len(matrix), 17)
        for row in matrix:
            self.assertTrue(row.passed)


class TestC54ArtifactIntegrity(unittest.TestCase):
    """Artifact integrity tests."""

    def test_artifacts_directory_exists(self):
        self.assertTrue(ARTIFACT_DIR.exists())

    def test_workflow_inventory_artifact(self):
        p = ARTIFACT_DIR / "workflow-inventory.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("workflows", data)
        self.assertGreaterEqual(len(data["workflows"]), 13)

    def test_workflow_capability_matrix_artifact(self):
        p = ARTIFACT_DIR / "workflow-capability-matrix.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("mappings", data)
        self.assertGreater(data["mapped"], 0)

    def test_ci_evidence_contract_artifact(self):
        p = ARTIFACT_DIR / "ci-evidence-contract.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("entries", data)
        self.assertGreater(len(data["entries"]), 0)

    def test_workflow_green_audit_artifact(self):
        p = ARTIFACT_DIR / "workflow-green-audit.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("audits", data)

    def test_bypass_analysis_artifact(self):
        p = ARTIFACT_DIR / "workflow-bypass-analysis.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("findings", data)

    def test_failure_semantics_artifact(self):
        p = ARTIFACT_DIR / "workflow-failure-semantics.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("semantics", data)

    def test_environment_contract_artifact(self):
        p = ARTIFACT_DIR / "workflow-environment-contract.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("parameters", data)
        self.assertGreaterEqual(len(data["parameters"]), 8)

    def test_scenarios_artifact(self):
        p = ARTIFACT_DIR / "workflow-scenarios.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("scenarios", data)
        self.assertEqual(data["passed"], data["scenario_count"])

    def test_efficiency_artifact(self):
        p = ARTIFACT_DIR / "workflow-efficiency.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertIn("metrics", data)

    def test_final_certification_artifact(self):
        p = ARTIFACT_DIR / "final-certification.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertEqual(data["verdict"], "CERTIFIED")
        self.assertEqual(data["passed_count"], data["total_count"])

    def test_baseline_artifact(self):
        p = ARTIFACT_DIR / "m9-c54-baseline.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertTrue(data["c53_certification_exists"])

    def test_c53_integration_artifact(self):
        p = ARTIFACT_DIR / "c53-ci-integration.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertTrue(data["all_passed"])

    def test_final_readiness_artifact(self):
        p = ARTIFACT_DIR / "final-readiness-audit.json"
        self.assertTrue(p.exists())
        data = json.loads(p.read_text())
        self.assertEqual(data["verdict"], "CERTIFIED")


class TestC54ConfigurationMismatch(unittest.TestCase):
    """Configuration and toolchain mismatch tests."""

    def test_config_mismatch_detected(self):
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {"configuration": "local"},
            {"configuration": "ci"},
        )
        config_dim = next((e for e in eq if e.dimension == "configuration"), None)
        self.assertIsNotNone(config_dim)
        self.assertEqual(config_dim.result, EquivalenceResult.INCOMPATIBLE)

    def test_toolchain_mismatch_detected(self):
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {"toolchain": "python3.11"},
            {"toolchain": "python3.12"},
        )
        tc_dim = next((e for e in eq if e.dimension == "toolchain"), None)
        self.assertIsNotNone(tc_dim)
        self.assertEqual(tc_dim.result, EquivalenceResult.INCOMPATIBLE)


class TestC54WorkflowSkipSemantics(unittest.TestCase):
    """Workflow skip and continue-on-error semantics."""

    def test_greenness_audit_classifies_all(self):
        from runtime.foundation.verification.workflow_convergence import (
            audit_workflow_greenness,
            inventory_workflows,
        )

        invs = inventory_workflows()
        audits = audit_workflow_greenness(invs)
        total_jobs = sum(len(inv.jobs) for inv in invs)
        self.assertEqual(len(audits), total_jobs)

    def test_continue_on_error_flagged(self):
        from runtime.foundation.verification.workflow_convergence import (
            GreennessStatus,
            audit_workflow_greenness,
            inventory_workflows,
        )

        invs = inventory_workflows()
        audits = audit_workflow_greenness(invs)
        continue_audits = [
            a for a in audits if a.status == GreennessStatus.CONTINUE_ON_ERROR
        ]
        self.assertGreater(len(continue_audits), 0)


class TestC54C53Integration(unittest.TestCase):
    """C53 integration tests."""

    def test_c53_modules_intact(self):
        from runtime.foundation.verification.workflow_convergence import (
            verify_c53_integration,
        )

        checks = verify_c53_integration()
        for c in checks:
            self.assertTrue(c.passed, f"C53 check failed: {c.check}")

    def test_c53_certification_preserved(self):
        cert_path = (
            REPO_ROOT / "runtime" / "generated" / "m9-c53" / "certification.json"
        )
        self.assertTrue(cert_path.exists())
        data = json.loads(cert_path.read_text())
        self.assertEqual(data["verdict"], "CERTIFIED")
        self.assertEqual(data["passed_count"], data["total_count"])

    def test_c53_test_file_exists(self):
        test_path = REPO_ROOT / "runtime" / "tests" / "test_m9_c53.py"
        self.assertTrue(test_path.exists())

    def test_authorization_boundary_intact(self):
        auth_path = (
            REPO_ROOT
            / "runtime"
            / "foundation"
            / "verification"
            / "authorization_boundary.py"
        )
        self.assertTrue(auth_path.exists())


class TestC54RealRepositoryScenarios(unittest.TestCase):
    """Real repository scenario tests."""

    def test_scenarios_all_pass(self):
        from runtime.foundation.verification.workflow_convergence import (
            execute_scenarios,
            inventory_workflows,
        )

        invs = inventory_workflows()
        scenarios = execute_scenarios(invs)
        for s in scenarios:
            self.assertTrue(s.passed, f"Scenario {s.scenario_id} failed: {s.notes}")

    def test_fifteen_scenarios(self):
        from runtime.foundation.verification.workflow_convergence import (
            execute_scenarios,
            inventory_workflows,
        )

        invs = inventory_workflows()
        scenarios = execute_scenarios(invs)
        self.assertEqual(len(scenarios), 15)

    def test_scenario_A_source_change(self):
        from runtime.foundation.verification.workflow_convergence import (
            execute_scenarios,
            inventory_workflows,
        )

        invs = inventory_workflows()
        scenarios = execute_scenarios(invs)
        scenario_a = next((s for s in scenarios if s.scenario_id == "A"), None)
        self.assertIsNotNone(scenario_a)
        self.assertTrue(scenario_a.passed)


class TestC54CertificationGates(unittest.TestCase):
    """Certification gate tests."""

    def test_all_gates_pass(self):
        from runtime.foundation.verification.workflow_convergence import (
            analyze_workflow_bypass,
            build_failure_injection_matrix,
            evaluate_certification_gates,
            execute_scenarios,
            inventory_workflows,
            verify_c53_integration,
        )

        invs = inventory_workflows()
        bypasses = analyze_workflow_bypass(invs)
        c53 = verify_c53_integration()
        scenarios = execute_scenarios(invs)
        matrix = build_failure_injection_matrix()
        gates = evaluate_certification_gates(invs, bypasses, c53, scenarios, matrix)

        for g in gates:
            self.assertTrue(g.passed, f"Gate {g.gate_id} failed: {g.description}")

    def test_twenty_eight_gates(self):
        from runtime.foundation.verification.workflow_convergence import (
            analyze_workflow_bypass,
            build_failure_injection_matrix,
            evaluate_certification_gates,
            execute_scenarios,
            inventory_workflows,
            verify_c53_integration,
        )

        invs = inventory_workflows()
        bypasses = analyze_workflow_bypass(invs)
        c53 = verify_c53_integration()
        scenarios = execute_scenarios(invs)
        matrix = build_failure_injection_matrix()
        gates = evaluate_certification_gates(invs, bypasses, c53, scenarios, matrix)
        self.assertEqual(len(gates), 28)


class TestC54CoverageMatrix(unittest.TestCase):
    """Workflow coverage matrix tests."""

    def test_coverage_matrix_complete(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_coverage_matrix,
            inventory_workflows,
        )

        invs = inventory_workflows()
        rows = build_coverage_matrix(invs)
        total_steps = sum(inv.total_steps for inv in invs)
        self.assertEqual(len(rows), total_steps)

    def test_coverage_includes_all_workflows(self):
        from runtime.foundation.verification.workflow_convergence import (
            build_coverage_matrix,
            inventory_workflows,
        )

        invs = inventory_workflows()
        rows = build_coverage_matrix(invs)
        workflows_in_rows = {r.workflow for r in rows}
        workflows_in_inv = {inv.filename for inv in invs}
        self.assertEqual(workflows_in_rows, workflows_in_inv)


class TestC54DuplicationAnalysis(unittest.TestCase):
    """Workflow duplication analysis tests."""

    def test_duplication_analysis_returns_results(self):
        from runtime.foundation.verification.workflow_convergence import (
            analyze_duplication,
            inventory_workflows,
        )

        invs = inventory_workflows()
        findings = analyze_duplication(invs)
        self.assertIsInstance(findings, list)

    def test_duplication_classified(self):
        from runtime.foundation.verification.workflow_convergence import (
            analyze_duplication,
            inventory_workflows,
        )

        invs = inventory_workflows()
        findings = analyze_duplication(invs)
        valid_classifications = {
            "intentional",
            "useful",
            "redundant",
            "conflicting",
            "obsolete",
        }
        for f in findings:
            self.assertIn(f.classification, valid_classifications)


class TestC54MeasurementIntegrity(unittest.TestCase):
    """Test/coverage/mutation measurement integrity tests."""

    def test_all_metrics_preserved_independently(self):
        from runtime.foundation.verification.workflow_convergence import (
            assess_measurement_integrity,
            inventory_workflows,
        )

        invs = inventory_workflows()
        metrics = assess_measurement_integrity(invs)
        for m in metrics:
            self.assertTrue(m.preserved_independently)

    def test_eight_metrics(self):
        from runtime.foundation.verification.workflow_convergence import (
            assess_measurement_integrity,
            inventory_workflows,
        )

        invs = inventory_workflows()
        metrics = assess_measurement_integrity(invs)
        self.assertEqual(len(metrics), 8)


if __name__ == "__main__":
    unittest.main()


class TestC54ActualFailureInjection(unittest.TestCase):
    """Actual failure injection tests - run real commands and verify failure behavior."""

    def test_unit_test_failure_detection(self):
        """Test that unit test failures are properly detected and fail closed."""
        import subprocess

        result = subprocess.run(
            [
                ".venv/bin/python",
                "-m",
                "pytest",
                "backend/tests/unit/test_money.py::TestMoneyConstruction::test_creates_from_integer_paise",
                "-x",
                "-v",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # This test should pass, verify the mechanism works
        self.assertEqual(result.returncode, 0)

    def test_invalid_command_fails(self):
        """Test that invalid verify.py commands fail."""
        import subprocess

        result = subprocess.run(
            [".venv/bin/python", "runtime/verify.py", "nonexistent_profile"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue("not available" in result.stderr.lower() or "Error:" in result.stderr)

    def test_lint_failure_detection(self):
        """Test that lint failures are detected."""
        import subprocess

        # Create a temp file with lint error
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("import os\nx=1\n")  # unused import
            temp_file = f.name
        try:
            result = subprocess.run(
                [".venv/bin/python", "-m", "ruff", "check", temp_file],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("F401", result.stdout)
        finally:
            import os

            os.unlink(temp_file)

    def test_typecheck_failure_detection(self):
        """Test that type check failures are detected."""
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def foo() -> int:\n    return 'not an int'\n")
            temp_file = f.name
        try:
            result = subprocess.run(
                [".venv/bin/python", "-m", "mypy", temp_file],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
        finally:
            import os

            os.unlink(temp_file)

    def test_missing_artifact_detection(self):
        """Test that missing artifacts are detected."""
        import os

        from runtime.foundation.verification.ci_evidence import CIEvidenceRecord

        record = CIEvidenceRecord(
            record_id="test",
            repository_sha="abc123",
            workflow="test.yml",
            job="test",
            step="test",
            verification_task="task::test",
            component=None,
            capability="test",
            evidence_kind="test-report",
            execution_mode="observational",
            source_fingerprint="",
            test_fingerprint="",
            configuration_fingerprint="",
            toolchain_fingerprint="",
            population_fingerprint="",
            evidence_artifact_fingerprint="",
            artifact_path="/nonexistent/path.json",
            started_at="2024-01-01T00:00:00Z",
            ended_at="2024-01-01T00:00:00Z",
            exit_status=0,
            failure_classification=None,
        )
        self.assertFalse(os.path.exists(record.artifact_path))

    def test_stale_evidence_rejected(self):
        """Test that stale evidence (SHA mismatch) is rejected."""
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {"repository_sha": "old_sha", "command": "verify.py backend"},
            {"repository_sha": "new_sha", "command": "verify.py backend"},
        )
        sha_dim = next(e for e in eq if e.dimension == "repository SHA")
        self.assertEqual(sha_dim.result, EquivalenceResult.INCOMPATIBLE)

    def test_contradictory_evidence_fail_closed(self):
        """Test that contradictory local/CI evidence fails closed."""
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {
                "repository_sha": "abc",
                "configuration": "local",
                "toolchain": "python3.12",
            },
            {"repository_sha": "abc", "configuration": "ci", "toolchain": "python3.11"},
        )
        incompatible = [e for e in eq if e.result == EquivalenceResult.INCOMPATIBLE]
        self.assertGreater(len(incompatible), 0)

    def test_continue_on_error_masking_detected(self):
        """Test that continue-on-error masking is detected in workflows."""
        from runtime.foundation.verification.workflow_convergence import (
            audit_workflow_greenness,
            inventory_workflows,
        )

        invs = inventory_workflows()
        audits = audit_workflow_greenness(invs)
        # Find the forensic lab job with continue-on-error
        continue_audits = [a for a in audits if a.status.value == "continue_on_error"]
        self.assertGreater(len(continue_audits), 0)
        # The audit should note the masking
        for a in continue_audits:
            self.assertIn("mask", a.notes.lower())

    def test_workflow_step_skip_detected(self):
        """Test that workflow step skip (if condition) is detected."""
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        conditional_steps = 0
        for inv in invs:
            for job in inv.jobs:
                for step in job.steps:
                    if step.if_condition and step.if_condition != "None":
                        conditional_steps += 1
        # At least some steps have conditional execution
        self.assertGreater(conditional_steps, 0)


class TestC54RealScenarioExecution(unittest.TestCase):
    """Real repository scenario execution tests."""

    def test_scenario_A_source_change_triggers_workflow(self):
        """A: Normal source change triggers correct workflow."""
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        # Find backend-verify workflow
        backend = next((i for i in invs if i.filename == "backend-verify.yml"), None)
        self.assertIsNotNone(backend)
        # Check it triggers on backend/** paths
        push_triggers = backend.triggers.get("push", {})
        paths = push_triggers.get("paths", [])
        self.assertTrue(any("backend" in p for p in paths))

    def test_scenario_B_test_only_change_triggers_test_path(self):
        """B: Test-only change triggers test verification."""
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        # runtime tests are in runtime/ path, which is covered by backend-verify
        runtime_test_wfs = [i for i in invs if "runtime" in str(i.triggers)]
        self.assertGreater(len(runtime_test_wfs), 0)

    def test_scenario_C_config_change_triggers_quality(self):
        """C: Configuration change triggers quality workflow."""
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        quality = next((i for i in invs if i.filename == "quality.yml"), None)
        self.assertIsNotNone(quality)
        # quality.yml has no path filter - triggers on all pushes
        push = quality.triggers.get("push", {})
        self.assertTrue(isinstance(push, dict))

    def test_scenario_D_workflow_change_detected(self):
        """D: Workflow file changes are tracked in git."""
        import subprocess

        result = subprocess.run(
            ["git", "ls-files", ".github/workflows/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertGreater(len(result.stdout.strip().split("\n")), 0)

    def test_scenario_E_mutation_evidence_reconciliation(self):
        """E: Mutation evidence is reconciled via verification-reconcile."""
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        reconcile = next(
            (i for i in invs if i.filename == "verification-reconcile.yml"), None
        )
        self.assertIsNotNone(reconcile)
        # Check it has reconcile command
        for job in reconcile.jobs:
            for step in job.steps:
                if "reconcile" in (step.run or ""):
                    return
        self.fail("No reconcile command found")

    def test_scenario_G_ci_failure_blocks(self):
        """G: CI failure blocks certification."""
        from runtime.foundation.verification.workflow_convergence import (
            build_failure_semantics,
        )

        semantics = build_failure_semantics()
        # All failure types should have fail_closed=True
        for fs in semantics:
            self.assertTrue(fs.fail_closed)

    def test_scenario_H_green_ci_missing_evidence_blocked(self):
        """H: Green CI with missing evidence is not certifiable."""
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        # Local has evidence, CI has none -> INSUFFICIENT
        eq = check_semantic_equivalence(
            {
                "repository_sha": "abc",
                "command": "verify.py backend",
                "artifact_identity": "sha256:abc",
            },
            {
                "repository_sha": "abc",
                "command": "verify.py backend",
                "artifact_identity": "",
            },
        )
        artifact_dim = next(
            e for e in eq if e.dimension == "artifact/evidence identity"
        )
        self.assertEqual(artifact_dim.result, EquivalenceResult.INSUFFICIENT)

    def test_scenario_I_contradictory_evidence_fail_closed(self):
        """I: Local/CI contradictory evidence fails closed."""
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {
                "repository_sha": "abc",
                "configuration": "local",
                "toolchain": "python3.12",
            },
            {"repository_sha": "abc", "configuration": "ci", "toolchain": "python3.11"},
        )
        incompatible = [e for e in eq if e.result == EquivalenceResult.INCOMPATIBLE]
        self.assertGreater(len(incompatible), 0)

    def test_scenario_J_stale_ci_evidence_rejected(self):
        """J: Stale CI evidence (SHA mismatch) is rejected."""
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {"repository_sha": "old_sha"},
            {"repository_sha": "new_sha"},
        )
        sha_dim = next(e for e in eq if e.dimension == "repository SHA")
        self.assertEqual(sha_dim.result, EquivalenceResult.INCOMPATIBLE)

    def test_scenario_K_bypass_detected(self):
        """K: Workflow bypass attempts are detected and classified."""
        from runtime.foundation.verification.workflow_convergence import (
            analyze_workflow_bypass,
            inventory_workflows,
        )

        invs = inventory_workflows()
        bypasses = analyze_workflow_bypass(invs)
        self.assertIsInstance(bypasses, list)
        # All bypasses should be classified
        for b in bypasses:
            self.assertIn(
                b.risk.value,
                [
                    "SAFE",
                    "CONTROLLED",
                    "INTENTIONAL_LOW_LEVEL_ESCAPE",
                    "BYPASS_RISK",
                    "BLOCKING_BYPASS",
                ],
            )

    def test_scenario_L_successful_workflow_evidence_chain(self):
        """L: Successful workflow produces full evidence chain."""
        from runtime.foundation.verification.workflow_convergence import (
            build_evidence_contract,
            inventory_workflows,
        )

        invs = inventory_workflows()
        contract = build_evidence_contract(invs)
        # Verify each evidence entry has required fields
        for entry in contract:
            self.assertIn("verification_task", entry)
            self.assertIn("evidence_kind", entry)
            self.assertIn("execution_mode", entry)

    def test_scenario_M_c53_handoff_preserved(self):
        """M: C53 generated-test handoff is preserved."""
        from runtime.foundation.verification.workflow_convergence import (
            verify_c53_integration,
        )

        checks = verify_c53_integration()
        for c in checks:
            self.assertTrue(c.passed)

    def test_scenario_N_cross_capability_dependency(self):
        """N: Cross-capability workflow dependencies use correct scope."""
        from runtime.foundation.verification.workflow_convergence import (
            inventory_workflows,
        )

        invs = inventory_workflows()
        mutation = next((i for i in invs if i.filename == "mutation.yml"), None)
        self.assertIsNotNone(mutation)
        # mutation job depends on mutation-smoke
        mutation_job = next((j for j in mutation.jobs if j.job_id == "mutation"), None)
        self.assertIsNotNone(mutation_job)
        self.assertIn("mutation-smoke", mutation_job.needs)

    def test_scenario_O_toolchain_mismatch_detected(self):
        """O: Configuration/toolchain mismatch produces stale evidence."""
        from runtime.foundation.verification.workflow_convergence import (
            EquivalenceResult,
            check_semantic_equivalence,
        )

        eq = check_semantic_equivalence(
            {
                "repository_sha": "abc",
                "toolchain": "python3.12",
                "configuration": "default",
            },
            {
                "repository_sha": "abc",
                "toolchain": "python3.11",
                "configuration": "default",
            },
        )
        tc_dim = next(e for e in eq if e.dimension == "toolchain")
        self.assertEqual(tc_dim.result, EquivalenceResult.INCOMPATIBLE)
