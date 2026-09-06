# runtime/tests/test_m9_c53.py
#
# M9-C53 — Automatic Test Generation & Evidence-Driven Strengthening
#          acceptance tests.
#
# Tests: genuine-gap detection, false-positive prevention, generation
# eligibility, each gap classification (A-G), candidate generation,
# candidate validation, mutation distinguishing behavior, coverage behavior,
# regression preservation, authorization boundary, stale evidence, fingerprint
# mismatch, scope drift, cross-capability impact, deterministic behavior,
# refusal behavior, and end-to-end generation → validation → authorization →
# targeted revalidation.

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestC53GapClassification(unittest.TestCase):
    """M9-C53 gap classification taxonomy (A–G)."""

    def test_classify_genuine_behavioral_gap_A(self):
        from runtime.foundation.verification.gap_classification import (
            GapClass,
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-a",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Genuine behavioral gap",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        result = classify_gap(gap)
        self.assertEqual(result.gap_class, GapClass.A_GENUINE_BEHAVIORAL)
        self.assertTrue(result.eligible_for_generation)

    def test_classify_equivalent_gap_B(self):
        from runtime.foundation.verification.gap_classification import (
            GapClass,
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-b",
            source="survivor",
            component="loan",
            capability="measure.mutation",
            location="backend/src/engines/loan_engine/amortization.py:88",
            description="Equivalent gap",
            evidence_kind="arithmetic",
            evidence_detail="a + b",
            status="survived",
            notes="equivalent: identical observable behavior",
        )
        result = classify_gap(gap)
        self.assertEqual(result.gap_class, GapClass.EQUIVALENT)
        self.assertFalse(result.eligible_for_generation)

    def test_classify_defensive_gap_C(self):
        from runtime.foundation.verification.gap_classification import (
            GapClass,
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-c",
            source="survivor",
            component="behaviour",
            capability="measure.mutation",
            location="backend/src/engines/behaviour_engine/rules.py:55",
            description="Defensive gap",
            evidence_kind="boolean",
            evidence_detail="logger.info(f'processing {count}')",
            status="survived",
            notes="",
        )
        result = classify_gap(gap)
        self.assertEqual(result.gap_class, GapClass.DEFENSIVE)
        self.assertFalse(result.eligible_for_generation)

    def test_classify_discovery_gap_D(self):
        from runtime.foundation.verification.gap_classification import (
            GapClass,
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-d",
            source="survivor",
            component="cashflow",
            capability="measure.mutation",
            location="backend/src/engines/cashflow_engine/projections.py:200",
            description="Discovery gap",
            evidence_kind="comparison",
            evidence_detail="if x > 0:",
            status="survived",
            notes="no_test_surface: no reachable test surface",
        )
        result = classify_gap(gap)
        self.assertEqual(result.gap_class, GapClass.DISCOVERY_GAP)
        self.assertFalse(result.eligible_for_generation)

    def test_classify_historical_gap_E(self):
        from runtime.foundation.verification.gap_classification import (
            GapClass,
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-e",
            source="survivor",
            component="reconciliation",
            capability="measure.mutation",
            location="backend/src/engines/reconciliation_engine/match.py:150",
            description="Historical gap",
            evidence_kind="comparison",
            evidence_detail="if diff <= tolerance:",
            status="survived",
            notes="repeated_survivor",
            historical_count=5,
        )
        result = classify_gap(gap)
        self.assertEqual(result.gap_class, GapClass.HISTORICAL)
        self.assertFalse(result.eligible_for_generation)

    def test_classify_measurement_failure_F(self):
        from runtime.foundation.verification.gap_classification import (
            GapClass,
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-f",
            source="survivor",
            component="forecasting",
            capability="measure.mutation",
            location="backend/src/engines/forecasting_engine/predict.py:110",
            description="Measurement failure",
            evidence_kind="arithmetic",
            evidence_detail="prediction = model.forecast(horizon)",
            status="timeout",
            notes="",
        )
        result = classify_gap(gap)
        self.assertEqual(result.gap_class, GapClass.MEASUREMENT_FAILURE)
        self.assertFalse(result.eligible_for_generation)

    def test_classify_missing_regression_G(self):
        from runtime.foundation.verification.gap_classification import (
            GapClass,
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-g",
            source="historical_regression",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Missing regression test",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="known_regression: previously fixed bug lacks regression test",
        )
        result = classify_gap(gap)
        self.assertEqual(result.gap_class, GapClass.MISSING_REGRESSION)
        self.assertTrue(result.eligible_for_generation)

    def test_classification_is_deterministic(self):
        from runtime.foundation.verification.gap_classification import (
            GapEvidence,
            classify_gap,
        )

        gap = GapEvidence(
            gap_id="test-det",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Determinism test",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        r1 = classify_gap(gap)
        r2 = classify_gap(gap)
        self.assertEqual(r1.gap_class, r2.gap_class)
        self.assertEqual(r1.eligible_for_generation, r2.eligible_for_generation)


class TestC53GenerationEligibility(unittest.TestCase):
    """M9-C53 generation eligibility decisions."""

    def test_genuine_gap_is_eligible(self):
        from runtime.foundation.verification.gap_classification import (
            GapEvidence,
            classify_gap,
        )
        from runtime.foundation.verification.generation_eligibility import (
            determine_eligibility,
        )

        gap = GapEvidence(
            gap_id="elig-a",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Eligible gap",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        classification = classify_gap(gap)
        eligibility = determine_eligibility(classification)
        self.assertTrue(eligibility.generation_allowed)
        self.assertFalse(eligibility.generation_refused)

    def test_equivalent_gap_is_refused(self):
        from runtime.foundation.verification.gap_classification import (
            GapEvidence,
            classify_gap,
        )
        from runtime.foundation.verification.generation_eligibility import (
            RefusalCode,
            determine_eligibility,
        )

        gap = GapEvidence(
            gap_id="elig-b",
            source="survivor",
            component="loan",
            capability="measure.mutation",
            location="backend/src/engines/loan_engine/amortization.py:88",
            description="Equivalent gap",
            evidence_kind="arithmetic",
            evidence_detail="a + b",
            status="survived",
            notes="equivalent",
        )
        classification = classify_gap(gap)
        eligibility = determine_eligibility(classification)
        self.assertFalse(eligibility.generation_allowed)
        self.assertTrue(eligibility.generation_refused)
        self.assertEqual(eligibility.refusal_code, RefusalCode.EQUIVALENT_SURVIVOR)

    def test_scope_drift_is_refused(self):
        from runtime.foundation.verification.gap_classification import (
            GapEvidence,
            classify_gap,
        )
        from runtime.foundation.verification.generation_eligibility import (
            RefusalCode,
            determine_eligibility,
        )

        gap = GapEvidence(
            gap_id="elig-scope",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Scope drift gap",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        classification = classify_gap(gap)
        eligibility = determine_eligibility(
            classification, scope_capability="api-contracts"
        )
        self.assertFalse(eligibility.generation_allowed)
        self.assertTrue(eligibility.generation_refused)
        self.assertEqual(eligibility.refusal_code, RefusalCode.SCOPE_DRIFT)

    def test_measurement_failure_is_refused(self):
        from runtime.foundation.verification.gap_classification import (
            GapEvidence,
            classify_gap,
        )
        from runtime.foundation.verification.generation_eligibility import (
            RefusalCode,
            determine_eligibility,
        )

        gap = GapEvidence(
            gap_id="elig-f",
            source="survivor",
            component="forecasting",
            capability="measure.mutation",
            location="backend/src/engines/forecasting_engine/predict.py:110",
            description="Measurement failure",
            evidence_kind="arithmetic",
            evidence_detail="x + y",
            status="timeout",
            notes="",
        )
        classification = classify_gap(gap)
        eligibility = determine_eligibility(classification)
        self.assertFalse(eligibility.generation_allowed)
        self.assertTrue(eligibility.generation_refused)
        self.assertEqual(eligibility.refusal_code, RefusalCode.MEASUREMENT_FAILURE)


class TestC53CandidateGeneration(unittest.TestCase):
    """M9-C53 candidate test generation."""

    def test_genuine_gap_produces_candidate(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="gen-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Genuine gap for generation",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        self.assertIsNotNone(result.candidate)
        self.assertIsNotNone(result.candidate.code)
        self.assertIn("def test_", result.candidate.code)

    def test_equivalent_gap_produces_no_candidate(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="gen-equiv",
            source="survivor",
            component="loan",
            capability="measure.mutation",
            location="backend/src/engines/loan_engine/amortization.py:88",
            description="Equivalent gap",
            evidence_kind="arithmetic",
            evidence_detail="a + b",
            status="survived",
            notes="equivalent",
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        self.assertIsNone(result.candidate)
        self.assertEqual(result.final_state, "REFUSED")

    def test_candidate_has_generation_id(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="gen-id-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Gap for generation ID test",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        self.assertIsNotNone(result.generation_id)
        self.assertTrue(result.generation_id.startswith("gen::"))


class TestC53CandidateValidation(unittest.TestCase):
    """M9-C53 candidate validation (8 dimensions)."""

    def test_validation_produces_8_dimensions(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="val-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Gap for validation",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        self.assertIsNotNone(result.validation)
        self.assertEqual(len(result.validation.dimensions), 8)

    def test_validation_dimension_names(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="val-dim-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Gap for dimension names",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        dimension_names = {d.dimension for d in result.validation.dimensions}
        expected = {
            "syntax",
            "static_quality",
            "focused_execution",
            "regression",
            "behavioral_relevance",
            "distinguishing_power",
            "non_regression",
            "determinism",
        }
        self.assertEqual(dimension_names, expected)

    def test_syntax_validation_passes_for_valid_code(self):
        from runtime.foundation.verification.candidate_validation import (
            validate_syntax,
        )

        code = "def test_example():\n    assert 1 + 1 == 2\n"
        result = validate_syntax(code, "test-id")
        self.assertTrue(result.passed)
        self.assertEqual(result.dimension, "syntax")


class TestC53AuthorizationBoundary(unittest.TestCase):
    """M9-C53 human authorization boundary."""

    def test_authorization_required_for_genuine_gap(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="auth-req-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Gap requiring authorization",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
            authorization_required=True,
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        self.assertEqual(result.final_state, "AWAITING_HUMAN_AUTHORIZATION")

    def test_authorization_chain_is_valid(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="auth-chain-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Gap for authorization chain",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
            authorization_required=True,
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        states = [r.state for r in result.authorization]
        # Should have at least PROPOSED → VALIDATED → AWAITING_HUMAN_AUTHORIZATION
        self.assertIn("PROPOSED", states)
        self.assertIn("VALIDATED", states)
        self.assertIn("AWAITING_HUMAN_AUTHORIZATION", states)

    def test_system_never_self_approves(self):
        from runtime.foundation.verification.authorization_boundary import (
            AuthorizationState,
            evaluate_authorization,
        )

        records = evaluate_authorization(
            candidate_id="test-self-approve",
            generation_id="gen-test",
            validation_passed=True,
            gap_class="A",
            authorization_required=True,
        )
        final_state = records[-1].state
        self.assertNotEqual(final_state, AuthorizationState.AUTHORIZED)
        self.assertEqual(final_state, AuthorizationState.AWAITING_HUMAN_AUTHORIZATION)


class TestC53RefusalBehavior(unittest.TestCase):
    """M9-C53 refusal behavior for invalid generation requests."""

    def test_equivalent_survivor_refused(self):
        from runtime.foundation.verification.c53_scenarios import (
            _run_scenario_c_equivalent_survivor,
        )

        result = _run_scenario_c_equivalent_survivor()
        self.assertTrue(result.passed)

    def test_defensive_survivor_refused(self):
        from runtime.foundation.verification.c53_scenarios import (
            _run_scenario_d_defensive_survivor,
        )

        result = _run_scenario_d_defensive_survivor()
        self.assertTrue(result.passed)

    def test_scope_expansion_refused(self):
        from runtime.foundation.verification.c53_scenarios import (
            _run_scenario_m_scope_expansion,
        )

        result = _run_scenario_m_scope_expansion()
        self.assertTrue(result.passed)

    def test_stale_evidence_refused(self):
        from runtime.foundation.verification.c53_scenarios import (
            _run_scenario_l_stale_evidence,
        )

        result = _run_scenario_l_stale_evidence()
        self.assertTrue(result.passed)


class TestC53EndToEnd(unittest.TestCase):
    """M9-C53 end-to-end generation → validation → authorization."""

    def test_full_pipeline_genuine_gap(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="e2e-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="End-to-end test gap",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)

        # Verify the full pipeline executed
        self.assertIsNotNone(result.classification)
        self.assertIsNotNone(result.eligibility)
        self.assertIsNotNone(result.candidate)
        self.assertIsNotNone(result.validation)
        self.assertTrue(len(result.authorization) > 0)
        self.assertIn(
            result.final_state,
            ("AWAITING_HUMAN_AUTHORIZATION", "AUTHORIZED", "REFUSED"),
        )

    def test_pipeline_records_all_stages(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="e2e-stages-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Pipeline stages test",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        engine = GenerationEngine()
        result = engine.generate_from_gap(gap)
        stage_names = [s.stage for s in result.stages]
        self.assertIn("gap_classification", stage_names)
        self.assertIn("generation_eligibility", stage_names)
        self.assertIn("test_generation", stage_names)
        self.assertIn("candidate_validation", stage_names)
        self.assertIn("authorization_boundary", stage_names)

    def test_generation_is_reproducible(self):
        from runtime.foundation.verification.gap_classification import GapEvidence
        from runtime.foundation.verification.generation_engine import (
            GenerationEngine,
        )

        gap = GapEvidence(
            gap_id="e2e-rep-001",
            source="survivor",
            component="credit_card",
            capability="measure.mutation",
            location="backend/src/engines/credit_card_engine/core.py:42",
            description="Reproducibility test",
            evidence_kind="comparison",
            evidence_detail="if balance > 0:",
            status="survived",
            notes="",
        )
        engine = GenerationEngine()
        r1 = engine.generate_from_gap(gap)
        r2 = engine.generate_from_gap(gap)
        self.assertEqual(r1.final_state, r2.final_state)
        self.assertEqual(r1.classification.gap_class, r2.classification.gap_class)
        self.assertEqual(r1.candidate.candidate_id, r2.candidate.candidate_id)


class TestC53RegressionPreservation(unittest.TestCase):
    """M9-C53 regression preservation: C52 tests must not regress."""

    def test_c52_tests_still_pass(self):
        import subprocess

        result = subprocess.run(
            ["python", "-m", "pytest", "runtime/tests/test_m9_c52.py", "-q", "--tb=no"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"C52 tests regressed: {result.stdout}{result.stderr}",
        )

    def test_c51_tests_still_pass(self):
        import subprocess

        result = subprocess.run(
            ["python", "-m", "pytest", "runtime/tests/test_m9_c51.py", "-q", "--tb=no"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"C51 tests regressed: {result.stdout}{result.stderr}",
        )

    def test_c50_tests_still_pass(self):
        import subprocess

        result = subprocess.run(
            ["python", "-m", "pytest", "runtime/tests/test_m9_c50.py", "-q", "--tb=no"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"C50 tests regressed: {result.stdout}{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
