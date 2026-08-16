#!/usr/bin/env python3
"""
Phase 4: Execution Graph.

Separate from ownership. Represents the RUNTIME CALL PATH of a request:
  Capability -> Endpoint -> Router -> Service -> Engine -> ImplementationModule
            -> Repository -> Database

Execution MAY traverse implementation modules; ownership MUST NOT.
Every edge has evidence.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path("/home/vasantha/AI-Projects/ClariFin_OS")
FRONTEND = REPO / "frontend"


def load_topology():
    return json.loads((REPO / "runtime" / "generated" / "engine-topology.json").read_text())


def router_endpoints(router_rel):
    f = REPO / router_rel
    if not f.exists():
        return []
    text = f.read_text(encoding="utf-8", errors="ignore")
    eps = re.findall(r'@router\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', text)
    return [f"{m.upper()} {p}" for m, p in eps]


def build():
    topo = load_topology()
    nodes = {}
    edges = []

    def node(nid, ntype, label):
        nodes[nid] = {"id": nid, "type": ntype, "label": label}

    def edge(frm, to, evidence, stage):
        edges.append({"from": frm, "to": to, "relation": "executes",
                      "evidence": evidence, "stage": stage})

    # endpoint -> router map (for all routers seen in topology)
    all_routers = set()
    for e in topo["engines"].values():
        all_routers.update(e["routers"])
    endpoint_to_router = {}
    router_ep_map = {}
    for r in all_routers:
        eps = router_endpoints(r)
        router_ep_map[r] = eps
        for ep in eps:
            endpoint_to_router.setdefault(ep, r)

    # capability -> engines (from topology)
    cap_to_engines = defaultdict(set)
    for ename, e in topo["engines"].items():
        for cap in e["capabilities"]:
            cap_to_engines[cap].add(ename)

    # service -> engines (which engines a service imports)
    service_to_engines = defaultdict(set)
    for ename, e in topo["engines"].items():
        for svc in e["services"]:
            service_to_engines[svc].add(ename)

    for cap, engines in cap_to_engines.items():
        cap_id = f"capability:{cap}"
        node(cap_id, "Capability", cap)
        # endpoints + routers served by this capability's engines
        endpoints = set()
        routers = set()
        for ename in engines:
            for r in topo["engines"][ename]["routers"]:
                routers.add(r)
                endpoints.update(router_ep_map.get(r, []))
        # services imported by those routers that belong to capability engines
        services = set()
        for r in routers:
            for svc in service_imports_in_router(r):
                if any(ename in engines for ename in service_to_engines.get(svc, set())):
                    services.add(svc)
        repos = set()
        modules = set()
        for ename in engines:
            modules.update(topo["engines"][ename]["implementation_modules"])
            repos.update(topo["engines"][ename]["repositories"])

        # request: capability -> endpoints
        for ep in sorted(endpoints):
            ep_id = f"endpoint:{ep}"
            node(ep_id, "Endpoint", ep)
            edge(cap_id, ep_id, f"capability {cap} invokes HTTP {ep}", "request")
            rtr = endpoint_to_router.get(ep)
            if rtr:
                rid = f"router:{rtr}"
                node(rid, "Router", rtr)
                edge(ep_id, rid, f"{ep} is defined by @router decorator in {rtr}", "dispatch")
        # dispatch: routers -> services
        for r in sorted(routers):
            rid = f"router:{r}"
            node(rid, "Router", r)
            for svc in sorted(service_imports_in_router(r)):
                if svc in services:
                    sid = f"service:{svc}"
                    node(sid, "Service", svc)
                    edge(rid, sid, f"{r} instantiates/calls {svc} service", "business")
        # business: services -> engines (capability-scoped)
        for svc in sorted(services):
            sid = f"service:{svc}"
            node(sid, "Service", svc)
            for ename in sorted(service_to_engines.get(svc, set())):
                if ename in engines:
                    eid = f"engine:{ename}"
                    node(eid, "Engine", ename)
                    edge(sid, eid, f"{svc} calls engines.{ename} functions", "compute")
        # compute: engines -> implementation modules (EXECUTION traverses modules)
        for ename in sorted(engines):
            eid = f"engine:{ename}"
            node(eid, "Engine", ename)
            for m in sorted(topo["engines"][ename]["implementation_modules"]):
                mid = f"module:{m}"
                node(mid, "EngineModule", m)
                edge(eid, mid,
                     f"{ename} entry delegates computation to {m} "
                     f"(module is on the execution path)", "compute")
        # persistence: services -> repositories -> database
        dbid = "database:finance.db"
        node(dbid, "Database", "SQLite finance.db")
        for svc in sorted(services):
            sid = f"service:{svc}"
            node(sid, "Service", svc)
            for repo in sorted(repos):
                repid = f"repository:{repo}"
                node(repid, "Repository", repo)
                edge(sid, repid, f"{svc} reads/writes via repositories.{repo}", "persistence")
                edge(repid, dbid, f"{repo} opens connection to finance.db", "persistence")

    out = {
        "generated_at": datetime.now().isoformat(),
        "description": "Execution graph: runtime call path. Traverses implementation modules. "
                       "Distinct from ownership graph.",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": list(nodes.values()),
        "edges": edges,
        "notes": [
            "Execution traverses Engine -> ImplementationModule (the called compute function "
            "lives in a submodule). Ownership MUST NOT do this: modules are owned BY the engine.",
            "Repository/DB access is performed by the Service layer (around the Engine). "
            "Engines and their implementation modules are PURE (no DB, no I/O).",
            "Engines without a capability owner (transaction_intelligence, financial_events, "
            "balance_engine, ledger_audit_engine, reconciliation_engine) "
            "appear only as sub-nodes in other engines' execution traces "
            "or as internal services, never as a top-level capability execution root.",
        ],
    }
    (REPO / "runtime" / "generated" / "execution-graph.json").write_text(json.dumps(out, indent=2))
    print(f"Execution graph: {len(nodes)} nodes, {len(edges)} edges")


def service_imports_in_router(router_rel):
    f = REPO / router_rel
    if not f.exists():
        return []
    text = f.read_text(encoding="utf-8", errors="ignore")
    found = []
    for m in re.finditer(r"services\.([a-z_]+_service)\b", text):
        found.append(f"backend/src/services/{m.group(1)}.py")
    for m in re.finditer(r"from\s+[^ \n]*services\s+import\s+([^\n]+)", text):
        for cls in re.findall(r"\b([A-Z][a-zA-Z]*Service)\b", m.group(1)):
            s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", cls)
            base = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower().replace(".py", "")
            found.append(f"backend/src/services/{base}.py")
    # dedupe preserving order
    seen, out = set(), []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


if __name__ == "__main__":
    build()
