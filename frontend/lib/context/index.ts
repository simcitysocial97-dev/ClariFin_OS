/**
 * Context Runtime — Public API
 *
 * Composes Selection, Timeline, Workspace states into a read-only ContextObject.
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §3
 */

export type {
  FilterOperator,
  FilterScope,
  FilterState,
  GlobalFilterState,
  HouseholdMember,
  AccountSummary,
  SelectionContext,
  TimeGranularity,
  PeriodLabel,
  TimelineContext,
  WorkspaceSortConfig,
  WorkspaceContext,
  ScenarioContext,
  HouseholdContext,
  ContextMetadata,
  ContextObject,
} from './types';

export type { ContextRuntime } from './types';

export {
  contextRuntime,
  resetContextRuntime,
} from './runtime';
