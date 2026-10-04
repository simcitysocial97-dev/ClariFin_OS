"""
M9-C49 — Verification Execution Orchestration.

Turns the C48 control-plane plan into an *executable, observable, deterministic*
verification pipeline. The orchestrator is the bridge from "what should I run?"
(C48) to "run it, observe it, decide what happens next, stop when defensible".

Design contract (M9-C49):

* The orchestrator consumes the C48 ControlPlanePlan; it never independently
  re-discovers which verifications to run. The capability graph remains the
  controlling abstraction.
* Same repository state + same control-plane input → same plan. Plan and task
  identity are content-derived; the generated-at timestamp is excluded from
  every fingerprint.
* Execution is observable. Every task produces a structured TaskExecutionRecord
  that records the command, capabilities served, start/end, exit code, completion
  state, produced artifacts, optional measurement truth, and next action.
* Stopping rules (Section 6) are deterministic:
    - mandatory tasks all PASS/REUSED → skip escalation; declare final decision.
    - any mandatory FAILED → run declared diagnostic; do not auto-execute
      escalation commands from the planner; decision is DIAGNOSTIC.
    - TIMEOUT / INFRASTRUCTURE / SCOPE / CONFIGURATION / CERTIFICATION failures
      never convert to PASS.
    - AUTHORIZATION_REQUIRED tasks (e.g. targeted mutation campaigns) stop at
      the human-authorization boundary unless explicitly authorized.
* Mutation execution is subordinate to orchestration. A targeted mutation is one
  capability among many; full campaigns require explicit authorization. The
  orchestrator reuses C45/C47 durable survivor intelligence and the native
  mutmut runner — never transient mutmut workspaces as evidence.
* Fingerprints are validated before execution: if the live repository state no
  longer matches the plan's captured fingerprint, the orchestrator refuses to
  run (decision: VALIDATION_BLOCKED) and the operator must re-plan.

This module is additive — it consumes the C48 planner, control plane,
measurement-truth, strengthening, and command-inventory modules without
introducing a parallel registry, evidence store, or capability system.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# C49 generated evidence root.
GENERATED_ROOT = REPO_ROOT / "runtime" / "generated" / "m9-c49"
GENERATED_ROOT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Completion state / failure stage / final decision (closed taxonomies)
# ---------------------------------------------------------------------------


class CompletionState(str, Enum):
    """Per-task completion state. Closed vocabulary, never converted to PASS."""

    PASS = "pass"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INFRASTRUCTURE = "infrastructure"
    EVIDENCE = "evidence"
    SCOPE = "scope"
    CONFIGURATION = "configuration"
    CERTIFICATION = "certification"
    AUTHORIZATION_REQUIRED = "authorization_required"
    REUSED = "reused"
    SKIPPED = "skipped"  # sufficiency: minimum verification already satisfied


# States that mean "the run is observably not a pass"
NON_PASS_STATES: frozenset[CompletionState] = frozenset(
    {
        CompletionState.FAILED,
        CompletionState.TIMEOUT,
        CompletionState.INFRASTRUCTURE,
        CompletionState.EVIDENCE,
        CompletionState.SCOPE,
        CompletionState.CONFIGURATION,
        CompletionState.CERTIFICATION,
        CompletionState.AUTHORIZATION_REQUIRED,
    }
)

PASSING_STATES: frozenset[CompletionState] = frozenset(
    {CompletionState.PASS, CompletionState.REUSED, CompletionState.SKIPPED}
)


#: The budget a mutation revalidation task declares in an execution plan.
#:
#: M10-R3 (C). This is the *declared* budget and it is not the budget that is
#: enforced: ``mutation_runner.DEFAULT_RUNTIME["target"]`` is 4200s. The two differed
#: by 3.5x and neither was recorded, so the runtime could not tell a campaign that hit
#: its own timeout from one the CI runner killed, and a workflow sizing
#: ``timeout-minutes`` from the declared value was sizing it from a number that does
#: not exist.
#:
#: Both values are now recorded on every mutation result
#: (``declared_timeout_seconds`` / ``enforced_timeout_seconds``) so the discrepancy is
#: visible in the evidence. Collapsing them into one authority is the transport work in
#: Checkpoint D; what this constant guarantees is that there is exactly *one* declared
#: value, greppable, rather than a literal repeated at two construction sites.
DECLARED_MUTATION_TIMEOUT_SECONDS = 1200


class FailureStage(str, Enum):
    """Diagnostic classification of a non-pass task outcome (Section 11)."""

    TEST_FAILURE = "test_failure"
    ASSERTION_FAILURE = "assertion_failure"
    CODE_DEFECT = "code_defect"
    CONFIGURATION_FAILURE = "configuration_failure"
    TOOLING_FAILURE = "tooling_failure"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    TIMEOUT = "timeout"
    INVALID_SCOPE = "invalid_scope"
    MISSING_EVIDENCE = "missing_evidence"
    STALE_EVIDENCE = "stale_evidence"
    AUTHORIZATION_REQUIRED = "authorization_required"
    NONE = "none"


class FinalDecision(str, Enum):
    """Pipeline-level decision (Section 6)."""

    CERTIFIED = "certified"
    NOT_CERTIFIABLE = "not_certifiable"
    DIAGNOSTIC = "diagnostic"
    AWAITING_AUTHORIZATION = "awaiting_authorization"
    INFRASTRUCTURE_BLOCKED = "infrastructure_blocked"
    TIMEOUT_BLOCKED = "timeout_blocked"
    VALIDATION_BLOCKED = "validation_blocked"


class TaskOrigin(str, Enum):
    """Origin classification for a task (transparency over why a task is in
    the plan)."""

    CONTROL_PLANE = "control_plane"
    REVALIDATION = "revalidation"  # injected by C49 because a measurement
    # record is stale/missing for a directly-affected capability


# ---------------------------------------------------------------------------
# Repository fingerprint (deterministic, never timestamp-derived)
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return out.stdout.strip()
    except Exception:
        return ""


_PYTEST_FAILURE_LINE = re.compile(r"^(FAILED|ERROR)\s+(\S+)", re.MULTILINE)
_PYTEST_TIMEOUT_MARKER = "from pytest-timeout"
_PYTEST_SUMMARY = re.compile(
    r"^(?:(\d+) failed)?(?:,?\s*(\d+) passed)?(?:,?\s*(\d+) skipped)?"
    r"(?:,?\s*(\d+) error)?(?:,?\s*(\d+) xfailed)?"
    r"(?:,?\s*(\d+) xpassed)?.*?in\s+(\d+\.?\d*)s",
    re.MULTILINE,
)


# M10-R2: the process-execution worker and its diagnosis vocabulary now live in
# `parallel_executor`, which is the single execution core both call paths use. These
# names remain bound here because they are referenced throughout this module and by
# external readers; the implementations are the ones in parallel_executor, so there is
# exactly one streaming tee, one process-group kill, one termination classifier and one
# pytest-outcome summariser in the repository. Defining a second copy here is precisely
# the divergence this milestone exists to remove.
from runtime.foundation.verification.parallel_executor import (  # noqa: E402
    classify_termination as _classify_termination,
)
from runtime.foundation.verification.parallel_executor import (  # noqa: E402
    execute_tasks_in_parallel,
    run_streaming_command,
)
from runtime.foundation.verification.parallel_executor import (  # noqa: E402
    summarise_pytest_outcome as _summarise_pytest_outcome,
)

_PYTEST_RE = re.compile(_PYTEST_SUMMARY.pattern, re.MULTILINE)


def _hash_file(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
    except OSError:
        return ""


def _hash_tree(working_dir: Path) -> str:
    if not working_dir.exists():
        return ""
    h = hashlib.sha256()
    for f in sorted(working_dir.rglob("*.py")):
        if any(part.startswith(".") for part in f.parts):
            continue
        rel = str(f.relative_to(working_dir))
        h.update(rel.encode("utf-8"))
        try:
            h.update(f.read_bytes())
        except OSError:
            h.update(b"<unreadable>")
    return h.hexdigest()


def _hash_toolchain() -> str:
    """Hash the canonical toolchain versions (mutmut, pytest, python)."""
    try:
        from runtime.foundation.verification.env import resolve_environment

        env = resolve_environment()
        parts = [
            env.python.version or "",
            env.pytest.version or "",
            env.mutmut.version or "",
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    except Exception:
        return ""


@dataclass(frozen=True, slots=True)
class RepositoryFingerprint:
    """A deterministic, content-derived fingerprint of the repository state."""

    repository_sha: str
    working_tree_hash: str
    config_hash: str
    toolchain_hash: str
    fingerprint: str

    @classmethod
    def capture(cls) -> RepositoryFingerprint:
        repo_sha = _git("rev-parse", "HEAD")
        if not repo_sha:
            # fallback: working-tree hash when no HEAD is available
            repo_sha = "no-head"
        tree = _hash_tree(REPO_ROOT / "backend" / "src")
        config_paths = [
            REPO_ROOT / "backend" / "pyproject.toml",
            REPO_ROOT / "pyproject.toml",
        ]
        config_h = hashlib.sha256()
        for p in config_paths:
            content = _hash_file(p)
            config_h.update(str(p.relative_to(REPO_ROOT)).encode())
            config_h.update(content.encode())
        config_hash = config_h.hexdigest()
        tool = _hash_toolchain()
        composite = hashlib.sha256(
            "|".join([repo_sha, tree, config_hash, tool]).encode("utf-8")
        ).hexdigest()
        return cls(
            repository_sha=repo_sha,
            working_tree_hash=tree,
            config_hash=config_hash,
            toolchain_hash=tool,
            fingerprint=composite,
        )

    def matches(self, other: RepositoryFingerprint) -> bool:
        return self.fingerprint == other.fingerprint

    def to_dict(self) -> dict:
        return {
            "repository_sha": self.repository_sha,
            "working_tree_hash": self.working_tree_hash,
            "config_hash": self.config_hash,
            "toolchain_hash": self.toolchain_hash,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RepositoryFingerprint:
        return cls(
            repository_sha=d.get("repository_sha", ""),
            working_tree_hash=d.get("working_tree_hash", ""),
            config_hash=d.get("config_hash", ""),
            toolchain_hash=d.get("toolchain_hash", ""),
            fingerprint=d.get("fingerprint", ""),
        )


# ---------------------------------------------------------------------------
# Environment requirements (M10-R3 / B1)
#
# ONE field, THREE validated forms, resolved BEFORE any spawn.
#
# History, because it explains the shape. Two fields used to mean "what this
# obligation needs": ``ExecutionTaskSpec.prerequisites`` (repository paths, and
# only paths) and ``ExecutableVerificationTask.required_environment`` (tools).
# The second was declared, populated 25 times, serialised, and **read by nothing
# outside its own ``to_dict()``** -- and it lived on a class that no execution
# path instantiates. ``verify_prerequisites`` read the first field, and then
# *skipped* five of its values (``.venv``, ``git``, ``mutmut==3.7.0``,
# ``pytest``, ``coverage``) outright, so it never checked a tool or a version.
#
# The consolidation is therefore not "add a variable axis". It is: one field,
# ``required_environment``, on the one class that actually executes, with a
# resolver that makes all three forms real. There is no second representation to
# drift.
#
# Forms (syntactically distinct, so a requirement is never ambiguous):
#
#   ".venv"                          PATH     repo-relative path must exist
#   "pytest"                         TOOL     resolvable, .venv/bin first
#   "mutmut==3.7.0"                  TOOL     resolvable AND version must match
#   "FINANCE_DB_PATH"                VARIABLE must be present in the child env
#   "PLAYWRIGHT_PROJECT=chromium"    VARIABLE present AND equal to the value
#   "FINANCE_DB_PATH=@workspace/x"   VARIABLE value resolved from provenance
#
# The resolver is deliberately not a template engine. Exactly six placeholders
# are substitutable, they come from :class:`ExecutionContext`, and an unknown
# ``@token`` is a hard error rather than a literal -- a silently unexpanded
# ``@workspace`` in a CI leg would be indistinguishable from a correct value.
# ---------------------------------------------------------------------------

#: The complete, closed set of substitutable placeholders.
PLACEHOLDER_TOKENS: tuple[str, ...] = (
    "workspace",
    "leg",
    "shard",
    "shard_count",
    "plan_id",
    "execution_id",
)

_REQUIREMENT_FORM_PATH = "path"
_REQUIREMENT_FORM_TOOL = "tool"
_REQUIREMENT_FORM_TOOL_VERSION = "tool_version"
_REQUIREMENT_FORM_VARIABLE = "variable"


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """The provenance an environment requirement may be resolved against.

    This is what makes one declaration yield the correct value in a CI shard leg,
    in a local reproduction, and on a laptop: the *requirement* is declared once
    and the *value* is supplied by whoever is executing. It is also the reason
    local and CI execution can be byte-identical rather than merely similar.
    """

    workspace: str = str(REPO_ROOT)
    leg: str = ""
    shard: int | None = None
    shard_count: int | None = None
    plan_id: str = ""
    execution_id: str = ""

    def placeholder_value(self, token: str) -> str:
        """Return the value for *token*, or raise ``KeyError`` if unknown."""
        match token:
            case "workspace":
                return self.workspace
            case "leg":
                return self.leg
            case "shard":
                return "" if self.shard is None else str(self.shard)
            case "shard_count":
                return "" if self.shard_count is None else str(self.shard_count)
            case "plan_id":
                return self.plan_id
            case "execution_id":
                return self.execution_id
            case _:
                raise KeyError(token)


@dataclass(frozen=True, slots=True)
class RequirementFailure:
    """One unmet environment requirement, named precisely enough to act on."""

    task_id: str
    form: str
    requirement: str
    detail: str

    def render(self) -> str:
        return f"{self.task_id}: [{self.form}] {self.requirement} — {self.detail}"


class RequirementSyntaxError(ValueError):
    """A requirement string could not be parsed. Raised, never ignored."""


def _resolve_placeholders(value: str, ctx: ExecutionContext) -> str:
    """Substitute ``@token`` from *ctx*. Unknown tokens raise.

    Only ``@``-prefixed whole tokens are substituted. ``user@host`` and a path
    containing ``@`` are therefore left alone, which is why the substitution
    requires the ``@`` to introduce a known token.
    """
    out: list[str] = []
    idx = 0
    while idx < len(value):
        at = value.find("@", idx)
        if at == -1:
            out.append(value[idx:])
            break
        out.append(value[idx:at])
        tail = value[at + 1 :]
        matched = next(
            (t for t in PLACEHOLDER_TOKENS if tail.startswith(t)), None
        )
        if matched is None:
            raise RequirementSyntaxError(
                f"unknown placeholder in {value!r}: '@{tail[:24]}' is not one of "
                + ", ".join(f"@{t}" for t in PLACEHOLDER_TOKENS)
            )
        # Reject a partial-token match such as ``@shard_count`` matching ``@shard``.
        after = tail[len(matched) :]
        if after and (after[0].isalnum() or after[0] == "_"):
            raise RequirementSyntaxError(
                f"unknown placeholder in {value!r}: '@{matched}' must be followed by "
                "a non-identifier character"
            )
        out.append(ctx.placeholder_value(matched))
        idx = at + 1 + len(matched)
    return "".join(out)


def _find_tool(name: str) -> Path | None:
    """Resolve *name* to an executable, preferring the canonical ``.venv``.

    ``.venv`` first is not a preference: ``AGENTS.md`` makes the repository-root
    virtualenv the single sanctioned environment, and a bare ``pytest`` resolved
    off ``PATH`` can be a different interpreter's.
    """
    candidate = REPO_ROOT / ".venv" / "bin" / name
    if candidate.exists():
        return candidate
    import shutil

    found = shutil.which(name)
    return Path(found) if found else None


def _tool_version_of(path: Path) -> str:
    """Best-effort version read for an executable.

    Installed-distribution metadata is tried first, and ``--version`` second.
    That order is not cosmetic: ``mutmut --version`` raises in this repository
    (its ``__main__`` imports ``mutmut.utils.safe_setproctitle``, which fails to
    import), so a ``--version``-only probe reports *any* pinned tool as a version
    mismatch — turning a working environment into a false prerequisite failure.
    The subprocess remains as the fallback for tools that are not installed
    distributions (shell scripts, system binaries).
    """
    import importlib.metadata as _md

    name = path.name
    for candidate in (name, name.removesuffix(".exe")):
        try:
            return _md.version(candidate)
        except (_md.PackageNotFoundError, ValueError):
            continue

    import subprocess as _sp

    try:
        proc = _sp.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, _sp.SubprocessError):
        return ""
    output = (proc.stdout or proc.stderr or "").strip()
    return output.splitlines()[0] if output else ""


_FORM_PREFIX_TOOL = "tool"
_FORM_PREFIX_PATH = "path"
_FORM_PREFIX_VARIABLE = "env"


def _classify_bare(subject: str) -> str:
    """Infer a requirement's form from a bare (unprefixed) subject.

    The inference is deliberately narrow and total, because a bare name is the
    only genuinely ambiguous form and an ambiguous requirement is an unenforceable
    one. Any author who does not agree with the inference can write the explicit
    prefix instead — ``tool:``, ``path:`` or ``env:`` — and the prefix always
    wins.

    * contains ``/``              → PATH   (``.venv``, ``backend/pyproject.toml``)
    * starts with ``.``           → PATH   (``.venv``, ``.git``)
    * SHOUTING_SNAKE              → VARIABLE (``FINANCE_DB_PATH``)
    * anything else               → TOOL   (``pytest``, ``coverage``, ``git``)
    """
    if "/" in subject or subject.startswith("."):
        return _REQUIREMENT_FORM_PATH
    if subject.replace("_", "").isupper() and subject.upper() == subject:
        return _REQUIREMENT_FORM_VARIABLE
    return _REQUIREMENT_FORM_TOOL


def _parse_requirement(raw: str) -> tuple[str, str, str]:
    """Parse one requirement into ``(form, subject, expected_value)``.

    Accepted spellings::

        ".venv"                       PATH       inferred
        "backend/pyproject.toml"      PATH       inferred
        "pytest"                      TOOL       inferred
        "mutmut==3.7.0"               TOOL       inferred (version pinned)
        "FINANCE_DB_PATH"             VARIABLE   inferred (must be set)
        "PLAYWRIGHT_PROJECT=chromium" VARIABLE   inferred (must equal)
        "tool:mutmut==3.7.0"          TOOL       explicit
        "path:.github/scripts/x.sh"   PATH       explicit
        "env:FINANCE_DB_PATH"         VARIABLE   explicit
        "env:FOO=@workspace/bar"      VARIABLE   explicit, ``@token`` value

    Note ``==`` is tested *before* ``=``: ``mutmut==3.7.0`` is a pinned tool, not
    a variable named ``mutmut`` whose value is ``=3.7.0``.
    """
    if not raw or not raw.strip():
        raise RequirementSyntaxError("empty requirement")
    text = raw.strip()

    forced: str | None = None
    for prefix, form in (
        (f"{_FORM_PREFIX_TOOL}:", _REQUIREMENT_FORM_TOOL),
        (f"{_FORM_PREFIX_PATH}:", _REQUIREMENT_FORM_PATH),
        (f"{_FORM_PREFIX_VARIABLE}:", _REQUIREMENT_FORM_VARIABLE),
    ):
        if text.startswith(prefix):
            forced = form
            text = text[len(prefix) :].strip()
            break
    if not text:
        raise RequirementSyntaxError(f"requirement {raw!r} has an empty subject")

    if "==" in text:
        name, _, version = text.partition("==")
        name, version = name.strip(), version.strip()
        if not name:
            raise RequirementSyntaxError(f"requirement {raw!r} has an empty tool name")
        form = _REQUIREMENT_FORM_TOOL_VERSION if forced in (None, _REQUIREMENT_FORM_TOOL) else forced
        return form, name, version

    if "=" in text:
        name, _, value = text.partition("=")
        name, value = name.strip(), value.strip()
        if not name:
            raise RequirementSyntaxError(
                f"requirement {raw!r} has an empty variable name"
            )
        if not name.replace("_", "").isalnum():
            raise RequirementSyntaxError(
                f"requirement {raw!r}: {name!r} is not a valid variable name"
            )
        form = (
            _REQUIREMENT_FORM_VARIABLE
            if forced in (None, _REQUIREMENT_FORM_VARIABLE)
            else forced
        )
        return form, name, value

    if forced is not None:
        return forced, text, ""
    return _classify_bare(text), text, ""


def verify_environment_requirement(
    raw: str,
    ctx: ExecutionContext,
    env: dict[str, str] | None,
    task_id: str = "",
) -> RequirementFailure | None:
    """Check one requirement. Returns ``None`` when satisfied.

    This is the single place an environment requirement is decided. Every
    enforcement path calls it, so a requirement cannot be enforced on one path
    and ignored on another.
    """
    try:
        form, subject, expected = _parse_requirement(raw)
    except RequirementSyntaxError as exc:
        return RequirementFailure(task_id, "syntax", raw, str(exc))

    if form == _REQUIREMENT_FORM_PATH:
        target = REPO_ROOT / subject.lstrip("/")
        if not target.exists():
            return RequirementFailure(
                task_id, form, raw, f"path does not exist: {subject}"
            )
        return None

    if form in (_REQUIREMENT_FORM_TOOL, _REQUIREMENT_FORM_TOOL_VERSION):
        located = _find_tool(subject)
        if located is None:
            return RequirementFailure(
                task_id,
                form,
                raw,
                f"executable {subject!r} not found in .venv/bin or on PATH",
            )
        if form == _REQUIREMENT_FORM_TOOL_VERSION:
            found = _tool_version_of(located)
            if expected and expected not in found:
                return RequirementFailure(
                    task_id,
                    form,
                    raw,
                    f"{subject} version mismatch: required {expected}, "
                    f"found {found or '<unreported>'} at {located}",
                )
        return None

    # VARIABLE
    assert env is not None, "variable requirements need a child environment"
    if subject not in env:
        return RequirementFailure(
            task_id, form, raw, f"environment variable {subject} is not set"
        )
    if expected:
        try:
            resolved = _resolve_placeholders(expected, ctx)
        except RequirementSyntaxError as exc:
            return RequirementFailure(task_id, "syntax", raw, str(exc))
        if env[subject] != resolved:
            return RequirementFailure(
                task_id,
                form,
                raw,
                f"{subject}={env[subject]!r} but the obligation requires "
                f"{resolved!r}",
            )
    return None


def verify_task_environment(
    task_id: str,
    requirements: tuple[str, ...] | list[str],
    ctx: ExecutionContext,
    env: dict[str, str] | None,
) -> list[RequirementFailure]:
    """Check every requirement of one task. Returns the failures, in order."""
    failures: list[RequirementFailure] = []
    for raw in requirements:
        failure = verify_environment_requirement(raw, ctx, env, task_id)
        if failure is not None:
            failures.append(failure)
    return failures


# ---------------------------------------------------------------------------
# Capability → mutation target (capability vocabulary → ENGINE_SELECTION)
# ---------------------------------------------------------------------------

# Registry capabilities that have a known C42 mutation contract target.
CAPABILITY_TO_MUTATION_TARGET: dict[str, str] = {
    "loan-engine": "loan_engine",
    "reconciliation": "reconciliation_engine",
    "ledger": "ledger_audit_engine",
    "credit_card": "credit_card_engine",
    "account_engine": "account_engine",
}


# ---------------------------------------------------------------------------
# Plan contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecutionTaskSpec:
    """The execution contract for a single task.

    A spec is a pure (frozen) dataclass so plan identity is content-only.
    """

    task_id: str
    source_task_id: str  # control-plane task ID this expands
    primary_capability: str
    capabilities: tuple[str, ...]
    verification_kind: str
    command: str
    profile: str
    scope: str
    is_mandatory: bool
    is_escalation: bool
    reason: str
    origin: str  # TaskOrigin
    required_environment: tuple[str, ...] = field(default_factory=tuple)
    """The single declaration of what this task needs in order to exist.

    Three forms, all validated by :func:`verify_environment_requirement` before
    any spawn:

    * PATH   ``".venv"`` — repo-relative path must exist.
    * TOOL   ``"pytest"`` / ``"mutmut==3.7.0"`` — resolvable (``.venv/bin``
      first, per ``AGENTS.md``), and the version must match when pinned.
    * VARIABLE ``"FINANCE_DB_PATH"`` / ``"PLAYWRIGHT_PROJECT=chromium"`` — must be
      present in the child environment, and equal to the value when one is given.
      A value may contain ``@token`` placeholders resolved from an
      :class:`ExecutionContext`, which is what lets one declaration be correct in
      a CI shard leg, a local reproduction, and on a laptop.

    This field *replaces* ``prerequisites`` (repository paths only, and it
    silently skipped five of its own values) and the never-read
    ``required_environment`` on the dead ``ExecutableVerificationTask``. A
    pre-M10-R3 ``plan.json`` carrying ``prerequisites`` still loads:
    :meth:`from_dict` folds it in. There is no second field to drift.
    """

    depends_on: tuple[str, ...] = field(default_factory=tuple)
    expected_evidence: tuple[str, ...] = field(default_factory=tuple)
    measurement_required: tuple[str, ...] = field(default_factory=tuple)
    escalation_conditions: tuple[str, ...] = field(default_factory=tuple)
    authorization_required: bool = False
    timeout_seconds: int = 600
    failure_policy: str = "diagnose_then_stop"
    evidence_reused: tuple[str, ...] = field(default_factory=tuple)
    evidence_invalidated: tuple[str, ...] = field(default_factory=tuple)
    estimated_duration_seconds: int = 0
    mutation_target: str = ""  # set when verification_kind == "mutation"

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "source_task_id": self.source_task_id,
            "primary_capability": self.primary_capability,
            "capabilities": list(self.capabilities),
            "verification_kind": self.verification_kind,
            "command": self.command,
            "profile": self.profile,
            "scope": self.scope,
            "is_mandatory": self.is_mandatory,
            "is_escalation": self.is_escalation,
            "reason": self.reason,
            "origin": self.origin,
            "required_environment": list(self.required_environment),
            "depends_on": list(self.depends_on),
            "expected_evidence": list(self.expected_evidence),
            "measurement_required": list(self.measurement_required),
            "escalation_conditions": list(self.escalation_conditions),
            "authorization_required": self.authorization_required,
            "timeout_seconds": self.timeout_seconds,
            "failure_policy": self.failure_policy,
            "evidence_reused": list(self.evidence_reused),
            "evidence_invalidated": list(self.evidence_invalidated),
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "mutation_target": self.mutation_target,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ExecutionTaskSpec:
        """Rebuild a spec from its ``to_dict`` form.

        M10-R2 (D3/C1). This is what makes a plan file *authoritative* rather than
        advisory, and therefore what makes ``check --shard`` able to execute exactly
        the tasks it was handed.

        Two properties matter and are tested:

        * **Total over the declared fields, tolerant of unknown keys.** A key the
          serialiser does not know about (a newer producer writing to an older
          consumer) is ignored rather than raising, so the plan can be rolled back
          without a coordinated upgrade of every reader. A key the serialiser
          *does* declare but omits from the payload falls back to the dataclass
          default, which keeps ``_add_dependency_edges``'s
          ``ExecutionTaskSpec(**{**spec.to_dict(), ...})`` rebuild total.
        * **Tuple fields stay tuples.** ``to_dict`` emits lists for the eight
          ``tuple[str, ...]`` fields; without the coercion a rebuilt spec would
          compare unequal to its original. Four call sites already rebuilt a spec
          from ``to_dict()`` — the dedup merge in ``_expand_control_plane_tasks``,
          the task-id reassignment after sorting, and ``_add_dependency_edges`` —
          so before M10-R2 those tuples were silently becoming lists in the live
          plan. Every such rebuild now routes through this classmethod, which is
          what makes the declared types honest and the round-trip exact.
        * **``prerequisites`` is a legacy input, not a second field.** M10-R3
          merged it into ``required_environment``. A plan written before that
          still deserialises, and its declarations survive — they are folded in
          rather than silently dropped, because dropping them would turn a
          satisfied requirement into an unenforced one, which is the exact defect
          this consolidation exists to remove.
        """
        tuple_fields = {
            "capabilities",
            "required_environment",
            "depends_on",
            "expected_evidence",
            "measurement_required",
            "escalation_conditions",
            "evidence_reused",
            "evidence_invalidated",
        }
        payload = dict(d)
        legacy = payload.pop("prerequisites", None)
        known = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in payload.items() if k in known}
        if legacy:
            merged = list(kwargs.get("required_environment") or ())
            for item in legacy:
                if item not in merged:
                    merged.append(item)
            kwargs["required_environment"] = merged
        for name in tuple_fields & known:
            if name in kwargs and kwargs[name] is not None:
                kwargs[name] = tuple(kwargs[name])
        return cls(**kwargs)


@dataclass
class ExecutionPlan:
    """The full execution plan — the C48 plan, expanded to a machine-readable
    contract that can be validated, persisted, and executed deterministically.
    """

    plan_id: str
    source_plan_id: str  # C48 ControlPlanePlan.plan_id
    repository_fingerprint: RepositoryFingerprint
    changed_files: list[str]
    affected_capabilities: list[str]
    affected_components: list[str]
    invalidated_evidence: list[str]
    reusable_evidence: list[str]
    tasks: list[ExecutionTaskSpec]
    escalation_conditions: list[str]
    measurement_requirements: list[dict]
    certification_requirements: list[dict]
    rationale: str
    plan_fingerprint: str
    generated_at: str
    # M9-C49: revalidation injections and persistent-evidence state.
    revalidation_sources: list[dict] = field(default_factory=list)
    reusable_measurements: list[dict] = field(default_factory=list)
    #: Boundary classification and the strategy this plan was built under.
    #: Present on every plan so a reader never has to infer the scope of a run
    #: from a warning in a log. See runtime.foundation.verification.boundary_policy.
    boundary_evidence: object | None = None

    #: M10-R2 (C1). Schema identifier for the serialized plan. ``to_dict`` writes
    #: it and ``from_dict`` asserts it, so a producer/consumer mismatch fails loudly
    #: instead of silently producing an under-specified plan. A payload with no
    #: ``schema`` key is accepted (tolerating a hand-written plan) but an
    #: unrecognised one is rejected.
    SCHEMA = "m9-c49-execution-plan/v1"

    def to_dict(self) -> dict:
        return {
            "schema": self.SCHEMA,
            "plan_id": self.plan_id,
            "source_plan_id": self.source_plan_id,
            "repository_fingerprint": self.repository_fingerprint.to_dict(),
            "changed_files": list(self.changed_files),
            "affected_capabilities": list(self.affected_capabilities),
            "affected_components": list(self.affected_components),
            "invalidated_evidence": list(self.invalidated_evidence),
            "reusable_evidence": list(self.reusable_evidence),
            "tasks": [t.to_dict() for t in self.tasks],
            "escalation_conditions": list(self.escalation_conditions),
            "measurement_requirements": list(self.measurement_requirements),
            "certification_requirements": list(self.certification_requirements),
            "rationale": self.rationale,
            "plan_fingerprint": self.plan_fingerprint,
            "generated_at": self.generated_at,
            "revalidation_sources": list(self.revalidation_sources),
            "reusable_measurements": list(self.reusable_measurements),
        }

    def to_json(self) -> str:
        """Serialise to a JSON **document**.

        Returns a string, not a dict. Callers producing machine-readable output must
        print this directly: wrapping it in ``json.dumps`` (M10-R2) yields a JSON
        string *literal* containing escaped JSON, which a parser reads back as one
        string rather than as an object. That bug made ``run --json`` unreadable to
        the reconcile aggregate job, which consumes shard reports.
        """
        return json.dumps(self.to_dict(), indent=2, default=str)

    def validate(self) -> list[str]:
        """Integrity checks on the plan. Empty list = OK."""
        errors: list[str] = []
        seen_ids: set[str] = set()
        for t in self.tasks:
            if t.task_id in seen_ids:
                errors.append(f"duplicate task_id={t.task_id}")
            seen_ids.add(t.task_id)
            if not t.command:
                errors.append(f"task {t.task_id} has empty command")
            if not t.capabilities:
                errors.append(f"task {t.task_id} has no capabilities")
        for t in self.tasks:
            if t.is_escalation:
                for dep in t.depends_on:
                    if dep not in {x.task_id for x in self.tasks}:
                        errors.append(
                            f"escalation task {t.task_id} depends on missing task {dep}"
                        )
        if not self.tasks:
            errors.append("plan has no tasks")
        return errors

    @classmethod
    def from_dict(cls, d: dict) -> ExecutionPlan:
        """Rebuild a plan from its ``to_dict`` form (M10-R2 C1).

        ``ControlPlane.run()`` previously loaded a plan file and then *discarded*
        it — ``ControlPlanePlan`` had no ``from_dict``, so the ``hasattr`` guard at
        ``control_plane_facade.py:372`` always fell through to regenerating a plan
        from the changed files, and ``:385`` rebuilt the execution plan regardless.
        That made every plan file advisory, which is precisely what would have made
        ``check --shard`` silently execute the whole plan in every shard.

        The schema is asserted, not assumed: a payload carrying a ``schema`` this
        build does not recognise is rejected rather than partially reconstructed,
        because a plan reconstructed under the wrong schema is a plan that reports a
        task set nobody intended to execute.

        ``boundary_evidence`` is carried through as an opaque object. It is
        presentation-only (it is rendered into the log and carries no execution
        semantics), so it is not reconstructed into a typed value; a consumer that
        needs it should re-derive it from ``rationale``.
        """
        schema = d.get("schema")
        if schema is not None and schema != cls.SCHEMA:
            raise ValueError(
                f"unsupported execution plan schema {schema!r}; "
                f"this build reads {cls.SCHEMA!r}"
            )
        return cls(
            plan_id=d.get("plan_id", ""),
            source_plan_id=d.get("source_plan_id", ""),
            repository_fingerprint=RepositoryFingerprint.from_dict(
                d.get("repository_fingerprint") or {}
            ),
            changed_files=list(d.get("changed_files") or []),
            affected_capabilities=list(d.get("affected_capabilities") or []),
            affected_components=list(d.get("affected_components") or []),
            invalidated_evidence=list(d.get("invalidated_evidence") or []),
            reusable_evidence=list(d.get("reusable_evidence") or []),
            tasks=[ExecutionTaskSpec.from_dict(t) for t in (d.get("tasks") or [])],
            escalation_conditions=list(d.get("escalation_conditions") or []),
            measurement_requirements=list(d.get("measurement_requirements") or []),
            certification_requirements=list(d.get("certification_requirements") or []),
            rationale=d.get("rationale", ""),
            plan_fingerprint=d.get("plan_fingerprint", ""),
            generated_at=d.get("generated_at", ""),
            revalidation_sources=list(d.get("revalidation_sources") or []),
            reusable_measurements=list(d.get("reusable_measurements") or []),
            boundary_evidence=d.get("boundary_evidence"),
        )


# ---------------------------------------------------------------------------
# Task execution record
# ---------------------------------------------------------------------------


@dataclass
class TaskExecutionRecord:
    record_id: str
    plan_id: str
    task_id: str
    primary_capability: str
    capabilities: list[str]
    command: str
    scope: str
    is_mandatory: bool
    is_escalation: bool
    verification_kind: str
    started_at: str
    completed_at: str
    duration_seconds: float
    exit_code: int | None
    completion_state: str  # CompletionState
    stdout_path: str
    stderr_path: str
    artifacts: list[str]
    measurement_truth: dict | None
    diagnostic: dict | None
    next_action: str
    reason: str
    prerequisites_satisfied: bool
    # How the process actually ended, kept apart from the completion state:
    # EXIT_ZERO / EXIT_NONZERO / WRAPPER_TIMEOUT / SIGNAL_TERMINATION /
    # INFRASTRUCTURE, plus an `inner` pytest classification when the command
    # ran pytest (TEST_ASSERTION_FAILURE / TEST_TIMEOUT /
    # COLLECTION_OR_INTERNAL_ERROR / PASSED). See `_classify_termination` and
    # `_summarise_pytest_outcome`. A long run that ends in any of these must be
    # diagnosable from the record alone, without re-running it.
    termination: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# The certification authority (M10-R3 / B2)
#
# ONE classifier, SIX producers.
#
# The defect this removes was measured, not inferred. Of the six ways this
# repository executes a verification obligation, exactly one (``verify check`` /
# ``verify run``) produced a ``FinalDecision`` and bracketed execution with a
# repository fingerprint. The other five — profile aliases, obligation legs,
# runtime shards, Playwright legs, mutation — used the *same* subprocess worker
# but formed their verdict as "first non-zero exit code in plan order" and wrote
# a literal ``final_decision="certified"`` into the event log without ever
# capturing a fingerprint.
#
# The consequence: a green ``verify backend`` was not evidence that the
# repository was unchanged during the run. It was evidence that no shell exited
# non-zero. Those are different claims and only one of them is a certification.
#
# So the decision is extracted from ``ExecutionOrchestrator._finalize`` — where
# it already existed and was already correct — into a module-level classifier
# over a minimal outcome type that *every* topology can produce without a plan,
# and the fingerprint bracket is lifted into a context manager that wraps the
# whole execution. The orchestrator becomes the first consumer rather than the
# only one.
#
# Deliberately NOT a new framework: no new engine, no new spawn path, no new
# vocabulary. ``CompletionState`` and ``FinalDecision`` already existed and are
# reused verbatim.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ObligationOutcome:
    """The minimum an execution path must report to be certifiable.

    Five topologies never build a :class:`TaskExecutionRecord` — they have no plan,
    no capabilities list and no artifact inventory. Rather than force a plan onto
    them (which would be the "envelope" approach, and would give them a richer
    record without giving them a real decision), they report this.
    """

    task_id: str
    state: CompletionState
    is_mandatory: bool = True
    detail: str = ""

    @classmethod
    def from_record(cls, record: TaskExecutionRecord) -> ObligationOutcome:
        """Adapt a full record. The orchestrator's own path."""
        state = record.completion_state
        if not isinstance(state, CompletionState):
            state = _coerce_completion_state(state)
        detail = ""
        if record.diagnostic:
            detail = str(record.diagnostic.get("message", ""))[:400]
        return cls(
            task_id=record.task_id,
            state=state,
            is_mandatory=record.is_mandatory,
            detail=detail,
        )


