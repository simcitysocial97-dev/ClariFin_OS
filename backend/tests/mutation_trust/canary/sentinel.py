# backend/tests/mutation_trust/canary/sentinel.py
#
# M9-C71 — Mutation execution sentinel.
#
# WHAT PROBLEM THIS SOLVES
# ------------------------
# mutmut's per-mutant verdict (killed / survived / no tests) is derived from a
# test process's EXIT CODE. That answers "did any test fail?" — it does NOT
# answer "did the mutated code actually run?".
#
# A mutant can be dispatched to the ORIGINAL function and still produce a clean
# exit code: the suite passes, mutmut records "survived", and the score looks
# like a test-quality problem when it is actually a dispatch defect. That is
# exactly what happened in this repository (C71 root cause: 0.0% with 285
# survivors on a suite that had never executed a single mutant).
#
# So survival cannot be interpreted without independent evidence that the
# mutated implementation executed. This module supplies that evidence.
#
# HOW IT WORKS (no production behaviour is altered)
# --------------------------------------------------
# mutmut runs each mutant in a forked child with ``MUTANT_UNDER_TEST`` set to
# the fully-qualified name of the mutant under test, e.g.
# ``canary.engine.x_known_kill_value__mutmut_3``. That environment variable is
# the authoritative signal of WHICH implementation the process is supposed to
# be exercising. This sentinel:
#
#   1. reads MUTANT_UNDER_TEST and resolves the mangled mutant function inside
#      the module under test (mutmut names it ``x_<func>__mutmut_<n>``);
#   2. attaches a PEP 669 ``sys.monitoring`` line-event callback to the code
#      object of that EXACT function, and nothing else;
#   3. appends an evidence record to a sink file, keyed by mutant name.
#
# Because the callback is scoped to one code object, a hit proves the mutated
# function's bytecode was entered — an independent runtime signal, not an
# inference from mutmut's output.
#
# A hit is also only recorded if the sentinel was successfully armed, so the
# absence of a record is meaningful (either never armed, or armed and never
# entered) rather than ambiguous.
#
# OUTSIDE A MUTANT FORK the sentinel is a strict no-op: no MUTANT_UNDER_TEST,
# no function to resolve, no monitoring callback, no sink write. The identical
# test file therefore remains a valid ordinary suite.

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

#: Environment variable mutmut sets in each forked mutant process.
MUTANT_UNDER_TEST_ENV = "MUTANT_UNDER_TEST"

#: Environment variable naming the append-only evidence sink.
SINK_ENV = "C71_MUTATION_SENTINEL_SINK"

#: mutmut reuses these two sentinel values for its own self-check phases. They
#: are NOT mutant runs, so they must never be treated as execution evidence.
NON_MUTANT_SENTINELS = frozenset({"", "fail", "stats"})

#: PEP 669 monitoring tool ids 0 and 1 are reserved (debugger / profiler), and
#: 2 (PROFILER_ID) is the conventional profiler slot other tools reach for
#: first. The sentinel therefore claims a free id at runtime rather than
#: hard-coding one: this suite runs under hypothesis, which also uses
#: sys.monitoring, and a fixed id collided with it — degrading hypothesis's
#: coverage analysis during every mutation run.
_MIN_TOOL_ID = 2
_MAX_TOOL_ID = 5
_SENTINEL_TOOL_NAME = "c71_mutation_execution_sentinel"

#: Records emitted per armed function, consumed by the Phase 4 classifier.
_armed: dict[str, dict[str, Any]] = {}


class SentinelError(RuntimeError):
    """Raised when the sentinel cannot be installed on a target function."""


def active_mutant() -> str:
    """Return the fully-qualified mutant name under test, or ``""``.

    Returns ``""`` outside a mutmut mutant fork, which is the signal that this
    process is a plain test run and the sentinel must stay inert.
    """
    value = os.environ.get(MUTANT_UNDER_TEST_ENV, "").strip()
    return "" if value in NON_MUTANT_SENTINELS else value


def _namespace(module: Any) -> dict:
    """Return the attribute mapping of a module or object.

    A module is a namespace object, but a *class instance* holding the generated
    symbols is not, and looking up ``__dict__`` blindly raises. Using
    ``vars()`` with a fallback keeps symbol resolution total instead of throwing
    on the first unexpected object shape — a sentinel that crashes is worse than
    one that reports it could not resolve.
    """
    try:
        return vars(module)
    except TypeError:
        namespace = getattr(module, "__dict__", None)
        if isinstance(namespace, dict):
            return namespace
        return {}


