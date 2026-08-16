"""Canonical Architecture subsystem — Program 13.2.

This package is the ONLY place in the Engineering Runtime allowed to define
what an Engine, Engine Module, Facade, Detector, Capability, Router, Endpoint,
Service, Repository, Workspace, Component, Mapper, DTO, ViewModel or Artifact
is.

Consumers import :func:`get_architecture` and read; they never rediscover.
"""

from __future__ import annotations

from runtime.foundation.architecture.models import (  # noqa: F401
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
from runtime.foundation.architecture.provider import (  # noqa: F401
    ArchitectureNotDiscovered,
    ArchitectureProvider,
    architecture_available,
    export_snapshot,
    get_architecture,
    get_provider,
)

__all__ = [
    "Architecture",
    "ArchitectureNotDiscovered",
    "ArchitectureProvider",
    "Artifact",
    "Capability",
    "Component",
    "DTO",
    "Detector",
    "Endpoint",
    "Engine",
    "Facade",
    "Graph",
    "GraphEdge",
    "GraphNode",
    "ImplementationModule",
    "Mapper",
    "Repository",
    "Router",
    "Service",
    "ViewModel",
    "Workspace",
    "architecture_available",
    "export_snapshot",
    "get_architecture",
    "get_provider",
]
