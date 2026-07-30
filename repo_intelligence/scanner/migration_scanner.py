"""Migration scanner — discovers database migration scripts.

Scans ``backend/scripts/`` for files matching ``migration_*.py``.
Parses each migration to extract:
- Migration version number
- Description
- Database tables created or modified

Creates ``migration`` nodes and ``owns`` edges from migrations to the
database tables they create.
"""

from __future__ import annotations

import re

from repo_intelligence.scanner.base import BaseScanner, ScanResult

# Pattern: migration_002_loan_engine.py
_MIGRATION_RE = re.compile(
    r"migration_(\d+)_(.+)\.py"
)
# Pattern: CREATE TABLE tablename
_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", re.IGNORECASE
)
# Pattern: ALTER TABLE tablename
_ALTER_TABLE_RE = re.compile(
    r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(\w+)", re.IGNORECASE
)


class MigrationScanner(BaseScanner):
    """Discover database migration scripts and their table effects."""

    def scan(self) -> ScanResult:
        result = ScanResult()
        scripts_dir = self.backend_dir / "scripts"
        if not scripts_dir.exists():
            return result

        for py_file in sorted(scripts_dir.glob("migration_*.py")):
            match = _MIGRATION_RE.match(py_file.name)
            if not match:
                continue

            version = match.group(1)
            description = match.group(2).replace("_", " ").title()
            rel = self.rel_path(py_file, self.repo_root)

            content = self.safe_read(py_file)
            tables_created: list[str] = []
            tables_altered: list[str] = []

            if content:
                tables_created = _CREATE_TABLE_RE.findall(content)
                tables_altered = _ALTER_TABLE_RE.findall(content)

            result.add_node(
                node_type="migration",
                name=f"Migration {version}: {description}",
                path=rel,
                source="filesystem:backend/scripts",
                properties={
                    "version": version,
                    "description": description,
                    "tables_created": tables_created,
                    "tables_altered": tables_altered,
                },
            )

            # Edges: migration owns database tables
            for table in tables_created:
                result.add_edge(
                    source_id=f"migration:{rel}",
                    target_id=f"database_table:{table}",
                    relationship="owns",
                    confidence=0.9,
                    evidence=f"create_table:{table}",
                )
            for table in tables_altered:
                result.add_edge(
                    source_id=f"migration:{rel}",
                    target_id=f"database_table:{table}",
                    relationship="owns",
                    confidence=0.8,
                    evidence=f"alter_table:{table}",
                )

        return result
