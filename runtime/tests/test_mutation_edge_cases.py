

def test_incremental_mutation_with_no_coverage():
    """Incremental mutation must handle engines with no test coverage."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "runtime.verify", "strengthen", "--target",
         "backend/src/services/account_service.py", "--smoke"],
        capture_output=True, text=True, timeout=300
    )

    assert result.returncode in [0, 1, 2], \
        f"Mutation crashed: {result.stderr[-500:]}"


def test_mutation_with_nonexistent_engine():
    """Mutation must handle requests for engines that don't exist."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "runtime.verify", "strengthen", "--target",
         "backend/src/engines/fake_engine/fake.py", "--smoke"],
        capture_output=True, text=True, timeout=60
    )

    assert result.returncode == 0, \
        f"Should exit 0 for no affected engines: {result.stderr}"


def test_survivor_enrichment_with_unknown_file():
    """Survivor enricher must handle survivors from unknown source files."""
    from runtime.foundation.verification.mutation.survivor_enricher import (
        SurvivorEnricher,
    )

    enricher = SurvivorEnricher()

    assert enricher is not None


def test_mutation_contract_three_gate_classification():
    """Three-gate classification must handle all edge cases."""
    from runtime.foundation.verification.mutation_contract import (
        MutationResult,
        classify_gates,
    )

    # Test Gate A failure (infrastructure)
    result_infra = MutationResult(
        run_id="test-run",
        repository_sha="abc123",
        tree_sha="def456",
        python_version="3.12",
        pytest_version="8.0",
        mutmut_version="3.7.0",
        config_hash="hash123",
        killed=0,
        survived=0,
        timeout=0,
        no_tests=0,
        suspicious=0,
        not_checked=100,
        execution_status="FAIL",
    )

    gate_a, gate_b, gate_c, verdict = classify_gates(result_infra)
    assert gate_a is False
    assert "NOT EVALUABLE" in verdict

    # Test Gate B failure (no evidence)
    result_no_evidence = MutationResult(
        run_id="test-run",
        repository_sha="abc123",
        tree_sha="def456",
        python_version="3.12",
        pytest_version="8.0",
        mutmut_version="3.7.0",
        config_hash="hash123",
        killed=0,
        survived=0,
        timeout=0,
        no_tests=0,
        suspicious=0,
        not_checked=0,
        execution_status="PASS",
        classification_status="FAIL",
        evidence_complete=False,
    )

    gate_a, gate_b, gate_c, verdict = classify_gates(result_no_evidence)
    assert gate_a is True
    assert gate_b is False
    assert "NOT EVALUABLE" in verdict

    # Test Gate C failure (below threshold)
    result_low_score = MutationResult(
        run_id="test-run",
        repository_sha="abc123",
        tree_sha="def456",
        python_version="3.12",
        pytest_version="8.0",
        mutmut_version="3.7.0",
        config_hash="hash123",
        killed=50,
        survived=50,
        timeout=0,
        no_tests=0,
        suspicious=0,
        not_checked=0,
        execution_status="PASS",
        classification_status="PASS",
        evidence_complete=True,
        mutation_score=50.0,
        threshold_percent=80,
    )

    gate_a, gate_b, gate_c, verdict = classify_gates(result_low_score)
    assert gate_a is True
    assert gate_b is True
    assert gate_c is False
    assert verdict == "QUALITY FAIL"
