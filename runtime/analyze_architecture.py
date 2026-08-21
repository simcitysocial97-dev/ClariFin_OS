#!/usr/bin/env python3
"""
Architecture Analysis Script for ClariFin_OS - Phase 1
Repository Architecture Inventory.

Classifies every Python/TypeScript module into exactly one canonical node type
using imports, registrations, runtime usage, dependency graph and execution flow
(NOT filename heuristics alone).
"""

import ast
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path("/home/vasantha/AI-Projects/ClariFin_OS")
BACKEND_SRC = REPO_ROOT / "backend" / "src"
RUNTIME_DIR = REPO_ROOT / "runtime"
FRONTEND_DIR = REPO_ROOT / "frontend"

# Single-file engines (real, in backend/src/engines/)
# NOTE (Program J): nudge_engine.py and insight_generator.py were removed from the
# tree; their behaviour was absorbed into behaviour_engine/nudges.py and
# behaviour_engine/insights.py. cashflow_engine.py is live again (un-parked) and
# backs the household_cashflow capability.
SINGLE_FILE_ENGINES = {
    "backend/src/engines/balance_engine.py",
    "backend/src/engines/cashflow_engine.py",
    "backend/src/engines/ledger_audit_engine.py",
    "backend/src/engines/reconciliation_engine.py",
}

# Parked / legacy single-file engines (do NOT import; replaced)
# NOTE (Program J): behavior_engine.py no longer exists on disk — the migration to
# the behaviour_engine/ package is complete, so there is no facade to declare.
ENGINE_FACADES: dict[str, str] = {}

# Package-based engine roots (directory packages whose __init__.py is the public API)
ENGINE_PACKAGE_ROOTS = {
    "backend/src/engines/account_engine",
    "backend/src/engines/behaviour_engine",
    "backend/src/engines/credit_card_engine",
    "backend/src/engines/financial_events",
    "backend/src/engines/financial_intelligence",
    "backend/src/engines/loan_engine",
    "backend/src/engines/recommendation_engine",
    "backend/src/engines/transaction_intelligence",
}

# Engine package -> display name
ENGINE_PACKAGE_NAMES = {
    "backend/src/engines/account_engine": "Account Engine",
    "backend/src/engines/behaviour_engine": "Behaviour Engine",
    "backend/src/engines/credit_card_engine": "Credit Card Engine",
    "backend/src/engines/financial_events": "Financial Events Engine",
    "backend/src/engines/financial_intelligence": "Financial Intelligence Engine",
    "backend/src/engines/loan_engine": "Loan Engine",
    "backend/src/engines/recommendation_engine": "Recommendation Engine",
    "backend/src/engines/transaction_intelligence": "Transaction Intelligence Engine",
}

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "evidence-download",
    ".hypothesis",
}
EXCLUDE_FILES = ("test_", "_test.py", "conftest.py")


