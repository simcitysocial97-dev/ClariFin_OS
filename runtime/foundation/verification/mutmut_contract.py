# runtime/foundation/verification/mutmut_contract.py
#
# M9-C71 — Mutation toolchain contract (single source of truth).
#
# PROBLEM THIS SOLVES (C71 root cause, previously misclassified as a quality gap)
# ------------------------------------------------------------------------------
# mutmut 3.7.0 derives a mutant's module name from its *path* via
# ``get_mutant_name()``, which explicitly strips a leading ``src.`` segment
# (``mutmut/utils/format_utils.py``). ClariFin_OS, however, imports production
# code as ``from src.engines...`` — ``backend/src`` is a real top-level package,
# not a setuptools "src layout" root.
#
# The mutated module's trampoline dispatches a mutant by comparing mutmut's
# stripped, path-derived module name (``engines.balance_engine``) with Python's
# real module name (``src.engines.balance_engine``). Pristine mutmut therefore
# takes the "mutant of another module is active -> call original function"
# branch for EVERY mutant: the test suite exercises unmutated code, every mutant
# is reported as *survived*, Gate A/B pass, and the campaign reports 0.0%.
#
# The local ``.venv`` happened to carry a hand-applied edit to
# ``site-packages/mutmut/mutation/trampoline.py`` (plus a stray ``.bak``), so
# local runs reported real kill counts while a fresh ``pip install -e "[all]"``
# environment — i.e. every CI runner — reported 0.0%. The declared dependency
# contract and the working toolchain had silently diverged, and the divergence
# presented itself as a 0.0% test-quality failure.
#
# THE CONTRACT
# ------------
# This module materialises the trampoline fix deterministically from repository
# code so the declared dependency contract and the working toolchain are the
# same thing locally and in CI. It is:
#   * version-gated   — refuses to touch anything but the pinned mutmut version;
#   * region-scoped   — rewrites exactly the module-dispatch region, by anchors;
#   * idempotent      — re-running is a no-op when already satisfied;
#   * self-healing    — a hand-edited venv is detected and re-derived canonically;
#   * audited         — writes a durable before/after evidence record.
#
# It deliberately weakens no gate: a campaign that cannot be measured faithfully
# must fail loudly rather than report a fabricated score.

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import sysconfig
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.env import PINNED_MUTMUT, REPO_ROOT, VENV_BIN

# Relative path of the mutated-file trampoline inside the mutmut package.
TRAMPOLINE_REL_PATH = "mutmut/mutation/trampoline.py"

# Stable identifier for the applied transformation, recorded with every
# measurement so evidence can be traced to a known toolchain state.
PATCH_ID = "c71-src-module-name-normalisation"

# Anchors delimiting the module-dispatch region. Everything between them is
# replaced; everything outside is left byte-identical.
REGION_START = "            # mutant under test is {module}.{mutant_name}\n"
REGION_END = "            mutated_func = mutants_dict.get(mutant_name)\n"

# The contract-conformant dispatch region. Normalises mutmut's stripped module
# name against Python's real (possibly ``src.``-prefixed) module name.
CONTRACT_REGION = """            # mutant under test is {module}.{mutant_name}
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
                return orig_func(*args, **kwargs)

"""

_NORMALISES_SRC_PREFIX_RE = re.compile(r'startswith\(\s*["\']src\.')


class MutmutContractError(RuntimeError):
    """Raised when the pinned mutation toolchain cannot be brought into contract
    without an unsafe or ambiguous edit."""


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
    detail: str

    @property
    def satisfied(self) -> bool:
        return self.status in ("SATISFIED", "APPLIED")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["satisfied"] = self.satisfied
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


def _split_region(text: str) -> tuple[str, str, str] | None:
    """Return (prefix, region, suffix) around the module-dispatch region."""
    start = text.find(REGION_START)
    if start < 0:
        return None
    end = text.find(REGION_END, start)
    if end < 0:
        return None
    return text[:start], text[start:end], text[end:]


def render_contract_source(current: str) -> str:
    """Return the canonical contract-conformant trampoline source.

    Raises :class:`MutmutContractError` when the dispatch region cannot be
    located — patching an unrecognised toolchain is never attempted.
    """
    parts = _split_region(current)
    if parts is None:
        raise MutmutContractError(
            "pinned mutmut trampoline does not contain the expected "
            "module-dispatch region; refusing to patch an unrecognised toolchain"
        )
    prefix, _region, suffix = parts
    return prefix + CONTRACT_REGION + suffix


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
            detail="mutmut trampoline module not found in the canonical environment",
        )

    current = path.read_text(encoding="utf-8")
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
            detail=str(exc),
        )

    satisfied = current == canonical
    if satisfied:
        detail = "dispatch region is canonical; src.* modules dispatch mutants"
    else:
        parts = _split_region(current)
        region = parts[1] if parts else ""
        if _NORMALISES_SRC_PREFIX_RE.search(region):
            detail = (
                "dispatch region normalises src.* but is not canonical; re-derivable"
            )
        else:
            detail = "dispatch region is pristine; contract not applied"
    return MutmutTrampolineContract(
        contract_id=PATCH_ID,
        status="SATISFIED" if satisfied else "VIOLATED",
        mutmut_version=mutmut_version,
        trampoline_path=str(path),
        before_sha256=_sha256(current),
        after_sha256=_sha256(current),
        canonical_sha256=_sha256(canonical),
        applied=False,
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
        detail=(
            "normalised mutmut trampoline module dispatch so src.* packages "
            "dispatch mutants instead of silently running original functions"
        ),
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
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
