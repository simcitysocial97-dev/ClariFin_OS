/**
 * Renderer Module — Stage 8C Financial Operating System Shell
 *
 * Central export for the Renderer Registry system.
 * Architecture Section 7.
 *
 * Pipeline: Capability → Mapper → ViewModel → RenderableViewModel → Renderer
 */

// Core types and registry
export {
  RendererRegistry,
  getRendererRegistry,
  resetRendererRegistry,
} from './registry';

export type { RegisteredRenderer } from './types';

export {
  selectRendererMode,
  resolveDensity,
} from './density';

export {
  type DensityLevel,
  type RendererMode,
  type MonetaryValue,
  type EntityReference,
  type EvidenceLink,
  type SelectionState,
  type RendererAction,
  type TemporalContext,
  type RenderableViewModel,
  type RendererProps,
  type RendererComponent,
  type RendererSelection,
} from './types';

// Adapter utilities
export { adaptTransaction } from './adapters/transaction-adapter';

// Transaction reference implementation
export {
  registerTransactionRenderers,
  TransactionCard,
  TransactionTable,
  TransactionTimeline,
  TransactionGraphNode,
  TransactionInspector,
  TransactionMiniWidget,
  TransactionChart,
} from '@/components/renderers/transaction';
