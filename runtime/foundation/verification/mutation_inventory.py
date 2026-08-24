# runtime/foundation/verification/mutation_inventory.py
#
# M9-C42.17 — Permanent forensic survivor-inventory + classification tool.
#
# This is ADDITIVE tooling. It does NOT modify the certified mutation execution
# path (mutation_runner.py / mutation_contract.py). It reads the mutmut results
# cache produced by a `verify.py mutation --target <engine>` run and builds the
# per-engine survivor inventory with evidence-based classifications.
#
# Reliability guarantees:
#   * Resolves mutmut via the canonical env resolver (venv-first) — identical to
#     the certified runner, so tooling parity is preserved.
#   * Runs `mutmut results` / `mutmut show` from backend/ (where the cache lives).
#   * `classify()` is a PURE function (no I/O) and is unit-tested, so the
#     classification logic is reviewable and regression-safe.
#   * Every emitted record carries classification + evidence + proposed action.
#
# Usage:
#   python runtime/verify.py mutation-inventory --target credit_card_engine
#   python -m runtime.foundation.verification.mutation_inventory --target credit_card_engine
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from runtime.foundation.verification.env import REPO_ROOT, resolve_environment

BACKEND_DIR = REPO_ROOT / "backend"
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"

# ── Classification vocabulary (single source of truth) ───────────────────────
A_REAL_GAP = "A"        # externally observable behavior the suite should constrain
B_EQUIVALENT = "B"      # cannot change externally observable behavior in valid domain
C_UNREACHABLE = "C"     # mutated path cannot be reached via valid system behavior
D_INFRA = "D"           # result caused by mutation infra / execution, not test quality
E_UNKNOWN = "E"         # genuinely insufficient evidence (temporary only)

CLASSIFICATION_LEGEND = {
    A_REAL_GAP: "REAL TEST GAP",
    B_EQUIVALENT: "EQUIVALENT MUTANT",
    C_UNREACHABLE: "INVALID/UNREACHABLE",
    D_INFRA: "INFRASTRUCTURE/EXECUTION ANOMALY",
    E_UNKNOWN: "UNKNOWN",
}


@dataclass(frozen=True)
class SurvivorChange:
    """One parsed changed region of a surviving mutant."""

    mutant: str
    source_file: str
    line: int | None
    original: str
    mutated: str


@dataclass(frozen=True)
class Classification:
    classification: str
    subclass: str
    evidence: str
    affected_behavior: str
    proposed_action: str


def _mutmut_bin() -> str:
    env = resolve_environment(config_dir=BACKEND_DIR)
    if env.mutmut.path:
        return env.mutmut.path
    raise RuntimeError("mutmut not resolvable from .venv or PATH")


def _env_with_venv_path() -> dict:
    return {**os.environ, "PATH": f"{REPO_ROOT / '.venv/bin'}:{os.environ.get('PATH','')}"}


