# runtime/foundation/verification/cli_governance.py
#
# M9-C48 G1 — CLI surface consolidation (GAP-014).
#
# Statically classifies every command dispatched by runtime/verify.py into
# one of the M9-C47 categories:
#
#   CANONICAL        — primary, production entrypoint.
#   ALIAS            — secondary name for an existing canonical command.
#   COMPATIBILITY    — retained for backward compatibility; do not use in
#                      new automation.
#   INTERNAL         — used by framework internals; not for operator use.
#   LEGACY           — historical, no longer documented.
#   DUPLICATE        — competes with another command for the same operation.
#   UNREACHABLE      — dead dispatch.
#
# The classifier parses verify.py for `if command == "..."` patterns and
# applies a curated policy table. The result is persisted as evidence.

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

CLASSES: tuple[str, ...] = (
    "CANONICAL",
    "ALIAS",
    "COMPATIBILITY",
    "INTERNAL",
    "LEGACY",
    "DUPLICATE",
    "UNREACHABLE",
)


# Policy table: command → (class, canonical_target, rationale).
# Commands not listed default to UNREACHABLE.
POLICY: dict[str, tuple[str, str, str]] = {
    # Mutation / coverage / measurement — canonical
    "mutation": ("CANONICAL", "", "canonical mutation entrypoint"),
    "measurement-truth": ("CANONICAL", "", "measurement truth CLI"),
    "measurement": ("CANONICAL", "", "measurement subcommands (coverage)"),
    # Verification orchestration
    "execute": ("CANONICAL", "", "executor pipeline"),
    "execution-plan": ("CANONICAL", "", "build execution plan"),
    "execution-status": ("CANONICAL", "", "show most recent report"),
    "execution-report": ("CANONICAL", "", "emit JSON report"),
    "enforce": ("CANONICAL", "", "execution enforcement boundary"),
    "evidence-plan": ("CANONICAL", "", "evidence plan"),
    "evidence-execute": ("CANONICAL", "", "evidence execute"),
    "evidence-reconcile": ("CANONICAL", "", "evidence reconcile"),
    "evidence-certify": ("CANONICAL", "", "evidence certify"),
    "evidence-integrity": ("CANONICAL", "", "evidence integrity"),
    "verification-contract": ("CANONICAL", "", "verification contract"),
    # Capabilities
    "capabilities": ("CANONICAL", "", "list capabilities"),
    "capability-for": ("CANONICAL", "", "resolve capability"),
    "capability-graph": ("CANONICAL", "", "capability graph"),
    "capability-inventory": ("CANONICAL", "", "capability inventory"),
    "control-plane-plan": ("CANONICAL", "", "control-plane plan"),
    "resolve-capabilities": ("CANONICAL", "", "resolve capabilities"),
    "bypass-audit": ("CANONICAL", "", "bypass audit"),
    "bypass-enforcement": ("CANONICAL", "", "bypass enforcement"),
    "latent-audit": ("CANONICAL", "", "latent capability audit"),
    "config-authority": ("CANONICAL", "", "configuration authority"),
    "config-authority-verify": ("CANONICAL", "", "configuration authority verify"),
    "pipeline-enforcement": ("CANONICAL", "", "pipeline enforcement"),
    # Mutation inventory / intel / forensic
    "mutation-inventory": ("CANONICAL", "", "mutation inventory"),
    "mutation-intel": ("CANONICAL", "", "survivor intel"),
    "forensic-diagnose": ("INTERNAL", "", "forensic diagnose (diagnostic)"),
    "forensic-report": ("INTERNAL", "", "forensic report (diagnostic)"),
    # Strengthening
    "strengthen-capability": ("CANONICAL", "", "strengthen capability"),
    "strengthen-survivor": ("CANONICAL", "", "strengthen survivor (canonical)"),
    "strengthen-survivor-forensic": ("INTERNAL", "", "low-level forensic variant"),
    "strengthen-analyze": ("CANONICAL", "", "strengthen analyze"),
    "strengthen-discover": ("CANONICAL", "", "strengthen discover"),
    "strengthen-propose": ("CANONICAL", "", "strengthen propose"),
    "strengthen-validate": ("CANONICAL", "", "strengthen validate"),
    "strengthen-report": ("CANONICAL", "", "strengthen report"),
    "strengthening-integration": ("CANONICAL", "", "strengthening integration"),
    "cross-capability-impact": ("CANONICAL", "", "cross-capability impact"),
    "efficiency": ("CANONICAL", "", "control-plane efficiency"),
    "regression": ("CANONICAL", "", "regression"),
    "certify": ("CANONICAL", "", "certification"),
    # C53 / C56
    "generate-test": ("CANONICAL", "", "generation engine"),
    "c53-scenarios": ("INTERNAL", "", "C53 scenarios"),
    "c53-certify": ("INTERNAL", "", "C53 certification"),
    "converge": ("CANONICAL", "", "autonomous convergence"),
    "convergence-status": ("CANONICAL", "", "C56 status"),
    "coverage-analysis": ("CANONICAL", "", "C56 coverage"),
    "mutation-analysis": ("CANONICAL", "", "C56 mutation"),
    "gap-analysis": ("CANONICAL", "", "C56 gap"),
    "convergence-plan": ("CANONICAL", "", "C56 plan"),
    "threshold-assessment": ("CANONICAL", "", "C56 threshold"),
    # Help / diagnostic
    "help-resolve": ("CANONICAL", "", "capability resolver for AI agents"),
    "what-should-i-run": ("CANONICAL", "", "what-should-i-run"),
    "blast-radius": ("CANONICAL", "", "blast radius"),
    # Environment
    "env-check": ("CANONICAL", "", "env check"),
    "env-contract": ("CANONICAL", "", "env contract"),
    # Scenarios
    "scenarios": ("CANONICAL", "", "real-repo scenarios"),
    # API contracts
    "api-contracts": ("CANONICAL", "", "api contract gate"),
    "contract-governance": ("CANONICAL", "", "contract governance"),
    "deep-contract": ("CANONICAL", "", "deep contract"),
    # Certify versions
    "certify-v4": ("COMPATIBILITY", "", "v4 retained for compat"),
    "certify-v5": ("COMPATIBILITY", "", "v5 retained for compat"),
    # Diagnostic / internal
    "ci-doctor": ("INTERNAL", "", "CI doctor"),
    "diagnose": ("INTERNAL", "", "diagnostic"),
    "diagnose-failures": ("INTERNAL", "", "diagnose failures"),
    "plan": ("INTERNAL", "", "diagnostic plan"),
    "reconcile": ("INTERNAL", "", "diagnostic reconcile"),
    "exec-evidence": ("INTERNAL", "", "exec evidence diagnostic"),
    "local-gate": ("INTERNAL", "", "local gate diagnostic"),
    "affected": ("INTERNAL", "", "affected diagnostic"),
    "repair": ("INTERNAL", "", "repair diagnostic"),
    "risk": ("INTERNAL", "", "risk diagnostic"),
    "integrity": ("INTERNAL", "", "integrity diagnostic"),
    "knowledge": ("INTERNAL", "", "knowledge subcommands"),
    "dashboard": ("INTERNAL", "", "dashboard diagnostic"),
    "intelligence": ("INTERNAL", "", "intelligence diagnostic"),
    "intelligence-audit": ("INTERNAL", "", "intelligence audit"),
    "audit": ("INTERNAL", "", "audit diagnostic"),
    "measurement-truth-report": ("INTERNAL", "", "measurement truth report"),
    # Status
    "status": ("CANONICAL", "", "platform status"),
    "metrics": ("CANONICAL", "", "platform metrics"),
    "history": ("CANONICAL", "", "platform history"),
    "deps": ("CANONICAL", "", "platform deps"),
    "verify-status": ("CANONICAL", "", "platform verify-status"),
    "doctor": ("INTERNAL", "", "doctor diagnostic"),
    "health": ("INTERNAL", "", "health diagnostic"),
    "analytics": ("INTERNAL", "", "analytics diagnostic"),
}


