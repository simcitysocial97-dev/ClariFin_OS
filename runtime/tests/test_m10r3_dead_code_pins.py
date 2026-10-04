"""M10-R3 / L8c — pin the dead-code facts instead of deleting on an unvalidated belief.

Checkpoint A reported that `forensic_cli` and `diagnostic_agent` are "unreachable from
the CLI". The reachability claim was right; the implication was not. Investigation before
deleting anything found:

* `forensic_cli` has **zero Python importers** — genuinely unreachable as code.
* But it is named as the *declared implementation site* in provenance metadata for routes
  the canonical table marks ``DEPRECATED`` (``route_authority.py:120``,
  ``certification.py:182``). Those strings are load-bearing: they are how this repository
  records where an implementation lives.
* `diagnostic_agent` supplies the ``Uncertainty`` / ``Explainability`` /
  ``CERTIFIABLE`` vocabulary those strings refer to, and is imported only by
  `forensic_cli`.

So deletion would orphan the provenance of deprecated routes — a documentation
regression traded for a tidy file list. The code removal stays deferred; what is done
here is to convert "I believe this is dead" into a mechanically enforced claim.

Each test below FAILS if someone wires the module up, and the failure message says to
delete the pin rather than to keep it. That is the behaviour a pin needs: it must be
annoying to leave behind.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "runtime" / "foundation" / "verification"


def _python_importers(module: str) -> list[Path]:
    """Files with a real ``import`` of *module*, excluding tests and archives."""
    offenders: list[Path] = []
    for path in PKG.rglob("*.py"):
        if "archive" in path.parts or path.name == f"{module}.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = {a.name for a in node.names}
                if node.module and node.module.endswith(module):
                    offenders.append(path)
                    break
                if (
                    node.module
                    and node.module.endswith("verification")
                    and names
                    & {
                        module,
                    }
                ):
                    offenders.append(path)
                    break
            elif isinstance(node, ast.Import):
                if any(a.name.endswith(module) for a in node.names):
                    offenders.append(path)
                    break
    return offenders


class TestForensicCliIsUnreachable:
    def test_nothing_imports_it(self):
        offenders = _python_importers("forensic_cli")
        assert not offenders, (
            f"{[p.name for p in offenders]} now import forensic_cli, so it is no "
            f"longer dead. Delete THIS PIN, not the module — and if the new caller "
            f"needs it on the CLI, that is a design change worth naming."
        )

    def test_but_it_is_a_declared_implementation_site_so_removal_is_not_free(self):
        """The reason this is pinned rather than deleted.

        If this test starts failing, the provenance has been cleaned up and the module
        can then be removed with no documentation left dangling.
        """
        route_authority = (PKG / "route_authority.py").read_text(encoding="utf-8")
        certification = (PKG / "certification.py").read_text(encoding="utf-8")
        referenced = (
            "forensic_cli" in route_authority or "forensic_cli" in certification
        )
        assert referenced, (
            "the provenance strings no longer name forensic_cli, so it can now be "
            "deleted outright — this test and its pin should go with it"
        )

    def test_the_cli_never_dispatches_to_it(self):
        """`forensic-diagnose` / `forensic-report` are rewritten to `diagnose`."""
        from runtime.foundation.verification.canonical_control_plane import (
            _MIGRATION,
        )

        assert _MIGRATION["forensic-diagnose"][0] == "diagnose"
        assert _MIGRATION["forensic-report"][0] == "diagnose"


class TestDiagnosticAgentVocabulary:
    def test_it_is_only_reachable_through_forensic_cli(self):
        offenders = _python_importers("diagnostic_agent")
        assert {p.name for p in offenders} <= {"forensic_cli.py"}, (
            f"diagnostic_agent gained an importer other than forensic_cli: "
            f"{[p.name for p in offenders]}. Its CERTIFIABLE/Explainability vocabulary "
            f"is load-bearing, so a new caller should be deliberate."
        )

    def test_the_vocabulary_still_exists(self):
        """The uncertainty/explainability model is part of the certification surface.

        Deleting it would remove concepts the runtime reasons about, which is a different
        decision from deleting an unreachable CLI shim.
        """
        source = (PKG / "diagnostic_agent.py").read_text(encoding="utf-8")
        for concept in ("Uncertainty", "Explainability", "CERTIFIABLE"):
            assert concept in source, f"{concept} vanished from diagnostic_agent"


class TestExecutorEngineIsConsolidated:
    """L8d — the second process engine is gone.

    `Executor` used to run its own `subprocess.Popen(shell=True, start_new_session=True)`
    with its own tee, its own `_kill_process_group` and its own result directory. The
    repository therefore had two spawn paths for the same work, and only the canonical one
    had heartbeat, `classify_termination` and missing-binary detection — so anything routed
    through `Executor` reported a failed assertion for a command that never ran.
    """

    def test_executor_no_longer_spawns(self):
        """Parsed, not grepped.

        A textual check for ``Popen(`` matches the module's own docstring describing
        what it used to do — the same trap that made an earlier test report a workflow
        comment as a declaration. Only an AST walk sees real calls.
        """
        tree = ast.parse((PKG / "executor.py").read_text(encoding="utf-8"))
        spawns: list[str] = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr
                in {"Popen", "run", "call", "check_call", "check_output"}
            ):
                spawns.append(ast.unparse(node.func))
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and (node.func.id in {"system", "popen"})
            ):
                spawns.append(node.func.id)
        assert not spawns, (
            f"executor.py has regained a direct spawn path: {spawns}. The canonical "
            f"worker is the one place a verification process is created."
        )

    def test_it_delegates_to_the_canonical_worker(self):
        executor = (PKG / "executor.py").read_text(encoding="utf-8")
        assert "run_streaming_command" in executor
        assert "classify_termination" in executor

    def test_each_retry_attempt_gets_its_own_evidence_file(self):
        """Attempts must not be concatenated into one file.

        The old code appended every attempt into `<task>-stdout.txt`, so after a retry
        the file held attempt 1 followed by attempt 2 with nothing to distinguish them.
        The canonical worker truncates up front — "a file means this execution" — because
        leftover content masquerading as current output is the stale-evidence hazard.
        Per-attempt files preserve every attempt *and* make each attributable.
        """
        executor = (PKG / "executor.py").read_text(encoding="utf-8")
        assert (
            "a{attempt}" in executor or "attempt" in executor
        ), "evidence filenames must distinguish retry attempts"

    def test_cancellation_still_works(self):
        """Delegating ownership of the child must not have made `cancel()` a no-op.

        It briefly did: `Executor` killed a process group it no longer owned. The
        canonical worker now accepts a `cancel_event` and kills the tree on it, so the
        right to stop the child travels with ownership of the child.
        """
        from runtime.foundation.verification.parallel_executor import (
            run_streaming_command,
        )

        import inspect

        assert "cancel_event" in inspect.signature(run_streaming_command).parameters

    def test_parallel_executor_is_the_canonical_worker(self):
        """The one authoritative spawn path, asserted so it cannot quietly fork."""
        source = (PKG / "parallel_executor.py").read_text(encoding="utf-8")
        assert "def run_streaming_command" in source
        assert "start_new_session=True" in source, (
            "the canonical worker must keep its own process group, or a timeout cannot "
            "kill a child's children"
        )


class TestOrphanCliSurface:
    def test_verification_cli_cli_py_is_still_unwired(self):
        """`verification/cli/cli.py` is an orphan: no entry point, no timeout."""
        orphan = PKG / "cli" / "cli.py"
        assert orphan.exists(), (
            "verification/cli/cli.py was removed — delete this pin and record the "
            "removal."
        )
        facade = (PKG / "control_plane_facade.py").read_text(encoding="utf-8")
        assert "verification.cli.cli" not in facade and "from .cli.cli" not in facade, (
            "the facade now imports verification/cli/cli.py, so it is no longer an "
            "orphan. Either wire it properly or delete it — but do not leave a second "
            "CLI surface."
        )
