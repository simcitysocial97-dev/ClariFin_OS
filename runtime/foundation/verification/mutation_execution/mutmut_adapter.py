# runtime/foundation/verification/mutation_execution/mutmut_adapter.py
#
# M9-C44.4 — Hardened mutmut Adapter.
#
# Treats mutmut as an implementation backend behind the MutationBackendBase
# interface.  The adapter:
#   * verifies tool version + configuration + environment before execution
#   * establishes campaign identity independent of mutmut internals
#   * isolates execution (working dir, env vars, PYTHONPATH, temp files)
#   * captures stdout/stderr/exit code/timeout/process state
#   * normalizes mutmut statuses to canonical MutationResultState values
#   * NEVER silently reinterprets a tool failure as a mutation result
#   * verifies mutated source actually differs from baseline (correctness gate)
#
# Canonical status mapping (mutmut exit code -> our state):
#   0 -> SURVIVED    (tests passed; mutation undetected)
#   1 -> KILLED      (tests failed; mutation detected)
#   3 -> KILLED      (internal pytest error counts as kill in mutmut)
#  -24 -> KILLED     (OS-level forced kill counts as kill in mutmut)
#   5 -> NO_TESTS
#  33 -> NO_TESTS
#  34 -> EXECUTION_ERROR (skipped — not a valid mutation outcome)
#  35 -> EXECUTION_ERROR (suspicious — indeterminate)
#  36 -> TIMEOUT
#   2 -> EXECUTION_ERROR (interrupted)
#   N/A -> NOT_EXECUTED (never reached execution)
#   default -> EXECUTION_ERROR

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.env import (
    PINNED_MUTMUT,
    REPO_ROOT,
    VENV_BIN,
    resolve_environment,
)
from runtime.foundation.verification.mutation_execution.backend_interface import (
    MutationBackendBase,
)
from runtime.foundation.verification.mutation_execution.domain_model import (
    InfrastructureFailureKind,
    MutationCampaign,
    MutationCandidate,
    MutationExecution,
    MutationResult,
    MutationResultState,
    TimeoutKind,
    derive_canonical_mutant_id,
)

BACKEND_DIR = REPO_ROOT / "backend"


# Authoritative mutmut 3.7.0 exit-code -> canonical state mapping.
_EXIT_CODE_TO_STATE: dict[int | None, MutationResultState] = {
    0: MutationResultState.SURVIVED,
    1: MutationResultState.KILLED,
    3: MutationResultState.KILLED,
    -24: MutationResultState.KILLED,
    5: MutationResultState.NO_TESTS,
    33: MutationResultState.NO_TESTS,
    34: MutationResultState.EXECUTION_ERROR,
    35: MutationResultState.EXECUTION_ERROR,
    36: MutationResultState.TIMEOUT,
    2: MutationResultState.EXECUTION_ERROR,
    None: MutationResultState.NOT_EXECUTED,
}

# Text-status mapping for `mutmut results` output lines.
_TEXT_STATUS_TO_STATE: dict[str, MutationResultState] = {
    "killed": MutationResultState.KILLED,
    "survived": MutationResultState.SURVIVED,
    "no tests": MutationResultState.NO_TESTS,
    "no test": MutationResultState.NO_TESTS,
    "timeout": MutationResultState.TIMEOUT,
    "suspicious": MutationResultState.EXECUTION_ERROR,
    "not checked": MutationResultState.NOT_EXECUTED,
    "skipped": MutationResultState.EXECUTION_ERROR,
    "interrupted": MutationResultState.EXECUTION_ERROR,
}