def resolve_mutant_symbol(module: Any, mutant_name: str) -> tuple[str, Any] | None:
    """Resolve mutmut's mutant name to the real symbol inside *module*.

    ``mutant_name`` is fully qualified (``<module path>.x_<func>__mutmut_<n>``).
    mutmut keeps the mangled *key* (``x_<func>``) as the trampoline's dict key
    and appends ``__mutmut_<n>`` per operator, so both the bare key and the
    per-operator name are accepted here.

    Returns ``(symbol_name, function)`` or ``None`` when the module does not
    contain the mutant — which is itself meaningful evidence (the mutant could
    not be dispatched, so it could not have executed).
    """
    mangled = mutant_name.rpartition(".")[2]
    if not mangled:
        return None

    namespace = _namespace(module)

    # Exact per-operator symbol, e.g. x_known_kill_value__mutmut_3
    exact = namespace.get(mangled)
    if exact is not None and callable(exact):
        return mangled, exact

    # Mangled key directly, e.g. x_known_kill_value
    key = namespace.get(mangled)
    if key is not None and callable(key):
        return mangled, key

    # Any operator variant of the mangled key.
    prefix = f"{mangled}__mutmut_"
    for name, value in namespace.items():
        if name.startswith(prefix) and callable(value):
            return name, value

    # Class-scoped functions. mutmut mangles them as
    # xǁ<Class>ǁ<method> (CLASS_NAME_SEPARATOR), so the same operator suffix
    # applies to a key that contains separators rather than underscores. Missing
    # this case is not cosmetic: it left every @classmethod mutant — including
    # the whole Money value object — reported as unobserved even though it ran,
    # which is precisely the false negative the sentinel must not produce.
    if _CLASS_SEPARATOR in mangled:
        # xǁ<Class>ǁ<method>__mutmut_<n>
        #
        # The class attribute keeps the FULL mangled name, class prefix
        # included ("xǁMoneyǁ__rmul____mutmut_1"), so the lookup prefix is the
        # name up to the operator suffix and nothing more. Building it as
        # "x<method>__mutmut_" instead silently matched nothing, which reported
        # every @classmethod mutant — the whole Money value object — as
        # unobserved while it plainly executed. A silent mismatch in the
        # measurement apparatus is worse than having no apparatus, so this is
        # recorded explicitly when it cannot be resolved.
        base, _, _operator = mangled.partition("__mutmut_")
        parts = base.split(_CLASS_SEPARATOR)
        if len(parts) >= 3:
            owner = namespace.get(parts[1])
            if owner is not None:
                for name, value in _namespace(owner).items():
                    if name.startswith(f"{base}__mutmut_") and callable(value):
                        return name, value
                for name, value in _namespace(owner).items():
                    if name == base and callable(value):
                        return name, value
    return None


#: mutmut's class-name separator inside a mangled function key
#: (``mutmut.mutation.trampoline_templates.CLASS_NAME_SEPARATOR``).
_CLASS_SEPARATOR = "ǁ"


# ── import hook: arm automatically, with no per-test opt-in ─────────────────


