/**
 * Financial Graph Runtime - Public API
 *
 * Central export for the Stage 4B Financial Graph Runtime.
 * Every workspace can import from here to export into the graph.
 *
 * Architecture: Workspace → Graph Adapter → Runtime → Money Graph
 */

// ===== Core Types =====
export type {
  NodeType,
  EdgeType,
  GraphNode,
  GraphEdge,
  GraphMetadata,
  GraphResult,
  GraphQuery,
  GraphFilter,
  GraphSelection,
  GraphFocus,
  GraphMetrics,
  Evidence,
  Calculation,
  Source,
  TracePath,
  ExplainabilityPayload,
  GraphEventType,
  GraphEvent,
  GraphAdapter,
  RuntimeAPI,
} from './types';

export { GRAPH_RUNTIME_VERSION } from './types';

// ===== Adapter Infrastructure =====
export {
  BaseAdapter,
  EmptyAdapter,
  scopedId,
  edgeId,
  buildMetadata,
  mergeGraphResults,
} from './adapter';

// ===== Registry =====
export {
  GraphRegistry,
  graphRegistry,
  RegistryError,
  AdapterNotFoundError,
  AdapterAlreadyRegisteredError,
} from './registry';

// ===== Event Bus =====
export {
  GraphEventBus,
  graphEventBus,
  type GraphEventHandler,
  type Subscription,
} from './event-bus';

// ===== Traversal Engine =====
export {
  GraphTraversalEngine,
  graphTraversal,
  type TraversalOptions,
  type TraversalResult,
} from './traversal';

// ===== Selection Engine =====
export {
  GraphSelectionEngine,
  graphSelection,
  type SelectionChangeHandler,
  type FocusChangeHandler,
} from './selection';

// ===== Metrics Engine =====
export {
  GraphMetricsEngine,
  graphMetrics,
} from './metrics';

// ===== Explainability Runtime =====
export {
  ExplainabilityRuntime,
  explainabilityRuntime,
  type ExplainabilityProvider,
} from './explainability';

// ===== Main Runtime =====
export {
  FinancialGraphRuntime,
  financialGraphRuntime,
  type RuntimeConfig,
} from './runtime';

// ===== Workspace Adapters =====
export {
  TransactionGraphAdapter,
  transactionGraphAdapter,
} from './adapters/transaction';

export {
  AccountsGraphAdapter,
  accountsGraphAdapter,
} from './adapters/accounts';

export {
  CashflowGraphAdapter,
  cashflowGraphAdapter,
} from './adapters/cashflow';

export {
  LoansGraphAdapter,
  loansGraphAdapter,
} from './adapters/loans';

export {
  CardsGraphAdapter,
  cardsGraphAdapter,
} from './adapters/cards';

export {
  InvestmentsGraphAdapter,
  investmentsGraphAdapter,
} from './adapters/investments';

export {
  BehaviourGraphAdapter,
  behaviourGraphAdapter,
} from './adapters/behaviour';

export {
  ReconciliationGraphAdapter,
  reconciliationGraphAdapter,
} from './adapters/reconciliation';

export {
  ForecastGraphAdapter,
  forecastGraphAdapter,
} from './adapters/forecast';