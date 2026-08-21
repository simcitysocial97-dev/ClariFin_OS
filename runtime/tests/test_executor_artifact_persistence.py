"""Executor artifact-persistence regression tests — M9.

Proves three invariants that the previous implementation violated:
  A. Successful command: stdout/stderr paths point to existing files with correct content.
  B. Failed command:   stdout/stderr paths still point to existing files.
  C. Empty stderr:      error == "" is distinct from error is None; stderr_path exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.foundation.verification.executor import Executor
from runtime.foundation.verification.models import VerificationStatus


@pytest.fixture
def executor(tmp_path: Path) -> Executor:
    return Executor(repo_root=tmp_path)


class TestExecutorArtifactPersistence:
    """Test A — successful command."""

    def test_success_persists_stdout_and_stderr(
        self, executor: Executor, tmp_path: Path
    ):
        result = executor.execute(
            "printf 'known stdout' >&1; echo 'known stderr' >&2",
            task_id="test-a-success",
        )

        assert result.exit_code == 0
        assert result.status == VerificationStatus.PASSED
        assert result.stdout_path is not None
        assert result.stderr_path is not None

        stdout_p = Path(result.stdout_path)
        stderr_p = Path(result.stderr_path)

        assert stdout_p.exists(), f"stdout_path does not exist: {result.stdout_path}"
        assert stderr_p.exists(), f"stderr_path does not exist: {result.stderr_path}"
        assert stdout_p.read_text(encoding="utf-8") == "known stdout"
        assert stderr_p.read_text(encoding="utf-8").strip() == "known stderr"

    def test_temp_files_are_cleaned_up(self, executor: Executor):
        """The original NamedTemporaryFile handles are gone; only durable copies remain."""
        result = executor.execute(
            "echo ok",
            task_id="test-a-cleanup",
        )
        # The durable file must exist; there should be no leftover temp files with
        # the original random suffix pattern (verify-{prefix}-*.txt).
        import glob

        leftovers = glob.glob(
            str(executor._results_dir / "verify-stdout-*.txt")
        ) + glob.glob(str(executor._results_dir / "verify-stderr-*.txt"))
        assert leftovers == [], f"Temp files were not cleaned up: {leftovers}"


class TestExecutorFailedCommand:
    """Test B — failed command preserves artifacts."""

    def test_failure_persists_stdout_and_stderr(self, executor: Executor):
        result = executor.execute(
            "echo 'some output'; echo 'some errors' >&2; exit 42",
            task_id="test-b-failure",
        )

        assert result.exit_code == 42
        assert result.status == VerificationStatus.FAILED
        assert result.stdout_path is not None
        assert result.stderr_path is not None

        assert Path(result.stdout_path).exists()
        assert Path(result.stderr_path).exists()
        assert "some output" in Path(result.stdout_path).read_text(encoding="utf-8")
        assert "some errors" in Path(result.stderr_path).read_text(encoding="utf-8")


class TestExecutorEmptyStderr:
    """Test C — empty stderr is distinct from missing stderr."""

    def test_empty_stderr_exit_one(self, executor: Executor):
        result = executor.execute(
            "printf 'known stdout'; exit 1",
            task_id="test-c-empty-stderr",
        )

        assert result.exit_code == 1
        assert result.status == VerificationStatus.FAILED
        assert result.error == ""
        assert result.stdout_path is not None
        assert result.stderr_path is not None

        assert Path(result.stdout_path).exists()
        assert Path(result.stdout_path).read_text(encoding="utf-8") == "known stdout"

        assert Path(result.stderr_path).exists()
        # stderr file exists but is empty — this is NOT "missing".
        assert Path(result.stderr_path).read_text(encoding="utf-8") == ""

    def test_error_none_vs_empty_string(self, executor: Executor):
        """error=None (no error supplied) vs error='' (subprocess failed, no stderr)."""
        passed = executor.execute("echo ok", task_id="test-c-none")
        assert passed.error is None

        failed_empty = executor.execute("printf out; exit 1", task_id="test-c-empty")
        assert failed_empty.error == ""
