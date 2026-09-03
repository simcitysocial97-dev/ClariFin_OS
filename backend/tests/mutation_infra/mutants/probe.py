# backend/tests/mutation_infra/probe.py
#
# M9-C42.5 — Clean-room mutation smoke fixture.
#
# Deliberately trivial code used ONLY to validate the mutation-testing
# infrastructure (not domain coverage). It is designed so a single `mutmut run`
# reliably produces three distinct classifications:
#
#   * killed     — a mutant the tests definitely catch,
#   * survived   — a mutant the tests do NOT catch (proves survivor detection),
#   * no tests   — a function with no associated test (proves no-test detection).
#
# The module MUST be importable as a top-level name (`probe`) — mutmut's
# trampoline rejects module names that start with a package prefix such as
# `src.`. Keeping the file flat in mutation_infra/ satisfies that contract.

from __future__ import annotations


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_mutation_probe__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_mutation_probe__mutmut)
def mutation_probe(value: int) -> int:
    """Return value+1 when value exceeds 10, else value unchanged."""
    if value > 10:
        return value + 1
    return value


def x_mutation_probe__mutmut_orig(value: int) -> int:
    """Return value+1 when value exceeds 10, else value unchanged."""
    if value > 10:
        return value + 1
    return value


def x_mutation_probe__mutmut_1(value: int) -> int:
    """Return value+1 when value exceeds 10, else value unchanged."""
    if value >= 10:
        return value + 1
    return value


def x_mutation_probe__mutmut_2(value: int) -> int:
    """Return value+1 when value exceeds 10, else value unchanged."""
    if value > 11:
        return value + 1
    return value


def x_mutation_probe__mutmut_3(value: int) -> int:
    """Return value+1 when value exceeds 10, else value unchanged."""
    if value > 10:
        return value - 1
    return value


def x_mutation_probe__mutmut_4(value: int) -> int:
    """Return value+1 when value exceeds 10, else value unchanged."""
    if value > 10:
        return value + 2
    return value

mutants_x_mutation_probe__mutmut['_mutmut_orig'] = x_mutation_probe__mutmut_orig # type: ignore # mutmut generated
mutants_x_mutation_probe__mutmut['x_mutation_probe__mutmut_1'] = x_mutation_probe__mutmut_1 # type: ignore # mutmut generated
mutants_x_mutation_probe__mutmut['x_mutation_probe__mutmut_2'] = x_mutation_probe__mutmut_2 # type: ignore # mutmut generated
mutants_x_mutation_probe__mutmut['x_mutation_probe__mutmut_3'] = x_mutation_probe__mutmut_3 # type: ignore # mutmut generated
mutants_x_mutation_probe__mutmut['x_mutation_probe__mutmut_4'] = x_mutation_probe__mutmut_4 # type: ignore # mutmut generated
mutants_x_unused_probe__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_unused_probe__mutmut)
def unused_probe(value: int) -> int:
    """Intentionally has NO test — exercises the 'no tests' classification."""
    return value * 2


def x_unused_probe__mutmut_orig(value: int) -> int:
    """Intentionally has NO test — exercises the 'no tests' classification."""
    return value * 2


def x_unused_probe__mutmut_1(value: int) -> int:
    """Intentionally has NO test — exercises the 'no tests' classification."""
    return value / 2


def x_unused_probe__mutmut_2(value: int) -> int:
    """Intentionally has NO test — exercises the 'no tests' classification."""
    return value * 3

mutants_x_unused_probe__mutmut['_mutmut_orig'] = x_unused_probe__mutmut_orig # type: ignore # mutmut generated
mutants_x_unused_probe__mutmut['x_unused_probe__mutmut_1'] = x_unused_probe__mutmut_1 # type: ignore # mutmut generated
mutants_x_unused_probe__mutmut['x_unused_probe__mutmut_2'] = x_unused_probe__mutmut_2 # type: ignore # mutmut generated