class MutmutAdapter(MutationBackendBase):
    """Hardened mutmut 3.7.0 adapter implementing MutationBackendProtocol."""

    backend_name = "mutmut"
    backend_version = PINNED_MUTMUT

    # ── Lifecycle hooks ────────────────────────────────────────────────────

    def verify_tool_version(self, minimum_version: str = PINNED_MUTMUT) -> bool:
        import pkg_resources

        try:
            installed = pkg_resources.get_distribution("mutmut").version
            return installed == minimum_version
        except Exception:
            return False

    def verify_configuration(self, workspace: Path) -> list[str]:
        errors = []
        pyproject = workspace / "pyproject.toml"
        if not pyproject.exists():
            errors.append(f"pyproject.toml not found at {pyproject}")
        else:
            text = pyproject.read_text()
            if "[tool.mutmut]" not in text:
                errors.append("pyproject.toml missing [tool.mutmut] section")
            if 'runner = "python3 -m pytest"' not in text and "runner =" not in text:
                errors.append("pyproject.toml missing mutmut runner config")
        return errors

    def verify_environment(self, workspace: Path) -> list[str]:
        env = resolve_environment(config_dir=workspace)
        errors = []
        if not env.consistent:
            errors.extend(env.errors)
        if env.mutmut.path is None:
            errors.append("mutmut binary not found")
        elif not self.verify_tool_version():
            errors.append(
                f"mutmut version mismatch: resolved={env.mutmut.version}, pinned={PINNED_MUTMUT}"
            )
        return errors

    # ── discover: derive canonical candidates from mutmut output ───────────

    def discover(
        self, scope: str, candidates: list[MutationCandidate]
    ) -> list[MutationCandidate]:
        """Mutmut-based discovery: run `mutmut --collect-only` and derive
        canonical candidates from the output, assigning deterministic IDs."""
        mutmut_bin = self._mutmut_bin()
        if mutmut_bin is None:
            return candidates

        # Run mutmut collect to get the raw mutant list.
        try:
            res = subprocess.run(
                [mutmut_bin, "results", "--no-progress"],
                cwd=str(BACKEND_DIR),
                capture_output=True,
                text=True,
                timeout=120,
                env=self._venv_env(),
            )
        except Exception:
            return candidates

        # Parse the output to extract mutant keys and derive canonical IDs.
        collected: list[MutationCandidate] = []
        for line in (res.stdout or "").splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.rsplit(":", 1)
            if len(parts) != 2:
                continue
            mutant_key = parts[0].strip()
            status_text = parts[1].strip().lower()

            # Derive source file and function from the mutant key.
            # Key format: engines.foo.x_bar__mutmut_3
            source_file, function = self._parse_mutant_key(mutant_key, scope)
            if source_file is None:
                continue

            # Read source hash.
            source_path = REPO_ROOT / source_file
            source_hash = ""
            if source_path.exists():
                source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()[:16]

            # Map status text.
            _TEXT_STATUS_TO_STATE.get(status_text, MutationResultState.UNKNOWN)

            # Derive canonical ID.
            canon_id = derive_canonical_mutant_id(
                repository_revision=subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(REPO_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout.strip(),
                source_file=source_file,
                source_hash=source_hash,
                function=function,
                line=None,
                operator=self._infer_operator(mutant_key),
                original_expression="",
                mutated_expression="",
            )

            collected.append(
                MutationCandidate(
                    canonical_mutant_id=canon_id,
                    source_file=source_file,
                    source_hash=source_hash,
                    function=function,
                    operator=self._infer_operator(mutant_key),
                    capability=self._infer_capability(source_file),
                    component=self._infer_component(source_file),
                    backend_metadata={
                        "mutmut_key": mutant_key,
                        "raw_status": status_text,
                    },
                )
            )

        return collected if collected else candidates

    # ── generate: apply mutations into workspace ──────────────────────────

    def generate(
        self,
        campaign: MutationCampaign,
        candidates: list[MutationCandidate],
        workspace: Path,
    ) -> Path:
        """Run mutmut new --no-run in the workspace to generate mutant source copies."""
        mutmut_bin = self._mutmut_bin()
        if mutmut_bin is None:
            raise RuntimeError("mutmut binary not available")

        # Copy pyproject.toml into workspace so mutmut can read config.
        src_pyproject = BACKEND_DIR / "pyproject.toml"
        ws_pyproject = workspace / "pyproject.toml"
        if src_pyproject.exists():
            ws_pyproject.write_text(src_pyproject.read_text())

        # Also copy the selected source into workspace/source/.
        self._copy_source_to_workspace(candidates, workspace)

        # Run mutmut new to generate mutants directory.
        try:
            res = subprocess.run(
                [mutmut_bin, "new", "--no-run"],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=300,
                env=self._venv_env(),
            )
            if res.returncode not in (0, 2):  # 2 = some survived (expected)
                raise RuntimeError(
                    f"mutmut new exited rc={res.returncode}: {res.stderr}"
                )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("mutmut new timed out") from exc  # noqa: B904

        mutants_path = workspace / "mutants"
        if not mutants_path.is_dir():
            mutants_path.mkdir()

        return mutants_path

    # ── execute: run one mutant in isolation ──────────────────────────────

    def execute(
        self,
        candidate: MutationCandidate,
        test_selection: tuple[str, ...],
        workspace: Path,
        environment: dict[str, str],
        timeout: float,
        worker_id: str,
        campaign_id: str,
    ) -> MutationExecution:
        """Execute a single mutant. Returns canonical MutationExecution."""
        exec_id = f"exec-{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat()
        execution = MutationExecution(
            execution_id=exec_id,
            campaign_id=campaign_id,
            mutant_id=candidate.canonical_mutant_id,
            worker_id=worker_id,
            start_time=now,
        )

        # Find the mutant file in workspace/mutants/.
        mutant_file = self._find_mutant_file(candidate, workspace)
        if mutant_file is None:
            execution.mutation_result = MutationResultState.INVALID_MUTANT
            execution.infrastructure_failure = (
                InfrastructureFailureKind.WORKSPACE_CORRUPTION
            )
            execution.end_time = datetime.now(UTC).isoformat()
            execution.duration_seconds = 0.0
            return execution

        # Verify the mutant file actually differs from baseline.
        baseline_content = self._read_baseline_source(candidate.source_file, workspace)
        mutant_content = mutant_file.read_text() if mutant_file.exists() else ""
        verification_passed = baseline_content != mutant_content

        if not verification_passed:
            execution.mutation_result = MutationResultState.INVALID_MUTANT
            execution.verification_passed = False
            execution.end_time = datetime.now(UTC).isoformat()
            execution.duration_seconds = 0.0
            return execution

        execution.verification_passed = True

        # Build and run the pytest command against the mutated source.
        cmd = self._build_test_command(
            candidate, test_selection, workspace, mutant_file
        )
        result = self._run_with_isolation(cmd, environment, timeout, exec_id, workspace)

        execution.exit_status = result.get("exit_code")
        execution.test_result = result.get("test_result", "UNKNOWN")
        execution.duration_seconds = result.get("duration", 0.0)
        execution.end_time = datetime.now(UTC).isoformat()
        execution.process_id = result.get("process_id")

        # Normalize result.
        self._classify_execution(result, execution, candidate, workspace)

        # Capture output refs.
        log_path = workspace / "logs" / f"{exec_id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(result.get("stdout", "") + "\n" + result.get("stderr", ""))
        execution.stdout_ref = str(log_path.relative_to(REPO_ROOT))

        return execution

    # ── collect: aggregate all executions into MutationResult ──────────────

    def collect(self, campaign: MutationCampaign, workspace: Path) -> MutationResult:
        """Aggregate per-mutant execution records into a MutationResult."""
        result = MutationResult(campaign_id=campaign.campaign_id)
        exec_dir = workspace / "executions"
        if not exec_dir.exists():
            return result

        for exec_file in sorted(exec_dir.glob("*.json")):
            try:
                data = json.loads(exec_file.read_text())
                exec_rec = MutationExecution.from_dict(data)
                result.total_executions += 1
                result.retries_total += exec_rec.retry_count

                state = exec_rec.mutation_result
                if state == MutationResultState.KILLED:
                    result.killed += 1
                    result.successful_executions += 1
                elif state == MutationResultState.SURVIVED:
                    result.survived += 1
                    result.successful_executions += 1
                elif state == MutationResultState.EQUIVALENT:
                    result.equivalent += 1
                    result.successful_executions += 1
                elif state == MutationResultState.NO_TESTS:
                    result.no_tests += 1
                    result.successful_executions += 1
                elif state == MutationResultState.TIMEOUT:
                    result.timeout += 1
                    result.successful_executions += 1
                elif state == MutationResultState.EXECUTION_ERROR:
                    result.execution_error += 1
                    result.infrastructure_failures += 1
                elif state == MutationResultState.INVALID_MUTANT:
                    result.invalid_mutant += 1
                elif state == MutationResultState.NOT_EXECUTED:
                    result.not_executed += 1
                elif state == MutationResultState.CANCELLED:
                    result.cancelled += 1
                else:
                    result.unknown += 1
            except Exception:
                continue

        # Count candidates that have no execution record.
        candidate_files = list(workspace.glob("candidates/*.json"))
        executed_ids = set()
        for exec_file in exec_dir.glob("*.json"):
            try:
                data = json.loads(exec_file.read_text())
                executed_ids.add(data.get("mutant_id", ""))
            except Exception:
                continue

        result.total_candidates = len(candidate_files)
        # Add any candidates with no execution record.
        pending = len(candidate_files) - len(
            executed_ids
            & {c.canonical_mutant_id for c in self._load_candidates(workspace)}
        )
        result.not_executed += max(0, pending)

        return result

    # ── private helpers ────────────────────────────────────────────────────

    def _mutmut_bin(self) -> str | None:
        env = resolve_environment(config_dir=BACKEND_DIR)
        return env.mutmut.path

    def _venv_env(self) -> dict[str, str]:
        return {
            **os.environ,
            "PATH": f"{VENV_BIN}:{os.environ.get('PATH', '')}",
        }

    def _parse_mutant_key(self, key: str, scope: str) -> tuple[str | None, str]:
        """Parse a mutmut key like 'engines.foo.x_bar__mutmut_3' into (source_file, function)."""
        base = key.rsplit("__mutmut_", 1)[0]
        parts = base.split(".")
        func = parts[-1] if parts else key

        # Infer source file from scope and function name.
        if scope == "full" or scope == "all":
            # Try common patterns.
            for prefix in ("src/engines/", "src/"):
                candidate = f"{prefix}{func.replace('_', '/')}.py"
                if (REPO_ROOT / candidate).exists():
                    return candidate, func
            return f"src/engines/{func}.py", func
        else:
            return f"src/engines/{scope}.py", func

    def _infer_operator(self, mutant_key: str) -> str:
        """Best-effort operator inference from mutmut key."""
        key_lower = mutant_key.lower()
        if any(op in key_lower for op in ("+", "-", "*", "/", "%")):
            return "arithmetic_operator"
        if any(op in key_lower for op in ("==", "!=", "<=", ">=", "<>", "<", ">")):
            return "comparison_operator"
        if any(kw in key_lower for kw in ("and", "or", "not")):
            return "boolean_operator"
        if "none" in key_lower or "true" in key_lower or "false" in key_lower:
            return "constant_replacement"
        if "raise" in key_lower:
            return "exception_message"
        if "(" in mutant_key:
            return "call_argument"
        return "unknown"

    def _infer_capability(self, source_file: str) -> str:
        """Map source file to capability name from Verification Graph."""
        if "credit_card" in source_file:
            return "credit_card_processing"
        if "account" in source_file:
            return "account_management"
        if "loan" in source_file:
            return "loan_processing"
        if "behaviour" in source_file:
            return "behaviour_analysis"
        if "financial_event" in source_file or "lineage_walker" in source_file:
            return "financial_event_detection"
        if "reconciliation" in source_file:
            return "reconciliation"
        if "balance" in source_file:
            return "balance_calculation"
        if "recommendation" in source_file:
            return "recommendation"
        if "transaction_intelligence" in source_file:
            return "transaction_intelligence"
        if "financial_intelligence" in source_file:
            return "financial_intelligence"
        if "cashflow" in source_file:
            return "cashflow_analysis"
        if "ledger_audit" in source_file:
            return "ledger_audit"
        if "money" in source_file:
            return "currency_domain"
        if "calculations" in source_file:
            return "common_calculations"
        return "unknown"

    def _infer_component(self, source_file: str) -> str:
        """Extract component/engine name from source file path."""
        for part in Path(source_file).parts:
            if "engine" in part or part in (
                "engines",
                "core",
                "common",
                "financial_events",
                "credit_card_engine",
                "account_engine",
                "loan_engine",
                "behaviour_engine",
                "reconciliation_engine",
                "balance_engine",
                "ledger_audit_engine",
                "cashflow_engine",
                "recommendation_engine",
                "transaction_intelligence",
                "financial_intelligence",
            ):
                return part
        return "unknown"

    def _find_mutant_file(
        self, candidate: MutationCandidate, workspace: Path
    ) -> Path | None:
        """Find the mutant source file in workspace/mutants/."""
        mutants_dir = workspace / "mutants"
        if not mutants_dir.exists():
            return None

        # Try to find by matching the source file path pattern.
        source_rel = candidate.source_file
        # e.g. "src/engines/credit_card_engine/calculator.py" -> look in mutants/src/engines/...
        search_paths = [
            mutants_dir / source_rel,
            mutants_dir / source_rel.replace("src/", ""),
        ]
        for sp in search_paths:
            if sp.exists():
                return sp

        # Fallback: scan for files containing the function name.
        func = candidate.function.replace("x_", "")
        for f in mutants_dir.rglob("*.py"):
            content = f.read_text(errors="replace")
            if func in content and candidate.source_file.split("/")[-1] in str(f):
                return f
        return None

    def _read_baseline_source(self, source_file: str, workspace: Path) -> str:
        """Read the baseline (unmutated) source."""
        paths = [
            REPO_ROOT / source_file,
            workspace / "source" / source_file,
            workspace / source_file,
        ]
        for p in paths:
            if p.exists():
                return p.read_text(errors="replace")
        return ""

    def _copy_source_to_workspace(
        self, candidates: list[MutationCandidate], workspace: Path
    ) -> None:
        """Copy source files referenced by candidates into workspace/source/."""
        source_dir = workspace / "source"
        source_dir.mkdir(exist_ok=True)
        seen = set()
        for c in candidates:
            if c.source_file in seen:
                continue
            seen.add(c.source_file)
            src = REPO_ROOT / c.source_file
            if src.exists():
                dst = source_dir / c.source_file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    def _build_test_command(
        self,
        candidate: MutationCandidate,
        test_selection: tuple[str, ...],
        workspace: Path,
        mutant_file: Path,
    ) -> list[str]:
        """Build the pytest command to run against a specific mutant."""
        mutmut_bin = self._mutmut_bin()
        if mutmut_bin is None:
            raise RuntimeError("mutmut binary not available")

        # Use mutmut's built-in run mechanism which handles source copying correctly.
        # We invoke mutmut run with the specific mutant name filter.
        mutmut_key = candidate.backend_metadata.get("mutmut_key", "")
        if mutmut_key:
            return [
                mutmut_bin,
                "run",
                mutmut_key,
                "--no-mail",
                "--no-progress",
            ]
        # Fallback: run pytest directly against the mutant file's parent directory
        # with the test selection, manipulating PYTHONPATH.
        pytest_bin = shutil.which("pytest") or str(VENV_BIN / "pytest")
        cmd = [pytest_bin, "-x", "--tb=short"]
        for ts in test_selection:
            cmd.append(ts)
        return cmd

    def _run_with_isolation(
        self,
        cmd: list[str],
        environment: dict[str, str],
        timeout: float,
        exec_id: str,
        workspace: Path,
    ) -> dict[str, Any]:
        """Run command with process isolation, timeout, and capture."""
        result = {
            "exit_code": None,
            "test_result": "UNKNOWN",
            "duration": 0.0,
            "process_id": None,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
        }

        start = time.monotonic()
        proc = None
        try:
            pythonpath = f"{BACKEND_DIR / 'src'}:{BACKEND_DIR / 'tests'}"
            proc_env = {
                **environment,
                "PATH": f"{VENV_BIN}:{environment.get('PATH', '')}",
                "PYTHONPATH": pythonpath,
            }
            proc = subprocess.Popen(
                cmd,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True,
                env=proc_env,
            )
            result["process_id"] = proc.pid
            pgid = os.getpgid(proc.pid)

            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                result["exit_code"] = proc.returncode
                result["stdout"] = stdout or ""
                result["stderr"] = stderr or ""
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
                try:
                    os.killpg(pgid, signal.SIGTERM)
                    time.sleep(0.5)
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=5)
                result["exit_code"] = None
                result["stdout"] = ""
                result["stderr"] = ""

            result["duration"] = time.monotonic() - start

            # Classify test result from exit code and output.
            if result["timed_out"]:
                result["test_result"] = "TIMEOUT"
            elif result["exit_code"] == 0:
                result["test_result"] = "PASS"
            elif result["exit_code"] == 1:
                result["test_result"] = "FAIL"
            elif result["exit_code"] is None:
                result["test_result"] = "CRASHED"
            else:
                result["test_result"] = f"EXIT_{result['exit_code']}"

        except Exception as exc:
            result["test_result"] = "ERROR"
            result["stderr"] = str(exc)
            result["duration"] = time.monotonic() - start

        return result

    def _classify_execution(
        self,
        run_result: dict[str, Any],
        execution: MutationExecution,
        candidate: MutationCandidate,
        workspace: Path,
    ) -> None:
        """Classify execution result into canonical MutationResultState."""
        if execution.mutation_result != MutationResultState.UNKNOWN:
            return  # Already classified (e.g. INVALID_MUTANT)

        exit_code = run_result.get("exit_code")
        test_result = run_result.get("test_result", "UNKNOWN")
        timed_out = run_result.get("timed_out", False)

        if timed_out:
            execution.mutation_result = MutationResultState.TIMEOUT
            execution.timeout = TimeoutKind.TEST_TIMEOUT
            return

        if exit_code is None and test_result == "CRASHED":
            execution.mutation_result = MutationResultState.EXECUTION_ERROR
            execution.infrastructure_failure = (
                InfrastructureFailureKind.SUBPROCESS_CRASH
            )
            return

        if exit_code is None:
            execution.mutation_result = MutationResultState.NOT_EXECUTED
            return

        # Map pytest exit code to canonical state.
        # pytest: 0=all passed, 1=some failed, 2=interrupted, 3=internal error
        if exit_code == 0:
            execution.mutation_result = MutationResultState.SURVIVED
        elif exit_code == 1:
            execution.mutation_result = MutationResultState.KILLED
        elif exit_code == 2:
            execution.mutation_result = MutationResultState.EXECUTION_ERROR
            execution.infrastructure_failure = InfrastructureFailureKind.SIGNAL_KILL
        elif exit_code == 3:
            # pytest internal error — treat as kill (mutation caused failure)
            execution.mutation_result = MutationResultState.KILLED
        else:
            execution.mutation_result = MutationResultState.EXECUTION_ERROR
            execution.infrastructure_failure = InfrastructureFailureKind.UNKNOWN

    def _load_candidates(self, workspace: Path) -> list[MutationCandidate]:
        """Load candidates from workspace."""
        candidates_dir = workspace / "candidates"
        if not candidates_dir.exists():
            return []
        candidates = []
        for f in sorted(candidates_dir.glob("*.json")):
            try:
                candidates.append(
                    MutationCandidate.from_dict(json.loads(f.read_text()))
                )
            except Exception:
                continue
        return candidates

    def cancel(self, campaign: MutationCampaign, workspace: Path) -> None:
        """Cancel running campaign: mark remaining candidates as CANCELLED."""
        exec_dir = workspace / "executions"
        if not exec_dir.exists():
            return
        now = datetime.now(UTC).isoformat()
        for exec_file in exec_dir.glob("*.json"):
            try:
                data = json.loads(exec_file.read_text())
                if data.get("mutation_result") == MutationResultState.UNKNOWN.value:
                    data["mutation_result"] = MutationResultState.CANCELLED.value
                    data["end_time"] = now
                    exec_file.write_text(json.dumps(data, indent=2) + "\n")
            except Exception:
                continue

    def cleanup(self, campaign: MutationCampaign, workspace: Path) -> None:
        """Clean up workspace artifacts (keep evidence)."""
        # Keep executions/ and evidence/ for audit.
        # Remove temporary mutant source copies.
        mutants_dir = workspace / "mutants"
        if mutants_dir.exists():
            shutil.rmtree(mutants_dir, ignore_errors=True)
        source_dir = workspace / "source"
        if source_dir.exists():
            shutil.rmtree(source_dir, ignore_errors=True)


def create_adapter() -> MutmutAdapter:
    return MutmutAdapter()


__all__ = [
    "MutmutAdapter",
    "create_adapter",
]