def _coerce_completion_state(value: Any) -> CompletionState:
    """Tolerate a state that arrived as a string.

    ``CompletionState`` is a ``str`` enum, but records round-trip through JSON, so
    a value can arrive as the enum itself, as its lowercase value (``"scope"``),
    as its member name (``"SCOPE"``), or as a qualified repr
    (``"CompletionState.SCOPE"``) — the last of which is what an
    ``f"{state}"``-style serialiser produces. All four must resolve to the same
    member.

    An unrecognised value falls back to ``FAILED``, never to ``PASS``: a state the
    classifier cannot understand must not be able to certify.
    """
    if isinstance(value, CompletionState):
        return value
    text = str(value).strip()
    if "." in text:
        text = text.rsplit(".", 1)[1]
    for candidate in (text, text.lower(), text.upper()):
        try:
            return CompletionState(candidate)
        except ValueError:
            continue
    return CompletionState.FAILED


def decide_final_outcome(
    outcomes: Sequence[ObligationOutcome],
    *,
    fingerprint_stable: bool = True,
    fingerprint_note: str = "",
    certification_requirements: Sequence[dict] = (),
    measurement_lookup: Callable[[str, str], Any] | None = None,
    current_sha: str = "",
) -> tuple[FinalDecision, str]:
    """Classify a set of obligation outcomes. The single decision function.

    Precedence is deliberate and is the same precedence ``_finalize`` used:

    1. ``INFRASTRUCTURE``  — the run could not be measured at all.
    2. ``TIMEOUT``        — never converts to PASS.
    3. fingerprint drift  — the repository changed under us.
    4. ``CONFIGURATION`` on a mandatory task.
    5. ``FAILED`` on a mandatory task.
    6. ``AUTHORIZATION_REQUIRED``.
    7. certification gate — measurement thresholds.
    8. ``CERTIFIED``.

    Ordering matters and is not cosmetic. Drift is checked *after* timeout so a
    timed-out run reports ``TIMEOUT_BLOCKED`` (the actionable cause) rather than
    a fingerprint mismatch (a symptom). Drift is checked *before* a mandatory
    failure so a run whose tree moved cannot be diagnosed as an ordinary test
    failure — the test result is not trustworthy once the tree has moved under it.
    """
    states = [o.state for o in outcomes]

    if any(s == CompletionState.INFRASTRUCTURE for s in states):
        ids = [o.task_id for o in outcomes if o.state == CompletionState.INFRASTRUCTURE]
        return (
            FinalDecision.INFRASTRUCTURE_BLOCKED,
            f"obligation(s) {', '.join(ids)} reported infrastructure failure — "
            "cannot certify",
        )
    if any(s == CompletionState.TIMEOUT for s in states):
        ids = [o.task_id for o in outcomes if o.state == CompletionState.TIMEOUT]
        return (
            FinalDecision.TIMEOUT_BLOCKED,
            f"obligation(s) {', '.join(ids)} timed out — cannot certify "
            "(a timeout never converts to PASS)",
        )
    # SCOPE and fingerprint drift are the same phenomenon observed two ways: the
    # repository state moved, so the run's own results cannot be attributed to the
    # commit under test. The orchestrator reports it as a SCOPE record; the
    # plan-less topologies report it as an unstable bracket. Both must land here.
    scoped = [o for o in outcomes if o.state == CompletionState.SCOPE]
    if scoped or not fingerprint_stable:
        detail = fingerprint_note if fingerprint_note else ""
        if scoped:
            named = ", ".join(
                f"{o.task_id}" + (f" ({o.detail})" if o.detail else "")
                for o in scoped
            )
            which = f"invalid scope on {named}"
        else:
            which = "repository drift"
        return (
            FinalDecision.VALIDATION_BLOCKED,
            f"{which} detected — cannot certify"
            + (f" ({detail})" if detail else ""),
        )
    mandatory_config = [
        o.task_id for o in outcomes
        if o.state == CompletionState.CONFIGURATION and o.is_mandatory
    ]
    if mandatory_config:
        return (
            FinalDecision.VALIDATION_BLOCKED,
            f"configuration failure on mandatory obligation(s) "
            f"{', '.join(mandatory_config)} — cannot certify",
        )
    mandatory_failed = [
        o.task_id for o in outcomes
        if o.state == CompletionState.FAILED and o.is_mandatory
    ]
    if mandatory_failed:
        return (
            FinalDecision.DIAGNOSTIC,
            f"mandatory obligation(s) failed: {', '.join(mandatory_failed)} — "
            "run the diagnostic path",
        )
    if any(s == CompletionState.AUTHORIZATION_REQUIRED for s in states):
        return (
            FinalDecision.AWAITING_AUTHORIZATION,
            "one or more obligations require explicit human authorization; "
            "production changes were not attempted",
        )

    missing = _certification_gate_gaps(
        certification_requirements, measurement_lookup, current_sha
    )
    if missing:
        return (
            FinalDecision.NOT_CERTIFIABLE,
            "certification conditions not satisfied: " + "; ".join(missing),
        )
    return (
        FinalDecision.CERTIFIED,
        "all mandatory obligations satisfied and certification conditions met",
    )


