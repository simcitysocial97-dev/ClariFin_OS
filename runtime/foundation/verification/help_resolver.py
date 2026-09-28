# runtime/foundation/verification/help_resolver.py
#
# M9-C56 — AI-Discoverable Capability Resolver.
#
# This module makes the entire ClariFin_OS verification infrastructure
# automatically discoverable and usable by AI agents (and humans) WITHOUT
# requiring knowledge of specific command names. Given a problem
# description, it:
#
#   1. Maps the problem to a verification capability via the C52 contract
#   2. Returns the EXACT command(s) to run
#   3. Returns the expected output schema
#   4. Returns the next logical step in the workflow
#
# This is the permanent architectural fix for the "I have all this
# infrastructure but can't use it" problem. Any AI agent that needs to
# improve test effectiveness, diagnose a failure, or understand the
# verification state should start with `verify.py help-resolve`.
#
# The resolver is built on the C52 problem-to-capability contract and the
# C51 capability graph, making it composable with the rest of the
# infrastructure.

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ═══════════════════════════════════════════════════════════════════════════════
# Problem → Capability Mapping
# ═══════════════════════════════════════════════════════════════════════════════

# Each entry maps a problem pattern to a resolution.
# The resolver uses keyword matching + the C52 capability-for contract.

PROBLEM_RESOLUTIONS: list[dict] = [
    {
        "keywords": [
            "mutation score",
            "mutation coverage",
            "kill mutant",
            "survivor",
            "improve mutation",
            "reach 80",
            "mutation threshold",
        ],
        "problem_type": "mutation_survivor",
        "primary_capability": "strengthen.capability-pipeline",
        "primary_command": "verify.py converge --component {component}",
        "supporting_commands": [
            "verify.py mutation --target {component}",
            "verify.py strengthen-survivor {survivor_id}",
            "verify.py c56-converge --component {component}",
        ],
        "description": "Improve mutation testing effectiveness by targeting surviving mutants with new tests.",
        "expected_workflow": [
            "1. DISCOVER: Load mutation survivors for the component",
            "2. CLASSIFY: Prioritize by classification (A=actionable, C=equivalent, E=production fix)",
            "3. GENERATE: Create test candidates targeting each survivor",
            "4. APPLY: Write tests additively to test files",
            "5. VALIDATE: Run focused tests, then re-measure mutation",
            "6. REPORT: Emit convergence ledger with score delta",
        ],
        "single_command": "verify.py converge --component {component} --max-survivors 20",
    },
    {
        "keywords": [
            "coverage gap",
            "improve coverage",
            "low coverage",
            "branch coverage",
            "line coverage",
            "uncovered",
            "missing tests",
        ],
        "problem_type": "coverage_gap",
        "primary_capability": "measure.coverage",
        "primary_command": "verify.py measurement coverage {scope}",
        "supporting_commands": [
            "verify.py c56-converge --component {component}",
            "verify.py generate-test --gap-id {gap_id}",
        ],
        "description": "Improve test coverage by generating tests for uncovered code paths.",
        "expected_workflow": [
            "1. MEASURE: Run coverage to identify gaps",
            "2. CLASSIFY: Determine if gaps are reachable or defensive",
            "3. GENERATE: Create test candidates for reachable gaps",
            "4. APPLY: Write tests to cover gaps",
            "5. VALIDATE: Re-measure coverage to confirm improvement",
        ],
    },
    {
        "keywords": [
            "test failure",
            "failing test",
            "diagnose",
            "failure",
            "broken test",
        ],
        "problem_type": "test_failure",
        "primary_capability": "diagnose.failure-attribution",
        "primary_command": "verify.py diagnose",
        "supporting_commands": [
            "verify.py diagnose-failures",
            "verify.py repair",
        ],
        "description": "Diagnose and fix test failures using the failure attribution pipeline.",
    },
    {
        "keywords": [
            "capability",
            "what can",
            "what should",
            "how to",
            "help",
            "available commands",
            "runtime",
            "infrastructure",
        ],
        "problem_type": "capability_discovery",
        "primary_capability": "discover.capability-inventory",
        "primary_command": "verify.py capability-inventory",
        "supporting_commands": [
            "verify.py capabilities",
            "verify.py capability-for --problem {problem}",
            "verify.py what-should-i-run {problem}",
        ],
        "description": "Discover available verification capabilities and how to use them.",
    },
    {
        "keywords": [
            "blast radius",
            "affected",
            "what changes",
            "impact",
        ],
        "problem_type": "blast_radius",
        "primary_capability": "discover.blast-radius",
        "primary_command": "verify.py blast-radius",
        "supporting_commands": [
            "verify.py affected",
        ],
        "description": "Determine the blast radius of code changes.",
    },
    {
        "keywords": [
            "certif",
            "certify",
            "threshold",
            "gate",
            "80%",
        ],
        "problem_type": "certification",
        "primary_capability": "certify.evidence-pipeline",
        "primary_command": "verify.py certify",
        "supporting_commands": [
            "verify.py c56-threshold-assessment",
            "verify.py certify-v5",
        ],
        "description": "Run certification pipeline to verify threshold achievement.",
    },
    {
        "keywords": [
            "regression",
            "broken",
            "something broke",
            "was working",
        ],
        "problem_type": "regression",
        "primary_capability": "diagnose.failure-attribution",
        "primary_command": "verify.py regression",
        "supporting_commands": [
            "verify.py diagnose",
        ],
        "description": "Investigate and fix regressions.",
    },
    {
        "keywords": [
            "environment",
            "setup",
            "install",
            "venv",
            "dependencies",
        ],
        "problem_type": "environment",
        "primary_capability": "exec.environment-check",
        "primary_command": "verify.py env-check",
        "supporting_commands": [
            "verify.py doctor",
            "verify.py deps",
        ],
        "description": "Check and fix the verification environment.",
    },
    {
        "keywords": [
            "evidence",
            "ci",
            "workflow",
            "convergence",
        ],
        "problem_type": "workflow_evidence",
        "primary_capability": "certify.evidence-pipeline",
        "primary_command": "verify.py evidence-plan",
        "supporting_commands": [
            "verify.py evidence-execute",
            "verify.py evidence-reconcile",
            "verify.py evidence-certify",
        ],
        "description": "Run the evidence pipeline for CI/workflow integration.",
    },
    {
        "keywords": [
            "forensic",
            "investigate",
            "deep dive",
            "root cause",
        ],
        "problem_type": "forensic",
        "primary_capability": "strengthen.forensic",
        "primary_command": "verify.py forensic-diagnose",
        "supporting_commands": [
            "verify.py strengthen-survivor-forensic {survivor_id}",
        ],
        "description": "Run forensic diagnosis on failures or survivors.",
    },
]