class _SentinelImportFinder:
    """Meta-path finder that arms the sentinel when a mutant module is imported.

    Phase 4 requires independent execution evidence for mutants across the whole
    representative sample, not only for the canary. Requiring every engine's
    test suite to call ``arm()`` would mean editing tests purely to satisfy the
    measurement apparatus — the same anti-pattern C71 forbids for test
    generation.

    So the sentinel arms itself: this finder watches for the import of a module
    that actually contains the mutant under test, and instruments it at that
    moment. The module is returned untouched, so production behaviour is
    completely unaltered — the only effect is a line-event callback on one code
    object.

    It is a no-op unless MUTANT_UNDER_TEST names a real mutant, so ordinary test
    runs and the mutation harness itself are unaffected.
    """

    def find_module(self, fullname: str, path: Any = None) -> Any:  # pragma: no cover
        return None

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        if not active_mutant():
            return None
        # Only act on the module that owns the mutant, and only once.
        #
        # mutmut derives the mutant's module name from its PATH and strips a
        # leading "src."; Python imports the same file as "src.<package>". The
        # two therefore differ by exactly that prefix, which is the same
        # normalisation the installed toolchain contract performs. Matching on
        # the normalised name is what lets the sentinel arm for this
        # repository's `src.*` layout instead of silently never arming.
        if not module_owns_mutant(fullname):
            return None
        if fullname in _ARMED_MODULES:
            return None
        _ARMED_MODULES.add(fullname)
        # Resolve the spec normally, then wrap the loader's exec_module so the
        # sentinel is armed immediately AFTER the module body has run and its
        # mutated symbols exist. Returning None here keeps import semantics
        # completely standard.
        import importlib.machinery

        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None:
            return None
        original_exec = spec.loader.exec_module

        def _exec_and_arm(module: Any, _orig=original_exec) -> None:
            _orig(module)
            try:
                arm(module)
            except SentinelError:
                # A sentinel failure must never change a mutant's outcome; it is
                # recorded as unproven rather than converted into a kill.
                _append_record(
                    {
                        "event": "ARM_FAILED",
                        "mutant": active_mutant(),
                        "module": fullname,
                        "armed": False,
                    }
                )

        spec.loader.exec_module = _exec_and_arm  # type: ignore[method-assign]
        return spec


_ARMED_MODULES: set[str] = set()
_FINDER: _SentinelImportFinder | None = None


def install_import_hook() -> bool:
    """Install the auto-arming import hook once per process.

    Also arms any module that is ALREADY imported. mutmut imports test modules
    during collection before the selected test runs, and a module imported
    through a path that bypassed this finder (a package ``__init__`` re-export,
    a plugin that imported it first) would otherwise never be instrumented —
    producing "no execution evidence" for a mutant that plainly did run.

    Returns True when the hook is active. Inert (and returns False) outside a
    mutant fork, so it can be installed unconditionally from a conftest.
    """
    global _FINDER
    if not active_mutant():
        return False
    if _FINDER is not None:
        return True
    _FINDER = _SentinelImportFinder()
    sys.meta_path.insert(0, _FINDER)
    arm_already_imported()
    return True


def arm_already_imported() -> None:
    """Instrument the mutant's module if it is already in ``sys.modules``."""
    for name, module in list(sys.modules.items()):
        if module is None:
            continue
        if module_owns_mutant(name) and name not in _ARMED_MODULES:
            _ARMED_MODULES.add(name)
            try:
                arm(module)
            except SentinelError:
                continue


def arm_active_module(module: Any) -> dict | None:
    """Arm the sentinel against *module* if it owns the mutant under test.

    Called automatically by the import hook path and directly by the canary, so
    both the opt-in and the automatic routes share one implementation and cannot
    drift apart.
    """
    mutant_name = active_mutant()
    if not mutant_name:
        return None
    if not module_owns_mutant(getattr(module, "__name__", "")):
        return None
    return arm(module)


def normalise_module_name(module: str) -> str:
    """Apply the toolchain contract's ``src.`` normalisation to a module name.

    Mirrors the installed trampoline (see ``mutmut_contract`` clause
    ``c71-1-src-module-name-normalisation``). Without this the sentinel could
    never arm for this repository's ``src.<package>`` imports, and would report
    every survivor as unobserved — a false negative in the measurement
    apparatus, which is worse than no apparatus at all.
    """
    return module[len("src.") :] if module.startswith("src.") else module


def module_owns_mutant(module_name: str) -> bool:
    """True when *module_name* is the module that defines the mutant under test."""
    mutant_name = active_mutant()
    if not mutant_name:
        return False
    return normalise_module_name(module_name) == mutant_name.rpartition(".")[0]


def _sink_path() -> Path | None:
    raw = os.environ.get(SINK_ENV, "").strip()
    return Path(raw) if raw else None


def _append_record(record: dict[str, Any]) -> None:
    """Append one JSON line to the sink. Never raises.

    Evidence collection must not be able to change a mutant's outcome: a
    sentinel that crashes the test process would turn a survivor into a kill
    and corrupt the score. Failures here are therefore swallowed, and the
    caller still returns normally.
    """
    sink = _sink_path()
    if sink is None:
        return
    try:
        sink.parent.mkdir(parents=True, exist_ok=True)
        with sink.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    except (OSError, TypeError, ValueError):
        return