def _certification_gate_gaps(
    certification_requirements: Sequence[dict],
    measurement_lookup: Callable[[str, str], Any] | None,
    current_sha: str,
) -> list[str]:
    """Evaluate declared certification thresholds. Extracted, not reimplemented."""
    if measurement_lookup is None:
        return []
    gaps: list[str] = []
    for cr in certification_requirements:
        cap = cr.get("capability", "")
        minimum = cr.get("minimum_mutation_score")
        if minimum is None:
            continue
        found = measurement_lookup(cap, "mutation")
        record = found[0] if isinstance(found, tuple) else found
        if record is None or not _certification_gate(record):
            gaps.append(f"{cap} mutation measurement authoritative+current")
            continue
        record_sha = str(getattr(record, "repository_sha", ""))
        if current_sha and record_sha != current_sha:
            gaps.append(f"{cap} mutation record sha={record_sha[:8]} != current")
            continue
        score = getattr(record, "mutation_score", None) or 0
        if score < minimum:
            gaps.append(f"{cap} mutation score {score} < {minimum}")
    return gaps


def _certification_gate(record: Any) -> bool:
    from runtime.foundation.verification.measurement_truth import certification_gate

    return bool(certification_gate(record))


class FingerprintDrift(RuntimeError):
    """The repository changed while verification was executing.

    Raised only where the caller asked for fail-fast (``strict=True``). The
    default is to *record* the drift and let :meth:`CertificationRun.decide`
    return ``VALIDATION_BLOCKED``, because a drift discovered mid-run usually has
    useful partial evidence attached to it and throwing that away helps nobody.
    """

    def __init__(self, before: RepositoryFingerprint, after: RepositoryFingerprint):
        self.before = before
        self.after = after
        super().__init__(
            f"repository fingerprint changed during verification: "
            f"{before.fingerprint[:12]} -> {after.fingerprint[:12]}"
        )


