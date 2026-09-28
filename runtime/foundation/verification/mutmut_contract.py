# runtime/foundation/verification/mutmut_contract.py
#
# M9-C71 — Mutation toolchain contract (single source of truth).
#
# WHAT THIS SOLVES
# ----------------
# mutmut 3.7.0 is generated against a narrower set of source conventions than
# this repository uses. Two of those gaps do not fail loudly — they silently
# corrupt the measurement — so they are materialised here, from repository code,
# making the declared dependency contract (`pip install -e ".[all]"` -> pristine
# mutmut) and the working toolchain the same thing locally and in CI.
#
# Clause 1 — src.* module dispatch
#   `get_mutant_name()` (mutmut/utils/format_utils.py) derives a mutant's module
#   name from its PATH and strips a leading ``src.`` segment. This repository is
#   not a setuptools "src layout": ``backend/src`` is a real top-level package
#   and production code is imported as ``from src.engines...``. The mutated
#   module's trampoline dispatches a mutant by comparing mutmut's stripped name
#   with the function's real module name, so on a pristine install EVERY mutant
#   is dispatched to the ORIGINAL function. The suite exercises unmutated code,
#   passes for every mutant, and the campaign reports a structurally impossible
#   0.0% score with all mutants "survived" — while Gate A/B report perfect
#   execution and evidence integrity. (GitHub run 36238247482.)
#
# Clause 2 — @classmethod original-dispatch
#   For `@classmethod` trampolines the decorator already rebinds and re-slices
#   the call (`orig_func = getattr(args[0], orig_func.__name__)`,
#   `call_args = list(args[1:])`), but the "mutant of another module is active"
#   early-return ignores that rebinding and passes the raw `*args`. On a
#   class-scoped mutant the original receives `cls` twice and the CLEAN test run
#   dies with
#       TypeError: Money.xǁMoneyǁfrom_rupees__mutmut_orig() takes 2 positional
#       arguments but 3 were given
#       Failed to run clean test
#   i.e. mutmut cannot even measure the unmodified suite for any module that
#   uses class-scoped functions — which includes the canonical Money value
#   object. The three-line-later sibling branch already uses `*call_args`; this
#   clause makes the early return agree with it.
#
# PROPERTIES
# ----------
#   * version-gated  — refuses to touch anything but the pinned mutmut version;
#   * region-scoped  — rewrites only the exact dispatch statements, located by
#                      stable anchors; the rest of the toolchain stays
#                      byte-identical;
#   * idempotent     — re-running is a no-op once satisfied;
#   * self-healing   — a hand-edited venv is detected and re-derived canonically
#                      instead of being trusted;
#   * audited        — writes a durable before/after evidence record naming each
#                      clause, and every mutation summary carries it;
#   * fail-loud      — if the contract cannot be satisfied the campaign returns an
#                      INFRASTRUCTURE_FAILURE, never a fabricated score.
#
# Nothing here weakens a gate: a campaign that cannot be measured faithfully must
# fail loudly rather than report a quality number.

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import sysconfig
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.env import PINNED_MUTMUT, REPO_ROOT, VENV_BIN

# Relative path of the mutated-file trampoline inside the mutmut package.
TRAMPOLINE_REL_PATH = "mutmut/mutation/trampoline.py"

# Stable identifier for the contract as a whole, recorded with every
# measurement so evidence can be traced to a known toolchain state.
PATCH_ID = "c71-mutation-toolchain-contract"


# ── Clause 1: src.* module-name normalisation ────────────────────────────────

# Anchors delimiting the module-dispatch region. Everything between them is
# replaced; everything outside is left byte-identical.
REGION_START = "            # mutant under test is {module}.{mutant_name}\n"
REGION_END = "            mutated_func = mutants_dict.get(mutant_name)\n"

_CLAUSE1_BODY = """            # mutant under test is {module}.{mutant_name}
            module, _, mutant_name = mutant_under_test.rpartition(".")

            # C71 mutation toolchain contract (see
            # runtime/foundation/verification/mutmut_contract.py). mutmut derives
            # mutant module names from file paths and strips a leading "src."
            # segment, but this repository imports production code as
            # "src.<package>" — a real top-level package. Without this
            # normalisation every mutant is dispatched to the original function
            # and the campaign silently reports 0.0% with all mutants "survived".
            func_module = decorated_func.__module__
            if func_module.startswith("src."):
                func_module = func_module[len("src.") :]
            if module != func_module:
                # mutant of another module is active -> call original function
                return orig_func(*call_args, **kwargs)

"""

_NORMALISES_SRC_PREFIX_RE = 'startswith("src.")'


# ── Clause 2: @classmethod original-dispatch rebinding ───────────────────────

_CLAUSE2_COMMENT = (
    "                # mutant of another module is active -> call original function\n"
)
_CLAUSE2_BUG = "                return orig_func(*args, **kwargs)\n"
_CLAUSE2_FIXED = "                return orig_func(*call_args, **kwargs)\n"


class MutmutContractError(RuntimeError):
    """Raised when the pinned mutation toolchain cannot be brought into contract
    without an unsafe or ambiguous edit."""


