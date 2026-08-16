# Financial OS Shell — Permanent Composition Architecture

> **Status:** ARCHITECTURE FREEZE
> **Version:** 1.0.0
> **Date:** 2026-03-08
> **Scope:** All future frontend development for ClariFin_OS
> **Stability:** This document is the permanent specification. It must remain stable throughout the lifetime of the project.

---

## Table of Contents

1. [Financial OS Shell](#1-financial-os-shell)
2. [Workspace Host](#2-workspace-host)
3. [Context Runtime Expansion](#3-context-runtime-expansion)
4. [Intelligence Layer](#4-intelligence-layer)
5. [Graph Runtime Integration](#5-graph-runtime-integration)
6. [Command Runtime](#6-command-runtime)
7. [Renderer Architecture](#7-renderer-architecture)
8. [Design System](#8-design-system)
9. [Runtime Event Bus](#9-runtime-event-bus)
10. [Future Runtime Roadmap](#10-future-runtime-roadmap)
11. [Anti-Patterns](#11-anti-patterns)
12. [Implementation Sequencing](#12-implementation-sequencing)
13. [Execution Rules (AI Operating Manual)](#13-execution-rules)
14. [Never Skip](#14-never-skip)
15. [Startup Validation](#15-startup-validation)
16. [End-of-Run Validation](#16-end-of-run-validation)
17. [Milestone State Machine](#17-milestone-state-machine)
18. [Milestone Template](#18-milestone-template)
19. [Rollback Support](#19-rollback-support)

---

## Preamble: Frozen Platform Foundation

The following platform systems are **complete, immutable, and treated as permanent APIs**. This specification builds on top of them. It does not redesign them.

| Frozen System | Role |
|---------------|------|
| Capability → Mapper → ViewModel | Canonical data-flow pipeline from backend to UI |
| RuntimeProvider | React context provider that injects all runtimes |
| Workspace Runtime | Source of truth for workspace registration, activation, lifecycle |
| Timeline Runtime | Source of truth for temporal context (date ranges, playback, periods) |
| Navigation Runtime | Source of truth for navigation history, breadcrumbs, undo/redo |
| Selection Runtime | Source of truth for selected entities, ranges, and multi-select state |
| Workspace Registration | Declarative registry of all workspace definitions |
| Canonical Endpoint Contracts | Backend API contracts (OpenAPI/schema-validated) |
| Canonical Monetary Conventions | Paise-based integers (₹1.00 = 100 paise), no loose floats |
| Application Routing | Next.js App Router structural routing |

### Canonical Data Flow (Immutable)

```
Backend
  ↓
Capability
  ↓
Mapper
  ↓
ViewModel
  ↓
Workspace
  ↓
Renderer
```

**Never bypass this pipeline.** No shell region, no workspace, no renderer, no intelligence module may skip a stage or inject raw DTOs directly into the UI.

---

## 1. Financial OS Shell

### 1.1 Shell Overview

The Financial OS Shell is the **permanent application container**. It is a pure composition layer — it owns no business logic, performs no financial calculations, and makes no API calls. Its sole responsibility is to compose runtime-backed regions into a cohesive operating-system-grade experience.

The shell implements a **Hybrid Matrix Architecture**:

| Axis | Role | Character |
|------|------|-----------|
| Workspaces | Primary surface | Where the user works |
| Timeline | Temporal context | When the user is looking |
| Graph Runtime | Investigative engine | How entities relate |
| Command Center | Control plane | What the user wants to do |
| Intelligence | Augmentation | What the system suggests |

No single axis dominates. The shell balances them as a matrix.

### 1.2 Shell Composition

```
┌──────────────────────────────────────────────────────────────────┐
│                      Global Header (48px)                         │
├──────────┬──────────────────────────────────┬─────────────────────┤
│          │         Command HUD (44px)       │                     │
│          ├──────────────────────────────────┤                     │
│  Left    │                                  │    Right Context    │
│  Nav     │       Workspace Host             │      Panel          │
│  Rail     │                                  │   (280–420px)       │
│ (180px)  │                                  │                     │
│          │                                  │                     │
│          ├──────────────────────────────────┤                     │
│          │    Bottom Intelligence Shelf      │                     │
│          │         (88px expanded)            │                     │
├──────────┴──────────────────────────────────┴─────────────────────┤
│                      Status Bar (24px)                           │
└──────────────────────────────────────────────────────────────────┘
         Overlay Layer (z-index: 1000+)
         Modal Layer (z-index: 2000+)
```

### 1.3 Shell Regions

Each region below is specified with: **ownership, runtime dependencies, responsibilities, lifecycle, resize behavior, responsive rules.**

---

#### 1.3.1 Global Header

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) |
| **Runtime Dependencies** | NavigationRuntime (breadcrumbs), WorkspaceRuntime (active workspace title), TimelineRuntime (active period label) |
| **Responsibilities** | Display application identity, active workspace name, active household name, current timeline period, global status indicators (sync state, connection state) |
| **Lifecycle** | Persistent across all workspace switches. Never unmounts during a session. Updates reactively from runtime state. |
| **Resize Behavior** | Fixed height (48px). Width fills viewport. Contents reflow: on narrow widths, household name truncates first, then period label, then workspace name. |
| **Responsive Rules** | Desktop (≥1280px): Full display. Tablet (768–1279px): Hide household name, show workspace + period. Mobile (<768px): Show workspace name only, collapse rest into Command HUD. |

**Interface Contract:**

```typescript
interface GlobalHeaderProps {
  // All derived from runtimes — no direct props from parent
  // Shell reads from RuntimeProvider context
}
```

---

#### 1.3.2 Command HUD

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) |
| **Runtime Dependencies** | CommandRuntime (future — command input, recent commands), NavigationRuntime (breadcrumbs), WorkspaceRuntime (active workspace actions) |
| **Responsibilities** | Provide always-visible command input, display breadcrumb trail, expose quick actions for active workspace, show keyboard shortcut hints |
| **Lifecycle** | Persistent. Command input state managed by CommandRuntime. Breadcrumb trail updates from NavigationRuntime. |
| **Resize Behavior** | Fixed height (44px). Width fills workspace area. Breadcrumb trail truncates from the left (oldest entries collapse to …). |
| **Responsive Rules** | Desktop: Full breadcrumb + command input + quick actions. Tablet: Breadcrumb truncates to 2 levels, quick actions collapse to icon-only. Mobile: Breadcrumb hidden, command input becomes full-width, quick actions in overflow menu. |

**Interface Contract:**

```typescript
interface CommandHUDProps {
  // Derived from CommandRuntime + NavigationRuntime
  // No direct business props
}

interface BreadcrumbEntry {
  label: string;
  workspaceId?: string;
  route?: string;
  timestamp: number;
}
```

---

#### 1.3.3 Left Navigation Rail

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) |
| **Runtime Dependencies** | NavigationRuntime (active route, navigation history), WorkspaceRuntime (registered workspaces) |
| **Responsibilities** | Display all registered workspaces as navigation entries, indicate active workspace, support collapse/expand, show workspace icons + labels, provide quick-switch via keyboard |
| **Lifecycle** | Persistent. Workspace list derived from WorkspaceRegistration (static at build time). Active state from NavigationRuntime. Collapse state persisted in StateRuntime. |
| **Resize Behavior** | Width: 180px expanded, 56px collapsed. User-controlled collapse toggle. Persisted across sessions. |
| **Responsive Rules** | Desktop: Full rail (180px). Tablet: Collapsed by default (56px, icon-only). Mobile: Hidden by default, slides in as overlay drawer on command or hamburger tap. |

**Interface Contract:**

```typescript
interface LeftNavRailProps {
  // Derived from WorkspaceRuntime + NavigationRuntime
}

interface NavRailEntry {
  workspaceId: string;
  label: string;
  icon: string; // semantic icon identifier
  route: string;
  badge?: string; // optional count/notification badge
  order: number;
}
```

---

#### 1.3.4 Workspace Host

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) — delegates to WorkspaceRuntime |
| **Runtime Dependencies** | WorkspaceRuntime (active workspace, lifecycle), TimelineRuntime (active period for workspace), SelectionRuntime (active selection context) |
| **Responsibilities** | Mount/unmount active workspace, manage workspace caching, provide workspace-scoped context, handle workspace transitions |
| **Lifecycle** | Mounts when workspace activated. Unmounts when workspace deactivated (unless cached). See [Part 2](#2-workspace-host) for full lifecycle. |
| **Resize Behavior** | Fills remaining space between Left Rail and Right Panel. Min-width: 320px. |
| **Responsive Rules** | Desktop: Full workspace area. Tablet: Right Panel collapses to drawer, workspace fills width. Mobile: Full-width, panels become stacked drawers. |

> **Full specification in [Part 2 — Workspace Host](#2-workspace-host).**

---

#### 1.3.5 Right Context Panel

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) — content driven by SelectionRuntime + Intelligence Runtime (future) |
| **Runtime Dependencies** | SelectionRuntime (selected entity), WorkspaceRuntime (active workspace context), Intelligence Runtime (future — contextual insights) |
| **Responsibilities** | Display inspector for selected entity, show contextual intelligence, provide detail drill-down, render entity relationships, display evidence trail |
| **Lifecycle** | Persistent. Content swaps based on SelectionRuntime state. When no selection, shows workspace default context (overview, recent activity). |
| **Resize Behavior** | Width: 280px min, 420px max. User-resizable within range. Persisted. Can be collapsed to 0 (hidden). |
| **Responsive Rules** | Desktop: Visible (280–420px). Tablet: Collapsed by default, opens as drawer on selection. Mobile: Always drawer, slides from right. |

**Interface Contract:**

```typescript
interface RightContextPanelProps {
  // Derived from SelectionRuntime + Intelligence Runtime
}

interface ContextPanelContent {
  type: 'inspector' | 'intelligence' | 'relationships' | 'evidence' | 'empty';
  entityId?: string;
  entityType?: string;
  workspaceId?: string;
}
```

---

#### 1.3.6 Bottom Intelligence Shelf

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) — content driven by Intelligence Runtime (future) + TimelineRuntime |
| **Runtime Dependencies** | Intelligence Runtime (future — insights, alerts), TimelineRuntime (temporal context for insights), SelectionRuntime (selection-scoped insights) |
| **Responsibilities** | Display passive intelligence insights, show timeline scrubber, provide temporal navigation, surface anomalies and patterns, show forecast summaries |
| **Lifecycle** | Persistent. Collapsed state shows timeline scrubber only (88px). Expanded state shows intelligence cards (up to 240px). |
| **Resize Behavior** | Height: 88px collapsed, up to 240px expanded. User-controlled expand toggle. Persisted. |
| **Responsive Rules** | Desktop: Visible (88px collapsed). Tablet: Timeline only, intelligence hidden. Mobile: Hidden by default, accessible via Command HUD toggle. |

**Interface Contract:**

```typescript
interface BottomIntelligenceShelfProps {
  // Derived from Intelligence Runtime + TimelineRuntime
}

interface IntelligenceCard {
  id: string;
  type: 'passive' | 'investigative' | 'executive';
  title: string;
  summary: string;
  severity: 'info' | 'warning' | 'critical' | 'positive';
  actionLabel?: string;
  actionRoute?: string;
}
```

---

#### 1.3.7 Overlay Layer

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) |
| **Runtime Dependencies** | Graph Runtime (future — graph overlay), CommandRuntime (future — command palette overlay), Intelligence Runtime (future — insight detail overlay) |
| **Responsibilities** | Render non-modal overlays: command palette, graph exploration surface, insight detail panels, search results dropdown, notification toasts |
| **Lifecycle** | On-demand. Mounts when an overlay is requested, unmounts when dismissed. Multiple overlays can stack (z-index ordered). |
| **Resize Behavior** | Varies by overlay type. Command palette: centered, 640px max-width. Graph overlay: full workspace area. Insight panel: right-aligned, 420px. |
| **Responsive Rules** | Desktop: As specified. Tablet/Mobile: Full-width overlays, stacked vertically. |

**Interface Contract:**

```typescript
interface OverlayLayerProps {
  // Managed by individual runtimes requesting overlays
}

type OverlayType =
  | 'command-palette'
  | 'graph-exploration'
  | 'insight-detail'
  | 'search-results'
  | 'notification-toast';

interface OverlayRequest {
  id: string;
  type: OverlayType;
  priority: number; // higher = on top
  dismissible: boolean;
}
```

---

#### 1.3.8 Modal Layer

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) |
| **Runtime Dependencies** | WorkspaceRuntime (workspace-scoped modals), NavigationRuntime (navigation confirmations), Intelligence Runtime (future — confirmation dialogs) |
| **Responsibilities** | Render modal dialogs: confirmations, create/edit forms, import wizards, scenario configuration, reconciliation resolution |
| **Lifecycle** | On-demand. Mounts when a modal is requested. Blocks interaction with underlying shell. Only one modal active at a time (stacking forbidden — use sequential flows instead). |
| **Resize Behavior** | Centered. Max-width: 640px (standard), 960px (wide). Max-height: 80vh with internal scroll. |
| **Responsive Rules** | Desktop: Centered modal. Tablet/Mobile: Full-screen modal (bottom-sheet on mobile). |

**Interface Contract:**

```typescript
interface ModalLayerProps {
  // Managed by runtime modal requests
}

interface ModalRequest {
  id: string;
  title: string;
  type: 'confirmation' | 'form' | 'wizard' | 'configuration';
  workspaceId?: string;
  dismissible: boolean;
  onCommit?: () => void;
  onCancel?: () => void;
}
```

---

#### 1.3.9 Status Bar

| Attribute | Specification |
|-----------|---------------|
| **Ownership** | Shell layer (composition only) |
| **Runtime Dependencies** | All runtimes (status indicators), TimelineRuntime (active period), SelectionRuntime (selection count) |
| **Responsibilities** | Display runtime status indicators, active period, selection count, sync state, keyboard mode indicator |
| **Lifecycle** | Persistent. Never unmounts. |
| **Resize Behavior** | Fixed height (24px). Width fills viewport. |
| **Responsive Rules** | Desktop: Full status. Tablet: Truncated status. Mobile: Hidden (status accessible via Command HUD). |

---

### 1.4 Shell Invariants

1. **No business logic in shell regions.** Shell regions compose; they do not compute.
2. **No direct API calls from shell regions.** All data flows through Capabilities.
3. **No local state for domain data.** All domain state lives in runtimes.
4. **Shell regions are runtime consumers, not runtime owners.**
5. **Shell layout is persistent.** Region visibility and sizing persist across sessions.
6. **Shell is responsive.** All regions have defined behavior at every breakpoint.

---

## 2. Workspace Host

### 2.1 Overview

The Workspace Host is the **permanent mounting surface** for all workspaces. It sits between the Workspace Runtime (source of truth) and individual Workspace Renderers. It manages lifecycle, caching, switching, and restoration — without owning any domain state.

### 2.2 Workspace Pipeline

```
Workspace Runtime
      ↓
  Workspace Host
      ↓
Workspace Renderer
      ↓
 Workspace View
```

| Stage | Responsibility |
|-------|----------------|
| Workspace Runtime | Source of truth for which workspace is active, registered, cached |
| Workspace Host | Mounting, unmounting, caching, transition management |
| Workspace Renderer | Workspace-scoped composition, capability invocation, renderer selection |
| Workspace View | Final rendered output — tables, cards, charts, inspectors |

### 2.3 Workspace Lifecycle

```
Registered → Activated → Mounted → Cached → Restored → Deactivated → Destroyed
```

| State | Description | Trigger |
|-------|-------------|---------|
| **Registered** | Workspace definition exists in WorkspaceRegistration | Build time (static) |
| **Activated** | Workspace is set as active by user navigation or command | NavigationRuntime / CommandRuntime |
| **Mounted** | Workspace Host renders the workspace's renderer | WorkspaceRuntime activation event |
| **Cached** | Workspace is deactivated but kept in memory for fast re-activation | WorkspaceRuntime cache policy |
| **Restored** | Cached workspace is re-activated without re-mounting | NavigationRuntime back/forward |
| **Deactivated** | Workspace is no longer active but may remain cached | User navigates away |
| **Destroyed** | Workspace is evicted from cache and unmounted | Cache eviction (LRU, max 5 cached) |

### 2.4 Mounting

- When a workspace is activated, the Workspace Host checks the cache.
- If cached: restore from cache (no re-mount, preserve scroll position and selection).
- If not cached: mount the workspace renderer, invoke capabilities, populate view models.
- Mounting is **lazy** — capabilities are invoked on mount, not on registration.

**Interface Contract:**

```typescript
interface WorkspaceHostProps {
  // Derived from WorkspaceRuntime
  activeWorkspaceId: string;
  cachedWorkspaceIds: string[];
}

interface WorkspaceMountRequest {
  workspaceId: string;
  restoreFromCache: boolean;
  preserveState: boolean;
}
```

### 2.5 Persistence

- Workspace state (scroll position, filters, selection, sort order) is persisted by the Workspace Runtime.
- On deactivation, the workspace's ephemeral state is snapshotted.
- On restoration, the snapshot is applied.
- Persistence scope: per-workspace, per-session. Cross-session persistence is handled by StateRuntime.

**Interface Contract:**

```typescript
interface WorkspaceStateSnapshot {
  workspaceId: string;
  scrollPosition: { x: number; y: number };
  filters: Record<string, unknown>;
  sortConfig: { field: string; direction: 'asc' | 'desc' } | null;
  selectionIds: string[];
  timestamp: number;
}
```

### 2.6 Switching

- Workspace switching is **instant** when target is cached.
- When target is not cached, a loading state is shown (skeleton, not spinner — see [Part 8](#8-design-system)).
- Transitions use **cross-fade** (150ms) — no slide animations for workspace switches.
- During transition, the outgoing workspace's capabilities are not cancelled (they may still update cache).

**Interface Contract:**

```typescript
interface WorkspaceSwitchRequest {
  fromWorkspaceId: string | null;
  toWorkspaceId: string;
  transitionType: 'cached-restore' | 'cold-mount';
  duration: number; // ms
}
```

### 2.7 Caching

- **Strategy:** LRU (Least Recently Used).
- **Max cached workspaces:** 5.
- **Eviction:** When cache is full and a new workspace is activated, the least recently used cached workspace is destroyed.
- **Cache invalidation:** When a capability's data is invalidated (React Query), the cached workspace's view models are refreshed on next restoration, not in the background.

**Interface Contract:**

```typescript
interface WorkspaceCachePolicy {
  maxCached: number; // 5
  evictionStrategy: 'lru';
  invalidateOnStale: boolean; // true
}
```

### 2.8 Restoration

- When navigating back/forward (NavigationRuntime), the Workspace Host checks if the target workspace is cached.
- If cached: restore state snapshot, preserve scroll position, re-apply filters and selection.
- If not cached: cold-mount with default state.
- Restoration is **synchronous** from the user's perspective (no loading state for cached workspaces).

**Interface Contract:**

```typescript
interface WorkspaceRestorationRequest {
  workspaceId: string;
  snapshot: WorkspaceStateSnapshot | null;
  restoreScroll: boolean;
  restoreSelection: boolean;
  restoreFilters: boolean;
}
```

### 2.9 Workspace Host Invariants

1. **Workspace Host owns no domain state.** It delegates to WorkspaceRuntime.
2. **Workspace Host never calls APIs directly.** Capabilities are invoked by Workspace Renderers.
3. **Workspace Host manages transitions, not content.** Content is rendered by Workspace Renderers.
4. **Cache is bounded.** Never exceeds 5 cached workspaces.
5. **Restoration preserves user state.** Scroll, filters, selection, sort.

---

## 3. Context Runtime Expansion

### 3.1 Overview

The Context Runtime is a **future runtime** that composes multiple runtime states into a single, unified Context Object. It does not replace existing runtimes — it reads from them and provides a derived, read-only context that workspaces, renderers, and intelligence modules can consume.

> **Status: Specification only. Do NOT implement. Only define interfaces.**

### 3.2 Context Object Composition

```
Selection Runtime ──→ ┌──────────────────┐
Timeline Runtime ───→ │                  │
Workspace Runtime ──→ │  Context Runtime │ → Context Object
Scenario State ─────→ │                  │
Filters State ──────→ │                  │
Active Household ───→ └──────────────────┘
```

### 3.3 Context Object Interface

```typescript
/**
 * The Context Object is the single, derived, read-only representation
 * of the user's current operational context. It is composed by the
 * Context Runtime from multiple runtime states.
 *
 * Workspaces, Renderers, and Intelligence modules consume this object
 * to adapt their behavior without directly coupling to individual runtimes.
 */
interface ContextObject {
  // ── Selection Context ──
  selection: {
    activeEntityId: string | null;
    activeEntityType: string | null;
    selectedIds: string[];
    selectionRange: { start: string; end: string } | null;
    multiSelect: boolean;
  };

  // ── Timeline Context ──
  timeline: {
    activePeriod: {
      start: string; // ISO date
      end: string;   // ISO date
      label: string; // e.g., "FY 2025-26 Q3"
    };
    granularity: 'day' | 'week' | 'month' | 'quarter' | 'year';
    comparisonPeriod: {
      start: string;
      end: string;
      label: string;
    } | null;
  };

  // ── Workspace Context ──
  workspace: {
    activeWorkspaceId: string;
    activeWorkspaceType: string;
    workspaceFilters: Record<string, unknown>;
    workspaceSortConfig: { field: string; direction: 'asc' | 'desc' } | null;
  };

  // ── Scenario Context ──
  scenario: {
    activeScenarioId: string | null;
    scenarioName: string | null;
    scenarioParameters: Record<string, unknown> | null;
    isBaseline: boolean; // true when no scenario is active
  };

  // ── Filters Context ──
  filters: {
    activeFilters: FilterState[];
    globalFilters: GlobalFilterState;
  };

  // ── Active Household ──
  household: {
    householdId: string;
    householdName: string;
    members: HouseholdMember[];
    accounts: AccountSummary[];
  };

  // ── Metadata ──
  metadata: {
    timestamp: number;
    version: string;
    sessionId: string;
  };
}

interface FilterState {
  id: string;
  field: string;
  operator: 'eq' | 'neq' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'between' | 'contains';
  value: unknown;
  scope: 'workspace' | 'global';
}

interface GlobalFilterState {
  accountIds: string[] | null;
  categoryIds: string[] | null;
  entityIds: string[] | null;
  minAmount: number | null; // paise
  maxAmount: number | null; // paise
}

interface HouseholdMember {
  memberId: string;
  name: string;
  role: string;
}

interface AccountSummary {
  accountId: string;
  accountName: string;
  accountType: string;
  bankName: string;
  balancePaise: number;
}
```

### 3.4 Context Runtime Interface

```typescript
/**
 * The Context Runtime reads from all existing runtimes and composes
 * the Context Object. It is a read-only derived state — it never
 * mutates the source runtimes.
 */
interface ContextRuntime {
  /**
   * Returns the current Context Object.
   * Recomputes only when a source runtime state changes.
   */
  getContext(): ContextObject;

  /**
   * Subscribe to context changes.
   * Called whenever any source runtime state changes.
   */
  subscribe(listener: (context: ContextObject) => void): () => void;

  /**
   * Returns a memoized selector result.
   * Workspaces use this to subscribe to specific slices.
   */
  select<T>(selector: (context: ContextObject) => T): T;
}
```

### 3.5 Context Composition Rules

1. **Read-only.** The Context Runtime never writes to source runtimes.
2. **Derived.** All fields are computed from source runtime state.
3. **Memoized.** Context Object is recomputed only when a source changes.
4. **Single source of truth.** Each field in the Context Object maps to exactly one source runtime.
5. **No duplication.** The Context Object does not store state that isn't in a source runtime.

### 3.6 Context Consumers

| Consumer | How it uses Context |
|----------|-------------------|
| Workspace Renderers | Adapt rendering based on active period, filters, scenario |
| Intelligence Layer | Generate insights scoped to active household, period, selection |
| Graph Runtime | Filter graph to active household, period, selected entities |
| Command Runtime | Suggest commands relevant to active workspace, selection, period |
| Renderers | Adapt density, columns, and detail level based on context |

---

## 4. Intelligence Layer

### 4.1 Overview

The Intelligence Layer provides **augmentation, not interruption**. It surfaces insights, patterns, anomalies, and recommendations at the right time and place — without overwhelming the user.

### 4.2 Intelligence Tiers

| Tier | Character | Placement | Trigger | Purpose |
|------|-----------|-----------|---------|---------|
| **Passive** | Ambient, non-blocking | Bottom Intelligence Shelf, Right Context Panel | Always available, user discovers | Surface patterns, trends, summaries |
| **Investigative** | On-demand, user-initiated | Overlay Layer (graph, detail panel) | User action (click, command) | Explore relationships, drill into anomalies |
| **Executive** | High-signal, requires attention | Modal Layer, notification toast | Threshold breach, anomaly detection | Alert on critical issues, require decisions |

### 4.3 Passive Intelligence

**Where:** Bottom Intelligence Shelf (collapsed state), Right Context Panel (when no selection).

**When:** Always available. Updates reactively as data changes.

**Why:** Provides ambient awareness without demanding attention. The user discovers insights by glancing at the shelf or opening the context panel.

**Examples:**
- "Spending in 'Dining Out' is 34% higher than last month"
- "Net cash flow is positive this quarter (+₹12,450)"
- "3 transactions are uncategorized"
- "Credit card payment due in 5 days (₹8,200)"

**Rules:**
- Maximum 5 passive insights visible at once.
- Insights are ranked by relevance (recency + severity + impact).
- Passive insights never block interaction.
- Dismissed insights are suppressed for the session.

**Interface Contract:**

```typescript
interface PassiveInsight {
  id: string;
  category: 'spending' | 'income' | 'cashflow' | 'forecast' | 'anomaly' | 'reminder';
  title: string;
  summary: string;
  severity: 'info' | 'positive' | 'warning' | 'critical';
  confidence: number; // 0.0–1.0
  relatedEntityId?: string;
  relatedEntityType?: string;
  actionLabel?: string;
  actionRoute?: string;
  dismissible: boolean;
}
```

### 4.4 Investigative Intelligence

**Where:** Overlay Layer (graph exploration), Right Context Panel (detail drill-down).

**When:** User-initiated. Triggered by clicking an insight, selecting an entity, or issuing a command.

**Why:** Allows the user to explore "why" behind a pattern or anomaly. Provides relationship maps, evidence trails, and drill-down paths.

**Examples:**
- "Show all transactions contributing to this anomaly"
- "What categories drove the spending increase?"
- "How does this transaction relate to other entities?"
- "What is the evidence trail for this reconciliation?"

**Rules:**
- Investigative intelligence is always user-initiated.
- It opens in an overlay or context panel — never blocks the workspace.
- It provides actionable drill-down paths, not dead-ends.
- Evidence is always traceable to source data.

**Interface Contract:**

```typescript
interface InvestigativeInsight {
  id: string;
  trigger: 'entity-selected' | 'insight-clicked' | 'command-issued';
  title: string;
  summary: string;
  evidenceTrail: EvidenceLink[];
  relatedEntities: EntityReference[];
  drillDownActions: DrillDownAction[];
}

interface EvidenceLink {
  label: string;
  sourceType: 'transaction' | 'statement' | 'reconciliation' | 'forecast';
  sourceId: string;
  confidence: number;
}

interface DrillDownAction {
  label: string;
  targetWorkspace?: string;
  targetRoute?: string;
  contextPayload?: Record<string, unknown>;
}
```

### 4.5 Executive Intelligence

**Where:** Modal Layer (confirmation required), notification toast (informational).

**When:** System-detected. Triggered by threshold breaches, anomaly detection, or critical reminders.

**Why:** Demands attention for issues that require user decision or awareness.

**Examples:**
- "Account balance below threshold (₹500)"
- "Large transaction detected (₹45,000) — confirm categorization"
- "Reconciliation mismatch: ₹230 difference — resolve?"
- "Forecast indicates negative cash flow in 3 weeks"

**Rules:**
- Maximum 1 executive intelligence active at a time.
- Critical severity requires user action (modal). Warning severity is informational (toast).
- Executive intelligence is never auto-dismissed.
- User decisions are logged for audit trail.

**Interface Contract:**

```typescript
interface ExecutiveInsight {
  id: string;
  severity: 'warning' | 'critical';
  title: string;
  summary: string;
  requiresAction: boolean;
  actionLabel: string;
  cancelLabel: string;
  onAction?: () => void;
  onCancel?: () => void;
  auditTrail: {
    detectedAt: number;
    threshold?: number; // paise
    actualValue?: number; // paise
  };
}
```

### 4.6 Anti-Overload Rules

1. **Maximum 5 passive insights** visible simultaneously.
2. **Maximum 1 executive insight** active at a time.
3. **Investigative insights** are never auto-surfaced — only user-initiated.
4. **Insight deduplication:** Same insight cannot appear in multiple tiers simultaneously.
5. **Insight suppression:** Dismissed insights are suppressed for the session. Resolved insights are removed.
6. **Insight ranking:** Relevance score = `recency(0.3) + severity(0.4) + impact(0.3)`.
7. **No notification spam:** If multiple insights share the same root cause, they are consolidated into one.

---

## 5. Graph Runtime Integration

### 5.1 Overview

The Graph Runtime is an **investigative engine**. It explores relationships between financial entities — transactions, accounts, categories, statements, reconciliations, forecasts. It is never the primary surface. It never becomes the desktop.

### 5.2 Graph Runtime Constraints

1. **Investigative only.** The graph is invoked to explore, not to navigate.
2. **Overlay surface.** The graph renders in the Overlay Layer, not in the Workspace Host.
3. **Context-bound.** The graph is always scoped to the current Context Object (household, period, selection).
4. **Evidence-linked.** Every graph node links back to source data via evidence trails.
5. **Never graph-first.** The user never starts in the graph. They arrive from a workspace, selection, or insight.

### 5.3 Invocation

The Graph Runtime is invoked through:

| Trigger | Source | Action |
|---------|--------|--------|
| Entity selection | SelectionRuntime | Show entity relationships in Right Context Panel |
| "Explore relationships" command | CommandRuntime | Open graph overlay |
| Insight drill-down | Intelligence Layer | Open graph overlay scoped to insight |
| Workspace action | Workspace Renderer | Open graph overlay scoped to workspace data |

**Interface Contract:**

```typescript
interface GraphInvocationRequest {
  trigger: 'selection' | 'command' | 'insight' | 'workspace-action';
  scope: {
    householdId: string;
    periodStart: string;
    periodEnd: string;
    entityIds?: string[];
    entityTypes?: string[];
  };
  displayMode: 'context-panel' | 'overlay';
  initialLayout: 'force-directed' | 'hierarchical' | 'temporal';
}
```

### 5.4 Synchronization

The Graph Runtime synchronizes with:

| Source | Synchronization |
|--------|----------------|
| SelectionRuntime | When a graph node is selected, SelectionRuntime is updated. When SelectionRuntime changes, graph highlights the selected entity. |
| TimelineRuntime | When the timeline period changes, the graph re-renders with the new period scope. |
| WorkspaceRuntime | When the active workspace changes, the graph overlay closes (if open). |
| Context Runtime (future) | The graph always reflects the current Context Object. |

**Rules:**
- Graph state is **ephemeral**. It is not persisted across sessions.
- Graph layout is **deterministic** given the same input (same nodes, same edges → same layout).
- Graph does not maintain its own selection state — it delegates to SelectionRuntime.

### 5.5 Overlays

The Graph Runtime renders in two modes:

| Mode | Surface | Size | Use Case |
|------|---------|------|----------|
| **Context Panel** | Right Context Panel | 280–420px | Quick relationship view for selected entity |
| **Full Overlay** | Overlay Layer | Full workspace area | Deep exploration, multi-hop traversal |

**Context Panel Mode:**
- Shows immediate relationships (1-hop) for the selected entity.
- Limited to 20 nodes.
- No interactive layout — static arrangement.

**Full Overlay Mode:**
- Shows multi-hop relationships (configurable depth, default 2).
- Interactive layout (pan, zoom, drag).
- Node selection updates SelectionRuntime.
- Evidence panel slides in on node click.

### 5.6 Evidence Visualization

Every graph node and edge must support evidence visualization:

```typescript
interface GraphEvidencePanel {
  nodeId: string;
  nodeType: string;
  nodeLabel: string;
  evidence: {
    sourceType: 'transaction' | 'statement' | 'reconciliation' | 'forecast';
    sourceId: string;
    sourceLabel: string;
    amountPaise?: number;
    date?: string;
    confidence: number;
  }[];
  drillDownActions: DrillDownAction[];
}
```

**Rules:**
- Evidence is always traceable to source data.
- Clicking an evidence link navigates to the source workspace with the entity pre-selected.
- Evidence confidence < 0.8 is visually marked (dashed border, warning color).

### 5.7 Relationship Exploration

The graph supports the following relationship types:

| Relationship | Source → Target | Edge Label |
|--------------|-----------------|------------|
| Transaction → Account | Transaction debited/credited from Account | `DEBIT` / `CREDIT` |
| Transaction → Category | Transaction categorized as Category | `CATEGORIZED_AS` |
| Transaction → Statement | Transaction appears in Statement | `APPEARS_IN` |
| Transaction → Reconciliation | Transaction matched in Reconciliation | `MATCHED_IN` |
| Account → Bank | Account belongs to Bank | `BELONGS_TO` |
| Category → Parent Category | Category is child of Parent Category | `CHILD_OF` |
| Forecast → Transaction | Forecast predicts Transaction pattern | `PREDICTS` |
| Scenario → Transaction | Scenario modifies Transaction | `MODIFIES` |

**Interface Contract:**

```typescript
interface GraphNode {
  id: string;
  type: 'transaction' | 'account' | 'category' | 'statement' | 'reconciliation' | 'forecast' | 'scenario' | 'bank';
  label: string;
  properties: Record<string, unknown>;
  evidenceCount: number;
}

interface GraphEdge {
  id: string;
  sourceId: string;
  targetId: string;
  type: string; // from relationship table above
  properties: Record<string, unknown>;
  weight: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  scope: GraphInvocationRequest['scope'];
}
```

### 5.8 Graph Runtime Invariants

1. **Never the primary surface.** Graph is always an overlay or context panel.
2. **Never persists state.** Graph state is ephemeral.
3. **Never owns selection.** Selection is delegated to SelectionRuntime.
4. **Never bypasses the data pipeline.** Graph data comes through Capabilities.
5. **Never becomes navigation.** Graph exploration is investigative, not navigational.

---

## 6. Command Runtime

### 6.1 Overview

The Command Runtime is the **control plane** of the Financial OS. It provides a unified interface for natural language commands, keyboard shortcuts, quick actions, recent commands, pinned workflows, and workspace launching.

### 6.2 Command Sources

| Source | Input | Example |
|--------|-------|---------|
| **Natural Language** | Free-text input in Command HUD | "Show me spending on dining last month" |
| **Keyboard Commands** | Keyboard shortcut | `Cmd+K` opens palette, `Cmd+1` switches to workspace 1 |
| **Quick Actions** | Contextual action buttons | "Reconcile", "Import Statement", "New Transaction" |
| **Recent Commands** | History of executed commands | Last 10 commands |
| **Pinned Workflows** | User-pinned multi-step flows | "Monthly Review", "Quarterly Reconciliation" |
| **Workspace Launching** | Direct workspace navigation | "Open Loans workspace" |

### 6.3 Command Interface

```typescript
/**
 * The Command Runtime manages command registration,
 * execution, routing, and history.
 */
interface CommandRuntime {
  /**
   * Register a command. Called at workspace registration time.
   */
  registerCommand(command: CommandDefinition): void;

  /**
   * Execute a command by ID or natural language input.
   * Routes to the appropriate handler.
   */
  execute(input: string | CommandId): Promise<CommandResult>;

  /**
   * Search commands by query (for command palette).
   */
  search(query: string): CommandSearchResult[];

  /**
   * Get recent commands (last N).
   */
  getRecent(limit: number): CommandHistoryEntry[];

  /**
   * Get pinned workflows.
   */
  getPinned(): PinnedWorkflow[];

  /**
   * Pin a workflow.
   */
  pin(workflow: PinnedWorkflow): void;

  /**
   * Subscribe to command execution events.
   */
  subscribe(listener: (event: CommandEvent) => void): () => void;
}

interface CommandDefinition {
  id: string;
  label: string;
  category: 'navigation' | 'action' | 'workflow' | 'intelligence' | 'graph';
  keywords: string[];
  shortcut?: string; // e.g., "mod+k", "mod+1"
  workspaceId?: string; // if command is workspace-scoped
  handler: (context: ContextObject) => Promise<CommandResult>;
  requiresContext?: boolean;
  icon?: string;
}

type CommandId = string;

interface CommandResult {
  success: boolean;
  message?: string;
  navigation?: { workspaceId?: string; route?: string };
  overlay?: OverlayRequest;
  insight?: PassiveInsight | InvestigativeInsight;
}

interface CommandSearchResult {
  command: CommandDefinition;
  score: number; // relevance score
  matchedOn: 'label' | 'keyword' | 'natural-language';
}

interface CommandHistoryEntry {
  commandId: string;
  input: string;
  timestamp: number;
  result: CommandResult;
}

interface PinnedWorkflow {
  id: string;
  label: string;
  steps: WorkflowStep[];
  icon?: string;
}

interface WorkflowStep {
  label: string;
  commandId: string;
  contextPayload?: Record<string, unknown>;
}

interface CommandEvent {
  type: 'executed' | 'failed' | 'cancelled';
  commandId: string;
  input: string;
  timestamp: number;
}
```

### 6.4 Command Routing

```
User Input (NL / Keyboard / Click)
         ↓
   Command Runtime
         ↓
    Parse and Match
         ↓
   ┌─────────────────────────┐
   │ Is it navigation?        │──→ NavigationRuntime.navigate()
   │ Is it a workspace action?│──→ WorkspaceRuntime.activate()
   │ Is it an intelligence?   │──→ IntelligenceRuntime (future)
   │ Is it a graph query?     │──→ GraphRuntime.invoke()
   │ Is it a workflow?        │──→ Execute workflow steps
   │ Is it a quick action?    │──→ Execute command handler
   └─────────────────────────┘
         ↓
   Command Result
         ↓
   Update History
         ↓
   Publish CommandEvent
```

### 6.5 Natural Language Processing

Natural language commands are parsed and matched to registered commands:

1. **Tokenize** the input.
2. **Match** against command labels, keywords, and synonyms.
3. **Extract** parameters (dates, amounts, categories, account names).
4. **Route** to the best-matching command handler.
5. **If no match:** return suggestions (fuzzy search results).

**Rules:**
- NL parsing is **client-side** (no backend NLP required for command routing).
- NL commands that require backend intelligence (e.g., "forecast my cash flow") route to the Intelligence Runtime (future).
- Ambiguous commands return disambiguation options.
- Amounts in NL are parsed to paise (₹1,234.56 → 123456 paise).

### 6.6 Keyboard Commands

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + K` | Open command palette |
| `Cmd/Ctrl + 1..9` | Switch to workspace N |
| `Cmd/Ctrl + [` | Navigate back |
| `Cmd/Ctrl + ]` | Navigate forward |
| `Cmd/Ctrl + F` | Focus search in active workspace |
| `Cmd/Ctrl + G` | Open graph overlay |
| `Cmd/Ctrl + I` | Open intelligence shelf |
| `Cmd/Ctrl + ,` | Open settings |
| `Esc` | Close overlay / modal / palette |
| `?` | Show keyboard shortcuts help |

**Rules:**
- Keyboard shortcuts are **global** — they work in any workspace.
- Workspace-specific shortcuts are registered by the workspace and only active when the workspace is mounted.
- Shortcuts never override browser/OS shortcuts (e.g., `Cmd+T`, `Cmd+W`).

### 6.7 Quick Actions

Quick actions are contextual command buttons that appear in the Command HUD and Right Context Panel. They are:

- **Workspace-scoped:** Each workspace registers its own quick actions.
- **Context-aware:** Available actions change based on selection and context.
- **Labeled:** Always have a clear label and icon.
- **Limited:** Maximum 5 quick actions visible at once.

**Interface Contract:**

```typescript
interface QuickAction {
  id: string;
  label: string;
  icon: string;
  workspaceId: string;
  commandId: string;
  contextRequired?: boolean; // if true, requires active selection
  order: number;
}
```

### 6.8 Recent Commands

- Last 10 executed commands are stored.
- Recent commands are **session-scoped** (not persisted across sessions).
- Clicking a recent command re-executes it with the current context.
- Recent commands are displayed in the command palette below search results.

### 6.9 Pinned Workflows

Pinned workflows are multi-step command sequences that the user pins for quick access:

- **User-created:** Users can pin any sequence of commands as a workflow.
- **Named:** Each workflow has a user-defined name and icon.
- **Sequential:** Steps execute in order. Each step's result feeds the next step's context.
- **Persistent:** Pinned workflows persist across sessions (StateRuntime).

**Example Workflow: "Monthly Review"**

```
Step 1: Navigate to Cashflow workspace
Step 2: Set timeline to last month
Step 3: Open spending breakdown
Step 4: Show anomalies for the period
Step 5: Navigate to Reconciliation workspace
```

### 6.10 Workspace Launching

- The command palette supports direct workspace launching by name.
- Typing a workspace name (e.g., "loans", "investments") in the command palette shows the workspace as the top result.
- Selecting the workspace result activates it via WorkspaceRuntime.

---

## 7. Renderer Architecture

### 7.1 Overview

Every Financial Object in ClariFin_OS must support multiple rendering modes without duplicating business logic. The Renderer Architecture defines a unified model where a single ViewModel can be rendered as a Card, Table row, Timeline entry, Graph node, Inspector panel, Mini widget, or Chart — all sharing the same underlying data and logic.

### 7.2 Financial Object Model

A Financial Object is any domain entity that has a ViewModel representation:

| Financial Object | Example ViewModels |
|------------------|-------------------|
| Transaction | TransactionViewModel |
| Account | AccountViewModel |
| Category | CategoryViewModel |
| Statement | StatementViewModel |
| Reconciliation | ReconciliationViewModel |
| Forecast | ForecastViewModel |
| Scenario | ScenarioViewModel |
| Net Worth Snapshot | NetWorthViewModel |
| Cash Flow Period | CashflowViewModel |
| Investment | InvestmentViewModel |
| Loan | LoanViewModel |
| Credit Card | CreditCardViewModel |

### 7.3 Renderer Modes

| Mode | Surface | Purpose | Density |
|------|---------|---------|---------|
| **Card** | Workspace grid, intelligence shelf | Summarized entity view | Medium |
| **Table** | Workspace list view | Dense tabular data | High |
| **Timeline** | Bottom Intelligence Shelf, timeline workspace | Chronological entry | Medium |
| **Graph Node** | Graph overlay, context panel | Relationship node | Low |
| **Inspector** | Right Context Panel | Full detail view | Medium |
| **Mini Widget** | Dashboard, status bar | Compact summary | Low |
| **Chart** | Workspace analytics view | Visual data representation | Variable |

### 7.4 Renderer Interface

```typescript
/**
 * Every Financial Object's ViewModel must implement this interface
 * to be renderable in all 7 modes.
 */
interface RenderableViewModel<TData> {
  /** Unique identifier for the entity */
  id: string;

  /** Entity type (e.g., 'transaction', 'account') */
  type: string;

  /** Human-readable label */
  label: string;

  /** Core data payload (the ViewModel itself) */
  data: TData;

  /** Monetary values in paise (never floats) */
  monetaryValues: MonetaryValue[];

  /** Temporal context (if applicable) */
  temporalContext?: {
    date: string; // ISO date
    period?: string;
  };

  /** Relationships (for graph rendering) */
  relationships?: EntityReference[];

  /** Evidence trail (for inspector and graph) */
  evidence?: EvidenceLink[];

  /** Selection state (managed by SelectionRuntime, not the renderer) */
  selectionState?: {
    isSelected: boolean;
    isHighlighted: boolean;
  };
}

interface MonetaryValue {
  label: string; // e.g., "Amount", "Balance", "Due"
  valuePaise: number; // absolute paise
  isPositive: boolean; // direction (income vs expense)
  format: 'currency' | 'percentage' | 'plain';
}

interface EntityReference {
  entityId: string;
  entityType: string;
  label: string;
  relationshipType: string;
}
```

### 7.5 Renderer Registry

```typescript
/**
 * The Renderer Registry maps Financial Object types to their
 * renderer implementations. Each renderer mode is a pure
 * presentational component that receives a RenderableViewModel
 * and renders the appropriate UI.
 */
interface RendererRegistry {
  /**
   * Register a renderer for a specific object type and mode.
   */
  register<TData>(
    objectType: string,
    mode: RendererMode,
    renderer: RendererComponent<TData>
  ): void;

  /**
   * Get the renderer for a specific object type and mode.
   */
  get<TData>(
    objectType: string,
    mode: RendererMode
  ): RendererComponent<TData> | null;

  /**
   * Check if a renderer exists for the given type and mode.
   */
  has(objectType: string, mode: RendererMode): boolean;
}

type RendererMode =
  | 'card'
  | 'table'
  | 'timeline'
  | 'graph-node'
  | 'inspector'
  | 'mini-widget'
  | 'chart';

/**
 * A renderer component is a pure function of ViewModel + Context.
 * It contains NO business logic. It only maps ViewModel fields to UI.
 */
interface RendererComponent<TData> {
  (props: {
    viewModel: RenderableViewModel<TData>;
    context: ContextObject;
    density: DensityLevel;
    selectionState: SelectionState;
    onAction: (action: RendererAction) => void;
  }): JSX.Element;
}

interface SelectionState {
  isSelected: boolean;
  isHighlighted: boolean;
  isFocused: boolean;
}

interface RendererAction {
  type: 'select' | 'navigate' | 'drill-down' | 'edit' | 'delete' | 'expand';
  payload?: Record<string, unknown>;
}

type DensityLevel = 'compact' | 'comfortable' | 'spacious';
```

### 7.6 Renderer Rules

1. **Single business logic source.** Each Financial Object has one ViewModel. All 7 renderers consume the same ViewModel.
2. **No logic in renderers.** Renderers are pure presentational mappings: ViewModel → UI.
3. **No API calls in renderers.** Data is provided by Capabilities.
4. **No state in renderers.** Selection, focus, and highlight state comes from SelectionRuntime.
5. **Context-aware.** Renderers adapt to the Context Object (density, period, filters).
6. **Action delegation.** Renderers emit actions (select, navigate, drill-down) — they do not execute them. Actions are routed by the workspace.

### 7.7 Renderer Selection Logic

Workspaces select the appropriate renderer mode based on:

| Factor | Effect |
|--------|--------|
| Workspace type | Each workspace has a default renderer mode |
| User preference | User can switch between table/card/chart views |
| Context density | Compact density → table; Spacious → card |
| Selection state | Selected entity → inspector in context panel |
| Timeline active | Timeline mode in bottom shelf |

```typescript
interface RendererSelection {
  objectType: string;
  mode: RendererMode;
  reason: 'workspace-default' | 'user-preference' | 'context-density' | 'selection' | 'timeline';
}
```

---

## 8. Design System

### 8.1 Overview

The Design System is the **UI grammar** of ClariFin_OS. It defines spacing, elevation, animation, motion, color semantics, density levels, information hierarchy, and all interaction states. It is the single source of truth for visual consistency.

The existing design system is defined in `frontend/styles/financial-os.css` with CSS custom properties. This specification formalizes and extends it.

### 8.2 Spacing

**Base unit:** 4px (half-step of 8px system).

| Token | Value | Usage |
|-------|-------|-------|
| `--space-0` | 0px | No spacing |
| `--space-1` | 4px | Tight inline spacing (icon + label) |
| `--space-2` | 8px | Default inline spacing |
| `--space-3` | 12px | Tight block spacing |
| `--space-4` | 16px | Default block spacing |
| `--space-5` | 24px | Section spacing |
| `--space-6` | 32px | Large section spacing |
| `--space-7` | 48px | Page-level spacing |
| `--space-8` | 64px | Major section separation |
| `--space-9` | 128px | Page top/bottom padding |

**Rules:**
- All spacing must use these tokens. No hardcoded pixel values.
- Inline spacing (horizontal) defaults to `--space-2` (8px).
- Block spacing (vertical) defaults to `--space-4` (16px).
- Financial data tables use `--space-1` (4px) cell padding for density.

### 8.3 Elevation

6-level shadow scale:

| Token | Value | Usage |
|-------|-------|-------|
| `--elevation-0` | none | Flat surfaces (workspace content) |
| `--elevation-1` | subtle shadow | Raised cards, table rows on hover |
| `--elevation-2` | medium shadow | Dropdowns, popovers |
| `--elevation-3` | prominent shadow | Right Context Panel, Bottom Shelf |
| `--elevation-4` | strong shadow | Overlays |
| `--elevation-5` | maximum shadow | Modals, command palette |

**Rules:**
- Workspace content is always `--elevation-0` (flat).
- Elevation increases as elements move away from the primary content.
- Modals are always highest elevation.

### 8.4 Animation

8-step duration scale:

| Token | Value | Usage |
|-------|-------|-------|
| `--duration-0` | 0ms | Instant (no animation) |
| `--duration-1` | 50ms | Micro-interactions (hover, focus) |
| `--duration-2` | 100ms | Toggle, checkbox |
| `--duration-3` | 150ms | Cross-fade (workspace switch) |
| `--duration-4` | 200ms | Slide, expand/collapse |
| `--duration-5` | 300ms | Panel open/close |
| `--duration-6` | 400ms | Overlay fade |
| `--duration-7` | 500ms | Modal entrance |

4 easing curves:

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-in` | cubic-bezier(0.4, 0, 1, 1) | Elements exiting |
| `--ease-out` | cubic-bezier(0, 0.2, 0.2, 1) | Elements entering |
| `--ease-in-out` | cubic-bezier(0.4, 0, 0.2, 1) | Bidirectional (expand/collapse) |
| `--ease-linear` | linear | Continuous motion (timeline scrubber) |

**Rules:**
- Workspace switches use `--duration-3` (150ms) cross-fade with `--ease-out`.
- Panel open/close uses `--duration-5` (300ms) with `--ease-in-out`.
- Hover and focus use `--duration-1` (50ms) with `--ease-out`.
- No animation exceeds 500ms.
- `prefers-reduced-motion` disables all non-essential animations.

### 8.5 Motion

Motion principles:

1. **Directional consistency.** Panels slide from their edge (left panel slides left-in, right panel slides right-in).
2. **Origin-based.** Overlays originate from the triggering element (command palette drops from Command HUD).
3. **Staggered lists.** List items animate in with 20ms stagger (max 10 items, then instant).
4. **No bounce.** Financial OS motion is precise, not playful. No spring/bounce physics.
5. **Interruptible.** All animations can be interrupted by user input (no animation locks).

### 8.6 Color Semantics

#### Surface Hierarchy

| Token | Usage |
|-------|-------|
| `--surface-default` | Workspace background |
| `--surface-raised` | Cards, table headers |
| `--surface-interactive` | Hover state on interactive elements |
| `--surface-selected` | Selected row/card background |
| `--surface-floating` | Dropdowns, popovers |
| `--surface-overlay` | Overlay background |
| `--surface-graph` | Graph canvas background |
| `--surface-terminal` | Command palette background |
| `--surface-timeline` | Bottom shelf background |

#### Financial Semantic Colors

| Token | Usage | Light | Dark |
|-------|-------|-------|------|
| `--color-positive` | Income, surplus, gains | Green | Green |
| `--color-negative` | Expense, deficit, loss | Red | Red |
| `--color-warning` | Threshold breach, alert | Amber | Amber |
| `--color-info` | Informational, neutral | Blue | Blue |
| `--color-neutral` | No change, baseline | Gray | Gray |

Each semantic color has a 50–900 scale (50 = lightest, 900 = darkest).

**Rules:**
- Financial values are always colored by their semantic meaning, not by UI preference.
- Positive = income/surplus. Negative = expense/deficit. Never invert.
- Warning is used for threshold breaches and alerts, not for general highlighting.
- Color is never the sole indicator — always pair with text or icon.

#### Graph Node Colors

13 node types, each with a dedicated color:

| Node Type | Color Family |
|-----------|-------------|
| Transaction | Blue |
| Account | Green |
| Category | Purple |
| Statement | Cyan |
| Reconciliation | Orange |
| Forecast | Indigo |
| Scenario | Pink |
| Bank | Teal |
| Investment | Lime |
| Loan | Red |
| Credit Card | Amber |
| Net Worth | Violet |
| Cash Flow | Sky |

### 8.7 Density Levels

| Level | Usage | Row Height | Cell Padding | Font Size |
|-------|-------|------------|--------------|-----------|
| **Compact** | Large datasets, tables | 32px | 4px | 12px |
| **Comfortable** | Default | 40px | 8px | 13px |
| **Spacious** | Dashboards, cards | 56px | 16px | 14px |

**Rules:**
- Default density is **Comfortable**.
- User can switch density in settings. Preference persists.
- Tables default to **Compact**.
- Cards default to **Spacious**.
- Density is part of the Context Object — renderers adapt.

### 8.8 Information Hierarchy

| Level | Font Size | Font Weight | Usage |
|-------|-----------|-------------|-------|
| **H1** | 24px | 700 | Workspace title (Global Header) |
| **H2** | 20px | 600 | Section heading within workspace |
| **H3** | 16px | 600 | Card title, panel heading |
| **Body** | 13px | 400 | Default text, table cells |
| **Small** | 12px | 400 | Secondary text, metadata |
| **Caption** | 11px | 400 | Timestamps, IDs, hints |
| **Mono** | 13px | 400 | Financial values (tabular-nums) |

**Typography:**
- Sans-serif: Inter (UI text)
- Monospace: JetBrains Mono (financial values, IDs, code)
- All financial values use `font-variant-numeric: tabular-nums` for alignment.

### 8.9 Loading Behavior

| Scenario | Pattern | Rationale |
|----------|---------|-----------|
| Workspace cold-mount | Skeleton (structure placeholder) | Shows content shape, not generic spinner |
| Table data loading | Skeleton rows (same height as data rows) | Preserves layout stability |
| Card data loading | Skeleton card (same dimensions) | No layout shift |
| Graph loading | Skeleton graph canvas with pulse | Indicates graph is computing |
| Command executing | Inline progress indicator in Command HUD | Non-blocking |
| Intelligence computing | Shimmer placeholder in Intelligence Shelf | Ambient, non-blocking |

**Rules:**
- Never use a generic full-screen spinner.
- Skeletons must match the final content dimensions (no layout shift).
- Loading state timeout: 10 seconds → show timeout message with retry.
- Loading states are derived from Capability state (React Query `isLoading`/`isFetching`).

### 8.10 Empty States

Every workspace and renderer must define an empty state:

| Scenario | Empty State Content |
|----------|---------------------|
| No transactions | "No transactions found. Import a statement to get started." + Import button |
| No accounts | "No accounts registered. Add an account to begin tracking." + Add button |
| No forecasts | "No forecasts generated. Run a forecast to see projections." + Forecast button |
| No reconciliation | "No reconciliation sessions. Start reconciling to match transactions." + Reconcile button |
| No search results | "No results found for '{query}'. Try different keywords." |
| No insights | "No insights available for this period. Data may be insufficient." |

**Rules:**
- Empty states always include a clear call-to-action.
- Empty states are contextual (different for each workspace).
- Empty states never show error styling (they are not errors).
- Empty states include an illustration or icon (not just text).

### 8.11 Error States

| Severity | Pattern | Action |
|----------|---------|--------|
| **Recoverable** | Inline error banner in workspace | "Retry" button |
| **Capability failure** | Error card in workspace content area | "Retry" + "Report" buttons |
| **Network failure** | Status bar indicator + toast | Auto-retry (3 attempts, exponential backoff) |
| **Critical failure** | Modal with error details | "Reload" + "Contact Support" |

**Rules:**
- Errors never crash the shell. Error boundaries catch and display gracefully.
- Error messages are human-readable (no stack traces in UI).
- All errors are logged for debugging.
- Retry is always available for recoverable errors.
- Error states use `--color-negative` for visual indication.

### 8.12 Selection States

| State | Visual | Trigger |
|-------|--------|---------|
| **Unselected** | Default styling | — |
| **Hovered** | `--surface-interactive` background | Mouse hover |
| **Selected** | `--surface-selected` background + left border accent | Click |
| **Multi-selected** | `--surface-selected` + checkbox indicator | Cmd/Ctrl+Click |
| **Range-selected** | `--surface-selected` (range) + count badge | Shift+Click |
| **Highlighted** | Subtle outline (no background change) | Graph node hover, search match |
| **Focused** | Focus ring (2px, `--color-info`) | Keyboard navigation |

**Rules:**
- Selection state is managed by SelectionRuntime, not by components.
- Components read selection state from the Context Object.
- Only one entity can be "Selected" (primary selection). Multiple can be "Multi-selected".
- "Highlighted" is ephemeral (hover, search match) and does not persist.

### 8.13 Focus States

| Element | Focus Style |
|---------|------------|
| Interactive elements | 2px focus ring, `--color-info`, offset 2px |
| Table rows | Inset focus ring on left border |
| Cards | Focus ring around card boundary |
| Graph nodes | Focus ring around node + slight scale (1.02) |
| Command palette input | Focus ring + cursor visible |

**Rules:**
- Focus is always visible (never `outline: none` without replacement).
- Focus order follows visual order (top-to-bottom, left-to-right).
- `focus-visible` is used to show focus ring only on keyboard navigation (not mouse click).
- Tab order is logical and documented per workspace.

### 8.14 Z-Index Hierarchy

| Token | Value | Usage |
|-------|-------|-------|
| `--z-base` | 0 | Workspace content |
| `--z-raised` | 10 | Cards, table headers (sticky) |
| `--z-dropdown` | 100 | Dropdowns, popovers |
| `--z-sticky` | 200 | Sticky headers, command HUD |
| `--z-overlay` | 1000 | Overlays (graph, command palette) |
| `--z-modal` | 2000 | Modals |
| `--z-notification` | 3000 | Toasts, notifications |

**Rules:**
- Z-index values are never hardcoded. Always use tokens.
- No element may exceed `--z-notification`.
- Within the same layer, stacking is by DOM order.

---

## 9. Runtime Event Bus

### 9.1 Overview

The Runtime Event Bus is the **inter-runtime communication mechanism**. Runtimes publish events when their state changes. Other runtimes, workspaces, and shell regions subscribe to relevant events. The event bus is **fire-and-forget** — publishers do not wait for subscriber responses.

### 9.2 Event Bus Interface

```typescript
/**
 * The Runtime Event Bus is a publish/subscribe mechanism
 * for inter-runtime communication.
 *
 * Runtimes publish events when their state changes.
 * Shell regions, workspaces, and other runtimes subscribe
 * to relevant events.
 *
 * The bus is fire-and-forget. Publishers do not wait for
 * subscriber responses. Events are synchronous but non-blocking.
 */
interface RuntimeEventBus {
  /**
   * Publish an event. All subscribers are notified synchronously.
   */
  publish<T extends RuntimeEvent>(event: T): void;

  /**
   * Subscribe to events of a specific type.
   * Returns an unsubscribe function.
   */
  subscribe<T extends RuntimeEvent>(
    eventType: T['type'],
    handler: (event: T) => void
  ): () => void;

  /**
   * Subscribe to all events (for logging/debugging).
   */
  subscribeAll(handler: (event: RuntimeEvent) => void): () => void;
}
```

### 9.3 Event Catalog

#### Selection Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `SelectionChanged` | SelectionRuntime | Context Runtime, Graph Runtime, Intelligence Runtime, Workspace Renderers | `{ activeEntityId, selectedIds, selectionRange }` |
| `SelectionCleared` | SelectionRuntime | Context Runtime, Graph Runtime, Right Context Panel | `{ previousEntityId }` |
| `SelectionHighlighted` | SelectionRuntime | Graph Runtime, Workspace Renderers | `{ entityId, source }` |

#### Timeline Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `TimelineChanged` | TimelineRuntime | Context Runtime, Workspace Renderers, Intelligence Runtime | `{ activePeriod, granularity, comparisonPeriod }` |
| `TimelineGranularityChanged` | TimelineRuntime | Workspace Renderers | `{ granularity }` |
| `TimelineScrubbed` | TimelineRuntime | Intelligence Runtime | `{ scrubPosition, period }` |

#### Workspace Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `WorkspaceOpened` | WorkspaceRuntime | Navigation Runtime, Command Runtime, Intelligence Runtime | `{ workspaceId, workspaceType }` |
| `WorkspaceClosed` | WorkspaceRuntime | Navigation Runtime, State Runtime | `{ workspaceId, snapshot }` |
| `WorkspaceSwitched` | WorkspaceRuntime | Navigation Runtime, Intelligence Runtime | `{ fromWorkspaceId, toWorkspaceId, transitionType }` |
| `WorkspaceCached` | WorkspaceRuntime | State Runtime | `{ workspaceId, snapshot }` |
| `WorkspaceRestored` | WorkspaceRuntime | Intelligence Runtime | `{ workspaceId, snapshot }` |

#### Navigation Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `NavigationRequested` | NavigationRuntime | Workspace Runtime | `{ target, source }` |
| `NavigationCompleted` | NavigationRuntime | Command Runtime, Intelligence Runtime | `{ route, workspaceId }` |
| `NavigationBack` | NavigationRuntime | Workspace Runtime | `{ fromRoute, toRoute }` |
| `NavigationForward` | NavigationRuntime | Workspace Runtime | `{ fromRoute, toRoute }` |

#### Scenario Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `ScenarioCommitted` | Scenario Runtime (future) | Context Runtime, Workspace Renderers, Intelligence Runtime | `{ scenarioId, scenarioName, parameters }` |
| `ScenarioReverted` | Scenario Runtime (future) | Context Runtime, Workspace Renderers | `{ scenarioId, previousScenarioId }` |
| `ScenarioCompared` | Scenario Runtime (future) | Workspace Renderers, Graph Runtime | `{ scenarioIds, comparisonMode }` |

#### Forecast Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `ForecastGenerated` | Simulation Runtime (future) | Intelligence Runtime, Workspace Renderers | `{ forecastId, period, confidence }` |
| `ForecastUpdated` | Simulation Runtime (future) | Workspace Renderers | `{ forecastId, changes }` |
| `ForecastInvalidated` | Simulation Runtime (future) | Workspace Renderers, Intelligence Runtime | `{ forecastId, reason }` |

#### Intelligence Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `InsightGenerated` | Intelligence Runtime (future) | Bottom Intelligence Shelf, Right Context Panel | `{ insight }` |
| `InsightAccepted` | Intelligence Runtime (future) | Context Runtime, Workspace Renderers | `{ insightId, actionTaken }` |
| `InsightDismissed` | Intelligence Runtime (future) | Intelligence Runtime | `{ insightId, reason }` |
| `InsightEscalated` | Intelligence Runtime (future) | Executive Intelligence, Modal Layer | `{ insightId, severity }` |

#### Graph Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `GraphNodeSelected` | Graph Runtime (future) | Selection Runtime, Right Context Panel | `{ nodeId, nodeType, relationships }` |
| `GraphOverlayOpened` | Graph Runtime (future) | Overlay Layer | `{ scope, layout }` |
| `GraphOverlayClosed` | Graph Runtime (future) | Overlay Layer | `{ reason }` |

#### Command Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `CommandExecuted` | Command Runtime (future) | Intelligence Runtime, State Runtime | `{ commandId, input, result }` |
| `CommandFailed` | Command Runtime (future) | Status Bar, Intelligence Runtime | `{ commandId, input, error }` |
| `CommandPaletteOpened` | Command Runtime (future) | Overlay Layer | `{ trigger }` |
| `CommandPaletteClosed` | Command Runtime (future) | Overlay Layer | `{ reason }` |

#### Filter Events

| Event | Publisher | Subscribers | Payload |
|-------|-----------|-------------|---------|
| `FilterApplied` | Filter Runtime (future) | Context Runtime, Workspace Renderers | `{ filterId, field, operator, value }` |
| `FilterCleared` | Filter Runtime (future) | Context Runtime, Workspace Renderers | `{ filterId }` |
| `GlobalFilterChanged` | Filter Runtime (future) | Context Runtime, all Workspaces | `{ globalFilters }` |

### 9.4 Event Interface Definition

```typescript
interface RuntimeEvent {
  type: string;
  timestamp: number;
  source: string; // runtime name
  payload: Record<string, unknown>;
}

// Concrete event types
interface SelectionChangedEvent extends RuntimeEvent {
  type: 'SelectionChanged';
  payload: {
    activeEntityId: string | null;
    selectedIds: string[];
    selectionRange: { start: string; end: string } | null;
  };
}

interface TimelineChangedEvent extends RuntimeEvent {
  type: 'TimelineChanged';
  payload: {
    activePeriod: { start: string; end: string; label: string };
    granularity: 'day' | 'week' | 'month' | 'quarter' | 'year';
    comparisonPeriod: { start: string; end: string; label: string } | null;
  };
}

interface WorkspaceOpenedEvent extends RuntimeEvent {
  type: 'WorkspaceOpened';
  payload: {
    workspaceId: string;
    workspaceType: string;
  };
}

interface ScenarioCommittedEvent extends RuntimeEvent {
  type: 'ScenarioCommitted';
  payload: {
    scenarioId: string;
    scenarioName: string;
    parameters: Record<string, unknown>;
  };
}

interface ForecastGeneratedEvent extends RuntimeEvent {
  type: 'ForecastGenerated';
  payload: {
    forecastId: string;
    period: { start: string; end: string };
    confidence: number;
  };
}

interface InsightAcceptedEvent extends RuntimeEvent {
  type: 'InsightAccepted';
  payload: {
    insightId: string;
    actionTaken: string;
  };
}

interface GraphNodeSelectedEvent extends RuntimeEvent {
  type: 'GraphNodeSelected';
  payload: {
    nodeId: string;
    nodeType: string;
    relationships: EntityReference[];
  };
}
```

### 9.5 Event Bus Rules

1. **Fire-and-forget.** Publishers do not wait for subscriber responses.
2. **Synchronous delivery.** Events are delivered synchronously to all subscribers.
3. **No side effects in subscribers.** Subscribers must not modify the event payload.
4. **No circular dependencies.** If Runtime A subscribes to Runtime B's events, Runtime B must not subscribe to Runtime A's events.
5. **Event ordering.** Events are delivered in publication order within a runtime. Cross-runtime ordering is not guaranteed.
6. **Error isolation.** If a subscriber throws, the error is caught and logged. Other subscribers are still notified.
7. **No event storms.** Runtimes must debounce high-frequency events (e.g., `TimelineScrubbed` should be throttled to 100ms).

### 9.6 Event Ownership

| Event | Publisher (Owner) | Responsibility |
|-------|-------------------|----------------|
| `SelectionChanged` | SelectionRuntime | Only SelectionRuntime publishes this event |
| `TimelineChanged` | TimelineRuntime | Only TimelineRuntime publishes this event |
| `WorkspaceOpened` | WorkspaceRuntime | Only WorkspaceRuntime publishes this event |
| `ScenarioCommitted` | Scenario Runtime (future) | Only Scenario Runtime publishes this event |
| `ForecastGenerated` | Simulation Runtime (future) | Only Simulation Runtime publishes this event |
| `InsightAccepted` | Intelligence Runtime (future) | Only Intelligence Runtime publishes this event |
| `GraphNodeSelected` | Graph Runtime (future) | Only Graph Runtime publishes this event |

**Rule:** Each event has exactly one publisher. Multiple runtimes can subscribe, but only the owning runtime publishes.

---

## 10. Future Runtime Roadmap

### 10.1 Overview

The platform currently has four frozen runtimes. The future runtime roadmap defines additional runtimes that will be built on top of the existing platform. Each future runtime follows the same pattern: extends BaseRuntime, uses React context for DI, and communicates via the Runtime Event Bus.

### 10.2 Existing Runtimes (Frozen)

| Runtime | Status | Responsibility |
|---------|--------|----------------|
| Workspace Runtime | Frozen | Workspace registration, activation, lifecycle, caching |
| Selection Runtime | Frozen | Entity selection, multi-select, range selection, highlight |
| Timeline Runtime | Frozen | Temporal context (periods, granularity, comparison, scrubbing) |
| Navigation Runtime | Frozen | Navigation history, breadcrumbs, back/forward |

### 10.3 Future Runtimes

#### Context Runtime

| Attribute | Specification |
|-----------|---------------|
| **Status** | Future (specified in [Part 3](#3-context-runtime-expansion)) |
| **Responsibility** | Compose Selection, Timeline, Workspace, Scenario, Filters, and Active Household states into a single, read-only Context Object |
| **Dependencies** | SelectionRuntime, TimelineRuntime, WorkspaceRuntime, Scenario Runtime, Filter Runtime |
| **Events Published** | `ContextChanged` (when any source state changes) |
| **Events Subscribed** | `SelectionChanged`, `TimelineChanged`, `WorkspaceOpened`, `ScenarioCommitted`, `FilterApplied` |
| **Consumers** | Workspace Renderers, Intelligence Runtime, Graph Runtime, Command Runtime, Renderers |
| **Key Constraint** | Read-only. Never mutates source runtime state. |

#### Graph Runtime

| Attribute | Specification |
|-----------|---------------|
| **Status** | Future (specified in [Part 5](#5-graph-runtime-integration)) |
| **Responsibility** | Investigative relationship exploration between financial entities |
| **Dependencies** | SelectionRuntime, TimelineRuntime, Context Runtime, Capabilities (for graph data) |
| **Events Published** | `GraphNodeSelected`, `GraphOverlayOpened`, `GraphOverlayClosed` |
| **Events Subscribed** | `SelectionChanged`, `TimelineChanged`, `WorkspaceOpened` (closes overlay on switch) |
| **Consumers** | Overlay Layer, Right Context Panel |
| **Key Constraint** | Investigative only. Never the primary surface. Never persists state. |

#### Command Runtime

| Attribute | Specification |
|-----------|---------------|
| **Status** | Future (specified in [Part 6](#6-command-runtime)) |
| **Responsibility** | Command registration, execution, routing, history, natural language parsing, keyboard shortcuts |
| **Dependencies** | NavigationRuntime, WorkspaceRuntime, Context Runtime, Intelligence Runtime |
| **Events Published** | `CommandExecuted`, `CommandFailed`, `CommandPaletteOpened`, `CommandPaletteClosed` |
| **Events Subscribed** | `WorkspaceOpened` (updates quick actions), `SelectionChanged` (updates context-aware commands) |
| **Consumers** | Command HUD, Overlay Layer (command palette) |
| **Key Constraint** | Never executes business logic directly. Routes to appropriate runtimes. |

#### Intelligence Runtime

| Attribute | Specification |
|-----------|---------------|
| **Status** | Future (specified in [Part 4](#4-intelligence-layer)) |
| **Responsibility** | Generate, rank, and surface insights (passive, investigative, executive) |
| **Dependencies** | Context Runtime, Capabilities (for data), Simulation Runtime (for forecasts) |
| **Events Published** | `InsightGenerated`, `InsightAccepted`, `InsightDismissed`, `InsightEscalated` |
| **Events Subscribed** | `SelectionChanged`, `TimelineChanged`, `WorkspaceOpened`, `ForecastGenerated`, `ScenarioCommitted` |
| **Consumers** | Bottom Intelligence Shelf, Right Context Panel, Modal Layer, Overlay Layer |
| **Key Constraint** | Augmentation, not interruption. Anti-overload rules enforced. |

#### Notification Runtime

| Attribute | Specification |
|-----------|---------------|
| **Status** | Future |
| **Responsibility** | Manage user-facing notifications (toasts, badges, notification center) |
| **Dependencies** | Intelligence Runtime, Command Runtime, all runtimes (for status notifications) |
| **Events Published** | `NotificationShown`, `NotificationDismissed`, `NotificationActionTaken` |
| **Events Subscribed** | `InsightEscalated`, `CommandFailed`, `ForecastGenerated` |
| **Consumers** | Status Bar, Overlay Layer (toast) |
| **Key Constraint** | Maximum 3 visible toasts. Auto-dismiss after 5 seconds (non-critical). Critical notifications persist until dismissed. |

**Interface Contract:**

```typescript
interface NotificationRuntime {
  show(notification: Notification): void;
  dismiss(notificationId: string): void;
  getActive(): Notification[];
  getHistory(limit: number): Notification[];
  subscribe(listener: (notification: Notification) => void): () => void;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  duration: number; // ms, 0 = persistent
  actionLabel?: string;
  actionRoute?: string;
  source: string; // runtime name
  timestamp: number;
}
```

#### Simulation Runtime

| Attribute | Specification |
|-----------|---------------|
| **Status** | Future |
| **Responsibility** | Run financial simulations (cash flow forecasts, scenario projections, what-if analysis) |
| **Dependencies** | Context Runtime, Capabilities (for historical data), Scenario Runtime |
| **Events Published** | `ForecastGenerated`, `ForecastUpdated`, `ForecastInvalidated`, `SimulationStarted`, `SimulationCompleted` |
| **Events Subscribed** | `ScenarioCommitted`, `TimelineChanged`, `FilterApplied` |
| **Consumers** | Intelligence Runtime, Workspace Renderers (forecast workspaces) |
| **Key Constraint** | All monetary values in paise. Deterministic given same inputs. No probabilistic outputs without confidence intervals. |

**Interface Contract:**

```typescript
interface SimulationRuntime {
  runForecast(params: ForecastParams): Promise<ForecastResult>;
  runScenario(params: ScenarioParams): Promise<ScenarioResult>;
  runWhatIf(params: WhatIfParams): Promise<WhatIfResult>;
  cancel(simulationId: string): void;
  getActiveSimulations(): Simulation[];
  subscribe(listener: (event: SimulationEvent) => void): () => void;
}

interface ForecastParams {
  householdId: string;
  periodStart: string;
  periodEnd: string;
  confidenceLevel: number; // 0.0–1.0
  scenarioId?: string;
}

interface ForecastResult {
  forecastId: string;
  period: { start: string; end: string };
  projectedCashflowPaise: number;
  confidence: number;
  dataPoints: ForecastDataPoint[];
}
```

### 10.4 Runtime Dependency Graph

```
                    ┌─────────────────┐
                    │  Context Runtime  │
                    │   (read-only)    │
                    └────────┬────────┘
                             │
         ┌───────────┬───────┼────────┬────────────┐
         │           │       │        │            │
         ▼           ▼       ▼        ▼            ▼
  ┌──────────┐ ┌─────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐
  │ Graph    │ │ Command │ │ Intelligence│ │ Simulation│ │Notification│
  │ Runtime  │ │ Runtime │ │ Runtime    │ │ Runtime   │ │ Runtime  │
  └──────────┘ └─────────┘ └────────────┘ └───────────┘ └──────────┘
```

**Rules:**
- Context Runtime is the foundation for all future runtimes.
- Future runtimes depend on Context Runtime, not on each other directly.
- If Runtime A needs data from Runtime B, it subscribes to B's events via the Event Bus.
- No circular dependencies between runtimes.

---

## 11. Anti-Patterns

### 11.1 Overview

The following patterns are **explicitly forbidden**. Any code that exhibits these patterns must be refactored immediately.

### 11.2 Forbidden Patterns

#### 11.2.1 Page-Level Business Logic

**Forbidden:** Business logic (financial calculations, data transformations, state management) in page components or route handlers.

**Why:** Pages are composition surfaces. They should compose workspaces and shell regions, not compute financial results.

**Correct:** Business logic lives in Capabilities and Mappers. Pages compose.

---

#### 11.2.2 DTO Transformations in UI

**Forbidden:** Transforming DTOs (backend data transfer objects) in frontend components.

**Why:** DTOs are backend contracts. Transforming them in the UI couples the frontend to backend internals and bypasses the Mapper stage.

**Correct:** DTOs are transformed to ViewModels by Mappers. UI only consumes ViewModels.

```
// FORBIDDEN
function TransactionCard({ dto }: { dto: TransactionDTO }) {
  const amount = dto.amount / 100; // DTO transformation in UI
  ...
}

// CORRECT
function TransactionCard({ viewModel }: { viewModel: TransactionViewModel }) {
  const amount = viewModel.amountPaise; // ViewModel already mapped
  ...
}
```

---

#### 11.2.3 Local Duplicated State

**Forbidden:** Storing domain state (selection, filters, timeline, workspace state) in component-level `useState` or `useReducer`.

**Why:** This creates duplicate state that can diverge from the runtime source of truth.

**Correct:** All domain state lives in runtimes. Components read from runtimes via Context/RuntimeProvider.

---

#### 11.2.4 Multiple Runtime Ownership

**Forbidden:** Two runtimes owning the same state. For example, both WorkspaceRuntime and a workspace component managing the "active workspace" state.

**Why:** Dual ownership leads to race conditions, stale state, and debugging nightmares.

**Correct:** Each piece of state has exactly one owning runtime. Other runtimes subscribe to events.

---

#### 11.2.5 Graph-First Navigation

**Forbidden:** Using the Graph Runtime as the primary navigation surface. Starting the user in the graph. Replacing workspace navigation with graph navigation.

**Why:** The graph is an investigative tool, not a navigation paradigm. Graph-first navigation disorients users and breaks the Hybrid Matrix.

**Correct:** The graph is always invoked from a workspace, selection, or insight. It opens as an overlay. It never replaces the workspace surface.

---

#### 11.2.6 Dashboard Card Sprawl

**Forbidden:** Adding unlimited dashboard cards without governance. Creating a "dashboard" that is a grid of disconnected widgets with no coherence.

**Why:** Card sprawl creates cognitive overload, violates the "workspaces are primary" principle, and produces an unmaintainable UI.

**Correct:** Dashboards are workspaces. They follow the same lifecycle, caching, and renderer rules. Cards are limited (max 6 per dashboard). Each card has a defined renderer and data source.

---

#### 11.2.7 Capability Bypassing

**Forbidden:** Calling backend APIs directly from components, hooks (outside capabilities), or runtimes (outside capabilities).

**Why:** This bypasses the canonical data flow pipeline, skips caching/retry logic, and creates inconsistent data states.

**Correct:** All backend data access goes through Capabilities. Capabilities invoke Mappers and expose ViewModels.

---

#### 11.2.8 Direct API Calls

**Forbidden:** Using `fetch`, `axios`, or any HTTP client directly in components, renderers, or shell regions.

**Why:** Direct API calls bypass React Query caching, retry logic, and the Capability abstraction.

**Correct:** All API calls are in Capabilities. Capabilities use React Query for data fetching.

---

#### 11.2.9 Renderer Duplication

**Forbidden:** Implementing the same business logic in multiple renderers. For example, a "Transaction Card" and a "Transaction Table Row" both computing the same derived value.

**Why:** Duplicated logic diverges over time, creating inconsistent displays of the same data.

**Correct:** Each Financial Object has one ViewModel. All renderers (Card, Table, Timeline, etc.) consume the same ViewModel. No business logic in renderers.

---

#### 11.2.10 Loose Float Monetary Values

**Forbidden:** Using JavaScript `number` or `float` for monetary values in the frontend.

**Why:** Floating-point arithmetic introduces rounding errors. Financial data must be exact.

**Correct:** All monetary values are integers representing absolute paise (₹1.00 = 100 paise). Division uses safe decimal handlers.

---

#### 11.2.11 `as any`, `@ts-ignore`, `@ts-nocheck`

**Forbidden:** Using TypeScript escape hatches (`as any`, `@ts-ignore`, `@ts-nocheck`).

**Why:** These disable type safety, which is the primary value of TypeScript.

**Correct:** Fix the types. If a type is wrong, fix the type definition. Never suppress.

---

#### 11.2.12 FinanceDB Import Outside Repositories

**Forbidden:** Importing `FinanceDB` or `get_db()` outside of `src/repositories/`.

**Why:** This violates the Repository Boundary Rule and couples non-repository code to database internals.

**Correct:** Only files under `src/repositories/` import FinanceDB. Routers and engines use repository interfaces.

---

### 11.3 Audit Protocol

Any code review or architecture review must check for these anti-patterns. If detected:

1. **Block the PR.**
2. **Document the violation** (which pattern, which file, which lines).
3. **Require refactoring** before approval.
4. **Update tests** to prevent regression.

---

## 12. Implementation Sequencing

### 12.1 Overview

Implementation is structured as **milestones**, not weeks. Each milestone is a state machine (see [Part 17](#17-milestone-state-machine)) with a 4-section format (see [Part 18](#18-milestone-template)): **Objective**, **Implementation**, **Validation**, **Freeze Decision**. Every execution cycle follows the fixed algorithm in [Part 14](#14-never-skip). Progress state lives exclusively in `docs/EXECUTION_STATE.md` — this architecture document never records current progress. No milestone modifies frozen platform APIs.

### 12.2 Milestone Progression

```
Milestone 1: Shell Skeleton and Region Contracts
    ↓
Milestone 2: Workspace Host and Lifecycle
    ↓
Milestone 3: Renderer Registry and Base Renderers
    ↓
Milestone 4: Context Runtime (Interface Only)
    ↓
Milestone 5: Command Runtime
    ↓
Milestone 6: Intelligence Layer (Passive)
    ↓
Milestone 7: Graph Runtime Integration
    ↓
Milestone 8: Intelligence Layer (Investigative and Executive)
    ↓
Milestone 9: Runtime Event Bus
    ↓
Milestone 10: Future Runtime Completion
```

Each milestone progresses through the state machine in [Part 17](#17-milestone-state-machine): `NOT_STARTED → IN_PROGRESS → VALIDATED → COMPLETE → FROZEN`. Milestones may also enter `BLOCKED` if a dependency prevents progress.

---

### Milestone 1: Shell Skeleton and Region Contracts

**State:** NOT_STARTED

**Objective:**
- Establish the permanent shell composition with all 8 regions
- Define region interfaces and ownership boundaries
- Implement resize and responsive behavior

**Implementation:**
- Shell composition with all 8 regions (Global Header, Command HUD, Left Nav Rail, Workspace Host, Right Context Panel, Bottom Intelligence Shelf, Overlay Layer, Modal Layer)
- Region interface contracts (TypeScript interfaces)
- Resize behavior for all regions
- Responsive rules for all breakpoints
- Status Bar

**Validation:**
- [ ] All 8 shell regions are present and mounted
- [ ] No shell region contains business logic
- [ ] No shell region makes direct API calls
- [ ] All regions resize correctly at 1280px, 768px, and 375px widths
- [ ] Region visibility persists across sessions
- [ ] Z-index hierarchy is correct (no overlapping issues)
- [ ] `ruff check .` passes (backend)
- [ ] `mypy .` passes (backend)
- [ ] `npx tsc --noEmit` passes (frontend)

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Shell skeleton is stable and all regions are present
- Region contracts are frozen
- No business logic in shell regions

---

### Milestone 2: Workspace Host and Lifecycle

**State:** NOT_STARTED

**Objective:**
- Implement the Workspace Host with full lifecycle management
- Implement workspace caching (LRU, max 5)
- Implement workspace switching with cross-fade transitions
- Implement state snapshot and restoration

**Implementation:**
- Workspace Host component
- Workspace lifecycle state machine (Registered → Activated → Mounted → Cached → Restored → Deactivated → Destroyed)
- LRU cache implementation (max 5 cached workspaces)
- State snapshot (scroll position, filters, selection, sort)
- Cross-fade transition (150ms)
- Cold-mount loading state (skeleton)

**Validation:**
- [ ] Workspace switches are instant when cached
- [ ] Cold-mount shows skeleton (not spinner)
- [ ] State snapshot preserves scroll, filters, selection, sort
- [ ] Cache evicts LRU when full (max 5)
- [ ] Cross-fade transition is 150ms
- [ ] No workspace state in local component state
- [ ] All state managed by WorkspaceRuntime
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Workspace Host is stable
- Lifecycle is fully implemented
- Caching and restoration work correctly

---

### Milestone 3: Renderer Registry and Base Renderers

**State:** NOT_STARTED

**Objective:**
- Implement the Renderer Registry
- Implement base renderers for all 7 modes (Card, Table, Timeline, Graph Node, Inspector, Mini Widget, Chart)
- Ensure single ViewModel → multiple renderers with no duplicated logic

**Implementation:**
- Renderer Registry implementation
- 7 renderer mode interfaces
- Base renderers for Transaction (as reference implementation)
- Renderer selection logic (workspace default, user preference, context density)
- Density level support (Compact, Comfortable, Spacious)

**Validation:**
- [ ] Renderer Registry can register and retrieve renderers
- [ ] Transaction ViewModel renders in all 7 modes
- [ ] No business logic in any renderer
- [ ] All renderers consume the same ViewModel
- [ ] Density levels work correctly
- [ ] Renderer selection logic is correct
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Renderer Registry is stable
- All 7 renderer modes are implemented
- Transaction serves as the reference renderer pattern

---

### Milestone 4: Context Runtime (Interface Only)

**State:** NOT_STARTED

**Objective:**
- Define the Context Runtime interface
- Define the Context Object composition
- Define context consumers and their contracts
- No implementation — interface specification only

**Implementation:**
- ContextObject interface
- ContextRuntime interface
- Context composition rules documented
- Context consumer contracts documented

**Validation:**
- [ ] ContextObject interface is complete
- [ ] All source runtimes are referenced
- [ ] No implementation code exists
- [ ] Interface is reviewed and approved
- [ ] No frozen APIs are modified

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Context Runtime interface is frozen
- Ready for implementation in a future milestone

---

### Milestone 5: Command Runtime

**State:** NOT_STARTED

**Objective:**
- Implement the Command Runtime
- Implement command registration, execution, and routing
- Implement keyboard shortcuts
- Implement command palette overlay
- Implement recent commands and pinned workflows

**Implementation:**
- CommandRuntime implementation
- Command registration system
- Command routing (navigation, workspace action, intelligence, graph, workflow, quick action)
- Keyboard shortcut system
- Command palette overlay
- Recent commands (last 10, session-scoped)
- Pinned workflows (persistent)

**Validation:**
- [ ] Commands can be registered and executed
- [ ] Keyboard shortcuts work globally
- [ ] Command palette opens with `Cmd+K`
- [ ] Recent commands are tracked
- [ ] Pinned workflows persist across sessions
- [ ] Command routing is correct (no direct execution)
- [ ] No business logic in Command Runtime (routing only)
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Command Runtime is stable
- All command sources are functional
- Command palette is operational

---

### Milestone 6: Intelligence Layer (Passive)

**State:** NOT_STARTED

**Objective:**
- Implement Passive Intelligence tier
- Surface passive insights in Bottom Intelligence Shelf and Right Context Panel
- Implement insight ranking and deduplication

**Implementation:**
- Passive insight generation (from Capability data)
- Bottom Intelligence Shelf content (passive insights)
- Right Context Panel default content (passive insights when no selection)
- Insight ranking algorithm (recency + severity + impact)
- Insight deduplication
- Insight dismissal (session-scoped suppression)

**Validation:**
- [ ] Passive insights appear in Intelligence Shelf
- [ ] Maximum 5 passive insights visible
- [ ] Insights are ranked correctly
- [ ] Dismissed insights are suppressed
- [ ] No notification overload
- [ ] Passive insights never block interaction
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Passive Intelligence is stable
- Anti-overload rules are enforced
- Intelligence Shelf is operational

---

### Milestone 7: Graph Runtime Integration

**State:** NOT_STARTED

**Objective:**
- Implement Graph Runtime as an investigative overlay
- Implement graph invocation from selection, command, and insight
- Implement evidence visualization
- Implement relationship exploration

**Implementation:**
- Graph Runtime implementation
- Graph overlay (full workspace area)
- Graph context panel mode (1-hop, limited to 20 nodes)
- Evidence panel with traceable links
- Relationship types (all 8 types from Part 5)
- Graph synchronization with SelectionRuntime and TimelineRuntime

**Validation:**
- [ ] Graph opens as overlay (never replaces workspace)
- [ ] Graph is scoped to Context Object
- [ ] Node selection updates SelectionRuntime
- [ ] Evidence links navigate to source workspace
- [ ] Graph state is ephemeral (not persisted)
- [ ] Graph never becomes navigation surface
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Graph Runtime is stable
- Investigative-only constraint is enforced
- Evidence visualization is operational

---

### Milestone 8: Intelligence Layer (Investigative and Executive)

**State:** NOT_STARTED

**Objective:**
- Implement Investigative Intelligence tier
- Implement Executive Intelligence tier
- Implement insight drill-down actions
- Implement executive modal confirmations

**Implementation:**
- Investigative insight generation (on-demand, user-initiated)
- Drill-down actions (navigate to workspace with pre-selected entity)
- Executive insight generation (threshold breach, anomaly detection)
- Executive modal (critical severity, requires action)
- Executive toast (warning severity, informational)
- Audit trail for executive decisions

**Validation:**
- [ ] Investigative insights are user-initiated only
- [ ] Drill-down actions navigate correctly
- [ ] Maximum 1 executive insight active at a time
- [ ] Critical insights require user action (modal)
- [ ] Warning insights are informational (toast)
- [ ] Executive decisions are logged
- [ ] Anti-overload rules are enforced
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- All three intelligence tiers are operational
- Anti-overload rules are fully enforced
- Audit trail is complete

---

### Milestone 9: Runtime Event Bus

**State:** NOT_STARTED

**Objective:**
- Implement the Runtime Event Bus
- Implement all event types from Part 9
- Ensure event ownership is correct (one publisher per event)
- Implement error isolation and debouncing

**Implementation:**
- RuntimeEventBus implementation
- All event type definitions
- Event publisher/subscriber wiring for all runtimes
- Error isolation (subscriber errors don't block other subscribers)
- Debouncing for high-frequency events

**Validation:**
- [ ] All events from Part 9 are defined
- [ ] Each event has exactly one publisher
- [ ] Subscribers receive events synchronously
- [ ] Subscriber errors are caught and logged
- [ ] High-frequency events are debounced
- [ ] No circular dependencies between runtimes
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- Event Bus is stable
- All runtimes are wired
- Event ownership is correct

---

### Milestone 10: Future Runtime Completion

**State:** NOT_STARTED

**Objective:**
- Implement Context Runtime (from Milestone 4 interface)
- Implement Notification Runtime
- Implement Simulation Runtime
- Complete Scenario Runtime (if not already implemented)

**Implementation:**
- ContextRuntime implementation (compose all source runtimes)
- NotificationRuntime implementation (toasts, badges, notification center)
- SimulationRuntime implementation (forecasts, scenarios, what-if)
- Scenario Runtime (scenario commit, revert, compare)

**Validation:**
- [ ] ContextRuntime composes all source runtimes
- [ ] Context Object is read-only
- [ ] NotificationRuntime shows max 3 toasts
- [ ] Non-critical notifications auto-dismiss after 5s
- [ ] SimulationRuntime uses paise for all monetary values
- [ ] Simulations are deterministic given same inputs
- [ ] No frozen APIs are modified
- [ ] `ruff check .` passes
- [ ] `mypy .` passes
- [ ] `npx tsc --noEmit` passes

**Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status.
- All future runtimes are implemented
- Runtime dependency graph is correct
- All runtimes communicate via Event Bus
- No circular dependencies

---

### 12.3 Milestone Constraints

1. **No frozen API modifications.** No milestone may modify the frozen platform APIs (Capability → Mapper → ViewModel, RuntimeProvider, existing runtimes, Workspace Registration, endpoint contracts, monetary conventions, application routing).
2. **Sequential where possible.** Milestones are designed to be sequential. Later milestones depend on earlier ones.
3. **Parallelizable within milestones.** Tasks within a milestone can be parallelized.
4. **Validation gates are mandatory.** No milestone is complete until all validation checklist items pass.
5. **Exit criteria are binding.** A milestone cannot be declared complete until all exit criteria are met.

---

## 13. Execution Rules (AI Operating Manual)

This section defines the **fixed algorithm** every AI agent must follow when working with this architecture. It is embedded in the architecture document so that any future AI can bootstrap from these two files alone:

1. `docs/FINANCIAL_OS_SHELL_ARCHITECTURE.md` — the immutable constitution
2. `docs/EXECUTION_STATE.md` — the mutable progress ledger

### Startup Sequence (Before Any Code Is Written)

1. **Read** `docs/FINANCIAL_OS_SHELL_ARCHITECTURE.md` in full.
2. **Read** `docs/EXECUTION_STATE.md`.
3. **Determine** the current milestone and its state.
4. **Validate** the previous milestone (run all checks — see [Part 15](#15-startup-validation) and [Part 16](#16-end-of-run-validation)).
5. **If validation fails:** log the failure in `EXECUTION_STATE.md` under "Blocked Tasks," then stop.
6. **If validation passes:** begin implementing the next unfinished capability within the current milestone.
7. **After each capability:** run validation.
8. **When all checklist items pass:** update milestone state to `VALIDATED`.
9. **When exit criteria are met:** update milestone state to `COMPLETE`.
10. **Update** `EXECUTION_STATE.md` with new state, modified files, and next immediate action.
11. **Stop only at a milestone boundary.** Never stop mid-capability.

### Execution Constraints

- **No architecture modifications.** The architecture document must not change. If the AI discovers a gap, it logs it as "Deferred Items" in `EXECUTION_STATE.md`.
- **No frozen API modifications.** No milestone may modify frozen platform APIs (Section 12.3).
- **State drives progress, not time.** Milestones advance by state, not by elapsed time.
- **One milestone at a time.** Never start a new milestone until the current one is `COMPLETE`.

---

## 14. Never Skip

This section is a literal checklist. **Every execution cycle must satisfy every item before writing any code.** If any item cannot be satisfied, the AI must stop and log the blocker.

### Before Writing Any Code

- [ ] Read `FINANCIAL_OS_SHELL_ARCHITECTURE.md`
- [ ] Read `EXECUTION_STATE.md`
- [ ] Determine current milestone and its state
- [ ] Validate previous milestone (`ruff`, `mypy`, `tsc`, tests, anti-pattern checks)
- [ ] Confirm current milestone is `IN_PROGRESS` (flip it from `NOT_STARTED` if needed)
- [ ] Identify the first incomplete capability / checklist item

### After Writing Any Code

- [ ] Run compile checks (`tsc --noEmit`, `ruff check`, `mypy`)
- [ ] Run relevant tests
- [ ] Verify anti-pattern compliance (Section 11.2)
- [ ] Verify no frozen API modifications
- [ ] Verify no architecture document modifications
- [ ] Update `EXECUTION_STATE.md` (state, files, next action)
- [ ] Stop only at a milestone boundary

### On Session Start (Every New Session)

- [ ] Read both files
- [ ] Reconstruct project state from `EXECUTION_STATE.md`
- [ ] Validate the milestone boundary you stopped at
- [ ] Resume from the exact next capability

---

## 15. Startup Validation

Every execution cycle must begin by running the following validation checks **before** writing any code. Failures must be logged in `EXECUTION_STATE.md` under "Blocked Tasks."

### 15.1 TypeScript Validation

```bash
cd frontend && npx tsc --noEmit
```

**Pass condition:** Zero errors, zero warnings.

### 15.2 Backend Validation

```bash
cd backend && ./venv/bin/python3 -m ruff check .
cd backend && ./venv/bin/python3 -m mypy .
```

**Pass condition:** Zero errors from both tools.

### 15.3 Frozen Architecture Violation Check

Scan the working tree for any file that:

| Violation | Detection |
|-----------|-----------|
| Capability bypass (direct API call) | `rg --type py "fetch\(|axios\.|requests\.get\(" frontend/components/ frontend/app/` |
| DTO in UI (no Mapper) | `rg --type py "dto\.|DTO" frontend/components/ frontend/app/` excluding `lib/mappers/` and `lib/capabilities/` |
| `as any` / `@ts-ignore` / `@ts-nocheck` | `rg "as any|@ts-ignore|@ts-nocheck" frontend/ --type tsx --type ts` |
| FinanceDB import outside repositories | `rg "FinanceDB|get_db\(" frontend/ --type tsx --type ts` excluding `repositories/` |
| Page-level business logic | Manual review of `app/*/page.tsx` for calculation logic |

**Pass condition:** Zero violations.

### 15.4 Runtime Violation Check

Scan for:

| Violation | Detection |
|-----------|-----------|
| Multiple runtime ownership | `rg "useState|useReducer" frontend/components/ --type tsx` for domain state in components |
| Local duplicated state | `rg "selectedIds|activeWorkspace|timelinePeriod" frontend/components/ --type tsx` excluding runtime files |
| Graph-first navigation | Verify `GraphRuntime` is only invoked from overlays |

**Pass condition:** Zero violations.

### 15.5 Anti-Pattern Violation Check

Cross-reference with [Section 11.2](#112-forbidden-patterns). Every AI run must verify:

- [ ] No page-level business logic
- [ ] No DTO transformations in UI
- [ ] No local duplicated state
- [ ] No multiple runtime ownership
- [ ] No graph-first navigation
- [ ] No dashboard card sprawl
- [ ] No capability bypassing
- [ ] No direct API calls
- [ ] No renderer duplication
- [ ] No loose float monetary values
- [ ] No `as any`, `@ts-ignore`, `@ts-nocheck`
- [ ] No FinanceDB import outside repositories

**Pass condition:** All anti-pattern checks pass.

---

## 16. End-of-Run Validation

Every execution cycle must end with the following steps **before** the AI stops.

### 16.1 Compile Checks

- [ ] `cd frontend && npx tsc --noEmit` — zero errors
- [ ] `cd backend && ./venv/bin/python3 -m ruff check .` — zero errors
- [ ] `cd backend && ./venv/bin/python3 -m mypy .` — zero errors

### 16.2 Test Validation

- [ ] Run relevant test suite for the milestone
- [ ] All tests pass
- [ ] No test regressions introduced

### 16.3 Milestone Checklist

- [ ] Every checklist item in the current milestone passes
- [ ] Every exit criterion is satisfied

### 16.4 Architecture Compliance

- [ ] No frozen platform APIs modified (Section 12.3)
- [ ] No anti-patterns introduced (Section 11.2)
- [ ] No architecture document modifications
- [ ] All new code references the Context Object, not individual runtimes (post-Milestone 4)

### 16.5 Execution State Update

- [ ] Update milestone state in `EXECUTION_STATE.md`
- [ ] Log all Modified / Created / Deleted files
- [ ] Set "Next Immediate Action" to the next capability
- [ ] Log any "Blocked Tasks" or "Known Technical Debt"
- [ ] Commit with conventional commit message referencing the milestone

**The AI must not stop until all five steps pass.**

---

## 17. Milestone State Machine

Each milestone progresses through a deterministic state machine. The state is stored in `EXECUTION_STATE.md`.

### State Diagram

```
NOT_STARTED
     ↓
IN_PROGRESS
     ↓ (all checklist items pass + startup/end-of-run validation)
VALIDATED
     ↓ (all exit criteria satisfied + freeze decision made)
COMPLETE
     ↓ (architecture review confirms stability)
FROZEN
```

### States

| State | Description | Transition In | Transition Out |
|-------|-------------|---------------|----------------|
| **`NOT_STARTED`** | Milestone not yet begun. Prerequisites not verified. | — | `IN_PROGRESS` |
| **`IN_PROGRESS`** | Implementation underway. Some checklist items incomplete. | `NOT_STARTED` | `VALIDATED`, `BLOCKED` |
| **`BLOCKED`** | Implementation blocked by a dependency, error, or violation. | any | `IN_PROGRESS` |
| **`VALIDATED`** | All checklist items pass. Compile and validation checks pass. | `IN_PROGRESS` | `COMPLETE`, `BLOCKED` |
| **`COMPLETE`** | All exit criteria satisfied. Freeze decision recorded. | `VALIDATED` | `FROZEN` |
| **`FROZEN`** | Milestone is permanently locked. No further modifications. | `COMPLETE` | — |

### State Transition Rules

1. **`NOT_STARTED → IN_PROGRESS`:** AI reads both files, validates previous milestone, and begins first capability.
2. **`IN_PROGRESS → VALIDATED`:** Every checklist item passes, startup validation + end-of-run validation pass.
3. **`IN_PROGRESS → BLOCKED`:** A blocker is discovered (dependency missing, violation found, error encountered).
4. **`VALIDATED → COMPLETE`:** All exit criteria are verified as met, freeze decision is recorded.
5. **`VALIDATED → BLOCKED`:** A blocker is discovered during final validation.
6. **`COMPLETE → FROZEN`:** Architecture review team confirms milestone is stable and should not change.
7. **`BLOCKED → IN_PROGRESS`:** Blocker is resolved.

### State Machine Interface

```typescript
type MilestoneState =
  | 'NOT_STARTED'
  | 'IN_PROGRESS'
  | 'BLOCKED'
  | 'VALIDATED'
  | 'COMPLETE'
  | 'FROZEN';

interface MilestoneStateRecord {
  milestoneId: string;
  state: MilestoneState;
  stateChangedAt: number; // epoch ms
  stateChangedBy: string; // AI session identifier
  blockerReason?: string; // present when state is BLOCKED
}
```

---

## 18. Milestone Template

Every milestone in Section 12 follows this 4-section template. The template is the contract; each milestone fills it.

### Template Structure

```
### Milestone N: <Title>

**State:** NOT_STARTED

**Objective:**
<One sentence describing what this milestone achieves.>

**Implementation:**
<List of deliverables — code files, interfaces, wiring. Not a task list; a specification of what exists when this milestone is done.>

**Validation:**
<Checklist of checks that must pass. Each check is a line with a checkbox.>

**Freeze Decision:**
- **Can this milestone be modified later?** YES or NO
- **Reason:** <One sentence explaining why.>
```

### Milestone Format Rules

1. **State is always first.** It is the single source of truth for progress (lives in `EXECUTION_STATE.md`, not here).
2. **Objective is one sentence.** It defines the milestone's purpose without prescribing implementation steps.
3. **Implementation lists deliverables, not tasks.** It describes the end state, not the process.
4. **Validation is a checklist.** Each item must be objectively verifiable.
5. **Freeze Decision is binary (YES/NO) with a reason.** This prevents unnecessary rewrites.

### Milestone Format Mapping (Legacy → Current)

| Legacy Header (Section 12) | Current Header (Template) |
|---------------------------|--------------------------|
| **State:** NOT_STARTED

**Objective:** | **Objective:** |
| **Implementation:** | **Implementation:** |
| **Validation:** | **Validation:** |
| **Freeze Decision:**
- **Can this milestone be modified later?** See EXECUTION_STATE.md for current freeze status. | **Freeze Decision:** |

Each milestone in Section 12 has been updated to use the **State** + 4-section format. The "Exit Criteria" content has been moved into "Freeze Decision" with the YES/NO/Reason structure.

---

## 19. Rollback Support

Each milestone records its modified files for deterministic rollback. This data lives in `EXECUTION_STATE.md` (not in this architecture document). This section defines the **format** only.

### Rollback Metadata Format

```yaml
# Per-milestone in EXECUTION_STATE.md
milestone: 1
state: NOT_STARTED
files:
  modified:
    - path: frontend/app/layout.tsx
      reason: "Added shell region composition"
  created:
    - path: frontend/components/os-shell/app-shell.tsx
      reason: "Shell Host component"
  deleted:
    - path: frontend/components/dashboard/old-dashboard.tsx
      reason: "Replaced by workspace pattern"
```

### Rollback Procedure

When a milestone needs to be rolled back:

1. **Read** `EXECUTION_STATE.md` for the milestone's file lists.
2. **For created files:** `git rm <path>` (restore to pre-milestone state).
3. **For modified files:** `git checkout <commit-before-milestone> -- <path>`.
4. **For deleted files:** `git checkout <commit-before-milestone> -- <path>`.
5. **Validate** that the rollback is clean (`tsc`, `ruff`, `mypy`).
6. **Update** `EXECUTION_STATE.md` to mark the milestone as `BLOCKED` with reason "Rollback initiated."

### Rollback Invariant

- **Each milestone's file changes are fully reversible.** No milestone should delete files that are used by other code without creating replacement files in the same milestone.
- **Rollback scope is per-milestone.** Rolling back Milestone N does not affect Milestones 1–N-1.

---

## Appendix A: Frozen Platform API Reference

| API | Location | Status |
|-----|----------|--------|
| Capability → Mapper → ViewModel | `frontend/lib/capabilities/`, `backend/src/core/mappers/` | Frozen |
| RuntimeProvider | `frontend/lib/runtime/` | Frozen |
| Workspace Runtime | `frontend/lib/runtime/WorkspaceRuntime.ts` | Frozen |
| Selection Runtime | `frontend/lib/runtime/SelectionRuntime.ts` | Frozen |
| Timeline Runtime | `frontend/lib/runtime/TimelineRuntime.ts` | Frozen |
| Navigation Runtime | `frontend/lib/runtime/NavigationRuntime.ts` | Frozen |
| Workspace Registration | `frontend/lib/workspace-registry/` | Frozen |
| Canonical Endpoint Contracts | `backend/src/routers/` | Frozen |
| Monetary Conventions | Paise-based integers (₹1.00 = 100 paise) | Frozen |
| Application Routing | `frontend/app/` (Next.js App Router) | Frozen |

---

## Appendix B: Shell Layout Constants

| Constant | Value | Source |
|----------|-------|--------|
| `--left-rail-width` | 180px | `financial-os.css` |
| `--left-rail-collapsed-width` | 56px | `financial-os.css` |
| `--command-bar-height` | 44px | `financial-os.css` |
| `--timeline-height` | 88px | `financial-os.css` |
| `--inspector-min-width` | 280px | `financial-os.css` |
| `--inspector-max-width` | 420px | `financial-os.css` |
| `--status-bar-height` | 24px | `financial-os.css` |
| `--global-header-height` | 48px | This specification |

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Shell** | The permanent application container that composes all regions |
| **Region** | A defined area of the shell (e.g., Left Nav Rail, Workspace Host) |
| **Workspace** | A primary surface for a financial domain (e.g., Transactions, Loans) |
| **Workspace Host** | The mounting surface that manages workspace lifecycle |
| **Workspace Renderer** | Workspace-scoped composition layer |
| **Runtime** | A state management module that is the source of truth for a domain |
| **Capability** | A React Query hook that fetches data and exposes ViewModels |
| **Mapper** | A pure function that transforms DTOs to ViewModels |
| **ViewModel** | A UI-ready data model derived from DTOs |
| **Renderer** | A pure presentational component that maps a ViewModel to UI |
| **Context Object** | A read-only, derived composition of all runtime states |
| **Financial Object** | Any domain entity that has a ViewModel (Transaction, Account, etc.) |
| **Paise** | The smallest monetary unit (₹1.00 = 100 paise). All monetary values are integers. |
| **Hybrid Matrix** | The architectural principle where Workspaces, Timeline, Graph, Command, and Intelligence are balanced axes |
| **Investigative** | A mode of interaction that is user-initiated and exploratory |
| **Passive** | A mode of intelligence that is ambient and non-blocking |
| **Executive** | A mode of intelligence that demands attention and requires action |

---

*This document is the permanent composition architecture for ClariFin_OS. It must remain stable throughout the lifetime of the project. All future frontend development must conform to this specification.*
