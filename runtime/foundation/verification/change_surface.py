"""
M9-C50 — Deterministic Change Surface Discovery.

The strongest deterministic change discovery available from the existing
repository. Given a repository state, discovers:

* git working-tree changes (unstaged + untracked)
* staged changes
* committed diff/range (when applicable)
* source files
* tests
* configuration
* workflow files
* runtime/verification infrastructure
* frontend/backend boundaries
* shared modules

Every discovered surface carries a reason/source and is classified into
the C50 surface taxonomy. A changed test is NOT automatically treated
as a production capability change. A changed shared/runtime/configuration
surface is treated conservatively.

This module is additive on top of the existing C42/C47/C48/C49
architecture. It does not introduce a second change-detection system.
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ---------------------------------------------------------------------------
# Surface taxonomy (C50 — M50.3)
# ---------------------------------------------------------------------------


class SurfaceKind(str, Enum):
    """Taxonomy of change surface kinds.

    A changed test is NOT automatically a production capability change.
    A changed shared/runtime/configuration surface IS treated conservatively.
    """

    SOURCE = "source"
    TEST = "test"
    CONFIG = "config"
    WORKFLOW = "workflow"
    RUNTIME_INFRASTRUCTURE = "runtime_infrastructure"
    FRONTEND = "frontend"
    BACKEND = "backend"
    SHARED_MODULE = "shared_module"
    DOCUMENTATION = "documentation"
    GENERATED = "generated"
    UNKNOWN = "unknown"


class ChangeScope(str, Enum):
    """Where the change was discovered."""

    WORKING_TREE_UNSTAGED = "working_tree_unstaged"
    WORKING_TREE_STAGED = "working_tree_staged"
    WORKING_TREE_UNTRACKED = "working_tree_untracked"
    COMMITTED_RANGE = "committed_range"
    EXPLICIT = "explicit"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Changed surface record
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChangedSurface:
    """A single changed surface with classification and provenance."""

    path: str
    kind: SurfaceKind
    scope: ChangeScope
    is_production: bool
    is_shared_infrastructure: bool
    is_runtime_infrastructure: bool
    reason: str
    source: str  # git output, explicit input, etc.

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChangeSurfaceAnalysis:
    """Complete change surface analysis for a repository state."""

    changed_files: list[str]
    surfaces: list[ChangedSurface]
    production_surfaces: list[ChangedSurface]
    test_surfaces: list[ChangedSurface]
    config_surfaces: list[ChangedSurface]
    workflow_surfaces: list[ChangedSurface]
    runtime_infrastructure_surfaces: list[ChangedSurface]
    shared_module_surfaces: list[ChangedSurface]
    generated_surfaces: list[ChangedSurface]
    unknown_surfaces: list[ChangedSurface]
    discovery_source: ChangeScope
    repository_sha: str
    working_tree_dirty: bool
    reasons: list[str]

    def to_dict(self) -> dict:
        return {
            "changed_files": list(self.changed_files),
            "surfaces": [s.to_dict() for s in self.surfaces],
            "production_surfaces": [s.to_dict() for s in self.production_surfaces],
            "test_surfaces": [s.to_dict() for s in self.test_surfaces],
            "config_surfaces": [s.to_dict() for s in self.config_surfaces],
            "workflow_surfaces": [s.to_dict() for s in self.workflow_surfaces],
            "runtime_infrastructure_surfaces": [
                s.to_dict() for s in self.runtime_infrastructure_surfaces
            ],
            "shared_module_surfaces": [
                s.to_dict() for s in self.shared_module_surfaces
            ],
            "generated_surfaces": [s.to_dict() for s in self.generated_surfaces],
            "unknown_surfaces": [s.to_dict() for s in self.unknown_surfaces],
            "discovery_source": self.discovery_source.value,
            "repository_sha": self.repository_sha,
            "working_tree_dirty": self.working_tree_dirty,
            "reasons": list(self.reasons),
        }


# ---------------------------------------------------------------------------
# Path classification helpers
# ---------------------------------------------------------------------------


def _classify_path(path: str) -> tuple[SurfaceKind, bool, bool, bool, str]:
    """Classify a path into the C50 surface taxonomy.

    Returns: (kind, is_production, is_shared_infrastructure, is_runtime_infrastructure, reason)
    """
    norm = path.replace("\\", "/")

    # Generated artifacts — never treated as production
    if norm.startswith("backend/tests/generated/") or norm.startswith(
        "runtime/generated/"
    ):
        return (
            SurfaceKind.GENERATED,
            False,
            False,
            False,
            "Generated artifact — not a production surface",
        )

    # Test files
    if norm.startswith("backend/tests/") and not norm.startswith(
        "backend/tests/generated/"
    ):
        return (
            SurfaceKind.TEST,
            False,
            False,
            False,
            "Test file — not a production capability change",
        )
    if norm.startswith("frontend/tests/") or norm.startswith("frontend/__tests__/"):
        return (
            SurfaceKind.TEST,
            False,
            False,
            False,
            "Frontend test file — not a production capability change",
        )
    if norm.startswith("runtime/tests/"):
        return (
            SurfaceKind.TEST,
            False,
            False,
            False,
            "Runtime test file — not a production capability change",
        )
    if "/tests/" in norm and (
        norm.endswith(".test.ts")
        or norm.endswith(".test.tsx")
        or norm.endswith(".spec.ts")
        or norm.endswith(".spec.tsx")
        or norm.endswith("_test.py")
    ):
        return (
            SurfaceKind.TEST,
            False,
            False,
            False,
            "Test file (by name pattern) — not a production capability change",
        )

    # Configuration
    if norm.endswith(
        (
            ".toml",
            ".ini",
            "pyproject.toml",
            "package.json",
            "tsconfig.json",
        )
    ):
        return (
            SurfaceKind.CONFIG,
            True,  # config changes can affect production behavior
            True,  # config is shared infrastructure
            False,
            "Configuration file — conservative expansion required",
        )

    # Workflow / CI (YAML in .github/ or scripts/)
    if (norm.startswith(".github/") or norm.startswith("scripts/")) and norm.endswith(
        (".yaml", ".yml")
    ):
        return (
            SurfaceKind.WORKFLOW,
            True,
            True,
            True,
            "Workflow/CI script — affects verification infrastructure",
        )

    # General YAML config (not in .github/)
    if norm.endswith((".yaml", ".yml")):
        return (
            SurfaceKind.CONFIG,
            True,  # config changes can affect production behavior
            True,  # config is shared infrastructure
            False,
            "Configuration file — conservative expansion required",
        )

    # Runtime / verification infrastructure
    if norm.startswith("runtime/"):
        is_runtime = (
            norm.startswith("runtime/foundation/verification/")
            or norm.startswith("runtime/foundation/workspace/")
            or norm.startswith("runtime/foundation/audit/")
        )
        return (
            SurfaceKind.RUNTIME_INFRASTRUCTURE,
            True,
            True,
            is_runtime,
            "Runtime/verification infrastructure — conservative expansion required",
        )

    # Frontend
    if norm.startswith("frontend/"):
        return (
            SurfaceKind.FRONTEND,
            True,
            False,
            False,
            "Frontend source — frontend-specific verification surfaces",
        )

    # Backend
    if norm.startswith("backend/src/"):
        # Shared module detection
        is_shared = (
            "/common/" in norm
            or "/core/" in norm
            or "/models/" in norm
            or "/dtos/" in norm
            or norm.startswith("backend/src/common/")
            or norm.startswith("backend/src/core/")
        )
        if is_shared:
            return (
                SurfaceKind.SHARED_MODULE,
                True,
                True,
                False,
                "Shared backend module — conservative expansion to all dependents",
            )
        return (
            SurfaceKind.BACKEND,
            True,
            False,
            False,
            "Backend source — backend-specific verification surfaces",
        )

    # Documentation
    if norm.endswith((".md", ".rst", ".txt")):
        return (
            SurfaceKind.DOCUMENTATION,
            False,
            False,
            False,
            "Documentation — no verification impact",
        )

    return (
        SurfaceKind.UNKNOWN,
        True,  # unknown is conservatively treated as production
        False,
        False,
        "Unknown surface — conservatively treated as production (requires manual review)",
    )


# ---------------------------------------------------------------------------
# Git discovery
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def _git_list_to_files(output: str) -> list[str]:
    """Parse git output (newline-separated paths) to a list of files."""
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def discover_working_tree_changes() -> list[str]:
    """Discover all working-tree changes (unstaged + staged + untracked).

    Returns repo-relative paths.
    """
    unstaged = _git_list_to_files(_git("diff", "--name-only", "--no-renames", "HEAD"))
    staged = _git_list_to_files(_git("diff", "--cached", "--name-only", "--no-renames"))
    untracked = _git_list_to_files(_git("ls-files", "--others", "--exclude-standard"))
    # Deduplicate, preserve order
    seen: set[str] = set()
    result: list[str] = []
    for f in unstaged + staged + untracked:
        if f and f not in seen:
            seen.add(f)
            result.append(f)
    return result


def discover_staged_changes() -> list[str]:
    """Discover staged changes only."""
    return _git_list_to_files(_git("diff", "--cached", "--name-only", "--no-renames"))


def discover_unstaged_changes() -> list[str]:
    """Discover unstaged working-tree changes only."""
    return _git_list_to_files(_git("diff", "--name-only", "--no-renames", "HEAD"))


def discover_untracked_changes() -> list[str]:
    """Discover untracked files only."""
    return _git_list_to_files(_git("ls-files", "--others", "--exclude-standard"))


def discover_committed_range(base: str, head: str = "HEAD") -> list[str]:
    """Discover files changed in a committed range."""
    return _git_list_to_files(_git("diff", "--name-only", "--no-renames", base, head))


def is_git_available() -> bool:
    """Check if git is available and we're in a repo."""
    return bool(_git("rev-parse", "--is-inside-work-tree"))


