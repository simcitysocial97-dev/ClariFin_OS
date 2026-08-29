# runtime/foundation/verification/survivor_catalog.py
#
# M9-C42.5 / C43.7 — Survivor catalog.
#
# Reconstructs every *surviving* mutant from mutmut 3.7.0 `.meta` files + the
# generated mutated source tree (`mutants/`), classifies each survivor by
# mutation type, and aggregates the result per function and per type.
#
# This lets `verify.py mutation` emit a structured, categorized per-function
# survivor breakdown directly — no post-hoc file/folder searching required.
#
# Pure reconstruction is offline: it reads the already-generated mutant
# population (the same one a prior `mutmut run` produced) and re-derives the
# diff via mutmut's own `get_diff_for_mutant` (libcst reconstruction from the
# mutated source + line-span index). No mutation execution happens here.

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Coarse type vocabulary (used for aggregation + reporting) ────────────────
CATEGORY_STRING = "string_literal"      # quoted literal change (incl. dict keys)
CATEGORY_NUMERIC = "numeric_literal"    # integer / float literal change
CATEGORY_ARITHMETIC = "arithmetic"      # constant inside an arithmetic expression
CATEGORY_COMPARISON = "comparison"      # >, <, >=, <=, ==, !=, in, is ...
CATEGORY_BOOLEAN = "boolean"            # and / or / True / False / None flips
CATEGORY_DEFAULT = "default_value"      # .get(k, X) -> .get(k, Y)
CATEGORY_KEY = "dict_key"               # string used as a mapping key
CATEGORY_CONTROL = "control_flow"       # return / if / loop body change
CATEGORY_OTHER = "other"

_CMP_OPS = {
    ">", "<", ">=", "<=", "==", "!=",
    " in", " not in", " is", " is not",
}
_BOOL_LITS = {"True", "False", "None"}
_BOOL_OPS = {"and", "or"}

_STRING_RE = re.compile(r'^\s*([bruf]*)("""|\'\'\'|"|\').*?\1\s*$', re.DOTALL)
_PLAIN_STRING_RE = re.compile(r'^\s*([bruf]*)("|\').*?\2\s*$')
_NUMERIC_RE = re.compile(r"^\s*-?\d+(\.\d+)?\s*$")
_ARITH_OP_RE = re.compile(r"(//|/|\*\*|%|\*|\+|-)")
_DICT_KEY_RE = re.compile(r"\.get\s*\(|\]\s*=|\[[^\]]*\]\s*[:=]")


@dataclass
class SurvivorEntry:
    key: str
    function: str
    source_file: str
    category: str
    old: str
    new: str
    signature: str  # normalized (function, category, old->new)


@dataclass
class SurvivorCatalog:
    total_survivors: int = 0
    by_function: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    by_file: dict[str, int] = field(default_factory=dict)
    by_function_category: dict[str, int] = field(default_factory=dict)
    entries: list[SurvivorEntry] = field(default_factory=list)

    def add(self, e: SurvivorEntry) -> None:
        self.total_survivors += 1
        self.by_function[e.function] = self.by_function.get(e.function, 0) + 1
        self.by_category[e.category] = self.by_category.get(e.category, 0) + 1
        self.by_file[e.source_file] = self.by_file.get(e.source_file, 0) + 1
        fc = f"{e.function} :: {e.category}"
        self.by_function_category[fc] = self.by_function_category.get(fc, 0) + 1
        self.entries.append(e)

    def to_dict(self) -> dict:
        return {
            "total_survivors": self.total_survivors,
            "by_category": dict(sorted(self.by_category.items(), key=lambda kv: -kv[1])),
            "by_function": dict(sorted(self.by_function.items(), key=lambda kv: -kv[1])),
            "by_file": dict(sorted(self.by_file.items(), key=lambda kv: -kv[1])),
            "by_function_category": dict(
                sorted(self.by_function_category.items(), key=lambda kv: -kv[1])
            ),
            "entries": [
                {
                    "key": e.key,
                    "function": e.function,
                    "source_file": e.source_file,
                    "category": e.category,
                    "old": e.old,
                    "new": e.new,
                    "signature": e.signature,
                }
                for e in self.entries
            ],
        }


