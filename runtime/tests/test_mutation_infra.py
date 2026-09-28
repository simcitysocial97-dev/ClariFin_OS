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

import pytest

from runtime.foundation.verification import mutation_contract as mc
from runtime.foundation.verification.env import (
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
    c = mc.MutationCounts(
        killed=4, survived=3, no_tests=2, timeout=1, suspicious=0, not_checked=1
    )
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
        run_id="r",
        repository_sha="s",
        tree_sha="t",
        python_version="3.12",
        pytest_version="9.1.1",
        mutmut_version="3.7.0",
        config_hash="h",
        killed=90,
        survived=10,
        timeout=0,
        execution_status="PASS",
        classification_status="PASS",
        evidence_complete=True,
        mutation_score=90.0,
        threshold_percent=80,
    )
    ga, gb, gc, verdict = mc.classify_gates(r)
    assert (ga, gb, gc) == (True, True, True)


def test_classify_gates_quality_fail():
    r = mc.MutationResult(
        run_id="r",
        repository_sha="s",
        tree_sha="t",
        python_version="3.12",
        pytest_version="9.1.1",
        mutmut_version="3.7.0",
        config_hash="h",
        killed=50,
        survived=50,
        timeout=0,
        execution_status="PASS",
        classification_status="PASS",
        evidence_complete=True,
        mutation_score=50.0,
        threshold_percent=80,
    )
    ga, gb, gc, verdict = mc.classify_gates(r)
    assert (ga, gb) == (True, True)
    assert gc is False
    assert verdict == "QUALITY FAIL"


def test_classify_gates_evidence_incomplete():
    r = mc.MutationResult(
        run_id="r",
        repository_sha="s",
        tree_sha="t",
        python_version="3.12",
        pytest_version="9.1.1",
        mutmut_version="3.7.0",
        config_hash="h",
        killed=1,
        survived=0,
        timeout=0,
        execution_status="PASS",
        classification_status="FAIL",
        evidence_complete=False,
        mutation_score=100.0,
        threshold_percent=80,
    )
    ga, gb, gc, verdict = mc.classify_gates(r)
    assert gb is False
    assert gc is None
    assert "evidence" in verdict.lower()


# ── 14. End-to-end smoke: infra distinguishes killed/survived/no-test ──────
def test_smoke_end_to_end_distinguishes_classifications():
    """Run the clean-room smoke fixture and assert the pipeline produces all
    three classifications — proving the mutation infrastructure is healthy."""
    result = execute_mutation(mode="smoke", allow_dirty=True)
    assert result.execution_status == "PASS", result.error
    assert result.evidence_complete is True
    # The fixture is designed to yield each bucket.
    assert result.killed > 0, "smoke must produce at least one killed mutant"
    assert result.survived > 0, "smoke must detect at least one surviving mutant"
    assert result.no_tests > 0, "smoke must detect at least one no-test mutant"
    assert result.mutants_generated == (
        result.killed
        + result.survived
        + result.no_tests
        + result.timeout
        + result.suspicious
        + result.not_checked
    )


# ── 15. R2: evidence is collected with the TARGET config still active ──────
@pytest.mark.timeout(300)
def test_r2_evidence_collected_with_target_config_active(monkeypatch, tmp_path):
    """M9-C42.20 Phase 8 (defect R2) — permanent architectural fix.

    The runner must collect `mutmut results` evidence while the correct *target*
    [tool.mutmut] configuration is still active, never after it has been restored
    to the original (different-scope) config. The fix is structural: evidence is
    collected inside the `try` body, *before* the `finally` block that restores
    the original config — so the ordering is guaranteed by Python's try/finally
    semantics, not a runtime flag.

    The test intercepts the single stable seam `FULL_CONFIG.write_text` to capture
    the [tool.mutmut] scope that is *active* at the moment `mutmut results` reads
    evidence. It asserts (a) evidence was collected with the target scope, and
    (b) the config was restored to the original afterward.
    """
    import re

    from runtime.foundation.verification import mutation_runner as mr

    backend_pyproject = mr.FULL_CONFIG
    original_text = backend_pyproject.read_text()

    def extract_source_paths(text: str) -> list[str] | None:
        m = re.search(r"source_paths\s*=\s*\[(.*?)\]", text, re.S)
        if not m:
            return None
        return re.findall(r'"([^"]+)"', m.group(1))

    # M9-C43.1: the test must be hermetic — the repository's resting
    # [tool.mutmut] scope is not a constant (it legitimately follows the last
    # targeted run). To keep R2 fully discriminating we seed a resting scope
    # DISTINCT from the target scope, then assert the exact round trip:
    # evidence under the TARGET scope, restoration to the seeded resting scope.
    target_scope = ["src/engines/credit_card_engine"]
    seeded_resting_scope = ["src/engines/balance_engine.py"]
    # Hermetic seed: whichever scope currently rests in backend/pyproject.toml,
    # ensure it is a scope DISTINCT from the target before the run. This holds
    # regardless of which targeted run previously left its resting scope (e.g.
    # behaviour_engine), so the R2 round-trip is always discriminating.
    if extract_source_paths(original_text) != seeded_resting_scope:
        backend_pyproject.write_text(
            re.sub(
                r"(source_paths\s*=\s*\[).*?(\])",
                lambda m: m.group(1) + '"src/engines/balance_engine.py"' + m.group(2),
                original_text,
                count=1,
                flags=re.S,
            )
        )
    resting_scope = extract_source_paths(backend_pyproject.read_text())
    assert resting_scope == seeded_resting_scope

    # Before the run we record the active scope whenever evidence is read. The
    # runner calls `subprocess.run([..., "mutmut", "results", ...])`; we capture
    # the config scope at that exact instant by snapshotting the live file.
    active_scope_at_results: dict[str, list[str] | None] = {"scope": None}
    real_run = mr.subprocess.run

    def patched_run(args, **kwargs):
        if (
            args
            and str(args[0]).endswith("mutmut")
            and len(args) > 1
            and args[1] == "results"
        ):
            active_scope_at_results["scope"] = extract_source_paths(
                backend_pyproject.read_text()
            )
        return real_run(args, **kwargs)

    monkeypatch.setattr(mr.subprocess, "run", patched_run)

    try:
        result = execute_mutation(
            mode="target", target="credit_card_engine", allow_dirty=True
        )
        # M9-C43.1: snapshot the config IMMEDIATELY after the runner returns —
        # i.e. after the runner's own try/finally restoration but BEFORE this
        # test's finally writes back the pristine text. Asserting on this
        # snapshot verifies the RUNNER's restore behavior directly (the old
        # assertion accidentally verified this test's own finally).
        post_run_text = backend_pyproject.read_text()
    finally:
        # Always restore the canonical backend config regardless of outcome.
        backend_pyproject.write_text(original_text)

    assert result.execution_status == "PASS", result.error
    # Evidence must have been collected while the TARGET (credit_card_engine)
    # config was active — NOT the seeded resting config.
    assert active_scope_at_results["scope"] == target_scope, (
        "evidence collected with wrong config scope: "
        f"{active_scope_at_results['scope']}"
    )
    # And the runner must have restored the seeded resting scope afterward.
    assert extract_source_paths(post_run_text) == resting_scope