class CertificationRun:
    """Brackets one execution with a fingerprint and produces its verdict.

    This is the object the five plan-less topologies were missing. Used as a
    context manager it guarantees the *final* fingerprint is captured even when the
    body raises, which is what makes the invariant hold on the interrupted and
    timed-out paths as well as the clean one — a bracket that only closes on the
    happy path is not an invariant.

    ::

        with CertificationRun(plan_id=plan.plan_id) as run:
            for task in tasks:
                run.record(task.id, CompletionState.PASS)
            ... execute ...
        print(run.decision, run.reason, run.exit_code)

    Three properties are load-bearing:

    * **One classifier.** :meth:`decide` delegates to :func:`decide_final_outcome`.
      There is no second precedence table to drift from the orchestrator's.
    * **Drift is always reported.** :attr:`fingerprint_stable` is computed from the
      bracket, never asserted by the caller.
    * **A partial run is not a pass.** With no recorded obligations the decision is
      ``NOT_CERTIFIABLE``, not ``CERTIFIED``. An execution that recorded nothing
      has certified nothing, and the difference must not be expressible as green.
    """

    __slots__ = (
        "_outcomes",
        "_started_at",
        "fingerprint_after",
        "fingerprint_before",
        "fingerprint_note",
        "plan_id",
        "strict",
        "_certification_requirements",
        "_measurement_lookup",
    )

    def __init__(
        self,
        plan_id: str = "",
        *,
        certification_requirements: Sequence[dict] = (),
        measurement_lookup: Callable[[str, str], Any] | None = None,
        strict: bool = False,
    ) -> None:
        self.plan_id = plan_id
        self._outcomes: list[ObligationOutcome] = []
        self.fingerprint_before: RepositoryFingerprint | None = None
        self.fingerprint_after: RepositoryFingerprint | None = None
        self.fingerprint_note = ""
        self.strict = strict
        self._certification_requirements = list(certification_requirements)
        self._measurement_lookup = measurement_lookup
        self._started_at = 0.0

    # -- context manager ---------------------------------------------------

    def __enter__(self) -> CertificationRun:
        self._started_at = time.monotonic()
        self.fingerprint_before = RepositoryFingerprint.capture()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Captured in a finally-equivalent: if the body raised, we still close the
        # bracket, because "the tree changed AND the run blew up" is the diagnosis
        # an operator needs, and losing the 'after' fingerprint loses half of it.
        self.fingerprint_after = RepositoryFingerprint.capture()
        if self.strict and not self.fingerprint_stable:
            assert self.fingerprint_before is not None
            raise FingerprintDrift(self.fingerprint_before, self.fingerprint_after)
        return False  # never swallow

    # -- recording ---------------------------------------------------------

    def record(
        self,
        task_id: str,
        state: CompletionState | str,
        *,
        is_mandatory: bool = True,
        detail: str = "",
    ) -> ObligationOutcome:
        """Record one obligation's outcome. Order-preserving and repeatable."""
        outcome = ObligationOutcome(
            task_id=task_id,
            state=_coerce_completion_state(state),
            is_mandatory=is_mandatory,
            detail=detail,
        )
        self._outcomes.append(outcome)
        return outcome

    def adopt(self, records: Sequence[TaskExecutionRecord]) -> None:
        """Adopt a full set of orchestrator records."""
        for record in records:
            self._outcomes.append(ObligationOutcome.from_record(record))

    @property
    def outcomes(self) -> tuple[ObligationOutcome, ...]:
        return tuple(self._outcomes)

    # -- verdict -----------------------------------------------------------

    @property
    def fingerprint_stable(self) -> bool:
        """True unless both captures exist and differ."""
        if self.fingerprint_before is None or self.fingerprint_after is None:
            # An unclosed bracket cannot assert stability. Reporting True here would
            # let a crash before __exit__ certify silently.
            return False
        return self.fingerprint_before.matches(self.fingerprint_after)

    @property
    def duration_seconds(self) -> float:
        return time.monotonic() - self._started_at if self._started_at else 0.0

    def decide(self) -> tuple[FinalDecision, str]:
        """Classify. The one call every topology makes."""
        if not self._outcomes:
            return (
                FinalDecision.NOT_CERTIFIABLE,
                "no obligation reported an outcome — nothing was certified",
            )
        stable = self.fingerprint_stable
        note = self.fingerprint_note
        if not stable and self.fingerprint_before and self.fingerprint_after:
            note = (
                f"before={self.fingerprint_before.fingerprint[:12]} "
                f"after={self.fingerprint_after.fingerprint[:12]}"
            )
        return decide_final_outcome(
            self._outcomes,
            fingerprint_stable=stable,
            fingerprint_note=note,
            certification_requirements=self._certification_requirements,
            measurement_lookup=self._measurement_lookup,
            current_sha=(
                self.fingerprint_before.repository_sha if self.fingerprint_before else ""
            ),
        )

    @property
    def decision(self) -> FinalDecision:
        return self.decide()[0]

    @property
    def reason(self) -> str:
        return self.decide()[1]

    def exit_code(self) -> int:
        """Map the decision onto a process exit code.

        ``CERTIFIED`` is 0 and nothing else is. Every blocked decision gets a
        distinct non-zero code so a CI log distinguishes "the tree moved" from
        "something timed out" from "a test asserted" without parsing prose.
        """
        return _DECISION_EXIT_CODES.get(self.decision, 1)

    def to_dict(self) -> dict:
        decision, reason = self.decide()
        return {
            "schema": "m10r3-certification-run/v1",
            "plan_id": self.plan_id,
            "decision": decision.value,
            "reason": reason,
            "exit_code": self.exit_code(),
            "duration_seconds": round(self.duration_seconds, 3),
            "fingerprint_before": (
                self.fingerprint_before.to_dict() if self.fingerprint_before else None
            ),
            "fingerprint_after": (
                self.fingerprint_after.to_dict() if self.fingerprint_after else None
            ),
            "fingerprint_stable": self.fingerprint_stable,
            "obligations": [
                {
                    "task_id": o.task_id,
                    "state": o.state.value,
                    "is_mandatory": o.is_mandatory,
                    "detail": o.detail,
                }
                for o in self._outcomes
            ],
        }


#: Distinct exit codes per blocked decision, so a CI leg can tell the failure modes
#: apart from the exit status alone without parsing prose.
#:
#: Two of these are conventions worth preserving rather than renumbering:
#: ``124`` is GNU ``timeout``'s "command timed out", and CI tooling, shell wrappers
#: and humans all read it that way. ``2`` is argparse's usage-error code, so
#: authorization deliberately does not take it.
_DECISION_EXIT_CODES: dict[FinalDecision, int] = {
    FinalDecision.CERTIFIED: 0,
    FinalDecision.NOT_CERTIFIABLE: 1,
    FinalDecision.DIAGNOSTIC: 1,
    FinalDecision.AWAITING_AUTHORIZATION: 6,
    FinalDecision.INFRASTRUCTURE_BLOCKED: 3,
    FinalDecision.TIMEOUT_BLOCKED: 124,
    FinalDecision.VALIDATION_BLOCKED: 5,
}


# ---------------------------------------------------------------------------
# Execution report
# ---------------------------------------------------------------------------



@dataclass
class ExecutionReport:
    report_id: str
    plan_id: str
    plan_fingerprint: str
    started_at: str
    completed_at: str
    total_duration_seconds: float
    records: list[TaskExecutionRecord]
    efficiency: dict
    final_decision: str  # FinalDecision
    decision_reason: str
    evidence_reused: list[str]
    escalations_triggered: list[str]
    decisions: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema": "m9-c49-execution-report/v1",
            "report_id": self.report_id,
            "plan_id": self.plan_id,
            "plan_fingerprint": self.plan_fingerprint,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_seconds": self.total_duration_seconds,
            "records": [r.to_dict() for r in self.records],
            "efficiency": dict(self.efficiency),
            "final_decision": self.final_decision,
            "decision_reason": self.decision_reason,
            "evidence_reused": list(self.evidence_reused),
            "escalations_triggered": list(self.escalations_triggered),
            "decisions": list(self.decisions),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capability_components(capabilities: list[str]) -> list[str]:
    """Deterministic list of engine components served by a capability set."""
    out: list[str] = []
    for c in capabilities:
        target = CAPABILITY_TO_MUTATION_TARGET.get(c, "")
        if target and target not in out:
            out.append(target)
    return out


def _measurement_kind_for_task(spec: ExecutionTaskSpec) -> str:
    """The MeasurementKind value for a task, or empty string for non-measurement."""
    if spec.verification_kind in ("mutation",):
        return "mutation"
    if spec.verification_kind in ("coverage",):
        return "coverage"
    if spec.profile == "mutation":
        return "mutation"
    if spec.profile == "coverage":
        return "coverage"
    return ""


# ---------------------------------------------------------------------------
# Execution orchestrator
# ---------------------------------------------------------------------------


