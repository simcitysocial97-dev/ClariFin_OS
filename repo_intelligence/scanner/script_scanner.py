"""Script scanner — discovers scripts across the repository.

Scans:
- ``scripts/`` (root-level shell scripts)
- ``backend/scripts/`` (Python scripts, including migrations)
- ``frontend/scripts/`` (TypeScript/JavaScript scripts)

Creates ``script`` nodes. Migration scripts are handled by
:class:`~repo_intelligence.scanner.migration_scanner.MigrationScanner`.
"""

from __future__ import annotations


from repo_intelligence.scanner.base import BaseScanner, ScanResult

# Script directories to scan
_SCRIPT_DIRS: list[tuple[str, str]] = [
    ("scripts", "shell"),
    ("backend/scripts", "python"),
    ("frontend/scripts", "typescript"),
]

# File extensions and their script types
_EXT_MAP: dict[str, str] = {
    ".sh": "shell",
    ".py": "python",
    ".ts": "typescript",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
}


class ScriptScanner(BaseScanner):
    """Discover scripts across the repository."""

    def scan(self) -> ScanResult:
        result = ScanResult()

        for dir_name, default_type in _SCRIPT_DIRS:
            script_dir = self.repo_root / dir_name
            if not script_dir.exists():
                continue

            for script_file in sorted(script_dir.iterdir()):
                if not script_file.is_file():
                    continue
                if script_file.name.startswith("__"):
                    continue

                ext = script_file.suffix.lower()
                script_type = _EXT_MAP.get(ext, default_type)

                # Skip migration scripts (handled by MigrationScanner)
                if "migration" in script_file.name.lower():
                    continue

                rel = self.rel_path(script_file, self.repo_root)
                result.add_node(
                    node_type="script",
                    name=script_file.name,
                    path=rel,
                    source=f"filesystem:{dir_name}",
                    properties={
                        "script_type": script_type,
                        "size_bytes": script_file.stat().st_size,
                    },
                )

        return result