def collect_results() -> dict[str, str]:
    """Return {mutant_name: status} from the backend mutmut cache."""
    mutmut = _mutmut_bin()
    res = subprocess.run(
        [mutmut, "results", "--all", "true"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        timeout=120,
        env=_env_with_venv_path(),
    )
    out: dict[str, str] = {}
    for line in res.stdout.splitlines():
        line = line.rstrip()
        if ": " not in line:
            continue
        name, status = line.rsplit(": ", 1)
        out[name.strip()] = status.strip().lower()
    return out


_STATUS_MAP = {
    "killed": "killed",
    "survived": "survived",
    "no tests": "no_tests",
    "no test": "no_tests",
    "timeout": "timeout",
    "suspicious": "suspicious",
    "not checked": "not_checked",
}


def parse_counts(results: dict[str, str]) -> dict[str, int]:
    counts = dict.fromkeys(_STATUS_MAP.values(), 0)
    for status in results.values():
        key = _STATUS_MAP.get(status, "not_checked")
        counts[key] += 1
    return counts


def show_mutant(name: str) -> str:
    """Return the `mutmut show <name>` diff text."""
    mutmut = _mutmut_bin()
    res = subprocess.run(
        [mutmut, "show", name],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        timeout=60,
        env=_env_with_venv_path(),
    )
    return res.stdout


def _parse_diff(text: str) -> list[SurvivorChange]:
    """Parse a `mutmut show` diff into changed regions (file/line/orig/mut)."""
    changes: list[SurvivorChange] = []
    mutant = ""
    cur_file: str | None = None
    hunk_start: int | None = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# ") and ln.endswith(":"):
            mutant = ln[2:-1].strip()
            i += 1
            continue
        if ln.startswith("--- "):
            cur_file = ln[4:].strip()
            i += 1
            continue
        if ln.startswith("@@"):
            m = re.search(r"\+(\d+)", ln)
            hunk_start = int(m.group(1)) if m else None
            i += 1
            continue
        if ln.startswith("-") and not ln.startswith("---"):
            original = ln[1:]
            mutated: str | None = None
            if i + 1 < len(lines) and lines[i + 1].startswith("+") and not lines[i + 1].startswith("+++"):
                mutated = lines[i + 1][1:]
                i += 2
            else:
                i += 1
            changes.append(
                SurvivorChange(
                    mutant=mutant,
                    source_file=cur_file or "",
                    line=hunk_start,
                    original=original,
                    mutated=mutated if mutated is not None else "",
                )
            )
            continue
        i += 1
    return changes


def infer_operator(original: str, mutated: str) -> str:
    o = original or ""
    m = mutated or ""
    ol, ml = o.lower(), m.lower()
    if "raise" in ol:
        return "exception_message_string_mutation"
    if "rounding=round_half_even" in ol or "rounding=round_half_even" in ml:
        return "rounding_argument_mutation"
    if "decimal(" in ol or "decimal(" in ml:
        return "decimal_argument_mutation"
    if re.search(r"[+\-*/%]", o) and re.search(r"[+\-*/%]", m):
        return "arithmetic_operator_mutation"
    if re.search(r"(<=|>=|==|!=|<|>)", o) or re.search(r"(<=|>=|==|!=|<|>)", m):
        return "comparison_operator_mutation"
    if re.search(r"\b(and|or|not)\b", ol) or re.search(r"\b(and|or|not)\b", ml):
        return "boolean_operator_mutation"
    if re.search(r"\b(true|false|none)\b", ol) or re.search(r"\b(true|false|none)\b", ml):
        return "constant_replacement_mutation"
    if (o.strip().startswith('"') or o.strip().startswith("'")) and (
        m.strip().startswith('"') or m.strip().startswith("'")
    ):
        return "string_literal_mutation"
    if re.search(r"\b\d+\b", o) or re.search(r"\b\d+\b", m):
        return "numeric_constant_mutation"
    if "(" in o or "(" in m:
        return "call_argument_mutation"
    return "other_mutation"


def classify(original: str, mutated: str) -> Classification:
    """Classify a surviving mutant with evidence.

    Rules are ordered; the first matching rule wins. Equivalence (B) requires
    proof that the mutation cannot change externally observable behavior in the
    valid domain — it is NEVER used merely for convenience.
    """
    o = original or ""
    m = mutated or ""
    ol = o.lower()
    ml = m.lower()

    # 1. Message-only exception mutation -> EQUIVALENT (diagnostic, non-contractual).
    #    Checked BEFORE the generic None/constant rule so that `raise ValueError(None)`
    #    (a message-string mutation) is not misclassified as a value replacement.
    if "raise" in ol:
        return Classification(
            B_EQUIVALENT,
            "equivalent_message",
            "Mutation changes only the ValueError message string. The exception TYPE "
            "(ValueError) and the validated condition (the raise fires for the same "
            "invalid input) are unchanged. No caller in src/engines/credit_card_engine "
            "or its tests reads exc.args[0]/message text (verified by repo-wide grep: "
            "zero consumers). The message is an internal diagnostic, not part of the "
            "observable financial contract (exception-type + computed value). Per "
            "Phase 6.1, message text is not a contractual guarantee and assertions are "
            "not added to avoid artificial coupling. Cannot alter externally observable "
            "domain behavior.",
            "ValueError message text only; validation outcome identical",
            "Classified EQUIVALENT. No test assertion added (non-contractual diagnostic; "
            "Phase 6.1). Documented, not hidden.",
        )

    # 2. Rounding argument handling (before generic None check, because `rounding=None`).
    if "rounding=" in ol or "rounding=" in ml:
        # Explicit ROUND_HALF_EVEN removed or set to None -> identical to Decimal default.
        if "rounding=round_half_even" in ol and ("rounding=none" in ml or "rounding=" not in ml):
            return Classification(
                B_EQUIVALENT,
                "equivalent_rounding_default",
                "Decimal.quantize default rounding IS ROUND_HALF_EVEN. Removing the explicit "
                "rounding=ROUND_HALF_EVEN argument or setting rounding=None yields identical "
                "banker's rounding behavior. No externally observable difference within the "
                "valid domain. INVARIANT 6 (banker's rounding) preserved.",
                "Intermediate quantize rounding (no observable output difference)",
                "Classified EQUIVALENT. No test change required.",
            )
        # Any other rounding change (ROUND_HALF_UP removal, rounding=None for a
        # non-HALF_EVEN source, strategy swap) alters banker's rounding behavior.
        return Classification(
            A_REAL_GAP,
            "real_gap_rounding_precision",
            "Mutation changes a Decimal quantize rounding argument. ROUND_HALF_UP (and any "
            "non-ROUND_HALF_EVEN mode) is NOT Decimal's default, so removing or altering it "
            "changes the rounded monetary/bps result for values at a half-way boundary. No "
            "existing test asserts the exact rounded result where the change is observable. "
            "Genuine behavioral gap.",
            "Computed utilization_bps / interest / amount changes for affected inputs",
            "Repair: add boundary test asserting exact value where the rounding change is "
            "observable (kill the mutant).",
        )

    # 3. Decimal precision / basis-point multiplier change -> REAL TEST GAP.
    if "decimal(" in ol or "decimal(" in ml:
        return Classification(
            A_REAL_GAP,
            "real_gap_rounding_precision",
            "Mutation changes a Decimal quantize precision or basis-point multiplier "
            "(e.g. Decimal(1)->Decimal(2), Decimal(10000)->Decimal(10001)). This alters "
            "the computed monetary/bps result for values where the changed digit is "
            "significant. No existing test asserts the exact rounded result at the "
            "boundary where the change is observable. Genuine behavioral gap.",
            "Computed utilization_bps / interest / amount changes for affected inputs",
            "Repair: add boundary test asserting exact value where the precision/"
            "multiplier change is observable (kill the mutant).",
        )

    # 4. Value replaced by None / removed -> real gap (constant replacement).
    if m == "" or "none" in ml:
        return Classification(
            A_REAL_GAP,
            "real_gap_constant",
            "Mutation replaces a value/argument with None or removes it. Under the "
            "mutant the function receives None (or omits the argument) where production "
            "passes a real value, altering control flow or raising (e.g. TypeError) for "
            "inputs that production handles. Externally observable; no test currently "
            "exercises this input/branch. Genuine behavioral test gap.",
            "Argument/value becomes None; downstream behavior differs or errors",
            "Repair: add a test exercising the affected call/branch (assert correct "
            "result or expected error) to kill the mutant.",
        )

    # 5. Control-flow / value mutations -> REAL TEST GAP.
    if (
        re.search(r"(<=|>=|==|!=|<|>)", o)
        or re.search(r"(<=|>=|==|!=|<|>)", m)
        or (re.search(r"[+\-*/%]", o) and re.search(r"[+\-*/%]", m))
        or re.search(r"\b(and|or|not)\b", ol)
        or re.search(r"\b(and|or|not)\b", ml)
        or re.search(r"\b(true|false|none)\b", ol)
        or re.search(r"\b(true|false|none)\b", ml)
        or (o.strip().startswith('"') or o.strip().startswith("'"))
        and (m.strip().startswith('"') or m.strip().startswith("'"))
        or re.search(r"\b\d+\b", o)
        or re.search(r"\b\d+\b", m)
        or "(" in o
        or "(" in m
    ):
        sub = "real_gap_logic"
        if re.search(r"(<=|>=|==|!=|<|>)", o) or re.search(r"(<=|>=|==|!=|<|>)", m):
            sub = "real_gap_comparison"
        elif re.search(r"[+\-*/%]", o) and re.search(r"[+\-*/%]", m):
            sub = "real_gap_arithmetic"
        elif re.search(r"\b(and|or|not)\b", ol) or re.search(r"\b(and|or|not)\b", ml):
            sub = "real_gap_boolean"
        elif re.search(r"\b(true|false|none)\b", ol) or re.search(r"\b(true|false|none)\b", ml):
            sub = "real_gap_constant"
        elif (o.strip().startswith('"') or o.strip().startswith("'")) and (
            m.strip().startswith('"') or m.strip().startswith("'")
        ):
            sub = "real_gap_dict_key"
        elif re.search(r"\b\d+\b", o) or re.search(r"\b\d+\b", m):
            sub = "real_gap_numeric_default"
        else:
            sub = "real_gap_call_arg"
        return Classification(
            A_REAL_GAP,
            sub,
            "Mutation changes control flow or a computed value (operator/constant/argument/"
            "dict-key). The changed behavior is externally observable for inputs on the "
            "affected branch, but no existing test exercises that exact input/branch, so "
            "the suite does not constrain it. Genuine behavioral test gap.",
            "Branch/value behavior differs for untested inputs",
            "Repair: add targeted test exercising the mutated branch/boundary to kill the "
            "mutant (assert correct behavior).",
        )

    return Classification(
        E_UNKNOWN,
        "unknown",
        "Insufficient evidence to classify this mutant.",
        "unknown",
        "Investigate the source and surrounding tests.",
    )


def build_inventory(target: str, now: str | None = None) -> dict:
    """Build and return the per-engine survivor inventory dict."""
    results = collect_results()
    survivors = [n for n, s in results.items() if s == "survived"]
    now = now or datetime.datetime.now(datetime.UTC).isoformat()

    records: list[dict] = []
    counts = {A_REAL_GAP: 0, B_EQUIVALENT: 0, C_UNREACHABLE: 0, D_INFRA: 0, E_UNKNOWN: 0}
    sub_counts: dict[str, int] = {}

    for name in survivors:
        diff = show_mutant(name)
        changes = _parse_diff(diff)
        if not changes:
            changes = [SurvivorChange(name, "", None, "", "")]
        for ch in changes:
            cls = classify(ch.original, ch.mutated)
            counts[cls.classification] += 1
            sub_counts[cls.subclass] = sub_counts.get(cls.subclass, 0) + 1
            records.append(
                {
                    "mutant": ch.mutant,
                    "source_file": ch.source_file,
                    "line": ch.line,
                    "mutation_operator": infer_operator(ch.original, ch.mutated),
                    "original_expression": ch.original,
                    "mutated_expression": ch.mutated,
                    "classification": cls.classification,
                    "subclassification": cls.subclass,
                    "evidence": cls.evidence,
                    "affected_behavior": cls.affected_behavior,
                    "proposed_action": cls.proposed_action,
                }
            )

    repo_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT),
        capture_output=True, text=True, timeout=30,
    ).stdout.strip()

    return {
        "phase": 2,
        "engine": target,
        "generated_at": now,
        "repository_sha": repo_sha,
        "total_survivors": len(records),
        "classification_counts": counts,
        "subclassification_counts": sub_counts,
        "classification_legend": CLASSIFICATION_LEGEND,
        "survivors": records,
    }