def _classify_pair(old_line: str, new_line: str) -> tuple[str, str, str]:
    """Classify a single (removed, added) line pair.

    Returns (category, old_token, new_token).
    """
    old = old_line.rstrip("\n")
    new = new_line.rstrip("\n")

    old_is_str = bool(_PLAIN_STRING_RE.match(old))
    new_is_str = bool(_PLAIN_STRING_RE.match(new))
    old_is_num = bool(_NUMERIC_RE.match(old))
    new_is_num = bool(_NUMERIC_RE.match(new))

    # String literal change
    if old_is_str and new_is_str:
        # dict-key context?
        if _DICT_KEY_RE.search(old) or _DICT_KEY_RE.search(new):
            return CATEGORY_KEY, old.strip(), new.strip()
        return CATEGORY_STRING, old.strip(), new.strip()

    # Numeric literal change
    if old_is_num and new_is_num:
        if _ARITH_OP_RE.search(old) or _ARITH_OP_RE.search(new):
            return CATEGORY_ARITHMETIC, old.strip(), new.strip()
        # default value inside .get(...)
        if ".get(" in old or ".get(" in new:
            return CATEGORY_DEFAULT, old.strip(), new.strip()
        return CATEGORY_NUMERIC, old.strip(), new.strip()

    # Comparison operator change
    for op in _CMP_OPS:
        if op in old and op not in new:
            return CATEGORY_COMPARISON, old.strip(), new.strip()
        if op in new and op not in old:
            return CATEGORY_COMPARISON, old.strip(), new.strip()
    if ("==" in old and "!=" in new) or ("!=" in old and "==" in new):
        return CATEGORY_COMPARISON, old.strip(), new.strip()

    # Boolean operator / literal change
    if old.strip() in _BOOL_LITS or new.strip() in _BOOL_LITS:
        return CATEGORY_BOOLEAN, old.strip(), new.strip()
    # bare `and` / `or` flip (word-boundary)
    if re.search(r"\band\b", old) and re.search(r"\bor\b", new):
        return CATEGORY_BOOLEAN, old.strip(), new.strip()
    if re.search(r"\bor\b", old) and re.search(r"\band\b", new):
        return CATEGORY_BOOLEAN, old.strip(), new.strip()

    # Arithmetic constant change (non-trivial literal, e.g. /100.0 -> /101.0)
    if _ARITH_OP_RE.search(old) or _ARITH_OP_RE.search(new):
        return CATEGORY_ARITHMETIC, old.strip(), new.strip()

    return CATEGORY_OTHER, old.strip(), new.strip()


def _classify_diff(diff: str) -> tuple[str, str, str]:
    """Classify a unified diff (single mutant) from its changed lines.

    Scans `-`/`+` line pairs (grouped by adjacency) and returns the dominant
    category. When multiple categories appear, picks the most specific one by
    priority: default_value > dict_key > comparison > boolean > arithmetic >
    numeric > string > control_flow > other.
    """
    lines = diff.split("\n")
    removed: list[str] = []
    added: list[str] = []
    pairs: list[tuple[str, str]] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            i += 1
            continue
        if line.startswith("-"):
            chunk = []
            while i < len(lines) and lines[i].startswith("-"):
                chunk.append(lines[i][1:])
                i += 1
            removed = chunk
            # collect following added
            added = []
            while i < len(lines) and lines[i].startswith("+"):
                added.append(lines[i][1:])
                i += 1
            # align by index
            for j in range(max(len(removed), len(added))):
                o = removed[j] if j < len(removed) else ""
                n = added[j] if j < len(added) else ""
                if o or n:
                    pairs.append((o, n))
        elif line.startswith("+"):
            chunk = []
            while i < len(lines) and lines[i].startswith("+"):
                chunk.append(lines[i][1:])
                i += 1
            for c in chunk:
                pairs.append(("", c))
        else:
            i += 1

    if not pairs:
        return CATEGORY_OTHER, "", ""

    priority = {
        CATEGORY_DEFAULT: 9,
        CATEGORY_KEY: 8,
        CATEGORY_COMPARISON: 7,
        CATEGORY_BOOLEAN: 6,
        CATEGORY_ARITHMETIC: 5,
        CATEGORY_NUMERIC: 4,
        CATEGORY_STRING: 3,
        CATEGORY_CONTROL: 2,
        CATEGORY_OTHER: 0,
    }
    best = (CATEGORY_OTHER, "", "")
    old_parts: list[str] = []
    new_parts: list[str] = []
    for o, n in pairs:
        cat, o2, n2 = _classify_pair(o, n)
        old_parts.append(o2)
        new_parts.append(n2)
        if priority[cat] > priority[best[0]]:
            best = (cat, o2, n2)
    if best[0] == CATEGORY_OTHER and (old_parts or new_parts):
        # fall back to a generic signature rather than losing the entry
        return CATEGORY_CONTROL, " ".join(old_parts)[:80], " ".join(new_parts)[:80]
    return best


def _source_file_from_key(meta_dir: Path, mutant_key: str) -> str:
    # mutant_key: engines.behaviour_engine.core.x_func__mutmut_N
    # map to a relative source path under meta_dir
    parts = mutant_key.split(".")
    # drop the trailing mangled function + __mutmut_N
    mod_parts = parts[:-1]
    rel = "/".join(mod_parts) + ".py"
    return rel


