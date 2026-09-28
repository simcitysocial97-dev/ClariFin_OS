# backend/tests/mutation_trust/canary/sentinel_plugin.py
#
# M9-C71 — pytest entry point that installs the mutation execution sentinel.
#
# WHY A SEPARATE PLUGIN RATHER THAN ONLY conftest
# -----------------------------------------------
# mutmut runs pytest with the working directory set to its generated ``mutants/``
# tree and ``--rootdir=.``, so ``mutants/tests/conftest.py`` is discovered ONLY
# when the selected test path actually lives under ``tests/``. A shard whose
# selection includes tests outside that subtree therefore never imports the
# conftest, the sentinel never installs, and every mutant is reported as
# unobserved — a false negative in the measurement apparatus, which is worse
# than having no apparatus because it looks like evidence.
#
# Loading the plugin explicitly with ``-p`` makes installation independent of
# test-path layout, so the sentinel covers every shard uniformly. It is inert
# outside a mutmut mutant fork, so the same flag is harmless in any other
# context.

from __future__ import annotations


def pytest_configure(config) -> None:  # noqa: ANN001, ARG001 - pytest hook signature
    """Install the execution sentinel as early as possible in the session."""
    import importlib.util
    import os
    import sys

    if not os.environ.get("MUTANT_UNDER_TEST"):
        return

    sentinel_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sentinel.py"
    )
    if not os.path.isfile(sentinel_path):
        return
    try:
        spec = importlib.util.spec_from_file_location(
            "c71_mutation_sentinel", sentinel_path
        )
        if spec is None or spec.loader is None:
            return
        sentinel = importlib.util.module_from_spec(spec)
        sys.modules["c71_mutation_sentinel"] = sentinel
        spec.loader.exec_module(sentinel)
        sentinel.install_import_hook()
        _SENTINEL.append(sentinel)
    except Exception:
        # A sentinel that cannot install must not change any mutant's outcome.
        # Its absence is exactly what the mutation trust gate detects, so the
        # failure is silent here by design and loud in the certification.
        return


#: Holds the installed sentinel module for the lifetime of the session.
_SENTINEL: list = []


def pytest_runtest_setup(item) -> None:  # noqa: ANN001 - pytest hook signature
    """Re-arm before each test.

    ``pytest_configure`` runs once, before collection, so a module first
    imported during a test's own setup would be missed. Re-arming per test is
    cheap (one dict lookup on an already-imported module) and makes the evidence
    independent of import order.
    """
    for sentinel in _SENTINEL:
        try:
            sentinel.arm_already_imported()
        except Exception:
            continue