def get_repository_sha() -> str:
    """Get current repository SHA (HEAD)."""
    return _git("rev-parse", "HEAD")


def is_working_tree_dirty() -> bool:
    """Check if the working tree has uncommitted changes."""
    return bool(_git("status", "--porcelain"))


# ---------------------------------------------------------------------------
# Change surface analysis
# ---------------------------------------------------------------------------


@dataclass
class ChangeSurfaceDiscovery:
    """Deterministic change surface discovery engine."""

    repo_root: Path = field(default_factory=lambda: REPO_ROOT)

    def discover(
        self,
        explicit_files: list[str] | None = None,
        base: str | None = None,
        head: str | None = None,
    ) -> ChangeSurfaceAnalysis:
        """Discover and classify all changed surfaces.

        Resolution order:
        1. If explicit_files provided → use them (scope=EXPLICIT)
        2. If base+head provided → use committed range (scope=COMMITTED_RANGE)
        3. Otherwise → use working-tree changes (scope=WORKING_TREE_*)
        """
        reasons: list[str] = []

        if explicit_files:
            files = list(explicit_files)
            scope = ChangeScope.EXPLICIT
            reasons.append(f"Using {len(files)} explicit files provided by operator")
        elif base and head:
            files = discover_committed_range(base, head)
            scope = ChangeScope.COMMITTED_RANGE
            reasons.append(f"Using committed range {base}..{head}: {len(files)} files")
        elif is_git_available():
            files = discover_working_tree_changes()
            scope = ChangeScope.WORKING_TREE_UNSTAGED
            reasons.append(
                f"Using working-tree changes (unstaged + staged + untracked): "
                f"{len(files)} files"
            )
        else:
            files = []
            scope = ChangeScope.UNKNOWN
            reasons.append("Git unavailable and no explicit files provided")

        # Classify each file
        surfaces: list[ChangedSurface] = []
        for f in files:
            kind, is_prod, is_shared, is_runtime, reason = _classify_path(f)
            surface = ChangedSurface(
                path=f,
                kind=kind,
                scope=scope,
                is_production=is_prod,
                is_shared_infrastructure=is_shared,
                is_runtime_infrastructure=is_runtime,
                reason=reason,
                source=(
                    f"git:{scope.value}"
                    if scope != ChangeScope.EXPLICIT
                    else "explicit"
                ),
            )
            surfaces.append(surface)

        # Bucket by kind
        production = [s for s in surfaces if s.is_production]
        test = [s for s in surfaces if s.kind == SurfaceKind.TEST]
        config = [s for s in surfaces if s.kind == SurfaceKind.CONFIG]
        workflow = [s for s in surfaces if s.kind == SurfaceKind.WORKFLOW]
        runtime_infra = [s for s in surfaces if s.is_runtime_infrastructure]
        shared = [s for s in surfaces if s.kind == SurfaceKind.SHARED_MODULE]
        generated = [s for s in surfaces if s.kind == SurfaceKind.GENERATED]
        unknown = [s for s in surfaces if s.kind == SurfaceKind.UNKNOWN]

        repo_sha = get_repository_sha() if is_git_available() else "no-head"
        dirty = is_working_tree_dirty() if is_git_available() else False

        return ChangeSurfaceAnalysis(
            changed_files=list(files),
            surfaces=surfaces,
            production_surfaces=production,
            test_surfaces=test,
            config_surfaces=config,
            workflow_surfaces=workflow,
            runtime_infrastructure_surfaces=runtime_infra,
            shared_module_surfaces=shared,
            generated_surfaces=generated,
            unknown_surfaces=unknown,
            discovery_source=scope,
            repository_sha=repo_sha,
            working_tree_dirty=dirty,
            reasons=reasons,
        )


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def discover_change_surfaces(
    explicit_files: list[str] | None = None,
    base: str | None = None,
    head: str | None = None,
) -> ChangeSurfaceAnalysis:
    """Convenience function to discover change surfaces."""
    return ChangeSurfaceDiscovery().discover(explicit_files, base, head)


