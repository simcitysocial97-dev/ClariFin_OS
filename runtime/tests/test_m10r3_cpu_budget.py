"""M10-R3 / Checkpoint D — the CPU budget, the missing execution condition.

Checkpoint A reproduced the reconcile failure and established its mechanism. The shard
planner assigns by estimated duration and the matrix rendered that as a **sum**, which
describes a serial machine. The executor does not run serially — it runs up to
DEFAULT_MAX_WORKERS tasks concurrently — and two of this repository's shell scripts
fork their own pools:

    .github/scripts/run_contract_tests.sh:78   -n auto
    .github/scripts/run_fast_checks.sh:89      -n auto

So shard 6 of the reproduced plan ran exec-0002 (4 CPU), exec-0003 (4 CPU) and
exec-0004 concurrently: nine CPU-bound processes against four cores, and against two on
a standard GitHub runner. Measured consequence: exec-0002 burned 180.3 s of a 360 s
budget and exec-0003 burned 352.2 s of a task declared ``estimated_duration=60``, and
correct obligations were reclassified TIMED_OUT.

Nothing modelled CPU as a consumable resource. Concurrency was a *worker count*, which
only equals CPU when every task is single-threaded — an assumption this repository
violates in its own shell scripts.

These tests pin the fix and, just as importantly, the ways it is easy to get wrong. Four
of the bugs found while implementing it are reproduced here as regressions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification import parallel_executor as px
from runtime.foundation.verification.execution_orchestrator import ExecutionPlan
from runtime.foundation.verification.execution_shards import (
    shard_cpu_peak,
    shard_wall_seconds,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class _Task:
    """Minimal stand-in carrying what the scheduler reads."""

    def __init__(self, task_id, command, estimated=0, cpu_demand=None):
        self.task_id = task_id
        self.command = command
        self.estimated_duration_seconds = estimated
        self.cpu_demand = cpu_demand


# ---------------------------------------------------------------------------
# Deriving CPU demand
# ---------------------------------------------------------------------------


class TestCpuDemandDerivation:
    def test_serial_command_is_one_cpu(self):
        assert px.cpu_demand_for(_Task("a", "echo hello")) == 1

    def test_flag_in_the_command_is_found(self):
        assert px.cpu_demand_for(_Task("a", "pytest -n 3 tests/")) == 3
        assert px.cpu_demand_for(_Task("b", "pytest -nauto tests/")) == px.cpu_count()
        assert px.cpu_demand_for(_Task("c", "pytest --numprocesses=2")) == 2

    def test_auto_resolves_to_the_core_count(self):
        assert px.cpu_demand_for(_Task("a", "pytest -n auto")) == px.cpu_count()

    def test_explicit_declaration_beats_derivation(self):
        assert px.cpu_demand_for(_Task("a", "pytest -n auto", cpu_demand=1)) == 1
        assert px.cpu_demand_for(_Task("b", "echo", cpu_demand=8)) == 8

    def test_the_real_scripts_are_derived_correctly(self):
        """The two heaviest tasks in this repository both fan out.

        If these returned 1 the budget would be inert in exactly the place it was
        introduced to fix something real.
        """
        assert (
            px.cpu_demand_for(
                _Task("c", "bash .github/scripts/run_contract_tests.sh")
            )
            == px.cpu_count()
        )
        assert (
            px.cpu_demand_for(_Task("f", "bash .github/scripts/run_fast_checks.sh"))
            == px.cpu_count()
        )

    def test_a_script_without_xdist_is_genuinely_single_threaded(self):
        assert (
            px.cpu_demand_for(_Task("p", "bash .github/scripts/run_property_tests.sh"))
            == 1
        )


class TestDerivationRegressions:
    """Four bugs found while implementing this, each of which silently disabled it."""

    def test_a_shell_string_test_is_not_a_worker_flag(self):
        """`[ -n "$X" ]` is a string test, not xdist.

        Without the exclusion the scan matches every `if [ -n ... ]` in a script and
        reports the *variable name* as a worker count. `run_contract_tests.sh` contains
        both forms — `[ -n "$CHANGED_FILES" ]` at line 31 and a real `-n auto` at line
        78 — so the exclusion is what makes the real flag findable at all.
        """
        text = 'if [ -n "$CHANGED_FILES" ]; then\n  pytest -n auto\nfi\n'
        assert px._first_worker_flag(text) == px.cpu_count()

    def test_a_non_numeric_token_does_not_raise(self):
        """`int()` on `"$CHANGED_FILES"` raised ValueError out of the scheduler."""
        text = 'if [ -n "$X" ]; then echo; fi\n'
        assert px._first_worker_flag(text) is None
        assert px.cpu_demand_in_script(text) is None

    def test_trailing_shell_punctuation_is_stripped(self):
        """`-n auto; then` must read as `auto`.

        The `;` was glued onto the token, so a genuinely fanning-out task was reported
        as single-threaded — the exact oversubscription this mechanism prevents.
        """
        assert px._first_worker_flag("pytest \\\n  -n auto; then\n") == px.cpu_count()

    def test_a_leading_dot_directory_survives_path_resolution(self):
        """`lstrip("./")` strips a character *set*, mangling `.github/…` to `github/…`.

        The path then does not exist, every task's demand falls back to 1, and the whole
        scheduler is inert while appearing to work. Found by checking the resolved value
        instead of trusting that the code looked right.
        """
        assert px._repo_relative(".github/scripts/x.sh") == ".github/scripts/x.sh"
        assert px._repo_relative("./.github/scripts/x.sh") == ".github/scripts/x.sh"
        assert px._repo_relative("/abs/path.sh") == "abs/path.sh"


class TestUnresolvedIsReported:
    def test_a_variable_worker_count_is_reported_not_guessed(self):
        tasks = [_Task("a", "bash .github/scripts/run_contract_tests.sh")]
        # Real script resolves, so nothing is reported.
        assert px.unresolved_cpu_demand_tasks(tasks) == []

    def test_a_script_with_no_flag_is_not_reported(self):
        """`run_property_tests.sh` has no xdist — it is honestly single-threaded.

        Reporting it would bury real findings in noise. Only a flag that is *present and
        unreadable* is a scheduling hazard.
        """
        tasks = [_Task("p", "bash .github/scripts/run_property_tests.sh")]
        assert px.unresolved_cpu_demand_tasks(tasks) == []

    def test_an_unreadable_flag_is_reported(self, tmp_path, monkeypatch):
        script = tmp_path / "fanout.sh"
        script.write_text('pytest -n "$NPROC"\n', encoding="utf-8")
        monkeypatch.setattr(px, "REPO_ROOT", tmp_path)
        tasks = [_Task("a", "bash fanout.sh")]
        problems = px.unresolved_cpu_demand_tasks(tasks)
        assert len(problems) == 1
        assert "cpu_demand" in problems[0]


# ---------------------------------------------------------------------------
# The budget itself
# ---------------------------------------------------------------------------


class TestCpuBudget:
    def test_admits_until_full_then_refuses(self):
        b = px.CpuBudget(4)
        assert b.try_acquire(2) is True
        assert b.try_acquire(2) is True
        assert b.try_acquire(1) is False, "admitted past the budget"
        assert b.in_flight == 4

    def test_release_frees_capacity(self):
        b = px.CpuBudget(4)
        b.try_acquire(4)
        b.release(4)
        assert b.try_acquire(4) is True

    def test_a_single_oversized_task_is_refused_rather_than_split(self):
        b = px.CpuBudget(2)
        assert b.try_acquire(4) is False

    def test_peak_is_recorded_as_evidence(self):
        b = px.CpuBudget(4)
        b.try_acquire(3)
        b.release(3)
        b.try_acquire(2)
        assert b.peak == 3

    def test_capacity_is_never_below_one(self):
        assert px.CpuBudget(0).capacity == 1
        assert px.CpuBudget(-5).capacity == 1


class TestScheduling:
    def test_heavy_tasks_run_alone(self):
        """The defect, stated as a property: two 4-CPU tasks must not overlap on 4 cores."""
        tasks = [
            _Task("heavy-a", "pytest -n auto", estimated=180),
            _Task("heavy-b", "pytest -n auto", estimated=60),
            _Task("light", "echo", estimated=300),
        ]
        waves = px.schedule_within_budget(tasks, px.CpuBudget(4))
        for wave in waves:
            demand = sum(px.cpu_demand_for(t) for t in wave)
            assert demand <= 4, f"wave {demand} CPU exceeds the budget"
        heavy_waves = [
            i for i, w in enumerate(waves)
            if any(px.cpu_demand_for(t) > 1 for t in w)
        ]
        assert len(heavy_waves) == 2, "the two fanning-out tasks were not serialised"

    def test_every_task_appears_exactly_once(self):
        tasks = [_Task(str(i), "echo") for i in range(10)]
        waves = px.schedule_within_budget(tasks, px.CpuBudget(3))
        flat = [t for wave in waves for t in wave]
        assert len(flat) == 10
        assert {t.task_id for t in flat} == {str(i) for i in range(10)}

    def test_largest_first(self):
        tasks = [
            _Task("small", "echo", estimated=1),
            _Task("big", "echo", estimated=1000),
        ]
        waves = px.schedule_within_budget(tasks, px.CpuBudget(2))
        assert waves[0][0].task_id == "big"

    def test_an_oversized_task_still_runs_alone(self):
        """Refusing it would deadlock the fan-out."""
        tasks = [_Task("huge", "pytest -n auto"), _Task("other", "echo")]
        waves = px.schedule_within_budget(tasks, px.CpuBudget(2))
        assert [t.task_id for w in waves for t in w] == ["huge", "other"]


class TestWallClockEstimate:
    def test_it_is_the_critical_path_not_the_sum(self):
        """A worker count is a CPU bound only for single-threaded work.

        Four independent one-second tasks have a serial sum of 4 and a critical path of
        1. The old matrix figure reported the sum, which describes a machine that never
        runs.
        """
        tasks = [_Task(str(i), "echo", estimated=60) for i in range(4)]
        budget = px.CpuBudget(4)
        assert px.estimate_wall_seconds(tasks, budget) == 60
        assert sum(t.estimated_duration_seconds for t in tasks) == 240

    def test_a_serialised_heavy_task_lengthens_the_estimate(self):
        """Bounded CPU costs wall clock, and the estimate must show it.

        This is the honest trade-off of the fix: total CPU-seconds are conserved, so
        preventing starvation means the run occupies more wall-clock time. An estimate
        that did not move would be the old bug wearing a new hat.
        """
        tasks = [
            _Task("a", "pytest -n auto", estimated=180),
            _Task("b", "echo", estimated=300),
        ]
        budget = px.CpuBudget(4)
        assert px.estimate_wall_seconds(tasks, budget) == 480


# ---------------------------------------------------------------------------
# Against the real reproduced plan
# ---------------------------------------------------------------------------


class TestAgainstTheReproducedPlan:
    @pytest.fixture
    def shard6(self):
        plan_path = REPO_ROOT / "docs/audits/m10-r3-checkpoint-a-plan.json"
        plan = ExecutionPlan.from_dict(json.loads(plan_path.read_text()))
        wanted = {"exec-0002", "exec-0003", "exec-0004", "exec-0009"}
        return [t for t in plan.tasks if t.task_id in wanted]

    def test_the_two_fanning_out_tasks_are_detected(self, shard6):
        by_id = {t.task_id: t for t in shard6}
        assert px.cpu_demand_for(by_id["exec-0002"]) == px.cpu_count()
        assert px.cpu_demand_for(by_id["exec-0003"]) == px.cpu_count()
        assert px.cpu_demand_for(by_id["exec-0004"]) == 1

    def test_no_wave_exceeds_four_cpus(self, shard6):
        for wave in px.schedule_within_budget(shard6, px.CpuBudget(4)):
            assert sum(px.cpu_demand_for(t) for t in wave) <= 4

    def test_nothing_is_left_unresolved(self, shard6):
        assert px.unresolved_cpu_demand_tasks(shard6) == []

    def test_peak_demand_is_reported(self, shard6):
        assert shard_cpu_peak(shard6, 4) == 4

    def test_the_estimate_is_now_a_real_schedule(self, shard6):
        """Previously 541s as a serial sum; now the critical path of the real schedule."""
        assert shard_wall_seconds(shard6, 4) > 0
        serial = sum(max(t.estimated_duration_seconds, 1) for t in shard6)
        assert serial == 541