# backend/tests/mutation_infra/python_312_probes/pep695_type_params.py
#
# M9-C45 L-ARCH-001 probe — PEP 695 generic syntax (Python 3.12+).
#
# Hypothesis: mutmut 3.7.0 may either (a) fail to parse this file at all
# (libcst pre-3.12 cannot represent TypeParameter nodes), or (b) parse
# it but generate 0 mutations because it cannot mutate the type-parameter
# block. Either case is a silent coverage gap.
#
# Tests below verify the FUNCTIONAL behavior — they do NOT depend on PEP 695
# syntax — so the test will pass regardless of whether mutmut can mutate it.
# The PROBE is the existence of zero mutations on this module.

from __future__ import annotations


class Box[T]:
    """Generic Box class using PEP 695 type-parameter syntax."""

    def __init__(self, inner: T) -> None:
        self.inner = inner

    def get(self) -> T:
        return self.inner


def first[T](items: list[T]) -> T | None:
    """PEP 695 generic function — returns first element or None."""
    if not items:
        return None
    return items[0]
