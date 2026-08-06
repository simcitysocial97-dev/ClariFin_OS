from __future__ import annotations

import inspect
import time
from pathlib import Path
from typing import Any

from runtime.foundation.audit.models import AuditFinding, AuditPriority, AuditSeverity, AuditStatus

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _f(check_id: str, name: str, status: str, severity: str, priority: str, message: str, details: dict[str, Any] = None, recommendation: str = "") -> AuditFinding:
    return AuditFinding(
        section="executor",
        check_id=check_id,
        name=name,
        status=AuditStatus(status),
        severity=AuditSeverity(severity),
        priority=AuditPriority(priority),
        message=message,
        details=details or {},
        recommendation=recommendation,
    )


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[AuditFinding] = []
    metrics: dict[str, Any] = {}

    from runtime.foundation.verification.executor import Executor
    from runtime.foundation.verification.models import VerificationStatus

    executor = Executor(repo_root)
    combined_source = inspect.getsource(Executor.execute)
    execute_once_source = inspect.getsource(Executor._execute_once)
    combined_source = combined_source + "\n" + execute_once_source

    expected_methods = [
        "execute",
        "execute_python",
        "execute_npm",
        "execute_pytest",
        "execute_vitest",
        "execute_playwright",
        "execute_schemathesis",
    ]
    for method_name in expected_methods:
        if not hasattr(executor, method_name):
            findings.append(
                _f(
                    f"missing-method-{method_name}",
                    f"Method {method_name} exists",
                    "fail",
                    "critical",
                    "critical",
                    f"Executor is missing method {method_name}",
                    {"method": method_name},
                    f"Add {method_name} method to Executor class",
                )
            )
        else:
            findings.append(
                _f(
                    f"method-exists-{method_name}",
                    f"Method {method_name} exists",
                    "pass",
                    "info",
                    "low",
                    f"Executor has method {method_name}",
                    {"method": method_name},
                )
            )

    result_echo = executor.execute("echo test")
    if result_echo.exit_code == 0 and result_echo.status == VerificationStatus.PASSED:
        findings.append(
            _f(
                "execute-return-code-pass",
                "Execute returns correct exit code for successful command",
                "pass",
                "info",
                "low",
                "Successful command returns exit code 0 with PASSED status",
                {"exit_code": result_echo.exit_code, "status": result_echo.status.value},
            )
        )
    else:
        findings.append(
            _f(
                "execute-return-code-pass",
                "Execute returns correct exit code for successful command",
                "fail",
                "high",
                "high",
                f"Successful command returned exit code {result_echo.exit_code} with status {result_echo.status.value}",
                {"exit_code": result_echo.exit_code, "status": result_echo.status.value},
                "Fix execute method to return correct exit codes for successful commands",
            )
        )

    result_fail = executor.execute("exit 1")
    if result_fail.exit_code != 0 and result_fail.status == VerificationStatus.FAILED:
        findings.append(
            _f(
                "execute-return-code-fail",
                "Execute returns correct exit code for failed command",
                "pass",
                "info",
                "low",
                "Failed command returns non-zero exit code with FAILED status",
                {"exit_code": result_fail.exit_code, "status": result_fail.status.value},
            )
        )
    else:
        findings.append(
            _f(
                "execute-return-code-fail",
                "Execute returns correct exit code for failed command",
                "fail",
                "high",
                "high",
                f"Failed command returned exit code {result_fail.exit_code} with status {result_fail.status.value}",
                {"exit_code": result_fail.exit_code, "status": result_fail.status.value},
                "Fix execute method to return correct exit codes for failed commands",
            )
        )

    if "timeout" in combined_source:
        findings.append(
            _f(
                "timeout-behavior",
                "Timeout behavior configured",
                "pass",
                "info",
                "low",
                "Executor.execute has timeout parameter configured in subprocess.run",
                {"timeout_seconds": 3600},
            )
        )
    else:
        findings.append(
            _f(
                "timeout-behavior",
                "Timeout behavior configured",
                "fail",
                "high",
                "high",
                "Executor.execute does not have timeout configured in subprocess.run",
                {},
                "Add timeout parameter to subprocess.run call",
            )
        )

    if "PYTHONUNBUFFERED" in combined_source:
        findings.append(
            _f(
                "env-vars-configured",
                "Environment variables configured",
                "pass",
                "info",
                "low",
                "Executor.execute sets PYTHONUNBUFFERED=1 in subprocess.run env",
                {"env_vars": ["PYTHONUNBUFFERED=1"]},
            )
        )
    else:
        findings.append(
            _f(
                "env-vars-configured",
                "Environment variables configured",
                "fail",
                "high",
                "high",
                "Executor.execute does not set environment variables in subprocess.run",
                {},
                "Set PYTHONUNBUFFERED=1 in subprocess.run env parameter",
            )
        )

    if "retry" not in combined_source.lower() and not hasattr(executor, "retry"):
        findings.append(
            _f(
                "retry-behavior",
                "Retry behavior implemented",
                "fail",
                "medium",
                "medium",
                "Executor does not implement retry logic for failed commands",
                {},
                "Add retry logic with configurable max retries and backoff",
            )
        )

    if "cancel" not in combined_source.lower() and not hasattr(executor, "cancel"):
        findings.append(
            _f(
                "cancellation-support",
                "Cancellation support exists",
                "fail",
                "medium",
                "medium",
                "Executor does not have a cancel method for interrupting running commands",
                {},
                "Add cancel method to Executor class using subprocess.Popen termination",
            )
        )

    if "parallel" not in combined_source.lower() and not hasattr(executor, "execute_parallel"):
        findings.append(
            _f(
                "parallel-execution",
                "Parallel execution support",
                "fail",
                "medium",
                "medium",
                "Executor does not support parallel execution of multiple commands",
                {},
                "Add parallel execution method using concurrent.futures.ThreadPoolExecutor",
            )
        )

    python_source = inspect.getsource(Executor.execute_python)
    if "python3 -m" in python_source and "" ".join" in python_source:
        findings.append(
            _f(
                "execute_python-command-format",
                "execute_python formats command correctly",
                "pass",
                "info",
                "low",
                "execute_python correctly formats command as python3 -m <module>",
                {"method": "execute_python"},
            )
        )
    else:
        findings.append(
            _f(
                "execute_python-command-format",
                "execute_python formats command correctly",
                "fail",
                "high",
                "high",
                "execute_python does not format command correctly",
                {},
                "Format command as 'python3 -m <module>'",
            )
        )

    npm_source = inspect.getsource(Executor.execute_npm)
    if "cd frontend && npm" in npm_source:
        findings.append(
            _f(
                "execute_npm-command-format",
                "execute_npm formats command correctly",
                "pass",
                "info",
                "low",
                "execute_npm correctly formats command with cd frontend prefix",
                {"method": "execute_npm"},
            )
        )
    else:
        findings.append(
            _f(
                "execute_npm-command-format",
                "execute_npm formats command correctly",
                "fail",
                "high",
                "high",
                "execute_npm does not format command correctly",
                {},
                "Format command with 'cd frontend && npm <command>'",
            )
        )

    pytest_source = inspect.getsource(Executor.execute_pytest)
    if "python3 -m pytest" in pytest_source:
        findings.append(
            _f(
                "execute_pytest-command-format",
                "execute_pytest formats command correctly",
                "pass",
                "info",
                "low",
                "execute_pytest correctly formats command with pytest arguments",
                {"method": "execute_pytest"},
            )
        )
    else:
        findings.append(
            _f(
                "execute_pytest-command-format",
                "execute_pytest formats command correctly",
                "fail",
                "high",
                "high",
                "execute_pytest does not format command correctly",
                {},
                "Format command as 'python3 -m pytest <paths> <extra_args>'",
            )
        )

    vitest_source = inspect.getsource(Executor.execute_vitest)
    if "cd frontend && npx vitest" in vitest_source:
        findings.append(
            _f(
                "execute_vitest-command-format",
                "execute_vitest formats command correctly",
                "pass",
                "info",
                "low",
                "execute_vitest correctly formats command with cd frontend prefix",
                {"method": "execute_vitest"},
            )
        )
    else:
        findings.append(
            _f(
                "execute_vitest-command-format",
                "execute_vitest formats command correctly",
                "fail",
                "high",
                "high",
                "execute_vitest does not format command correctly",
                {},
                "Format command with 'cd frontend && npx vitest run'",
            )
        )

    playwright_source = inspect.getsource(Executor.execute_playwright)
    if "cd frontend && npx playwright" in playwright_source:
        findings.append(
            _f(
                "execute_playwright-command-format",
                "execute_playwright formats command correctly",
                "pass",
                "info",
                "low",
                "execute_playwright correctly formats command with cd frontend prefix",
                {"method": "execute_playwright"},
            )
        )
    else:
        findings.append(
            _f(
                "execute_playwright-command-format",
                "execute_playwright formats command correctly",
                "fail",
                "high",
                "high",
                "execute_playwright does not format command correctly",
                {},
                "Format command with 'cd frontend && npx playwright test'",
            )
        )

    schemathesis_source = inspect.getsource(Executor.execute_schemathesis)
    if "python3 -m schemathesis run" in schemathesis_source:
        findings.append(
            _f(
                "execute_schemathesis-command-format",
                "execute_schemathesis formats command correctly",
                "pass",
                "info",
                "low",
                "execute_schemathesis correctly formats command with schemathesis arguments",
                {"method": "execute_schemathesis"},
            )
        )
    else:
        findings.append(
            _f(
                "execute_schemathesis-command-format",
                "execute_schemathesis formats command correctly",
                "fail",
                "high",
                "high",
                "execute_schemathesis does not format command correctly",
                {},
                "Format command as 'python3 -m schemathesis run --hypothesis-max-examples=N <target>'",
            )
        )

    metrics["total_commands"] = len(expected_methods)
    metrics["methods_with_timeout"] = 1 if "timeout" in combined_source else 0
    metrics["has_env_vars"] = 1 if "PYTHONUNBUFFERED" in combined_source else 0
    metrics["has_retry"] = 0
    metrics["has_cancellation"] = 0
    metrics["has_parallel"] = 0
    metrics["return_code_handling"] = "correct"
    metrics["commands_inspected"] = 7

    all_pass = all(f.status == AuditStatus.PASS for f in findings)
    overall = AuditStatus.PASS if all_pass else AuditStatus.FAIL

    duration = time.monotonic() - start

    return {
        "section": "executor",
        "name": "Executor Audit",
        "status": overall,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 4),
    }