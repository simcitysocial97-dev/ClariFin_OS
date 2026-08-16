# Stage 4B Technical Specification

## Runtime Architecture

Backend

↓

DTO

↓

Mapper

↓

ViewModel

↓

Capability

↓

Workspace

↓

Graph Adapter

↓

Financial Runtime

↓

Money Graph Engine

---

## Graph Node

Every node contains

- id
- type
- label
- metadata
- evidence
- navigation
- metrics

---

## Graph Edge

Every edge contains

- id
- source
- target
- relationship
- evidence
- confidence

---

## Runtime Services

Graph Registry

Graph Builder

Traversal Engine

Selection Engine

Filtering Engine

Metrics Engine

Explainability Engine

Relationship Engine

---

## Public Runtime API

registerAdapter()

build()

nodes()

edges()

findNode()

findRelated()

traceMoney()

traceEvidence()

subgraph()

metrics()

events()

dispose()

---

## Adapter Contract

Each workspace exposes

toGraph()

returning

GraphResult

without changing existing runtime.

---

## Explainability Contract

Every node must expose

summary

evidence

calculation

confidence

source

No hidden calculations.

---

## Runtime Rules

No business logic.

No backend modification.

No financial calculations.

No duplicated nodes.

No duplicated edges.

Immutable graph state.

Workspace remains source of truth.
