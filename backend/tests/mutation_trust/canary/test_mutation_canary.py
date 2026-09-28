# backend/tests/mutation_trust/canary/test_mutation_canary.py
#
# M9-C71 — Canary suite: asserts the exact known outcomes.
#
# The module under test is loaded by FILE PATH rather than by package import so
# the identical test file works in three contexts:
#
#   * as a plain suite over the pristine source (production-like),
#   * from inside mutmut's ``mutants/`` directory during the stats phase,
#   * from inside the forked mutant process during the mutation phase.
#
# mutmut runs pytest with cwd = ``mutants/``, so the pristine module is not
# importable by name there — only the generated mutant module is. Resolving the
# path explicitly is what makes the canary deterministic in all three contexts.
#
# The sentinel is likewise loaded by path: ``backend.tests`` is not an importable
# package in this repository (there is no ``backend/__init__.py``), so a normal
# import would work locally and fail inside the mutant fork.
#
# Each test calls ``sentinel.arm`` FIRST. That is what converts "the suite ran"
# into "this exact mutated implementation executed at this exact location" —
# the independent runtime signal Phase 2/4 require. The sentinel is a no-op
# outside a mutant fork, so the same file is a valid production-shaped suite.

from __future__ import annotations

import importlib.util
import os
import sys

_MODULE_STEM = "mutation_canary"


def _load_sibling(stem: str, alias: str):
    """Load a module from this directory, whichever copy is reachable.

    Looks beside the test file first, then under ``mutants/`` (mutmut's layout
    for also-copied files), so the same import works in all three run contexts.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, f"{stem}.py"),
        os.path.join("mutants", "tests", "mutation_trust", "canary", f"{stem}.py"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            spec = importlib.util.spec_from_file_location(alias, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[alias] = module
            spec.loader.exec_module(module)
            return module
    raise RuntimeError(f"module {stem!r} not found in any of: {candidates}")


def _load_module():
    """Load the pristine or mutated canary module, whichever is importable."""
    candidates = [
        os.path.join("src", "canary", f"{_MODULE_STEM}.py"),
        os.path.join("mutants", "src", "canary", f"{_MODULE_STEM}.py"),
    ]
    here = os.path.dirname(os.path.abspath(__file__))
    candidates += [os.path.join(here, f"{_MODULE_STEM}.py")]
    for path in candidates:
        if os.path.isfile(path):
            # The module MUST be registered under its canonical name. mutmut
            # refuses to run when the suite records trampoline hits under a
            # different module path than the source path implies — it cannot
            # then tell a real dispatch failure from a naming mismatch, and it
            # stops the campaign rather than measure the wrong thing.
            spec = importlib.util.spec_from_file_location(_MODULE_STEM, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[_MODULE_STEM] = module
            spec.loader.exec_module(module)
            return module
    raise RuntimeError(f"canary module not found in any of: {candidates}")


sentinel = _load_sibling("sentinel", "c71_mutation_sentinel")


def test_known_kill_mutant_is_killed() -> None:
    """Known-kill location: exact assertion, so mutants here are KILLED."""
    module = _load_module()
    sentinel.arm(module, module.known_kill_value)
    assert module.known_kill_value(20) == 21


def test_known_survivor_mutant_survives_for_behavioural_reason() -> None:
    """Known-survivor location: the guard never holds, so mutants are equivalent.

    Called only with a non-positive value, so every operator variant of ``>``
    yields the same observable result. The mutant survives because the
    behaviour is genuinely identical — not because the harness failed to
    dispatch it. Phase 7 re-establishes this independently of survival.
    """
    module = _load_module()
    sentinel.arm(module, module.known_survivor_boundary)
    assert module.known_survivor_boundary(0) == 0
    assert module.known_survivor_boundary(-5) == 0


def test_known_reached_location_is_reached() -> None:
    """Known-reached location: the suite must execute this function."""
    module = _load_module()
    sentinel.arm(module, module.known_reached_guard)
    assert module.known_reached_guard(1) == "positive"


def test_classmethod_shape_is_dispatchable() -> None:
    """The @classmethod trampoline branch must dispatch without a TypeError.

    This is the regression guard for C71 toolchain defect #2: with the defect
    present mutmut cannot even measure the CLEAN run of any classmethod-bearing
    module, and the failure surfaces as a shard with no summary at all.
    """
    module = _load_module()
    sentinel.arm(module, module.CanaryAmount.doubled)
    amount = module.CanaryAmount.from_rupees(21)
    assert amount.rupees == 21
    assert amount.doubled() == 42
