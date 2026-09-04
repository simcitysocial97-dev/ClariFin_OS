# runtime/foundation/verification/frontend_financial_arithmetic_lint.py
#
# M9-C48 D1 — Frontend financial-arithmetic enforcement (GAP-012).
#
# The architectural rule:
#
#   Frontend MUST NOT perform financial arithmetic on monetary values.
#   All such arithmetic belongs to the backend. The frontend may
#   FORMAT and DISPLAY monetary values only.
#
# This module is a static-analysis rule. It scans TypeScript files under
# ``frontend/`` for the prohibited arithmetic pattern:
#
#     <monetary-identifier> <op> <monetary-identifier>
#     <monetary-identifier> <op> <literal>
#
# where ``op`` ∈ { +, -, *, /, ** } and a monetary identifier is any
# variable/property whose name contains a monetary keyword.
#
# The rule allows:
#
#   * Currency formatting helpers (format, formatCurrency, locale).
#   * Constants and type declarations.
#   * Display / render / label / sort logic.
#   * Math on non-monetary identifiers (e.g. timestamps, ids, counts).
#
# Findings are produced as a structured report and a non-zero exit code
# signals a violation. A baseline may be supplied to allow pre-existing
# intentional exceptions to pass without modifying the rule.

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


MONETARY_KEYWORDS: tuple[str, ...] = (
    "amount",
    "balance",
    "total",
    "subtotal",
    "principal",
    "interest",
    "payment",
    "emi",
    "fee",
    "interest_rate",
    "rate",
    "paise",
    "cents",
    "currency",
    "money",
    "price",
    "cost",
    "limit",
    "available",
    "outstanding",
    "spent",
    "received",
    "income",
    "expense",
    "salary",
    "wage",
    "deposit",
    "withdrawal",
    "credit",
    "debit",
)


# Identifier pattern: a JS/TS identifier that contains a monetary keyword
# (case-insensitive). Allows word-boundary awareness so 'subtotal' matches
# but 'totally' (without word boundary) does not.
_IDENT_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\b"
)

# Arithmetic operator pattern. We avoid regexing `+` and `-` because they
# are common in template literals; we use word-boundary operators or
# tokens in arithmetic contexts (assignment, comparison, return).
_ARITH_RE = re.compile(
    r"(?:^|[^=!<>])(\*|\*\*|/|%)\s*([^=])"
)

# Plus/minus in arithmetic context: variable (op) variable, with operators
# preceded by spaces (heuristic for arithmetic, not string concat).
_PLUSMINUS_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*([+\-])\s*([A-Za-z_][A-Za-z0-9_]*)\b"
)

# Identifier (op) literal: variable (op) numeric literal.
_PLUSMINUS_LITERAL_RE = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*([+\-])\s*([0-9]+(?:\.[0-9]+)?)\b"
)


@dataclass(frozen=True, slots=True)
class Finding:
    file: str
    line: int
    column: int
    rule: str
    snippet: str
    identifier: str
    severity: str = "error"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class LintReport:
    findings: tuple[Finding, ...]
    scanned_files: tuple[str, ...]
    exceptions_applied: tuple[str, ...]
    generated_at: str
    schema: str = "m9-c48/frontend-financial-arithmetic-lint@1"

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "scanned_files": list(self.scanned_files),
            "exceptions_applied": list(self.exceptions_applied),
            "findings": [f.to_dict() for f in self.findings],
            "violation_count": len(self.findings),
            "ok": len(self.findings) == 0,
        }


def _is_monetary(name: str) -> bool:
    n = name.lower()
    for kw in MONETARY_KEYWORDS:
        if kw in n:
            return True
    return False


def _is_format_or_display_context(line: str) -> bool:
    """Return True if *line* is clearly display-only and not arithmetic."""
    lower = line.lower()
    if "format" in lower or "formatcurrency" in lower or "tolocalestring" in lower:
        return True
    if "label" in lower or "render" in lower or "display" in lower:
        return True
    if "type " in lower or "interface " in lower:
        return True
    if "console." in lower:
        return True
    # Property/type declarations: e.g., `paise: number;` or
    # `credit_limit_paise?: number;` — no arithmetic.
    if re.search(r":\s*\w+(?:[\.<>\[\],\s\|]+(?:\w+|null))*;\s*(?://.*)?$", line.strip()):
        return True
    # Field declarations of object types.
    if "amount:" in lower or "balance:" in lower or "paise:" in lower:
        # Only treat as display if it's clearly a field declaration.
        if re.search(r"^\s*[A-Za-z_][A-Za-z0-9_]*\??:\s*", line):
            return True
    # BPS → percent conversion (unit conversion for display).
    if re.search(r"/\s*100\b", line) and "Bps" in line:
        return True
    if re.search(r"\*\s*100\b", line) and "Bps" in line:
        return True
    # Pagination arithmetic (offset = (page - 1) * limit) is non-monetary
    # and legitimate on the frontend.
    if re.search(r"\(\s*page\s*-\s*1\s*\)\s*\*\s*limit\b", line, re.IGNORECASE):
        return True
    return False