def source_path_from_meta(meta_file: Path, meta_dir: Path) -> str | None:
    """Derive the source-relative path of a mutant's file from its .meta
    location.

    The .meta files live at ``mutants/<source_rel>.meta``, so the source-relative
    path is the meta path minus the ``.meta`` suffix. This is the stable,
    lifecycle-proof source of truth for the mutated file — it is independent of
    whichever engine's [tool.mutmut] scope happens to be resting in
    backend/pyproject.toml at post-run evidence-gathering time.
    """
    try:
        return str(meta_file.relative_to(meta_dir).with_suffix(""))
    except ValueError:
        return None


def build_survivor_catalog(meta_dir: Path, backend_dir: Path) -> SurvivorCatalog:
    """Build a categorized catalog of all *surviving* mutants.

    Requires `backend_dir` to be the cwd-equivalent for mutmut's
    `get_diff_for_mutant` (it reads `mutants/<path>` relative to cwd).
    """
    from mutmut.__main__ import get_diff_for_mutant

    from runtime.foundation.verification.mutation_contract import (
        _MUTMUT_EXIT_CODE_TO_STATUS,
    )

    catalog = SurvivorCatalog()
    if not meta_dir.is_dir():
        return catalog

    for meta_file in meta_dir.rglob("*.meta"):
        # M9-C45.2 lifecycle fix: reconstruct each diff via the explicit
        # source-relative path (mutants/<path>), NOT via the config-walking
        # find_mutant(). The mutation runner restores backend/pyproject.toml
        # to its resting [tool.mutmut] scope before post-run evidence is
        # gathered, so config-walking silently fails for any target whose
        # scope differs from the resting scope (diffs came back empty and
        # every survivor was miscategorized as "other"). The .meta layout
        # (mutants/<source_rel>.meta) is the stable, lifecycle-proof
        # source of truth for the mutated file path.
        source_rel = source_path_from_meta(meta_file, meta_dir)
        # M9-C45.7 measurement hygiene: exclude copied test-fixture/probe
        # `.meta` files (e.g. src/tests/mutation_infra/mutants/probe.py.meta)
        # from the survivor catalog. When an engine's source tree is copied
        # (mutmut also_copy=["src"]) and a smoke-probe fixture lives under
        # src/tests/, its stale .meta would otherwise be counted as a survivor
        # of the target engine, polluting the measurement.
        if source_rel and (
            source_rel.startswith("tests/") or "mutation_infra" in source_rel
        ):
            continue
        try:
            meta = json.loads(meta_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        exit_codes = meta.get("exit_code_by_key") or {}
        for key, ec in exit_codes.items():
            status = _MUTMUT_EXIT_CODE_TO_STATUS.get(ec, "suspicious")
            if status != "survived":
                continue
            try:
                diff = (
                    get_diff_for_mutant(key, path=source_rel)
                    if source_rel is not None
                    else get_diff_for_mutant(key)
                )
            except Exception:
                diff = ""
            category, old, new = _classify_diff(diff)
            func = key.rsplit("__mutmut_", 1)[0].rsplit(".", 1)[-1]
            src = source_rel or _source_file_from_key(meta_dir, key)
            entry = SurvivorEntry(
                key=key,
                function=func,
                source_file=src,
                category=category,
                old=old,
                new=new,
                signature=f"{func} :: {category} :: {old} -> {new}",
            )
            catalog.add(entry)
    return catalog


def run_catalog_cli(meta_dir: Path, backend_dir: Path, out_path: Path | None = None) -> SurvivorCatalog:
    import os

    prev = os.getcwd()
    os.chdir(backend_dir)
    try:
        catalog = build_survivor_catalog(meta_dir, backend_dir)
    finally:
        os.chdir(prev)

    report = catalog.to_dict()
    if out_path is None:
        out_path = backend_dir / "tests" / "generated" / "mutation" / "mutation-survivors.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    print("=" * 72)
    print("  MUTATION SURVIVOR CATALOG")
    print("=" * 72)
    print(f"  Total survivors : {catalog.total_survivors}")
    print("-" * 72)
    print("  By category:")
    for cat, n in report["by_category"].items():
        print(f"    {cat:<18} {n}")
    print("-" * 72)
    print("  Top functions (by survivors):")
    for fn, n in list(report["by_function"].items())[:25]:
        print(f"    {fn:<48} {n}")
    print("-" * 72)
    print("  Top function :: category combos:")
    for fc, n in list(report["by_function_category"].items())[:25]:
        print(f"    {fc:<56} {n}")
    print("=" * 72)
    print(f"  Wrote: {out_path}")
    return catalog
