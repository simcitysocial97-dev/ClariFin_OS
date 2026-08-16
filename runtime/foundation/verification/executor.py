from __future__ import annotations

import os
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

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
            if last_result.status == VerificationStatus.PASSED or attempt == attempts - 1:
                break
        return last_result

    def _execute_once(self, command: str, task_id: str = "") -> ExecutionResult:
        """Execute a command once without retry logic.

        C5.2: uses ``Popen`` with line-buffered pipe readers so output is written
        to durable evidence files and surfaced via ``_log_callback`` as soon as
        each line is produced — the CI log is no longer silent for hours.
        """
        start_time = datetime.now(timezone.utc)
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
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(self._repo_root),
                env={
                    **os.environ,
                    "PYTHONUNBUFFERED": "1",
                },
            )

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
                proc.kill()
                proc.wait(timeout=5)
                rc = -1

            stdout_thread.join(timeout=3)
            stderr_thread.join(timeout=3)

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

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
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ExecutionResult(
                task_id=task_id,
                command=command,
                status=VerificationStatus.FAILED,
                exit_code=-1,
                duration_seconds=duration,
                stdout_path=str(stdout_persistent) if stdout_persistent.exists() else "",
                stderr_path=str(stderr_persistent) if stderr_persistent.exists() else "",
                error=f"Command timed out after {self._per_step_timeout} seconds",
                classification=FailureClassification.TIMEOUT,
            )
        except Exception as exc:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
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

    def retry(self, command: str, task_id: str = "", max_retries: int = 3) -> ExecutionResult:
        """Execute a command with retry logic for transient failures."""
        return self.execute(command, task_id=task_id, max_retries=max_retries)

    def cancel(self) -> None:
        """Cancel any currently running commands."""
        self._cancel_flag.set()

    def reset_cancel(self) -> None:
        """Reset the cancel flag to allow new commands."""
        self._cancel_flag.clear()

    def execute_parallel(
        self, commands: list[str], task_id: str = ""
    ) -> list[ExecutionResult]:
        """Execute multiple commands in parallel using a thread pool."""
        self._cancel_flag.clear()
        results: list[ExecutionResult] = []
        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=min(len(commands), 4)) as executor:
            future_to_cmd = {
                executor.submit(self.execute, cmd, f"{task_id}-{i}"): cmd
                for i, cmd in enumerate(commands)
            }
            for future in as_completed(future_to_cmd):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    results.append(
                        ExecutionResult(
                            task_id=task_id,
                            command=future_to_cmd[future],
                            status=VerificationStatus.FAILED,
                            exit_code=-1,
                            duration_seconds=0.0,
                            stdout_path="",
                            stderr_path="",
                            error=str(exc),
                        )
                    )
        return results

    def execute_python(self, module: str, args: list[str] | None = None) -> ExecutionResult:
        """Execute a Python module command."""
        cmd = f"python3 -m {module}"
        if args:
            cmd += " " + " ".join(args)
        return self.execute(cmd)

    def execute_npm(self, command: str, cwd: str | None = None) -> ExecutionResult:
        """Execute an npm command."""
        full_command = f"cd frontend && npm {command}"
        if cwd:
            full_command = f"cd {cwd} && npm {command}"
        return self.execute(full_command)

    def execute_pytest(
        self,
        paths: list[str] | None = None,
        extra_args: list[str] | None = None,
    ) -> ExecutionResult:
        """Execute pytest with optional paths and arguments."""
        cmd = "python3 -m pytest"
        if paths:
            cmd += " " + " ".join(paths)
        if extra_args:
            cmd += " " + " ".join(extra_args)
        return self.execute(cmd)

    def execute_vitest(self, args: list[str] | None = None) -> ExecutionResult:
        """Execute vitest."""
        cmd = "cd frontend && npx vitest run"
        if args:
            cmd += " " + " ".join(args)
        return self.execute(cmd)

    def execute_playwright(self, args: list[str] | None = None) -> ExecutionResult:
        """Execute Playwright tests."""
        cmd = "cd frontend && npx playwright test"
        if args:
            cmd += " " + " ".join(args)
        return self.execute(cmd)

    def execute_schemathesis(
        self,
        target: str,
        max_examples: int = 50,
    ) -> ExecutionResult:
        """Execute schemathesis contract tests."""
        command = (
            f"python3 -m schemathesis run "
            f"--hypothesis-max-examples={max_examples} "
            f"--hypothesis-database=none "
            f"{target}"
        )
        return self.execute(command)
