/**
 * Graph Types - Stage 4B Financial Graph Runtime
 *
 * Core type definitions for the Financial Graph Runtime.
 * These types are the foundation for all graph operations:
 * nodes, edges, metadata, queries, and results.
 *
 * All monetary values are in paise (₹1.00 = 100 paise) for financial determinism.
 */

// ===== Node Types =====
export type NodeType =
  | 'transaction'
  | 'account'
  | 'cashflow_month'
  | 'cashflow_category'
  | 'loan'
  | 'amortization_entry'
  | 'credit_card'
  | 'credit_card_statement'
  | 'investment'
  | 'holding'
  | 'behaviour_score'
  | 'spending_pattern'
  | 'reconciliation_statement'
  | 'discrepancy'
  | 'forecast_projection'
  | 'forecast_scenario'
  | 'net_worth_snapshot'
  | 'net_worth_breakdown'
  | 'merchant'
  | 'category'
  | 'institution';

// ===== Edge Types =====
export type EdgeType =
  | 'belongs_to'        // Transaction → Account
  | 'categorized_as'    // Transaction → Category
  | 'from_merchant'     // Transaction → Merchant
  | 'at_institution'    // Account → Institution
  | 'composes'          // NetWorth → Account/Loan/Card
  | 'affects_cashflow'  // Transaction → CashflowMonth
  | 'amortizes'         // Loan → AmortizationEntry
  | 'has_statement'     // CreditCard → Statement
  | 'has_holding'       // Investment → Holding
  | 'impacts_score'     // Transaction → BehaviourScore
  | 'reconciles'        // Transaction → ReconciliationStatement
  | 'projects'          // Forecast → Projection
  | 'scenario_of'       // ForecastScenario → Forecast
  | 'traces_to'         // Evidence → Source
  | 'references'        // Cross-workspace reference
  | 'derived_from'      // Derived metric → Source node
  | 'related_to';       // Generic relationship

// ===== Graph Node =====
export interface GraphNode {
  /** Unique node identifier (workspace-specific prefix + id) */
  id: string;
  /** Node type for classification */
  type: NodeType;
  /** Human-readable label */
  label: string;
  /** Workspace origin (e.g., 'transactions', 'accounts', 'loans') */
  workspace: string;
  /** Monetary value in paise (if applicable) */
  value_paise?: number;
  /** Date associated with this node (ISO format) */
  date?: string;
  /** Status or state label */
  status?: string;
  /** Confidence score (0-100) if applicable */
  confidence?: number;
  /** Additional metadata key-value pairs */
  metadata: Record<string, unknown>;
  /** Deep link to the source workspace view */
  deep_link?: string;
}

// ===== Graph Edge =====
export interface GraphEdge {
  /** Unique edge identifier */
  id: string;
  /** Source node ID */
  source: string;
  /** Target node ID */
  target: string;
  /** Edge type for classification */
  type: EdgeType;
  /** Human-readable label */
  label: string;
  /** Weight for traversal algorithms (default: 1) */
  weight: number;
  /** Additional metadata */
  metadata: Record<string, unknown>;
}

// ===== Graph Metadata =====
export interface GraphMetadata {
  /** Total node count */
  node_count: number;
  /** Total edge count */
  edge_count: number;
  /** Node count by type */
  nodes_by_type: Record<NodeType, number>;
  /** Edge count by type */
  edges_by_type: Record<EdgeType, number>;
  /** Workspace breakdown */
  workspaces: string[];
  /** Build timestamp (ISO format) */
  built_at: string;
  /** Runtime version */
  version: string;
}

// ===== Graph Result =====
export interface GraphResult {
  /** Array of graph nodes */
  nodes: GraphNode[];
  /** Array of graph edges */
  edges: GraphEdge[];
  /** Graph metadata */
  metadata: GraphMetadata;
}

// ===== Graph Query =====
export interface GraphQuery {
  /** Filter by node types */
  node_types?: NodeType[];
  /** Filter by edge types */
  edge_types?: EdgeType[];
  /** Filter by workspace */
  workspace?: string;
  /** Filter by date range */
  date_range?: { from: string; to: string };
  /** Filter by value range (paise) */
  value_range?: { min: number; max: number };
  /** Search text in labels and metadata */
  search?: string;
  /** Maximum results to return */
  limit?: number;
  /** Offset for pagination */
  offset?: number;
}

