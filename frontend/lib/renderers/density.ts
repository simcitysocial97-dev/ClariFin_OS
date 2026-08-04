/**
 * Density Resolution — Architecture Section 7.7
 *
 * Workspaces select the appropriate renderer mode based on:
 * - Workspace type (each workspace has a default renderer mode)
 * - User preference (can switch between table/card/chart views)
 * - Context density (compact → table, spacious → card)
 * - Selection state (selected entity → inspector)
 * - Timeline active (timeline mode in bottom shelf)
 */

import type { DensityLevel, RendererMode } from './types';

// ===== Workspace defaults =====
const WORKSPACE_DEFAULT_MODES: Record<string, RendererMode> = {
  transactions: 'table',
  accounts: 'card',
  cards: 'card',
  loans: 'card',
  investments: 'chart',
  'net-worth': 'card',
  cashflow: 'table',
  behaviour: 'chart',
  forecast: 'chart',
  reconciliation: 'table',
  dashboard: 'card',
  settings: 'table',
  'command-center': 'table',
};

// ===== Density-to-mode mapping =====
const DENSITY_MODE_MAP: Record<DensityLevel, RendererMode> = {
  compact: 'table',
  comfortable: 'table',
  spacious: 'card',
};

// ===== Selection-driven mode override =====
const SELECTION_OVERRIDE_MODE: RendererMode = 'inspector';

/**
 * Determine which renderer mode to use for a given context.
 * Priority: selection > user-preference > context-density > workspace-default
 */
export function selectRendererMode(
  objectType: string,
  options: {
    workspaceDefault?: RendererMode;
    userPreference?: RendererMode | null;
    density?: DensityLevel;
    hasSelection?: boolean;
    isTimelineActive?: boolean;
  } = {},
): RendererMode {
  // Selection overrides everything
  if (options.hasSelection) {
    return SELECTION_OVERRIDE_MODE;
  }

  // Timeline mode
  if (options.isTimelineActive) {
    return 'timeline';
  }

  // User preference
  if (options.userPreference) {
    return options.userPreference;
  }

  // Context density
  if (options.density) {
    return DENSITY_MODE_MAP[options.density];
  }

  // Workspace default
  if (options.workspaceDefault) {
    return options.workspaceDefault;
  }

  // Fallback: workspace default from registry
  const fallback = WORKSPACE_DEFAULT_MODES[objectType];
  if (fallback) return fallback;

  return 'table';
}

/**
 * Get the appropriate density for a workspace view.
 */
export function resolveDensity(options: {
  userPreference?: DensityLevel | null;
  objectType?: string;
  isTablePreferred?: boolean;
}): DensityLevel {
  if (options.userPreference) return options.userPreference;
  if (options.isTablePreferred) return 'compact';
  return 'comfortable';
}