class ExecutionOrchestrator:
    """Consumes the C48 control-plane plan and drives it to a final decision.

    The orchestrator is the *only* component that decides which commands
    actually run, in which order, under which stop rules, and what the final
    certification state is. It never invents new verifications: every task
    traces back to a C48 control-plane task or a revalidation injection that
    a stale/missing persistent measurement record justifies.
    """

    def __init__(
        self,
        contract_registry=None,
        population=None,
        measurements=None,
        command_overrides: dict[str, str] | None = None,
        measurement_search_dirs: list[str] | None = None,
        max_runtime_overrides: dict[str, int] | None = None,
        evidence_root: Path | None = None,
        progress_prefix: str | None = None,
    ) -> None:
        """*progress_prefix* enables live per-task lifecycle logging (M10-R2 closeout).

        When set, every task executed through this orchestrator emits
        ``[<prefix>/<task_id>] start|running|exit=...`` to stderr. This is the only
        orchestrator-side change live observability needs: the per-task line is composed
        here and executed by ``run_streaming_command``, which every verification
        subprocess in the repository already routes through.

        ``None`` (the default) restores byte-identical behaviour, so local runs and the
        existing suite are unaffected.
        """
        from runtime.foundation.verification.capability_contract import (
            get_capability_contract_registry,
        )
        from runtime.foundation.verification.evidence_reuse import (
            c42_24_b_measurements,
            c42_25_measurements,
            c42_26_population,
        )

        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._population = population or c42_26_population()
        self._measurements = measurements or (
            c42_24_b_measurements() + c42_25_measurements()
        )
        self._command_overrides = dict(command_overrides or {})
        self._max_runtime_overrides = dict(max_runtime_overrides or {})
        self._measurement_search_dirs = list(measurement_search_dirs or [])
        self._evidence_root = evidence_root or GENERATED_ROOT
        #: M10-R2 (C1b). scope -> capabilities sharing one coverage execution, as
        #: decided by the most recent `_inject_revalidations`. Read by
        #: `fan_out_shared_measurement_records`.
        self._last_coverage_groups: dict[str, list[str]] = {}
        self._progress_prefix = progress_prefix

    def fan_out_shared_measurement_records(
        self,
        measurement_dir: Path | None = None,
    ) -> list[str]:
        """Materialise one coverage record per requesting capability.

        M10-R2 (C1b). The dedup executes each distinct coverage scope once, but the
        evidence contract is unchanged: `_find_measurement_record` resolves a record
        *per capability*, and `_finalize`'s certification gate reads those. So after
        the shared execution has written its record, this copies it to
        ``measurement-truth-{cap}-coverage.json`` for every other capability that
        shared the scope, preserving the measured scope, score, repository sha and
        evidence fingerprint verbatim.

        The copy is marked with ``measurement_provenance`` recording which capability
        the execution actually ran for. Nothing is asserted that the measurement does
        not support: the record still reports the scope that was *measured*, so
        `_component_for_mapping`'s scope check in `_find_measurement_record` continues
        to accept it on exactly the same terms it accepted the original.

        Existing files are never overwritten — if a real per-capability record is
        already present it is authoritative and is left alone.

        Returns the paths written.
        """
        from runtime.foundation.verification.measurement_truth import (
            load_measurement_truth,
        )

        if not self._last_coverage_groups:
            return []

        target_dir = measurement_dir or (
            REPO_ROOT / "runtime" / "generated" / "m9-c49" / "measurements"
        )
        target_dir.mkdir(parents=True, exist_ok=True)

        written: list[str] = []
        for scope, capabilities in sorted(self._last_coverage_groups.items()):
            for lead in capabilities:
                source_path = target_dir / f"measurement-truth-{lead}-coverage.json"
                if not source_path.exists():
                    continue
                try:
                    record = load_measurement_truth(source_path)
                except Exception:
                    continue
                payload = (
                    record.to_dict() if hasattr(record, "to_dict") else dict(record)
                )
                for cap in capabilities:
                    if cap == lead:
                        continue
                    dest = target_dir / f"measurement-truth-{cap}-coverage.json"
                    if dest.exists():
                        continue
                    payload["measurement_provenance"] = {
                        "shared_from": lead,
                        "measured_scope": scope,
                        "note": (
                            "One execution of this scope serves every capability "
                            "mapped to it; this record is a per-capability view of "
                            "that single measurement, not a separate run."
                        ),
                    }
                    dest.write_text(
                        json.dumps(payload, indent=2, default=str),
                        encoding="utf-8",
                    )
                    written.append(str(dest))
        return written

    # ------------------------------------------------------------- planning

    def build_execution_plan(self, changed_files: list[str]) -> ExecutionPlan:
        """Build a deterministic ExecutionPlan from a list of changed files.

        The plan consumes the C48 ControlPlanePlan. It then:
        * deduplicates identical commands across capabilities (one execution
          can serve multiple capabilities);
        * orders tasks deterministically (mandatory first, escalation last);
        * injects revalidation tasks for missing/stale authoritative
          measurement records (Section 6 — "stale evidence → invalidate and
          execute the minimum replacement verification").
        """
        from runtime.foundation.verification.control_plane import (
            generate_control_plane_plan,
        )

        cp = generate_control_plane_plan(
            changed_files,
            population=self._population,
            measurements=self._measurements,
        )

        live_fp = RepositoryFingerprint.capture()
        tasks, _dedup_keys = self._expand_control_plane_tasks(cp, live_fp)
        revalidation_tasks, revalidation_sources, reusable = self._inject_revalidations(
            cp, tasks, live_fp
        )
        tasks = tasks + revalidation_tasks
        self._add_dependency_edges(tasks)

        plan_fingerprint = self._compute_plan_fingerprint(
            cp.plan_id, live_fp, changed_files, tasks
        )
        plan_id = f"execplan-{plan_fingerprint[:12]}"

        rationale = self._build_rationale(cp, tasks, reusable, revalidation_sources)

        plan = ExecutionPlan(
            plan_id=plan_id,
            source_plan_id=cp.plan_id,
            repository_fingerprint=live_fp,
            changed_files=list(changed_files),
            affected_capabilities=sorted(
                set(cp.capability_resolution.all_affected_capabilities)
            ),
            affected_components=self._collect_components(tasks),
            invalidated_evidence=list(cp.capability_resolution.invalidated_evidence),
            reusable_evidence=list(cp.capability_resolution.reusable_evidence),
            tasks=tasks,
            escalation_conditions=list(cp.escalation_conditions),
            measurement_requirements=list(cp.measurement_requirements),
            certification_requirements=list(cp.certification_requirements),
            rationale=rationale,
            plan_fingerprint=plan_fingerprint,
            generated_at=datetime.now(UTC).isoformat(),
            revalidation_sources=revalidation_sources,
            reusable_measurements=reusable,
        )
        return plan

    def _expand_control_plane_tasks(self, cp, live_fp: RepositoryFingerprint):
        """Translate C48 control-plane tasks into deduplicated ExecutionTaskSpec.

        Dedup key: (command, verification_kind, profile). One execution
        serves all capabilities the same command covers (per Section 16
        efficiency requirement).
        """
        inventory = self._get_inventory_map()
        dedup: dict[tuple[str], dict] = {}
        order: list[tuple[str]] = []

        for cp_task in cp.tasks:
            inv_entry = inventory.get(cp_task.profile) or inventory.get(
                _profile_from_command(cp_task.command)
            )
            timeout = self._timeout_for(cp_task, inv_entry, fallback=900)
            # Authorization boundary: only commands that actually mutate
            # the repository or are the full mutation campaign require
            # human authorization. Profile script commands (which the C48
            # inventory flags as "escalation") do not themselves mutate.
            is_mutation = (
                "mutation" in cp_task.profile
                or "mutation" in cp_task.command
                or cp_task.verification_kind == "mutation"
            )
            auth_required = is_mutation
            expected_evidence = list(inv_entry.evidence_produced) if inv_entry else []
            prereqs = list(inv_entry.required_environment) if inv_entry else [".venv"]
            dedup_key = (cp_task.command.strip(),)
            bucket = dedup.get(dedup_key)
            if bucket is None:
                spec = ExecutionTaskSpec(
                    task_id=f"exec-{len(order) + 1:04d}",
                    source_task_id=f"{cp_task.capability_id}::{cp_task.task_id}",
                    primary_capability=cp_task.capability_id,
                    capabilities=(cp_task.capability_id,),
                    verification_kind=cp_task.verification_kind,
                    command=cp_task.command.strip(),
                    profile=cp_task.profile,
                    scope=cp_task.profile,
                    is_mandatory=cp_task.is_mandatory,
                    is_escalation=cp_task.is_escalation,
                    reason=cp_task.reason,
                    origin=TaskOrigin.CONTROL_PLANE.value,
                    required_environment=tuple(prereqs),
                    expected_evidence=tuple(expected_evidence),
                    measurement_required=tuple(
                        m.value for m in cp_task.measurement_required
                    ),
                    escalation_conditions=(),
                    authorization_required=auth_required,
                    timeout_seconds=timeout,
                    evidence_reused=tuple(cp_task.evidence_reused),
                    evidence_invalidated=tuple(cp_task.evidence_invalidated),
                    estimated_duration_seconds=cp_task.estimated_duration_seconds,
                )
                bucket = {
                    "spec": spec,
                    "capabilities": {cp_task.capability_id},
                }
                dedup[dedup_key] = bucket
                order.append(dedup_key)
            else:
                bucket["capabilities"].add(cp_task.capability_id)
                # Merge deduped spec: upgrade mandatory / authorization
                # if any contributing task needs them.
                new_dict = bucket["spec"].to_dict()
                if cp_task.is_mandatory and not bucket["spec"].is_mandatory:
                    new_dict["is_mandatory"] = True
                if cp_task.evidence_invalidated:
                    new_dict["is_mandatory"] = True
                if auth_required and not bucket["spec"].authorization_required:
                    new_dict["authorization_required"] = True
                # Track the earliest source task id for provenance
                if cp_task.task_id < new_dict["source_task_id"]:
                    new_dict["source_task_id"] = cp_task.task_id
                bucket["spec"] = ExecutionTaskSpec.from_dict(new_dict)
        # Finalize per-bucket capabilities into the spec.
        tasks: list[ExecutionTaskSpec] = []
        for key in order:
            bucket = dedup[key]
            spec_dict = bucket["spec"].to_dict()
            caps = sorted(bucket["capabilities"])
            spec_dict["primary_capability"] = caps[0]
            spec_dict["capabilities"] = caps
            spec_dict["reason"] = (
                spec_dict["reason"] + f" (serves: {', '.join(caps)})"
            ).strip()
            tasks.append(ExecutionTaskSpec.from_dict(spec_dict))
        # Apply deterministic ordering: mandatory first by (primary_cap, command).
        tasks.sort(
            key=lambda t: (
                0 if t.is_mandatory else 1,
                t.primary_capability,
                t.command,
            )
        )
        # Reassign stable task IDs after sort.
        tasks = [
            ExecutionTaskSpec.from_dict({**t.to_dict(), "task_id": f"exec-{i + 1:04d}"})
            for i, t in enumerate(tasks)
        ]
        return tasks, order

    def _inject_revalidations(self, cp, tasks: list[ExecutionTaskSpec], live_fp):
        """Inspect durable measurement records and inject revalidation tasks
        for capabilities whose required measurements are missing or stale."""
        from runtime.foundation.verification.measurement_truth import (
            MeasurementKind,
            certification_gate,
        )

        revalidation_sources: list[dict] = []
        reusable: list[dict] = []
        new_tasks: list[ExecutionTaskSpec] = []
        next_id = len(tasks) + 1

        # M10-R2 (C1b). Coverage revalidation used to emit one task per
        # (capability, measurement-mapping) pair. Because the ``--out`` path embeds
        # the capability name, N capabilities whose coverage mapping resolves to the
        # *same* scope produced N byte-different command strings running the *same*
        # measurement. On a 40-file boundary that is 4 executions of
        # ``measurement coverage tests/unit/engines`` (measured; see
        # docs/audits/m10-r2-baseline.md) where one suffices.
        #
        # Keying on the command string cannot fix it, which is why the dedup added
        # in `_expand_control_plane_tasks` (keyed on the command) does not apply
        # here. The key must be the *resolved scope* — computed below, after the
        # api-contracts/``backend`` rewrites below have been applied.
        #
        # Grouping is sound because `_find_measurement_record` already enforces, via
        # `_component_for_mapping`, that a record speaks only for the scope it
        # actually measured. Two capabilities declaring the same scope legitimately
        # share one measurement; two different scopes never merge.
        coverage_groups: dict[str, dict] = {}

        for cap_id in sorted(
            set(cp.capability_resolution.directly_affected_capabilities)
        ):
            contract = self._contract_registry.get_contract(cap_id)
            if not contract:
                continue
            for mm in contract.measurement_mappings:
                kind = mm.measurement_kind.value
                cap = cap_id
                component = self._component_for_mapping(cap, kind)
                record, path = self._find_measurement_record(
                    cap, kind, mm.authoritative_evidence_path
                )
                if record is not None and certification_gate(record):
                    if record.repository_sha == live_fp.repository_sha:
                        reusable.append(
                            {
                                "capability": cap,
                                "kind": kind,
                                "path": str(path),
                                "repository_sha": record.repository_sha,
                                "score": (
                                    record.mutation_score
                                    if kind == MeasurementKind.MUTATION.value
                                    else (
                                        record.coverage_result_percent
                                        or record.coverage.line_percent
                                    )
                                ),
                            }
                        )
                        continue
                    # stale: present but repo sha does not match
                    revalidation_sources.append(
                        {
                            "capability": cap,
                            "kind": kind,
                            "reason": (
                                f"evidence stale: recorded sha "
                                f"{record.repository_sha[:12]} != current "
                                f"{live_fp.repository_sha[:12]}"
                            ),
                            "path": str(path),
                        }
                    )
                else:
                    revalidation_sources.append(
                        {
                            "capability": cap,
                            "kind": kind,
                            "reason": (
                                "no authoritative certifiable measurement record found"
                                if not record
                                else "record not certifiable"
                            ),
                            "path": mm.authoritative_evidence_path or "",
                        }
                    )

                # Inject a revalidation task
                if kind == "mutation":
                    target = CAPABILITY_TO_MUTATION_TARGET.get(cap, "")
                    if not target:
                        new_tasks.append(
                            ExecutionTaskSpec(
                                task_id=f"exec-{next_id:04d}",
                                source_task_id=f"revalidate::{cap}::mutation",
                                primary_capability=cap,
                                capabilities=(cap,),
                                verification_kind="mutation",
                                command=(
                                    f".venv/bin/python -m runtime.verify mutation "
                                    f"--target {component} --json"
                                    if component
                                    else ""
                                ),
                                profile="mutation",
                                scope="mutation",
                                is_mandatory=mm.required_for_certification,
                                is_escalation=False,
                                reason=(
                                    f"revalidation: {cap} mutation evidence is "
                                    f"{'stale' if record else 'missing'} for "
                                    f"certification"
                                ),
                                origin=TaskOrigin.REVALIDATION.value,
                                required_environment=(
                                    ".venv",
                                    "mutmut==3.7.0",
                                    "git",
                                ),
                                expected_evidence=(
                                    "mutation_score",
                                    "survivor_intel",
                                ),
                                measurement_required=("mutation",),
                                authorization_required=True,
                                # M10-R3 C: shared with mutation_runner so the
                                # declared budget and the enforced one are named in
                                # one place. The two still DIFFER
                                # (DEFAULT_RUNTIME["target"] = 4200 is enforced);
                                # the divergence is recorded on every result rather
                                # than silently tolerated, and
                                # DECLARED_MUTATION_TIMEOUT_SECONDS is asserted
                                # against this site by test.
                                timeout_seconds=DECLARED_MUTATION_TIMEOUT_SECONDS,
                                estimated_duration_seconds=DECLARED_MUTATION_TIMEOUT_SECONDS,
                                mutation_target=component,
                            )
                        )
                    else:
                        new_tasks.append(
                            ExecutionTaskSpec(
                                task_id=f"exec-{next_id:04d}",
                                source_task_id=f"revalidate::{cap}::mutation",
                                primary_capability=cap,
                                capabilities=(cap,),
                                verification_kind="mutation",
                                command=(
                                    f".venv/bin/python -m runtime.verify mutation "
                                    f"--target {target} --json"
                                ),
                                profile="mutation",
                                scope="mutation",
                                is_mandatory=mm.required_for_certification,
                                is_escalation=False,
                                reason=(
                                    f"revalidation: {cap} mutation evidence is "
                                    f"{'stale' if record else 'missing'} for "
                                    f"certification"
                                ),
                                origin=TaskOrigin.REVALIDATION.value,
                                required_environment=(
                                    ".venv",
                                    "mutmut==3.7.0",
                                    "git",
                                ),
                                expected_evidence=(
                                    "mutation_score",
                                    "survivor_intel",
                                ),
                                measurement_required=("mutation",),
                                authorization_required=True,
                                # M10-R3 C: shared with mutation_runner so the
                                # declared budget and the enforced one are named in
                                # one place. The two still DIFFER
                                # (DEFAULT_RUNTIME["target"] = 4200 is enforced);
                                # the divergence is recorded on every result rather
                                # than silently tolerated, and
                                # DECLARED_MUTATION_TIMEOUT_SECONDS is asserted
                                # against this site by test.
                                timeout_seconds=DECLARED_MUTATION_TIMEOUT_SECONDS,
                                estimated_duration_seconds=DECLARED_MUTATION_TIMEOUT_SECONDS,
                                mutation_target=target,
                            )
                        )
                elif kind == "coverage":
                    scope = mm.scope or "tests/unit/engines"
                    if (
                        cap == "api-contracts"
                        or "contract" in cap
                        or scope in {"backend", "backend/src", "."}
                    ):
                        scope = "."
                    # Defer emission: group by resolved scope, emit one task per
                    # scope once every capability has been visited. `next_id` is
                    # consumed here so the ids stay dense, but the id is only
                    # provisional — the task is built at the end of the function.
                    group = coverage_groups.get(scope)
                    if group is None:
                        group = {
                            "scope": scope,
                            "capabilities": [],
                            "reasons": [],
                            "mandatory": False,
                            "task_id": f"exec-{next_id:04d}",
                        }
                        coverage_groups[scope] = group
                    group["capabilities"].append(cap)
                    group["reasons"].append(f"{cap} {'stale' if record else 'missing'}")
                    # A measurement required for certification makes the whole
                    # scope's single execution mandatory.
                    if mm.required_for_certification:
                        group["mandatory"] = True
                    next_id += 1
                    continue
                next_id += 1

        # Emit one coverage revalidation task per distinct resolved scope. The
        # per-capability narrative is untouched: `revalidation_sources` above still
        # carries one entry per capability, and the per-capability record files are
        # materialised from this single measurement by
        # `fan_out_shared_measurement_records`.
        for scope in sorted(coverage_groups):
            group = coverage_groups[scope]
            caps = sorted(group["capabilities"])
            lead = caps[0]
            new_tasks.append(
                ExecutionTaskSpec(
                    task_id=group["task_id"],
                    source_task_id="revalidate::" + ",".join(caps) + "::coverage",
                    primary_capability=lead,
                    capabilities=tuple(caps),
                    verification_kind="coverage",
                    command=(
                        f".venv/bin/python -m runtime.verify measurement "
                        f"coverage {scope} --out "
                        f"{REPO_ROOT / 'runtime' / 'generated' / 'm9-c49' / 'measurements' / f'measurement-truth-{lead}-coverage.json'}"
                    ),
                    profile="coverage",
                    scope="coverage",
                    is_mandatory=bool(group["mandatory"]),
                    is_escalation=False,
                    reason=(
                        "revalidation: shared coverage measurement for scope "
                        f"{scope!r} serving {len(caps)} capabilit"
                        f"{'y' if len(caps) == 1 else 'ies'} — "
                        + "; ".join(group["reasons"])
                        + f" (single execution; records fanned out to {', '.join(caps)})"
                    ),
                    origin=TaskOrigin.REVALIDATION.value,
                    required_environment=(".venv", "coverage"),
                    expected_evidence=("measurement_truth",),
                    measurement_required=("coverage",),
                    authorization_required=False,
                    timeout_seconds=1800,
                    estimated_duration_seconds=1800,
                )
            )
        self._last_coverage_groups = {
            scope: sorted(group["capabilities"])
            for scope, group in coverage_groups.items()
        }

        # Re-sort: revalidation tasks are mandatory, ordered after control-plane
        # mandatory tasks but before escalation tasks. Keep deterministic order
        # by (origin, primary_cap, command).
        new_tasks.sort(key=lambda t: (t.origin, t.primary_capability, t.command))
        return new_tasks, revalidation_sources, reusable

    def _find_measurement_record(self, cap_id: str, kind: str, mapping_path: str):
        from runtime.foundation.verification.measurement_truth import (
            load_measurement_truth,
        )

        candidates: list[Path] = []
        for d in [Path(p) for p in self._measurement_search_dirs if p]:
            if d.is_dir():
                candidates.extend(sorted(d.glob(f"measurement-truth-*-{kind}.json")))
                candidates.extend(sorted(d.glob("measurement-truth*.json")))
        if mapping_path:
            p = Path(mapping_path)
            if not p.is_absolute():
                p = REPO_ROOT / p
            candidates.insert(0, p)
        # Per-capability defaults
        for search_dir in self._measurement_search_dirs:
            dd = Path(search_dir)
            if not dd.is_absolute():
                dd = REPO_ROOT / dd
            candidates.append(dd / f"measurement-truth-{cap_id}.json")
        # Default durable locations
        for default in [
            REPO_ROOT
            / "backend"
            / "tests"
            / "generated"
            / "mutation"
            / f"measurement-truth-{cap_id}.json",
            REPO_ROOT
            / "backend"
            / "tests"
            / "generated"
            / "mutation"
            / "local-smoke"
            / "measurement-truth.json",
            REPO_ROOT
            / "runtime"
            / "generated"
            / "m9-c47"
            / "coverage"
            / "measurement-truth-coverage.json",
            REPO_ROOT
            / "runtime"
            / "generated"
            / "m9-c47"
            / f"measurement-truth-{cap_id}.json",
        ]:
            candidates.append(default)
        for path in candidates:
            if not path.exists():
                continue
            try:
                rec = load_measurement_truth(path)
            except Exception:
                continue
            if rec.measurement_kind != kind:
                continue
            # A record only speaks for the scope it actually measured.
            #
            # The candidate list ends in generic, non-per-capability locations —
            # `backend/tests/generated/mutation/local-smoke/measurement-truth.json`
            # and `.../measurement-truth-coverage.json` — and the only filter
            # applied before this point was `measurement_kind`. So a single
            # generic file was accepted as the measurement for *every*
            # capability whose own path was absent.
            #
            # That is not hypothetical. The reuse guard requires an
            # authoritative record at the live SHA, and before the record-minting
            # order was fixed, freshly measured records were always derived, so
            # the guard never fired and the defect stayed hidden. Fixing the
            # minting exposed it: `local-smoke/measurement-truth.json` — a
            # 6-mutant smoke probe of a scratch file, `requested_scope:
            # "probe.py"`, `mode: "smoke"`, score 50% — was consumed as the
            # authoritative mutation measurement for ledger, loan-engine *and*
            # reconciliation, and certification failed on
            # "mutation score 50.0 < 80.0" for all three.
            #
            # For mutation the capability's target is unambiguous
            # (`CAPABILITY_TO_MUTATION_TARGET`), so require the record to name
            # that target and refuse a smoke-mode record outright. Coverage needs
            # the same discipline and it is stricter still: every engine
            # capability declares the coverage scope `tests/unit/engines`, while
            # the single shared record in the candidate list measured
            # `tests/unit/engines/credit_card`. Containment would accept it —
            # that path is inside the declared scope — but a measurement taken
            # over one engine's tests is not coverage evidence for another
            # engine, so the record's scope must *equal* the declared scope.
            #
            # Both checks only ever refuse. A refused record causes the
            # measurement to be re-run, which is the safe direction: it can
            # never let a campaign certify on evidence it did not produce.
            if kind == "mutation":
                target = CAPABILITY_TO_MUTATION_TARGET.get(cap_id)
                if not target:
                    continue
                scopes = {
                    str(getattr(rec, "requested_scope", "") or ""),
                    str(getattr(rec, "actual_scope", "") or ""),
                    str(getattr(rec, "target", "") or ""),
                }
                if target not in scopes:
                    continue
                if str(getattr(rec, "mode", "") or "") == "smoke":
                    continue
            else:
                expected = self._component_for_mapping(cap_id, kind)
                if expected:
                    got = {
                        str(getattr(rec, "requested_scope", "") or ""),
                        str(getattr(rec, "actual_scope", "") or ""),
                    }
                    if expected not in got:
                        continue
            return rec, path
        return None, None

    def _component_for_mapping(self, cap_id: str, kind: str) -> str:
        if kind == "mutation":
            return CAPABILITY_TO_MUTATION_TARGET.get(cap_id, "")
        if kind == "coverage":
            contract = self._contract_registry.get_contract(cap_id)
            if contract and contract.measurement_mappings:
                for mm in contract.measurement_mappings:
                    if mm.measurement_kind.value == "coverage":
                        return mm.scope
        return ""

    # ----------------------------------------------------------------------

    def _add_dependency_edges(self, tasks: list[ExecutionTaskSpec]) -> None:
        """Mark escalation tasks as depending on all mandatory tasks (so the
        orchestrator can decide skip vs. run at execution time)."""
        mandatory_ids = {t.task_id for t in tasks if t.is_mandatory}
        for i, t in enumerate(tasks):
            if t.is_escalation and not t.depends_on:
                tasks[i] = ExecutionTaskSpec.from_dict(
                    {**t.to_dict(), "depends_on": tuple(sorted(mandatory_ids))}
                )

    def _compute_plan_fingerprint(
        self,
        source_plan_id: str,
        live_fp: RepositoryFingerprint,
        changed_files: list[str],
        tasks: list[ExecutionTaskSpec],
    ) -> str:
        h = hashlib.sha256()
        h.update(source_plan_id.encode("utf-8"))
        h.update(live_fp.fingerprint.encode("utf-8"))
        for f in sorted(changed_files):
            h.update(f.encode("utf-8"))
        for t in tasks:
            h.update(
                "|".join(
                    [
                        t.task_id,
                        ",".join(t.capabilities),
                        t.verification_kind,
                        t.command,
                        str(int(t.is_mandatory)),
                        str(int(t.is_escalation)),
                        str(t.timeout_seconds),
                        str(int(t.authorization_required)),
                        t.origin,
                    ]
                ).encode("utf-8")
            )
        return h.hexdigest()

    def _build_rationale(
        self,
        cp,
        tasks: list[ExecutionTaskSpec],
        reusable: list[dict],
        revalidation_sources: list[dict],
    ) -> str:
        mandatory = sum(1 for t in tasks if t.is_mandatory)
        escalation = sum(1 for t in tasks if t.is_escalation)
        reused = len(reusable)
        revals = len(revalidation_sources)
        return (
            f"Plan built from C48 control-plane {cp.plan_id} for "
            f"{len(cp.changed_files)} changed file(s). Selected "
            f"{len(cp.capability_resolution.directly_affected_capabilities)} "
            f"directly + "
            f"{len(cp.capability_resolution.transitively_affected_capabilities)} "
            f"transitively affected capabilities. Mandatory tasks: {mandatory}; "
            f"escalation tasks: {escalation}; reusable measurements: {reused}; "
            f"revalidation injections: {revals}. "
            f"Mutation is a single capability among many; full mutation campaigns "
            f"require explicit authorization. Stop-on-sufficiency rule applies: "
            f"escalation tasks are skipped when all mandatory tasks are PASS or REUSED."
        )

    def _collect_components(self, tasks: list[ExecutionTaskSpec]) -> list[str]:
        comps: set[str] = set()
        for t in tasks:
            comps.update(_capability_components(list(t.capabilities)))
            if t.mutation_target:
                comps.add(t.mutation_target)
        return sorted(comps)

    def _get_inventory_map(self) -> dict[str, Any]:
        try:
            from runtime.foundation.verification.command_inventory import (
                get_command_inventory,
            )

            inv = get_command_inventory()
        except Exception:
            return {}
        out: dict[str, Any] = {}
        for cmd in inv.commands:
            if cmd.profile_name:
                out.setdefault(cmd.profile_name, cmd)
            if cmd.command_id:
                out.setdefault(cmd.command_id, cmd)
        return out

    def _timeout_for(self, cp_task, inv_entry, fallback: int) -> int:
        kind = cp_task.verification_kind
        if kind in self._max_runtime_overrides:
            return self._max_runtime_overrides[kind]
        if inv_entry and inv_entry.estimated_duration_seconds:
            return max(60, int(inv_entry.estimated_duration_seconds) * 2)
        if cp_task.estimated_duration_seconds:
            return max(60, int(cp_task.estimated_duration_seconds) * 2)
        return fallback

    # ------------------------------------------------------------- validation

    def validate_execution(
        self, plan: ExecutionPlan
    ) -> tuple[list[str], RepositoryFingerprint]:
        """Validate plan + repository fingerprint. Returns (errors, live_fp)."""
        errors: list[str] = []
        errors.extend(plan.validate())
        live_fp = RepositoryFingerprint.capture()
        if not plan.repository_fingerprint.matches(live_fp):
            errors.append(
                "repository state changed since plan was built "
                f"(plan_fp={plan.repository_fingerprint.fingerprint[:12]} "
                f"vs live_fp={live_fp.fingerprint[:12]})"
            )
        return errors, live_fp

    def verify_prerequisites(
        self,
        plan: ExecutionPlan,
        ctx: ExecutionContext | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[bool, list[str]]:
        """Verify every declared environment requirement, before any spawn.

        M10-R3 (B1). This used to verify repository *paths only*, and to skip five
        of its own declared values outright (``.venv``, ``git``,
        ``mutmut==3.7.0``, ``pytest``, ``coverage``) — so it never once checked a
        tool, a version, or an environment variable. The ``required_environment``
        field that was supposed to carry those was read by nothing outside its own
        serialiser.

        It now resolves all three forms through
        :func:`verify_environment_requirement`, which is the single place an
        environment requirement is decided. Every failure names the task, the
        form, the requirement and what was actually found — so a missing
        prerequisite is a *named prerequisite failure at second zero* instead of a
        non-zero exit several minutes later with the real cause in a log nobody
        was watching.

        Returns ``(ok, rendered_failures)``. ``rendered_failures`` is a list of
        human-readable strings for backward compatibility with the existing
        ``missing prerequisites: ...`` report line; the structured failures are
        available via :meth:`collect_requirement_failures`.
        """
        failures = self.collect_requirement_failures(plan, ctx=ctx, env=env)
        return (not failures), [f.render() for f in failures]

    def collect_requirement_failures(
        self,
        plan: ExecutionPlan,
        ctx: ExecutionContext | None = None,
        env: dict[str, str] | None = None,
    ) -> list[RequirementFailure]:
        """Structured form of :meth:`verify_prerequisites`.

        Kept separate because the call sites that *report* want strings and the
        call sites that *classify* want the form and the detail.
        """
        if ctx is None:
            ctx = ExecutionContext(workspace=str(REPO_ROOT), plan_id=plan.plan_id)
        if env is None:
            from runtime.foundation.verification.env import child_process_env

            env = dict(child_process_env())

        failures: list[RequirementFailure] = []

        # Global requirements. These are the repository-level preconditions every
        # obligation inherits; they are reported against the plan itself because
        # they are not any one task's declaration.
        if not (REPO_ROOT / ".venv" / "bin" / "python").exists():
            failures.append(
                RequirementFailure(
                    "<plan>",
                    _REQUIREMENT_FORM_PATH,
                    ".venv/bin/python",
                    "the canonical virtualenv interpreter is missing; run "
                    "scripts/bootstrap.sh",
                )
            )
        for path in (".git", "backend", "pyproject.toml"):
            if not (REPO_ROOT / path).exists():
                failures.append(
                    RequirementFailure(
                        "<plan>",
                        _REQUIREMENT_FORM_PATH,
                        path,
                        "required repository path is missing",
                    )
                )

        for t in plan.tasks:
            failures.extend(
                verify_task_environment(t.task_id, t.required_environment, ctx, env)
            )
        return failures

    # ------------------------------------------------------------- execution

    def execute(
        self,
        plan: ExecutionPlan,
        authorize: set[str] | None = None,
        dry_run: bool = False,
        on_record: Callable[[TaskExecutionRecord], None] | None = None,
    ) -> ExecutionReport:
        """Execute the plan and produce an ExecutionReport.

        * ``authorize`` is a set of task_ids (or profile names) for which the
          operator has explicitly authorized production-affecting work. Tasks
          that are not authorized but require authorization transition to
          AUTHORIZATION_REQUIRED without executing.
        * ``dry_run`` plans and validates but never runs commands; useful for
          acceptance tests and inspection.
        * ``on_record`` is an optional callback invoked with each
          TaskExecutionRecord as it is produced. Callers use it to observe
          in-flight progress (and to capture partial progress if the run is
          interrupted) without changing orchestration semantics.
        """
        authorize = set(authorize or [])
        validation_errors, live_fp = self.validate_execution(plan)
        if validation_errors:
            report = self._blocked_report(plan, validation_errors, live_fp)
            return report

        prereq_ok, prereq_missing = self.verify_prerequisites(plan)
        if not prereq_ok:
            report = self._blocked_report(
                plan,
                [f"missing prerequisites: {', '.join(prereq_missing)}"],
                live_fp,
            )
            return report

        if dry_run:
            report = self._dry_run_report(plan, live_fp)
            return report

        records: list[TaskExecutionRecord] = []
        evidence_reused: list[str] = []
        escalations_triggered: list[str] = []
        decisions: list[dict] = []
        started_at = datetime.now(UTC).isoformat()
        t0 = time.monotonic()

        def _push_record(rec: TaskExecutionRecord) -> None:
            records.append(rec)
            if on_record is not None:
                on_record(rec)

        # Section 6 stop-on-sufficiency state
        any_mandatory_fail = False

        # M10-R2 (C3d): the anti-tamper invariant is now checked once around the
        # fan-out instead of once per task. See `_fingerprint_integrity_record` for
        # why this is strictly stronger, not weaker.
        #
        # M10-R2 (C3b): independent tasks run concurrently. Escalation tasks are a
        # barrier, not a fan-out unit — `_add_dependency_edges` gives every one of
        # them `depends_on = <all mandatory task ids>`, and stop-on-sufficiency is
        # only decidable once the mandatory set has a complete result. They run
        # after, in plan order, exactly as before.
        independent = [s for s in plan.tasks if not s.is_escalation]
        barrier = [s for s in plan.tasks if s.is_escalation]

        def _execute_independent(
            spec: ExecutionTaskSpec,
        ) -> TaskExecutionRecord:
            """Reuse/re-authorization gates, then execute. Pure per-task work."""
            # Evidence reuse: for measurement tasks, check the persistent record
            # before executing (Section 6).
            if _measurement_kind_for_task(spec):
                reusable = self._check_reusable_measurement(spec, live_fp)
                if reusable is not None:
                    return (
                        self._make_record(
                            spec,
                            plan,
                            exit_code=0,
                            state=CompletionState.REUSED,
                            reason_text=(
                                f"authoritative {spec.verification_kind} record reused "
                                f"from {reusable.get('path', '?')}"
                            ),
                            stderr_tail=[],
                            measurement_truth={
                                "kind": spec.verification_kind,
                                "path": reusable.get("path", ""),
                                "score": reusable.get("score"),
                                "repository_sha": reusable.get("repository_sha", ""),
                                "completion_status": "AUTHORITATIVE_COMPLETE",
                            },
                        ),
                        reusable,
                    )

            if spec.authorization_required and spec.task_id not in authorize:
                return (
                    self._make_record(
                        spec,
                        plan,
                        exit_code=-1,
                        state=CompletionState.AUTHORIZATION_REQUIRED,
                        reason_text=(
                            "task requires human authorization; not authorized at "
                            "execution time — no production changes attempted"
                        ),
                        stderr_tail=[],
                        diagnostic={
                            "stage": FailureStage.AUTHORIZATION_REQUIRED.value,
                            "message": "operator must pass --authorize to run",
                        },
                        next_action=(
                            "review capability / component / required evidence and "
                            "rerun with --authorize <task_id> or --authorize all"
                        ),
                    ),
                    None,
                )

            return self._execute_task(spec, plan, live_fp), None

        def _run_one(
            spec: ExecutionTaskSpec,
        ) -> tuple[TaskExecutionRecord, Any]:
            try:
                return _execute_independent(spec)
            except Exception as exc:  # noqa: BLE001 - one task must not erase the rest
                return (
                    self._make_record(
                        spec,
                        plan,
                        exit_code=None,
                        state=CompletionState.INFRASTRUCTURE,
                        reason_text=f"orchestrator raised {type(exc).__name__}: {exc}",
                        stderr_tail=[],
                    ),
                    None,
                )

        # Collect into plan order regardless of completion order, so evidence output
        # can never depend on scheduling.
        #
        # M10-R2: mutation and authorization-gated tasks run on the *calling*
        # thread. mutmut installs signal handlers (ValueError off the main thread)
        # and rewrites source, so it must neither race the pool nor the fingerprint
        # hash. Everything else — including coverage, which is one of the longest
        # tasks and was proven safe concurrently — fans out.
        main_thread_tasks = [s for s in independent if self._requires_main_thread(s)]
        concurrent_tasks = [s for s in independent if not self._requires_main_thread(s)]

        outcomes_by_id: dict[str, Any] = {}
        for spec, outcome in zip(
            concurrent_tasks,
            execute_tasks_in_parallel(concurrent_tasks, _run_one),
            strict=True,
        ):
            outcomes_by_id[spec.task_id] = outcome
        for spec in main_thread_tasks:
            try:
                outcomes_by_id[spec.task_id] = _run_one(spec)
            except Exception as exc:  # noqa: BLE001 - one task must not erase the rest
                outcomes_by_id[spec.task_id] = exc

        independent_outcomes = [outcomes_by_id[spec.task_id] for spec in independent]

        for spec, outcome in zip(independent, independent_outcomes, strict=True):
            if isinstance(outcome, Exception):
                record, reusable = (
                    self._make_record(
                        spec,
                        plan,
                        exit_code=None,
                        state=CompletionState.INFRASTRUCTURE,
                        reason_text=f"worker raised {type(outcome).__name__}: {outcome}",
                        stderr_tail=[],
                    ),
                    None,
                )
            else:
                record, reusable = outcome
            _push_record(record)
            if reusable is not None:
                evidence_reused.append(spec.task_id)
            if spec.authorization_required and (
                record.completion_state == CompletionState.AUTHORIZATION_REQUIRED
            ):
                escalations_triggered.append(spec.task_id)
            if spec.is_mandatory and record.completion_state in NON_PASS_STATES:
                any_mandatory_fail = True
            if record.completion_state is CompletionState.FAILED:
                decisions.append(
                    {
                        "stage": "diagnostic",
                        "task_id": spec.task_id,
                        "decision": record.next_action,
                        "failure_stage": (record.diagnostic or {}).get(
                            "stage", FailureStage.NONE.value
                        ),
                    }
                )

        # Escalation barrier: stop-on-sufficiency is now decidable because the
        # mandatory set has a complete result.
        for spec in barrier:
            if not any_mandatory_fail:
                _push_record(
                    self._make_record(
                        spec,
                        plan,
                        exit_code=0,
                        state=CompletionState.SKIPPED,
                        reason_text=(
                            "stop-on-sufficiency: all mandatory tasks PASS or REUSED; "
                            "escalation skipped"
                        ),
                        stderr_tail=[],
                    )
                )
                continue

            outcome = _run_one(spec)
            record = outcome[0]
            _push_record(record)
            if record.completion_state is CompletionState.FAILED:
                decisions.append(
                    {
                        "stage": "diagnostic",
                        "task_id": spec.task_id,
                        "decision": record.next_action,
                        "failure_stage": (record.diagnostic or {}).get(
                            "stage", FailureStage.NONE.value
                        ),
                    }
                )

        # M10-R2 (C3d): capture the fingerprint once more, after every task has finished,
        # and enforce the same invariant the per-task check used to.
        #
        # This is strictly stronger than the pre-M10-R2 behaviour, which only
        # observed the tree *between* tasks: a change made during the final task — or
        # after the last task but before the decision — was missed. Here it cannot be.
        #
        # The verdict is also identical: `_finalize` maps any SCOPE record to
        # VALIDATION_BLOCKED, so no new decision value and no threshold change is
        # introduced. What is lost is the early `break`, which is recorded explicitly
        # in `decisions` so the evidence does not claim work was abandoned when it was
        # in fact completed and then rejected for provenance.
        fp_integrity = self._check_fingerprint_integrity(plan, live_fp)
        if fp_integrity is not None:
            _push_record(fp_integrity)
            decisions.append(
                {
                    "stage": "in_flight",
                    "decision": "repository-integrity-check-failed",
                    "reason": (
                        "the repository changed during execution; results are rejected "
                        "for provenance. Pre-M10-R2 this was only observable between "
                        "tasks, so a change during the final task went undetected."
                    ),
                    "fingerprint_before": live_fp.fingerprint[:12],
                    "fingerprint_after": fp_integrity.fingerprint_after[:12],
                }
            )

        # M10-R2 (C1b). If coverage was measured once for a scope shared by several
        # capabilities, materialise the per-capability records now — before the
        # decision — so `_finalize`'s per-capability lookups resolve exactly as they
        # did when each capability ran its own copy. Runs unconditionally and is a
        # no-op when the plan had no shared coverage group.
        try:
            fanned = self.fan_out_shared_measurement_records()
        except Exception as exc:  # never let bookkeeping fail a verification
            fanned = []
            print(
                f"[orchestrator] coverage record fan-out skipped: "
                f"{type(exc).__name__}: {exc}"
            )
        if fanned:
            print(
                f"[orchestrator] fanned out {len(fanned)} shared coverage record(s)",
                file=sys.stderr,
            )

        # Finalize.
        final_decision, reason = self._finalize(plan, records, live_fp)
        report_id = (
            "report-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|" + started_at).encode("utf-8")
            ).hexdigest()[:12]
        )
        efficiency = self._compute_efficiency(plan, records)
        return ExecutionReport(
            report_id=report_id,
            plan_id=plan.plan_id,
            plan_fingerprint=plan.plan_fingerprint,
            started_at=started_at,
            completed_at=datetime.now(UTC).isoformat(),
            total_duration_seconds=time.monotonic() - t0,
            records=records,
            efficiency=efficiency,
            final_decision=final_decision.value,
            decision_reason=reason,
            evidence_reused=evidence_reused,
            escalations_triggered=escalations_triggered,
            decisions=decisions,
        )

    @staticmethod
    def _requires_main_thread(spec: ExecutionTaskSpec) -> bool:
        """Tasks that must not run on a worker thread, and why.

        Discovered by running the plan, not by inspection: with the fan-out enabled,
        ``exec-0007`` failed with ``ValueError: signal only works in main thread of
        the main interpreter`` because mutmut installs a signal handler when it runs.
        A ``ThreadPoolExecutor`` worker is not the main thread, so the handler
        registration raises and the mutation campaign never starts.

        Two classes are excluded:

        * **Mutation tasks** (``verification_kind == "mutation"``, or any spec
          carrying a ``mutation_target``). They need the main thread for signal
          handlers, *and* they rewrite source files while the run is in flight —
          exactly the race the fingerprint check guards against. Running one
          concurrently with a coverage measurement walking ``backend/src`` would
          produce spurious ``VALIDATION_BLOCKED`` verdicts.
        * **Authorization-gated tasks.** By definition these are the sensitive
          ones; they run serially so their side effects stay ordered and
          observable.

        Coverage is deliberately *not* excluded: it was exercised concurrently and
        passes, and it is one of the longest tasks, so excluding it would cost most
        of the win.
        """
        if spec.authorization_required:
            return True
        return bool(spec.verification_kind == "mutation" or spec.mutation_target)

    def _check_fingerprint_integrity(
        self,
        plan: ExecutionPlan,
        live_fp: RepositoryFingerprint,
    ) -> TaskExecutionRecord | None:
        """M10-R2 (C3d). Enforce the anti-tamper invariant around the fan-out.

        Returns a SCOPE record when the repository changed while tasks were running,
        or ``None`` when the state is intact.

        The invariant is unchanged in *meaning*: the evidence in this report must
        describe the repository state the plan was built against. Only the *when*
        moved. Previously the comparison happened per task, which had two defects
        under fan-out — it could not work (no single "between tasks" instant), and it
        re-walked all of ``backend/src`` on every iteration for a check that only has
        two interesting moments.
        """
        after = RepositoryFingerprint.capture()
        if after.fingerprint == live_fp.fingerprint:
            return None
        spec = ExecutionTaskSpec(
            task_id="fingerprint-integrity",
            source_task_id="orchestrator::fingerprint-integrity",
            primary_capability="orchestration",
            capabilities=("orchestration",),
            verification_kind="integrity",
            command="",
            profile="orchestration",
            scope="integrity",
            is_mandatory=True,
            is_escalation=False,
            reason="repository state changed during execution",
            origin=TaskOrigin.CONTROL_PLANE.value,
        )
        record = self._make_record(
            spec,
            plan,
            exit_code=-1,
            state=CompletionState.SCOPE,
            reason_text=(
                "repository state changed during execution: "
                f"before={live_fp.fingerprint[:12]} after={after.fingerprint[:12]} "
                "— evidence rejected for provenance; re-run"
            ),
            stderr_tail=[],
            diagnostic={
                "stage": FailureStage.INVALID_SCOPE.value,
                "message": "repository fingerprint changed during verification",
                "fingerprint_before": live_fp.fingerprint,
                "fingerprint_after": after.fingerprint,
            },
            next_action=(
                "re-run verification; if the tree is expected to change during a "
                "task, that task is not safe to run inside a fan-out"
            ),
            duration_seconds=0.0,
        )
        # `fingerprint_after` is surfaced on the record so the two values are
        # available without re-capturing a state that has already moved on.
        object.__setattr__(record, "fingerprint_after", after.fingerprint)
        return record

    def _execute_task(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        live_fp: RepositoryFingerprint,
    ) -> TaskExecutionRecord:
        # If a per-kind override is set, route through the shell path so
        # the override substitution applies (the internal runners ignore
        # the command string).
        if f"kind:{spec.verification_kind}" in self._command_overrides:
            return self._execute_shell_task(spec, plan)
        if spec.command in self._command_overrides:
            return self._execute_shell_task(spec, plan)
        # Internal measurement executor: for measurement revalidation tasks,
        # route through the native mutmut runner (Section 8 — mutation is one
        # verification capability among many, run via internal runner).
        if spec.verification_kind == "mutation" and spec.mutation_target:
            return self._execute_measurement_task(spec, plan, live_fp)
        if spec.verification_kind == "coverage":
            return self._execute_coverage_task(spec, plan, live_fp)
        # Default: shell command
        return self._execute_shell_task(spec, plan)

    def _execute_shell_task(
        self, spec: ExecutionTaskSpec, plan: ExecutionPlan
    ) -> TaskExecutionRecord:
        """Execute a shell task via the promoted streaming worker (M10-R2).

        The process execution itself lives in
        ``parallel_executor.run_streaming_command`` so this module and the profile
        path share one worker. What stays here is the record/classification layer,
        because only the orchestrator owns ``TaskExecutionRecord`` and
        ``CompletionState``.
        """
        command = self._resolve_command(spec)
        log_dir = self._evidence_root / "logs" / plan.plan_id
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = log_dir / f"{spec.task_id}-stdout.log"
        stderr_path = log_dir / f"{spec.task_id}-stderr.log"

        # Canonical child environment (M9-C57): venv-first PATH + ED7 locale/TZ,
        # shared with executor.py via env.child_process_env.
        from runtime.foundation.verification.env import child_process_env

        # M10-R2 closeout: live per-task lifecycle logging. Composed here so the label
        # carries the leg AND the canonical task id — the reconcile shard log line that
        # reads `shard=1/7 ... tasks=playwright-e2e` is what makes a failing leg
        # diagnosable without waiting for its artifact.
        progress = None
        if self._progress_prefix:
            from runtime.foundation.verification.parallel_executor import (
                ProgressContext,
            )

            progress = ProgressContext(
                label=f"{self._progress_prefix}/{spec.task_id}",
                kind="task",
                log_dir=log_dir,
                timeout_seconds=spec.timeout_seconds,
            )

        result = run_streaming_command(
            command,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_seconds=spec.timeout_seconds,
            cwd=REPO_ROOT,
            env=child_process_env(),
            progress=progress,
        )

        exit_code = result.exit_code
        timed_out = result.timed_out
        infra_error = result.infra_error
        stdout_data = result.stdout
        stderr_data = result.stderr
        duration = result.duration_seconds
        artifacts: list[str] = [str(stdout_path), str(stderr_path)]

        if infra_error:
            state = CompletionState.INFRASTRUCTURE
            reason_text = infra_error
        elif timed_out:
            state = CompletionState.TIMEOUT
            reason_text = f"command exceeded {spec.timeout_seconds}s"
        elif exit_code == 0:
            state = CompletionState.PASS
            reason_text = "command exit 0"
        else:
            # Reclassify infrastructure signals from stderr before defaulting to
            # FAILED — an actual runtime FileNotFoundError or ModuleNotFoundError
            # means the verification surface itself is broken (not a test assertion
            # failure).
            infra_signals = (
                "FileNotFoundError",
                "No such file or directory",
                "ModuleNotFoundError",
                "command not found",
                "Permission denied",
                "No such command",
            )
            stderr_text = (stderr_data or "") + "\n" + (stdout_data or "")
            if any(sig in stderr_text for sig in infra_signals) or exit_code == 127:
                state = CompletionState.INFRASTRUCTURE
                reason_text = (
                    f"infrastructure error (exit {exit_code}): "
                    f"{stderr_text.strip()[:200]}"
                )
            else:
                state = CompletionState.FAILED
                reason_text = f"command exit {exit_code}"

        diag = self._diagnose(spec, state, stderr_data, stdout_data)
        next_action = self._next_action(spec, state, diag)
        termination = _classify_termination(exit_code, timed_out, infra_error)
        pytest_detail = _summarise_pytest_outcome(stdout_data + "\n" + stderr_data)
        if pytest_detail and state is not CompletionState.PASS:
            diag = dict(diag or {})
            diag.setdefault("pytest", pytest_detail)
            termination = dict(termination)
            termination["inner"] = pytest_detail
            if not timed_out and not infra_error and exit_code != 0:
                # Keep the wrapper's EXIT_NONZERO but say what the inner run
                # actually was, so the two are never confused.
                termination["kind"] = "EXIT_NONZERO_WITH_INNER_" + pytest_detail["kind"]
        return self._make_record(
            spec,
            plan,
            exit_code=exit_code,
            state=state,
            reason_text=reason_text,
            stderr_tail=stderr_data.splitlines()[-20:],
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            artifacts=artifacts,
            diagnostic=diag,
            next_action=next_action,
            duration_seconds=duration,
            termination=termination,
        )

    def _execute_measurement_task(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        live_fp: RepositoryFingerprint,
    ) -> TaskExecutionRecord:
        from runtime.foundation.verification.measurement_truth import (
            EvidenceClassification,
            FailureClassification,
            MeasurementCompletionStatus,
            MeasurementKind,
            MeasurementTruthRecord,
            PopulationAccounting,
            certification_gate,
            classify_completion,
            save_measurement_truth,
            set_evidence_fingerprint,
        )

        started = datetime.now(UTC)
        t0 = time.monotonic()
        try:
            from runtime.foundation.verification.mutation_runner import (
                execute_mutation,
            )

            result = execute_mutation(
                mode="target", target=spec.mutation_target, allow_dirty=True
            )
        except Exception as exc:
            duration = time.monotonic() - t0
            diag = {
                "stage": FailureStage.INFRASTRUCTURE_FAILURE.value,
                "message": f"mutation runner raised: {type(exc).__name__}: {exc}",
            }
            return self._make_record(
                spec,
                plan,
                exit_code=-1,
                state=CompletionState.INFRASTRUCTURE,
                reason_text=str(exc),
                stderr_tail=[diag["message"]],
                diagnostic=diag,
                next_action="verify.py env-check; clean worktree, then re-authorize",
                duration_seconds=duration,
            )

        duration = time.monotonic() - t0
        # Build MeasurementTruthRecord
        if result.execution_status != "PASS":
            state = CompletionState.INFRASTRUCTURE
            reason = result.error or "mutation runner reported infrastructure failure"
        elif result.classification_status != "PASS" or not result.evidence_complete:
            state = CompletionState.EVIDENCE
            reason = (
                "mutation evidence could not be reconciled "
                f"(classification_status={result.classification_status}, "
                f"complete={result.evidence_complete})"
            )
        else:
            state = CompletionState.PASS
            reason = (
                f"targeted mutation: score {result.mutation_score}%, "
                f"killed {result.killed}/{result.mutants_generated}"
            )

        record_path = (
            self._evidence_root
            / "measurements"
            / f"measurement-truth-{spec.primary_capability}-mutation.json"
        )
        record_path.parent.mkdir(parents=True, exist_ok=True)
        truth = MeasurementTruthRecord(
            run_id=result.run_id,
            measurement_kind=MeasurementKind.MUTATION.value,
            repository_sha=result.repository_sha or live_fp.repository_sha,
            tree_sha=result.tree_sha or live_fp.working_tree_hash,
            configuration_fingerprint=result.config_hash or live_fp.config_hash,
            toolchain_fingerprint=live_fp.toolchain_hash,
            environment_fingerprint=live_fp.fingerprint,
            command=f"verify.py mutation --target {spec.mutation_target}",
            requested_scope=spec.mutation_target,
            actual_scope=result.source_scope or spec.mutation_target,
            population=PopulationAccounting(
                requested_generated=result.mutants_generated,
                generated=result.mutants_generated,
                killed=result.killed,
                survived=result.survived,
                no_tests=result.no_tests,
                timeout=result.timeout,
                suspicious=result.suspicious,
                not_checked=result.not_checked,
            ),
            mutation_score=result.mutation_score,
            execution_status=result.execution_status,
            failure_classification=(
                FailureClassification.NONE.value
                if state == CompletionState.PASS
                else FailureClassification.INFRASTRUCTURE.value
            ),
            start_time=started.isoformat(),
            end_time=datetime.now(UTC).isoformat(),
            duration_seconds=duration,
            toolchain_versions={
                "python": result.python_version,
                "pytest": result.pytest_version,
                "mutmut": result.mutmut_version,
            },
            artifact_paths=[str(record_path)],
            # Seed the classification optimistically: the campaign really did
            # just execute. `classify_completion` then downgrades it on its own
            # if the run was partial, timed out, hit an infrastructure error or
            # produced unusable evidence — so a bad run is still refused, and
            # the label is decided by the canonical classifier rather than
            # hard-coded here.
            evidence_classification=EvidenceClassification.AUTHORITATIVE.value,
            mode="target",
            target=spec.mutation_target,
            error=result.error,
        )
        # Order matters. `classify_completion` rejects a record whose
        # `evidence_fingerprint` is empty while it has processed a non-empty
        # population (EVIDENCE_FAILURE), so durability must be stamped *before*
        # classification, not after. Measured on the real records: the ledger,
        # loan-engine and reconciliation campaigns each processed their full
        # population (190/190, 1273/1273, 368/368) with zero timeouts and
        # `failure_classification` "none" at the current repository SHA, and were
        # still refused by certification as "mutation measurement
        # authoritative+current" — because this path left the classification at
        # the dataclass default (DERIVED), never stamped a fingerprint, and so
        # could never mint a consumable record at all.
        #
        # The reuse path in this same file hard-codes
        # `"completion_status": "AUTHORITATIVE_COMPLETE"` for a reused record,
        # so a reused measurement certified while a freshly measured one could
        # not — the inverse of the intended contract.
        #
        # This weakens nothing. `classify_completion` still refuses a partial
        # population, an empty population, a population that does not reconcile,
        # a timeout-classified, infrastructure-failed or interrupted run, and an
        # invalid scope — verified against each case directly. The canonical
        # classifier decides the label, instead of the writer hard-coding one
        # that the gate then refuses.
        set_evidence_fingerprint(truth)
        truth.completion_status = classify_completion(record=truth)
        truth.evidence_classification = (
            EvidenceClassification.AUTHORITATIVE.value
            if truth.completion_status
            == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
            else EvidenceClassification.DERIVED.value
        )
        truth.consumable_by_certification = certification_gate(truth)
        with contextlib.suppress(Exception):
            save_measurement_truth(truth, record_path)

        diag = self._diagnose(spec, state, reason, "")
        next_action = self._next_action(spec, state, diag)
        return self._make_record(
            spec,
            plan,
            exit_code=0 if state == CompletionState.PASS else 1,
            state=state,
            reason_text=reason,
            stderr_tail=[],
            diagnostic=diag,
            next_action=next_action,
            measurement_truth={
                "kind": "mutation",
                "path": str(record_path),
                "score": result.mutation_score,
                "repository_sha": truth.repository_sha,
                "completion_status": truth.completion_status,
                "evidence_classification": truth.evidence_classification,
                "consumable_by_certification": truth.consumable_by_certification,
            },
            duration_seconds=duration,
        )

    def _execute_coverage_task(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        live_fp: RepositoryFingerprint,
    ) -> TaskExecutionRecord:
        # The C49 orchestrator executes coverage via the canonical measurement
        # CLI. We respect a per-task command_overrides substitution so tests
        # can substitute fast commands.
        return self._execute_shell_task(spec, plan)

    def _check_reusable_measurement(
        self, spec: ExecutionTaskSpec, live_fp: RepositoryFingerprint
    ) -> dict | None:
        contract = self._contract_registry.get_contract(spec.primary_capability)
        if not contract:
            return None
        from runtime.foundation.verification.measurement_truth import (
            certification_gate,
        )

        kind = _measurement_kind_for_task(spec)
        if not kind:
            return None
        mm = next(
            (
                m
                for m in contract.measurement_mappings
                if m.measurement_kind.value == kind
            ),
            None,
        )
        if mm is None:
            return None
        record, path = self._find_measurement_record(
            spec.primary_capability, kind, mm.authoritative_evidence_path
        )
        if record is None or not certification_gate(record):
            return None
        if record.repository_sha != live_fp.repository_sha:
            return None
        return {
            "kind": kind,
            "path": str(path),
            "score": (
                record.mutation_score
                if kind == "mutation"
                else record.coverage_result_percent or record.coverage.line_percent
            ),
            "repository_sha": record.repository_sha,
        }

    # ------------------------------------------------------------- diagnose

    def _diagnose(
        self,
        spec: ExecutionTaskSpec,
        state: CompletionState,
        stderr: str,
        stdout: str,
    ) -> dict:
        if state == CompletionState.PASS or state == CompletionState.REUSED:
            return {"stage": FailureStage.NONE.value, "message": "ok"}
        if state == CompletionState.TIMEOUT:
            return {
                "stage": FailureStage.TIMEOUT.value,
                "message": "command exceeded timeout",
            }
        if state == CompletionState.INFRASTRUCTURE:
            return {
                "stage": FailureStage.INFRASTRUCTURE_FAILURE.value,
                "message": stderr[:400] if stderr else "infrastructure error",
            }
        if state == CompletionState.SCOPE:
            return {
                "stage": FailureStage.INVALID_SCOPE.value,
                "message": stderr[:400] if stderr else "scope mismatch",
            }
        if state == CompletionState.CONFIGURATION:
            return {
                "stage": FailureStage.CONFIGURATION_FAILURE.value,
                "message": stderr[:400] if stderr else "configuration error",
            }
        if state == CompletionState.EVIDENCE:
            return {
                "stage": FailureStage.MISSING_EVIDENCE.value,
                "message": stderr[:400] if stderr else "evidence incomplete",
            }
        if state == CompletionState.AUTHORIZATION_REQUIRED:
            return {
                "stage": FailureStage.AUTHORIZATION_REQUIRED.value,
                "message": "human authorization required",
            }
        # FAILED — classify
        text = (stderr or "") + "\n" + (stdout or "")
        if re.search(r"AssertionError|assert .* ==", text):
            stage = FailureStage.ASSERTION_FAILURE
        elif re.search(r"collected 0 items|no tests ran", text):
            stage = FailureStage.MISSING_EVIDENCE
        elif re.search(r"ModuleNotFoundError|ImportError", text):
            stage = FailureStage.CONFIGURATION_FAILURE
        elif re.search(r"\bError\b", text) and re.search(r"line \d+", text):
            stage = FailureStage.CODE_DEFECT
        elif re.search(r"\bFAIL\b|\bFAILED\b|\bE\s+\b", text):
            stage = FailureStage.TEST_FAILURE
        else:
            stage = FailureStage.TOOLING_FAILURE
        return {
            "stage": stage.value,
            "message": (stderr or text).strip()[:400],
        }

    def _next_action(
        self, spec: ExecutionTaskSpec, state: CompletionState, diag: dict
    ) -> str:
        if state in PASSING_STATES:
            return "no action — task satisfied"
        if state == CompletionState.AUTHORIZATION_REQUIRED:
            return (
                "review task profile + measurement history; rerun with explicit "
                "--authorize <task_id> or --authorize all"
            )
        if state == CompletionState.TIMEOUT:
            return (
                "increase timeout for this profile, or run targeted subset; "
                "do not assume the previous score"
            )
        if state == CompletionState.INFRASTRUCTURE:
            return (
                "diagnose infrastructure (verify.py env-check, .venv health) "
                "and rerun; cannot be certified"
            )
        if state == CompletionState.SCOPE:
            return "align requested vs actual scope, then re-plan"
        if state == CompletionState.CONFIGURATION:
            return "verify prerequisites and rerun"
        if state == CompletionState.EVIDENCE:
            return "rerun measurement to capture complete evidence"
        # FAILED — capability-aware diagnostic path
        primary = spec.primary_capability
        return (
            f"run capability-aware diagnostic for {primary} "
            f"(verify.py what-should-i-run failing-test <test> or "
            f"verify.py strengthen-survivor <survivor_id>); "
            f"do not auto-run unrelated tasks"
        )

    # ------------------------------------------------------------- finalize

    def _finalize(
        self,
        plan: ExecutionPlan,
        records: list[TaskExecutionRecord],
        live_fp: RepositoryFingerprint,
    ) -> tuple[FinalDecision, str]:
        """Classify a completed run.

        M10-R3 (B2): this used to carry its own precedence table. It now delegates
        to :func:`decide_final_outcome` — the *same* function the five plan-less
        topologies call — so the orchestrator and a CI shard leg cannot reach
        different verdicts from identical outcomes. A second precedence table is
        exactly how "green means two different things" happens.
        """
        return decide_final_outcome(
            [ObligationOutcome.from_record(r) for r in records],
            # The orchestrator already materialised drift as a SCOPE record inside
            # its own bracket, so the flag stays True here; SCOPE carries it.
            fingerprint_stable=True,
            certification_requirements=plan.certification_requirements,
            # The classifier's lookup protocol is (capability, kind); the
            # orchestrator's resolver also takes an explicit mapping path, which
            # the gate does not use. Adapted here rather than changing either
            # signature to suit the other.
            measurement_lookup=lambda cap, kind: self._find_measurement_record(
                cap, kind, ""
            ),
            current_sha=live_fp.repository_sha,
        )

    # ------------------------------------------------------------- helpers

    def _make_record(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        *,
        exit_code: int | None,
        state: CompletionState,
        reason_text: str,
        stderr_tail: list[str],
        stdout_path: str = "",
        stderr_path: str = "",
        artifacts: list[str] | None = None,
        diagnostic: dict | None = None,
        next_action: str = "",
        measurement_truth: dict | None = None,
        duration_seconds: float = 0.0,
        termination: dict | None = None,
    ) -> TaskExecutionRecord:
        record_id = (
            "task-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|" + spec.task_id + "|" + state.value).encode(
                    "utf-8"
                )
            ).hexdigest()[:12]
        )
        return TaskExecutionRecord(
            record_id=record_id,
            plan_id=plan.plan_id,
            task_id=spec.task_id,
            primary_capability=spec.primary_capability,
            capabilities=list(spec.capabilities),
            command=spec.command,
            scope=spec.scope,
            is_mandatory=spec.is_mandatory,
            is_escalation=spec.is_escalation,
            verification_kind=spec.verification_kind,
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            duration_seconds=duration_seconds,
            exit_code=exit_code,
            completion_state=state.value,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            artifacts=list(artifacts or []),
            measurement_truth=measurement_truth,
            diagnostic=diagnostic,
            next_action=next_action or "no action",
            reason=reason_text,
            prerequisites_satisfied=True,
            termination=termination,
        )

    def _blocked_report(
        self,
        plan: ExecutionPlan,
        errors: list[str],
        live_fp: RepositoryFingerprint,
    ) -> ExecutionReport:
        return ExecutionReport(
            report_id="report-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|blocked").encode("utf-8")
            ).hexdigest()[:12],
            plan_id=plan.plan_id,
            plan_fingerprint=plan.plan_fingerprint,
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            total_duration_seconds=0.0,
            records=[],
            efficiency=self._compute_efficiency(plan, []),
            final_decision=FinalDecision.VALIDATION_BLOCKED.value,
            decision_reason="; ".join(errors),
            evidence_reused=[],
            escalations_triggered=[],
        )

    def _dry_run_report(
        self, plan: ExecutionPlan, live_fp: RepositoryFingerprint
    ) -> ExecutionReport:
        return ExecutionReport(
            report_id="report-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|dry").encode("utf-8")
            ).hexdigest()[:12],
            plan_id=plan.plan_id,
            plan_fingerprint=plan.plan_fingerprint,
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            total_duration_seconds=0.0,
            records=[],
            efficiency=self._compute_efficiency(plan, []),
            final_decision=FinalDecision.DIAGNOSTIC.value,
            decision_reason="dry run — no execution performed",
            evidence_reused=[],
            escalations_triggered=[],
        )

    def _compute_efficiency(
        self, plan: ExecutionPlan, records: list[TaskExecutionRecord]
    ) -> dict:
        """Section-16 efficiency metrics."""
        try:
            from runtime.foundation.verification.command_inventory import (
                get_command_inventory,
            )

            inv = get_command_inventory()
            total_available = len(inv.commands)
        except Exception:
            total_available = 0
        selected = len(plan.tasks)
        executed = sum(
            1
            for r in records
            if r.completion_state
            in (
                CompletionState.PASS.value,
                CompletionState.FAILED.value,
                CompletionState.TIMEOUT.value,
                CompletionState.INFRASTRUCTURE.value,
                CompletionState.EVIDENCE.value,
                CompletionState.SCOPE.value,
                CompletionState.CONFIGURATION.value,
                CompletionState.CERTIFICATION.value,
            )
        )
        reused = sum(
            1 for r in records if r.completion_state == CompletionState.REUSED.value
        )
        skipped = sum(
            1 for r in records if r.completion_state == CompletionState.SKIPPED.value
        )
        auth_required = sum(
            1
            for r in records
            if r.completion_state == CompletionState.AUTHORIZATION_REQUIRED.value
        )
        blind_total = self._blind_total_commands()
        executed_unique = len(
            {
                r.command
                for r in records
                if r.completion_state == CompletionState.PASS.value
            }
        )
        unnecessary_avoided = max(0, blind_total - executed_unique)
        return {
            "total_available_tasks": total_available,
            "tasks_selected": selected,
            "tasks_executed": executed,
            "tasks_reused": reused,
            "tasks_skipped": skipped,
            "tasks_awaiting_authorization": auth_required,
            "blind_total_commands": blind_total,
            "unnecessary_execution_avoided": unnecessary_avoided,
            "execution_time_seconds": sum(r.duration_seconds for r in records),
        }

    def _blind_total_commands(self) -> int:
        try:
            from runtime.foundation.verification.capability_contract import (
                get_capability_contract_registry,
            )
            from runtime.foundation.verification.command_inventory import (
                get_command_inventory,
            )

            registry = get_capability_contract_registry()
            inventory = get_command_inventory()
        except Exception:
            return 0
        registry.load()
        seen: set[str] = set()
        for cap in registry.get_all_contracts():
            for wf in cap.workflow_mappings:
                seen.add(wf.command.strip())
        # also count capability-derived commands
        for _cid, cmds in inventory.capabilities_index.items():
            for cmd_id in cmds:
                cmd = inventory.get_command(cmd_id)
                if cmd:
                    seen.add(cmd.command.strip())
        return len(seen)

    def _resolve_command(self, spec: ExecutionTaskSpec) -> str:
        if spec.command in self._command_overrides:
            return self._command_overrides[spec.command]
        # Per-kind override (used in tests to substitute fast commands for
        # revalidation measurement tasks whose auto-generated commands vary).
        kind_key = f"kind:{spec.verification_kind}"
        if kind_key in self._command_overrides:
            return self._command_overrides[kind_key]
        return spec.command


