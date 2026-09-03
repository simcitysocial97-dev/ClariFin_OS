# backend/tests/mutation_infra/test_probe.py
#
# M9-C42.5 — Tests for the clean-room mutation smoke fixture.
#
# These tests exist to validate the mutation infrastructure, not to cover
# production behaviour. They are intentionally minimal:
#   * test_killed  — catches the `+1 -> -1` mutant,
#   * test_survive — does NOT catch the `> 10 -> >= 10` mutant (survivor),
#   * (unused_probe has no test — exercises the 'no tests' bucket).

from __future__ import annotations

from probe import mutation_probe


def test_killed() -> None:
    assert mutation_probe(20) == 21


def test_survive() -> None:
    assert mutation_probe(5) == 5