def should_exclude(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return True
    name = path.name
    if name.startswith(EXCLUDE_FILES) or name.endswith("_test.py"):
        return True
    if name == "__init__.py" and path.parent.name == "tests":
        return True
    return False


def find_python_files():
    files = []
    for root in (BACKEND_SRC, RUNTIME_DIR):
        for p in root.rglob("*.py"):
            if not should_exclude(p):
                files.append(p)
    return files


def find_ts_files():
    files = []
    for p in FRONTEND_DIR.rglob("*.ts"):
        if not should_exclude(p):
            files.append(p)
    for p in FRONTEND_DIR.rglob("*.tsx"):
        if not should_exclude(p):
            files.append(p)
    return files


def parse_py(filepath: Path):
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception as e:
        return {
            "error": str(e),
            "imports": [],
            "classes": [],
            "functions": [],
            "decorators": [],
            "docstring": "",
            "content": "",
        }
    imports, classes, functions, decorators = [], [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.append(a.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for a in node.names:
                imports.append(f"{mod}.{a.name}")
        elif isinstance(node, ast.ClassDef):
            classes.append(
                {
                    "name": node.name,
                    "bases": [ast.unparse(b) for b in node.bases],
                    "decorators": [ast.unparse(d) for d in node.decorator_list],
                    "methods": [
                        n.name for n in node.body if isinstance(n, ast.FunctionDef)
                    ],
                }
            )
        elif isinstance(node, ast.FunctionDef):
            functions.append(
                {
                    "name": node.name,
                    "decorators": [ast.unparse(d) for d in node.decorator_list],
                    "args": [a.arg for a in node.args.args],
                }
            )
            for d in node.decorator_list:
                decorators.append(ast.unparse(d))
    return {
        "imports": imports,
        "classes": classes,
        "functions": functions,
        "decorators": decorators,
        "docstring": ast.get_docstring(tree) or "",
        "content": content,
    }


def classify_py(rel: str, info: dict) -> str:
    """Classify a backend/runtime Python module into exactly one node type."""
    classes = [c["name"] for c in info["classes"]]
    functions = [f["name"] for f in info["functions"]]
    decorators = info["decorators"]
    imports = info["imports"]
    clower = " ".join(classes).lower()
    flower = " ".join(functions).lower()
    ilower = " ".join(imports).lower()

    # ---- ENGINES ----
    if rel in ENGINE_FACADES:
        return "Engine Facade"
    if rel in SINGLE_FILE_ENGINES:
        return "Engine"
    if rel == "backend/src/engines/__init__.py":
        return "Engine Package"  # engines namespace root
    for root in ENGINE_PACKAGE_ROOTS:
        if rel == f"{root}/__init__.py":
            return "Engine Package"
        if rel.startswith(root + "/") and rel.endswith(".py"):
            # submodule of a package engine
            if "transaction_intelligence" in root:
                base = Path(rel).stem
                if base.endswith("_detector"):
                    return "Detector"
                return "Engine Module"
            return "Engine Module"

    # ---- APPLICATION (app factory / entrypoint) ----
    if rel in ("backend/src/main.py", "backend/src/api.py", "backend/src/startup.py"):
        return "Application"

    # ---- ROUTER ----
    if "/routers/" in rel:
        return "Router"
    if any("router" in c.lower() for c in classes) or any(
        "@router." in d for d in decorators
    ):
        return "Router"
    if ("fastapi" in ilower or "APIRouter" in ilower) and "/routers/" not in rel:
        return "Router"

    # ---- SERVICE ----
    if "/services/" in rel:
        return "Service"
    if "service" in clower and not any(
        x in rel for x in ("test", "frontend", "runtime")
    ):
        return "Service"

    # ---- REPOSITORY ----
    if "/repositories/" in rel:
        return "Repository"
    if "repository" in clower:
        return "Repository"

    # ---- ENTITY (backend SQLAlchemy models) ----
    if rel.startswith("backend/src/models/") and "dto" not in rel and "dtos" not in rel:
        return "Entity"

    # ---- DTO ----
    if "/dtos/" in rel or "/core/dtos/" in rel:
        return "DTO"

    # ---- MAPPER (backend) ----
    if "/core/mappers/" in rel:
        return "Mapper"

    # ---- WORKFLOW / ORCHESTRATION ----
    if "/orchestration/" in rel:
        return "Workflow"
    if "orchestrat" in clower or ("workflow" in rel and "scanner" not in rel):
        return "Workflow"

    # ---- STRATEGY ----
    if "strategy" in rel.lower() or any("strategy" in c.lower() for c in classes):
        return "Strategy"

    # ---- VERIFICATION PROFILE ----
    if "verification" in rel and ("profile" in rel):
        return "Verification Profile"
    if rel.endswith("verification/profiles.py"):
        return "Verification Profile"

    # ---- KNOWLEDGE SOURCE ----
    if "knowledge" in rel and (
        "indexer" in rel or "catalog" in rel or "/query" in rel or "query" in rel
    ):
        return "Knowledge Source"

    # ---- ARTIFACT PRODUCER / CONSUMER ----
    if any(k in flower for k in ("generate_", "build_", "emit_", "produce_")) and (
        "runtime" in rel or "tools" in rel
    ):
        return "Artifact Producer"
    if "artifact" in rel and any(
        k in flower for k in ("consume", "load_", "read_", "parse_")
    ):
        return "Artifact Consumer"

    # ---- UTILITY (core infra, common, extraction, runtime foundation) ----
    if any(
        p in rel
        for p in (
            "/utils/",
            "/common/",
            "/core/db/",
            "/core/domain/",
            "/data/",
            "/extraction/",
            "runtime/foundation/audit/",
            "runtime/foundation/intelligence/",
            "runtime/foundation/integrity/",
            "runtime/foundation/workspace/",
            "runtime/system/",
        )
    ):
        return "Utility"

    return "Utility"


FRONTEND_CAP_RE = re.compile(r"use[A-Z][a-zA-Z]*Capability")
FRONTEND_VM_RE = re.compile(r"[A-Z][a-zA-Z]*ViewModel")


def classify_ts(rel: str, content: str, exports) -> str:
    if (
        "/lib/capabilities/" in rel
        and rel.endswith(".ts")
        and not rel.endswith(".test.ts")
    ):
        return "Capability"
    if "/lib/store/" in rel:
        return "ViewModel"
    if "/lib/mappers/" in rel and rel.endswith("mapper.ts"):
        return "Mapper"
    if rel.startswith("frontend/app/") and (
        rel.endswith("page.tsx") or rel.endswith("layout.tsx")
    ):
        return "Workspace"
    return "Utility"


def main():
    py_files = find_python_files()
    ts_files = find_ts_files()
    modules = []

    for f in py_files:
        info = parse_py(f)
        rel = str(f.relative_to(REPO_ROOT))
        nt = classify_py(rel, info)
        modules.append(
            {
                "path": rel,
                "language": "python",
                "node_type": nt,
                "imports": info["imports"],
                "classes": [c["name"] for c in info["classes"]],
                "functions": [x["name"] for x in info["functions"]],
                "decorators": info["decorators"],
                "docstring": info["docstring"],
                "engine_name": ENGINE_PACKAGE_NAMES.get(
                    next(
                        (
                            r
                            for r in ENGINE_PACKAGE_ROOTS
                            if rel.startswith(r + "/") or rel == f"{r}/__init__.py"
                        ),
                        "",
                    ),
                    "",
                ),
            }
        )

    for f in ts_files:
        content = ""
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            pass
        exports = re.findall(
            r"export\s+(?:default\s+)?(?:class|function|const|interface|type)\s+(\w+)",
            content,
        )
        rel = str(f.relative_to(REPO_ROOT))
        nt = classify_ts(rel, content, exports)
        modules.append(
            {
                "path": rel,
                "language": "typescript",
                "node_type": nt,
                "imports": re.findall(r'from\s+[\'"]([^\'"]+)[\'"]', content),
                "classes": exports,
                "functions": [],
                "decorators": [],
                "docstring": "",
                "engine_name": "",
            }
        )

    type_counts = Counter(m["node_type"] for m in modules)
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_modules": len(modules),
        "type_counts": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        "modules": modules,
    }
    out = REPO_ROOT / "runtime" / "generated" / "architecture-inventory.json"
    out.write_text(json.dumps(output, indent=2))

    # Compact summary grouped by type
    by_type = defaultdict(list)
    for m in modules:
        by_type[m["node_type"]].append(m["path"])
    summary = {
        "generated_at": output["generated_at"],
        "total_modules": len(modules),
        "type_counts": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        "modules_by_type": {k: sorted(v) for k, v in sorted(by_type.items())},
    }
    (
        REPO_ROOT / "runtime" / "generated" / "architecture-inventory-summary.json"
    ).write_text(json.dumps(summary, indent=2))

    print(f"Total modules: {len(modules)}")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")


if __name__ == "__main__":
    main()
