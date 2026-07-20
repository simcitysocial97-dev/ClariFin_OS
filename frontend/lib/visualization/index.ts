/**
 * Visualization Module - Stage 8C Financial OS Visual System
 *
 * Public API for visualization components.
 */

// Registry
export {
  VisualizationRegistry,
  visualizationRegistry,
  type VisualizationComponent,
  type VisualizationRegistration,
} from './registry';

// Graph Model
export {
  FinancialGraphModel,
  type RenderNode,
  type RenderEdge,
  type RenderGraph,
  type LayoutOptions,
} from '../graph/financial-graph-model';

// Graph Renderer
export { GraphRenderer } from '@/components/graph/renderer/graph-renderer';

// Visualization Primitives
export { MoneyGraph } from '@/components/visualization/money-graph/money-graph';
export { SankeyEngine, type SankeyData, type SankeyNode, type SankeyLink } from '@/components/visualization/sankey/sankey-engine';
export { TimelineEngine, type TimelineItem } from '@/components/visualization/timeline/timeline-engine';
export { AllocationMatrix, type AllocationItem } from '@/components/visualization/allocation-matrix/allocation-matrix';
export { WaterfallEngine, type WaterfallItem } from '@/components/visualization/waterfall/waterfall-engine';
export { ScenarioEngine, type ScenarioItem } from '@/components/visualization/scenario/scenario-engine';
export { EvidenceTree, type EvidenceItem } from '@/components/visualization/evidence-tree/evidence-tree';

// UI Primitives
export { MetricTile } from '@/components/primitives/metric-tile/metric-tile';
export { EntityCard } from '@/components/primitives/entity-card/entity-card';
export { ConfidenceBadge } from '@/components/primitives/confidence-badge/confidence-badge';
export { RiskBadge } from '@/components/primitives/risk-badge/risk-badge';
export { InspectorBlock } from '@/components/primitives/inspector-block/inspector-block';

// Platform
export { keyboardShortcuts, createKeyboardHandler } from '@/lib/platform/keyboard';
export { getGraphAriaLabel, getNodeAriaLabel, focusElement, isKeyboardNavigation } from '@/lib/platform/accessibility';
export { getAnimationClass, getTransitionClass, getStaggerDelay } from '@/lib/platform/animation';