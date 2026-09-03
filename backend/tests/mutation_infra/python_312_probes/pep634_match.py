# backend/tests/mutation_infra/python_312_probes/pep634_match.py
#
# M9-C45 L-ARCH-001 probe — PEP 634 structural pattern matching (Python 3.10+).
#
# Hypothesis: mutmut 3.7.0 (libcst-based) generates mutations for `match`
# statement bodies (the arms) but may silently skip the structural pattern
# itself when the AST node shape diverges from cst's expectations.
#
# This module is a STANDALONE probe — not under src/ — so it must be
# importable as a top-level name (mutmut trampoline rejects src.* prefix).

from __future__ import annotations


def classify_with_match(value: int) -> str:
    """Return a label for the int using structural pattern matching."""
    match value:
        case 0:
            return "zero"
        case 1 | 2:
            return "small"
        case x if x > 100:
            return "large"
        case _:
            return "other"


def match_on_shape(point: tuple[int, int]) -> str:
    """Pattern-match on tuple shape (sequence pattern)."""
    match point:
        case (0, 0):
            return "origin"
        case (x, 0):
            return f"x-axis-{x}"
        case (0, y):
            return f"y-axis-{y}"
        case (x, y):
            return f"point-{x}-{y}"
        case _:
            return "unknown"