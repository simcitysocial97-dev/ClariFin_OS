"""M9-C55 — Semantic Diagnostics E2E Tests.

Traces FinancialInvariantViolation through parser and formatter to verify
human-readable diagnostic output.
"""
from __future__ import annotations

import pytest

from runtime.foundation.verification.semantics.assertions import (
    FinancialAssertion,
    FinancialInvariantViolation,
)
from runtime.foundation.verification.semantics.parser import SemanticFailureParser
from runtime.foundation.verification.diagnostics.formatter import (
    DiagnosticFormatter,
    EnrichedFailureReport,
)


class TestSemanticDiagnosticsE2E:
    """End-to-end semantic failure pipeline."""

    def test_full_diagnostic_pipeline(self):
        try:
            FinancialAssertion.closure_zero_balance(final_balance=1000)
            pytest.fail("Expected FinancialInvariantViolation")
        except FinancialInvariantViolation as exc:
            parsed = SemanticFailureParser.parse(str(exc))
            assert parsed is not None
            assert parsed.invariant_id == "closure_requires_zero_balance"
            assert parsed.expected == "final_balance == 0"
            assert "1000" in str(parsed.actual)
            assert parsed.remediation is not None

            report = EnrichedFailureReport(
                classification="TEST_FAILURE",
                unit_id="test_semantic",
                command="pytest test_semantic_diagnostics_e2e.py",
                exit_code=1,
                failure_summary="Semantic failure",
                test_failure_count=1,
                root_failure="test_full_diagnostic_pipeline",
                diagnostic=str(exc),
                evidence_path=None,
                semantic_failure=parsed,
            )
            formatted = DiagnosticFormatter.format(report)
            assert "FINANCIAL INVARIANT VIOLATED" in formatted
            assert "closure_requires_zero_balance" in formatted
            assert "final_balance == 0" in formatted
            assert "1000" in formatted

    def test_diagnostic_agent_has_q10_q11(self):
        from runtime.foundation.verification.diagnostic_agent import DiagnosticAgent
        agent = DiagnosticAgent()
        assert hasattr(agent, "_answer_q10")
        assert hasattr(agent, "_answer_q11")
