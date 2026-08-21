"""The ONE canonical Architecture Provider — Program 13.2, Phase 2.

Every Engineering Runtime subsystem must obtain architectural facts from this
module. No subsystem may:

* rediscover architecture,
* assume ``*.py == Engine``,
* guess ownership from filenames, paths, or regexes,
* build its own engine/capability/router/endpoint registry.

The provider is a pure CONSUMER of the constitutional artifacts produced by the
single architecture discovery pipeline
(:mod:`runtime.foundation.architecture.discovery`):

    runtime/generated/architecture-inventory.json    (module classification)
    runtime/generated/engine-topology.json           (canonical engines)
    runtime/generated/ownership-graph.json           (who owns what)
    runtime/generated/execution-graph.json           (runtime call path)
    runtime/generated/engine-normalization.json      (migration status)
    runtime/generated/artifact-ownership-v2.json     (artifact ownership seed)
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.architecture import ids
from runtime.foundation.architecture.models import (
    Architecture,
    Artifact,
    Capability,
    Component,
    Detector,
    DTO,
    Endpoint,
    Engine,
    Facade,
    Graph,
    GraphEdge,
    GraphNode,
    ImplementationModule,
    Mapper,
    Repository,
    Router,
    Service,
    ViewModel,
    Workspace,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"

INVENTORY = "architecture-inventory.json"
TOPOLOGY = "engine-topology.json"
OWNERSHIP = "ownership-graph.json"
EXECUTION = "execution-graph.json"
NORMALIZATION = "engine-normalization.json"
ARTIFACTS_V2 = "artifact-ownership-v2.json"
ARTIFACTS_V3 = "artifact-ownership-v3.json"

CANONICAL_SOURCES = (
    INVENTORY,
    TOPOLOGY,
    OWNERSHIP,
    EXECUTION,
    NORMALIZATION,
    ARTIFACTS_V2,
)

PROVIDER_SNAPSHOT = "architecture-provider.json"


class ArchitectureNotDiscovered(RuntimeError):
    """Raised when the canonical artifacts are absent.

    Subsystems must NOT fall back to independent discovery; they must run the
    single discovery pipeline instead.
    """


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _load(generated_dir: Path, name: str) -> dict[str, Any]:
    path = generated_dir / name
    if not path.exists():
        raise ArchitectureNotDiscovered(
            f"Canonical architecture artifact missing: {path}. "
            "Run `python runtime/verify.py architecture discover` "
            "(the single architecture discovery pipeline)."
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover - defensive
        raise ArchitectureNotDiscovered(f"Cannot read {path}: {exc}") from exc


def _load_optional(generated_dir: Path, name: str) -> dict[str, Any]:
    path = generated_dir / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _split_endpoint(signature: str) -> tuple[str, str]:
    if " " in signature:
        method, path = signature.split(" ", 1)
        return method.strip(), path.strip()
    return "GET", signature


# ---------------------------------------------------------------------------
# provider
# ---------------------------------------------------------------------------


class ArchitectureProvider:
    """Single source of architectural truth for the Engineering Runtime."""

    _lock = threading.Lock()
    _instance: "ArchitectureProvider | None" = None

    def __init__(self, generated_dir: Path | None = None) -> None:
        self.generated_dir = generated_dir or GENERATED_DIR
        self._architecture: Architecture | None = None

    # -- singleton ------------------------------------------------------
    @classmethod
    def instance(cls, generated_dir: Path | None = None) -> "ArchitectureProvider":
        with cls._lock:
            if cls._instance is None or (
                generated_dir is not None
                and cls._instance.generated_dir != generated_dir
            ):
                cls._instance = cls(generated_dir)
            return cls._instance

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls._instance = None

    # -- loading --------------------------------------------------------
    def architecture(self, refresh: bool = False) -> Architecture:
        if self._architecture is None or refresh:
            self._architecture = self._build()
        return self._architecture

    def available(self) -> bool:
        return all((self.generated_dir / n).exists() for n in CANONICAL_SOURCES)

    def _build(self) -> Architecture:
        gen = self.generated_dir
        inventory = _load(gen, INVENTORY)
        topology = _load(gen, TOPOLOGY)
        ownership = _load(gen, OWNERSHIP)
        execution = _load(gen, EXECUTION)
        normalization = _load_optional(gen, NORMALIZATION)
        artifacts_raw = _load_optional(gen, ARTIFACTS_V3) or _load_optional(
            gen, ARTIFACTS_V2
        )

        modules_by_path: dict[str, dict[str, Any]] = {
            m["path"]: m for m in inventory.get("modules", [])
        }

        engines, engine_modules, detectors = self._build_engines(
            topology, normalization, modules_by_path, ownership, execution
        )
        facades = self._build_facades(topology, normalization, modules_by_path)
        routers, endpoints = self._build_http(execution, engines, modules_by_path)
        services = self._build_services(ownership, engines, routers, modules_by_path)
        repositories = self._build_repositories(ownership, engines, modules_by_path)
        capabilities, workspaces, components = self._build_frontend(
            inventory, ownership, execution, engines, modules_by_path
        )
        mappers, dtos, view_models = self._build_support(modules_by_path)
        artifacts = self._build_artifacts(artifacts_raw)

        # attach capability/endpoint back-references onto engines
        engines = self._link_engines(engines, capabilities, routers, endpoints)

        own_graph = self._graph_from_artifact(
            "ownership",
            ownership,
            "Ownership graph: who OWNS what. Never traverses implementation modules "
            "as roots; engines own their modules.",
        )
        exec_graph = self._graph_from_artifact(
            "execution",
            execution,
            "Execution graph: the runtime call path. May traverse implementation "
            "modules; ownership must not.",
        )
        dep_graph = self._build_dependency_graph(
            modules_by_path, engines, engine_modules, detectors
        )

        return Architecture(
            generated_at=datetime.now(timezone.utc).isoformat(),
            source_artifacts=CANONICAL_SOURCES,
            engines=engines,
            engine_modules=engine_modules,
            detectors=detectors,
            facades=facades,
            capabilities=capabilities,
            routers=routers,
            endpoints=endpoints,
            services=services,
            repositories=repositories,
            workspaces=workspaces,
            components=components,
            mappers=mappers,
            dtos=dtos,
            view_models=view_models,
            artifacts=artifacts,
            ownership=own_graph,
            execution=exec_graph,
            dependency=dep_graph,
        )

    # -- engines --------------------------------------------------------
    def _build_engines(
        self,
        topology: dict[str, Any],
        normalization: dict[str, Any],
        modules_by_path: dict[str, dict[str, Any]],
        ownership: dict[str, Any],
        execution: dict[str, Any],
    ) -> tuple[dict[str, Engine], dict[str, ImplementationModule], dict[str, Detector]]:
        engines: dict[str, Engine] = {}
        engine_modules: dict[str, ImplementationModule] = {}
        detectors: dict[str, Detector] = {}

        norm_engines = normalization.get("engines", {})

        for name, entry in topology.get("engines", {}).items():
            style = entry.get("canonical_style", "package")
            raw_entry_point = entry.get("public_entry_point", "")
            entry_point = (
                raw_entry_point
                if raw_entry_point.startswith("backend/")
                else f"backend/src/{raw_entry_point}"
            )
            if style == "package":
                engine_path = entry_point.removesuffix("/__init__.py")
            else:
                engine_path = entry_point

            impl_paths: list[str] = []
            detector_paths: list[str] = []
            for mod_path in entry.get("implementation_modules", []):
                inv = modules_by_path.get(mod_path, {})
                node_type = inv.get("node_type", "Engine Module")
                record_kwargs = dict(
                    path=mod_path,
                    engine=name,
                    classes=tuple(inv.get("classes", ())),
                    functions=tuple(inv.get("functions", ())),
                    docstring=inv.get("docstring", "") or "",
                )
                if node_type == "Detector":
                    detectors[mod_path] = Detector(
                        id=ids.detector_id(mod_path), **record_kwargs
                    )
                    detector_paths.append(mod_path)
                else:
                    engine_modules[mod_path] = ImplementationModule(
                        id=ids.module_id(mod_path), **record_kwargs
                    )
                impl_paths.append(mod_path)

            norm = norm_engines.get(name, {})
            engines[name] = Engine(
                id=ids.engine_id(name),
                name=name,
                style=style,
                path=engine_path,
                entry_point=entry_point,
                implementation_modules=tuple(sorted(impl_paths)),
                detectors=tuple(sorted(detector_paths)),
                services=tuple(sorted(entry.get("services", []))),
                routers=tuple(sorted(entry.get("routers", []))),
                repositories=tuple(sorted(entry.get("repositories", []))),
                endpoints=(),  # linked later from the execution graph
                capabilities=tuple(sorted(entry.get("capabilities", []))),
                tests=tuple(sorted(entry.get("tests", []))),
                artifacts=tuple(sorted(entry.get("artifacts", []))),
                migration_status=norm.get("migration_status", ""),
                internal=not entry.get("capabilities"),
                evidence=entry.get("evidence", {}),
            )
        return engines, engine_modules, detectors

    def _build_facades(
        self,
        topology: dict[str, Any],
        normalization: dict[str, Any],
        modules_by_path: dict[str, dict[str, Any]],
    ) -> dict[str, Facade]:
        facades: dict[str, Facade] = {}
        for name, entry in topology.get("parked_facades", {}).items():
            raw = entry.get("path", "")
            path = raw if raw.startswith("backend/") else f"backend/src/{raw}"
            facades[path] = Facade(
                id=ids.facade_id(path),
                path=path,
                status=entry.get("status", "PARKED"),
                replaces=entry.get("replaces"),
                import_references=entry.get("import_references", 0),
            )
        for name, entry in normalization.get("engines", {}).items():
            status = entry.get("migration_status", "")
            if status not in {"FACADE", "PARKED"}:
                continue
            path = entry.get("entry_point") or entry.get("path") or ""
            if not path:
                continue
            if not path.startswith("backend/"):
                path = f"backend/src/{path}"
            facades.setdefault(
                path,
                Facade(
                    id=ids.facade_id(path),
                    path=path,
                    status=status,
                    replaces=entry.get("replaces"),
                    import_references=entry.get("import_references", 0),
                ),
            )
        for path, mod in modules_by_path.items():
            if mod.get("node_type") == "Engine Facade":
                facades.setdefault(
                    path,
                    Facade(id=ids.facade_id(path), path=path, status="FACADE"),
                )
        return facades

    # -- HTTP layer -----------------------------------------------------
    def _build_http(
        self,
        execution: dict[str, Any],
        engines: dict[str, Engine],
        modules_by_path: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, Router], dict[str, Endpoint]]:
        endpoint_to_router: dict[str, str] = {}
        capability_of_endpoint: dict[str, set[str]] = {}
        for edge in execution.get("edges", []):
            src, dst = edge.get("from", ""), edge.get("to", "")
            if src.startswith("endpoint:") and dst.startswith("router:"):
                endpoint_to_router[ids.local_of(src)] = ids.local_of(dst)
            elif src.startswith("capability:") and dst.startswith("endpoint:"):
                capability_of_endpoint.setdefault(ids.local_of(dst), set()).add(
                    ids.local_of(src)
                )

        router_engines: dict[str, set[str]] = {}
        for eng in engines.values():
            for r in eng.routers:
                router_engines.setdefault(r, set()).add(eng.name)

        routers: dict[str, Router] = {}
        for router_path in sorted(
            set(endpoint_to_router.values()) | set(router_engines)
        ):
            routers[router_path] = Router(
                id=ids.router_id(router_path),
                path=router_path,
                endpoints=tuple(
                    sorted(
                        ep for ep, r in endpoint_to_router.items() if r == router_path
                    )
                ),
                engines=tuple(sorted(router_engines.get(router_path, ()))),
            )

        endpoints: dict[str, Endpoint] = {}
        for signature, router_path in sorted(endpoint_to_router.items()):
            method, path = _split_endpoint(signature)
            endpoints[signature] = Endpoint(
                id=ids.endpoint_id(signature),
                method=method,
                path=path,
                router=router_path,
                engines=tuple(sorted(router_engines.get(router_path, ()))),
                capabilities=tuple(sorted(capability_of_endpoint.get(signature, ()))),
            )
        return routers, endpoints

    def _build_services(
        self,
        ownership: dict[str, Any],
        engines: dict[str, Engine],
        routers: dict[str, Router],
        modules_by_path: dict[str, dict[str, Any]],
    ) -> dict[str, Service]:
        service_engines: dict[str, set[str]] = {}
        service_routers: dict[str, set[str]] = {}
        for edge in ownership.get("edges", []):
            src, dst = edge.get("from", ""), edge.get("to", "")
            if src.startswith("service:") and dst.startswith("engine:"):
                service_engines.setdefault(ids.local_of(src), set()).add(
                    ids.local_of(dst).split(":")[0]
                )
            elif src.startswith("router:") and dst.startswith("service:"):
                service_routers.setdefault(ids.local_of(dst), set()).add(
                    ids.local_of(src)
                )

        known = set(service_engines) | set(service_routers)
        for eng in engines.values():
            known.update(eng.services)
        for path, mod in modules_by_path.items():
            if mod.get("node_type") == "Service":
                known.add(path)

        services: dict[str, Service] = {}
        for path in sorted(known):
            services[path] = Service(
                id=ids.service_id(path),
                path=path,
                engines=tuple(sorted(service_engines.get(path, ()))),
                routers=tuple(sorted(service_routers.get(path, ()))),
            )
        return services

    def _build_repositories(
        self,
        ownership: dict[str, Any],
        engines: dict[str, Engine],
        modules_by_path: dict[str, dict[str, Any]],
    ) -> dict[str, Repository]:
        names: set[str] = set()
        for node in ownership.get("nodes", []):
            if node.get("id", "").startswith("repository:"):
                names.add(ids.local_of(node["id"]))
        for eng in engines.values():
            names.update(eng.repositories)

        repo_engines: dict[str, set[str]] = {}
        for eng in engines.values():
            for r in eng.repositories:
                repo_engines.setdefault(r, set()).add(eng.name)

        paths_by_name = {
            p.rsplit("/", 1)[-1].removesuffix(".py"): p
            for p, m in modules_by_path.items()
            if m.get("node_type") == "Repository"
        }
        repositories: dict[str, Repository] = {}
        for name in sorted(names):
            repositories[name] = Repository(
                id=ids.repository_id(name),
                name=name,
                path=paths_by_name.get(name, ""),
                engines=tuple(sorted(repo_engines.get(name, ()))),
            )
        return repositories

    # -- frontend -------------------------------------------------------
    def _build_frontend(
        self,
        inventory: dict[str, Any],
        ownership: dict[str, Any],
        execution: dict[str, Any],
        engines: dict[str, Engine],
        modules_by_path: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, Capability], dict[str, Workspace], dict[str, Component]]:
        # capability hook name comes from the DECLARED symbol, not the filename
        cap_paths: dict[str, str] = {}
        for path, mod in modules_by_path.items():
            if mod.get("node_type") != "Capability":
                continue
            for symbol in mod.get("classes", []):
                if symbol.startswith("use") and symbol.endswith("Capability"):
                    cap_paths[symbol] = path

        # Aliases: older artifacts spell hooks with different casing
        # (useNetworthCapability vs the declared useNetWorthCapability).
        # The DECLARED symbol always wins; aliases are folded into it.
        canonical_by_key = {sym.lower(): sym for sym in cap_paths}

        def canon_cap(name: str) -> str:
            return canonical_by_key.get(name.lower(), name)

        cap_engines: dict[str, set[str]] = {}
        for edge in ownership.get("edges", []):
            src, dst = edge.get("from", ""), edge.get("to", "")
            if src.startswith("capability:") and dst.startswith("engine:"):
                cap_engines.setdefault(canon_cap(ids.local_of(src)), set()).add(
                    ids.local_of(dst)
                )
        for eng in engines.values():
            for cap in eng.capabilities:
                cap_engines.setdefault(canon_cap(cap), set()).add(eng.name)

        cap_endpoints: dict[str, set[str]] = {}
        for edge in execution.get("edges", []):
            src, dst = edge.get("from", ""), edge.get("to", "")
            if src.startswith("capability:") and dst.startswith("endpoint:"):
                cap_endpoints.setdefault(canon_cap(ids.local_of(src)), set()).add(
                    ids.local_of(dst)
                )

        for tree_cap in ownership.get("ownership_trees_by_capability", {}):
            cap_engines.setdefault(canon_cap(tree_cap), set())

        # workspaces: frontend workspace-page modules, linked by import evidence
        workspaces: dict[str, Workspace] = {}
        components: dict[str, Component] = {}
        cap_workspaces: dict[str, set[str]] = {}

        component_paths: dict[str, str] = {}
        for path, mod in modules_by_path.items():
            if "/components/" in path and mod.get("language") == "typescript":
                component_paths[path] = path

        for path, mod in modules_by_path.items():
            if mod.get("node_type") != "Workspace":
                continue
            if not path.endswith("workspace-page.tsx"):
                continue
            ws_name = path.split("/")[2] if path.count("/") >= 2 else path
            imports = mod.get("imports", [])
            ws_caps: set[str] = set()
            ws_components: set[str] = set()
            for imp in imports:
                for cap_name, cap_path in cap_paths.items():
                    stem = cap_path.removeprefix("frontend/").removesuffix(".ts")
                    if imp.endswith(stem) or imp.endswith(stem.removeprefix("lib/")):
                        ws_caps.add(canon_cap(cap_name))
                if imp.startswith("@/components/") or imp.startswith("components/"):
                    comp_rel = imp.removeprefix("@/")
                    ws_components.add(comp_rel)
            workspaces[ws_name] = Workspace(
                id=ids.workspace_id(ws_name),
                name=ws_name,
                path=path,
                capabilities=tuple(sorted(ws_caps)),
                components=tuple(sorted(ws_components)),
            )
            for cap in ws_caps:
                cap_workspaces.setdefault(cap, set()).add(ws_name)
            for comp in ws_components:
                existing = components.get(comp)
                owners = set(existing.workspaces) if existing else set()
                owners.add(ws_name)
                components[comp] = Component(
                    id=ids.component_id(comp),
                    name=comp.rsplit("/", 1)[-1],
                    path=f"frontend/{comp}.tsx",
                    workspaces=tuple(sorted(owners)),
                )

        capabilities: dict[str, Capability] = {}
        for cap_name in sorted(set(cap_paths) | set(cap_engines)):
            capabilities[cap_name] = Capability(
                id=ids.capability_id(cap_name),
                name=cap_name,
                path=cap_paths.get(cap_name, ""),
                engines=tuple(sorted(cap_engines.get(cap_name, ()))),
                endpoints=tuple(sorted(cap_endpoints.get(cap_name, ()))),
                workspaces=tuple(sorted(cap_workspaces.get(cap_name, ()))),
            )
        return capabilities, workspaces, components

    def _build_support(
        self, modules_by_path: dict[str, dict[str, Any]]
    ) -> tuple[dict[str, Mapper], dict[str, DTO], dict[str, ViewModel]]:
        mappers: dict[str, Mapper] = {}
        dtos: dict[str, DTO] = {}
        view_models: dict[str, ViewModel] = {}
        for path, mod in modules_by_path.items():
            node_type = mod.get("node_type")
            name = path.rsplit("/", 1)[-1].removesuffix(".py").removesuffix(".ts")
            if node_type == "Mapper":
                mappers[path] = Mapper(
                    id=ids.mapper_id(path),
                    name=name,
                    path=path,
                    layer="frontend" if path.startswith("frontend/") else "backend",
                )
            elif node_type == "DTO":
                dtos[path] = DTO(id=ids.dto_id(path), name=name, path=path)
            elif node_type == "ViewModel":
                view_models[path] = ViewModel(
                    id=ids.viewmodel_id(name), name=name, path=path
                )
            for symbol in mod.get("classes", []):
                if symbol.endswith("ViewModel") and symbol not in view_models:
                    view_models[symbol] = ViewModel(
                        id=ids.viewmodel_id(symbol), name=symbol, path=path
                    )
        return mappers, dtos, view_models

    def _build_artifacts(self, raw: dict[str, Any]) -> dict[str, Artifact]:
        artifacts: dict[str, Artifact] = {}
        for entry in raw.get("artifacts", []):
            path = entry.get("artifact") or entry.get("path", "")
            if not path:
                continue
            artifacts[path] = Artifact(
                id=ids.artifact_id(path),
                path=path,
                producer=entry.get("producer", ""),
                owner=entry.get("owner", ""),
                consumers=tuple(entry.get("consumers", ())),
                verification_stage=entry.get("verification_stage", ""),
                pipeline=entry.get("pipeline", ""),
                lifecycle=entry.get("lifecycle", ""),
                retention=entry.get("retention", ""),
                regeneration_source=entry.get("regeneration_source", ""),
                engine=entry.get("engine"),
                capability=entry.get("capability"),
                unknown_ownership=bool(entry.get("unknown_ownership", False)),
            )
        return artifacts

    # -- linking --------------------------------------------------------
    def _link_engines(
        self,
        engines: dict[str, Engine],
        capabilities: dict[str, Capability],
        routers: dict[str, Router],
        endpoints: dict[str, Endpoint],
    ) -> dict[str, Engine]:
        linked: dict[str, Engine] = {}
        for name, eng in engines.items():
            eng_endpoints: set[str] = set()
            for router_path in eng.routers:
                router = routers.get(router_path)
                if router:
                    eng_endpoints.update(router.endpoints)
            eng_caps = {c.name for c in capabilities.values() if name in c.engines}
            eng_caps.update(eng.capabilities)
            linked[name] = Engine(
                id=eng.id,
                name=eng.name,
                style=eng.style,
                path=eng.path,
                entry_point=eng.entry_point,
                implementation_modules=eng.implementation_modules,
                detectors=eng.detectors,
                services=eng.services,
                routers=eng.routers,
                repositories=eng.repositories,
                endpoints=tuple(sorted(eng_endpoints)),
                capabilities=tuple(sorted(eng_caps)),
                tests=eng.tests,
                artifacts=eng.artifacts,
                migration_status=eng.migration_status,
                internal=not eng_caps,
                evidence=eng.evidence,
            )
        return linked

    # -- graphs ---------------------------------------------------------
    def _graph_from_artifact(
        self, kind: str, data: dict[str, Any], description: str
    ) -> Graph:
        nodes = tuple(
            GraphNode(id=n["id"], type=n.get("type", ""), label=n.get("label", n["id"]))
            for n in data.get("nodes", [])
        )
        edges = tuple(
            GraphEdge(
                source=e.get("from", ""),
                target=e.get("to", ""),
                relation=e.get("relation", ""),
                evidence=e.get("evidence", ""),
                attributes={
                    k: v
                    for k, v in e.items()
                    if k not in {"from", "to", "relation", "evidence"}
                },
            )
            for e in data.get("edges", [])
        )
        return Graph(kind=kind, description=description, nodes=nodes, edges=edges)

    def _build_dependency_graph(
        self,
        modules_by_path: dict[str, dict[str, Any]],
        engines: dict[str, Engine],
        engine_modules: dict[str, ImplementationModule],
        detectors: dict[str, Detector],
    ) -> Graph:
        """Static import dependency graph.

        Distinct from ownership (who owns what) and execution (runtime call
        path). Edges are ``depends_on`` and come exclusively from recorded
        import statements resolved against the architecture inventory.
        """
        resolver = _ImportResolver(modules_by_path)
        module_owner: dict[str, str] = {}
        for path, mod in engine_modules.items():
            module_owner[path] = ids.engine_id(mod.engine)
        for path, det in detectors.items():
            module_owner[path] = ids.engine_id(det.engine)
        for eng in engines.values():
            module_owner[eng.entry_point] = eng.id
            if eng.style == "single_file":
                module_owner[eng.path] = eng.id

        node_ids: dict[str, GraphNode] = {}
        edge_map: dict[tuple[str, str], GraphEdge] = {}

        def node_for(path: str) -> GraphNode | None:
            owner = module_owner.get(path)
            if owner:
                name = ids.local_of(owner)
                return GraphNode(id=owner, type="Engine", label=name)
            mod = modules_by_path.get(path)
            if mod is None:
                return None
            node_type = mod.get("node_type", "Utility")
            mapping = {
                "Service": (ids.service_id, "Service"),
                "Router": (ids.router_id, "Router"),
                "Repository": (ids.repository_id, "Repository"),
                "Mapper": (ids.mapper_id, "Mapper"),
                "DTO": (ids.dto_id, "DTO"),
                "Capability": (ids.capability_id, "Capability"),
                "Workspace": (ids.workspace_id, "Workspace"),
            }
            if node_type == "Repository":
                name = path.rsplit("/", 1)[-1].removesuffix(".py")
                return GraphNode(
                    id=ids.repository_id(name), type="Repository", label=name
                )
            if node_type in mapping:
                fn, label_type = mapping[node_type]
                return GraphNode(id=fn(path), type=label_type, label=path)
            return None

        for path, mod in modules_by_path.items():
            source_node = node_for(path)
            if source_node is None:
                continue
            for imp in mod.get("imports", []):
                target_path = resolver.resolve(imp, path)
                if not target_path or target_path == path:
                    continue
                target_node = node_for(target_path)
                if target_node is None or target_node.id == source_node.id:
                    continue
                node_ids.setdefault(source_node.id, source_node)
                node_ids.setdefault(target_node.id, target_node)
                key = (source_node.id, target_node.id)
                if key not in edge_map:
                    edge_map[key] = GraphEdge(
                        source=source_node.id,
                        target=target_node.id,
                        relation="depends_on",
                        evidence=f"{path} imports {imp} -> {target_path}",
                        attributes={"kind": "static_import"},
                    )

        return Graph(
            kind="dependency",
            description=(
                "Dependency graph: static import dependencies between canonical "
                "architecture nodes. Distinct from ownership and execution."
            ),
            nodes=tuple(sorted(node_ids.values(), key=lambda n: n.id)),
            edges=tuple(sorted(edge_map.values(), key=lambda e: (e.source, e.target))),
        )


class _ImportResolver:
    """Resolves recorded import strings to inventory module paths."""

    def __init__(self, modules_by_path: dict[str, dict[str, Any]]) -> None:
        self._paths = set(modules_by_path)

    def resolve(self, imp: str, importer: str) -> str | None:
        if importer.startswith("backend/"):
            return self._resolve_python(imp, importer)
        if importer.startswith("frontend/"):
            return self._resolve_ts(imp)
        return None

    def _candidates(self, dotted: str, prefix: str) -> list[str]:
        parts = dotted.split(".")
        out: list[str] = []
        for cut in range(len(parts), 0, -1):
            base = "/".join(parts[:cut])
            out.append(f"{prefix}/{base}.py")
            out.append(f"{prefix}/{base}/__init__.py")
        return out

    def _resolve_python(self, imp: str, importer: str) -> str | None:
        if imp.startswith("src."):
            for cand in self._candidates(imp.removeprefix("src."), "backend/src"):
                if cand in self._paths:
                    return cand
            return None
        # intra-package relative import recorded without the package prefix
        pkg_dir = importer.rsplit("/", 1)[0]
        for cand in self._candidates(imp, pkg_dir):
            if cand in self._paths:
                return cand
        return None

    def _resolve_ts(self, imp: str) -> str | None:
        if imp.startswith("@/"):
            base = f"frontend/{imp.removeprefix('@/')}"
        elif imp.startswith("frontend/"):
            base = imp
        else:
            return None
        for ext in (".ts", ".tsx", "/index.ts", "/index.tsx"):
            cand = f"{base}{ext}"
            if cand in self._paths:
                return cand
        return base if base in self._paths else None


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------


def get_provider(generated_dir: Path | None = None) -> ArchitectureProvider:
    return ArchitectureProvider.instance(generated_dir)


def get_architecture(
    refresh: bool = False, generated_dir: Path | None = None
) -> Architecture:
    """Return the canonical architecture. THE entry point for all subsystems."""
    return get_provider(generated_dir).architecture(refresh=refresh)


def architecture_available(generated_dir: Path | None = None) -> bool:
    return get_provider(generated_dir).available()


def export_snapshot(output_path: Path | None = None) -> Path:
    """Write ``architecture-provider.json`` — the provider's resolved view."""
    arch = get_architecture(refresh=True)
    target = output_path or (GENERATED_DIR / PROVIDER_SNAPSHOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": arch.generated_at,
        "schema": "architecture-provider-v1",
        "principle": (
            "An Engine is an architectural UNIT (package root or designated "
            "single file). Implementation modules, detectors and facades are "
            "children, never engines. '*.py == Engine' is forbidden."
        ),
        "single_discovery_pipeline": "runtime.foundation.architecture.discovery",
        "source_artifacts": [f"runtime/generated/{n}" for n in arch.source_artifacts],
        "counts": arch.counts(),
        "id_scheme": sorted(ids.PREFIXES),
        "engines": {name: eng.to_dict() for name, eng in sorted(arch.engines.items())},
        "engine_modules": {
            path: mod.to_dict() for path, mod in sorted(arch.engine_modules.items())
        },
        "detectors": {
            path: det.to_dict() for path, det in sorted(arch.detectors.items())
        },
        "facades": {path: f.to_dict() for path, f in sorted(arch.facades.items())},
        "capabilities": {n: c.to_dict() for n, c in sorted(arch.capabilities.items())},
        "routers": {p: r.to_dict() for p, r in sorted(arch.routers.items())},
        "endpoints": {s: e.to_dict() for s, e in sorted(arch.endpoints.items())},
        "services": {p: s.to_dict() for p, s in sorted(arch.services.items())},
        "repositories": {n: r.to_dict() for n, r in sorted(arch.repositories.items())},
        "workspaces": {n: w.to_dict() for n, w in sorted(arch.workspaces.items())},
        "components": {n: c.to_dict() for n, c in sorted(arch.components.items())},
        "mappers": {p: m.to_dict() for p, m in sorted(arch.mappers.items())},
        "dtos": {p: d.to_dict() for p, d in sorted(arch.dtos.items())},
        "view_models": {n: v.to_dict() for n, v in sorted(arch.view_models.items())},
        "artifact_count": len(arch.artifacts),
        "graphs": {
            "ownership": {
                "node_count": len(arch.ownership.nodes),
                "edge_count": len(arch.ownership.edges),
                "description": arch.ownership.description,
            },
            "execution": {
                "node_count": len(arch.execution.nodes),
                "edge_count": len(arch.execution.edges),
                "description": arch.execution.description,
            },
            "dependency": {
                "node_count": len(arch.dependency.nodes),
                "edge_count": len(arch.dependency.edges),
                "description": arch.dependency.description,
            },
        },
    }
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    return target
