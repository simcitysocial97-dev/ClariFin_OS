# runtime/foundation/verification/test_quality.py
#
# M9-C48 F2 — Test Quality Sampling & Classification (GAP-017).
#
# Tests are not all equal. The purpose of this module is to classify
# tests across the important verification surfaces into one of the
# following quality categories:
#
#   EXECUTION_ONLY        — invokes code but asserts nothing meaningful.
#   WEAK_ASSERTION        — asserts on trivial properties (truthy, len>0).
#   BEHAVIORAL            — asserts on observable behaviour of the SUT.
#   INVARIANT             — asserts on a system invariant.
#   PROPERTY              — property-based (parametrised over many inputs).
#   CONTRACT              — asserts on API / schema contract.
#   INTEGRATION           — exercises multiple components together.
#   E2E                   — end-to-end across the stack.
#   GOLDEN                — snapshot / golden regression.
#   MUTATION_SENSITIVE    — kills known mutants (verified).
#   DIAGNOSTIC            — produces diagnostic output; not a gate.
#   FALSE_POSITIVE_GUARD  — protects against false-positive passes.
#
# This module is heuristic, not perfect. It samples test files in
# important surfaces and classifies them by structural markers. The
# purpose is NOT to maximize the count of any category but to determine
# whether tests actually DISTINGUISH incorrect behaviour.
#
# Integration point: ``classify_tests`` consumes a list of test file
# paths and produces a per-file classification report. The aggregated
# report is persisted as evidence.

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


QUALITY_CATEGORIES: tuple[str, ...] = (
    "EXECUTION_ONLY",
    "WEAK_ASSERTION",
    "BEHAVIORAL",
    "INVARIANT",
    "PROPERTY",
    "CONTRACT",
    "INTEGRATION",
    "E2E",
    "GOLDEN",
    "MUTATION_SENSITIVE",
    "DIAGNOSTIC",
    "FALSE_POSITIVE_GUARD",
)


@dataclass(frozen=True, slots=True)
class TestClassification:
    file: str
    primary_category: str
    secondary_categories: tuple[str, ...]
    assert_count: int
    parametrize_count: int
    is_e2e: bool
    is_golden: bool
    rationale: str

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "primary_category": self.primary_category,
            "secondary_categories": list(self.secondary_categories),
            "assert_count": self.assert_count,
            "parametrize_count": self.parametrize_count,
            "is_e2e": self.is_e2e,
            "is_golden": self.is_golden,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class QualityReport:
    classifications: tuple[TestClassification, ...]
    summary: dict[str, int]
    generated_at: str
    schema: str = "m9-c48/test-quality@1"

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "total_files": len(self.classifications),
            "classifications": [c.to_dict() for c in self.classifications],
        }


# Heuristics (regex on file contents).
_RE_ASSERT = re.compile(r"^\s*assert\b", re.MULTILINE)
_RE_PARAMETRIZE = re.compile(r"@pytest\.mark\.parametrize|@given\b")
_RE_E2E = re.compile(r"\b(e2e|playwright|cypress|page\.goto)\b", re.IGNORECASE)
_RE_GOLDEN = re.compile(r"\b(golden|regression|snapshot|baseline)\b", re.IGNORECASE)
_RE_PROPERTY = re.compile(r"@property|@given|hypothesis\.")
_RE_CONTRACT = re.compile(r"\b(contract|schema|dto|api_schema)\b", re.IGNORECASE)
_RE_INTEGRATION = re.compile(r"\bintegration\b|\bacceptance\b", re.IGNORECASE)
_RE_FALSE_POSITIVE = re.compile(
    r"(?:\b|_)(?:guard|invariant|never|always|forbid|prohibit|must|forbidden)(?:\b|_)"
)
_RE_DIAGNOSTIC = re.compile(r"\b(diagnostic|skip|xfail|debug)\b", re.IGNORECASE)
# Weak assertion pattern: asserts whose entire right side is a literal
# or trivial comparison (e.g. assert True / assert 1 / assert "x").
_RE_WEAK_ASSERT = re.compile(
    r"assert\s+(?:True|False|None|\d+(?:\.\d+)?|[\"'][^\"']*[\"'])\s*(?:,|$)",
    re.IGNORECASE,
)
_RE_MUTATION_SENSITIVE = re.compile(
    r"\b(mutant|mutation|mutmut)\b", re.IGNORECASE
)


