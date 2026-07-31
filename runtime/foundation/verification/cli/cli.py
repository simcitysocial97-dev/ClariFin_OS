"""
Verification Runtime CLI — Phase 6

CLI for verification planning only. No execution.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click

# Ensure repository root is in sys.path for runtime imports
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.models import (
    VerificationPlan,
    VerificationScope,
    VerificationStatus,
)
from runtime.foundation.verification.planner import plan_verification, PlanningContext
from runtime.foundation.verification.registry import VerificationRegistry
from runtime.foundation.verification.models.scope import (
    ScopeResolver,
    get_scope_resolver,
)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """ClariFin OS Verification Runtime CLI — Planning Only.

    This CLI produces verification plans. It does NOT execute tests.
    Execution is delegated to existing scripts and GitHub workflows.
    """
    pass


@cli.command()
@click.option("--file", "-f", "files", multiple=True, help="Changed file paths")
@click.option("--capability", "-c", "capabilities", multiple=True, help="Changed capabilities")
@click.option("--endpoint", "-e", "endpoints", multiple=True, help="Changed endpoints")
@click.option("--scope", "-s", type=click.Choice([s.value for s in VerificationScope]), help="Requested scope")
@click.option("--output", "-o", type=click.Path(), help="Output JSON file")
@click.option("--table", is_flag=True, help="Show human-readable table")
def plan(
    files: tuple[str, ...],
    capabilities: tuple[str, ...],
    endpoints: tuple[str, ...],
    scope: str | None,
    output: str | None,
    table: bool,
):
    """Generate a verification plan from changed files/capabilities/endpoints."""
    requested_scope = VerificationScope(scope) if scope else None

    plan = plan_verification(
        changed_files=list(files) if files else None,
        changed_capabilities=list(capabilities) if capabilities else None,
        changed_endpoints=list(endpoints) if endpoints else None,
        scope=requested_scope,
    )

    if output:
        with open(output, "w") as f:
            json.dump(plan_to_dict(plan), f, indent=2, default=str)
        click.echo(f"Plan written to {output}")
    else:
        click.echo(json.dumps(plan_to_dict(plan), indent=2, default=str))

    if table:
        print_plan_table(plan)


@cli.command()
@click.argument("scope", type=click.Choice([s.value for s in VerificationScope]))
def scope(scope: str):
    """Show verification targets for a scope."""
    requested_scope = VerificationScope(scope)
    plan = plan_verification(scope=requested_scope)
    print_plan_table(plan)


@cli.command()
@click.argument("capability")
def capability(capability: str):
    """Show verification plan for a capability."""
    plan = plan_verification(changed_capabilities=[capability])
    print_plan_table(plan)


@cli.command()
def repository():
    """Show full repository verification plan."""
    plan = plan_verification(scope=VerificationScope.REPOSITORY)
    print_plan_table(plan)


@cli.command()
def quick():
    """Show quick verification plan."""
    plan = plan_verification(scope=VerificationScope.QUICK)
    print_plan_table(plan)


@cli.command()
@click.argument("file_paths", nargs=-1)
def resolve(file_paths: tuple[str, ...]):
    """Resolve scopes for file paths and explain WHY."""
    resolver = get_scope_resolver()

    if not file_paths:
        click.echo("Usage: verify resolve FILE [FILE...]")
        return

    for file_path in file_paths:
        resolution = resolver.resolve_file(file_path)
        click.echo(f"\nFile: {file_path}")
        click.echo(f"Scopes: {', '.join(s.value for s in resolution.scopes)}")
        click.echo("Reasons:")
        for reason in resolution.reasons:
            cat = f" [{reason.category.value}]" if reason.category else ""
            mod = f" (module: {reason.module})" if reason.module else ""
            cap = f" (capability: {reason.capability})" if reason.capability else ""
            click.echo(f"  - {reason.scope.value}: {reason.reason}{cat}{mod}{cap}")

    # Summary
    all_scopes = resolver.get_affected_scopes(list(file_paths))
    all_capabilities = resolver.get_affected_capabilities(list(file_paths))
    all_modules = resolver.get_affected_modules(list(file_paths))

    click.echo(f"\nSummary:")
    click.echo(f"  Affected scopes: {', '.join(s.value for s in all_scopes)}")
    click.echo(f"  Affected capabilities: {', '.join(all_capabilities) or 'none'}")
    click.echo(f"  Affected modules: {', '.join(all_modules) or 'none'}")


@cli.command()
@click.argument("scope", type=click.Choice([s.value for s in VerificationScope]))
@click.argument("file_paths", nargs=-1)
def explain(scope: str, file_paths: tuple[str, ...]):
    """Explain why a scope is affected by given files."""
    resolver = get_scope_resolver()
    explanation = resolver.explain_scope(VerificationScope(scope), list(file_paths))
    click.echo(explanation)


@cli.command()
def scopes():
    """List all verification scopes with descriptions."""
    click.echo("Verification Scopes:")
    click.echo("=" * 50)
    for scope, desc in SCOPE_EXPLANATIONS.items():
        click.echo(f"  {scope.value:15} - {desc}")


@cli.command()
def examples():
    """Show scope resolution examples."""
    click.echo(explain_loan_engine())
    click.echo(explain_frontend_api_change())


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to verification.yaml")
def registry(config: str | None):
    """Show verification registry summary."""
    registry = VerificationRegistry(Path(config) if config else None)
    registry.load()

    click.echo("Verification Registry Summary")
    click.echo("=" * 50)

    click.echo(f"\nCategories: {len(registry._categories)}")
    for cat in registry._categories:
        click.echo(f"  - {cat.value}")

    click.echo(f"\nScopes: {len(registry._scopes)}")
    for scope in registry._scopes:
        click.echo(f"  - {scope.value}")

    click.echo(f"\nWorkflows: {len(registry._workflows)}")
    for wf in registry._workflows.values():
        click.echo(f"  - {wf.id}: {wf.name} ({wf.scope.value})")

    click.echo(f"\nScripts: {len(registry._scripts)}")
    for script in registry._scripts.values():
        click.echo(f"  - {script.id}: {script.name} ({script.scope.value})")

    click.echo(f"\nCapabilities: {len(registry._capabilities)}")
    for cap in registry._capabilities.values():
        click.echo(f"  - {cap.id}: {cap.name} ({len(cap.requirements)} requirements)")


@cli.command()
def validate():
    """Validate verification.yaml and registry."""
    registry = VerificationRegistry()
    registry.load()

    click.echo("Validation Results")
    click.echo("=" * 50)

    errors = []
    warnings = []

    # Check workflows exist
    for wf in registry._workflows.values():
        if wf.command and not Path(wf.command).exists():
            warnings.append(f"Workflow '{wf.id}': command not found: {wf.command}")
        if wf.script and not Path(wf.script).exists():
            warnings.append(f"Workflow '{wf.id}': script not found: {wf.script}")

    # Check scripts exist
    for script in registry._scripts.values():
        if not Path(script.path).exists():
            warnings.append(f"Script '{script.id}': path not found: {script.path}")

    # Check for duplicate IDs
    seen = set()
    for wf in registry._workflows:
        if wf in seen:
            errors.append(f"Duplicate workflow ID: {wf}")
        seen.add(wf)
    for script in registry._scripts:
        if script in seen:
            errors.append(f"Duplicate script ID: {script}")
        seen.add(script)
    for cap in registry._capabilities:
        if cap in seen:
            errors.append(f"Duplicate capability ID: {cap}")
        seen.add(cap)

    if errors:
        click.echo("\nErrors:", err=True)
        for err in errors:
            click.echo(f"  ERROR: {err}", err=True)

    if warnings:
        click.echo("\nWarnings:")
        for warn in warnings:
            click.echo(f"  WARN: {warn}")

    if not errors and not warnings:
        click.echo("All checks passed.")

    if errors:
        sys.exit(1)


def plan_to_dict(plan: VerificationPlan) -> dict[str, Any]:
    """Convert plan to dictionary for JSON serialization."""
    return {
        "id": plan.id,
        "name": plan.name,
        "scope": plan.scope.value,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "targets": [
            {
                "id": t.id,
                "name": t.name,
                "category": t.category.value,
                "scope": t.scope.value,
                "module": t.module,
                "capability": t.capability,
                "file_path": t.file_path,
                "function_name": t.function_name,
                "class_name": t.class_name,
                "reason": t.reason,
                "requirements": [r.id for r in t.requirements],
                "dependencies": [d.target_id for d in t.dependencies],
            }
            for t in plan.targets
        ],
        "steps": [
            {
                "id": s.id,
                "target_id": s.target.id,
                "order": s.order,
                "command": s.command,
                "workflow": s.workflow,
                "script": s.script,
                "estimated_duration_seconds": s.estimated_duration_seconds,
                "required_evidence": s.required_evidence,
                "dependencies": s.dependencies,
                "status": s.status.value,
            }
            for s in plan.steps
        ],
        "required_workflows": plan.required_workflows,
        "required_scripts": plan.required_scripts,
        "estimated_duration_seconds": plan.estimated_duration_seconds,
    }


def print_plan_table(plan: VerificationPlan) -> None:
    """Print human-readable plan table."""
    click.echo(f"\nVerification Plan: {plan.name} ({plan.id})")
    click.echo(f"Scope: {plan.scope.value}")
    click.echo(f"Created: {plan.created_at}")
    click.echo(f"Targets: {len(plan.targets)}")
    click.echo(f"Steps: {len(plan.steps)}")
    click.echo(f"Estimated Duration: {plan.estimated_duration_seconds}s")
    click.echo()

    if plan.targets:
        click.echo("Targets:")
        click.echo("-" * 100)
        click.echo(f"{'ID':<12} {'Name':<40} {'Category':<15} {'Scope':<12} {'Capability':<15} {'Module'}")
        click.echo("-" * 100)
        for t in plan.targets:
            click.echo(f"{t.id:<12} {t.name[:38]:<40} {t.category.value:<15} {t.scope.value:<12} {t.capability or '-':<15} {t.module or '-'}")

    if plan.steps:
        click.echo("\nSteps:")
        click.echo("-" * 120)
        click.echo(f"{'ID':<12} {'Order':<6} {'Target':<40} {'Command/Workflow':<40} {'Deps':<15}")
        click.echo("-" * 120)
        for s in plan.steps:
            cmd = s.command or s.workflow or s.script or "-"
            deps = ", ".join(s.dependencies) if s.dependencies else "-"
            click.echo(f"{s.id:<12} {s.order:<6} {s.target.name[:38]:<40} {cmd[:38]:<40} {deps[:13]:<15}")

    if plan.required_workflows:
        click.echo(f"\nRequired Workflows: {', '.join(plan.required_workflows)}")
    if plan.required_scripts:
        click.echo(f"Required Scripts: {', '.join(plan.required_scripts)}")


if __name__ == "__main__":
    cli()