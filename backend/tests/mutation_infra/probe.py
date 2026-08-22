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


def mutation_probe(value: int) -> int:
    """Return value+1 when value exceeds 10, else value unchanged."""
    if value > 10:
        return value + 1
    return value


def unused_probe(value: int) -> int:
    """Intentionally has NO test — exercises the 'no tests' classification."""
    return value * 2
