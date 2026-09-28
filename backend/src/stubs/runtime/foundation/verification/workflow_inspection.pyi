from __future__ import annotations

from enum import Enum
from typing import Protocol

class BoundaryClassification(str, Enum):
    LOCAL = "LOCAL"
    GITHUB_ONLY = "GITHUB_ONLY"
    ENVIRONMENT_BOUNDARY = "ENVIRONMENT_BOUNDARY"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    EXTERNAL_TOOLING = "EXTERNAL_TOOLING"
    BROWSER = "BROWSER"
    NETWORK = "NETWORK"
    HARDWARE = "HARDWARE"

class WorkflowJob(Protocol):
    job_id: str

class WorkflowRecord(Protocol):
    workflow_id: str
    name: str
    path: str
    triggers: list[str]
    jobs: list[WorkflowJob]
    commands: list[str]
    canonical_command: str | None
    local_executable: bool
    boundary_classification: BoundaryClassification
    environment_requirements: list[str]
    parity_status: str

def enumerate_workflows() -> list[WorkflowRecord]: ...
