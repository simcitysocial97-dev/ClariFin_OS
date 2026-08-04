#!/usr/bin/env python3
"""Cross-Layer Intelligence Map Generator - Program 7A.

Generates deterministic dependency graph: Engine → Service → Router → Endpoint → Capability → Mapper → ViewModel → Workspace → Component → Renderer → Tests.
Generated artifact. Never edit manually.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "runtime" / "generated" / "cross-layer-map.json"

BACKEND_SERVICES = PROJECT_ROOT / "backend" / "src" / "services"
BACKEND_ROUTERS = PROJECT_ROOT / "backend" / "src" / "routers"
BACKEND_ENGINES = PROJECT_ROOT / "backend" / "src" / "engines"
FRONTEND_CAPABILITIES = PROJECT_ROOT / "frontend" / "lib" / "capabilities"
FRONTEND_APP = PROJECT_ROOT / "frontend" / "app"
FRONTEND_GRAPH = PROJECT_ROOT / "frontend" / "lib" / "graph"


@dataclass
class EngineEntry:
    engine_file: str
    services: list[str] = field(default_factory=list)


@dataclass
class ServiceEntry:
    service_module: str
    routers: list[str] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)


@dataclass
class RouterEntry:
    router_file: str
    endpoints: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)


@dataclass
class CapabilityEntry:
    capability_file: str
    hook_name: str = ""
    api_paths: list[str] = field(default_factory=list)
    mappers: list[str] = field(default_factory=list)
    view_models: list[str] = field(default_factory=list)


@dataclass
class WorkspaceEntry:
    workspace_name: str = ""
    page: str = ""
    workspace: str = ""
    components: list[str] = field(default_factory=list)
    graph_renderers: list[str] = field(default_factory=list)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _find_engine_imports(src: str) -> list[str]:
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return re.findall(r"from\s+src\.engines\.([\w\.]+)", src)
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("src.engines"):
            out.append(n.module)
    return out


def _find_classes(src: str) -> list[str]:
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            out.append(n.name)
    return out


def _find_service_imports(src: str) -> list[str]:
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("src.services"):
            for a in n.names:
                out.append(a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("src.services"):
                    out.append(a.name)
    return out


def _find_endpoints(src: str) -> list[str]:
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    methods = {"get", "post", "put", "delete", "patch", "options", "head"}
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            for d in n.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                    m = d.func.attr
                    if m in methods and d.args:
                        a = d.args[0]
                        if isinstance(a, ast.Constant) and isinstance(a.value, str):
                            out.append(f"{m.upper()} {a.value}")
    return out


def _find_router_prefix(src: str) -> str:
    m = re.search(r'APIRouter\(\s*prefix=["\']([^"\']+)["\']', src)
    return m.group(1) if m else ""


def _find_api_paths(src: str) -> list[str]:
    out = []
    # Double-quoted strings
    out.extend(re.findall(r'fetch\(\s*["\'](/api/[^"\']+)["\']', src))
    # Template literals (backticks)
    out.extend(re.findall(r'fetch\(\s*`(/api/[^`]+)`', src))
    return list(dict.fromkeys(out))  # deduplicate preserving order


def _hook_name(path: Path) -> str:
    parts = path.stem.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _find_mappers(src: str) -> list[str]:
    out = []
    for m in re.finditer(r"import\s*\{([^}]+)\}\s*from\s*['\"](?:@/lib/mappers|\.\./\.\./\.\./lib/mappers|\.\./mappers)[^'\"]*['\"]", src):
        for n in m.group(1).split(","):
            n = n.strip()
            if n:
                out.append(n)
    return out


def _find_view_models(src: str) -> list[str]:
    out = []
    for m in re.finditer(r"import\s+type\s*\{([^}]+)\}\s*from\s*['\"](?:@/types|\.\./\.\./types)[^'\"]*['\"]", src):
        for n in m.group(1).split(","):
            n = n.strip()
            if "ViewModel" in n:
                out.append(n)
    return out


def _find_components(src: str) -> list[str]:
    out = []
    for m in re.finditer(r"import\s*\{([^}]+)\}\s*from\s*['\"](?:@/components|\.\./components|\.\./\.\./components)[^'\"]*['\"]", src):
        for n in m.group(1).split(","):
            n = n.strip()
            if n:
                out.append(n)
    return out


def _parse_layer_a() -> dict[str, EngineEntry]:
    emap: dict[str, EngineEntry] = {}
    if not BACKEND_SERVICES.exists():
        return emap
    for sf in sorted(BACKEND_SERVICES.rglob("*.py")):
        if sf.name == "__init__.py":
            continue
        src = _read(sf)
        imports = _find_engine_imports(src)
        classes = _find_classes(src)
        if not imports:
            continue
        for imp in imports:
            parts = imp.replace("src.engines.", "").split(".")
            edir = BACKEND_ENGINES / parts[0]
            if not edir.exists():
                continue
            if parts[0] == "loan_engine" and len(parts) > 1:
                efile = f"backend/src/engines/{parts[0]}/{parts[1]}.py"
            elif parts[0] == "loan_engine":
                efile = f"backend/src/engines/{parts[0]}/__init__.py"
            else:
                efile = f"backend/src/engines/{parts[0]}.py"
            entry = emap.setdefault(efile, EngineEntry(engine_file=efile))
            for c in classes:
                if c not in entry.services:
                    entry.services.append(c)
    # Sub-module imports
    pattern = re.compile(r"from\s+src\.engines\.([\w\.]+)\s+import")
    for sf in sorted(BACKEND_SERVICES.rglob("*.py")):
        if sf.name == "__init__.py":
            continue
        src = _read(sf)
        classes = _find_classes(src)
        for m in pattern.finditer(src):
            parts = m.group(1).split(".")
            if len(parts) >= 2:
                efile = f"backend/src/engines/{parts[0]}/{parts[1]}.py"
                entry = emap.setdefault(efile, EngineEntry(engine_file=efile))
                for c in classes:
                    if c not in entry.services:
                        entry.services.append(c)

    # Expand: for each engine package directory that has entries, add all
    # sub-module files mapping the same services.
    for eng_dir in sorted(BACKEND_ENGINES.rglob("*")):
        if not eng_dir.is_dir():
            continue
        # Check if any engine entry maps to a file in this directory package root
        package_key = ""
        for k in emap.keys():
            if k.startswith(f"backend/src/engines/{eng_dir.name}"):
                package_key = k
                break
        if not package_key and eng_dir.name.endswith("_engine"):
            for k in emap.keys():
                if f"backend/src/engines/{eng_dir.name}.py" == k:
                    package_key = k
                    break
        if not package_key:
            continue
        # Add all sub-module files in this package
        for subfile in sorted(eng_dir.rglob("*.py")):
            if subfile.name == "__init__.py":
                continue
            rel = subfile.relative_to(PROJECT_ROOT).as_posix()
            if rel not in emap:
                emap[rel] = EngineEntry(engine_file=rel, services=list(emap[package_key].services))
    return emap


def _parse_layer_b() -> tuple[dict[str, ServiceEntry], dict[str, RouterEntry]]:
    smap: dict[str, ServiceEntry] = {}
    rmap: dict[str, RouterEntry] = {}
    if not BACKEND_ROUTERS.exists():
        return smap, rmap
    for rf in sorted(BACKEND_ROUTERS.rglob("*.py")):
        if rf.name == "__init__.py":
            continue
        rel = rf.relative_to(PROJECT_ROOT).as_posix()
        src = _read(rf)
        eps = _find_endpoints(src)
        prefix = _find_router_prefix(src)
        svcs = _find_service_imports(src)
        full_eps = []
        for ep in eps:
            method, path = ep.split(" ", 1)
            full = path
            if prefix and not path.startswith(prefix):
                full = f"{prefix}{path}" if prefix.endswith("/") or path.startswith("/") else f"{prefix}/{path}"
            full_eps.append(f"{method} {full}")
        rmap[rel] = RouterEntry(router_file=rel, endpoints=full_eps, services=svcs)
        for s in svcs:
            e = smap.setdefault(s, ServiceEntry(service_module=s))
            if rel not in e.routers:
                e.routers.append(rel)
            for ep in full_eps:
                if ep not in e.endpoints:
                    e.endpoints.append(ep)
    return smap, rmap


def _parse_layer_c() -> dict[str, CapabilityEntry]:
    cmap: dict[str, CapabilityEntry] = {}
    if not FRONTEND_CAPABILITIES.exists():
        return cmap
    for cf in sorted(FRONTEND_CAPABILITIES.glob("*.ts")):
        if cf.name in ("index.ts", "__init__.ts"):
            continue
        rel = cf.relative_to(PROJECT_ROOT).as_posix()
        src = _read(cf)
        hook = _hook_name(cf)
        cmap[hook] = CapabilityEntry(
            capability_file=rel, hook_name=hook,
            api_paths=_find_api_paths(src),
            mappers=_find_mappers(src),
            view_models=_find_view_models(src),
        )
    return cmap


def _parse_layer_d() -> dict[str, WorkspaceEntry]:
    wmap: dict[str, WorkspaceEntry] = {}
    if FRONTEND_APP.exists():
        for pf in sorted(FRONTEND_APP.rglob("workspace-page.tsx")):
            rel_dir = pf.parent.relative_to(FRONTEND_APP).as_posix()
            src = _read(pf)
            comps = _find_components(src)
            wmap[rel_dir] = WorkspaceEntry(
                workspace_name=rel_dir,
                page=f"app/{rel_dir}/page.tsx",
                workspace=f"{rel_dir.capitalize()}Workspace",
                components=comps,
            )
    renderer = FRONTEND_GRAPH / "renderer" / "graph-renderer.tsx"
    if renderer.exists():
        for e in wmap.values():
            e.graph_renderers.append("components/graph/renderer/graph-renderer.tsx")
    return wmap


def _find_engine_tests(engine_file: str) -> list[str]:
    tests = []
    ename = ""
    for part in engine_file.split("/"):
        if part.endswith("_engine"):
            ename = part.replace("_engine", "")
            break
    if not ename:
        return tests
    ud = PROJECT_ROOT / "backend" / "tests" / "unit" / "engines" / ename
    if ud.exists():
        for t in sorted(ud.rglob("*.py")):
            tests.append(t.relative_to(PROJECT_ROOT).as_posix())
    cd = PROJECT_ROOT / "backend" / "tests" / "contract" / "generated"
    if cd.exists():
        for t in sorted(cd.glob("*.py")):
            if ename in t.name or "v1" in t.name:
                tests.append(t.relative_to(PROJECT_ROOT).as_posix())
    pd = PROJECT_ROOT / "backend" / "tests" / "properties" / ename
    if pd.exists():
        for t in sorted(pd.rglob("*.py")):
            tests.append(t.relative_to(PROJECT_ROOT).as_posix())
    fc = PROJECT_ROOT / "frontend" / "__tests__" / "api-contracts"
    if fc.exists():
        for t in sorted(fc.glob("*contract.test.ts")):
            if ename in t.name.lower():
                tests.append(t.relative_to(PROJECT_ROOT).as_posix())
    ct = PROJECT_ROOT / "frontend" / "lib" / "capabilities" / "__tests__"
    if ct.exists():
        for t in sorted(ct.glob("*.test.ts")):
            if ename in t.name.lower():
                tests.append(t.relative_to(PROJECT_ROOT).as_posix())
    return tests


def _build(
    emap: dict[str, EngineEntry], smap: dict[str, ServiceEntry],
    rmap: dict[str, RouterEntry], cmap: dict[str, CapabilityEntry],
    wmap: dict[str, WorkspaceEntry],
) -> dict:
    result = {}
    for efile, ee in emap.items():
        chain = {
            "engine": efile, "services": list(ee.services), "routers": [],
            "endpoints": [], "capabilities": [], "mappers": [], "viewModels": [],
            "pages": [], "workspace": [], "components": [], "graphRenderers": [],
            "tests": [],
        }
        for sn in ee.services:
            se = smap.get(sn)
            if se:
                for r in se.routers:
                    if r not in chain["routers"]:
                        chain["routers"].append(r)
                for ep in se.endpoints:
                    if ep not in chain["endpoints"]:
                        chain["endpoints"].append(ep)
        for ep in chain["endpoints"]:
            _, path = ep.split(" ", 1)
            norm = path.replace("{", "").replace("}", "")
            # Normalize /api/v1 prefix variations to /api
            norm_v1 = norm.replace("/api/v1", "/api")
            for hook, ce in cmap.items():
                for ap in ce.api_paths:
                    ap_norm = ap.replace("{", "").replace("}", "")
                    ap_v1 = ap_norm.replace("/api/v1", "/api")
                    # Match if one path contains the other or v1-normalized forms match
                    if (
                        norm in ap_norm or ap_norm in norm or
                        norm_v1 in ap_v1 or ap_v1 in norm_v1 or
                        norm_v1 == ap_v1
                    ):
                        if hook not in chain["capabilities"]:
                            chain["capabilities"].append(hook)
                            for m in ce.mappers:
                                if m not in chain["mappers"]:
                                    chain["mappers"].append(m)
                            for v in ce.view_models:
                                if v not in chain["viewModels"]:
                                    chain["viewModels"].append(v)
                            break
        for cap in chain["capabilities"]:
            for wn, we in wmap.items():
                # Check workspace-page.tsx first (where capability calls live)
                ws_page = PROJECT_ROOT / "frontend" / "app" / wn / "workspace-page.tsx"
                psrc = _read(ws_page) if ws_page.exists() else ""
                # Fall back to page.tsx
                if cap not in psrc:
                    page = PROJECT_ROOT / we.page
                    psrc = _read(page) if page.exists() else ""
                if cap in psrc:
                    if we.page not in chain["pages"]:
                        chain["pages"].append(we.page)
                    if we.workspace not in chain["workspace"]:
                        chain["workspace"].append(we.workspace)
                    for c in we.components:
                        if c not in chain["components"]:
                            chain["components"].append(c)
                    for r in we.graph_renderers:
                        if r not in chain["graphRenderers"]:
                            chain["graphRenderers"].append(r)
        chain["tests"] = _find_engine_tests(efile)
        result[efile] = chain
    return result


def main() -> int:
    print("Building Cross-Layer Intelligence Map...")
    emap = _parse_layer_a()
    print(f"  Engine files: {len(emap)}")
    smap, rmap = _parse_layer_b()
    print(f"  Services: {len(smap)}, Routers: {len(rmap)}")
    cmap = _parse_layer_c()
    print(f"  Capabilities: {len(cmap)}")
    wmap = _parse_layer_d()
    print(f"  Workspaces: {len(wmap)}")
    result = _build(emap, smap, rmap, cmap, wmap)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"  Wrote {OUTPUT_PATH}")
    print(f"  Entries: {len(result)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())