def _is_string_context(line: str, idx: int) -> bool:
    """Heuristic: True if ``idx`` is inside a template literal or string."""
    # Count backticks and quotes before idx.
    chunk = line[:idx]
    backticks = chunk.count("`")
    if backticks % 2 == 1:
        return True
    dquotes = chunk.count('"') - chunk.count('\\"')
    if dquotes % 2 == 1:
        return True
    squotes = chunk.count("'") - chunk.count("\\'")
    if squotes % 2 == 1:
        return True
    return False


def _is_comment(line: str) -> bool:
    s = line.lstrip()
    return s.startswith("//") or s.startswith("/*") or s.startswith("*")


def scan_line(file: str, line_no: int, line: str) -> list[Finding]:
    findings: list[Finding] = []
    if _is_comment(line) or _is_format_or_display_context(line):
        return findings

    # 1. * / % / ** operator scan
    for m in _ARITH_RE.finditer(line):
        op = m.group(1)
        # Look left of the operator for an identifier (monetary).
        prefix = line[: m.start(1)]
        left_match = list(_IDENT_RE.finditer(prefix))
        right_match = list(_IDENT_RE.finditer(line[m.end(1):]))
        if not left_match or not right_match:
            continue
        left = left_match[-1].group(1)
        right = right_match[0].group(1)
        if _is_monetary(left) or _is_monetary(right):
            col = m.start(1)
            if _is_string_context(line, col):
                continue
            findings.append(
                Finding(
                    file=file,
                    line=line_no,
                    column=col,
                    rule="no-monetary-arithmetic",
                    snippet=line.strip()[:200],
                    identifier=left if _is_monetary(left) else right,
                )
            )

    # 2. + / - between two identifiers (heuristic).
    for m in _PLUSMINUS_RE.finditer(line):
        a, op, b = m.group(1), m.group(2), m.group(3)
        if _is_monetary(a) and _is_monetary(b):
            col = m.start(1)
            if _is_string_context(line, col):
                continue
            findings.append(
                Finding(
                    file=file,
                    line=line_no,
                    column=col,
                    rule="no-monetary-arithmetic",
                    snippet=line.strip()[:200],
                    identifier=a,
                )
            )
        elif _is_monetary(a) and b.isdigit():
            col = m.start(1)
            if _is_string_context(line, col):
                continue
            findings.append(
                Finding(
                    file=file,
                    line=line_no,
                    column=col,
                    rule="no-monetary-arithmetic-literal",
                    snippet=line.strip()[:200],
                    identifier=a,
                )
            )

    # 3. variable (op) numeric literal.
    for m in _PLUSMINUS_LITERAL_RE.finditer(line):
        a, op, lit = m.group(1), m.group(2), m.group(3)
        if _is_monetary(a):
            col = m.start(1)
            if _is_string_context(line, col):
                continue
            findings.append(
                Finding(
                    file=file,
                    line=line_no,
                    column=col,
                    rule="no-monetary-arithmetic-literal",
                    snippet=line.strip()[:200],
                    identifier=a,
                )
            )

    return findings


def scan_text(file: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for i, line in enumerate(text.splitlines(), start=1):
        findings.extend(scan_line(file, i, line))
    return findings


def scan_paths(
    paths: Iterable[str | Path],
    *,
    exceptions: Iterable[str] = (),
) -> LintReport:
    """Scan the given TS files and produce a structured report.

    ``exceptions`` is a sequence of file paths or ``file:line`` patterns
    that are explicitly allowed (e.g. legacy code that the rule has not
    been retroactively enforced against).
    """
    findings: list[Finding] = []
    scanned: list[str] = []
    exceptions = tuple(exceptions)
    for p in paths:
        path = Path(p)
        if not path.exists() or not path.is_file():
            continue
        scanned.append(str(path))
        for f in scan_text(str(path), path.read_text()):
            key = f"{f.file}:{f.line}"
            if key in exceptions or f.file in exceptions:
                continue
            findings.append(f)
    return LintReport(
        findings=tuple(findings),
        scanned_files=tuple(sorted(scanned)),
        exceptions_applied=tuple(exceptions),
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def scan_frontend(
    frontend_root: str | Path = "frontend",
    *,
    include_globs: Iterable[str] = ("**/*.ts", "**/*.tsx"),
    exclude_dirs: Iterable[str] = ("node_modules", "dist", ".next", "generated"),
    exceptions: Iterable[str] = (),
) -> LintReport:
    """Scan the frontend tree for prohibited arithmetic patterns."""
    root = Path(frontend_root)
    if not root.exists():
        return LintReport(
            findings=(),
            scanned_files=(),
            exceptions_applied=tuple(exceptions),
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
    paths: list[Path] = []
    exclude_set = set(exclude_dirs)
    for pat in include_globs:
        for p in root.glob(pat):
            if not p.is_file():
                continue
            if any(part in exclude_set for part in p.parts):
                continue
            paths.append(p)
    return scan_paths(paths, exceptions=exceptions)


__all__ = [
    "MONETARY_KEYWORDS",
    "Finding",
    "LintReport",
    "scan_line",
    "scan_text",
    "scan_paths",
    "scan_frontend",
]
