# runtime/tests/test_mutation_infra.py
#
# M9-C42.5 — Mutation infrastructure regression tests.
#
# These verify the VERIFICATION FRAMEWORK (not domain code):
#   * result/evidence contract parsing & arithmetic reconciliation,
#   * three-gate classification,
#   * infrastructure failure must NOT produce a mutation score,
#   * cache invalidation,
#   * forbidden-venv detection (permanent environment guard),
#   * end-to-end smoke proving killed/survived/no-test are distinguished.

from __future__ import annotations

from pathlib import Path

from runtime.foundation.verification import mutation_contract as mc
from runtime.foundation.verification.env import (
    FORBIDDEN_VENV_DIRS,
    resolve_environment,
)
from runtime.foundation.verification.mutation_runner import (
    _validate_cache,
    execute_mutation,
)

# ── 1. Valid mutant classification parsing ──────────────────────────────────
SAMPLE = """
    engines.foo.x_bar__mutmut_1: killed
    engines.foo.x_bar__mutmut_2: survived
    engines.foo.x_bar__mutmut_3: no tests
    engines.foo.x_bar__mutmut_4: timeout
    engines.foo.x_bar__mutmut_5: suspicious
    engines.foo.x_bar__mutmut_6: not checked
"""


def test_parse_mutmut_results_buckets():
    c = mc.parse_mutmut_results(SAMPLE)
    assert c.killed == 1
    assert c.survived == 1
    assert c.no_tests == 1
    assert c.timeout == 1
    assert c.suspicious == 1
    assert c.not_checked == 1
    assert c.generated == 6


# ── 2. Killed mutant ─────────────────────────────────────────────────────────
def test_parse_mutmut_results_killed():
    c = mc.parse_mutmut_results("a.x__mutmut_1: killed\n")
    assert c.killed == 1
    assert c.generated == 1


# ── 3. Surviving mutant ──────────────────────────────────────────────────────
def test_parse_mutmut_results_survived():
    c = mc.parse_mutmut_results("a.x__mutmut_1: survived\n")
    assert c.survived == 1


# ── 4. No-test mutant ───────────────────────────────────────────────────────
def test_parse_mutmut_results_no_tests():
    c = mc.parse_mutmut_results("a.x__mutmut_1: no tests\n")
    assert c.no_tests == 1


# ── 5. Timeout mutant ───────────────────────────────────────────────────────
def test_parse_mutmut_results_timeout():
    c = mc.parse_mutmut_results("a.x__mutmut_1: timeout\n")
    assert c.timeout == 1


# ── 6. Not-checked mutant ───────────────────────────────────────────────────
def test_parse_mutmut_results_not_checked():
    c = mc.parse_mutmut_results("a.x__mutmut_1: not checked\n")
    assert c.not_checked == 1


# ── 7. Missing mutant identifier / malformed output ─────────────────────────
def test_parse_mutmut_results_malformed_lines_ignored():
    # Lines that are not <name>: <status> are ignored; unknown statuses -> not_checked.
    c = mc.parse_mutmut_results("just some log line\nweirdstatus: bogus\n")
    assert c.not_checked == 1
    assert c.generated == 1


# ── 8. Empty mutation result ────────────────────────────────────────────────
def test_parse_mutmut_results_empty():
    c = mc.parse_mutmut_results("")
    assert c.generated == 0


# ── 9. Arithmetic reconciliation ────────────────────────────────────────────
def test_reconcile_counts_invariant():
    c = mc.MutationCounts(killed=4, survived=3, no_tests=2, timeout=1, suspicious=0, not_checked=1)
    assert mc.reconcile_counts(c) is True
    assert c.generated == 11


def test_reconcile_counts_mismatch():
    c = mc.MutationCounts(killed=1, survived=1)
    # Provided total disagrees with summed buckets.
    assert mc.reconcile_counts(c, generated=99) is False


# ── 10. Configuration/version mismatch (env guard) ──────────────────────────
def test_env_forbidden_venv_detection(monkeypatch, tmp_path):
    fake = tmp_path / "backend" / "venv"
    fake.mkdir(parents=True)
    monkeypatch.setattr(
        "runtime.foundation.verification.env.FORBIDDEN_VENV_DIRS", [fake]
    )
    report = resolve_environment()
    assert report.consistent is False
    assert any("venv" in v for v in report.forbidden_venvs)


def test_env_consistent_when_clean():
    # Current repo has no forbidden venv and mutmut 3.7.0 installed.
    report = resolve_environment()
    assert report.consistent is True
    assert report.forbidden_venvs == ()


