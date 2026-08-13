"""
M9-C3 failure-report contract.

Helpers that turn a raw :class:`ExecutionResult` into an *actionable* failure
description: a stable :class:`FailureClassification`, a structured test failure
summary, the first/root failing node, and a safe (bounded) diagnostic excerpt.

The runtime never invents a classification it cannot support. When the cause is
not attributable from the available evidence, the unit is classified as
``UNKNOWN_FAILURE`` and the raw diagnostic text is preserved verbatim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.foundation.verification.models import (
    ExecutionResult,
    FailureClassification,
    VerificationStatus,
)

# pytest short-summary line, e.g. "1 failed, 65 passed" or "2 failed, 3 error".
_PYTEST_SUMMARY_RE = re.compile(
    r"(?:\d+\s+(?:failed|passed|error|skipped|xfailed|xpassed|"
    r"warning)\b[, ]*)+",
    re.IGNORECASE,
)

# A failing node id line under "==== FAILURES ====", e.g.
# "____ tests/x/test_foo.py::test_bar ____".
_PYTEST_NODE_RE = re.compile(r"_{4,}\s+(?P<node>[\w./:\[\]'\"-]+)\s+_{4,}")


def _pytest_failed_test_ids(output: str) -> list[str]:
    """Return the failing pytest node ids visible in the captured output."""
    ids: list[str] = []
    # First preference: the "short test summary info" section, which lists every
    # failing node id on its own line, e.g. "FAILED x.py::t".
    short = output.split("short test summary info")
    body = short[-1] if len(short) > 1 else output
    for line in body.splitlines():
        line = line.strip()
        m = re.match(r"(?:FAILED|ERROR)\s+(?P<node>\S+)", line)
        if m:
            ids.append(m.group("node"))
    if ids:
        return ids
    # Fallback: the underline-delimited "____ node ____" blocks.
    return _PYTEST_NODE_RE.findall(output)


def _count_pytest_failures(summary_text: str) -> int | None:
    """Extract the integer count of failed tests from a pytest summary string."""
    total = 0
    found = False
    for m in re.finditer(r"(?P<n>\d+)\s+failed\b", summary_text, re.IGNORECASE):
        total += int(m.group("n"))
        found = True
    return total if found else None


def _pytest_summary_line(output: str) -> str | None:
    """Return the first concise pytest summary line, if present."""
    for line in output.splitlines():
        if _PYTEST_SUMMARY_RE.search(line):
            return line.strip()
    return None


def is_pytest_command(command: str) -> bool:
    return "pytest" in command


def is_import_failure(output: str) -> bool:
    return bool(
        re.search(
            r"(ModuleNotFoundError|ImportError|SyntaxError|"
            r"cannot import name|No module named)",
            output,
            re.IGNORECASE,
        )
    )


@dataclass(frozen=True, slots=True)
class FailureReport:
    """Actionable, bounded description of a failed verification unit."""

    classification: FailureClassification
    unit_id: str | None
    command: str
    exit_code: int | None
    failure_summary: str | None = None
    test_failure_count: int | None = None
    root_failure: str | None = None
    diagnostic: str | None = None
    evidence_path: str | None = None
    status: str = "failed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "unit_id": self.unit_id,
            "command": self.command,
            "exit_code": self.exit_code,
            "failure_summary": self.failure_summary,
            "test_failure_count": self.test_failure_count,
            "root_failure": self.root_failure,
            "diagnostic": self.diagnostic,
            "evidence_path": self.evidence_path,
            "status": self.status,
        }


def build_failure_report(result: ExecutionResult) -> FailureReport:
    """Build an actionable failure report from an :class:`ExecutionResult`.

    The output/error streams are truncated to a bounded excerpt so the CLI stays
    readable; the full evidence remains in the persisted artifact files.
    """
    if result.status != VerificationStatus.FAILED:
        raise ValueError("build_failure_report requires a FAILED result")

    stdout_text = _read_artifact(result.stdout_path)
    stderr_text = _read_artifact(result.stderr_path)
    combined = "\n".join(
        part for part in (result.error or "", stdout_text) if part
    )

    classification = result.classification
    # Honor an already-derived classification (preferred), otherwise infer from
    # the available evidence. The executor pre-fills TIMEOUT/ENVIRONMENT so we
    # only infer the test/import/command branches here.
    if classification == FailureClassification.UNKNOWN_FAILURE:
        classification = _infer_classification(
            command=result.command,
            combined=combined + "\n" + stderr_text,
        )

    summary = _pytest_summary_line(combined)
    test_failure_count = _count_pytest_failures(summary) if summary else None
    root_failure = None
    if test_failure_count is None or test_failure_count > 0:
        failed_ids = _pytest_failed_test_ids(combined)
        if failed_ids:
            root_failure = failed_ids[0]

    diagnostic = _bounded_diagnostic(combined + "\n" + stderr_text)

    return FailureReport(
        classification=classification,
        unit_id=result.unit_id,
        command=result.command,
        exit_code=result.exit_code,
        failure_summary=result.failure_summary or summary,
        test_failure_count=result.test_failure_count
        if result.test_failure_count is not None
        else test_failure_count,
        root_failure=result.root_failure or root_failure,
        diagnostic=diagnostic,
        evidence_path=result.stderr_path or result.stdout_path or None,
        status=result.status.value,
    )


def _infer_classification(
    command: str, combined: str
) -> FailureClassification:
    if is_pytest_command(command) or "pytest" in combined.lower():
        if is_import_failure(combined):
            return FailureClassification.IMPORT_FAILURE
        return FailureClassification.TEST_FAILURE
    if is_import_failure(combined) and ("python" in command or "pytest" in command):
        return FailureClassification.IMPORT_FAILURE
    return FailureClassification.COMMAND_FAILURE


def _read_artifact(path: str | None) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _bounded_diagnostic(text: str, limit: int = 1200) -> str | None:
    text = (text or "").strip()
    if not text:
        return None
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text
