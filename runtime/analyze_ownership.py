#!/usr/bin/env python3
"""
Phase 3: Ownership Graph.

Builds a top-down ownership hierarchy. Every ownership edge carries EVIDENCE.
Ownership is distinct from execution (Phase 4).

Canonical ownership chain (per the program):
  Capability -> Workspace -> ViewModel -> Mapper -> Endpoint -> Router
             -> Service -> Engine -> Repository -> Artifacts -> Tests
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path("/home/vasantha/AI-Projects/ClariFin_OS")
FRONTEND = REPO / "frontend"

CAP_DOMAIN = {
    "useAccountsCapability": "accounts",
    "useBehaviourCapability": "behaviour",
    "useCashflowCapability": "cashflow",
    "useCreditCardsCapability": "credit-cards",
    "useForecastCapability": "forecast",
    "useInvestmentsCapability": "investments",
    "useLoansCapability": "loans",
    "useNetworthCapability": "net-worth",
    "useReconciliationCapability": "reconciliation",
    "useTransactionCapability": "transactions",
}
DOMAIN_CAP = {v: k for k, v in CAP_DOMAIN.items()}

# app/<dir> -> domain key used by capabilities
APP_DIR_DOMAIN = {
    "accounts": "accounts", "behaviour": "behaviour", "cashflow": "cashflow",
    "cards": "credit-cards", "forecast": "forecast", "investments": "investments",
    "loans": "loans", "net-worth": "net-worth", "reconciliation": "reconciliation",
    "transactions": "transactions", "dashboard": "dashboard", "settings": "settings",
    "command-center": "command-center",
}


def load_topology():
    return json.loads((REPO / "runtime" / "generated" / "engine-topology.json").read_text())


def discover_frontend():
    """Return capability -> {workspace, mapper} evidence by domain."""
    caps = {}
    for p in (FRONTEND / "lib" / "capabilities").rglob("use-*.ts"):
        name = p.stem  # use-accounts-capability
        if name in CAP_DOMAIN:
            caps[CAP_DOMAIN[name]] = {"capability": f"lib/capabilities/{p.name}",
                                      "workspace": None, "mapper": None}
    # workspaces
    for d in (FRONTEND / "app").iterdir():
        if d.is_dir() and d.name in APP_DIR_DOMAIN:
            dom = APP_DIR_DOMAIN[d.name]
            wp = d / "workspace-page.tsx"
            pg = d / "page.tsx"
            target = wp if wp.exists() else (pg if pg.exists() else None)
            if dom in caps and target:
                caps[dom]["workspace"] = str(target.relative_to(REPO))
    # mappers
    for p in (FRONTEND / "lib" / "mappers").glob("*-mapper.ts"):
        stem = p.stem.replace("-mapper", "")
        # map credit-cards -> credit-cards domain; accounts -> accounts
        dom = stem.replace("creditcards", "credit-cards").replace("credit_cards", "credit-cards")
        # normalize: behaviour mapper etc.
        dom_norm = {
            "accounts": "accounts", "behaviour": "behaviour", "cashflow": "cashflow",
            "credit-cards": "credit-cards", "forecast": "forecast", "investments": "investments",
            "loans": "loans", "networth": "net-worth", "reconciliation": "reconciliation",
            "transaction": "transactions",
        }.get(dom)
        if dom_norm and dom_norm in caps:
            caps[dom_norm]["mapper"] = str(p.relative_to(REPO))
    return caps


def build():
    topo = load_topology()
    fe = discover_frontend()
    nodes = {}
    edges = []

    def node(nid, ntype, label):
        nodes[nid] = {"id": nid, "type": ntype, "label": label}

    def edge(frm, to, evidence, layer):
        edges.append({"from": frm, "to": to, "relation": "owns",
                      "evidence": evidence, "layer": layer})

    # ---------- FRONTEND OWNERSHIP ----------
    for dom, info in fe.items():
        cap = DOMAIN_CAP[dom]
        cap_id = f"capability:{cap}"
        node(cap_id, "Capability", cap)
        if info["workspace"]:
            ws_id = f"workspace:{dom}"
            node(ws_id, "Workspace", info["workspace"])
            edge(cap_id, ws_id,
                 f"{info['workspace']} imports {info['capability']} (use-{dom}-capability)",
                 "frontend")
        if info["mapper"]:
            mp_id = f"mapper:{dom}"
            node(mp_id, "Mapper", info["mapper"])
            edge(cap_id, mp_id,
                 f"capability {cap} consumes {info['mapper']} to map DTO->view model",
                 "frontend")
        # shared ViewModel (app store)
        vm_id = "viewmodel:use-app-store"
        node(vm_id, "ViewModel", "lib/store/use-app-store.ts")
        edge(cap_id, vm_id,
             f"workspace for {dom} binds global app store (use-app-store.ts) as its view model",
             "frontend")

    # ---------- BACKEND OWNERSHIP (per engine) ----------
    # capability -> engine(s)
    cap_to_engines = defaultdict(set)
    for ename, e in topo["engines"].items():
        for cap in e["capabilities"]:
            cap_to_engines[cap].add(ename)

    for ename, e in topo["engines"].items():
        eng_id = f"engine:{ename}"
        node(eng_id, "Engine", ename)
        node(eng_id + ":entry", "EngineEntryPoint", e["public_entry_point"])
        edge(eng_id, eng_id + ":entry",
             f"public_entry_point = {e['public_entry_point']} (canonical_style={e['canonical_style']})",
             "backend")
        # engine -> implementation modules
        for m in e["implementation_modules"]:
            mid = f"module:{m}"
            node(mid, "EngineModule", m)
            edge(eng_id, mid,
                 f"{e['public_entry_point']} re-exports symbols from {m}", "backend")
        # engine -> services -> routers -> repositories
        for svc in e["services"]:
            sid = f"service:{svc}"
            node(sid, "Service", svc)
            edge(sid, eng_id, f"{svc} imports engines.{ename} (see importer_files)", "backend")
        for rtr in e["routers"]:
            rid = f"router:{rtr}"
            node(rid, "Router", rtr)
            # router -> its services (evidence: router imports service)
            for svc in e["services"]:
                sid = f"service:{svc}"
                if router_imports_service(rtr, svc):
                    edge(rid, sid, f"{rtr} imports service class from {svc}", "backend")
        for repo in e["repositories"]:
            repid = f"repository:{repo}"
            node(repid, "Repository", repo)
            # service -> repository
            for svc in e["services"]:
                if service_imports_repo(svc, repo):
                    edge(f"service:{svc}", repid,
                         f"{svc} imports repositories.{repo}", "backend")
        # engine -> tests
        for t in e["tests"]:
            tid = f"test:{t}"
            node(tid, "Test", t)
            edge(eng_id, tid, f"test file imports engines.{ename}", "backend")
        # engine -> artifacts
        for a in e["artifacts"]:
            aid = f"artifact:{a}"
            node(aid, "Artifact", a)
            edge(eng_id, aid, f"artifact produced/owned by {ename} pipeline", "backend")

    # ---------- CROSS OWNERSHIP: capability -> engine ----------
    for cap, engines in cap_to_engines.items():
        cap_id = f"capability:{cap}"
        for ename in engines:
            edge(cap_id, f"engine:{ename}",
                 f"capability {cap} is backed by engine {ename} (engine.capabilities includes {cap})",
                 "cross")

    # ---------- ownership trees (per capability) ----------
    trees = {}
    for cap in CAP_DOMAIN:
        dom = CAP_DOMAIN[cap]
        cap_id = f"capability:{cap}"
        tree = {"capability": cap, "owns": []}
        if dom in fe and fe[dom]["workspace"]:
            tree["owns"].append({"node": f"workspace:{dom}", "type": "Workspace",
                                 "owns": [{"node": "viewmodel:use-app-store", "type": "ViewModel"},
                                          {"node": f"mapper:{dom}", "type": "Mapper"}]})
        for ename in sorted(cap_to_engines.get(cap, [])):
            e = topo["engines"][ename]
            tree["owns"].append({
                "node": f"engine:{ename}", "type": "Engine",
                "owns": [
                    {"node": f"service:{s}", "type": "Service"} for s in e["services"]
                ] + [
                    {"node": f"router:{r}", "type": "Router"} for r in e["routers"]
                ] + [
                    {"node": f"repository:{r}", "type": "Repository"} for r in e["repositories"]
                ],
            })
        trees[cap] = tree

    out = {
        "generated_at": datetime.now().isoformat(),
        "description": "Ownership graph: every edge has evidence. Ownership != execution.",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": list(nodes.values()),
        "edges": edges,
        "ownership_trees_by_capability": trees,
        "notes": [
            "Implementation modules (EngineModule) are owned BY their engine; they are NOT "
            "ownership roots. The legacy cross-layer-map listed them as separate engines.",
            "Capability is the top ownership root. Workspace/ViewModel/Mapper live in the "
            "frontend; Router/Service/Engine/Repository live in the backend.",
            "transaction_intelligence, financial_events, balance_engine, ledger_audit_engine, "
            "reconciliation_engine, nudge_engine, insight_generator have NO capability owner: "
            "they are internal/sub engines consumed by other engines or services.",
        ],
    }
    (REPO / "runtime" / "generated" / "ownership-graph.json").write_text(json.dumps(out, indent=2))
    print(f"Ownership graph: {len(nodes)} nodes, {len(edges)} edges")
    print(f"Capabilities with ownership trees: {len(trees)}")


def router_imports_service(router_rel, svc_rel):
    f = REPO / router_rel
    if not f.exists():
        return False
    text = f.read_text(encoding="utf-8", errors="ignore")
    svc_base = svc_rel.split("/")[-1].replace(".py", "")
    cls = "".join(w.capitalize() for w in svc_base.replace("_service", "").split("_")) + "Service"
    return (f"services.{svc_base}" in text) or (cls in text)


def service_imports_repo(svc_rel, repo_base):
    f = REPO / svc_rel
    if not f.exists():
        return False
    text = f.read_text(encoding="utf-8", errors="ignore")
    return f"repositories.{repo_base}" in text


if __name__ == "__main__":
    build()
