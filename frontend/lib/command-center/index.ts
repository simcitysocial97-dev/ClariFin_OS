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
  type WorkspaceRegistration,
} from './runtime';

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
