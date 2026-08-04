/**
 * Context Runtime — Stage 10 Financial Operating System
 *
 * The Context Runtime composes multiple runtime states into a single,
 * derived, read-only Context Object. It does not replace existing runtimes —
 * it reads from them and provides a unified view that workspaces, renderers,
 * and intelligence modules can consume.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §3
 */

// ─── Filter State ────────────────────────────────────────────────────────────

export type FilterOperator =
  | 'eq'
  | 'neq'
  | 'gt'
  | 'lt'
  | 'gte'
  | 'lte'
  | 'in'
  | 'between'
  | 'contains';

export type FilterScope = 'workspace' | 'global';

export interface FilterState {
  id: string;
  field: string;
  operator: FilterOperator;
  value: unknown;
  scope: FilterScope;
}

export interface GlobalFilterState {
  accountIds: string[] | null;
  categoryIds: string[] | null;
  entityIds: string[] | null;
  minAmount: number | null; // paise
  maxAmount: number | null; // paise
}

// ─── Household ────────────────────────────────────────────────────────────────

export interface HouseholdMember {
  memberId: string;
  name: string;
  role: string;
}

export interface AccountSummary {
  accountId: string;
  accountName: string;
  accountType: string;
  bankName: string;
  balancePaise: number;
}

// ─── Selection Context ────────────────────────────────────────────────────────

export interface SelectionContext {
  activeEntityId: string | null;
  activeEntityType: string | null;
  selectedIds: string[];
  selectionRange: { start: string; end: string } | null;
  multiSelect: boolean;
}

// ─── Timeline Context ─────────────────────────────────────────────────────────

export type TimeGranularity = 'day' | 'week' | 'month' | 'quarter' | 'year';

export interface PeriodLabel {
  start: string; // ISO date
  end: string;   // ISO date
  label: string; // e.g., "FY 2025-26 Q3"
}

export interface TimelineContext {
  activePeriod: PeriodLabel;
  granularity: TimeGranularity;
  comparisonPeriod: PeriodLabel | null;
}

// ─── Workspace Context ────────────────────────────────────────────────────────

export interface WorkspaceSortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

export interface WorkspaceContext {
  activeWorkspaceId: string;
  activeWorkspaceType: string;
  workspaceFilters: Record<string, unknown>;
  workspaceSortConfig: WorkspaceSortConfig | null;
}

// ─── Scenario Context ─────────────────────────────────────────────────────────

export interface ScenarioContext {
  activeScenarioId: string | null;
  scenarioName: string | null;
  scenarioParameters: Record<string, unknown> | null;
  isBaseline: boolean; // true when no scenario is active
}

// ─── Household Context ────────────────────────────────────────────────────────

export interface HouseholdContext {
  householdId: string;
  householdName: string;
  members: HouseholdMember[];
  accounts: AccountSummary[];
}

// ─── Metadata ─────────────────────────────────────────────────────────────────

export interface ContextMetadata {
  timestamp: number;
  version: string;
  sessionId: string;
}

// ─── Context Object ───────────────────────────────────────────────────────────

/**
 * The Context Object is the single, derived, read-only representation
 * of the user's current operational context. It is composed by the
 * Context Runtime from multiple runtime states.
 *
 * Workspaces, Renderers, and Intelligence modules consume this object
 * to adapt their behavior without directly coupling to individual runtimes.
 *
 * Composition sources:
 *   - selection: SelectionRuntime
 *   - timeline: TimelineRuntime
 *   - workspace: WorkspaceRuntime + WorkspaceStateSnapshot
 *   - scenario: ScenarioState (future runtime)
 *   - filters: FilterState from Filters Runtime
 *   - household: Active household state
 *   - metadata: Session-scoped bookkeeping
 */
export interface ContextObject {
  selection: SelectionContext;
  timeline: TimelineContext;
  workspace: WorkspaceContext;
  scenario: ScenarioContext;
  filters: {
    activeFilters: FilterState[];
    globalFilters: GlobalFilterState;
  };
  household: HouseholdContext;
  metadata: ContextMetadata;
}

// ─── Context Runtime Interface ────────────────────────────────────────────────

/**
 * The Context Runtime reads from all existing runtimes and composes
 * the Context Object. It is a read-only derived state — it never
 * mutates the source runtimes.
 *
 * COMPOSITION RULES:
 *   1. Read-only: Never writes to source runtimes.
 *   2. Derived: All fields computed from source runtime state.
 *   3. Memoized: Recomputed only when a source changes.
 *   4. Single source of truth: Each field maps to exactly one source runtime.
 *   5. No duplication: Stores no state absent from source runtimes.
 *
 * CONTEXT CONSUMERS:
 *   - Workspace Renderers: Adapt rendering based on active period, filters, scenario
 *   - Intelligence Layer: Generate insights scoped to active household, period, selection
 *   - Graph Runtime: Filter graph to active household, period, selected entities
 *   - Command Runtime: Suggest commands relevant to active workspace, selection, period
 *   - Renderers: Adapt density, columns, and detail level based on context
 */
export interface ContextRuntime {
  /**
   * Returns the current Context Object.
   * Recomputes only when a source runtime state changes.
   */
  getContext(): ContextObject;

  /**
   * Subscribe to context changes.
   * Called whenever any source runtime state changes.
   * Returns an unsubscribe function.
   */
  subscribe(listener: (context: ContextObject) => void): () => void;

  /**
   * Returns a memoized selector result.
   * Workspaces use this to subscribe to specific slices.
   */
  select<T>(selector: (context: ContextObject) => T): T;
}
