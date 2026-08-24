from __future__ import annotations

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
        self._proc_lock = threading.Lock()

    def _build_exec_env(self) -> dict[str, str]:
        """Build the canonical execution environment (called once at init).

        Locally: ensures .venv/bin tools (python, pytest, ruff, black, mypy, mutmut, etc.)
        are resolved before any system installations.
        CI: .venv absent at repo_root; falls through to runner-provided PATH (equivalent semantics).

        ED7: Explicit locale/TZ policy for deterministic execution:
        - TZ=UTC: All date/time operations use UTC
        - LC_ALL=C.UTF-8: C locale with UTF-8 encoding for consistent sorting/formatting
        - LANG=C.UTF-8: Base locale for applications that don't set LC_ALL
        - PYTHONUNBUFFERED=1: Unbuffered Python output for real-time logging
        """
        env = dict(os.environ)
        env["PYTHONUNBUFFERED"] = "1"
        # ED7: Deterministic locale/TZ policy
        env["TZ"] = "UTC"
        env["LC_ALL"] = "C.UTF-8"
        env["LANG"] = "C.UTF-8"
        venv_bin = self._repo_root / ".venv" / "bin"
        if venv_bin.exists():
            env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"
        return env

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
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # Already gone
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
            try:
                proc.kill()
            except Exception:
                pass

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
            last_result = self._execute_once(command, task_id)
            if (
                last_result.status == VerificationStatus.PASSED
                or attempt == attempts - 1
            ):
                break
        assert last_result is not None
        return last_result

    def _execute_once(self, command: str, task_id: str = "") -> ExecutionResult:
        """Execute a command once without retry logic.

        C5.2: uses ``Popen`` with line-buffered pipe readers so output is written
        to durable evidence files and surfaced via ``_log_callback`` as soon as
        each line is produced — the CI log is no longer silent for hours.

        F19: Command runs in its own process group (start_new_session=True).
        Timeout/cancellation kills the entire process group via os.killpg().
        """
        start_time = datetime.now(UTC)
        task_label = task_id or "step"

        stdout_persistent = self._results_dir / f"{task_label}-stdout.txt"
        stderr_persistent = self._results_dir / f"{task_label}-stderr.txt"
        stdout_persistent.parent.mkdir(parents=True, exist_ok=True)
        stderr_persistent.parent.mkdir(parents=True, exist_ok=True)

        lock = threading.Lock()

        def _tee(pipe, persistent: Path, tag: str) -> None:
            """Read lines from *pipe*, write to *persistent* and invoke the
            log callback.  ``tag`` is used to prefix callback invocations so
            stdout/stderr mixing in the callback is disambiguated."""
            with persistent.open("a", encoding="utf-8") as fh:
                for raw in pipe:
                    line = (
                        raw
                        if isinstance(raw, str)
                        else raw.decode("utf-8", errors="replace")
                    )
                    with lock:
                        fh.write(line)
                        fh.flush()
                    if self._log_callback:
                        self._log_callback(f"[{tag}] {line}")

        try:
            # F19: start_new_session=True creates a new process group (setsid).
            # The process group ID equals the PID of the session leader.
            # This ensures we can kill the entire tree on timeout/cancellation.
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(self._repo_root),
                env=self._exec_env,
                start_new_session=True,  # F19: creates new session + process group
            )

            # Track process group for cleanup on timeout/cancellation
            with self._proc_lock:
                self._proc = proc
                self._current_pgid = os.getpgid(proc.pid)

            stdout_thread = threading.Thread(
                target=_tee, args=(proc.stdout, stdout_persistent, "OUT"), daemon=True
            )
            stderr_thread = threading.Thread(
                target=_tee, args=(proc.stderr, stderr_persistent, "ERR"), daemon=True
            )
            stdout_thread.start()
            stderr_thread.start()

            try:
                rc = proc.wait(timeout=self._per_step_timeout)
            except subprocess.TimeoutExpired:
                # F19: Kill entire process group, not just the shell
                self._kill_process_group()
                rc = -1

            stdout_thread.join(timeout=3)
            stderr_thread.join(timeout=3)

            duration = (datetime.now(UTC) - start_time).total_seconds()

            stderr_content = (
                stderr_persistent.read_text(encoding="utf-8")
                if stderr_persistent.exists()
                else ""
            )

            status = VerificationStatus.PASSED if rc == 0 else VerificationStatus.FAILED

            if rc == 0:
                error = None
                classification = FailureClassification.UNKNOWN_FAILURE
            else:
                error = stderr_content if stderr_content else ""
                classification = (
                    FailureClassification.TIMEOUT
                    if rc < 0
                    else FailureClassification.UNKNOWN_FAILURE
                )

            return ExecutionResult(
                task_id=task_id,
                command=command,
                status=status,
                exit_code=rc,
                duration_seconds=duration,
                stdout_path=str(stdout_persistent),
                stderr_path=str(stderr_persistent),
                error=error,
                classification=classification,
            )
        except subprocess.TimeoutExpired:
            # Fallback: ensure process group is killed
            self._kill_process_group()
            duration = (datetime.now(UTC) - start_time).total_seconds()
            return ExecutionResult(
                task_id=task_id,
                command=command,
                status=VerificationStatus.FAILED,
                exit_code=-1,
                duration_seconds=duration,
                stdout_path=(
                    str(stdout_persistent) if stdout_persistent.exists() else ""
                ),
                stderr_path=(
                    str(stderr_persistent) if stderr_persistent.exists() else ""
                ),
                error=f"Command timed out after {self._per_step_timeout} seconds",
                classification=FailureClassification.TIMEOUT,
            )
        except Exception as exc:
            # Fallback: ensure process group is killed
            self._kill_process_group()
            duration = (datetime.now(UTC) - start_time).total_seconds()
            return ExecutionResult(
                task_id=task_id,
                command=command,
                status=VerificationStatus.FAILED,
                exit_code=-1,
                duration_seconds=duration,
                stdout_path="",
                stderr_path="",
                error=str(exc),
                classification=FailureClassification.ENVIRONMENT_FAILURE,
            )
        finally:
            # Clear process group tracking
            with self._proc_lock:
                self._proc = None
                self._current_pgid = None

    def cancel(self) -> None:
        """Cancel any currently running commands by killing the process group."""
        self._cancel_flag.set()
        self._kill_process_group()

    def reset_cancel(self) -> None:
        """Reset the cancel flag to allow new commands."""
        self._cancel_flag.clear()
