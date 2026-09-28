# backend/tests/mutation_infra/python_312_probes/control_probe.py
#
# M9-C45 L-ARCH-001 probe — control module using ONLY Python 3.9 syntax.
#
# This establishes the BASELINE: mutmut 3.7.0 generates X mutations on
# idiomatic Python 3.9 code. Comparison vs the 3.10+/3.11+/3.12+ probes
# quantifies the syntax-skip gap.

from __future__ import annotations


def classify(value: int) -> str:
    """Return a label for the int using classic if/elif chain."""
    if value == 0:
        return "zero"
    elif value == 1 or value == 2:
        return "small"
    elif value > 100:
        return "large"
    else:
        return "other"


def coerce_baseline(value: int | None) -> str:
    """Coerce using classic None-check semantics."""
    if value is None:
        return "empty"
    return str(value)
