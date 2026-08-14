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
    import mutmut.__main__ as _mm_main
    import functools as _functools

    _orig_record = _mm_main.record_trampoline_hit

    @_functools.wraps(_orig_record)
    def _safe_record_trampoline_hit(name: str, caller=None):
        if name.startswith("src."):
            name = name[len("src.") :]
        _orig_record(name, caller=caller)

    _mm_main.record_trampoline_hit = _safe_record_trampoline_hit

    # mutmut's trampoline changes call context, which triggers hypothesis's
    # `differing_executors` health check. Suppress it so mutation runs complete.
    try:
        from hypothesis import settings, HealthCheck  # noqa: PLC0415

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
