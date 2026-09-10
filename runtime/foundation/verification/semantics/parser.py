"""
M9-C57 — Semantic failure parser.

Extracts structured information from FinancialInvariantViolation traceback
strings for use in diagnostic reporting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SemanticFailure:
    """Parsed semantic failure from a test output."""

    invariant_id: str
    expected: str
    actual: str
    context: dict[str, Any]
    remediation: str


class SemanticFailureParser:
    """Parse FinancialInvariantViolation messages into structured data."""

    # Pattern matches the multi-line format produced by FinancialInvariantViolation
    _PATTERN = re.compile(
        r"Financial Invariant Violated: (?P<invariant_id>\S+)"
        r"\n\s+Invariant: (?P<description>.*)"
        r"\n\s+Expected: (?P<expected>.*)"
        r"\n\s+Actual: (?P<actual>.*)"
        r"(?:\n\s+Context: \{(?P<context>[^}]+)\})?"
        r"(?:\n\s+Remediation: (?P<remediation>.*))?",
        re.MULTILINE,
    )

    _CTX_PATTERN = re.compile(r"(\w+)\s*[=:]\s*([^,}]+)")

    @classmethod
    def parse(cls, message: str) -> SemanticFailure | None:
        """Parse a FinancialInvariantViolation message.

        Returns None if the message does not match the expected format.
        """
        m = cls._PATTERN.search(message)
        if not m:
            return None

        ctx_str = m.group("context") or ""
        context: dict[str, Any] = {}
        if ctx_str:
            for kv in cls._CTX_PATTERN.findall(ctx_str):
                key, val = kv
                val = val.strip()
                try:
                    context[key] = int(val)
                except ValueError:
                    try:
                        context[key] = float(val)
                    except ValueError:
                        context[key] = val

        return SemanticFailure(
            invariant_id=m.group("invariant_id"),
            expected=m.group("expected").strip(),
            actual=m.group("actual").strip(),
            context=context,
            remediation=(m.group("remediation") or "").strip(),
        )

    @classmethod
    def extract_from_traceback(cls, tb: str) -> list[SemanticFailure]:
        """Extract all semantic failures from a traceback string."""
        failures = []
        for m in cls._PATTERN.finditer(tb):
            ctx_str = m.group("context") or ""
            context: dict[str, Any] = {}
            if ctx_str:
                for kv in cls._CTX_PATTERN.findall(ctx_str):
                    key, val = kv
                    val = val.strip()
                    try:
                        context[key] = int(val)
                    except ValueError:
                        try:
                            context[key] = float(val)
                        except ValueError:
                            context[key] = val
            failures.append(
                SemanticFailure(
                    invariant_id=m.group("invariant_id"),
                    expected=m.group("expected").strip(),
                    actual=m.group("actual").strip(),
                    context=context,
                    remediation=(m.group("remediation") or "").strip(),
                )
            )
        return failures
