"""Run-id containment for the AI orchestrator (CWE-22).

``get_run``/``finalize_run``/``cancel_run`` are reached through HTTP routes
(``/platform/v1/ai/runs/{run_id}``), so the run id is externally controlled and
is used to build a filesystem path under the runs directory:

    GET  /platform/v1/ai/runs/{run_id}
    POST /platform/v1/ai/runs/{run_id}/cancel

Before the fix, ``self._runs_dir / f"{run_id}.json"`` was read and written with
no validation, so a traversal segment in the id reached an arbitrary file read
(``get_run``) and, when the run existed in memory, an arbitrary file write
(``_persist_run`` via ``cancel_run``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.platform.ai.orchestrator import (  # noqa: E402
    _RUN_ID_RE,
    AIOrchestrator,
    _run_path,
)

VALID_ID = "ai-0123456789ab"


class TestRunIdFormat:
    def test_the_shape_this_module_mints_is_accepted(self):
        assert _RUN_ID_RE.match(VALID_ID)

    @pytest.mark.parametrize(
        "bad",
        [
            "",
            "ai-",
            "ai-XYZ",
            "ai-0123456789ABC",  # uppercase hex
            "ai-0123456789abX",  # trailing junk
            "ai-0123456789a",  # too short
            "ai-0123456789abc",  # too long
            "0123456789ab",
            "run-0123456789ab",
            "ai-0123456789ab.json",
        ],
    )
    def test_malformed_ids_are_rejected(self, bad):
        assert not _RUN_ID_RE.match(bad)

    @pytest.mark.parametrize(
        "bad",
        [
            "../../etc/passwd",
            "../secret",
            "..",
            "../../../etc/passwd",
            "ai-0123456789ab/../../../etc/passwd",
            "/etc/passwd",
            "/absolute/path",
            "ai-0123456789ab\x00.json",
        ],
    )
    def test_traversal_ids_are_rejected(self, bad):
        assert not _RUN_ID_RE.match(bad)

    def test_non_string_is_rejected(self):
        assert _run_path(Path("/tmp"), None) is None  # type: ignore[arg-type]
        assert _run_path(Path("/tmp"), 12345) is None  # type: ignore[arg-type]


class TestRunPathContainment:
    def test_valid_id_resolves_inside_the_runs_dir(self, tmp_path):
        path = _run_path(tmp_path, VALID_ID)
        assert path is not None
        assert path.resolve().parent == tmp_path.resolve()

    def test_traversal_id_yields_no_path(self, tmp_path):
        assert _run_path(tmp_path, "../../etc/passwd") is None
        assert _run_path(tmp_path, "..") is None
        assert _run_path(tmp_path, "/etc/passwd") is None


class TestOrchestratorRejectsTraversal:
    @pytest.fixture()
    def orchestrator(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        return AIOrchestrator()

    def _write_secret(self, orchestrator) -> Path:
        """Plant a readable file outside the runs directory."""

        secret = orchestrator._runs_dir.parent / "secret.json"
        secret.parent.mkdir(parents=True, exist_ok=True)
        secret.write_text(json.dumps({"stolen": True}), encoding="utf-8")
        return secret

    def test_get_run_does_not_read_outside_the_runs_dir(self, orchestrator):
        secret = self._write_secret(orchestrator)
        traversal = f"../{secret.name}"
        assert orchestrator.get_run(traversal) is None
        assert traversal not in orchestrator._runs

    def test_get_run_returns_a_real_run(self, orchestrator):
        run = orchestrator.start_run(symptom="demo")
        fetched = orchestrator.get_run(run["id"])
        assert fetched is not None
        assert fetched["id"] == run["id"]

    def test_persist_refuses_an_invalid_id(self, orchestrator, tmp_path):
        outside = tmp_path / "escaped.json"
        # A run registered under a traversal id must not be written outside.
        orchestrator._runs["../escaped"] = {"run_id": "../escaped"}
        orchestrator._persist_run("../escaped")
        assert not outside.exists()

    def test_cancel_run_on_a_traversal_id_is_a_no_op(self, orchestrator):
        orchestrator._runs["../../etc"] = {"run_id": "../../etc", "status": "PENDING"}
        # cancel_run may still flip in-memory state, but must never persist
        # outside the runs directory.
        orchestrator.cancel_run("../../etc")
        assert not (orchestrator._runs_dir.parent.parent / "etc.json").exists()
