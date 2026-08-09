#!/usr/bin/env python3
"""
Phase 2: Engine Discovery / Engine Topology.

Discovers every real engine and, for each, identifies:
  - canonical_style (package | single_file)
  - public_entry_point
  - implementation_modules (Engine Module files)
  - services, routers, repositories that consume it (by import evidence)
  - tests
  - artifacts it produces
  - capabilities it backs

Evidence is gathered from import statements, registrations, router decorators,
and the existing cross-layer-map (used only as corroboration).
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path("/home/vasantha/AI-Projects/ClariFin_OS")
BACKEND = REPO / "backend" / "src"

# Canonical engine registry: name -> package root dir (relative to backend/src)
ENGINE_ROOTS = {
    "account_engine": "engines/account_engine",
    "behaviour_engine": "engines/behaviour_engine",
    "credit_card_engine": "engines/credit_card_engine",
    "financial_events": "engines/financial_events",
    "financial_intelligence": "engines/financial_intelligence",
    "loan_engine": "engines/loan_engine",
    "recommendation_engine": "engines/recommendation_engine",
    "transaction_intelligence": "engines/transaction_intelligence",
}
SINGLE_FILE_ENGINES = {
    "balance_engine": "engines/balance_engine.py",
    "cashflow_engine": "engines/cashflow_engine.py",
    "ledger_audit_engine": "engines/ledger_audit_engine.py",
    "reconciliation_engine": "engines/reconciliation_engine.py",
}
# NOTE (Program J): behavior_engine.py, nudge_engine.py and insight_generator.py no
# longer exist. Their behaviour lives in the behaviour_engine/ package
# (nudges.py, insights.py). No parked facade remains on disk.
PARKED_FACADE: dict[str, str] = {}


def classify_importer(rel: str) -> str:
    if "/services/" in rel:
        return "Service"
    if "/routers/" in rel:
        return "Router"
    if "/repositories/" in rel:
        return "Repository"
    if "/models/" in rel:
        return "Entity"
    if "/engines/" in rel:
        return "Engine"
    if "/core/mappers/" in rel or "/mappers/" in rel:
        return "Mapper"
    if "/dtos/" in rel:
        return "DTO"
    return "Other"


ENGINE_ROOT_NAMES = list(ENGINE_ROOTS.keys()) + list(SINGLE_FILE_ENGINES.keys())
ENGINE_PAT = re.compile(r"engines\.(" + "|".join(re.escape(n) for n in ENGINE_ROOT_NAMES) + r")\b")
REPO_PAT = re.compile(r"repositories\.([a-z_]+_repository)\b")
SERVICE_ATTR_PAT = re.compile(r"services\.([a-z_]+_service)\b")
SERVICE_IMPORT_PAT = re.compile(r"from\s+[^ \n]*services\s+import\s+([^\n]+)")


def camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def extract_service_modules(text: str):
    """Return set of service MODULE basenames (e.g. 'loan_service')."""
    mods = set()
    for m in SERVICE_ATTR_PAT.finditer(text):
        mods.add(m.group(1))
    for m in SERVICE_IMPORT_PAT.finditer(text):
        clause = m.group(1)
        for cls in re.findall(r"\b([A-Z][a-zA-Z]*Service)\b", clause):
            mods.add(camel_to_snake(cls))
    return mods


def file_tokens(rel: str):
    """Return sets of engine / service_module / repo_module tokens referenced."""
    f = REPO / rel
    engines, services, repos = set(), set(), set()
    if not f.exists():
        return engines, services, repos
    text = f.read_text(encoding="utf-8", errors="ignore")
    for m in ENGINE_PAT.finditer(text):
        engines.add(m.group(1))
    services = extract_service_modules(text)
    for m in REPO_PAT.finditer(text):
        repos.add(m.group(1))
    return engines, services, repos


def scan_importers():
    """Return engine_name -> {importer_rel: node_type} (direct engine importers)."""
    result = defaultdict(dict)
    for f in BACKEND.rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        rel = str(f.relative_to(REPO))
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in ENGINE_PAT.finditer(text):
            result[m.group(1)][rel] = classify_importer(rel)
    return result


def collect_service_and_repo_tokens():
    """Map each backend module rel -> (engines, services, repos) tokens."""
    tokens = {}
    for f in BACKEND.rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        rel = str(f.relative_to(REPO))
        tokens[rel] = file_tokens(rel)
    return tokens


def router_endpoints(router_rel: str):
    f = REPO / router_rel
    if not f.exists():
        return []
    text = f.read_text(encoding="utf-8", errors="ignore")
    eps = re.findall(r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', text)
    out = []
    for method, path in eps:
        out.append(f"{method.upper()} {path}")
    return out


def compute_consumers(name, imp, service_to_routers, service_to_repos):
    """Resolve services (direct), routers (direct + via services), repos (via services)."""
    svc_rels = sorted([r for r, t in imp.items() if t == "Service"])
    rtr_direct = sorted([r for r, t in imp.items() if t == "Router"])
    svc_basenames = [p.split("/")[-1].replace(".py", "") for p in svc_rels]
    rtr_transitive = set()
    repos = set()
    for sb in svc_basenames:
        rtr_transitive |= service_to_routers.get(sb, set())
        repos |= service_to_repos.get(sb, set())
    routers = sorted(set(rtr_direct) | rtr_transitive)
    return svc_rels, routers, sorted(repos)


def find_tests(engine_name: str):
    tests = []
    for f in (REPO / "backend" / "tests").rglob("*.py"):
        rel = str(f.relative_to(REPO))
        if "__pycache__" in rel:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # match engine root name in import or in path
        if re.search(r"engines\." + re.escape(engine_name) + r"\b", text) or engine_name in rel:
            tests.append(rel)
    return sorted(set(tests))


def engine_artifacts(engine_name: str):
    """Artifacts in runtime/generated produced by / named after the engine."""
    arts = []
    gen = REPO / "runtime" / "generated"
    # test-derived artifacts that reference the engine name
    for f in gen.rglob("*"):
        if f.is_file() and engine_name.replace("_", "") in f.name.lower().replace("_", "").replace("-", ""):
            arts.append(str(f.relative_to(REPO)))
    # known explicit artifacts
    known = {
        "loan_engine": ["runtime/generated/loan-results.txt"],
        "balance_engine": [],
        "ledger_audit_engine": [],
        "reconciliation_engine": [],
        "cashflow_engine": [],
        "account_engine": [],
        "behaviour_engine": [],
        "credit_card_engine": [],
        "financial_events": [],
        "financial_intelligence": [],
        "recommendation_engine": [],
        "transaction_intelligence": [],
    }
    for k in known.get(engine_name, []):
        if (REPO / k).exists() and k not in arts:
            arts.append(k)
    return sorted(set(arts))


def main():
    importers = scan_importers()
    tokens = collect_service_and_repo_tokens()

    # Build service -> routers map (routers that import a service)
    service_to_routers = defaultdict(set)
    for rel, (engs, svcs, repos) in tokens.items():
        if classify_importer(rel) == "Router":
            for s in svcs:
                service_to_routers[s].add(rel)
    # service -> repositories
    service_to_repos = defaultdict(set)
    for rel, (engs, svcs, repos) in tokens.items():
        if classify_importer(rel) == "Service":
            for r in repos:
                service_to_repos[rel.split("/")[-1].replace(".py", "")].add(r)

    topology = {
        "generated_at": datetime.now().isoformat(),
        "engine_count": 0,
        "engines": {},
        "parked_facades": {},
        "notes": [],
    }

    # Package engines
    for name, root in sorted(ENGINE_ROOTS.items()):
        entry = f"{root}/__init__.py"
        impl_modules = sorted(
            str(p.relative_to(REPO))
            for p in (BACKEND / root).rglob("*.py")
            if p.name != "__init__.py" and "__pycache__" not in str(p)
        )
        imp = importers.get(name, {})
        services, routers, repos = compute_consumers(name, imp, service_to_routers, service_to_repos)
        endpoints = sorted({e for r in routers for e in router_endpoints(r)})
        topology["engines"][name] = {
            "canonical_style": "package",
            "public_entry_point": entry,
            "implementation_modules": impl_modules,
            "implementation_module_count": len(impl_modules),
            "services": services,
            "routers": routers,
            "repositories": repos,
            "endpoints": endpoints,
            "endpoint_count": len(endpoints),
            "tests": find_tests(name),
            "artifacts": engine_artifacts(name),
            "capabilities": [],  # filled below
            "evidence": {
                "import_references": len(imp),
                "importer_files": sorted(imp.keys()),
            },
        }

    # Single-file engines
    for name, fp in sorted(SINGLE_FILE_ENGINES.items()):
        imp = importers.get(name, {})
        services, routers, repos = compute_consumers(name, imp, service_to_routers, service_to_repos)
        endpoints = sorted({e for r in routers for e in router_endpoints(r)})
        topology["engines"][name] = {
            "canonical_style": "single_file",
            "public_entry_point": fp,
            "implementation_modules": [],
            "implementation_module_count": 0,
            "services": services,
            "routers": routers,
            "repositories": repos,
            "endpoints": endpoints,
            "endpoint_count": len(endpoints),
            "tests": find_tests(name),
            "artifacts": engine_artifacts(name),
            "capabilities": [],
            "evidence": {
                "import_references": len(imp),
                "importer_files": sorted(imp.keys()),
            },
        }

    # Parked facade
    for name, fp in PARKED_FACADE.items():
        topology["parked_facades"][name] = {
            "path": fp,
            "status": "PARKED_LEGACY",
            "replaces": "engines/behaviour_engine/",
            "import_references": len(importers.get(name, {})),
        }

    topology["engine_count"] = len(topology["engines"])

    # ---- Capability mapping (evidence-based; cross-layer-map dependency removed) ----
    # A capability (frontend/lib/capabilities/use-XCapability.ts) backs an engine
    # when its fetch base path matches a router endpoint OWNED (via services) by
    # that engine. This removes the defective cross-layer-map linkage entirely
    # (which invented phantom <engine>.py keys and dropped useReconciliationCapability).
    def norm_cap_path(p: str) -> str:
        return p.replace("/api/v1", "/api").rstrip("/")

    cap_hooks: dict[str, list[str]] = defaultdict(list)
    cap_dir = REPO / "frontend" / "lib" / "capabilities"
    if cap_dir.exists():
        for f in sorted(cap_dir.glob("*.ts")):
            text = f.read_text(encoding="utf-8", errors="ignore")
            for sym in re.findall(r"export function (use\w*Capability)", text):
                cap_hooks[sym].append(str(f.relative_to(REPO)))

    # router -> owning engines (from the topology computed above)
    router_owners: dict[str, set[str]] = defaultdict(set)
    for _name, _entry in topology["engines"].items():
        for _r in _entry.get("routers", []):
            router_owners[_r].add(_name)

    endpoint_cache: dict[str, list[str]] = {}

    def eps_of(router_rel: str) -> list[str]:
        if router_rel not in endpoint_cache:
            endpoint_cache[router_rel] = full_endpoints(router_rel)
        return endpoint_cache[router_rel]

    def full_endpoints(router_rel: str) -> list[str]:
        """Return METHOD + (prefix + path) endpoint signatures for a router file."""
        f = REPO / router_rel
        if not f.exists():
            return []
        text = f.read_text(encoding="utf-8", errors="ignore")
        pm = re.search(r'APIRouter\(\s*prefix=["\']([^"\']+)["\']', text)
        pre = pm.group(1) if pm else ""
        out = []
        for m, p in re.findall(
            r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', text
        ):
            full = pre + p if p != "/" else pre
            out.append(f"{m.upper()} {full}")
        return out

    caps_by_root: dict[str, set[str]] = defaultdict(set)
    for sym, rels in cap_hooks.items():
        bases: set[str] = set()
        for rel in rels:
            try:
                t2 = (REPO / rel).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in re.findall(r"fetch\(\s*['\"`](/api[^'\"`?]*)", t2):
                bases.add(m)
        for base in bases:
            nb = norm_cap_path(base)
            for router_rel, owners in router_owners.items():
                for ep in eps_of(router_rel):
                    ep_path = norm_cap_path(ep.split(" ", 1)[1])
                    if ep_path == nb or ep_path.startswith(nb + "/"):
                        for owner in owners:
                            caps_by_root[owner].add(sym)
                        break
    for eng in topology["engines"]:
        topology["engines"][eng]["capabilities"] = sorted(caps_by_root.get(eng, set()))

    # Notes / observations
    topology["notes"].append(
        "Cross-layer-map invents 7 non-existent '.py' engine files "
        "(account_engine.py, credit_card_engine.py, financial_events.py, "
        "financial_intelligence.py, recommendation_engine.py, "
        "transaction_intelligence.py, behaviour_engine.py) by treating "
        "engine PACKAGE directories as files. These package roots are "
        "real engines; their __init__.py is the public entry point."
    )
    topology["notes"].append(
        "Internal engine submodules (e.g. behaviour_engine/core.py, "
        "account_engine/balance.py) are listed as separate 'engines' in "
        "cross-layer-map. They are Engine Modules, NOT ownership roots."
    )

    out = REPO / "runtime" / "generated" / "engine-topology.json"
    out.write_text(json.dumps(topology, indent=2))
    print(f"Engines discovered: {topology['engine_count']}")
    print(f"Parked facades: {len(topology['parked_facades'])}")
    for n, e in sorted(topology["engines"].items()):
        print(f"  {n:24} style={e['canonical_style']:10} svc={len(e['services'])} "
              f"rtr={len(e['routers'])} mods={e['implementation_module_count']} "
              f"caps={e['capabilities']}")


if __name__ == "__main__":
    main()
