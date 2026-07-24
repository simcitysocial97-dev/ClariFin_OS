/**
 * Command Center - Stage 5 Command Center Platform
 *
 * Public API exports for the Command Center module.
 */

export {
  CommandCenterRuntime,
  commandCenterRuntime,
  type PanelId,
  type PanelState,
  type LayoutConfig,
} from './runtime';

// Re-export WorkspaceRegistration from workspace module
export {
  type WorkspaceRegistration,
} from '../workspace';

export {
  LayoutRuntime,
  layoutRuntime,
  type PanelPosition,
  type LayoutSnapshot,
} from './layout';

export {
  NavigationRuntime,
  navigationRuntime,
  type NavigationTarget,
  type NavigationHistory,
} from './navigation';

// ===== Intelligence Integration =====
export {
  type IntelligenceResult,
  type IntelligenceContext,
  type IntelligenceConfig,
  type Insight,
  type Alert,
  type Recommendation,
  type RiskScore,
  type OpportunityScore,
  type Goal,
  type HealthScore,
} from '../intelligence';

// ===== Simulation Integration =====
export {
  type SimulationResult,
  type SimulationContext,
  type SimulationConfig,
} from '../simulation';

// ===== Stage 7.5 Runtime Consolidation =====
export {
  CommandPalette,
  commandPalette,
  createDefaultCommands,
  type Command,
  type CommandCategory,
  type CommandGroup,
  type CommandPaletteState,
} from './command-palette';