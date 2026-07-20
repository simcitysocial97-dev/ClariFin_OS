/**
 * Design System - Stage 8C Financial OS Visual System
 *
 * Public API for the design system.
 */

// Tokens
export { spacing, borderRadius, borderWidth, opacity, zIndex, duration, easing, fontFamily, fontSize, fontWeight, lineHeight, shadow, screen } from './tokens';

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