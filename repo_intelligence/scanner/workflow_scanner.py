"""Workflow scanner — discovers GitHub Actions workflows.

Scans ``.github/workflows/`` for YAML workflow files and extracts:
- Workflow name
- Triggers (on:)
- Jobs

Creates ``workflow`` nodes. Does NOT modify workflows — read-only discovery.
"""

from __future__ import annotations


from repo_intelligence.scanner.base import BaseScanner, ScanResult


class WorkflowScanner(BaseScanner):
    """Discover GitHub Actions workflows."""

    def scan(self) -> ScanResult:
        result = ScanResult()
        workflows_dir = self.repo_root / ".github" / "workflows"
        if not workflows_dir.exists():
            return result

        for yml_file in sorted(workflows_dir.glob("*.yml")):
            data = self.safe_read_yaml(yml_file)
            if data is None:
                continue

            rel = self.rel_path(yml_file, self.repo_root)
            name = data.get("name", yml_file.stem)
            triggers = self._extract_triggers(data)
            jobs = list(data.get("jobs", {}).keys())

            result.add_node(
                node_type="workflow",
                name=name,
                path=rel,
                source="filesystem:.github/workflows",
                properties={
                    "triggers": triggers,
                    "jobs": jobs,
                    "job_count": len(jobs),
                },
            )

        # Also scan .github/scripts/ if present
        scripts_dir = self.repo_root / ".github" / "scripts"
        if scripts_dir.exists():
            for script_file in sorted(scripts_dir.glob("*.sh")):
                rel = self.rel_path(script_file, self.repo_root)
                result.add_node(
                    node_type="script",
                    name=script_file.name,
                    path=rel,
                    source="filesystem:.github/scripts",
                    properties={
                        "script_type": "shell",
                    },
                )

        return result

    @staticmethod
    def _extract_triggers(data: dict) -> list[str]:
        """Extract workflow trigger names from the 'on' field."""
        on_field = data.get("on", data.get("on:", {}))
        if isinstance(on_field, str):
            return [on_field]
        if isinstance(on_field, dict):
            return list(on_field.keys())
        if isinstance(on_field, list):
            return on_field
        return []
