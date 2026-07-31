"""
Validation — Phase 8

Validates verification.yaml, registry consistency, and produces structured findings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ValidationSeverity(str, Enum):
    """Validation finding severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """A validation finding."""

    code: str
    message: str
    severity: ValidationSeverity
    path: str | None = None
    line: int | None = None
    column: int | None = None
    suggestion: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        loc = ""
        if self.path:
            loc = f" ({self.path}"
            if self.line:
                loc += f":{self.line}"
            loc += ")"
        return f"[{self.severity.value.upper()}] {self.code}: {self.message}{loc}"


def verify_config(config_path: Path) -> list[ValidationFinding]:
    """Verify verification.yaml configuration."""
    import yaml

    findings = []

    if not config_path.exists():
        findings.append(ValidationFinding(
            code="CONFIG_NOT_FOUND",
            message=f"Verification config not found: {config_path}",
            severity=ValidationSeverity.ERROR,
            path=str(config_path),
        ))
        return findings

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        findings.append(ValidationFinding(
            code="CONFIG_PARSE_ERROR",
            message=f"Failed to parse YAML: {e}",
            severity=ValidationSeverity.ERROR,
            path=str(config_path),
        ))
        return findings

    # Check required fields
    if "version" not in config:
        findings.append(ValidationFinding(
            code="MISSING_VERSION",
            message="Config missing 'version' field",
            severity=ValidationSeverity.WARNING,
            path=str(config_path),
        ))

    # Check scopes
    valid_scopes = {
        "quick", "backend", "frontend", "contracts", "property",
        "mutation", "integration", "migration", "repository", "full"
    }
    if "scopes" in config:
        for scope in config["scopes"]:
            if scope not in valid_scopes:
                findings.append(ValidationFinding(
                    code="UNKNOWN_SCOPE",
                    message=f"Unknown scope in config: {scope}",
                    severity=ValidationSeverity.WARNING,
                    path=str(config_path),
                    suggestion=f"Valid scopes: {', '.join(sorted(valid_scopes))}",
                ))

    # Check workflows
    if "workflows" in config:
        for wf_id, wf_config in config["workflows"].items():
            if "scope" in wf_config and wf_config["scope"] not in valid_scopes:
                findings.append(ValidationFinding(
                    code="WORKFLOW_UNKNOWN_SCOPE",
                    message=f"Workflow '{wf_id}' references unknown scope: {wf_config['scope']}",
                    severity=ValidationSeverity.WARNING,
                    path=str(config_path),
                ))

    # Check capabilities
    if "capabilities" in config:
        for cap_id, cap_config in config["capabilities"].items():
            if "scopes" in cap_config:
                for scope in cap_config["scopes"]:
                    if scope not in valid_scopes:
                        findings.append(ValidationFinding(
                            code="CAPABILITY_UNKNOWN_SCOPE",
                            message=f"Capability '{cap_id}' references unknown scope: {scope}",
                            severity=ValidationSeverity.WARNING,
                            path=str(config_path),
                        ))

    # Check paths exist
    backend_config = config.get("backend", {})
    if "paths" in backend_config:
        for path_key, path_val in backend_config["paths"].items():
            if path_val and not Path(path_val).exists():
                findings.append(ValidationFinding(
                    code="BACKEND_PATH_NOT_FOUND",
                    message=f"Backend path '{path_key}' not found: {path_val}",
                    severity=ValidationSeverity.WARNING,
                    path=str(config_path),
                ))

    frontend_config = config.get("frontend", {})
    if "paths" in frontend_config:
        for path_key, path_val in frontend_config["paths"].items():
            if path_val and not Path(path_val).exists():
                findings.append(ValidationFinding(
                    code="FRONTEND_PATH_NOT_FOUND",
                    message=f"Frontend path '{path_key}' not found: {path_val}",
                    severity=ValidationSeverity.WARNING,
                    path=str(config_path),
                ))

    return findings


