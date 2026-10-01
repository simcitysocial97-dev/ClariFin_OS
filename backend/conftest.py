"""Backend conftest.py — loads test fixtures for pytest 9.x compatibility."""

pytest_plugins = [
    "tests.fixtures.pytest_config",
    "tests.fixtures.hypothesis",
    "tests.fixtures.database",
    "tests.fixtures.seed",
    "tests.fixtures.client",
    "tests.fixtures.builders",
    "tests.fixtures.factories",
]

# Test-level progress evidence (M9 stabilization, 2026-09-30).
#
# The backend suites are long enough that a failure which stops mid-run used to
# leave no evidence of which test was executing. The tracker writes each test's
# start and report as they happen and maintains a state file naming the last
# test started, so an interrupted run identifies its failing test without a
# re-run. It observes only and can never fail a test run. The same tracker runs
# for the runtime suite (see runtime/tests/conftest.py); the module is
# repository-level so both suites report into one comparable format.
try:
    from runtime.foundation.verification.pytest_progress import TestProgressTracker

    _pytest_progress = TestProgressTracker()
except Exception:  # noqa: BLE001 - instrumentation must never break the suite
    _pytest_progress = None

if _pytest_progress is not None:

    def pytest_sessionstart(session):
        _pytest_progress.pytest_sessionstart(session)

    def pytest_sessionfinish(session, exitstatus):
        _pytest_progress.pytest_sessionfinish(session, exitstatus)

    def pytest_runtest_logstart(nodeid, location):
        _pytest_progress.pytest_runtest_logstart(nodeid, location)

    def pytest_runtest_logreport(report):
        _pytest_progress.pytest_runtest_logreport(report)