def resolve_problem(problem: str) -> list[dict]:
    """Resolve a problem description to one or more capability resolutions.

    Returns a ranked list of matching resolutions, with the most relevant first.
    """
    problem_lower = problem.lower()
    matches = []

    for resolution in PROBLEM_RESOLUTIONS:
        score = 0
        for kw in resolution["keywords"]:
            if kw in problem_lower:
                score += 1
        if score > 0:
            matches.append((score, resolution))

    # Sort by score descending
    matches.sort(key=lambda x: -x[0])
    return [r for _, r in matches]


def extract_components_from_problem(problem: str) -> list[str]:
    """Extract component names from a problem description."""
    components = []
    problem_lower = problem.lower()

    component_map = {
        "financial_events": [
            "financial_events",
            "financial events",
            "financial-events",
        ],
        "credit_card_engine": ["credit_card", "credit card", "creditcard"],
        "loan_engine": ["loan_engine", "loan engine", "loan"],
        "account_engine": ["account_engine", "account engine", "account"],
    }

    for canonical, aliases in component_map.items():
        for alias in aliases:
            if alias in problem_lower:
                components.append(canonical)
                break

    return components


def extract_survivor_id_from_problem(problem: str) -> str | None:
    """Extract a survivor ID from a problem description."""
    # Look for patterns like "survivor X" or "mutmut_NN"
    match = re.search(r"(survivor[:\s]+)([\w\.]+)", problem, re.IGNORECASE)
    if match:
        return match.group(2)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_help_resolve(argv: list[str]) -> int:
    """Resolve a problem to a verification capability + command.

    Usage: verify.py help-resolve <problem description>
    or:     verify.py help-resolve (interactive, reads from stdin)
    """
    if argv:
        problem = " ".join(argv)
    else:
        print("Enter problem description (Ctrl+D to finish):")
        problem = sys.stdin.read().strip()

    if not problem:
        print("Usage: verify.py help-resolve <problem description>", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print(
            "  verify.py help-resolve 'How do I improve mutation score?'",
            file=sys.stderr,
        )
        print(
            "  verify.py help-resolve 'mutation score is 79% need 80%'", file=sys.stderr
        )
        print(
            "  verify.py help-resolve 'coverage is low on credit_card_engine'",
            file=sys.stderr,
        )
        return 1

    print(f"\n{'='*70}")
    print("  M9-C56 CAPABILITY RESOLVER")
    print(f"  Problem: {problem}")
    print(f"{'='*70}\n")

    matches = resolve_problem(problem)

    if not matches:
        print("  No matching capability found for this problem.")
        print("\n  TIP: Try keywords like 'mutation', 'coverage', 'test failure',")
        print("       'capability', 'environment', 'certify', 'regression'.")
        print("\n  Or use: verify.py capability-inventory (list all capabilities)")
        return 0

    components = extract_components_from_problem(problem)
    survivor_id = extract_survivor_id_from_problem(problem)

    for i, match in enumerate(matches[:3], 1):
        print(f"  Resolution {i}: {match['problem_type'].upper()}")
        print(f"  {'─'*60}")
        print(f"  {match['description']}")
        print(f"\n  Primary capability: {match['primary_capability']}")

        # Format commands with extracted entities
        component = components[0] if components else "<engine_name>"

        primary_cmd = match["primary_command"].format(
            component=component,
            survivor_id=survivor_id or "<survivor_id>",
            scope=component,
            gap_id="<gap_id>",
            problem=problem,
        )
        print("\n  ┌─ SINGLE COMMAND (recommended):")
        print(f"  │  {primary_cmd}")
        print("  └─")

        print("\n  Supporting commands:")
        for cmd in match.get("supporting_commands", []):
            fmt_cmd = cmd.format(
                component=component,
                survivor_id=survivor_id or "<survivor_id>",
                scope=component,
                gap_id="<gap_id>",
                problem=problem,
            )
            print(f"    • {fmt_cmd}")

        if "single_command" in match:
            print("\n  EASIEST PATH:")
            print(f"    {match['single_command'].format(component=component)}")

        if "expected_workflow" in match:
            print("\n  Expected workflow:")
            for step in match["expected_workflow"]:
                print(f"    {step}")

        print()

    # Always show the meta hint
    print(f"  {'─'*60}")
    print("  TIP: Run the SINGLE COMMAND above to automatically solve this problem.")
    print("  The converge pipeline handles everything end-to-end.")
    print(f"{'='*70}\n")

    return 0


def cmd_what_should_i_run(argv: list[str]) -> int:
    """Determine the sequence of commands to run for a given problem.

    Usage: verify.py what-should-i-run <problem>
    """
    if not argv:
        print("Usage: verify.py what-should-i-run <problem>", file=sys.stderr)
        return 1

    problem = " ".join(argv)
    matches = resolve_problem(problem)

    if not matches:
        print("No matching workflow found. Try: verify.py help-resolve <problem>")
        return 1

    components = extract_components_from_problem(problem)
    component = components[0] if components else "<engine>"

    best = matches[0]

    print(f"\n{'='*70}")
    print("  M9-C56 WHAT SHOULD I RUN")
    print(f"  Problem: {problem}")
    print(f"{'='*70}\n")

    # Provide a JSON output for AI consumption
    output = {
        "problem": problem,
        "resolved_problem_type": best["problem_type"],
        "primary_capability": best["primary_capability"],
        "single_command": best.get("single_command", best["primary_command"]).format(
            component=component
        ),
        "command_sequence": [
            best.get("single_command", best["primary_command"]).format(
                component=component
            )
        ],
        "supporting_commands": [
            c.format(
                component=component,
                survivor_id="<survivor_id>",
                scope=component,
                gap_id="<gap_id>",
            )
            for c in best.get("supporting_commands", [])
        ],
        "description": best["description"],
    }

    print(json.dumps(output, indent=2))
    return 0


# ═══════════════════════════════════════════════════════════════════════════════
# Terminal Hints — automatically suggest next steps
# ═══════════════════════════════════════════════════════════════════════════════


def emit_next_step_hint(problem_type: str, context: dict | None = None) -> str:
    """Emit a terminal hint suggesting the next step based on what just happened.

    This is the key to making the infrastructure self-discoverable: every
    command output is followed by a hint about what to do next.
    """
    context = context or {}

    hints = {
        "mutation_run_complete": (
            "\n  ┌─ NEXT STEP ──────────────────────────────────────────┐\n"
            "  │  Mutation run complete. To automatically improve      │\n"
            "  │  the score, run:                                     │\n"
            "  │                                                      │\n"
            "  │  verify.py converge --component {component}          │\n"
            "  │                                                      │\n"
            "  │  This discovers survivors, generates tests, applies   │\n"
            "  │  them, and re-measures in one end-to-end pipeline.    │\n"
            "  └──────────────────────────────────────────────────────┘\n"
        ),
        "test_run_complete": (
            "\n  ┌─ NEXT STEP ──────────────────────────────────────────┐\n"
            "  │  Tests complete. If failures remain, diagnose with:  │\n"
            "  │                                                      │\n"
            "  │  verify.py diagnose                                  │\n"
            "  │  verify.py diagnose-failures                         │\n"
            "  └──────────────────────────────────────────────────────┘\n"
        ),
        "convergence_complete": (
            "\n  ┌─ NEXT STEP ──────────────────────────────────────────┐\n"
            "  │  Convergence run complete. Check the score with:     │\n"
            "  │                                                      │\n"
            "  │  verify.py c56-threshold-assessment                  │\n"
            "  │  verify.py mutation --target {component}             │\n"
            "  └──────────────────────────────────────────────────────┘\n"
        ),
    }

    return hints.get(problem_type, "")


if __name__ == "__main__":
    sys.exit(cmd_help_resolve(sys.argv[1:]))
