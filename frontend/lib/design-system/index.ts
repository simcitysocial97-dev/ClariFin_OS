/**
 * Design System - Stage 8E Financial OS Visual Language
 *
 * Public API for the design system.
 * Single source of truth for all financial OS visual tokens.
 */

// Tokens
export { spacing, spacingPx, layoutConstants, LEFT_RAIL_WIDTH, COMMAND_BAR_HEIGHT, TIMELINE_HEIGHT, STATUS_BAR_HEIGHT, INSPECTOR_MIN, INSPECTOR_MAX, GRID_GAP, px } from './spacing';
export type { SpacingToken } from './spacing';
export { borderRadius, borderWidth, opacity, zIndex, duration, easing, fontFamily, fontSize, fontWeight, lineHeight, shadow, screen } from './tokens';

// Elevations
export { elevations, elevationClasses } from './elevations';
export type { Elevation } from './elevations';

// Typography
export { financialTypography, typographyClasses } from './typography';

// Colors
export {
  financialColors,
  nodeTypeColors,
  edgeTypeColors,
  confidenceColors,
  riskColors,
  uiColors,
} from './colors';

// Motion
export { financialMotion, motionClasses, keyframes } from './motion';

// Density
export { densityConfig, densityClasses, DEFAULT_DENSITY, getDensityConfig, getDensityClass } from './density';
export type { DensityLevel, DensityConfig } from './density';

// Financial Semantics
export {
  nodeGrammar,
  edgeGrammar,
  getNodeGrammar,
  getEdgeGrammar,
  getConfidenceColor,
  getRiskColor,
  type NodeShape,
  type NodeGrammar,
  type EdgeGrammar,
} from './financial-semantics';