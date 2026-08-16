# Program 1 Runtime Architecture

FinancialGraphRuntime

↓

CommandCenterRuntime

↓

WorkspaceRuntime

↓

LayoutRuntime

↓

NavigationRuntime

↓

ContextRuntime

↓

SelectionRuntime

↓

Workspace

↓

Panels

↓

Components

---

Rules

Workspace owns data.

Command Center owns orchestration.

Graph owns relationships.

Layouts own positioning.

Navigation owns movement.

Context owns inspection.

Selection owns focus.

Components never own business logic.

Every interaction flows through runtime.

No runtime bypasses another runtime.

No duplicated state.

No duplicated navigation.

No duplicated selection.

Backend remains source of truth.
