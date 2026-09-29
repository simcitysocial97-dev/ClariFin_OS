"""Regression coverage for changed-file parsing and boundary classification.

Two defects motivated this module:

*   ``git diff --name-only`` was read as newline-delimited text. Git quotes and
    C-stylescapes any path containing a space, quote, tab, backslash, non-ASCII
    character or control character, so those records reached capability matching
    as a mangled transport encoding and silently matched no capability. A
    committed boundary on the M9 merge contained 19 such records.

*   Regenerable ``runtime/generated`` output was only excluded when it sat at
    the repository root, so a tool running from a subdirectory produced an
    escaped copy (``backend/runtime/generated/``) that entered the boundary.

Both are covered here, together with the large-boundary classification.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.orchestrator import (  # noqa: E402
    GENERATED_PATH_PREFIXES,
    _filter_changed_files,
    is_generated_or_artifact_path,
    normalize_repo_path,
)

# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------


class TestNormalizeRepoPath:
    def test_plain_path_is_unchanged(self):
        assert normalize_repo_path("backend/src/api.py") == "backend/src/api.py"

    def test_backslash_is_preserved_as_a_filename_character(self):
        # Git never emits a backslash as a path separator, so rewriting one
        # would corrupt a real file named `with\backslash.py` into a path in a
        # `with/` directory.
        assert normalize_repo_path("docs/with\\backslash.py") == (
            "docs/with\\backslash.py"
        )

    def test_backslash_inside_a_quoted_record_survives(self):
        assert normalize_repo_path('"docs/with\\\\backslash.py"') == (
            "docs/with\\backslash.py"
        )

    def test_leading_dot_slash_is_stripped(self):
        assert normalize_repo_path("./backend/src/api.py") == "backend/src/api.py"

    def test_duplicate_separators_collapse(self):
        assert normalize_repo_path("backend//src///api.py") == "backend/src/api.py"

    def test_surrounding_whitespace_is_trimmed(self):
        assert normalize_repo_path("  backend/src/api.py  ") == "backend/src/api.py"

    @pytest.mark.parametrize("value", ["", "   ", ".", "./", "/"])
    def test_non_paths_normalize_to_empty(self, value):
        assert normalize_repo_path(value) == ""

    def test_path_with_spaces_is_preserved(self):
        assert normalize_repo_path("docs/my notes/plan v2.md") == (
            "docs/my notes/plan v2.md"
        )

    def test_path_with_tab_is_preserved(self):
        assert normalize_repo_path("docs/a\tb.md") == "docs/a\tb.md"

    def test_path_with_unicode_is_preserved(self):
        assert normalize_repo_path("docs/rapport-café-über.md") == (
            "docs/rapport-café-über.md"
        )

    def test_git_octal_escape_is_decoded(self):
        # Git renders a non-ASCII byte inside a quoted path as an octal escape.
        assert normalize_repo_path('"docs/caf\\303\\251.md"') == "docs/café.md"

    def test_git_escape_sequences_are_decoded(self):
        assert normalize_repo_path('"docs/a\\tb.md"') == "docs/a\tb.md"
        assert normalize_repo_path('"docs/a\\"b.md"') == 'docs/a"b.md'
        assert normalize_repo_path('"docs/a\\\\b.md"') == "docs/a\\b.md"

    def test_embedded_quote_survives_a_second_pass(self):
        # A path that genuinely contains a quote must round-trip unchanged, so
        # normalizing it twice is idempotent.
        path = 'docs/say"hi".md'
        once = normalize_repo_path(f'"{path}"')
        assert once == path
        assert normalize_repo_path(once) == once


# ---------------------------------------------------------------------------
# Generated / artifact exclusion
# ---------------------------------------------------------------------------


class TestGeneratedExclusion:
    @pytest.mark.parametrize(
        "path",
        [
            "runtime/generated/m9-c42.21/survivors/core.diff",
            "runtime/generated/verification-cache.json",
            "runtime/generated/platform/snapshot.json",
        ],
    )
    def test_root_generated_output_is_excluded(self, path):
        assert is_generated_or_artifact_path(path)

    @pytest.mark.parametrize(
        "path",
        [
            "runtime/runtime/generated/git-fetch-events.jsonl",
            "backend/runtime/generated/platform/snapshot.json",
            "frontend/runtime/generated/typescript-symbol-cache/symbol-cache.json",
        ],
    )
    def test_escaped_generated_roots_are_excluded(self, path):
        """A cwd-relative write must not escape the boundary filter."""

        assert is_generated_or_artifact_path(path)

    def test_generated_at_any_depth_is_excluded(self):
        assert is_generated_or_artifact_path("tools/x/runtime/generated/a.json")

    @pytest.mark.parametrize(
        "path",
        [
            "backend/tests/generated/capability-registry.yaml",
            "node_modules/react/index.js",
            "frontend/node_modules/next/index.js",
            "backend/src/__pycache__/api.cpython-312.pyc",
            "backend/mutants/src/api.py",
            "backend/tests/contract/generated/test_accounts.py",
        ],
    )
    def test_caches_binaries_and_derived_tests_are_excluded(self, path):
        assert is_generated_or_artifact_path(path)

    @pytest.mark.parametrize(
        "path",
        [
            "backend/src/api.py",
            "runtime/foundation/verification/orchestrator.py",
            "frontend/app/platform/page.tsx",
            ".github/workflows/quality.yml",
            "backend/tests/integration/test_platform_api_phase3.py",
        ],
    )
    def test_source_paths_are_kept(self, path):
        assert not is_generated_or_artifact_path(path)

    def test_generated_prefixes_are_absolute_repo_relative(self):
        # Every prefix must anchor at a repository-relative root so the filter
        # cannot match an unrelated directory elsewhere in the tree.
        for prefix in GENERATED_PATH_PREFIXES:
            assert not prefix.startswith("/")
            assert not prefix.startswith("./")


# ---------------------------------------------------------------------------
# Filter behaviour
# ---------------------------------------------------------------------------


class TestFilterChangedFiles:
    def test_filter_is_deterministic_and_deduplicated(self):
        result = _filter_changed_files(["b.py", "a.py", "b.py", "a.py"])
        assert result == ["a.py", "b.py"]

    def test_filter_is_order_independent(self):
        forward = _filter_changed_files(["a.py", "b.py", "c.py"])
        reverse = _filter_changed_files(["c.py", "b.py", "a.py"])
        assert forward == reverse

    def test_generated_only_change_yields_empty_boundary(self):
        assert _filter_changed_files(["runtime/generated/metrics/x.json"]) == []

    def test_mixed_change_keeps_only_source(self):
        result = _filter_changed_files(
            [
                "runtime/generated/metrics/x.json",
                "backend/src/api.py",
                "backend/tests/generated/registry.yaml",
                "frontend/app/page.tsx",
            ]
        )
        assert result == ["backend/src/api.py", "frontend/app/page.tsx"]


# ---------------------------------------------------------------------------
# End-to-end: real git output containing hostile paths
# ---------------------------------------------------------------------------


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], capture_output=True, cwd=str(cwd), timeout=120
    )


@pytest.mark.slow
class TestRealGitPathParsing:
    """Build a throwaway repository whose changed files need git quoting."""

    HOSTILE = {
        "plain.py": "x = 1\n",
        "with space.py": "x = 2\n",
        'with"quote.py': "x = 3\n",
        "with\ttab.py": "x = 4\n",
        "with\\backslash.py": "x = 5\n",
        "with-unicode-café.py": "x = 6\n",
    }

    @pytest.fixture(scope="class")
    def repo_with_hostile_paths(self, tmp_path_factory):
        repo = tmp_path_factory.mktemp("hostile-paths")
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.invalid",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.invalid",
        }
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=env)
        for rel, content in self.HOSTILE.items():
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, env=env)
        subprocess.run(
            ["git", "commit", "-q", "-m", "base"], cwd=repo, check=True, env=env
        )
        for rel in self.HOSTILE:
            (repo / rel).write_text("x = 99\n", encoding="utf-8")
        return repo

    def test_newline_output_is_unparseable_for_hostile_paths(self, repo_with_hostile_paths):
        """Documents the defect: git quotes these records on one line each."""

        result = _git("diff", "--name-only", "HEAD", cwd=repo_with_hostile_paths)
        raw = result.stdout.decode("utf-8", "surrogateescape")
        quoted = [line for line in raw.splitlines() if line.startswith('"')]
        assert quoted, "expected git to quote at least one hostile path"

    def test_nul_output_yields_exact_paths(self, repo_with_hostile_paths):
        result = _git("diff", "--name-only", "-z", "HEAD", cwd=repo_with_hostile_paths)
        records = [r for r in result.stdout.decode("utf-8", "surrogateescape").split("\0") if r]
        assert set(records) == set(self.HOSTILE)
        assert not any(r.startswith('"') for r in records)

    def test_normalization_recovers_every_hostile_path(self, repo_with_hostile_paths):
        result = _git("diff", "--name-only", "-z", "HEAD", cwd=repo_with_hostile_paths)
        records = [r for r in result.stdout.decode("utf-8", "surrogateescape").split("\0") if r]
        assert {normalize_repo_path(r) for r in records} == set(self.HOSTILE)

    def test_quoted_newline_records_recover_exact_paths(self, repo_with_hostile_paths):
        """Even a caller that still receives quoted records recovers the path."""

        result = _git("diff", "--name-only", "HEAD", cwd=repo_with_hostile_paths)
        raw = result.stdout.decode("utf-8", "surrogateescape")
        recovered = {
            normalize_repo_path(line) for line in raw.splitlines() if line.strip()
        }
        assert set(self.HOSTILE) <= recovered