@dataclass(frozen=True, slots=True)
class Classification:
    command: str
    classification: str
    canonical_target: str
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ClassificationReport:
    classifications: tuple[Classification, ...]
    total: int
    by_class: dict[str, int]
    generated_at: str
    schema: str = "m9-c48/cli-governance@1"

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "total": self.total,
            "by_class": self.by_class,
            "classifications": [c.to_dict() for c in self.classifications],
        }


_COMMAND_RE = re.compile(r'if command\s*==\s*"([^"]+)"')

# M9-C49: Also scan the canonical control plane facade for canonical operations
_CANONICAL_OP_RE = re.compile(r"CanonicalOperation\.\w+\s*=\s*\"(\w+)\"")
_MIGRATION_KEY_RE = re.compile(r'^\s*"([^"]+)":\s*\(', re.MULTILINE)


def extract_commands(verify_path: str | Path = "runtime/verify.py") -> list[str]:
    """Extract command names from verify.py and the canonical control plane.

    M9-C49: verify.py is now a thin shim that delegates to the canonical
    control plane facade. Commands are sourced from:
    1. Legacy verify.py if present (deprecated path)
    2. Canonical CLI surface (canonical_control_plane.py)
    3. Migration map (canonical_control_plane.py)
    """
    commands: set[str] = set()

    # Scan legacy verify.py for `if command == "..."` patterns
    p = Path(verify_path)
    if p.exists():
        text = p.read_text()
        commands.update(_COMMAND_RE.findall(text))

    # Scan canonical control plane for canonical operations
    canonical_path = Path(__file__).parent / "canonical_control_plane.py"
    if canonical_path.exists():
        canonical_text = canonical_path.read_text()
        # Add canonical operations
        for match in _CANONICAL_OP_RE.finditer(canonical_text):
            commands.add(match.group(1))
        # Add migration map keys (legacy commands)
        for match in _MIGRATION_KEY_RE.finditer(canonical_text):
            commands.add(match.group(1))

    return sorted(commands)


def classify_commands(
    commands: list[str] | None = None,
    verify_path: str | Path = "runtime/verify.py",
) -> ClassificationReport:
    if commands is None:
        commands = extract_commands(verify_path)
    classifications: list[Classification] = []
    for cmd in commands:
        if cmd in POLICY:
            klass, target, rationale = POLICY[cmd]
        else:
            klass, target, rationale = ("UNREACHABLE", "", "not classified by policy")
        classifications.append(
            Classification(
                command=cmd,
                classification=klass,
                canonical_target=target,
                rationale=rationale,
            )
        )
    by_class: dict[str, int] = {}
    for c in classifications:
        by_class[c.classification] = by_class.get(c.classification, 0) + 1
    return ClassificationReport(
        classifications=tuple(classifications),
        total=len(classifications),
        by_class=by_class,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


__all__ = [
    "CLASSES",
    "POLICY",
    "Classification",
    "ClassificationReport",
    "extract_commands",
    "classify_commands",
]