def verify_registry(registry) -> list[ValidationFinding]:
    """Verify registry consistency."""
    findings = []

    # Duplicate IDs
    workflow_ids = list(registry._workflows.keys())
    if len(workflow_ids) != len(set(workflow_ids)):
        findings.append(ValidationFinding(
            code="DUPLICATE_WORKFLOW_IDS",
            message="Duplicate workflow IDs found",
            severity=ValidationSeverity.ERROR,
        ))

    script_ids = list(registry._scripts.keys())
    if len(script_ids) != len(set(script_ids)):
        findings.append(ValidationFinding(
            code="DUPLICATE_SCRIPT_IDS",
            message="Duplicate script IDs found",
            severity=ValidationSeverity.ERROR,
        ))

    capability_ids = list(registry._capabilities.keys())
    if len(capability_ids) != len(set(capability_ids)):
        findings.append(ValidationFinding(
            code="DUPLICATE_CAPABILITY_IDS",
            message="Duplicate capability IDs found",
            severity=ValidationSeverity.ERROR,
        ))

    # Workflows reference valid scripts
    for wf in registry._workflows.values():
        if wf.script and wf.script not in registry._scripts:
            findings.append(ValidationFinding(
                code="WORKFLOW_UNKNOWN_SCRIPT",
                message=f"Workflow '{wf.id}' references unknown script '{wf.script}'",
                severity=ValidationSeverity.WARNING,
            ))

        # Check workflow scripts exist on disk
        if wf.command:
            from pathlib import Path
            if not Path(wf.command).exists():
                findings.append(ValidationFinding(
                    code="WORKFLOW_COMMAND_NOT_FOUND",
                    message=f"Workflow '{wf.id}' command not found: {wf.command}",
                    severity=ValidationSeverity.WARNING,
                ))

    # Capabilities reference valid workflows/scripts
    for cap in registry._capabilities.values():
        for wf_id in cap.workflows:
            if wf_id not in registry._workflows:
                findings.append(ValidationFinding(
                    code="CAPABILITY_UNKNOWN_WORKFLOW",
                    message=f"Capability '{cap.id}' references unknown workflow '{wf_id}'",
                    severity=ValidationSeverity.WARNING,
                ))
        for script_id in cap.scripts:
            if script_id not in registry._scripts:
                findings.append(ValidationFinding(
                    code="CAPABILITY_UNKNOWN_SCRIPT",
                    message=f"Capability '{cap.id}' references unknown script '{script_id}'",
                    severity=ValidationSeverity.WARNING,
                ))

    # Scripts exist on disk
    for script in registry._scripts.values():
        if script.path and not Path(script.path).exists():
            findings.append(ValidationFinding(
                code="SCRIPT_NOT_FOUND",
                message=f"Script '{script.id}' path not found: {script.path}",
                severity=ValidationSeverity.WARNING,
            ))

    # Check unknown scopes in workflows
    valid_scopes = {s.value for s in registry._scopes}
    for wf in registry._workflows.values():
        for scope in wf.scopes:
            if scope.value not in valid_scopes:
                findings.append(ValidationFinding(
                    code="WORKFLOW_UNKNOWN_SCOPE",
                    message=f"Workflow '{wf.id}' references unknown scope '{scope.value}'",
                    severity=ValidationSeverity.WARNING,
                ))

    return findings


def validate_all(config_path: Path | None = None) -> list[ValidationFinding]:
    """Run all validations."""
    from runtime.foundation.verification.registry import VerificationRegistry

    findings = []

    if config_path:
        findings.extend(verify_config(config_path))

    registry = VerificationRegistry(config_path)
    registry.load()
    findings.extend(verify_registry(registry))

    return findings


def print_findings(findings: list[ValidationFinding]) -> int:
    """Print findings and return exit code."""
    errors = [f for f in findings if f.severity == ValidationSeverity.ERROR]
    warnings = [f for f in findings if f.severity == ValidationSeverity.WARNING]
    infos = [f for f in findings if f.severity == ValidationSeverity.INFO]

    if errors:
        print("\nErrors:")
        for f in errors:
            print(f"  {f}")

    if warnings:
        print("\nWarnings:")
        for f in warnings:
            print(f"  {f}")

    if infos:
        print("\nInfo:")
        for f in infos:
            print(f"  {f}")

    if not findings:
        print("All checks passed.")

    return 1 if errors else 0