def _profile_from_command(command: str) -> str:
    """Heuristic: map a command string to a profile name (best effort)."""
    m = re.search(r"\.github/scripts/run_([a-z_]+)\.sh", command)
    if m:
        return m.group(1)
    return ""


# ---------------------------------------------------------------------------
# Convenience entry points
# ---------------------------------------------------------------------------


def build_plan(
    changed_files: list[str], orchestrator: ExecutionOrchestrator | None = None
) -> ExecutionPlan:
    orch = orchestrator or ExecutionOrchestrator()
    return orch.build_execution_plan(changed_files)


def format_plan(plan: ExecutionPlan) -> str:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("  VERIFICATION EXECUTION PLAN (M9-C49)")
    lines.append("=" * 80)
    lines.append(f"  Plan ID:       {plan.plan_id}")
    lines.append(f"  Source:        C48 {plan.source_plan_id}")
    lines.append(f"  Fingerprint:   {plan.plan_fingerprint[:12]}")
    lines.append(f"  Repository:    {plan.repository_fingerprint.repository_sha[:12]}")
    lines.append(f"  Toolchain:     {plan.repository_fingerprint.toolchain_hash[:12]}")
    lines.append(f"  Changed:       {len(plan.changed_files)}")
    lines.append(f"  Affected caps: {', '.join(plan.affected_capabilities)}")
    lines.append("-" * 80)
    lines.append("  TASKS:")
    for t in plan.tasks:
        auth = " [AUTH]" if t.authorization_required else ""
        mand = " (mandatory)" if t.is_mandatory else ""
        if t.is_escalation:
            mand = " (escalation)"
        lines.append(
            f"    [{t.verification_kind:>9s}] {t.task_id} -> {t.primary_capability}{auth}{mand}"
        )
        lines.append(f"             cmd: {t.command}")
        lines.append(f"             origin: {t.origin}  reason: {t.reason[:120]}")
    lines.append("-" * 80)
    lines.append("  REVALIDATION:")
    for r in plan.revalidation_sources:
        lines.append(
            f"    {r.get('capability', '?')} {r.get('kind', '?')}: {r.get('reason', '?')}"
        )
    lines.append("  REUSABLE:")
    for r in plan.reusable_measurements:
        lines.append(
            f"    {r.get('capability', '?')} {r.get('kind', '?')}: score={r.get('score')} sha={r.get('repository_sha', '?')[:12]}"
        )
    lines.append("-" * 80)
    lines.append(f"  RATIONALE: {plan.rationale}")
    lines.append("=" * 80)
    return "\n".join(lines)


