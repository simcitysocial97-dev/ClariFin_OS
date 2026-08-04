/**
 * Context Runtime — Stage 10 Financial Operating System
 *
 * Composes SelectionRuntime, TimelineRuntime, and WorkspaceRuntime states
 * into a single, derived, read-only Context Object.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §3
 */

import { runtimeEventBus } from '../event-bus';
import { selectionRuntime } from '../runtime/selection-runtime';
import { timelineRuntime } from '../runtime/timeline-runtime';
import { workspaceRuntime } from '../runtime/workspace-runtime';
import type {
  ContextObject,
  ContextRuntime,
  SelectionContext,
  TimelineContext,
  WorkspaceContext,
  ScenarioContext,
  FilterState,
  GlobalFilterState,
  HouseholdContext,
} from './types';

// ─── Default Context ──────────────────────────────────────────────────────────

const DEFAULT_SELECTION: SelectionContext = {
  activeEntityId: null,
  activeEntityType: null,
  selectedIds: [],
  selectionRange: null,
  multiSelect: false,
};

const DEFAULT_TIMELINE: TimelineContext = {
  activePeriod: { start: '', end: '', label: '' },
  granularity: 'month',
  comparisonPeriod: null,
};

const DEFAULT_WORKSPACE: WorkspaceContext = {
  activeWorkspaceId: 'dashboard',
  activeWorkspaceType: 'dashboard',
  workspaceFilters: {},
  workspaceSortConfig: null,
};

const DEFAULT_SCENARIO: ScenarioContext = {
  activeScenarioId: null,
  scenarioName: null,
  scenarioParameters: null,
  isBaseline: true,
};

const DEFAULT_FILTERS: { activeFilters: FilterState[]; globalFilters: GlobalFilterState } = {
  activeFilters: [],
  globalFilters: { accountIds: null, categoryIds: null, entityIds: null, minAmount: null, maxAmount: null },
};

const DEFAULT_HOUSEHOLD: HouseholdContext = {
  householdId: '',
  householdName: 'My Household',
  members: [],
  accounts: [],
};

const DEFAULT_METADATA = {
  timestamp: Date.now(),
  version: '1.0.0',
  sessionId: crypto.randomUUID?.() ?? `session-${Date.now()}`,
};

// ─── State ────────────────────────────────────────────────────────────────────

let _context: ContextObject = {
  selection: DEFAULT_SELECTION,
  timeline: DEFAULT_TIMELINE,
  workspace: DEFAULT_WORKSPACE,
  scenario: DEFAULT_SCENARIO,
  filters: DEFAULT_FILTERS,
  household: DEFAULT_HOUSEHOLD,
  metadata: { ...DEFAULT_METADATA },
};

const _listeners = new Set<(context: ContextObject) => void>();
const _selectors = new Map<symbol, { fn: <T>(ctx: ContextObject) => T; lastResult: unknown; lastVersion: number }>();
let _version = 0;

function notify() {
  _version++;
  _listeners.forEach(fn => fn(_context));
}

// ─── Recompute ────────────────────────────────────────────────────────────────

function recompute(): void {
  const sel = selectionRuntime.state;
  const tl = timelineRuntime.state;
  const ws = workspaceRuntime.state;

  _context = {
    selection: {
      activeEntityId: sel.active ? String(sel.active.id) : null,
      activeEntityType: sel.active ? String(sel.active.type) : null,
      selectedIds: Array.from(sel.multi),
      selectionRange: null,
      multiSelect: sel.multi.size > 0,
    },
    timeline: {
      activePeriod: {
        start: tl.date ?? '',
        end: tl.date ?? '',
        label: tl.date ? formatPeriodLabel(tl.date) : '',
      },
      granularity: mapGranularity(tl.granularity),
      comparisonPeriod: tl.comparisonPeriod
        ? {
            start: tl.comparisonPeriod.from ?? '',
            end: tl.comparisonPeriod.to ?? '',
            label: '',
          }
        : null,
    },
    workspace: {
      activeWorkspaceId: ws.current,
      activeWorkspaceType: ws.current,
      workspaceFilters: ws.filters,
      workspaceSortConfig: null,
    },
    scenario: DEFAULT_SCENARIO,
    filters: DEFAULT_FILTERS,
    household: DEFAULT_HOUSEHOLD,
    metadata: { ..._context.metadata, timestamp: Date.now() },
  };

  notify();
}

function formatPeriodLabel(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    const year = d.getFullYear();
    const month = d.toLocaleString('en-US', { month: 'short' });
    return `${month} ${year}`;
  } catch {
    return dateStr;
  }
}

function mapGranularity(g: string): 'day' | 'week' | 'month' | 'quarter' | 'year' {
  switch (g) {
    case 'month': return 'month';
    case 'quarter': return 'quarter';
    case 'year': return 'year';
    default: return 'month';
  }
}

// ─── Public API ───────────────────────────────────────────────────────────────

function getContext(): ContextObject {
  return _context;
}

function subscribe(listener: (context: ContextObject) => void): () => void {
  _listeners.add(listener);
  return () => {
    _listeners.delete(listener);
  };
}

function select<T>(selector: (context: ContextObject) => T): T {
  const result = selector(_context);
  return result;
}

// ─── Event Bus Integration ────────────────────────────────────────────────────

function initEventSubscription() {
  // Subscribe to all relevant runtime events
  runtimeEventBus.subscribe('SelectionChanged', recompute);
  runtimeEventBus.subscribe('SelectionCleared', recompute);
  runtimeEventBus.subscribe('TimelineChanged', recompute);
  runtimeEventBus.subscribe('TimelineGranularityChanged', recompute);
  runtimeEventBus.subscribe('WorkspaceSwitched', recompute);
  runtimeEventBus.subscribe('WorkspaceOpened', recompute);
  runtimeEventBus.subscribe('NavigationCompleted', recompute);

  return () => {
    // Unsubscribe handled by event bus — no cleanup needed here
  };
}

// ─── Reset ────────────────────────────────────────────────────────────────────

function reset() {
  _context = {
    selection: DEFAULT_SELECTION,
    timeline: DEFAULT_TIMELINE,
    workspace: DEFAULT_WORKSPACE,
    scenario: DEFAULT_SCENARIO,
    filters: DEFAULT_FILTERS,
    household: DEFAULT_HOUSEHOLD,
    metadata: { ...DEFAULT_METADATA, sessionId: `session-${Date.now()}` },
  };
  _version = 0;
  _selectors.clear();
  notify();
}

// ─── Singleton Export ──────────────────────────────────────────────────────────

export const contextRuntime: ContextRuntime = {
  getContext,
  subscribe,
  select,
};

export function resetContextRuntime() {
  reset();
}

// ─── Init ─────────────────────────────────────────────────────────────────────
initEventSubscription();
recompute();