def arm(module: Any, function: Any = None) -> dict[str, Any] | None:
    """Attach the line-event sentinel to the mutant's own code object.

    *function* is the production symbol the test intends to exercise; it is
    used as a fallback target when *module* does not expose the mutant symbol
    directly. Returns the armed evidence record, or ``None`` when this process
    is not a mutant fork (the normal, inert case).
    """
    mutant_name = active_mutant()
    if not mutant_name:
        return None

    resolved = resolve_mutant_symbol(module, mutant_name)
    symbol: str | None = None
    target: Any = None

    if resolved is not None:
        symbol, target = resolved
    elif function is not None:
        target = function
        symbol = getattr(function, "__name__", None)

    if target is None or not hasattr(target, "__code__"):
        # Dispatch could not be resolved: record it, because an unresolvable
        # mutant is precisely the failure mode this sentinel exists to catch.
        _append_record(
            {
                "event": "DISPATCH_UNRESOLVED",
                "mutant": mutant_name,
                "module": getattr(module, "__name__", ""),
                "armed": False,
            }
        )
        return None

    code = target.__code__
    if _is_instrumentation(code.co_filename):
        _append_record(
            {
                "event": "TARGET_IS_TEST_CODE",
                "mutant": mutant_name,
                "symbol": symbol,
                "armed": False,
            }
        )
        return None

    hits: set[int] = set()
    monitoring = sys.monitoring
    tool_id = _claim_tool_id()
    if tool_id is None:
        _append_record(
            {
                "event": "NO_FREE_TOOL_ID",
                "mutant": mutant_name,
                "module": getattr(module, "__name__", ""),
                "armed": False,
            }
        )
        return None

    def _on_line(code_object: Any, line_number: int) -> None:
        if code_object is code:
            hits.add(line_number)

    try:
        monitoring.use_tool_id(tool_id, _SENTINEL_TOOL_NAME)
        monitoring.register_callback(tool_id, monitoring.events.LINE, _on_line)
        monitoring.set_local_events(tool_id, code, monitoring.events.LINE)
    except (ValueError, RuntimeError) as exc:
        raise SentinelError(
            f"failed to install the C71 mutation execution sentinel on "
            f"{code.co_filename}:{code.co_name}: {exc}"
        ) from exc

    record = {
        "event": "ARMED",
        "mutant": mutant_name,
        "module": getattr(module, "__name__", ""),
        "symbol": symbol,
        "armed": True,
        "code_file": code.co_filename,
        "code_name": code.co_name,
        "code_firstlineno": code.co_firstlineno,
    }
    _armed[mutant_name] = record
    _append_record(record)
    return record


def _tool_in_use(monitoring: Any, tool_id: int) -> bool:
    """True when *tool_id* has already been claimed in this process."""
    try:
        return monitoring.get_tool(tool_id) is not None
    except (ValueError, KeyError):
        return False


def _claim_tool_id() -> int | None:
    """Claim a free PEP 669 tool id, or return None if all are taken.

    Claiming dynamically matters because this sentinel runs inside the same
    process as hypothesis's own sys.monitoring usage. A hard-coded id silently
    disabled hypothesis tracing during every mutation run, which is exactly the
    kind of measurement interference the sentinel exists to rule out.
    """
    monitoring = sys.monitoring
    for candidate in range(_MIN_TOOL_ID, _MAX_TOOL_ID):
        if not _tool_in_use(monitoring, candidate):
            return candidate
    return None


def _is_instrumentation(filename: str) -> bool:
    """True when *filename* is the sentinel or the canary suite's own code.

    Deliberately narrow. A mutant's code object always lives under mutmut's
    generated ``mutants/`` tree, so a broad substring match (e.g. rejecting any
    path containing "pytest") is unnecessary AND harmful: it would reject a
    genuine mutant whose module happens to live under a directory containing
    that substring, and it reports a false negative for any code defined
    in-memory. The correct rule is "never instrument the measurement apparatus
    itself", so the sentinel's own filename is the only exclusion.
    """
    return Path(filename).name in ("sentinel.py", "sentinel_plugin.py")


def report() -> list[dict[str, Any]]:
    """Return every record armed in this process (test/diagnostic aid)."""
    return [dict(record) for record in _armed.values()]