def classify_test_file(path: str | Path) -> TestClassification:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return TestClassification(
            file=str(path),
            primary_category="DIAGNOSTIC",
            secondary_categories=(),
            assert_count=0,
            parametrize_count=0,
            is_e2e=False,
            is_golden=False,
            rationale="file not found",
        )
    text = p.read_text()
    assert_count = len(_RE_ASSERT.findall(text))
    param_count = len(_RE_PARAMETRIZE.findall(text))
    is_e2e = bool(_RE_E2E.search(text) or "e2e" in p.parts or "playwright" in str(path))
    is_golden = bool(_RE_GOLDEN.search(text) or "golden" in p.parts)

    secondary: list[str] = []
    if param_count > 0:
        secondary.append("PROPERTY")
    if _RE_CONTRACT.search(text):
        secondary.append("CONTRACT")
    if _RE_INTEGRATION.search(text):
        secondary.append("INTEGRATION")
    if _RE_FALSE_POSITIVE.search(text):
        secondary.append("FALSE_POSITIVE_GUARD")
    if _RE_MUTATION_SENSITIVE.search(text):
        secondary.append("MUTATION_SENSITIVE")
    if is_e2e:
        secondary.append("E2E")
    if is_golden:
        secondary.append("GOLDEN")

    # Determine primary.
    if assert_count == 0:
        primary = "EXECUTION_ONLY"
    elif is_e2e:
        primary = "E2E"
    elif is_golden:
        primary = "GOLDEN"
    elif "PROPERTY" in secondary:
        primary = "PROPERTY"
    elif "CONTRACT" in secondary:
        primary = "CONTRACT"
    elif "INTEGRATION" in secondary:
        primary = "INTEGRATION"
    elif assert_count <= 1 and len(_RE_WEAK_ASSERT.findall(text)) > 0:
        primary = "WEAK_ASSERTION"
    elif _RE_FALSE_POSITIVE.search(text) and assert_count >= 2:
        primary = "INVARIANT"
    else:
        primary = "BEHAVIORAL"

    rationale = (
        f"asserts={assert_count} param={param_count} e2e={is_e2e} golden={is_golden}"
    )
    return TestClassification(
        file=str(path),
        primary_category=primary,
        secondary_categories=tuple(secondary),
        assert_count=assert_count,
        parametrize_count=param_count,
        is_e2e=is_e2e,
        is_golden=is_golden,
        rationale=rationale,
    )


def sample_paths(
    *,
    backend_tests: str | Path = "backend/tests",
    frontend_tests: str | Path = "frontend/__tests__",
    max_files: int = 50,
) -> list[str]:
    """Sample test files across the important verification surfaces."""
    paths: list[str] = []
    for root in (backend_tests, frontend_tests):
        rp = Path(root)
        if not rp.exists():
            continue
        for p in sorted(rp.glob("**/*.py")):
            paths.append(str(p))
            if len(paths) >= max_files:
                return paths
    return paths


def classify_tests(paths: Iterable[str | Path] | None = None) -> QualityReport:
    if paths is None:
        paths = sample_paths()
    classifications = tuple(classify_test_file(p) for p in paths)
    summary: dict[str, int] = Counter()
    for c in classifications:
        summary[c.primary_category] += 1
    return QualityReport(
        classifications=classifications,
        summary=dict(summary),
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


__all__ = [
    "QUALITY_CATEGORIES",
    "TestClassification",
    "QualityReport",
    "classify_test_file",
    "sample_paths",
    "classify_tests",
]