def format_surface_analysis(analysis: ChangeSurfaceAnalysis) -> str:
    """Format a change surface analysis for human display."""
    lines = []
    lines.append("=" * 72)
    lines.append("  CHANGE SURFACE ANALYSIS (M9-C50)")
    lines.append("=" * 72)
    lines.append(f"  Discovery source: {analysis.discovery_source.value}")
    lines.append(f"  Repository SHA:   {analysis.repository_sha[:12]}")
    lines.append(f"  Working tree dirty: {analysis.working_tree_dirty}")
    lines.append(f"  Total files:      {len(analysis.changed_files)}")
    lines.append("-" * 72)

    def _bucket(name: str, items: list[ChangedSurface]) -> None:
        lines.append(f"  {name} ({len(items)}):")
        for s in items:
            lines.append(f"    • {s.path}")
            lines.append(f"        kind={s.kind.value}  reason={s.reason}")

    _bucket("PRODUCTION", analysis.production_surfaces)
    _bucket("TEST", analysis.test_surfaces)
    _bucket("CONFIG", analysis.config_surfaces)
    _bucket("WORKFLOW/CI", analysis.workflow_surfaces)
    _bucket("RUNTIME INFRASTRUCTURE", analysis.runtime_infrastructure_surfaces)
    _bucket("SHARED MODULES", analysis.shared_module_surfaces)
    _bucket("GENERATED", analysis.generated_surfaces)
    _bucket("UNKNOWN", analysis.unknown_surfaces)

    lines.append("-" * 72)
    lines.append("  REASONS:")
    for r in analysis.reasons:
        lines.append(f"    • {r}")
    lines.append("=" * 72)
    return "\n".join(lines)
