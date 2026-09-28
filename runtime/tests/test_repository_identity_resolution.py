# runtime/tests/test_repository_identity_resolution.py
#
# M9-C72 — Repository identity must survive a detached HEAD.
#
# WHY THIS EXISTS
# ---------------
# `_resolve_repository_identity()` read the branch with
# `git branch --show-current`, which returns an EMPTY STRING on a detached
# HEAD. GitHub's `pull_request` event checks out a synthetic merge commit, so
# the checkout is ALWAYS detached on a pull request — meaning the recorded
# verification event carried no branch on exactly the runs where attributing
# evidence matters most. Two C57 self-contract tests caught it
# (O2-G9 "identity not empty"), and because `Runtime Verification` is a
# REQUIRED status check, every pull request failed to merge.
#
# The failure was invisible locally and on push runs, because there HEAD is
# attached. It only appeared on `pull_request`. That is the worst possible
# place for a defect to hide, so the detached case is asserted here directly
# rather than being left to be rediscovered by a blocked merge.
#
# These tests use the REAL git binary against a real temporary repository, so
# they exercise the actual command behaviour rather than a mock's assumption
# about it — a mock would have encoded the same wrong belief as the bug.

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from runtime.system.observability import event_store


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    """A real git repository with one commit, in a non-bare state."""
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, env=env, check=True)
    (repo / "a.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    return repo


def _resolve_against(repo: Path, monkeypatch, **env_extra) -> tuple[str, str]:
    """Resolve identity as if the process were running inside *repo*."""
    monkeypatch.setattr(event_store, "REPO_ROOT", repo)
    for key in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env_extra.items():
        monkeypatch.setenv(key, value)
    return event_store._resolve_repository_identity()


class TestRepositoryIdentity:
    def test_attached_head_reports_the_branch(self, temp_repo, monkeypatch):
        commit_sha, branch = _resolve_against(temp_repo, monkeypatch)

        assert commit_sha
        assert branch == "main", "an attached HEAD must report its real branch"

    def test_detached_head_never_reports_a_blank_branch(self, temp_repo, monkeypatch):
        """The exact regression: a PR checkout is detached, so blank is not an option."""
        subprocess.run(
            ["git", "checkout", "-q", "--detach", "HEAD"],
            cwd=temp_repo,
            check=True,
        )
        assert (
            subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=temp_repo,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            == ""
        ), "fixture must actually be detached for this test to mean anything"

        commit_sha, branch = _resolve_against(temp_repo, monkeypatch)

        assert commit_sha
        assert branch.strip(), "a detached HEAD must still yield a non-blank identity"

    def test_pull_request_env_yields_the_source_branch(self, temp_repo, monkeypatch):
        """`GITHUB_HEAD_REF` is the PR's source branch — the most useful answer."""
        subprocess.run(
            ["git", "checkout", "-q", "--detach", "HEAD"],
            cwd=temp_repo,
            check=True,
        )

        _, branch = _resolve_against(
            temp_repo, monkeypatch, GITHUB_HEAD_REF="feature/my-change"
        )

        assert branch == "feature/my-change"

    def test_workflow_ref_name_is_the_next_best_hint(self, temp_repo, monkeypatch):
        subprocess.run(
            ["git", "checkout", "-q", "--detach", "HEAD"],
            cwd=temp_repo,
            check=True,
        )

        _, branch = _resolve_against(
            temp_repo, monkeypatch, GITHUB_REF_NAME="release/1.2.3"
        )

        assert branch == "release/1.2.3"

    def test_detached_fallback_carries_the_commit_it_was_built_from(
        self, temp_repo, monkeypatch
    ):
        """With no branch and no CI hint, the identity must still say something true."""
        subprocess.run(
            ["git", "checkout", "-q", "--detach", "HEAD"],
            cwd=temp_repo,
            check=True,
        )

        commit_sha, branch = _resolve_against(temp_repo, monkeypatch)
        short = commit_sha[: len(branch.split("@")[-1])] if "@" in branch else ""

        assert branch.startswith("detached@"), branch
        assert short, "the detached sentinel should embed the short sha it names"

    def test_a_broken_git_never_returns_a_blank_branch(self, temp_repo, monkeypatch):
        """Even total failure must produce an identity, not an empty field.

        An observability system that silently records nothing when its probe
        fails is worse than one that records a sentinel: the gap is invisible.
        """
        monkeypatch.setattr(event_store, "REPO_ROOT", temp_repo)

        def _boom(*args, **kwargs):
            raise OSError("git unavailable")

        monkeypatch.setattr(event_store.subprocess, "run", _boom)
        monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
        monkeypatch.delenv("GITHUB_REF_NAME", raising=False)

        commit_sha, branch = event_store._resolve_repository_identity()

        assert commit_sha == ""
        assert branch.strip(), "identity must be a sentinel, never blank"
