from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.models import (
    ExecutionResult,
    FailureClassification,
    VerificationStatus,
)


class Executor:
    """
    Execution pipeline for verification commands.

    Supports:
    - Python commands (python3 -m ...)
    - npm commands (npm run ...)
    - pytest
    - vitest
    - playwright
    - schemathesis
    - Shell commands (bash ...)
    - Retry logic for transient failures
    - Cancellation of long-running commands
    - Parallel execution of multiple commands
    - Streaming output to both durable artifacts and the console (C5.2)
    - Process-group ownership: every command runs in its own process group;
      timeout/cancellation kills the entire group (F19 fix).

    Returns structured ExecutionResult objects.
    """

    def __init__(
        self,
        repo_root: Path | None = None,
        per_step_timeout: int = 3600,
        log_callback: Callable[[str], None] | None = None,
    ):
        self._repo_root = repo_root or Path.cwd()
        self._results_dir = self._repo_root / "runtime" / "generated" / "execution"
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._max_retries = 3
        self._retry_delay = 1
        self._cancel_flag = threading.Event()
        self._per_step_timeout = per_step_timeout
        # C5.2: callback invoked with every output line so the orchestrator can
        # surface progress to the CI log in real time instead of waiting for the
        # subprocess to finish (the original capture_output=True behaviour).
        self._log_callback = log_callback
        # Canonical execution environment: prepend .venv/bin when it exists
        self._exec_env = self._build_exec_env()
        # Process-group tracking for F19
        self._current_pgid: int | None = None
        self._proc: subprocess.Popen | None = None
        self._attempt_index = 0
        self._proc_lock = threading.Lock()

    def _build_exec_env(self) -> dict[str, str]:
        """Build the canonical execution environment (called once at init).

        Delegates to env.child_process_env — the single canonical
        child-environment contract shared by every executor:
          * venv/bin (and the runtime interpreter's bin dir) precede PATH,
          * locally the .venv toolchain is used, in CI the runner-provisioned
            Python is used (no .venv present),
          * ED7 locale/TZ policy for deterministic output.
        """
        from runtime.foundation.verification.env import child_process_env

        return child_process_env()

    def _kill_process_group(self) -> None:
        """Kill the entire process group associated with the current command.

        This ensures no orphaned descendants survive timeout or cancellation (F19).
        """
        with self._proc_lock:
            pgid = self._current_pgid
            proc = self._proc
            self._current_pgid = None
            self._proc = None

        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)
                # Give processes a moment to terminate gracefully
                time.sleep(0.5)
                # Force kill any remaining
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(pgid, signal.SIGKILL)  # Already gone
            except ProcessLookupError:
                pass  # Process group already gone
            except PermissionError:
                pass  # No permission (shouldn't happen for our children)
            # Evidence: record process group termination
            self._record_lifecycle_event(
                "process_group_killed", {"pgid": pgid, "signal": "SIGTERM+SIGKILL"}
            )

        # Also try direct proc kill as fallback
        if proc is not None:
            with contextlib.suppress(Exception):
                proc.kill()

    def _record_lifecycle_event(self, event_type: str, details: dict) -> None:
        """Record a lifecycle event for evidence tracking."""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event_type,
            "details": details,
        }
        # Append to lifecycle log
        log_file = self._results_dir / "lifecycle-events.jsonl"
        try:
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass  # Non-critical

    def _set_process_group(self) -> None:
        """Called in child process to create new process group."""
        os.setsid()

    def execute(
        self,
        command: str,
        task_id: str = "",
        max_retries: int = 0,
    ) -> ExecutionResult:
        """Execute a command and return a structured result with optional retry."""
        last_result: ExecutionResult | None = None
        attempts = max(1, max_retries + 1)
        for attempt in range(attempts):
            if self._cancel_flag.is_set():
                return ExecutionResult(
                    task_id=task_id,
                    command=command,
                    status=VerificationStatus.FAILED,
                    exit_code=-1,
                    duration_seconds=0.0,
                    stdout_path="",
                    stderr_path="",
                    error="Command cancelled",
                )
            self._attempt_index = attempt
            last_result = self._execute_once(command, task_id)
            if (
                last_result.status == VerificationStatus.PASSED
                or attempt == attempts - 1
            ):
                break
        assert last_result is not None
        return last_result

    def _execute_once(self, command: str, task_id: str = "") -> ExecutionResult:
        """Execute a command once, by delegating to the canonical worker.

        M10-R3 (L8d). This used to be a second, hand-rolled process engine: its own
        ``subprocess.Popen(shell=True, start_new_session=True)``, its own line-buffered
        tee, its own ``_kill_process_group``, its own result directory. Between them the
        repository had two spawn paths for the same work, and only the canonical one had
        heartbeat, ``classify_termination`` and missing-binary detection — so anything
        routed through here reported a failed assertion for a command that never ran.

        It now calls :func:`parallel_executor.run_streaming_command` and maps the result.
        The engine is deleted rather than kept alongside, because "two workers, pick one"
        is the condition this milestone set out to remove.

        One behaviour changes, deliberately: **each attempt gets its own evidence file.**

        The old code appended every attempt into ``<task>-stdout.txt``, so after a retry
        the file held attempt 1's output followed by attempt 2's with nothing to
        distinguish them. The canonical worker truncates up front — *"a file means this
        execution"*, because leftover content masquerading as current output is precisely
        the stale-evidence hazard this milestone targets. Per-attempt files preserve
        every attempt's evidence and make each one attributable, which append could not.
        """
        from runtime.foundation.verification.parallel_executor import (
            classify_termination,
            run_streaming_command,
        )

        start_time = datetime.now(UTC)
        task_label = task_id or "step"
        attempt = getattr(self, "_attempt_index", 0)

        stdout_persistent = self._results_dir / f"{task_label}-a{attempt}-stdout.txt"
        stderr_persistent = self._results_dir / f"{task_label}-a{attempt}-stderr.txt"
        stdout_persistent.parent.mkdir(parents=True, exist_ok=True)

        def _emit(line: str) -> None:
            """Per-line live output, the capability that kept this engine alive."""
            if self._log_callback:
                self._log_callback(line.rstrip("\n"))

        result = run_streaming_command(
            command,
            stdout_path=stdout_persistent,
            stderr_path=stderr_persistent,
            timeout_seconds=self._per_step_timeout,
            cwd=self._repo_root,
            env=self._exec_env,
            on_line=_emit,
            # Cancellation is the caller's right, and the child now belongs to the
            # canonical worker, so the right is passed down with it.
            cancel_event=self._cancel_flag if self._cancel_flag.is_set() or True else None,
        )

        duration = (datetime.now(UTC) - start_time).total_seconds()
        termination = classify_termination(
            result.exit_code, result.timed_out, result.infra_error
        )

        if result.infra_error:
            status = VerificationStatus.FAILED
            error = result.infra_error
            classification = FailureClassification.ENVIRONMENT_FAILURE
        elif result.timed_out:
            status = VerificationStatus.FAILED
            error = (
                f"per-step timeout of {self._per_step_timeout}s exceeded "
                f"({termination['detail']})"
            )
            classification = FailureClassification.TIMEOUT
        elif result.exit_code == 0:
            status = VerificationStatus.PASSED
            error = None
            classification = FailureClassification.UNKNOWN_FAILURE
        else:
            status = VerificationStatus.FAILED
            # Preserve the three-way distinction the result contract encodes:
            #   error is None  -> no error, the command passed
            #   error is ""    -> the command failed and produced no stderr
            #   error is text  -> the command failed and stderr holds the reason
            #
            # Substituting "exit N" for the empty case would collapse the second and
            # third into one, and the exit code is already carried in its own field.
            error = result.stderr
            classification = FailureClassification.UNKNOWN_FAILURE

        return ExecutionResult(
            task_id=task_id,
            command=command,
            status=status,
            exit_code=result.exit_code if result.exit_code is not None else -1,
            duration_seconds=duration,
            stdout_path=str(stdout_persistent),
            stderr_path=str(stderr_persistent),
            error=error,
            classification=classification,
        )

    def cancel(self) -> None:
        """Cancel any currently running commands by killing the process group."""
        self._cancel_flag.set()
        self._kill_process_group()

    def reset_cancel(self) -> None:
        """Reset the cancel flag to allow new commands."""
        self._cancel_flag.clear()
