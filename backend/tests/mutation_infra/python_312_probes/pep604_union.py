# backend/tests/mutation_infra/python_312_probes/pep604_union.py
#
# M9-C45 L-ARCH-001 probe — PEP 604 X | Y union syntax (Python 3.10+).

from __future__ import annotations


def coerce(value: int | str | None) -> str:
    """Coerce a value (int|str|None) to a string."""
    if value is None:
        return "empty"
    return str(value)


def union_arg(x: int | float, y: int | float) -> int | float:
    """Return the larger of two int|float values."""
    return x if x > y else y