# backend/tests/mutation_trust/canary/mutation_canary.py
#
# M9-C71 — Mutation-measurement canary (real repository code shape).
#
# WHY THIS FILE EXISTS
# --------------------
# A mutation campaign is trustworthy only if the harness itself can be shown to
# distinguish a mutant that was killed from a mutant that survived from a mutant
# that was never executed at all. mutmut's own summary cannot make that
# distinction: it reports "survived" identically for a mutant the suite observed
# and for a mutant the suite never reached. This file makes all three
# distinguishable by construction, so the harness can be certified BEFORE any
# score is interpreted.
#
# The code deliberately mirrors production shapes used across the repository
# (a dataclass value object, a classmethod constructor, an early-return guard,
# a dictionary default) so the canary exercises the same mutation operators and
# the same dispatch paths the real campaign uses — including the `src.<package>`
# import form and the `@classmethod` trampoline branch that were both proven
# defective in C71.
#
# THE FOUR REQUIRED PROOFS
# ------------------------
#   1. KNOWN_KILL_MUTANT   — a mutant the test suite must kill.
#      `known_kill_value(20)` returns 21. mutmut's `+1 -> -1` operator produces
#      19, and the test asserts 21, so the mutant is killed.
#
#   2. KNOWN_SURVIVOR_MUTANT — a mutant the test suite must NOT kill.
#      `known_survivor_boundary(0)` returns 0 via the `value > 0` guard. mutmut
#      mutates that comparison, but with value == 0 every operator variant of
#      `>` returns the same result, so the mutant survives *and is genuinely
#      equivalent* — the test observes exactly the same output.
#
#   3. KNOWN_REACHED_LOCATION — a mutation location the tests must execute.
#      `known_reached_guard` is called by the suite, so its mutants are executed.
#
#   4. KNOWN_UNREACHED_LOCATION — a mutation location the tests must NOT execute.
#      `known_unreached_helper` is never called, so mutmut classifies its mutants
#      as `no tests` and never forks a test process for them. This is the proof
#      that a reported survivor was not merely an unreached location being
#      silently counted as a legitimate survivor.

from __future__ import annotations

from dataclasses import dataclass

# ── 1. KNOWN_KILL_MUTANT ─────────────────────────────────────────────────────
# The test asserts the exact value, so mutmut's arithmetic mutation of `+ 1`
# is observable and the mutant is killed. A survivor here would mean the mutant
# was never dispatched, i.e. the harness is broken.


def known_kill_value(value: int) -> int:
    """Return ``value + 1`` — a boundary the canary test asserts exactly."""
    if value > 0:
        return value + 1
    return value


# ── 2. KNOWN_SURVIVOR_MUTANT ────────────────────────────────────────────────
# The canary test calls this ONLY with a value that does not satisfy the guard,
# so every operator variant of the comparison produces an identical observable
# result. The mutant survives for a *behavioural* reason, which is the property
# Phase 7 must be able to establish independently of survival.


def known_survivor_boundary(value: int) -> int:
    """Return ``0`` for a non-positive value regardless of the exact operator."""
    if value > 0:
        return value
    return 0


# ── 3. KNOWN_REACHED_LOCATION ───────────────────────────────────────────────
# Called by the canary test, so its mutants are genuinely executed.


def known_reached_guard(value: int) -> str:
    """Return a label; the early return is reached by the canary test."""
    if value <= 0:
        return "non_positive"
    return "positive"


# ── 4. KNOWN_UNREACHED_LOCATION ─────────────────────────────────────────────
# Never called by the canary test. mutmut must classify these mutants as
# `no tests`, and the Phase 4 sentinel must never observe them executing.


def known_unreached_helper(value: int) -> int:
    """Intentionally unreachable by the canary suite — proves `no tests`."""
    if value < 0:
        raise ValueError("negative value is not accepted")
    return value * 2


# ── Real repository shape: dataclass value object + @classmethod ctor ───────
# The `@classmethod` trampoline branch was the second proven toolchain defect
# (the CLEAN test run crashed with
# "Money.x__from_rupees__mutmut_orig() takes 2 positional arguments but 3 were
# given"). Including a classmethod here means the canary FAILS LOUDLY if that
# regression ever returns, instead of silently degrading the whole shard.


@dataclass(frozen=True)
class CanaryAmount:
    """Minimal frozen value object mirroring the Money shape in the repository."""

    _rupees: int

    @classmethod
    def from_rupees(cls, rupees: int) -> CanaryAmount:
        """Construct from rupees — exercises the classmethod trampoline branch."""
        return cls(rupees)

    @property
    def rupees(self) -> int:
        return self._rupees

    def doubled(self) -> int:
        """Arithmetic the canary test asserts exactly, so mutants are killed."""
        return self._rupees * 2
