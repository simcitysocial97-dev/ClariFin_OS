# runtime/tests/test_m9_c48_mutation_unified.py
#
# M9-C48 A3 acceptance tests for the unified MutationResult projection.

from __future__ import annotations

from dataclasses import dataclass

from runtime.foundation.verification.mutation_contract import MutationResult
from runtime.foundation.verification.mutation_result_unified import (
    _ORCH_TO_CANON,
    project_orchestrator_to_canonical,
)


@dataclass
class FakeOrch:
    killed: int = 0
    survived: int = 0
    equivalent: int = 0
    no_tests: int = 0
    timeout: int = 0
    execution_error: int = 0
    invalid_mutant: int = 0
    not_executed: int = 0
    cancelled: int = 0
    unknown: int = 0


def _project(orch: FakeOrch, **overrides):
    defaults = dict(
        run_id="mut-test",
        repository_sha="abc",
        tree_sha="def",
        python_version="3.12",
        pytest_version="8.0",
        mutmut_version="3.7.0",
        config_hash="cfg",
    )
    defaults.update(overrides)
    return project_orchestrator_to_canonical(orchestrator_result=orch, **defaults)


def test_equivalent_collapses_to_survived():
    proj = _project(FakeOrch(killed=4, survived=2, equivalent=2))
    assert proj.canonical.survived == 4  # 2 base + 2 equivalent
    assert proj.orchestrator_provenance["equivalent"] == 2
    assert proj.canonical.mutation_score == 50.0


def test_execution_error_marks_infra_failure():
    proj = _project(FakeOrch(execution_error=3))
    assert proj.canonical.execution_status == "INFRASTRUCTURE_FAILURE"
    assert proj.canonical.mutation_score is None
    assert proj.canonical.not_checked == 3


def test_mixed_execution_error_does_not_mark_infra_failure():
    proj = _project(FakeOrch(execution_error=3, killed=1))
    assert proj.canonical.execution_status == "PASS"
    assert proj.canonical.not_checked == 3
    assert proj.canonical.killed == 1


def test_no_tests_bucket():
    proj = _project(FakeOrch(killed=3, no_tests=2))
    assert proj.canonical.no_tests == 2
    assert proj.canonical.mutation_score == 100.0


def test_invalid_mutant_collapses_to_suspicious():
    proj = _project(FakeOrch(invalid_mutant=2))
    assert proj.canonical.suspicious == 2
    assert proj.canonical.mutation_score is None  # denom=0


def test_zero_denom_score_is_none():
    proj = _project(FakeOrch(no_tests=2))
    assert proj.canonical.mutation_score is None


def test_all_orchestrator_states_are_mapped():
    # Every orchestrator state must appear in the map.
    required = {
        "killed",
        "survived",
        "equivalent",
        "no_tests",
        "timeout",
        "execution_error",
        "invalid_mutant",
        "not_executed",
        "cancelled",
        "unknown",
    }
    assert required.issubset(set(_ORCH_TO_CANON.keys()))


def test_canonical_result_is_mutation_contract_type():
    proj = _project(FakeOrch(killed=1))
    assert isinstance(proj.canonical, MutationResult)


def test_to_dict_roundtrip():
    proj = _project(FakeOrch(killed=3, survived=2))
    d = proj.to_dict()
    assert d["canonical"]["killed"] == 3
    assert d["canonical"]["survived"] == 2
    assert d["projection"] == "m9-c48/mutation-result-unified@1"
    assert "orchestrator_provenance" in d


def test_provenance_retains_rich_taxonomy():
    proj = _project(
        FakeOrch(killed=5, survived=2, equivalent=1, no_tests=1, timeout=1)
    )
    p = proj.orchestrator_provenance
    assert p == {
        "killed": 5,
        "survived": 2,
        "equivalent": 1,
        "no_tests": 1,
        "timeout": 1,
        "execution_error": 0,
        "invalid_mutant": 0,
        "not_executed": 0,
        "cancelled": 0,
        "unknown": 0,
    }


def test_execution_path_is_preserved():
    proj = _project(
        FakeOrch(killed=1),
        execution_path="VERIFICATION_CONTROL_PLANE",
    )
    assert proj.canonical.execution_path == "VERIFICATION_CONTROL_PLANE"
