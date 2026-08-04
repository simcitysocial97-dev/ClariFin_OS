/**
 * Transaction Renderers — Reference Implementation
 *
 * All 7 renderer modes for the Transaction Financial Object.
 * Each renderer consumes the same RenderableViewModel<TransactionViewModel>.
 * No duplicated business logic — only presentational mapping.
 *
 * Registers with RendererRegistry at module load time.
 */

import { getRendererRegistry } from '@/lib/renderers';
import { adaptTransaction } from '@/lib/renderers/adapters/transaction-adapter';
import { TransactionCard } from './card';
import { TransactionTable } from './table';
import { TransactionTimeline } from './timeline';
import { TransactionGraphNode } from './graph-node';
import { TransactionInspector } from './inspector';
import { TransactionMiniWidget } from './mini-widget';
import { TransactionChart } from './chart';

// ===== Registry key =====
const OBJECT_TYPE = 'transaction';

// ===== Register all 7 renderer modes =====
export function registerTransactionRenderers(): void {
  const registry = getRendererRegistry();

  // Card (default: spacious)
  registry.register(
    OBJECT_TYPE,
    'card',
    TransactionCard,
    { defaultDensity: 'spacious' },
  );

  // Table (default: compact)
  registry.register(
    OBJECT_TYPE,
    'table',
    TransactionTable,
    { defaultDensity: 'compact' },
  );

  // Timeline (default: comfortable)
  registry.register(
    OBJECT_TYPE,
    'timeline',
    TransactionTimeline,
    { defaultDensity: 'comfortable' },
  );

  // Graph Node (default: compact)
  registry.register(
    OBJECT_TYPE,
    'graph-node',
    TransactionGraphNode,
    { defaultDensity: 'compact' },
  );

  // Inspector (default: comfortable)
  registry.register(
    OBJECT_TYPE,
    'inspector',
    TransactionInspector,
    { defaultDensity: 'comfortable' },
  );

  // Mini Widget (default: compact)
  registry.register(
    OBJECT_TYPE,
    'mini-widget',
    TransactionMiniWidget,
    { defaultDensity: 'compact' },
  );

  // Chart (default: comfortable)
  registry.register(
    OBJECT_TYPE,
    'chart',
    TransactionChart,
    { defaultDensity: 'comfortable' },
  );
}

// ===== Export adapter for direct ViewModel → Renderable conversion =====
export { adaptTransaction };

// ===== Re-export individual renderers for direct use =====
export { TransactionCard };
export { TransactionTable };
export { TransactionTimeline };
export { TransactionGraphNode };
export { TransactionInspector };
export { TransactionMiniWidget };
export { TransactionChart };
