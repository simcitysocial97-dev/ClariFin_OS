/**
 * Runtime Types - Shared state contracts for all runtimes.
 */

// ===== Workspace =====
export type WorkspaceName =
  | 'dashboard'
  | 'transactions'
  | 'accounts'
  | 'cards'
  | 'loans'
  | 'investments'
  | 'net-worth'
  | 'cashflow'
  | 'behaviour'
  | 'forecast'
  | 'reconciliation'
  | 'settings'
  | 'command-center';

export type SurfaceType =
  | 'GRAPH'
  | 'TABLE'
  | 'SANKEY'
  | 'MATRIX'
  | 'HEATMAP'
  | 'TIMELINE'
  | 'CHARTS'
  | 'FORM'
  | 'INVESTIGATION'
  | 'SIMULATION'
  | 'CONFIGURATION';

export interface WorkspaceConfig {
  name: WorkspaceName;
  label: string;
  icon: string;
  deepLink: string;
  defaultSurface: SurfaceType;
  supportedCommands: string[];
  supportedFilters: string[];
  supportedSelections: string[];
}

export interface WorkspaceState {
  current: WorkspaceName;
  breadcrumbs: string[];
  title: string;
  dateRange: { from?: string; to?: string } | null;
  member: string | null;
  filters: Record<string, unknown>;
}

// ===== Selection =====
export type SelectionEntity =
  | { type: 'transaction'; id: string }
  | { type: 'loan'; id: string }
  | { type: 'card'; id: string }
  | { type: 'investment'; id: string }
  | { type: 'account'; id: string }
  | { type: 'reconciliation'; id: number }
  | { type: 'event'; id: string };

export interface SelectionState {
  active: SelectionEntity | null;
  multi: Set<string>;
  history: SelectionEntity[];
}

// ===== Timeline =====
export type TimeGranularity = 'month' | 'quarter' | 'year';

export interface TimelinePosition {
  date: string | null;
  granularity: TimeGranularity;
  comparisonPeriod: { from?: string; to?: string } | null;
}

// ===== Navigation =====
export interface NavigationEntry {
  path: string;
  timestamp: number;
  workspace?: WorkspaceName;
}

export interface NavigationState {
  history: NavigationEntry[];
  currentIndex: number;
}

// ===== Runtime Composed State =====
export interface RuntimeState {
  workspace: WorkspaceState;
  selection: SelectionState;
  timeline: TimelinePosition;
  navigation: NavigationState;
}