@dataclass(frozen=True, slots=True)
class Clause:
    """One verified, idempotent transformation of the pinned toolchain."""

    clause_id: str
    summary: str
    locator: Callable[[str], bool]
    renderer: Callable[[str], str]
    satisfier: Callable[[str], bool]


def _split_region(text: str) -> tuple[str, str, str] | None:
    """Return (prefix, region, suffix) around the module-dispatch region."""
    start = text.find(REGION_START)
    if start < 0:
        return None
    end = text.find(REGION_END, start)
    if end < 0:
        return None
    return text[:start], text[start:end], text[end:]


def _clause1_render(current: str) -> str:
    parts = _split_region(current)
    if parts is None:
        raise MutmutContractError(
            "pinned mutmut trampoline does not contain the expected "
            "module-dispatch region; refusing to patch an unrecognised toolchain"
        )
    prefix, _region, suffix = parts
    return prefix + _CLAUSE1_BODY + suffix


def _clause1_satisfied(current: str) -> bool:
    try:
        return _clause1_render(current) == current
    except MutmutContractError:
        return False


def _clause1_locatable(current: str) -> bool:
    return _split_region(current) is not None


def _clause2_render(current: str) -> str:
    marker = _CLAUSE2_COMMENT + _CLAUSE2_BUG
    if marker not in current:
        # Already conformant, or the anchor is gone entirely.
        if _CLAUSE2_COMMENT + _CLAUSE2_FIXED in current:
            return current
        raise MutmutContractError(
            "pinned mutmut trampoline does not contain the expected "
            "class-method dispatch statement; refusing to patch an unrecognised "
            "toolchain"
        )
    if current.count(marker) != 1:
        raise MutmutContractError(
            "pinned mutmut trampoline repeats the class-method dispatch "
            "statement; refusing an ambiguous patch"
        )
    return current.replace(marker, _CLAUSE2_COMMENT + _CLAUSE2_FIXED, 1)


def _clause2_satisfied(current: str) -> bool:
    try:
        return _clause2_render(current) == current
    except MutmutContractError:
        return False


def _clause2_locatable(current: str) -> bool:
    return (_CLAUSE2_COMMENT + _CLAUSE2_BUG) in current or (
        _CLAUSE2_COMMENT + _CLAUSE2_FIXED
    ) in current


CLAUSES: tuple[Clause, ...] = (
    Clause(
        clause_id="c71-1-src-module-name-normalisation",
        summary=(
            "normalise mutmut's path-derived mutant module name against Python's "
            "real module name so src.* packages dispatch mutants instead of "
            "silently running original functions"
        ),
        locator=_clause1_locatable,
        renderer=_clause1_render,
        satisfier=_clause1_satisfied,
    ),
    Clause(
        clause_id="c71-2-classmethod-original-dispatch",
        summary=(
            "use the rebound call_args when the class-method trampoline falls back "
            "to the original function, so @classmethod mutants are measurable"
        ),
        locator=_clause2_locatable,
        renderer=_clause2_render,
        satisfier=_clause2_satisfied,
    ),
)


