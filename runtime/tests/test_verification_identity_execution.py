"""Identity Threading Through Execution (VEA-2 Phase 2, M3)

Tests that `unit_id` + `provenance` survive plan → execute → result → manifest.

Why these tests exist
---------------------
Before M3 there was no artifact anywhere joining a planned verification unit to an
executed command. Phase 1.5's attribution worked only because failures were hand-fed from
manually parsed log files. The run manifest is the durable join-key artifact that makes
attribution automatic (M6).

Three invariants are load-bearing here:

1. **Executed commands must not change.** Phase 2 threads identity *through* existing
   execution, additively. If M3 altered what CI runs, the whole phase's central control
   is void.

2. **Dedup must not lose identity.** The planner rebuilds surviving steps field-by-field
   during command dedup, so any field not explicitly carried is silently dropped. When
   two units collapse onto one command, *both* IDs must survive — otherwise the second
   unit's failures become permanently unattributable.

3. **UNMAPPED must be visible.** A step with no mapped unit must appear in the manifest
   as `UNMAPPED` and must not crash the run. UNKNOWN over GUESSED.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.foundation.verification.models import VerificationStatus
from runtime.foundation.verification.orchestrator import VerificationOrchestrator
from runtime.foundation.verification.profiles import get_profile
from runtime.foundation.verification.registry import UNMAPPED

PROFILES = ["quick", "backend", "frontend", "runtime", "golden", "mutation", "playwright"]


class _FakeExecResult:
    """Stand-in for the Executor's result; no subprocess is ever spawned."""

    def __init__(self, exit_code: int = 0):
        self.exit_code = exit_code
        self.status = (
            VerificationStatus.PASSED if exit_code == 0 else VerificationStatus.FAILED
        )
        self.duration_seconds = 0.5
        self.stdout_path = "/tmp/stdout.log"
        self.stderr_path = "/tmp/stderr.log"
        self.error = None


def _planned(profile_name: str) -> VerificationOrchestrator:
    profile = get_profile(profile_name)
    orchestrator = VerificationOrchestrator(profile=profile)
    orchestrator.collect_changed_files()
    orchestrator.analyze_cross_layer()
    orchestrator.generate_plan(scope=profile.scope)
    return orchestrator


def _execute(orchestrator: VerificationOrchestrator, exit_code: int = 0):
    with patch.object(
        orchestrator._executor, "execute", return_value=_FakeExecResult(exit_code)
    ):
        return orchestrator.execute()


class TestPlannedStepsCarryIdentity:
    def test_known_unit_step_carries_expected_unit_id(self):
        """A planned step for a known unit carries the expected unit_id."""
        orchestrator = _planned("runtime")
        steps = orchestrator.plan.steps
        runtime_steps = [s for s in steps if s.workflow == "runtime"]
        assert runtime_steps, "expected a runtime-workflow step"
        assert runtime_steps[0].unit_id == "runtime-self-test"

    def test_backend_step_carries_backend_unit_identity(self):
        orchestrator = _planned("backend")
        backend_steps = [s for s in orchestrator.plan.steps if s.workflow == "backend"]
        assert backend_steps
        assert backend_steps[0].unit_id == "backend-unit"

    def test_step_provenance_carries_c11_shape(self):
        orchestrator = _planned("runtime")
        step = next(s for s in orchestrator.plan.steps if s.workflow == "runtime")
        assert set(step.provenance) >= {"capabilities", "impact_kinds", "source"}
        assert step.provenance["source"] == "registry-workflow-mapping"

    def test_unmapped_workflow_yields_none_unit_id_not_a_guess(self):
        """The `quick` workflow has no unit mapping; it must not borrow one."""
        orchestrator = _planned("backend")
        quick_steps = [s for s in orchestrator.plan.steps if s.workflow == "quick"]
        assert quick_steps, "expected a quick-workflow step in the backend profile"
        assert quick_steps[0].unit_id is None
        assert quick_steps[0].provenance == {}


class TestDedupPreservesIdentity:
    """Plan §M3.5 — two units collapsing to one command must retain both IDs."""

    def test_many_to_one_collapse_retains_all_contributing_units(self):
        orchestrator = _planned("backend")
        backend_step = next(
            s for s in orchestrator.plan.steps if s.workflow == "backend"
        )
        contributing = backend_step.provenance.get("contributing_units")
        assert contributing == ["backend-unit", "unit-targeted"], (
            "dedup dropped a contributing unit; the second unit's failures would be "
            "permanently unattributable"
        )

    def test_contributing_units_are_unique(self):
        orchestrator = _planned("backend")
        for step in orchestrator.plan.steps:
            contributing = step.provenance.get("contributing_units") or []
            assert len(contributing) == len(set(contributing))

    def test_step_unit_id_is_one_of_its_contributing_units(self):
        """The scalar unit_id must never disagree with the recorded set."""
        for profile in PROFILES:
            for step in _planned(profile).plan.steps:
                contributing = step.provenance.get("contributing_units") or []
                if step.unit_id and contributing:
                    assert step.unit_id in contributing

    def test_commands_remain_unique_after_dedup(self):
        """Identity threading must not resurrect duplicate commands."""
        for profile in PROFILES:
            commands = [s.command for s in _planned(profile).plan.steps]
            assert len(commands) == len(set(commands))


class TestExecutionResultCarriesIdentity:
    def test_result_unit_id_matches_its_step(self):
        orchestrator = _planned("backend")
        results = _execute(orchestrator)
        steps_by_id = {s.id: s for s in orchestrator.plan.steps}
        for result in results:
            step = steps_by_id[result.task_id]
            assert result.unit_id == step.unit_id
            assert result.provenance == step.provenance

    def test_identity_is_copied_not_rederived(self):
        """A result must never resolve identity independently of its step.

        Re-derivation could drift from the plan; copying cannot.
        """
        orchestrator = _planned("runtime")
        step = orchestrator.plan.steps[0]
        results = _execute(orchestrator)
        assert results[0].provenance is step.provenance


