# runtime/foundation/verification/route_authority.py
#
# M9-C52.2 — CLI Route Authority Resolution.
#
# Deterministically resolves the verify.py CLI dispatch table from SOURCE
# (AST), detects any route name bound by more than one dispatcher branch
# (shadowing), and certifies that the formerly-shadowed `strengthen-survivor`
# route is now owned by exactly one capability, with the low-level forensic
# variant exposed under a distinct unshadowed name.
#
# This module audits/represents route ownership; it does not create a new
# capability or change execution behavior.

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_VERIFY_PY = REPO_ROOT / "runtime" / "verify.py"


@dataclass
class RouteBinding:
    route: str
    line: int
    target: str  # dotted module path of the imported/executed implementation
    capability: str  # catalog capability that owns the route (or "unclaimed")


def _import_target_in_block(block: ast.AST) -> str:
    """Best-effort: find the call/import inside a dispatcher branch."""
    for node in ast.walk(block):
        if isinstance(node, ast.ImportFrom) and node.module:
            return node.module
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                return fn.id
            if isinstance(fn, ast.Attribute):
                return f"{getattr(fn.value, 'id', '')}.{fn.attr}"
    return "unknown"


def analyze_dispatch_table() -> dict[str, Any]:
    """Parse verify.py and map route name -> list of {line, target}.

    A route bound by >1 branch is a SHADOW (ambiguous). This is the core
    audit: the C51 finding was that `strengthen-survivor` had 2 branches.
    """
    src = _VERIFY_PY.read_text()
    tree = ast.parse(src)

    bindings: dict[str, list[dict[str, Any]]] = {}

    # We collect `if/elif command == "route": <body>` from the main() function.
    def walk(node: ast.AST):
        for child in ast.iter_child_nodes(node):
            test_route = None
            body = []
            if isinstance(child, ast.If):
                test = child.test
                # command == "route"
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "command"
                    and len(test.ops) == 1
                    and isinstance(test.ops[0], ast.Eq)
                    and test.comparators
                    and isinstance(test.comparators[0], ast.Constant)
                    and isinstance(test.comparators[0].value, str)
                ):
                    test_route = test.comparators[0].value
                    body = child.body
            if test_route:
                target = None
                for stmt in body:
                    tgt = _import_target_in_block(stmt)
                    if tgt and tgt != "unknown":
                        target = tgt
                        break
                bindings.setdefault(test_route, []).append(
                    {
                        "route": test_route,
                        "line": child.lineno,
                        "target": target or "unknown",
                    }
                )
            walk(child)

    walk(tree)
    return bindings


def build_route_authority() -> dict[str, Any]:
    bindings = analyze_dispatch_table()

    shadows = {
        route: entries for route, entries in bindings.items() if len(entries) > 1
    }

    canon = {
        "strengthen-survivor": {
            "owner_capability": "strengthen.capability-pipeline",
            "implementation": "runtime.foundation.verification.strengthening_pipeline:cmd_strengthen_survivor",
            "class": "NORMAL_CERTIFICATION_PATH",
            "semantics": (
                "Canonical per-survivor route: capability-aware, durable-intel-"
                "driven analysis (intel -> classify -> propose -> validate -> "
                "revalidate). Does not require a live mutation run."
            ),
        },
        "strengthen-survivor-forensic": {
            "owner_capability": "strengthen.forensic",
            "implementation": "runtime.foundation.verification.forensic_cli:run_strengthen_survivor",
            "class": "INTENTIONAL_LOW_LEVEL_ESCAPE",
            "semantics": (
                "Low-level forensic per-survivor analyzer using mutmut built-ins "
                "(show / tests-for-mutant). REQUIRES a live mutation run. Explicit "
                "developer/diagnostic escape; never used silently by the "
                "certification path."
            ),
        },
    }

    # Cross-check the two distinct routes are not bound to the same target.
    same_target = False
    s1 = bindings.get("strengthen-survivor", [])
    s2 = bindings.get("strengthen-survivor-forensic", [])
    t1 = {e["target"] for e in s1}
    t2 = {e["target"] for e in s2}
    same_target = bool(t1 & t2)

    deterministic = (
        len(shadows) == 0 and len(s1) == 1 and len(s2) == 1 and not same_target
    )

    return {
        "schema": "m9-c52-route-authority/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_routes_bound": len(bindings),
        "shadows": shadows,
        "shadow_count": len(shadows),
        "strengthen_survivor_resolution": {
            "was_shadowed": True,
            "c51_finding": "C51 M51.6: 'Shadowed C48 strengthen-survivor route detected and documented'",
            "resolution": (
                "The route is bound by EXACTLY ONE dispatcher branch (the "
                "capability-aware pipeline). The low-level forensic variant was "
                "renamed to `strengthen-survivor-forensic` (distinct, unshadowed) "
                "so both capabilities remain executable with explicit semantics."
            ),
            "canonical_route": "strengthen-survivor",
            "canonical": canonical_entry(canon["strengthen-survivor"], s1),
            "forensic_route": "strengthen-survivor-forensic",
            "forensic": canonical_entry(canon["strengthen-survivor-forensic"], s2),
            "same_implementation": same_target,
            "deterministic": deterministic,
            "regression_test": "runtime/tests/test_m9_c52.py::test_route_resolution_no_shadows",
        },
        "passed": deterministic and len(shadows) == 0,
    }


def canonical_entry(
    meta: dict[str, str], entries: list[dict[str, Any]]
) -> dict[str, Any]:
    e = entries[0] if entries else {"line": None, "target": "unknown"}
    return {
        **meta,
        "bound_at_line": e.get("line"),
        "bound_target_from_source": e.get("target"),
    }


def main() -> int:
    auth = build_route_authority()
    out = REPO_ROOT / "runtime" / "generated" / "m9-c52" / "m9-c52-route-authority.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(auth, indent=2))
    print(
        f"routes={auth['total_routes_bound']} shadows={auth['shadow_count']} "
        f"strengthen-survivor-deterministic={auth['strengthen_survivor_resolution']['deterministic']} "
        f"passed={auth['passed']}"
    )
    return 0 if auth["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