// ===== Graph Filter =====
export interface GraphFilter {
  /** Include only these node IDs */
  include_nodes?: string[];
  /** Exclude these node IDs */
  exclude_nodes?: string[];
  /** Include only these edge types */
  include_edge_types?: EdgeType[];
  /** Minimum confidence threshold (0-100) */
  min_confidence?: number;
  /** Maximum depth for traversal */
  max_depth?: number;
}

// ===== Graph Selection =====
export interface GraphSelection {
  /** Selected node IDs */
  node_ids: string[];
  /** Selected edge IDs */
  edge_ids: string[];
  /** Whether all nodes are selected */
  all_selected: boolean;
  /** Timestamp of selection (ISO format) */
  selected_at: string;
}

// ===== Graph Focus =====
export interface GraphFocus {
  /** Focused node ID */
  node_id: string;
  /** Depth of surrounding context */
  depth: number;
  /** Included edge types for context */
  edge_types?: EdgeType[];
}

// ===== Graph Metrics =====
export interface GraphMetrics {
  /** Total nodes */
  node_count: number;
  /** Total edges */
  edge_count: number;
  /** Graph density (0-1) */
  density: number;
  /** Average degree */
  average_degree: number;
  /** Number of connected components */
  component_count: number;
  /** Node count by workspace */
  nodes_by_workspace: Record<string, number>;
  /** Edge count by type */
  edges_by_type: Record<EdgeType, number>;
  /** Total monetary value in paise */
  total_value_paise: number;
  /** Node count by type */
  nodes_by_type: Record<NodeType, number>;
}

// ===== Explainability Types =====
export interface Evidence {
  /** Evidence type */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface Calculation {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values */
  inputs: Record<string, unknown>;
  /** Output values */
  outputs: Record<string, unknown>;
}

export interface Source {
  /** Source identifier */
  id: string;
  /** Source type (file, api, calculation) */
  type: string;
  /** Source label */
  label: string;
  /** Source timestamp (ISO format) */
  timestamp: string;
}

export interface TracePath {
  /** Ordered list of node IDs in the trace */
  path: string[];
  /** Edge types traversed */
  edge_types: EdgeType[];
  /** Total steps in the trace */
  steps: number;
  /** Whether the trace is complete */
  complete: boolean;
}

export interface ExplainabilityPayload {
  /** Node ID being explained */
  node_id: string;
  /** Evidence items */
  evidence: Evidence[];
  /** Calculation steps */
  calculations: Calculation[];
  /** Source references */
  sources: Source[];
  /** Overall confidence (0-100) */
  confidence: number;
  /** Trace path through the graph */
  trace_path?: TracePath;
}

// ===== Event Types =====
export type GraphEventType =
  | 'node:added'
  | 'node:updated'
  | 'node:removed'
  | 'edge:added'
  | 'edge:updated'
  | 'edge:removed'
  | 'graph:built'
  | 'graph:invalidated'
  | 'selection:changed'
  | 'focus:changed';

export interface GraphEvent {
  /** Event type */
  type: GraphEventType;
  /** Event payload */
  payload: unknown;
  /** Event timestamp (ISO format) */
  timestamp: string;
  /** Source that emitted the event */
  source: string;
}

// ===== Adapter Interface =====
export interface GraphAdapter<TViewModel> {
  /** Unique adapter name matching workspace name */
  readonly name: string;
  /** Export the ViewModel as a GraphResult */
  export(viewModel: TViewModel): GraphResult;
  /** Build nodes from the ViewModel */
  buildNodes(viewModel: TViewModel): GraphNode[];
  /** Build edges from the ViewModel */
  buildEdges(viewModel: TViewModel, nodes: GraphNode[]): GraphEdge[];
  /** Build metadata for the result */
  buildMetadata(nodes: GraphNode[], edges: GraphEdge[]): GraphMetadata;
}

// ===== Runtime API Types =====
export interface RuntimeAPI {
  /** Build the full financial graph from all registered adapters */
  build(): GraphResult;
  /** Trace money flow between two nodes */
  traceMoney(from: string, to: string): TracePath | null;
  /** Find related nodes to a given node */
  related(nodeId: string, depth?: number): GraphResult;
  /** Extract a subgraph based on a filter */
  subgraph(filter: GraphFilter): GraphResult;
  /** Get graph metrics */
  metrics(): GraphMetrics;
  /** Focus on a specific node with surrounding context */
  focus(nodeId: string, depth?: number): GraphResult;
  /** Get current selection */
  selection(): GraphSelection;
}

// ===== Version =====
export const GRAPH_RUNTIME_VERSION = '1.0.0';