"""Thin root conftest — pytest_plugins loader and backward-compatible re-exports.

All fixtures, markers, and configuration have been moved into modular
plugins under ``tests/fixtures/``. This file exists solely to:

1. Register the fixture plugins with pytest.
2. Preserve legacy import paths for tests that import symbols directly
   from ``tests.conftest`` (see backward-compatibility notes below).
3. Provide mutmut 3.x compatibility (see ``_shim_mutmut_src_namespace``).

Backward-compatible re-exports
-------------------------------
The following symbols are imported here so that existing code such as::

    from tests.conftest import make_transaction

continues to work without modification.
"""

from __future__ import annotations

# ============================================================
# mutmut 3.x compatibility shim — DO NOT REMOVE
# ============================================================
# mutmut 3.x's trampoline guard rejects module names starting with `src.`:
#     assert not name.startswith("src."), "Failed trampoline hit..."
# This repo uses a top-level ``src`` package for all internal imports
# (``from src.engines.account ...``).  Patch mutmut's ``record_trampoline_hit``
# to strip the ``src.`` prefix before recording, so mutation testing works
# without changing any production import statements.  Only active when mutmut
# sets MUTANT_UNDER_TEST (normal pytest runs are unaffected).
# ============================================================
if __import__("os").environ.get("MUTANT_UNDER_TEST"):
    import functools as _functools

    import mutmut.__main__ as _mm_main

    _orig_record = _mm_main.record_trampoline_hit

    @_functools.wraps(_orig_record)
    def _safe_record_trampoline_hit(name: str, caller=None):
        if name.startswith("src."):
            name = name[len("src.") :]
        _orig_record(name, caller=caller)

    _mm_main.record_trampoline_hit = _safe_record_trampoline_hit

    # M9-C71: install the independent mutation execution sentinel. mutmut's
    # verdict comes from a test process's exit code, which proves "a test
    # failed", not "the mutated code ran". The sentinel records the latter
    # directly, so a survivor can be distinguished from a mutant the suite
    # never executed. It arms via an import hook, so no test needs to opt in
    # and no test is modified to satisfy the measurement apparatus.
    try:
        import importlib.util as _importlib_util
        import os as _os

        # Resolve the sentinel by walking up from this file until the directory
        # holding it is found. A fixed number of parent hops would be wrong
        # here: mutmut runs pytest from inside ``mutants/``, where this same
        # conftest lives at ``mutants/tests/conftest.py`` — two levels up is
        # ``mutants/``, not ``backend/``. Searching for the file itself is
        # correct in both the pristine and the mutated tree.
        _sentinel_path = None
        _here = _os.path.dirname(_os.path.abspath(__file__))
        for _depth in range(6):
            _candidate = _os.path.join(_here, "mutation_trust", "canary", "sentinel.py")
            if _os.path.isfile(_candidate):
                _sentinel_path = _candidate
                break
            _here = _os.path.dirname(_here)
        if _sentinel_path is None:
            raise FileNotFoundError("C71 mutation sentinel not found above conftest")
        _sentinel_spec = _importlib_util.spec_from_file_location(
            "c71_mutation_sentinel", _sentinel_path
        )
        if _sentinel_spec is not None and _sentinel_spec.loader is not None:
            _sentinel = _importlib_util.module_from_spec(_sentinel_spec)
            __import__("sys").modules["c71_mutation_sentinel"] = _sentinel
            _sentinel_spec.loader.exec_module(_sentinel)
            _sentinel.install_import_hook()
    except Exception:
        # A sentinel that cannot install must not change any mutant's outcome;
        # the absence of its evidence is what the trust gate detects.
        pass

    # mutmut's trampoline changes call context, which triggers hypothesis's
    # `differing_executors` health check. Suppress it so mutation runs complete.
    try:
        from hypothesis import HealthCheck, settings  # noqa: PLC0415

        _cur = settings.current_profile().suppress_health_check
        if HealthCheck.differing_executors not in _cur:
            settings.register_profile(
                "mutmut_hints",
                suppress_health_check=list(_cur) + [HealthCheck.differing_executors],
            )
            settings.load_profile("mutmut_hints")
    except Exception:
        pass

# ============================================================
# Plugin Registration
# ============================================================
pytest_plugins = [
    "tests.fixtures.pytest_config",
    "tests.fixtures.hypothesis",
    "tests.fixtures.database",
    "tests.fixtures.seed",
    "tests.fixtures.client",
    "tests.fixtures.builders",
    "tests.fixtures.factories",
]

# ============================================================
# Backward-Compatible Re-Exports
# ============================================================
# Tests that import directly from tests.conftest continue to work.
from tests.fixtures.builders import (  # noqa: F401
    make_reconciliation_match,
    make_transaction,
)
from tests.fixtures.factories import (  # noqa: F401
    AccountBuilder,
    CreditCardBuilder,
    FinancialEventBuilder,
    HouseholdBuilder,
    LoanBuilder,
    ReconciliationMatchBuilder,
    StatementBuilder,
    TransactionBuilder,
)
