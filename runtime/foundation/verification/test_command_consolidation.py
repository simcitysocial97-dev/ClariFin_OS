"""Runtime command consolidation tests.

Validates that all runtime verification commands are properly defined,
documented, and accessible via verify.py.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from runtime.foundation.verification.profiles import (
    VerificationProfile,
    get_profile,
    list_profiles,
    profile_names,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestProfileDefinitions:
    """Validate all profiles are defined and loadable."""

    def test_all_11_profiles_exist(self) -> None:
        """All 11 expected profiles are defined."""
        expected = {
            "quick",
            "backend",
            "frontend",
            "contracts",
            "graph",
            "full",
            "integration",
            "mutation",
            "runtime",
            "golden",
            "playwright",
        }
        actual = set(profile_names())
        assert expected.issubset(actual), f"Missing profiles: {expected - actual}"

    def test_get_profile_returns_correct_type(self) -> None:
        """get_profile() returns a VerificationProfile instance."""
        profile = get_profile("quick")
        assert isinstance(profile, VerificationProfile)
        assert profile.name == "quick"
        assert profile.scope is not None
        assert len(profile.tasks) > 0

    def test_get_profile_invalid_raises(self) -> None:
        """get_profile() raises for unknown profile names."""
        with pytest.raises(ValueError):
            get_profile("nonexistent_profile")

    def test_profile_has_no_duplicate_commands(self) -> None:
        """No profile should have duplicate task IDs."""
        for profile in list_profiles():
            task_ids = profile.task_ids()
            assert len(task_ids) == len(
                set(task_ids)
            ), f"Profile {profile.name} has duplicate task IDs: {task_ids}"

    def test_profile_commands_are_deterministic(self) -> None:
        """Profile task list is deterministic across calls."""
        profile1 = get_profile("backend")
        profile2 = get_profile("backend")
        assert profile1.task_ids() == profile2.task_ids()
        assert profile1.command_count() == profile2.command_count()


class TestQuickProfile:
    """Validate quick profile specifics."""

    def test_quick_profile_has_four_tasks(self) -> None:
        """Quick profile has exactly 4 tasks."""
        profile = get_profile("quick")
        assert len(profile.tasks) == 4

    def test_quick_profile_includes_lint(self) -> None:
        """Quick profile includes ruff linting."""
        profile = get_profile("quick")
        all_commands = []
        for task in profile.tasks:
            all_commands.extend(task.commands)
        assert any("ruff" in cmd for cmd in all_commands), "Quick should include ruff"

    def test_quick_profile_includes_format(self) -> None:
        """Quick profile includes black format check."""
        profile = get_profile("quick")
        all_commands = []
        for task in profile.tasks:
            all_commands.extend(task.commands)
        assert any("black" in cmd for cmd in all_commands), "Quick should include black"


class TestBackendProfile:
    """Validate backend profile specifics."""

    def test_backend_has_seven_tasks(self) -> None:
        """Backend profile has 7 tasks per documentation."""
        profile = get_profile("backend")
        assert len(profile.tasks) == 7


class TestGoldenProfile:
    """Validate golden profile specifics."""

    def test_golden_profile_runs_golden_tests(self) -> None:
        """Golden profile runs the golden test suite."""
        profile = get_profile("golden")
        all_commands = []
        for task in profile.tasks:
            all_commands.extend(task.commands)
        assert any(
            "golden" in cmd for cmd in all_commands
        ), "Golden profile should run golden tests"


class TestMutationProfile:
    """Validate mutation profile specifics."""

    def test_mutation_profile_distinguishes_smoke_from_full(self) -> None:
        """Mutation profile supports --smoke and full campaign modes."""
        profile = get_profile("mutation")
        assert len(profile.tasks) >= 2, "Mutation should have smoke + full tasks"

    def test_mutation_commands_include_runner(self) -> None:
        """Mutation profile uses mutation runner script."""
        profile = get_profile("mutation")
        all_commands = []
        for task in profile.tasks:
            all_commands.extend(task.commands)
        assert any(
            "mutation" in cmd.lower() for cmd in all_commands
        ), "Mutation profile should include mutation runner"


class TestFullProfile:
    """Validate full profile aggregates all scopes."""

    def test_full_profile_includes_lint_typecheck(self) -> None:
        """Full profile includes lint and typecheck."""
        profile = get_profile("full")
        all_commands = []
        for task in profile.tasks:
            all_commands.extend(task.commands)

        assert any("ruff" in cmd for cmd in all_commands), "Full should include ruff"
        assert any("mypy" in cmd for cmd in all_commands), "Full should include mypy"


class TestProfileScopes:
    """Validate profile scopes are correctly set."""

    def test_quick_scope_is_quick(self) -> None:
        """Quick profile has QUICK scope."""
        profile = get_profile("quick")
        assert profile.scope.value == "quick"

    def test_backend_scope_is_backend(self) -> None:
        """Backend profile has BACKEND scope."""
        profile = get_profile("backend")
        assert profile.scope.value == "backend"

    def test_frontend_scope_is_frontend(self) -> None:
        """Frontend profile has FRONTEND scope."""
        profile = get_profile("frontend")
        assert profile.scope.value == "frontend"

    def test_full_scope_is_full(self) -> None:
        """Full profile has FULL scope."""
        profile = get_profile("full")
        assert profile.scope.value == "full"


class TestCommandDocumentation:
    """Validate that commands are documented."""

    def test_verify_py_help_works(self) -> None:
        """verify.py responds with valid help output."""
        result = subprocess.run(
            ["python", "runtime/verify.py"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=REPO_ROOT,
        )
        output = result.stdout + result.stderr
        assert "Profiles:" in output, "Should list profiles in help"
        assert "Commands:" in output, "Should list commands in help"

    def test_verify_py_status_works(self) -> None:
        """verify.py status command works."""
        result = subprocess.run(
            ["python", "runtime/verify.py", "status"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=REPO_ROOT,
        )
        output = result.stdout
        assert "Repository Status" in output, "Status command should show repo status"

    def test_verify_py_env_check_works(self) -> None:
        """verify.py env-check command works."""
        result = subprocess.run(
            ["python", "runtime/verify.py", "env-check"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"env-check failed: {result.stderr}"


class TestNoConflictingProfiles:
    """Validate profiles don't have conflicting commands."""

    def test_profiles_have_distinct_task_ids(self) -> None:
        """Task IDs are unique across all profiles."""
        all_task_ids = []
        for profile in list_profiles():
            all_task_ids.extend(profile.task_ids())

        assert len(all_task_ids) == len(
            set(all_task_ids)
        ), f"Duplicate task IDs across profiles: {[t for t in all_task_ids if all_task_ids.count(t) > 1]}"

    def test_profile_descriptions_non_empty(self) -> None:
        """All profiles have non-empty descriptions."""
        for profile in list_profiles():
            assert profile.description, f"Profile {profile.name} has empty description"
            assert (
                len(profile.description) > 10
            ), f"Profile {profile.name} description too short: {profile.description}"
