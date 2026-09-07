#!/usr/bin/env python3
"""Proof Experiment 3: Controlled Environment Failure"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

def test_infrastructure_failure_builder():
    print("\n[Test 1] Infrastructure failure builder")
    
    from runtime.foundation.verification.mutation_contract import build_infrastructure_failure, classify_gates
    
    result = build_infrastructure_failure(
        run_id='proof-exp-3-test',
        repository_sha='test-sha',
        tree_sha='test-tree-sha',
        python_version='3.12.0',
        pytest_version='7.4.0',
        mutmut_version='3.7.0',
        config_hash='test-config-hash',
        error='test infrastructure failure',
        mode='smoke',
        target='account_engine'
    )
    
    assert result.execution_status == "INFRASTRUCTURE_FAILURE"
    assert result.classification_status == "FAIL"
    assert result.mutation_score is None
    
    gate_a, gate_b, gate_c, verdict = classify_gates(result)
    assert gate_a == False
    assert "NOT EVALUABLE" in verdict
    
    print("  PASS: Infrastructure failure correctly classified")
    return result


def test_missing_test_paths_detection():
    print("\n[Test 2] Missing test paths detection")
    
    from runtime.foundation.verification.mutation_contract import ENGINE_SELECTION
    from runtime.foundation.verification.env import REPO_ROOT as ENV_REPO_ROOT
    
    missing = []
    for engine, sel in ENGINE_SELECTION.items():
        for test_path in sel.test_selection:
            full_path = ENV_REPO_ROOT / "backend" / test_path
            if not full_path.exists():
                missing.append(test_path)
    
    if missing:
        print(f"  WARN: Found missing test paths: {missing}")
    else:
        print("  PASS: All test paths exist")
    
    return len(missing) == 0


def test_baseline_gate_validation():
    print("\n[Test 3] Baseline gate validation")
    
    from runtime.foundation.verification.env import resolve_environment
    
    env = resolve_environment(config_dir=REPO_ROOT / "backend")
    
    if env.consistent:
        print("  PASS: Environment is consistent")
    else:
        print(f"  FAIL: Environment issues: {env.errors}")
    
    return env.consistent


if __name__ == "__main__":
    print("=" * 60)
    print("M9-C57 Proof Experiment 3: Controlled Environment Failure")
    print("=" * 60)
    
    r1 = test_infrastructure_failure_builder()
    r2 = test_missing_test_paths_detection()
    r3 = test_baseline_gate_validation()
    
    print("\n" + "=" * 60)
    if all([r1 is not None, r2, r3]):
        print("Proof Experiment 3: ALL TESTS PASSED")
    else:
        print("Proof Experiment 3: SOME TESTS FAILED")
    print("=" * 60)
