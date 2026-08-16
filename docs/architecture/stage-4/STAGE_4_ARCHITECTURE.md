# Stage 4 Architecture

Every workspace follows exactly the same runtime.

Backend

↓

API

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

Components

Every workspace contains:

Mapper

ViewModel

Capability

Toolbar

Filters

Search

Evidence Drawer

Loading

Empty

Error

No workspace may bypass this architecture.

No component consumes DTO.

No component performs financial calculations.

Capability orchestrates everything.

Backend remains the only financial source of truth.
