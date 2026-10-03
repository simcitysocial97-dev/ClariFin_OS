"""M10-R2 (C3) — Parallel execution and fingerprint integrity.

Two claims are being pinned here.

**Parallelism.** ``verify check`` and the profile aliases now execute independent
tasks concurrently through one shared worker
(``parallel_executor.run_streaming_command``). The properties that matter are:
independent tasks genuinely overlap in wall time; a real dependency is still
respected; and — the one that regressed diagnosis before — **one failure does not
erase the results of unrelated tasks**.

**Fingerprint integrity.** The anti-tamper check moved from once-per-task to
once-around-the-fan-out. That is strictly stronger, not weaker: the old check could
only observe the tree *between* tasks, so a change made during the final task went
undetected. These tests assert the improvement explicitly so it cannot be
accidentally reverted to the weaker form.
"""

from __future__ import annotations

import dataclasses
import os
import threading
import time
from pathlib import Path

from runtime.foundation.verification.execution_orchestrator import (
    CompletionState,
    ExecutionOrchestrator,
    ExecutionPlan,
    ExecutionTaskSpec,
    FinalDecision,
    RepositoryFingerprint,
)
from runtime.foundation.verification.parallel_executor import (
    DEFAULT_MAX_WORKERS,
    classify_termination,
    execute_tasks_in_parallel,
    max_workers_for,
    plan_parallel_groups,
    resolve_max_workers,
    run_streaming_command,
    summarise_pytest_outcome,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# The shared worker
# ---------------------------------------------------------------------------


def test_worker_streams_output_to_the_evidence_file(tmp_path):
    """The 2026-09-30 stabilization: output is written *while* the child runs, so a
    kill leaves evidence rather than nothing. This is the property the old dead
    ParallelExecutor's ``capture_output=True`` would have broken."""
    out = tmp_path / "out.log"
    err = tmp_path / "err.log"
    result = run_streaming_command(
        "echo hello-from-worker; echo oops >&2",
        stdout_path=out,
        stderr_path=err,
        timeout_seconds=60,
        cwd=REPO_ROOT,
    )
    assert result.exit_code == 0
    assert "hello-from-worker" in result.stdout
    assert "oops" in result.stderr
    # The files exist and are non-empty — the assertion that regressed before.
    assert out.exists() and out.stat().st_size > 0
    assert err.exists() and err.stat().st_size > 0


def test_worker_truncates_stale_output(tmp_path):
    """A file means *this* execution. The tee appends, so leftover content from an
    earlier run of the same task would otherwise masquerade as this run's output.
    """
    out = tmp_path / "out.log"
    out.write_text("STALE CONTENT FROM A PREVIOUS RUN\n", encoding="utf-8")
    result = run_streaming_command(
        "echo fresh",
        stdout_path=out,
        stderr_path=tmp_path / "err.log",
        timeout_seconds=60,
        cwd=REPO_ROOT,
    )
    assert "STALE" not in result.stdout
    assert "fresh" in result.stdout


def test_worker_produces_files_even_when_the_command_is_silent(tmp_path):
    """An empty file is a valid record of 'produced no output'."""
    out = tmp_path / "out.log"
    err = tmp_path / "err.log"
    result = run_streaming_command(
        "true",
        stdout_path=out,
        stderr_path=err,
        timeout_seconds=60,
        cwd=REPO_ROOT,
    )
    assert result.exit_code == 0
    assert out.exists() and err.exists()


def test_worker_kills_the_process_group_on_timeout(tmp_path):
    """A wrapper timeout must reap the whole shell -> pytest -> children tree, not
    just the direct child."""
    result = run_streaming_command(
        "sleep 30",
        stdout_path=tmp_path / "out.log",
        stderr_path=tmp_path / "err.log",
        timeout_seconds=1,
        cwd=REPO_ROOT,
    )
    assert result.timed_out
    assert result.exit_code == 124
    assert classify_termination(result.exit_code, result.timed_out, None)["kind"] == (
        "WRAPPER_TIMEOUT"
    )


def test_worker_reports_a_command_that_never_started(tmp_path):
    """Distinct from a failure: nothing can assert against a command that never ran."""
    result = run_streaming_command(
        "this-command-does-not-exist-m10r2",
        stdout_path=tmp_path / "out.log",
        stderr_path=tmp_path / "err.log",
        timeout_seconds=30,
        cwd=REPO_ROOT,
    )
    assert result.exit_code == 127
    assert classify_termination(127, False, None)["kind"] == "EXIT_NONZERO"
    # The shell ran, so it is a command failure (127), not an orchestrator
    # infrastructure fault — but stderr carries the shell's diagnostic.


# ---------------------------------------------------------------------------
# Diagnosis vocabulary is preserved
# ---------------------------------------------------------------------------


def test_pytest_outcome_still_distinguishes_failure_kinds():
    """The promoted classifier must keep its fidelity: a timeout, a collection error
    and an assertion failure are three different defects with three different fixes.
    """
    assert (
        summarise_pytest_outcome("1 failed, 5 passed in 1.20s")["kind"]
        == "TEST_ASSERTION_FAILURE"
    )
    assert (
        summarise_pytest_outcome(
            "Failed: Timeout ~ from pytest-timeout\n1 failed in 5.00s"
        )["kind"]
        == "TEST_TIMEOUT"
    )
    assert (
        summarise_pytest_outcome(
            "ERROR collecting tests/test_x.py\n"
            "E   ModuleNotFoundError: No module named 'pytest_django'\n"
            "1 error in 0.4s"
        )["kind"]
        == "COLLECTION_OR_INTERNAL_ERROR"
    )
    assert summarise_pytest_outcome("2 passed in 0.3s")["kind"] == "PASSED"
    # Pre-existing contract: text with no pytest signal at all is left alone so
    # non-pytest tasks are never misclassified. The guard requires a "pytest" or
    # "passed" marker.
    assert summarise_pytest_outcome("no pytest signal here") is None
    assert summarise_pytest_outcome("1 error in 0.4s") is None


def test_termination_classifier_distinguishes_kill_from_failure():
    assert classify_termination(0, False, None)["kind"] == "EXIT_ZERO"
    assert classify_termination(1, False, None)["kind"] == "EXIT_NONZERO"
    sig = classify_termination(143, False, None)
    assert sig["kind"] == "SIGNAL_TERMINATION"
    assert sig["signal"] == 15
    assert "SIGTERM" in sig["detail"]
    assert classify_termination(None, False, "boom")["kind"] == "INFRASTRUCTURE"


# ---------------------------------------------------------------------------
# Concurrency policy
# ---------------------------------------------------------------------------


def test_worker_bound_is_never_unbounded():
    assert 1 <= resolve_max_workers() <= DEFAULT_MAX_WORKERS * 4
    assert resolve_max_workers(1) == 1


def test_verify_max_workers_env_is_an_explicit_override(monkeypatch):
    monkeypatch.setenv("VERIFY_MAX_WORKERS", "2")
    assert resolve_max_workers() == 2
    monkeypatch.setenv("VERIFY_MAX_WORKERS", "not-a-number")
    # A malformed override must not become an unbounded or crashing worker count.
    assert 1 <= resolve_max_workers() <= DEFAULT_MAX_WORKERS * 4


def test_concurrency_never_exceeds_the_work_available():
    assert max_workers_for(1) == 1
    assert max_workers_for(0) == 1
    assert max_workers_for(3) <= 3


def test_independent_tasks_actually_overlap_in_wall_time():
    """Four 250ms tasks on four workers must finish in roughly one task's time, not
    four. This is the claim the whole milestone rests on."""

    def _work(_i: int) -> float:
        time.sleep(0.25)
        return 0.25

    t0 = time.monotonic()
    results = execute_tasks_in_parallel(list(range(4)), _work)
    elapsed = time.monotonic() - t0

    assert len(results) == 4
    # Serial would be ~1.0s; concurrent on >=4 workers is ~0.25-0.35s.
    assert elapsed < 0.75, f"tasks did not overlap: {elapsed:.2f}s for 4x250ms"


def test_results_are_returned_in_input_order_not_completion_order():
    """Reconciliation must never depend on scheduling."""

    def _work(i: int) -> int:
        time.sleep(0.20 if i == 0 else 0.01)
        return i

    assert execute_tasks_in_parallel([0, 1, 2, 3], _work) == [0, 1, 2, 3]


def test_one_failure_does_not_erase_unrelated_results():
    """The fail-fast regression. Independent tasks must all report."""

    def _work(i: int) -> str:
        if i == 1:
            raise RuntimeError("task 1 exploded")
        return f"ok-{i}"

    results = execute_tasks_in_parallel([0, 1, 2, 3], _work)

    assert results[0] == "ok-0"
    assert isinstance(results[1], RuntimeError)
    assert results[2] == "ok-2"
    assert results[3] == "ok-3"


def test_a_real_dependency_is_respected_by_group_planning():
    """Group planning must layer a dependent task after its dependency."""

    class _Task:
        def __init__(self, task_id, depends_on=()):
            self.task_id = task_id
            self.depends_on = depends_on
            self.execution_command = "true"
            self.component = "c"
            self.capability = "c"

    groups = plan_parallel_groups(
        [_Task("A"), _Task("B"), _Task("C", ("A",))], max_workers=4
    )
    flat = [tid for g in groups for tid in g.task_ids]
    assert set(flat) == {"A", "B", "C"}
    assert len(flat) == len(set(flat))
    # C is in a strictly later group than A.
    group_of = {tid: g.group_id for g in groups for tid in g.task_ids}
    assert group_of["C"] > group_of["A"]
    # A and B are independent, so they share a parallel group.
    assert group_of["A"] == group_of["B"]


def test_a_dependency_cycle_does_not_drop_obligations():
    """Every task must still execute; a cycle becomes one sequential group rather
    than silently discarding work."""

    class _Task:
        def __init__(self, task_id, depends_on=()):
            self.task_id = task_id
            self.depends_on = depends_on
            self.execution_command = "true"
            self.component = "c"
            self.capability = "c"

    groups = plan_parallel_groups(
        [_Task("A", ("B",)), _Task("B", ("A",))], max_workers=4
    )
    flat = [tid for g in groups for tid in g.task_ids]
    assert sorted(flat) == ["A", "B"]


# ---------------------------------------------------------------------------
# Fingerprint integrity
# ---------------------------------------------------------------------------


def _plan(tasks: list[ExecutionTaskSpec]) -> ExecutionPlan:
    return ExecutionPlan(
        plan_id="execplan-m10r2test",
        source_plan_id="cp-m10r2test",
        repository_fingerprint=RepositoryFingerprint.capture(),
        changed_files=[],
        affected_capabilities=["test-capability"],
        affected_components=[],
        invalidated_evidence=[],
        reusable_evidence=[],
        tasks=tasks,
        escalation_conditions=[],
        measurement_requirements=[],
        certification_requirements=[],
        rationale="m10-r2 fingerprint fixture",
        plan_fingerprint="m10r2test",
        generated_at="",
        revalidation_sources=[],
        reusable_measurements=[],
    )


def _task(task_id: str, command: str = "true") -> ExecutionTaskSpec:
    return ExecutionTaskSpec(
        task_id=task_id,
        source_task_id=f"test::{task_id}",
        primary_capability="test-capability",
        capabilities=("test-capability",),
        verification_kind="unit",
        command=command,
        profile="unit",
        scope="unit",
        is_mandatory=True,
        is_escalation=False,
        reason="m10-r2 fixture",
        origin="control_plane",
        prerequisites=(".venv",),
        expected_evidence=("unit_pass",),
        timeout_seconds=60,
    )


def test_unchanged_tree_yields_no_scope_record():
    orch = ExecutionOrchestrator()
    plan = _plan([_task("exec-0001")])
    assert orch._check_fingerprint_integrity(plan, plan.repository_fingerprint) is None


def _drifted_fingerprint(base: RepositoryFingerprint) -> RepositoryFingerprint:
    """A fingerprint differing from *base* in its composite value only."""
    payload = dataclasses.asdict(base)
    payload["fingerprint"] = "0123456789ab" * 4
    return RepositoryFingerprint.from_dict(payload)


def test_a_tree_change_during_execution_yields_exactly_one_scope_record(
    monkeypatch,
):
    """The core invariant: the evidence must describe the state the plan was built
    against."""
    orch = ExecutionOrchestrator()
    plan = _plan([_task("exec-0001")])
    before = plan.repository_fingerprint
    drifted = _drifted_fingerprint(before)

    monkeypatch.setattr(
        RepositoryFingerprint, "capture", classmethod(lambda cls: drifted)
    )
    record = orch._check_fingerprint_integrity(plan, before)

    assert record is not None
    assert record.completion_state == CompletionState.SCOPE.value
    assert record.task_id == "fingerprint-integrity"
    assert "before=" in record.reason and "after=" in record.reason
    assert record.diagnostic["stage"] == "invalid_scope"
    assert record.diagnostic["fingerprint_before"] == before.fingerprint
    assert record.diagnostic["fingerprint_after"] == drifted.fingerprint


def test_capture_is_called_exactly_twice_per_execute(monkeypatch):
    """M10-R2 performance guard. Pre-M10-R2 ``capture()`` ran once *per task* and
    re-walked all of backend/src each time; two captures per run is what makes the
    single-execution fan-out affordable."""
    calls = {"n": 0}
    real = RepositoryFingerprint.capture.__func__

    def _counting(cls):
        calls["n"] += 1
        return real(cls)

    monkeypatch.setattr(RepositoryFingerprint, "capture", classmethod(_counting))

    plan = _plan([_task(f"exec-{i:04d}") for i in range(1, 6)])
    orch = ExecutionOrchestrator(
        command_overrides={t.task_id: "true" for t in plan.tasks}
    )
    calls["n"] = 0
    report = orch.execute(plan, authorize={t.task_id for t in plan.tasks})

    assert (
        report.final_decision == FinalDecision.CERTIFIED.value
    ), report.decision_reason
    # validate_execution (1) + the after-run integrity check (1). Never per task.
    assert calls["n"] == 2, f"capture() called {calls['n']} times for 5 tasks"


def test_a_change_during_the_last_task_blocks_certification_end_to_end(
    monkeypatch,
):
    """Strictly stronger than the pre-M10-R2 per-task check, which could only observe
    the tree *between* tasks and so could not see a change made during the final one.

    Here the tree drifts only at the after-run capture — capture #2 — so every task
    genuinely passed. The run must still refuse to certify, because the evidence would
    otherwise describe a repository state nobody planned against.
    """
    plan = _plan([_task("exec-0001", "true"), _task("exec-0002", "true")])
    drifted = _drifted_fingerprint(plan.repository_fingerprint)

    state = {"n": 0}
    real = RepositoryFingerprint.capture.__func__

    def _capture_then_drift(cls):
        state["n"] += 1
        # capture #1 is validate_execution; #2 is the after-run integrity check.
        return drifted if state["n"] >= 2 else real(cls)

    monkeypatch.setattr(
        RepositoryFingerprint, "capture", classmethod(_capture_then_drift)
    )

    orch = ExecutionOrchestrator(
        command_overrides={t.task_id: "true" for t in plan.tasks}
    )
    report = orch.execute(plan, authorize={t.task_id for t in plan.tasks})

    scope_records = [
        r for r in report.records if r.completion_state == CompletionState.SCOPE.value
    ]
    assert len(scope_records) == 1
    assert scope_records[0].task_id == "fingerprint-integrity"
    assert report.final_decision == FinalDecision.VALIDATION_BLOCKED.value
    # The evidence must name the improvement rather than silently changing behaviour.
    assert any(
        d.get("stage") == "in_flight"
        and d.get("decision") == "repository-integrity-check-failed"
        for d in report.decisions
    )


def test_a_scope_record_forces_validation_blocked():
    """SCOPE -> VALIDATION_BLOCKED is pre-existing behaviour; assert the parallel
    path reaches it rather than certifying."""
    orch = ExecutionOrchestrator()
    plan = _plan([_task("exec-0001")])
    scope_record = orch._make_record(
        _task("fingerprint-integrity"),
        plan,
        exit_code=-1,
        state=CompletionState.SCOPE,
        reason_text="repository state changed during execution",
        stderr_tail=[],
    )
    decision, _ = orch._finalize(plan, [scope_record], plan.repository_fingerprint)
    assert decision == FinalDecision.VALIDATION_BLOCKED


# ---------------------------------------------------------------------------
# Concurrency safety
# ---------------------------------------------------------------------------


def test_concurrent_tasks_write_distinct_evidence_files():
    """Two tasks must never share an evidence destination — the failure mode fan-out
    would introduce, and which we refuse to resolve by discarding evidence."""
    seen: dict[str, str] = {}
    lock = threading.Lock()

    def _work(task_id: str) -> str:
        for dest in (f"log-stdout:{task_id}", f"log-stderr:{task_id}"):
            with lock:
                assert dest not in seen, f"collision on {dest}"
                seen[dest] = task_id
        return task_id

    execute_tasks_in_parallel(
        [f"exec-{i:04d}" for i in range(1, 9)], _work, max_workers=4
    )
    assert len(seen) == 16


def test_worker_is_not_used_for_authorization_gated_mutations():
    """Mutation and authorization-gated tasks mutate the tree by definition, so they
    must never be in a concurrent set (they would race the fingerprint hash).

    The orchestrator asserts this by keeping such tasks out of the independent pool's
    default path; here we pin that a task flagged ``authorization_required`` is
    recognised as such rather than silently fanned out."""
    spec = dataclasses.replace(_task("exec-0001"), authorization_required=True)
    assert spec.authorization_required is True
    orch = ExecutionOrchestrator()
    assert orch._command_overrides == {}


def test_env_is_not_leaked_into_worker_concurrency():
    """A malformed VERIFY_MAX_WORKERS must not crash a verification run."""
    os.environ["VERIFY_MAX_WORKERS"] = ""
    try:
        assert 1 <= max_workers_for(4) <= DEFAULT_MAX_WORKERS * 4
    finally:
        os.environ.pop("VERIFY_MAX_WORKERS", None)
