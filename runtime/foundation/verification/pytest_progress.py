"""Test-level progress evidence for long verification suites.

Why this exists
---------------
A verification suite that takes half an hour reports, at the end, only a
summary line. If the process dies, is killed, or times out mid-run, the
operator is left with a duration and an exit code and no way to tell *which
test* was executing. During the M9 stabilization of 2026-09-30 that produced
two 29-minute runs whose evidence was a bare ``command exit 1``, and
reproducing them meant running the whole suite again to try to catch the
failure in the act. Reconcile run ``execplan-d210b2f3ea52`` lost its output
entirely: the orchestrator buffered every task's stdout in memory and wrote it
only after the child exited, so all 20 task logs were zero bytes.

This module makes a running suite answer that question while it is running.

What it records
---------------
Two files per pytest process, both under
``runtime/generated/verification-progress/`` (overridable with
``VERIFY_PYTEST_PROGRESS_DIR``):

``pytest-progress-<pid>.jsonl``
    Append-only event stream: one line per test start and one per test report
    (setup/call/teardown), plus a session header and footer. Flushed after
    every line, so the evidence is on disk as it happens and survives the
    process being killed.

``pytest-state-<pid>.json``
    A small, atomically-replaced summary of *right now*: which test last
    started, which last completed, that test's outcome and timestamp, and the
    running counts. When a suite dies mid-test, ``last_started_test`` with no
    matching completion is the test to investigate, immediately, with no
    re-run.

Design constraints
------------------
* Minimal and additive. It observes; it never changes collection, ordering,
  outcomes or assertions, and it is not a reporting framework.
* Never raises into the test run. Every write is guarded, and the tracker
  disables itself permanently on the first failure so a broken filesystem
  cannot break verification.
* Flush-per-line, atomic-replace for the state file, so an abnormal
  termination cannot destroy the record of what happened before it.
* Off with ``VERIFY_PYTEST_PROGRESS=0``.

It uses pytest's own ``pytest_runtest_logstart`` / ``pytest_runtest_logreport``
hooks. The repository had no test-progress instrumentation of any kind before
this (no ``pytest_runtest_*`` hook existed anywhere, and no plugin was
registered), so this is the smallest hook that produces the required evidence
and it needs no change to any verification command.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_PROGRESS_DIR = REPO_ROOT / "runtime" / "generated" / "verification-progress"


def _safe(fn):
    """Call *fn*, returning None on any failure. Diagnostics must never raise."""
    try:
        return fn()
    except Exception:  # noqa: BLE001
        return None


def _pytest_version() -> str | None:
    """The running pytest version, or None if it cannot be determined."""
    import pytest

    return _safe(lambda: str(pytest.__version__))


def _installed_plugin_names(session) -> list[str]:
    """Best-effort list of active pytest plugin *distribution* names.

    Recorded so a failure can be compared against the plugin set that produced
    it — plugin sets change which hooks and which timeout handling exist. Only
    distributions are kept: the full plugin set includes object reprs with
    memory addresses, which are noise in an evidence file and differ every run.
    """
    manager = _safe(lambda: session.config.pluginmanager)
    if manager is None:
        return []
    names = set()
    for entry in _safe(lambda: list(manager.list_plugin_distinfo())) or []:
        name = _safe(lambda entry=entry: getattr(entry, "project_name", None))
        if name:
            names.add(str(name))
    for entry in _safe(lambda: list(manager.get_plugins())) or []:
        mod = _safe(lambda entry=entry: getattr(entry, "__name__", None))
        if mod and "." not in str(mod):
            names.add(str(mod))
    return sorted(names)


def _resource_sample() -> dict:
    """Cheap resource reading taken at each test boundary.

    A run that fails is very often a run that was starved, and the question
    "was the machine out of memory / CPU at the moment this test ran?" cannot
    be answered after the fact without this. ``os.getloadavg()`` and the RSS
    page count are two syscalls, so sampling them per test is affordable; the
    values land next to the nodeid that was executing.
    """
    sample: dict[str, Any] = {}
    load = _safe(os.getloadavg)
    if load:
        sample["loadavg_1m"] = round(load[0], 2)
        sample["loadavg_5m"] = round(load[1], 2)
    rss_pages = _safe(lambda: os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    if rss_pages:
        try:
            with open("/proc/self/statm", encoding="utf-8") as handle:
                resident_pages = int(handle.read().split()[1])
            sample["system_ram_bytes"] = rss_pages
            sample["process_rss_bytes"] = resident_pages * os.sysconf("SC_PAGE_SIZE")
            sample["rss_percent_of_ram"] = round(
                100.0 * resident_pages * os.sysconf("SC_PAGE_SIZE") / rss_pages, 2
            )
        except (OSError, ValueError, IndexError):
            pass
    return sample


class TestProgressTracker:
    """Records per-test start/report events for one pytest process.

    Registered as a pytest plugin by whichever ``conftest.py`` covers the suite
    under test. All public methods are no-ops if the tracker is disabled or has
    failed, so a hook can never fail a test run.
    """

    def __init__(self, progress_dir: Path | None = None) -> None:
        self._dir = Path(
            progress_dir
            or os.environ.get("VERIFY_PYTEST_PROGRESS_DIR", str(DEFAULT_PROGRESS_DIR))
        )
        self._enabled = os.environ.get("VERIFY_PYTEST_PROGRESS", "1") != "0"
        self._disabled_reason: str | None = None
        self._pid = os.getpid()
        self._events: Path = self._dir / f"pytest-progress-{self._pid}.jsonl"
        self._state: Path = self._dir / f"pytest-state-{self._pid}.json"
        self._started_at = time.time()
        self._last_started: str | None = None
        self._last_completed: str | None = None
        self._last_outcome: str | None = None
        self._last_completed_at: float | None = None
        self._counts: dict[str, int] = {}
        self._session_started = False

    # -- plumbing ---------------------------------------------------------

    @property
    def events_path(self) -> Path:
        """Path of this process's append-only event stream."""
        return self._events

    @property
    def state_path(self) -> Path:
        """Path of this process's last-known state record."""
        return self._state

    def _disable(self, reason: str) -> None:
        self._enabled = False
        self._disabled_reason = reason

    def _ensure_dir(self) -> bool:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._disable(f"cannot create progress dir: {exc}")
            return False
        return True

    def _append(self, event: dict[str, Any]) -> None:
        """Append one event and flush it. A crash after this keeps the line."""
        if not self._enabled:
            return
        try:
            with self._events.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
                handle.flush()
        except OSError as exc:
            self._disable(f"cannot append progress event: {exc}")

    def _write_state(self, **extra: Any) -> None:
        """Atomically replace the state record.

        Write-then-rename so a reader never sees a half-written file and so the
        previous good state survives a crash mid-write.
        """
        if not self._enabled:
            return
        state: dict[str, Any] = {
            "pid": self._pid,
            "session_started_at": self._started_at,
            "session_started": self._session_started,
            "last_started_test": self._last_started,
            "last_completed_test": self._last_completed,
            "last_test_outcome": self._last_outcome,
            "last_test_timestamp": self._last_completed_at,
            "counts": dict(self._counts),
            "resources": _resource_sample(),
            "updated_at": time.time(),
        }
        state.update(extra)
        tmp = self._state.with_suffix(".json.tmp")
        try:
            tmp.write_text(
                json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
            )
            os.replace(tmp, self._state)
        except OSError as exc:
            self._disable(f"cannot write progress state: {exc}")

    def _bump(self, outcome: str) -> None:
        self._counts[outcome] = self._counts.get(outcome, 0) + 1

    # -- lifecycle --------------------------------------------------------

    def pytest_sessionstart(self, session) -> None:
        if not self._enabled or not self._ensure_dir():
            return
        self._session_started = True
        self._started_at = time.time()
        self._append(
            {
                "event": "session_start",
                "pid": self._pid,
                "ts": self._started_at,
                "argv": list(sys.argv),
                "cwd": os.getcwd(),
                "python": sys.executable,
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "rootdir": str(getattr(session.config, "rootpath", "")),
                "pytest_version": _pytest_version(),
                "plugins": _installed_plugin_names(session),
                "events_path": str(self._events),
                "state_path": str(self._state),
            }
        )
        self._write_state()

    def pytest_sessionfinish(self, session, exitstatus) -> None:
        if not self._enabled:
            return
        self._append(
            {
                "event": "session_finish",
                "pid": self._pid,
                "ts": time.time(),
                "exitstatus": int(exitstatus),
                "counts": dict(self._counts),
                "last_started_test": self._last_started,
                "last_completed_test": self._last_completed,
            }
        )
        self._write_state(
            session_finished=True,
            exit_status=int(exitstatus),
            duration_seconds=time.time() - self._started_at,
        )

    # -- per-test hooks ---------------------------------------------------

    def pytest_runtest_logstart(self, nodeid: str, location) -> None:
        """A test has begun.

        This is the hook that answers "what was running when it died": the
        record holds the nodeid the instant the test starts, before any of its
        code runs, so it is already on disk if the process never returns.
        """
        if not self._enabled:
            return
        self._last_started = nodeid
        self._append(
            {
                "event": "start",
                "pid": self._pid,
                "ts": time.time(),
                "nodeid": nodeid,
                "resources": _resource_sample(),
            }
        )
        self._write_state()

    def pytest_runtest_logreport(self, report) -> None:
        """A test phase (setup / call / teardown) has produced a report."""
        if not self._enabled:
            return
        outcome = str(report.outcome)
        event = {
            "event": "report",
            "pid": self._pid,
            "ts": time.time(),
            "nodeid": report.nodeid,
            "phase": report.when,
            "outcome": outcome,
            "duration": getattr(report, "duration", None),
        }
        if outcome == "failed":
            # The longrepr is what makes the record actionable without a
            # re-run, so keep it, bounded so one huge traceback cannot bloat
            # the stream.
            text = ""
            try:
                text = str(report.longrepr)[:4000]
            except Exception:  # noqa: BLE001 - diagnostics must never raise
                text = "<longrepr unavailable>"
            event["longrepr"] = text
        self._append(event)
        # Only the call phase decides the test's outcome; setup/teardown report
        # for the same nodeid and would otherwise overwrite it.
        if report.when == "call":
            self._last_completed = report.nodeid
            self._last_outcome = outcome
            self._last_completed_at = event["ts"]
        self._bump(f"{report.when}:{outcome}")
        self._write_state()