def format_report(report: ExecutionReport) -> str:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("  VERIFICATION EXECUTION REPORT (M9-C49)")
    lines.append("=" * 80)
    lines.append(f"  Report ID:     {report.report_id}")
    lines.append(f"  Plan ID:       {report.plan_id}")
    lines.append(f"  Decision:      {report.final_decision}")
    lines.append(f"  Reason:        {report.decision_reason}")
    lines.append(f"  Total time:    {report.total_duration_seconds:.1f}s")
    lines.append("-" * 80)
    eff = report.efficiency
    lines.append(
        f"  EFFICIENCY: selected={eff.get('tasks_selected', 0)} "
        f"executed={eff.get('tasks_executed', 0)} "
        f"reused={eff.get('tasks_reused', 0)} "
        f"skipped={eff.get('tasks_skipped', 0)} "
        f"auth_required={eff.get('tasks_awaiting_authorization', 0)} "
        f"avoided={eff.get('unnecessary_execution_avoided', 0)}"
    )
    lines.append("-" * 80)
    lines.append("  TASK RECORDS:")
    for r in report.records:
        lines.append(
            f"    [{r.completion_state:>22s}] {r.task_id} ({r.primary_capability}) "
            f"exit={r.exit_code} dur={r.duration_seconds:.1f}s"
        )
        if r.next_action and r.completion_state not in (
            "pass",
            "reused",
            "skipped",
        ):
            lines.append(f"             next: {r.next_action[:120]}")
    lines.append("=" * 80)
    return "\n".join(lines)