# ── 11. Stale cache detection ───────────────────────────────────────────────
def test_cache_invalidation_on_sha_mismatch(tmp_path):
    cache = tmp_path / ".mutmut-cache"
    cache.mkdir()
    (cache / "provenance.json").write_text(
        '{"repository_sha":"deadbeef","config_hash":"x","mutmut_version":"3.7.0"}'
    )
    _validate_cache(tmp_path, no_cache=False, config_hash="abc")
    assert not cache.exists()


def test_cache_kept_when_provenance_matches(tmp_path):
    import subprocess

    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    cache = tmp_path / ".mutmut-cache"
    cache.mkdir()
    (cache / "provenance.json").write_text(
        f'{{"repository_sha":"{sha}","config_hash":"abc","mutmut_version":"3.7.0"}}'
    )
    _validate_cache(tmp_path, no_cache=False, config_hash="abc")
    assert cache.exists()


def test_cache_discarded_with_no_cache_flag(tmp_path):
    cache = tmp_path / ".mutmut-cache"
    cache.mkdir()
    _validate_cache(tmp_path, no_cache=True, config_hash="abc")
    assert not cache.exists()


# ── 12. Infrastructure failure must NOT produce a mutation score ─────────────
def test_infrastructure_failure_has_no_score():
    r = mc.build_infrastructure_failure(
        run_id="x",
        repository_sha="s",
        tree_sha="t",
        python_version="3.12",
        pytest_version="9.1.1",
        mutmut_version="3.7.0",
        config_hash="h",
        error="boom",
    )
    assert r.mutation_score is None
    assert r.execution_status == "INFRASTRUCTURE_FAILURE"
    assert r.evidence_complete is False
    gate_a, gate_b, gate_c, verdict = mc.classify_gates(r)
    assert gate_a is False
    assert gate_c is None
    assert verdict.startswith("NOT EVALUABLE")


# ── 13. Quality gate cannot execute without valid evidence ──────────────────
def test_classify_gates_quality_pass():
    r = mc.MutationResult(
        run_id="r", repository_sha="s", tree_sha="t",
        python_version="3.12", pytest_version="9.1.1", mutmut_version="3.7.0",
        config_hash="h", killed=90, survived=10, timeout=0,
        execution_status="PASS", classification_status="PASS",
        evidence_complete=True, mutation_score=90.0, threshold_percent=80,
    )
    ga, gb, gc, verdict = mc.classify_gates(r)
    assert (ga, gb, gc) == (True, True, True)


def test_classify_gates_quality_fail():
    r = mc.MutationResult(
        run_id="r", repository_sha="s", tree_sha="t",
        python_version="3.12", pytest_version="9.1.1", mutmut_version="3.7.0",
        config_hash="h", killed=50, survived=50, timeout=0,
        execution_status="PASS", classification_status="PASS",
        evidence_complete=True, mutation_score=50.0, threshold_percent=80,
    )
    ga, gb, gc, verdict = mc.classify_gates(r)
    assert (ga, gb) == (True, True)
    assert gc is False
    assert verdict == "QUALITY FAIL"


def test_classify_gates_evidence_incomplete():
    r = mc.MutationResult(
        run_id="r", repository_sha="s", tree_sha="t",
        python_version="3.12", pytest_version="9.1.1", mutmut_version="3.7.0",
        config_hash="h", killed=1, survived=0, timeout=0,
        execution_status="PASS", classification_status="FAIL",
        evidence_complete=False, mutation_score=100.0, threshold_percent=80,
    )
    ga, gb, gc, verdict = mc.classify_gates(r)
    assert gb is False
    assert gc is None
    assert "evidence" in verdict.lower()


# ── 14. End-to-end smoke: infra distinguishes killed/survived/no-test ──────
def test_smoke_end_to_end_distinguishes_classifications():
    """Run the clean-room smoke fixture and assert the pipeline produces all
    three classifications — proving the mutation infrastructure is healthy."""
    result = execute_mutation(mode="smoke")
    assert result.execution_status == "PASS", result.error
    assert result.evidence_complete is True
    # The fixture is designed to yield each bucket.
    assert result.killed > 0, "smoke must produce at least one killed mutant"
    assert result.survived > 0, "smoke must detect at least one surviving mutant"
    assert result.no_tests > 0, "smoke must detect at least one no-test mutant"
    assert result.mutants_generated == (
        result.killed + result.survived + result.no_tests
        + result.timeout + result.suspicious + result.not_checked
    )
