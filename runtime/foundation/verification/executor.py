"""
Execution Pipeline — Program 7B

Executes verification commands and returns structured ExecutionResult objects.
No direct printing. Everything returns typed dataclasses.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
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

    Returns structured ExecutionResult objects.
    No direct printing.
    """

    def __init__(self, repo_root: Path | None = None):
        self._repo_root = repo_root or Path.cwd()
        self._results_dir = self._repo_root / "runtime" / "generated" / "execution"
        self._results_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, command: str, task_id: str = "") -> ExecutionResult:
        """Execute a command and return a structured result."""
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
                stdout_path=stdout_file.name,
                stderr_path=stderr_file.name,
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
                stdout_path=stdout_file.name,
                stderr_path=stderr_file.name,
                error=str(exc),
            )
        finally:
            self._cleanup_temp_file(stdout_file.name)
            self._cleanup_temp_file(stderr_file.name)

    def execute_python(self, module: str, args: list[str] | None = None) -> ExecutionResult:
        """Execute a Python module command."""
        cmd_parts = ["python3", "-m", module]
        if args:
            cmd_parts.extend(args)
        return self.execute(" ".join(cmd_parts))

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
        cmd_parts = ["python3", "-m", "pytest"]
        if paths:
            cmd_parts.extend(paths)
        if extra_args:
            cmd_parts.extend(extra_args)
        return self.execute(" ".join(cmd_parts))

    def execute_vitest(self, args: list[str] | None = None) -> ExecutionResult:
        """Execute vitest."""
        cmd_parts = ["cd", "frontend", "&&", "npx", "vitest", "run"]
        if args:
            cmd_parts.extend(args)
        return self.execute(" ".join(cmd_parts))

    def execute_playwright(self, args: list[str] | None = None) -> ExecutionResult:
        """Execute Playwright tests."""
        cmd_parts = ["cd", "frontend", "&&", "npx", "playwright", "test"]
        if args:
            cmd_parts.extend(args)
        return self.execute(" ".join(cmd_parts))

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
        """Write command output to a persistent file and return its path."""
        persistent_path = self._results_dir / Path(temp_path).name
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