@dataclass(frozen=True, slots=True)
class MutmutTrampolineContract:
    """Auditable outcome of the mutation toolchain contract check/apply."""

    contract_id: str
    status: str
    mutmut_version: str
    trampoline_path: str
    before_sha256: str
    after_sha256: str
    canonical_sha256: str
    applied: bool
    unsatisfied_clauses: tuple[str, ...]
    detail: str

    @property
    def satisfied(self) -> bool:
        return self.status in ("SATISFIED", "APPLIED")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["satisfied"] = self.satisfied
        data["unsatisfied_clauses"] = list(self.unsatisfied_clauses)
        return data


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_trampoline_path() -> Path:
    """Resolve the trampoline module inside the canonical environment.

    Site-packages layout is ``<venv>/lib/python3.X/site-packages/<rel>``. The
    running interpreter's ``purelib`` is preferred so a Python minor upgrade
    cannot silently disable the contract; the venv interpreter is probed as a
    fallback for out-of-process callers.
    """
    candidate = Path(sysconfig.get_paths()["purelib"]) / TRAMPOLINE_REL_PATH
    if candidate.is_file():
        return candidate

    interpreter = VENV_BIN / "python"
    if interpreter.exists():
        try:
            out = subprocess.run(
                [
                    str(interpreter),
                    "-c",
                    "import mutmut.mutation.trampoline as t; print(t.__file__)",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except Exception:
            out = None
        if out is not None and out.returncode == 0 and out.stdout.strip():
            probed = Path(out.stdout.strip())
            if probed.is_file():
                return probed

    return (
        VENV_BIN.parent
        / "lib"
        / f"python{sys.version_info.minor}"
        / "site-packages"
        / TRAMPOLINE_REL_PATH
    )


def render_contract_source(current: str) -> str:
    """Return the canonical contract-conformant trampoline source.

    Raises :class:`MutmutContractError` when a clause's anchor cannot be located
    — patching an unrecognised toolchain is never attempted.
    """
    out = current
    for clause in CLAUSES:
        if clause.satisfier(out):
            continue
        if not clause.locator(out):
            raise MutmutContractError(
                f"{clause.clause_id}: cannot locate the expected dispatch "
                "statement; refusing to patch an unrecognised toolchain"
            )
        out = clause.renderer(out)
    return out


def inspect(mutmut_version: str) -> MutmutTrampolineContract:
    """Report the contract state without modifying anything."""
    path = resolve_trampoline_path()
    if not path.is_file():
        return MutmutTrampolineContract(
            contract_id=PATCH_ID,
            status="INAPPLICABLE",
            mutmut_version=mutmut_version,
            trampoline_path=str(path),
            before_sha256="",
            after_sha256="",
            canonical_sha256="",
            applied=False,
            unsatisfied_clauses=(),
            detail="mutmut trampoline module not found in the canonical environment",
        )

    current = path.read_text(encoding="utf-8")
    unsatisfied = tuple(c.clause_id for c in CLAUSES if not c.satisfier(current))
    try:
        canonical = render_contract_source(current)
    except MutmutContractError as exc:
        return MutmutTrampolineContract(
            contract_id=PATCH_ID,
            status="VIOLATED",
            mutmut_version=mutmut_version,
            trampoline_path=str(path),
            before_sha256=_sha256(current),
            after_sha256=_sha256(current),
            canonical_sha256="",
            applied=False,
            unsatisfied_clauses=unsatisfied,
            detail=str(exc),
        )

    satisfied = current == canonical
    if satisfied:
        detail = "all clauses satisfied; toolchain is canonical"
    else:
        detail = f"{len(unsatisfied)} clause(s) not applied: {', '.join(unsatisfied)}"
    return MutmutTrampolineContract(
        contract_id=PATCH_ID,
        status="SATISFIED" if satisfied else "VIOLATED",
        mutmut_version=mutmut_version,
        trampoline_path=str(path),
        before_sha256=_sha256(current),
        after_sha256=_sha256(current),
        canonical_sha256=_sha256(canonical),
        applied=False,
        unsatisfied_clauses=unsatisfied,
        detail=detail,
    )


def ensure(mutmut_version: str) -> MutmutTrampolineContract:
    """Bring the pinned mutation toolchain into contract; return the audit record.

    Idempotent. Raises :class:`MutmutContractError` when the toolchain cannot be
    brought into contract — the caller must then fail the campaign rather than
    report an unmeasured score.
    """
    state = inspect(mutmut_version)
    if state.satisfied or state.status == "INAPPLICABLE":
        return state

    if PINNED_MUTMUT and PINNED_MUTMUT not in (mutmut_version or ""):
        raise MutmutContractError(
            f"mutation toolchain is {mutmut_version!r}, expected the pinned "
            f"mutmut {PINNED_MUTMUT}; refusing to modify an unverified toolchain"
        )

    path = Path(state.trampoline_path)
    current = path.read_text(encoding="utf-8")
    canonical = render_contract_source(current)

    # Byte-compiled caches must not shadow the corrected source.
    cache = path.parent / "__pycache__"
    if cache.is_dir():
        for stale in sorted(cache.glob("trampoline.*.pyc")):
            stale.unlink()
    # A hand-applied edit leaves a stray backup that would otherwise masquerade
    # as the pristine upstream file.
    for stray in (path.with_suffix(".py.bak"), path.parent / "trampoline.py.bak"):
        if stray.is_file():
            stray.unlink()

    path.write_text(canonical, encoding="utf-8")

    applied = inspect(mutmut_version)
    if not applied.satisfied:
        raise MutmutContractError(
            f"failed to satisfy the mutation toolchain contract at {path}: "
            f"{applied.detail}"
        )
    return MutmutTrampolineContract(
        contract_id=PATCH_ID,
        status="APPLIED",
        mutmut_version=mutmut_version,
        trampoline_path=str(path),
        before_sha256=state.before_sha256,
        after_sha256=applied.after_sha256,
        canonical_sha256=applied.canonical_sha256,
        applied=True,
        unsatisfied_clauses=(),
        detail=("applied " + ", ".join(c.summary for c in CLAUSES)),
    )


def ensure_mutmut_contract(mutmut_version: str) -> MutmutTrampolineContract:
    """Public alias used by the canonical mutation runner."""
    return ensure(mutmut_version)


def write_mutmut_contract_evidence(contract: MutmutTrampolineContract) -> Path:
    """Public alias used by the canonical mutation runner."""
    return write_evidence(contract)


def evidence_path() -> Path:
    return (
        REPO_ROOT
        / "backend"
        / "tests"
        / "generated"
        / "mutation"
        / "mutmut-toolchain-contract.json"
    )


def write_evidence(contract: MutmutTrampolineContract) -> Path:
    """Persist the durable toolchain-contract audit record."""
    out = evidence_path()
    payload = contract.to_dict()
    payload["recorded_at"] = datetime.now(UTC).isoformat()
    payload["pinned_mutmut"] = PINNED_MUTMUT
    payload["clauses"] = [
        {"clause_id": c.clause_id, "summary": c.summary} for c in CLAUSES
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
