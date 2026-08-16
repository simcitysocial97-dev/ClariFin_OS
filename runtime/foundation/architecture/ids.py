"""Canonical architecture ID scheme — Program 13.2.

Every runtime subsystem MUST address architectural entities through these IDs.
No subsystem may invent its own identifier format, and no ID may be derived
from a filename heuristic (``*.py`` -> engine) or a path guess.

The scheme is the one already used by the constitutional artifacts produced by
Program 13.1 (``ownership-graph.json`` / ``execution-graph.json``):

    engine:<engine_name>                       Engine (package root or single file)
    engine:<engine_name>:entry                 Engine public entry point
    module:<repo/relative/path.py>             Implementation module (Engine Module)
    detector:<repo/relative/path.py>           Detector (specialised Engine Module)
    facade:<repo/relative/path.py>             Facade / parked engine
    capability:<useXCapability>                Frontend capability hook
    router:<repo/relative/path.py>             HTTP router
    endpoint:<METHOD /path>                    HTTP endpoint
    service:<repo/relative/path.py>            Application service
    repository:<name_repository>               Persistence repository
    workspace:<WorkspaceName>                  Frontend workspace
    component:<ComponentName>                  Frontend component
    mapper:<name>                              Mapper (backend module path or FE symbol)
    dto:<repo/relative/path.py>                DTO
    viewmodel:<Name>                           ViewModel
    artifact:<repo/relative/path>              Generated artifact
    test:<repo/relative/path>                  Test module
    database:<name>                            Datastore
"""

from __future__ import annotations

ENGINE = "engine"
ENGINE_ENTRY_SUFFIX = "entry"
MODULE = "module"
DETECTOR = "detector"
FACADE = "facade"
CAPABILITY = "capability"
ROUTER = "router"
ENDPOINT = "endpoint"
SERVICE = "service"
REPOSITORY = "repository"
WORKSPACE = "workspace"
COMPONENT = "component"
MAPPER = "mapper"
DTO = "dto"
VIEWMODEL = "viewmodel"
ARTIFACT = "artifact"
TEST = "test"
DATABASE = "database"

#: Every legal ID prefix. Used by the consistency audit.
PREFIXES: frozenset[str] = frozenset(
    {
        ENGINE,
        MODULE,
        DETECTOR,
        FACADE,
        CAPABILITY,
        ROUTER,
        ENDPOINT,
        SERVICE,
        REPOSITORY,
        WORKSPACE,
        COMPONENT,
        MAPPER,
        DTO,
        VIEWMODEL,
        ARTIFACT,
        TEST,
        DATABASE,
    }
)


def engine_id(name: str) -> str:
    """Canonical Engine ID. ``name`` is the engine name, never a file path."""
    return f"{ENGINE}:{name}"


def engine_entry_id(name: str) -> str:
    return f"{ENGINE}:{name}:{ENGINE_ENTRY_SUFFIX}"


def module_id(path: str) -> str:
    return f"{MODULE}:{path}"


def detector_id(path: str) -> str:
    return f"{DETECTOR}:{path}"


def facade_id(path: str) -> str:
    return f"{FACADE}:{path}"


def capability_id(hook: str) -> str:
    return f"{CAPABILITY}:{hook}"


def router_id(path: str) -> str:
    return f"{ROUTER}:{path}"


def endpoint_id(signature: str) -> str:
    return f"{ENDPOINT}:{signature}"


def service_id(path: str) -> str:
    return f"{SERVICE}:{path}"


def repository_id(name: str) -> str:
    return f"{REPOSITORY}:{name}"


def workspace_id(name: str) -> str:
    return f"{WORKSPACE}:{name}"


def component_id(name: str) -> str:
    return f"{COMPONENT}:{name}"


def mapper_id(name: str) -> str:
    return f"{MAPPER}:{name}"


def dto_id(path: str) -> str:
    return f"{DTO}:{path}"


def viewmodel_id(name: str) -> str:
    return f"{VIEWMODEL}:{name}"


def artifact_id(path: str) -> str:
    return f"{ARTIFACT}:{path}"


def test_id(path: str) -> str:
    return f"{TEST}:{path}"


def database_id(name: str) -> str:
    return f"{DATABASE}:{name}"


def prefix_of(node_id: str) -> str:
    """Return the ID prefix (``engine``, ``module``, ...) of a canonical ID."""
    return node_id.split(":", 1)[0] if ":" in node_id else ""


def local_of(node_id: str) -> str:
    """Return the local part of a canonical ID (everything after the prefix)."""
    return node_id.split(":", 1)[1] if ":" in node_id else node_id


def is_canonical(node_id: str) -> bool:
    return prefix_of(node_id) in PREFIXES