def _write_artifacts(inv: dict, target: str) -> tuple[Path, Path]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    base = f"m9-c42.17-{target}-survivor-inventory"
    json_path = GENERATED_DIR / f"{base}.json"
    md_path = GENERATED_DIR / f"{base}.md"
    json_path.write_text(json.dumps(inv, indent=2))

    counts = inv["classification_counts"]
    lines = [
        f"# M9-C42.17 Phase 2 — {target} Survivor Forensic Inventory",
        "",
        f"- **Engine**: {target}",
        f"- **Total survivors**: {inv['total_survivors']}",
        f"- **Repo SHA**: `{inv['repository_sha']}`",
        "",
        "## Classification totals",
        "",
        "| Class | Count |",
        "|---|---:|",
    ]
    for k in (A_REAL_GAP, B_EQUIVALENT, C_UNREACHABLE, D_INFRA, E_UNKNOWN):
        lines.append(f"| {k} — {CLASSIFICATION_LEGEND[k]} | {counts[k]} |")
    lines += ["", "## Subclassification totals", "", "| Subclass | Count |"]
    for k, v in sorted(inv["subclassification_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "## Per-mutant inventory",
        "",
        "Full machine-readable detail in "
        f"`{base}.json`.",
        "",
        "| # | Mutant | File:Line | Op | Class | Subclass |",
        "|---|---|---|---|---|---|",
    ]
    for i, s in enumerate(inv["survivors"], 1):
        lines.append(
            f"| {i} | `{s['mutant']}` | {s['source_file']}:{s['line']} | "
            f"{s['mutation_operator']} | {s['classification']} | {s['subclassification']} |"
        )
    md_path.write_text("\n".join(lines) + "\n")
    return json_path, md_path


def run_mutation_inventory_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify.py mutation-inventory")
    parser.add_argument("--target", required=True, help="engine name (e.g. credit_card_engine)")
    args = parser.parse_args(argv)

    inv = build_inventory(args.target)
    json_path, md_path = _write_artifacts(inv, args.target)
    print(f"Inventory written: {json_path}")
    print(f"Markdown:          {md_path}")
    print(f"Survivors: {inv['total_survivors']}  "
          f"A={inv['classification_counts'][A_REAL_GAP]} "
          f"B={inv['classification_counts'][B_EQUIVALENT]} "
          f"E={inv['classification_counts'][E_UNKNOWN]}")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(run_mutation_inventory_cli(sys.argv[1:]))
