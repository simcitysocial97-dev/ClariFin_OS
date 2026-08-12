from __future__ import annotations

import os
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from runtime.foundation.verification.models import (
    ExecutionResult,
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

    Returns structured ExecutionResult objects.
    No direct printing.
    """

    def __init__(self, repo_root: Path | None = None):
        self._repo_root = repo_root or Path.cwd()
        self._results_dir = self._repo_root / "runtime" / "generated" / "execution"
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._max_retries = 3
        self._retry_delay = 1
        self._cancel_flag = threading.Event()
        self._parallel_executor: ThreadPoolExecutor | None = None

    def execute(self, command: str, task_id: str = "", max_retries: int = 0) -> ExecutionResult:
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
        """Execute a command once without retry logic."""
        start_time = datetime.now(timezone.utc)

        stdout_file = self._create_temp_file("stdout")
        stderr_file = self._create_temp_file("stderr")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600,
                cwd=str(self._repo_root),
                env={
                    **os.environ,
                    "PYTHONUNBUFFERED": "1",
                },
            )
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            stdout_path = self._write_output(stdout_file.name, result.stdout)
            stderr_path = self._write_output(stderr_file.name, result.stderr)

            status = (
                VerificationStatus.PASSED
                if result.returncode == 0
                else VerificationStatus.FAILED
            )

            return ExecutionResult(
                task_id=task_id,
                command=command,
                status=status,
                exit_code=result.returncode,
                duration_seconds=duration,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                error=result.stderr if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            return ExecutionResult(
                task_id=task_id,
                command=command,
                status=VerificationStatus.FAILED,
                exit_code=-1,
                duration_seconds=duration,
                stdout_path="",
                stderr_path="",
                error="Command timed out after 3600 seconds",
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
            )
        finally:
            self._cleanup_temp_file(stdout_file.name)
            self._cleanup_temp_file(stderr_file.name)

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

    def _create_temp_file(self, prefix: str) -> tempfile._TemporaryFileWrapper:
        """Create a temporary file for capturing output."""
        return tempfile.NamedTemporaryFile(
            prefix=f"verify-{prefix}-",
            suffix=".txt",
            dir=str(self._results_dir),
            delete=False,
            mode="w",
        )

    def _write_output(self, temp_path: str, content: str) -> str:
        """Write command output to a durable persistent file and return its path.

        The durable path uses a timestamped name distinct from the temporary file
        name so that ``_cleanup_temp_file`` cannot accidentally delete the persisted
        evidence.
        """
        import time

        temp_name = Path(temp_path).name
        durable_name = f"{time.monotonic_ns()}_{temp_name}"
        persistent_path = self._results_dir / durable_name
        self._results_dir.mkdir(parents=True, exist_ok=True)
        persistent_path.write_text(content, encoding="utf-8")
        return str(persistent_path)

    def _cleanup_temp_file(self, temp_path: str) -> None:
        """Remove temporary file if it still exists."""
        try:
            p = Path(temp_path)
            if p.exists():
                p.unlink()
        except Exception:
            pass