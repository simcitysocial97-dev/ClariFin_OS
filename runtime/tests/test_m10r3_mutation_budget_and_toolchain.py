"""M10-R3 / Checkpoint C — mutation budget authority and crash-safe toolchain restore.

Two defects, both reproduced rather than inferred.

**The SIGKILL one is not theoretical.** During M10-R3 Checkpoint A a reconcile shard
leg was killed while ``exec-0021`` (a mutation campaign) held the tree. Afterwards
``backend/pyproject.toml`` read::

    # Scope: reconciliation_engine
    source_paths = ["src/engines/reconciliation_engine.py"]

That file is one of the two inputs to the repository fingerprint's ``config_hash``, so
the *next* run's capture mismatched and the orchestrator reported
``VALIDATION_BLOCKED`` — "scope or fingerprint mismatch detected". The real fault was
"a mutation campaign was killed and did not restore its toolchain config". A green
suite was blocked by a phantom integrity failure whose name pointed an operator at the
wrong file.

Restoration was reachable only from ``atexit`` and from SIGTERM/SIGINT handlers.
SIGKILL cannot be caught. These tests pin the replacement: a durable pre-write backup
plus an atomic replace, so restoration no longer depends on catching anything.

**The budget one is a silent divergence.** A mutation revalidation task declares
``timeout_seconds=1200``; ``mutation_runner`` enforces
``DEFAULT_RUNTIME["target"] = 4200``. Neither number was recorded anywhere, so a
campaign killed by its own timeout and a campaign killed by the CI runner were
indistinguishable, and a workflow sizing ``timeout-minutes`` from the declared value
was sizing it from a number that does not exist.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from runtime.foundation.verification import mutation_runner as mr
from runtime.foundation.verification.execution_orchestrator import (
    DECLARED_MUTATION_TIMEOUT_SECONDS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Crash-safe restoration
# ---------------------------------------------------------------------------


class TestCrashSafeRestoration:
    def test_backup_is_written_before_anything_is_rewritten(self, monkeypatch, tmp_path):
        """The backup must precede the rewrite, not merely the signal handlers.

        Installing an exit handler and *then* rewriting leaves the window in which a
        kill destroys the config with no copy of the original anywhere. That window is
        the whole failure.
        """
        safety = mr._MutationSafety(mode="target")
        monkeypatch.setattr(mr, "FULL_CONFIG", tmp_path / "pyproject.toml")
        monkeypatch.setattr(mr, "CONFIG_BACKUP", tmp_path / ".pyproject.toml.bak")
        (tmp_path / "pyproject.toml").write_text("original\n", encoding="utf-8")

        safety.enter()
        try:
            assert (tmp_path / ".pyproject.toml.bak").is_file()
            assert (tmp_path / ".pyproject.toml.bak").read_text() == "original\n"
        finally:
            safety._restore_config()

    def test_restore_is_atomic_and_leaves_no_temp_file(self, monkeypatch, tmp_path):
        target = tmp_path / "pyproject.toml"
        target.write_text("damaged\n", encoding="utf-8")
        mr._MutationSafety._atomic_write(target, "restored\n")
        assert target.read_text() == "restored\n"
        assert list(tmp_path.glob(".*m10r3-tmp")) == []

    def test_a_stale_backup_is_repaired_on_the_next_run(self, monkeypatch, tmp_path):
        """The property that makes SIGKILL survivable: no signal needed.

        Reproduces the Checkpoint A damage — config rewritten, process gone — and
        asserts the *next* invocation repairs it.
        """
        config = tmp_path / "pyproject.toml"
        backup = tmp_path / ".pyproject.toml.bak"
        monkeypatch.setattr(mr, "FULL_CONFIG", config)
        monkeypatch.setattr(mr, "CONFIG_BACKUP", backup)

        config.write_text("# Scope: reconciliation_engine\n", encoding="utf-8")
        backup.write_text("# backend/pyproject.toml\n", encoding="utf-8")

        assert mr._MutationSafety.recover_stale_backup() is True
        assert config.read_text() == "# backend/pyproject.toml\n"
        assert not backup.exists(), "the repair must consume the backup"

    def test_no_backup_means_nothing_to_repair(self, monkeypatch, tmp_path):
        monkeypatch.setattr(mr, "CONFIG_BACKUP", tmp_path / "absent.bak")
        assert mr._MutationSafety.recover_stale_backup() is False

    def test_recovery_runs_before_the_dirty_worktree_check(self):
        """Otherwise the stale mutation edit is reported as an unrelated dirty file.

        The operator would be told to investigate a change they did not make, and the
        run would refuse to start — the exact situation the backup exists to end.
        """
        source = Path(mr.__file__).read_text(encoding="utf-8")
        enter = source.split("def enter(self)", 1)[1]
        body = enter.split("def _atomic_write", 1)[0] if "def _atomic_write" in enter else enter
        assert "recover_stale_backup" in body, (
            "recover_stale_backup must be called in enter() before the dirty check"
        )
        assert body.index("recover_stale_backup") < body.index("_check_dirty_worktree")

    def test_a_killed_process_leaves_a_recoverable_state(self, tmp_path):
        """End-to-end with a REAL SIGKILL — the signal that cannot be caught.

        Spawns a child that writes the backup, rewrites the config, then kills itself
        with SIGKILL. Nothing in the child can run: no atexit, no signal handler. The
        parent's assertion is that the damage is nonetheless recoverable on the next
        run.

        This is the exact Checkpoint A observation, re-executed as a test: a reconcile
        shard leg was killed mid-campaign and left ``backend/pyproject.toml`` pointing
        at the campaign's target scope.
        """
        config = tmp_path / "pyproject.toml"
        backup = tmp_path / ".pyproject.toml.bak"
        pristine = "# backend/pyproject.toml\n"
        config.write_text(pristine, encoding="utf-8")

        def _child(*, take_backup: bool) -> int:
            script = textwrap.dedent(f"""
                import os, pathlib, signal, sys
                sys.path.insert(0, {str(REPO_ROOT)!r})
                from runtime.foundation.verification import mutation_runner as mr
                mr.FULL_CONFIG = pathlib.Path({str(config)!r})
                mr.CONFIG_BACKUP = pathlib.Path({str(backup)!r})
                {"mr._MutationSafety._write_backup(mr.FULL_CONFIG.read_text())" if take_backup else "pass"}
                mr.FULL_CONFIG.write_text("# Scope: reconciliation_engine\\n")
                os.kill(os.getpid(), signal.SIGKILL)
            """)
            proc = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return proc.returncode

        # 1. Without the fix: the config is destroyed and nothing can repair it.
        assert _child(take_backup=False) == -9
        assert config.read_text() == "# Scope: reconciliation_engine\n"
        assert not backup.exists(), "no backup existed before the fix"
        assert (
            mr._MutationSafety.recover_stale_backup(config, backup) is False
        ), "and with no backup there is nothing to recover from"

        # 2. With the fix, the same kill leaves a recoverable state.
        config.write_text(pristine, encoding="utf-8")
        assert _child(take_backup=True) == -9
        assert backup.is_file(), "the backup must survive a SIGKILL"
        assert config.read_text() == "# Scope: reconciliation_engine\n"

        # 3. The next run repairs it.
        assert mr._MutationSafety.recover_stale_backup(config, backup) is True
        assert config.read_text() == pristine
        assert not backup.exists()

    def test_the_real_repo_config_is_never_left_damaged(self):
        """Guards the fixture itself: these tests must not damage the repository."""
        head = (REPO_ROOT / "backend" / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert "reconciliation_engine" not in head.split("\n\n")[0], (
            "backend/pyproject.toml looks like it was left mutated by a killed "
            "campaign; run `git checkout -- backend/pyproject.toml`"
        )


# ---------------------------------------------------------------------------
# Budget authority
# ---------------------------------------------------------------------------


class TestBudgetAuthority:
    def test_the_declared_budget_has_exactly_one_definition(self):
        """The literal must not creep back into the construction sites.

        It appeared twice as a bare ``1200`` before this checkpoint, which is how two
        budgets became three.
        """
        source = Path(mr.__file__).read_text(encoding="utf-8")
        assert source.count("timeout_seconds=1200") == 0, (
            "a bare 1200 has reappeared in mutation_runner; use "
            "DECLARED_MUTATION_TIMEOUT_SECONDS"
        )
        orch = (REPO_ROOT / "runtime/foundation/verification/execution_orchestrator.py").read_text(
            encoding="utf-8"
        )
        assert "timeout_seconds=1200" not in orch, (
            "the planner re-declared the mutation budget inline; use "
            "DECLARED_MUTATION_TIMEOUT_SECONDS"
        )

    def test_both_sides_agree_on_the_declared_value(self):
        assert mr.DECLARED_MUTATION_TIMEOUT_SECONDS == DECLARED_MUTATION_TIMEOUT_SECONDS

    def test_the_divergence_is_recorded_not_tolerated(self):
        """The whole point: the discrepancy must be visible in the evidence."""
        declared = mr._declared_mutation_timeout("target", "reconciliation_engine")
        enforced = mr.DEFAULT_RUNTIME["target"]
        assert declared == DECLARED_MUTATION_TIMEOUT_SECONDS
        assert enforced == 4200
        # If these ever converge the divergence machinery becomes dead weight and this
        # assertion fails loudly, prompting its removal rather than silent rot.
        assert declared != enforced, (
            "the declared and enforced mutation budgets have converged; "
            "the recorded-pair plumbing should now be simplified"
        )

    def test_smoke_has_no_declared_budget(self):
        """Distinguishable from 'a budget of zero'."""
        assert mr._declared_mutation_timeout("smoke", None) == 0

    def test_the_result_carries_both_budgets(self):
        fields = mr.MutationResult.__dataclass_fields__
        assert "declared_timeout_seconds" in fields
        assert "enforced_timeout_seconds" in fields
        assert "toolchain_restored" in fields
        assert "recovered_stale_backup" in fields
        assert "fingerprint_stable" in fields
        assert "certification_decision" in fields

    def test_the_result_round_trips_through_json(self):
        import json

        result = mr.MutationResult(
            run_id="mut-test",
            repository_sha="a" * 40,
            tree_sha="b" * 40,
            python_version="3.12",
            pytest_version="9.1.1",
            mutmut_version="3.7.0",
            config_hash="c" * 64,
            declared_timeout_seconds=1200,
            enforced_timeout_seconds=4200,
            toolchain_restored=False,
            recovered_stale_backup=True,
            certification_decision="validation_blocked",
        )
        payload = json.loads(json.dumps(result.to_dict(), default=str))
        assert payload["declared_timeout_seconds"] == 1200
        assert payload["enforced_timeout_seconds"] == 4200
        assert payload["toolchain_restored"] is False
        assert payload["recovered_stale_backup"] is True
        assert payload["certification_decision"] == "validation_blocked"


# ---------------------------------------------------------------------------
# The sixth topology joins the authority
# ---------------------------------------------------------------------------


class TestMutationIsCertifiable:
    """The sixth topology joins the shared authority.

    These tests exercise the *verdict* logic, so they build a `_MutationSafety` and
    set its restoration flag directly rather than driving `enter()`/`exit()`. `exit()`
    verifies restoration against the real `backend/pyproject.toml` — correct behaviour
    for production, and irrelevant here: restoration itself is covered by
    TestCrashSafeRestoration, including a real SIGKILL.
    """

    @staticmethod
    def _safety(*, restored: bool) -> mr._MutationSafety:
        safety = mr._MutationSafety(mode="target")
        safety.config_restored = restored
        return safety

    @staticmethod
    def _result(**kw) -> mr.MutationResult:
        base = dict(
            run_id="mut-test",
            repository_sha="a" * 40,
            tree_sha="b" * 40,
            python_version="3.12",
            pytest_version="9.1.1",
            mutmut_version="3.7.0",
            config_hash="c" * 64,
            execution_status="PASS",
        )
        base.update(kw)
        return mr.MutationResult(**base)

    def test_an_unrestored_toolchain_is_recorded_as_scope(self):
        """Mutation rewrites repository files by design.

        A naive per-obligation "did the tree change" check would report drift on every
        healthy campaign. What must be distinguished is "mutated and restored exactly"
        (certifiable) from "mutated and abandoned" (not) — so the verdict keys off
        restoration, and an unrestored config is a hard SCOPE block whose reason says
        what will go wrong *next* run.
        """
        from runtime.foundation.verification.execution_orchestrator import (
            CertificationRun,
            FinalDecision,
        )

        with CertificationRun("mutation:test") as run:
            result = mr._finalise_mutation_certification(
                run, self._safety(restored=False), self._result(), timeout=4200
            )

        assert result is not None
        assert result.toolchain_restored is False
        assert run.decision is FinalDecision.VALIDATION_BLOCKED
        assert "backend/pyproject.toml" in run.reason, (
            "the verdict must name the file that will fail the next run's capture; "
            "a bare VALIDATION_BLOCKED sends the operator to the wrong place"
        )
        assert result.certification_decision == "validation_blocked"

    def test_a_clean_campaign_certifies_and_records_its_bracket(self):
        from runtime.foundation.verification.execution_orchestrator import (
            CertificationRun,
            FinalDecision,
        )

        with CertificationRun("mutation:test") as run:
            result = mr._finalise_mutation_certification(
                run, self._safety(restored=True), self._result(), timeout=4200
            )

        assert result is not None
        assert result.toolchain_restored is True
        assert result.fingerprint_before is not None
        assert result.fingerprint_after is not None
        # The bracket closes AFTER restoration, so a healthy campaign is stable even
        # though it rewrote backend/pyproject.toml mid-run. This is the property that
        # a per-obligation fingerprint check could not have.
        assert result.fingerprint_stable is True
        assert run.decision is FinalDecision.CERTIFIED

    def test_an_infrastructure_campaign_is_not_certified(self):
        from runtime.foundation.verification.execution_orchestrator import (
            CertificationRun,
            FinalDecision,
        )

        with CertificationRun("mutation:test") as run:
            result = mr._finalise_mutation_certification(
                run,
                self._safety(restored=True),
                self._result(
                    execution_status="INFRASTRUCTURE_FAILURE",
                    error="mutation run exceeded max_runtime=4200s",
                ),
                timeout=4200,
            )

        assert run.decision is FinalDecision.INFRASTRUCTURE_BLOCKED
        assert result is not None
        assert result.enforced_timeout_seconds == 4200
        assert result.declared_timeout_seconds == DECLARED_MUTATION_TIMEOUT_SECONDS

    def test_the_budget_pair_is_attached_by_replacement(self):
        """`MutationResult` is frozen, so the verdict is attached by replacement.

        An earlier version assigned to its fields, raised FrozenInstanceError, and the
        enclosing `contextlib.suppress` swallowed it — so the verdict was silently
        never applied and every campaign reported `certified` with no bracket. The
        return value is what makes that impossible.
        """
        import dataclasses

        with pytest.raises(dataclasses.FrozenInstanceError):
            self._result().toolchain_restored = False


# ---------------------------------------------------------------------------
# The Playwright gate consumes the bracket too
# ---------------------------------------------------------------------------


class TestPlaywrightGateConsumesTheBracket:
    def _leg(self, **kw):
        from runtime.foundation.verification.runtime_shards import ShardResult

        base = dict(
            shard_id="playwright-chromium-visual",
            status="passed",
            exit_code=0,
            duration_seconds=1.0,
            fingerprint_before={"fingerprint": "a" * 64},
            fingerprint_after={"fingerprint": "a" * 64},
            fingerprint_stable=True,
        )
        base.update(kw)
        return ShardResult(**base)

    def test_a_clean_leg_certifies(self):
        from runtime.foundation.verification.playwright_shards import verify_legs

        assert verify_legs(["playwright-chromium-visual"], [self._leg()]) == []

    def test_a_leg_that_drifted_is_refused(self):
        from runtime.foundation.verification.playwright_shards import verify_legs

        leg = self._leg(
            fingerprint_after={"fingerprint": "b" * 64}, fingerprint_stable=False
        )
        problems = verify_legs(["playwright-chromium-visual"], [leg])
        assert problems
        assert "fingerprint changed" in problems[0]

    def test_a_legacy_leg_document_is_refused(self):
        from runtime.foundation.verification.playwright_shards import verify_legs

        problems = verify_legs(["playwright-chromium-visual"], [self._leg(
            fingerprint_before=None, fingerprint_after=None, fingerprint_stable=False
        )])
        assert problems
        assert "no fingerprint bracket" in problems[0]
