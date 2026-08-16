/**
 * Renderer Types — Architecture Section 7
 *
 * Every Financial Object's ViewModel implements RenderableViewModel.
 * A single ViewModel is consumed by 7 renderer modes with no duplicated logic.
 */

// ===== Density Levels =====
export type DensityLevel = 'compact' | 'comfortable' | 'spacious';

// ===== Renderer Modes =====
export type RendererMode =
  | 'card'
  | 'table'
  | 'timeline'
  | 'graph-node'
  | 'inspector'
  | 'mini-widget'
  | 'chart';

// ===== Monetary Value =====
export interface MonetaryValue {
  label: string;
  valuePaise: number;
  isPositive: boolean;
  format: 'currency' | 'percentage' | 'plain';
}

// ===== Entity Reference (for graph rendering) =====
export interface EntityReference {
  entityId: string;
  entityType: string;
  label: string;
  relationshipType: string;
}

// ===== Evidence Link =====
export interface EvidenceLink {
  label: string;
  sourceType: 'transaction' | 'statement' | 'reconciliation' | 'forecast';
  sourceId: string;
  confidence: number;
}

// ===== Selection State =====
export interface SelectionState {
  isSelected: boolean;
  isHighlighted: boolean;
  isFocused: boolean;
}

// ===== Renderer Action =====
export interface RendererAction {
  type: 'select' | 'navigate' | 'drill-down' | 'edit' | 'delete' | 'expand';
  payload?: Record<string, unknown>;
}

// ===== Temporal Context =====
export interface TemporalContext {
  date: string;
  period?: string;
}

// ===== RenderableViewModel (interface every Financial Object must implement) =====
export interface RenderableViewModel<TData> {
  /** Unique identifier for the entity */
  id: string;

  /** Entity type (e.g., 'transaction', 'account') */
  type: string;

  /** Human-readable label */
  label: string;

  /** Core data payload (the ViewModel itself) */
  data: TData;

  /** Monetary values in paise (never floats) */
  monetaryValues: MonetaryValue[];

  /** Temporal context (if applicable) */
  temporalContext?: TemporalContext;

  /** Relationships (for graph rendering) */
  relationships?: EntityReference[];

  /** Evidence trail (for inspector and graph) */
  evidence?: EvidenceLink[];

  /** Selection state (managed by SelectionRuntime, not the renderer) */
  selectionState?: SelectionState;
}

// ===== Renderer Component Props =====
export interface RendererProps<TData> {
  viewModel: RenderableViewModel<TData>;
  density: DensityLevel;
  onAction: (action: RendererAction) => void;
  context?: Record<string, unknown>;
}

// ===== Renderer Component Type =====
export type RendererComponent<TData> = React.ComponentType<RendererProps<TData>>;

// ===== Renderer Selection Info =====
export interface RendererSelection {
  objectType: string;
  mode: RendererMode;
  reason: 'workspace-default' | 'user-preference' | 'context-density' | 'selection' | 'timeline';
}

// ===== Registry Entry =====
export interface RegisteredRenderer {
  objectType: string;
  mode: RendererMode;
  component: RendererComponent<unknown>;
  defaultDensity: DensityLevel;
}
