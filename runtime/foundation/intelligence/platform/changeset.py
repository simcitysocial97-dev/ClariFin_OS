"""Git change collection for the Engineering Intelligence Layer.

This module is the ONLY place in the intelligence layer allowed to touch git.
It answers "what changed?" at the *text* level: files, symbols, imports.

It deliberately does NOT interpret architecture. Turning a changed file into
an engine/router/capability is the job of :mod:`change`, which uses the
canonical provider. Keeping the two apart is what stops diff parsing from
degenerating into a second discovery pipeline.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]

__all__ = ["ChangedFile", "ChangeSet", "collect_changeset", "git_available"]

# Symbol definitions we can recognise deterministically in a diff hunk.
_PY_DEF = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)")
_PY_CLASS = re.compile(r"^\s*class\s+([A-Za-z_]\w*)")
_PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))")
_TS_SYMBOL = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?"
    r"(?:async\s+)?(?:function|class|const|interface|type|enum)\s+([A-Za-z_$][\w$]*)"
)
_TS_IMPORT = re.compile(r"""^\s*import\s+(?:.*?\s+from\s+)?['"]([^'"]+)['"]""")
# FastAPI-style route decorators: an API surface change signal.
_ROUTE_DECORATOR = re.compile(
    r"^\s*@\w+\.(get|post|put|patch|delete|head|options)\(\s*['\"]([^'\"]+)['\"]"
)


@dataclass(frozen=True, slots=True)
class ChangedFile:
    path: str
    status: str
    added_lines: int = 0
    removed_lines: int = 0
    added_symbols: tuple[str, ...] = ()
    removed_symbols: tuple[str, ...] = ()
    added_imports: tuple[str, ...] = ()
    removed_imports: tuple[str, ...] = ()
    added_routes: tuple[str, ...] = ()
    removed_routes: tuple[str, ...] = ()

    @property
    def changed_symbols(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.added_symbols) | set(self.removed_symbols)))

    @property
    def changed_imports(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.added_imports) | set(self.removed_imports)))

    @property
    def changed_routes(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.added_routes) | set(self.removed_routes)))

    @property
    def api_changed(self) -> bool:
        return bool(self.changed_routes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
            "changed_symbols": list(self.changed_symbols),
            "changed_imports": list(self.changed_imports),
            "changed_routes": list(self.changed_routes),
            "api_changed": self.api_changed,
        }


@dataclass(frozen=True, slots=True)
class ChangeSet:
    base: str
    head: str
    files: tuple[ChangedFile, ...] = ()
    source: str = "git"
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(f.path for f in self.files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "base": self.base,
            "head": self.head,
            "source": self.source,
            "file_count": len(self.files),
            "files": [f.to_dict() for f in self.files],
            "notes": list(self.notes),
        }


def _git(args: list[str], repo_root: Path) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=30,
        )
        return result.returncode, result.stdout
    except Exception:
        return 1, ""


def git_available(repo_root: Path | None = None) -> bool:
    code, _ = _git(["rev-parse", "--git-dir"], repo_root or REPO_ROOT)
    return code == 0


def _parse_numstat(output: str) -> dict[str, tuple[int, int]]:
    stats: dict[str, tuple[int, int]] = {}
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, path = parts
        stats[path.strip()] = (
            int(added) if added.isdigit() else 0,
            int(removed) if removed.isdigit() else 0,
        )
    return stats


def _extract(line: str, path: str) -> tuple[str | None, str | None, str | None]:
    """Return (symbol, import, route) recognised on a diff content line."""
    route = None
    match = _ROUTE_DECORATOR.match(line)
    if match:
        route = f"{match.group(1).upper()} {match.group(2)}"

    if path.endswith(".py"):
        for pattern in (_PY_DEF, _PY_CLASS):
            m = pattern.match(line)
            if m:
                return m.group(1), None, route
        m = _PY_IMPORT.match(line)
        if m:
            return None, (m.group(1) or m.group(2)), route
        return None, None, route

    if path.endswith((".ts", ".tsx", ".js", ".jsx")):
        m = _TS_IMPORT.match(line)
        if m:
            return None, m.group(1), route
        m = _TS_SYMBOL.match(line)
        if m:
            return m.group(1), None, route
    return None, None, route


def _parse_patch(patch: str) -> dict[str, dict[str, set[str]]]:
    """Parse a unified diff into per-file added/removed symbols and imports."""
    per_file: dict[str, dict[str, set[str]]] = {}
    current: str | None = None
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            current = None
            continue
        if line.startswith("+++ b/"):
            current = line[6:].strip()
            per_file.setdefault(
                current,
                {
                    "added_symbols": set(),
                    "removed_symbols": set(),
                    "added_imports": set(),
                    "removed_imports": set(),
                    "added_routes": set(),
                    "removed_routes": set(),
                },
            )
            continue
        if current is None or not line:
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line[0] not in "+-":
            continue
        polarity = "added" if line[0] == "+" else "removed"
        symbol, imp, route = _extract(line[1:], current)
        bucket = per_file[current]
        if symbol:
            bucket[f"{polarity}_symbols"].add(symbol)
        if imp:
            bucket[f"{polarity}_imports"].add(imp)
        if route:
            bucket[f"{polarity}_routes"].add(route)
    return per_file


def collect_changeset(
    base: str | None = None,
    repo_root: Path | None = None,
    paths: list[str] | None = None,
) -> ChangeSet:
    """Collect the current change set.

    ``paths`` allows callers (and tests) to inject an explicit file list,
    bypassing git entirely. This is a test seam, not a discovery path.
    """
    root = repo_root or REPO_ROOT
    notes: list[str] = []

    if paths is not None:
        files = tuple(
            ChangedFile(path=p, status="modified") for p in sorted(set(paths))
        )
        return ChangeSet(
            base="injected", head="injected", files=files, source="injected"
        )

    if not git_available(root):
        return ChangeSet(
            base="",
            head="",
            files=(),
            source="unavailable",
            notes=("git unavailable; change intelligence is empty",),
        )

    _, head_out = _git(["rev-parse", "HEAD"], root)
    head = head_out.strip() or "unknown"
    ref = base or "HEAD"

    code, name_status = _git(["diff", "--name-status", ref], root)
    if code != 0:
        return ChangeSet(base=ref, head=head, files=(), source="git",
                         notes=("git diff failed",))

    statuses: dict[str, str] = {}
    for line in name_status.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            statuses[parts[-1].strip()] = parts[0].strip()[:1]

    # Untracked files are real changes; include them as additions.
    _, untracked = _git(["ls-files", "--others", "--exclude-standard"], root)
    for line in untracked.splitlines():
        if line.strip():
            statuses.setdefault(line.strip(), "A")

    _, numstat = _git(["diff", "--numstat", ref], root)
    stats = _parse_numstat(numstat)

    _, patch = _git(["diff", "--unified=0", ref], root)
    hunks = _parse_patch(patch)

    status_names = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}
    files: list[ChangedFile] = []
    for path in sorted(statuses):
        added, removed = stats.get(path, (0, 0))
        h = hunks.get(path, {})
        files.append(
            ChangedFile(
                path=path,
                status=status_names.get(statuses[path], "modified"),
                added_lines=added,
                removed_lines=removed,
                added_symbols=tuple(sorted(h.get("added_symbols", set()))),
                removed_symbols=tuple(sorted(h.get("removed_symbols", set()))),
                added_imports=tuple(sorted(h.get("added_imports", set()))),
                removed_imports=tuple(sorted(h.get("removed_imports", set()))),
                added_routes=tuple(sorted(h.get("added_routes", set()))),
                removed_routes=tuple(sorted(h.get("removed_routes", set()))),
            )
        )

    if not files:
        notes.append("no changes detected against " + ref)

    return ChangeSet(base=ref, head=head, files=tuple(files), notes=tuple(notes))