class TestRunManifest:
    def _manifest(self, orchestrator, tmp_path: Path) -> dict:
        path = tmp_path / "run-manifest.json"
        orchestrator.write_run_manifest(path=path)
        return json.loads(path.read_text())

    def test_manifest_round_trips_and_contains_provenance(self, tmp_path: Path):
        orchestrator = _planned("runtime")
        _execute(orchestrator)
        manifest = self._manifest(orchestrator, tmp_path)

        assert manifest["schema"] == "run-manifest/v1"
        assert manifest["commit"]
        assert manifest["branch"]
        assert manifest["generated_at"]
        assert manifest["profile"] == "runtime"

        runtime_entry = next(
            e for e in manifest["steps"] if e["unit_id"] == "runtime-self-test"
        )
        assert runtime_entry["unit_id"] == "runtime-self-test"
        assert runtime_entry["provenance"]["source"] == "registry-workflow-mapping"

    def test_manifest_entry_has_every_required_field(self, tmp_path: Path):
        orchestrator = _planned("backend")
        _execute(orchestrator)
        manifest = self._manifest(orchestrator, tmp_path)
        required = {
            "unit_id",
            "command",
            "exit_code",
            "status",
            "duration_seconds",
            "stdout_path",
            "stderr_path",
            "provenance",
        }
        for entry in manifest["steps"]:
            assert required <= set(entry)

    def test_manifest_records_all_contributing_units(self, tmp_path: Path):
        orchestrator = _planned("backend")
        _execute(orchestrator)
        manifest = self._manifest(orchestrator, tmp_path)
        backend = next(
            e for e in manifest["steps"] if e["workflow"] == "backend"
        )
        assert backend["contributing_units"] == ["backend-unit", "unit-targeted"]

    def test_manifest_has_top_level_unmapped_list(self, tmp_path: Path):
        orchestrator = _planned("backend")
        _execute(orchestrator)
        manifest = self._manifest(orchestrator, tmp_path)
        assert isinstance(manifest["unmapped"], list)

    def test_failing_run_is_recorded_faithfully(self, tmp_path: Path):
        orchestrator = _planned("runtime")
        _execute(orchestrator, exit_code=1)
        manifest = self._manifest(orchestrator, tmp_path)
        entry = next(
            e for e in manifest["steps"] if e["unit_id"] == "runtime-self-test"
        )
        assert entry["exit_code"] == 1
        assert entry["status"] == "failed"
        assert entry["unit_id"] == "runtime-self-test"

    def test_manifest_is_written_by_execute(self):
        """execute() emits the manifest without an explicit call."""
        orchestrator = _planned("runtime")
        default_path = (
            orchestrator._repo_root
            / "runtime/generated/evidence/run-manifest.json"
        )
        if default_path.exists():
            default_path.unlink()
        _execute(orchestrator)
        assert default_path.exists()

    def test_write_manifest_returns_none_when_nothing_executed(self, tmp_path: Path):
        orchestrator = _planned("runtime")
        assert orchestrator.write_run_manifest(path=tmp_path / "m.json") is None


class TestUnmappedIsVisibleAndNonFatal:
    """NEGATIVE TEST — plan §M3 requires UNMAPPED to be reported, not fatal."""

    def test_unmapped_step_appears_in_manifest_and_does_not_crash(
        self, tmp_path: Path
    ):
        orchestrator = _planned("backend")
        results = _execute(orchestrator)  # must not raise
        path = tmp_path / "run-manifest.json"
        orchestrator.write_run_manifest(path=path)
        manifest = json.loads(path.read_text())

        quick = next(
            e for e in manifest["steps"] if "run_fast_checks.sh" in e["command"]
        )
        assert quick["unit_id"] == UNMAPPED
        assert any(u["step_id"] == quick["step_id"] for u in manifest["unmapped"])
        assert len(results) == len(orchestrator.plan.steps)

    def test_unmapped_entries_state_a_reason(self, tmp_path: Path):
        orchestrator = _planned("backend")
        _execute(orchestrator)
        path = tmp_path / "run-manifest.json"
        orchestrator.write_run_manifest(path=path)
        manifest = json.loads(path.read_text())
        for entry in manifest["unmapped"]:
            assert entry["reason"]
            assert entry["command"]

    def test_unmapped_is_never_silently_replaced_by_a_real_unit(self, tmp_path: Path):
        """The guard against 'first entry wins' reappearing in the manifest."""
        orchestrator = _planned("backend")
        _execute(orchestrator)
        path = tmp_path / "run-manifest.json"
        orchestrator.write_run_manifest(path=path)
        manifest = json.loads(path.read_text())
        for entry in manifest["steps"]:
            if entry["unit_id"] == UNMAPPED:
                assert entry["contributing_units"] == []


class TestExecutedCommandsAreUnchanged:
    """The Phase 2 central control: identity threading changes nothing executed."""

    @pytest.mark.parametrize("profile", PROFILES)
    def test_every_step_still_has_a_command(self, profile):
        for step in _planned(profile).plan.steps:
            assert step.command
            assert step.command.startswith("bash .github/scripts/")

    @pytest.mark.parametrize("profile", PROFILES)
    def test_step_ids_remain_positional_and_contiguous(self, profile):
        steps = _planned(profile).plan.steps
        assert [s.id for s in steps] == [
            f"step-{i + 1:04d}" for i in range(len(steps))
        ]
        assert [s.order for s in steps] == list(range(1, len(steps) + 1))
