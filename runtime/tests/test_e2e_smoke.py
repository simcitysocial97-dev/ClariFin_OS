"""
M9-C57 — End-to-end smoke test for the semantic verification pipeline.

Validates the full pipeline: change detection → blast radius → semantic
impact → test selection → execution → semantic failure diagnosis.

Runnable locally and in CI; no GPU or heavy infrastructure required.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Tier 1 — Blast radius & semantic impact
# ---------------------------------------------------------------------------


def test_semantic_blast_radius():
    """Verify blast radius computes financial concepts for engine changes."""
    from runtime.foundation.verification.blast_radius import BlastRadiusEngine  # noqa: PLC0415

    engine = BlastRadiusEngine()
    contract = engine.compute(
        explicit_files=["backend/src/engines/loan_engine/emi.py"]
    )

    assert contract.directly_affected_capabilities, "Should detect affected capabilities"
    assert contract.affected_components, "Should detect affected components"
    assert "loan-engine" in contract.directly_affected_capabilities


def test_financial_blast_radius_concepts():
    """Verify _FinancialBlastRadius maps files to concepts correctly."""
    from runtime.foundation.verification.semantics.blast_radius import (  # noqa: PLC0415
        _FinancialBlastRadius,
    )

    changed = ["backend/src/engines/loan_engine/emi.py"]
    affected = _FinancialBlastRadius.compute_affected_concepts(changed)
    assert "emi_calculation" in affected
    assert "interest_computation" in affected

    at_risk = _FinancialBlastRadius.compute_at_risk_invariants(affected)
    assert "emi_must_exceed_interest" in at_risk
    assert "total_payment_covers_principal" in at_risk


def test_financial_blast_radius_transitive():
    """Transitive closure expands downstream concepts."""
    from runtime.foundation.verification.semantics.blast_radius import (  # noqa: PLC0415
        _FinancialBlastRadius,
    )

    initial = ["emi_calculation"]
    closure = _FinancialBlastRadius.compute_transitive_closure(initial)
    assert "emi_calculation" in closure
    assert "schedule_generation" in closure  # depends on emi_calculation


# ---------------------------------------------------------------------------
# Semantic assertion / parser round-trip
# ---------------------------------------------------------------------------


def test_semantic_assertion_failure_format():
    """Verify FinancialInvariantViolation produces parseable output."""
    from runtime.foundation.verification.semantics.assertions import (  # noqa: PLC0415
        FinancialAssertion,
        FinancialInvariantViolation,
    )
    from runtime.foundation.verification.semantics.parser import (  # noqa: PLC0415
        SemanticFailureParser,
    )

    with pytest.raises(FinancialInvariantViolation):
        FinancialAssertion.closure_zero_balance(100, context={"loan_id": "TEST"})

    try:
        FinancialAssertion.closure_zero_balance(100, context={"loan_id": "TEST"})
    except FinancialInvariantViolation as exc:
        failure_output = str(exc)
        parsed = SemanticFailureParser.parse(failure_output)
        assert parsed is not None
        assert parsed.invariant_id == "closure_requires_zero_balance"
        assert parsed.remediation is not None
        assert "payment" in parsed.remediation.lower() or "rounding" in parsed.remediation.lower()


def test_semantic_parser_no_match():
    """Parser returns None for non-semantic failure messages."""
    from runtime.foundation.verification.semantics.parser import (  # noqa: PLC0415
        SemanticFailureParser,
    )

    result = SemanticFailureParser.parse("this is not a semantic failure")
    assert result is None


def test_semantic_parser_extract_multiple():
    """Parser extracts all SemanticFailure occurrences from a traceback."""
    from runtime.foundation.verification.semantics.parser import (  # noqa: PLC0415
        SemanticFailureParser,
    )

    tb = (
        "Financial Invariant Violated: emi_must_exceed_interest\n"
        "  Invariant: EMI must exceed monthly interest\n"
        "  Expected: emi > interest\n"
        "  Actual: emi <= interest\n"
        "Financial Invariant Violated: closure_requires_zero_balance\n"
        "  Invariant: Loan closure requires final balance to be zero\n"
        "  Expected: final_balance == 0\n"
        "  Actual: final_balance == 500\n"
    )
    failures = SemanticFailureParser.extract_from_traceback(tb)
    assert len(failures) == 2
    assert failures[0].invariant_id == "emi_must_exceed_interest"
    assert failures[1].invariant_id == "closure_requires_zero_balance"


# ---------------------------------------------------------------------------
# Frontend-backend mapping
# ---------------------------------------------------------------------------


def test_frontend_backend_mapping():
    """Verify consumer map is populated."""
    from runtime.foundation.verification.frontend_backend_map import (  # noqa: PLC0415
        FrontendBackendMapper,
    )

    mapper = FrontendBackendMapper()
    result = mapper.build_consumer_map()
    assert len(result) > 10, f"Expected >10 endpoints, got {len(result)}"


# ---------------------------------------------------------------------------
# Regression detector round-trip
# ---------------------------------------------------------------------------


def test_regression_detector_roundtrip():
    """Verify metrics storage and retrieval."""
    from runtime.foundation.verification.regression_detector import (  # noqa: PLC0415
        RegressionDetector,
        RunMetrics,
    )

    detector = RegressionDetector()
    run_id = f"smoke-{int(time.time())}"
    metrics = RunMetrics(
        run_id=run_id,
        timestamp="2024-01-01T00:00:00",
        branch="smoke-test",
        commit_sha="abc123",
        coverage_pct=75.0,
        mutation_score=82.0,
        test_count=500,
        passed=495,
        failed=5,
        duration_seconds=120,
    )
    detector.store_run_metrics(run_id, "smoke-test", metrics.__dict__)
    baseline = detector.get_baseline_metrics("smoke-test")
    assert baseline is not None
    assert baseline["coverage_pct"] == 75.0

    report = RegressionDetector.detect_regressions(metrics.__dict__, baseline)
    assert report.has_regression is False  # Same metrics, no regression


def test_regression_detector_detects_drop():
    """Regression detected when current < baseline significantly."""
    from runtime.foundation.verification.regression_detector import (  # noqa: PLC0415
        RegressionDetector,
    )

    baseline = {
        "coverage_pct": 90.0,
        "mutation_score": 85.0,
        "test_count": 500,
    }
    current = {
        "coverage_pct": 70.0,  # -20% drop → CRITICAL
        "mutation_score": 60.0,  # -25% drop → CRITICAL
        "test_count": 300,  # -40% drop → WARNING
    }
    report = RegressionDetector.detect_regressions(current, baseline)
    assert report.has_regression is True
    assert any("CRITICAL" in a for a in report.alerts)
    assert report.coverage_delta == -20.0


# ---------------------------------------------------------------------------
# E2E route mapper
# ---------------------------------------------------------------------------


def test_e2e_route_mapper():
    """Verify E2ERouteMapper scans routes and builds mapping."""
    from runtime.foundation.verification.e2e_route_mapper import (  # noqa: PLC0415
        E2ERouteMapper,
    )

    mapper = E2ERouteMapper()
    routes = mapper.scan_frontend_routes()
    assert isinstance(routes, list)
    # Root route is always present
    assert "/" in routes


def test_e2e_coverage_summary():
    """Coverage summary returns valid structure."""
    from runtime.foundation.verification.e2e_route_mapper import (  # noqa: PLC0415
        E2ERouteMapper,
    )

    mapper = E2ERouteMapper()
    summary = mapper.get_coverage_summary()
    assert "total_routes" in summary
    assert "covered_routes" in summary
    assert "uncovered_routes" in summary
    assert "coverage_pct" in summary


# ---------------------------------------------------------------------------
# Parallel executor integration
# ---------------------------------------------------------------------------


def test_parallel_executor_planning():
    """ParallelExecutor correctly plans independent vs dependent groups."""
    from runtime.foundation.verification.parallel_executor import (  # noqa: PLC0415
        ParallelExecutor,
        TaskGroup,
    )

    executor = ParallelExecutor(max_workers=2)

    # Mock tasks with task_id, dependencies
    class _Task:
        def __init__(self, task_id: str, depends_on: tuple[str, ...] = ()):
            self.task_id = task_id
            self.depends_on = depends_on
            self.execution_command = "true"
            self.component = "test"
            self.capability = "test"

    t1 = _Task("A", ())
    t2 = _Task("B", ())
    t3 = _Task("C", ("A",))

    groups = executor.plan_parallel_groups([t1, t2, t3])
    assert len(groups) >= 1

    # At least one group should be parallel (A and B are independent)
    parallel_count = sum(1 for g in groups if g.parallel)
    assert parallel_count >= 1


def test_parallel_executor_execution():
    """ParallelExecutor runs simple commands and reports results."""
    from runtime.foundation.verification.parallel_executor import (  # noqa: PLC0415
        ExecutionReport,
        ParallelExecutor,
    )

    executor = ParallelExecutor(max_workers=2)

    class _Task:
        def __init__(self, task_id: str, command: str):
            self.task_id = task_id
            self.execution_command = command
            self.component = "test"
            self.capability = "test"

    tasks = [
        _Task("pass-1", "echo ok"),
        _Task("pass-2", "echo ok"),
    ]

    report = executor.execute_parallel(
        [ParallelExecutor(max_workers=2).plan_parallel_groups(tasks)[0]],
        plan_id="smoke",
    )
    assert isinstance(report, ExecutionReport)
    assert report.exit_code == 0
    assert all(r.success for r in report.results)


# ---------------------------------------------------------------------------
# Diagnostic agent Q10/Q11 integration
# ---------------------------------------------------------------------------


def test_diagnostic_q10_financial_semantics():
    """DiagnosticAgent surfaces financial invariant violation from record."""
    from runtime.foundation.verification.diagnostic_agent import (  # noqa: PLC0415
        DiagnosticForensicAgent,
    )

    agent = DiagnosticForensicAgent()
    record = {
        "record_id": "test-1",
        "repository_sha": "abc123",
        "change": {"changed_files": []},
        "affected_graph_nodes": {},
        "invalidations": {},
        "reused_evidence": {},
        "selected_tasks": {"components": [], "count": 0},
        "executed_tasks": {"components": [], "count": 0},
        "execution_results": {
            "by_component": {
                "loan-engine": {
                    "failure_kind": "verification_failure",
                    "semantic_failure": {
                        "invariant_id": "closure_requires_zero_balance",
                        "description": "Loan closure requires final balance to be zero",
                        "source_file": "backend/src/engines/loan_engine/foreclosure.py",
                        "remediation": "Verify all payments applied",
                    },
                }
            }
        },
        "new_evidence": {},
        "derived_evidence": {},
        "failures": {"count": 1, "by_component": {}},
        "uncertainties": {},
        "certification_decision": {},
    }

    report = agent.diagnose(record)
    assert report.q10_financial_diagnosis.get("invariant_violated") == "closure_requires_zero_balance"
    assert report.q11_minimal_fix.get("invariant_id") == "closure_requires_zero_balance"


def test_diagnostic_q10_none_when_no_semantic_failure():
    """Q10 returns 'none' when no semantic failure is present."""
    from runtime.foundation.verification.diagnostic_agent import (  # noqa: PLC0415
        DiagnosticForensicAgent,
    )

    agent = DiagnosticForensicAgent()
    record = {
        "record_id": "test-2",
        "repository_sha": "abc123",
        "change": {"changed_files": []},
        "affected_graph_nodes": {},
        "invalidations": {},
        "reused_evidence": {},
        "selected_tasks": {"components": [], "count": 0},
        "executed_tasks": {"components": [], "count": 0},
        "execution_results": {"by_component": {}},
        "new_evidence": {},
        "derived_evidence": {},
        "failures": {"count": 0, "by_component": {}},
        "uncertainties": {},
        "certification_decision": {},
    }

    report = agent.diagnose(record)
    assert report.q10_financial_diagnosis.get("financial_diagnosis") == "none"


# ---------------------------------------------------------------------------
# Survivor enricher integration
# ---------------------------------------------------------------------------


def test_survivor_enricher_loads_catalog():
    """SurvivorEnricher handles missing catalog gracefully."""
    from runtime.foundation.verification.mutation.survivor_enricher import (  # noqa: PLC0415
        SurvivorEnricher,
    )

    enricher = SurvivorEnricher()
    results = enricher.enrich("/tmp/nonexistent-catalog.json")
    assert results == []


def test_survivor_enricher_enriches_record():
    """SurvivorEnricher attaches concept + invariant to a survivor dict."""
    from runtime.foundation.verification.mutation.survivor_enricher import (  # noqa: PLC0415
        SurvivorEnricher,
    )

    enricher = SurvivorEnricher()
    survivors = [
        {
            "survivor_id": "mut-1",
            "source_file": "src/engines/loan_engine/emi.py",
            "mutation_type": "operator",
            "component": "loan_engine",
            "original_expression": "emi = principal * r",
            "mutated_expression": "emi = principal * r + 1",
        }
    ]
    results = enricher.enrich_batch(survivors)
    assert len(results) == 1
    assert results[0].concept_id in ("emi_calculation", "interest_computation")
    assert results[0].at_risk_invariant in (
        "emi_must_exceed_interest",
        "total_payment_covers_principal",
    )
    assert results[0].suggested_test_name.startswith("test_")


# ---------------------------------------------------------------------------
# Workflow convergence
# ---------------------------------------------------------------------------


def test_workflow_convergence_inventory():
    """Workflow convergence inventory loads without error."""
    from runtime.foundation.verification.workflow_convergence import (  # noqa: PLC0415
        inventory_workflows,
    )

    workflows = inventory_workflows()
    assert isinstance(workflows, list)
    assert len(workflows) > 0


def test_workflow_convergence_gates():
    """Certification gates evaluate to a list of gate results."""
    from runtime.foundation.verification.workflow_convergence import (  # noqa: PLC0415
        evaluate_certification_gates,
    )

    result = evaluate_certification_gates([], [], [], [], [], sha="smoke")
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Evidence schema
# ---------------------------------------------------------------------------


def test_evidence_schema_coverage():
    """CoverageEvidence serialises correctly."""
    from runtime.foundation.verification.evidence_schema import (  # noqa: PLC0415
        CoverageEvidence,
    )

    ev = CoverageEvidence(percentage=85.0, covered_lines=1000, total_lines=1200)
    d = ev.to_dict()
    assert d["percentage"] == 85.0
    assert ev.to_json()  # JSON round-trip


def test_evidence_schema_mutation():
    """MutationEvidence serialises correctly."""
    from runtime.foundation.verification.evidence_schema import (  # noqa: PLC0415
        MutationEvidence,
    )

    ev = MutationEvidence(score=82.0, killed=100, survived=18)
    d = ev.to_dict()
    assert d["score"] == 82.0


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------


def test_config_loader_thresholds():
    """Config loader returns configured thresholds with fallback defaults."""
    from runtime.foundation.verification.config_loader import (  # noqa: PLC0415
        get_threshold,
    )

    # Known key from verification.yaml
    mut_threshold = get_threshold("mutation_thresholds", "full_campaign", 80)
    assert isinstance(mut_threshold, (int, float))
    assert mut_threshold > 0

    # Missing key falls back to default
    assert get_threshold("nonexistent", "key", 42) == 42
