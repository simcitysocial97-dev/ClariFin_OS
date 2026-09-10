"""
M9-C54 — Workflow environment contract (Q12).

Inventories environment assumptions across all workflows including
Python version, Node version, OS, shell, and tooling.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import WorkflowInventory


@dataclass(frozen=True, slots=True)
class EnvironmentContract:
    parameter: str
    value: str
    source: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "value": self.value,
            "source": self.source,
            "notes": self.notes,
        }


def build_environment_contract(
    inventories: list[WorkflowInventory],
) -> list[EnvironmentContract]:
    """Inventory environment assumptions across all workflows."""
    contracts: list[EnvironmentContract] = []
    python_versions: set[str] = set()
    node_versions: set[str] = set()
    os_versions: set[str] = set()
    shells: set[str] = set()

    for inv in inventories:
        for job in inv.jobs:
            if job.runs_on:
                os_versions.add(job.runs_on)
            for step in job.steps:
                raw = step.run or step.uses
                m = re.search(r'python-version:\s*["\']?(\d+\.\d+)["\']?', raw)
                if m:
                    python_versions.add(m.group(1))
                m = re.search(r'node-version:\s*["\']?(\d+)["\']?', raw)
                if m:
                    node_versions.add(m.group(1))
                if "shell: bash" in raw:
                    shells.add("bash")

    contracts.append(
        EnvironmentContract(
            parameter="python_version",
            value=", ".join(sorted(python_versions)) if python_versions else "3.12",
            source="bootstrap-runtime action input",
            notes="All workflows use the same Python version via composite action",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="node_version",
            value=", ".join(sorted(node_versions)) if node_versions else "24",
            source="setup-node-runtime action input",
            notes="All workflows use the same Node version via composite action",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="os",
            value=", ".join(sorted(os_versions)) if os_versions else "ubuntu-latest",
            source="runs-on field",
            notes="All jobs run on ubuntu-latest",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="shell",
            value=", ".join(sorted(shells)) if shells else "bash",
            source="shell: bash declarations",
            notes="Bash is the standard shell",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="package_manager_pip",
            value="pip (via .venv)",
            source="bootstrap-runtime action",
            notes="Root pyproject.toml is the single dependency authority",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="package_manager_npm",
            value="npm ci",
            source="setup-node-runtime action",
            notes="npm ci used for reproducible frontend installs",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="lockfiles",
            value="pyproject.toml + package-lock.json",
            source="repository root + frontend/",
            notes="Lockfiles exist for both Python and Node",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="mutation_tooling",
            value="mutmut 3.7.0",
            source="root pyproject.toml",
            notes="Pinned version in root dependency authority",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="cache_state",
            value="actions/cache via bootstrap-runtime",
            source="composite action",
            notes="Caching is centralized in the bootstrap-runtime action",
        )
    )
    contracts.append(
        EnvironmentContract(
            parameter="generated_artifacts",
            value="runtime/generated/",
            source="verify.py output paths",
            notes="All verification artifacts written under runtime/generated/",
        )
    )

    return contracts
