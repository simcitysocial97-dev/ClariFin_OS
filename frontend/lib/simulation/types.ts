/**
 * Simulation Types - Stage 7 Simulation & Forecast Engine
 *
 * Core type definitions for deterministic financial simulation and forecasting.
 * Every projection must include assumptions, inputs, outputs, evidence, confidence,
 * and related graph nodes.
 *
 * All monetary values are in paise (₹1.00 = 100 paise) for financial determinism.
 * All scores are in basis points (0-10000 for 0-100%) unless otherwise noted.
 */

// ===== Projection Types =====

/**
 * A single projection point in a simulation timeline.
 */
export interface Projection {
  /** Unique projection identifier */
  id: string;
  /** Projection type (cashflow, net_worth, loan, investment, etc.) */
  type: ProjectionType;
  /** Date of projection (ISO format) */
  date: string;
  /** Projected value in paise */
  value_paise: number;
  /** Lower confidence bound in paise */
  lower_bound_paise?: number;
  /** Upper confidence bound in paise */
  upper_bound_paise?: number;
  /** Confidence score (0-100) */
  confidence: number;
  /** Related graph node IDs */
  related_nodes: string[];
}

/**
 * Types of projections supported.
 */
export type ProjectionType =
  | 'cashflow'
  | 'net_worth'
  | 'loan_balance'
  | 'investment_value'
  | 'retirement_corpus'
  | 'goal_progress'
  | 'emergency_fund';

// ===== Scenario Types =====

/**
 * A what-if scenario for financial simulation.
 */
export interface Scenario {
  /** Unique scenario identifier */
  id: string;
  /** Scenario name */
  name: string;
  /** Human-readable description */
  description: string;
  /** Probability in basis points (0-10000) */
  probability_bps: number;
  /** List of projections for this scenario */
  projections: Projection[];
  /** Assumptions made in this scenario */
  assumptions: SimulationAssumption[];
  /** Evidence chain for explainability */
  evidence: SimulationEvidenceChain;
}

// ===== Simulation Input/Output Types =====

/**
 * Input parameters for a simulation.
 */
export interface SimulationInput {
  /** Input name */
  name: string;
  /** Input value */
  value: number | string | boolean;
  /** Input description */
  description: string;
  /** Source of the input (user, historical, default) */
  source: 'user' | 'historical' | 'default';
}

/**
 * Output of a simulation.
 */
export interface SimulationOutput {
  /** Output name */
  name: string;
  /** Output value in paise (if monetary) */
  value_paise?: number;
  /** Output value (generic) */
  value?: number | string | boolean;
  /** Output description */
  description: string;
  /** Unit of measurement */
  unit?: string;
}

// ===== Assumption Types =====

/**
 * An assumption made in a simulation.
 */
export interface SimulationAssumption {
  /** Assumption identifier */
  id: string;
  /** Assumption description */
  description: string;
  /** Assumption category */
  category: AssumptionCategory;
  /** Numerical value of assumption (if applicable) */
  value?: number;
  /** Confidence in this assumption (0-100) */
  confidence: number;
  /** Source of assumption */
  source: string;
}

/**
 * Categories of assumptions.
 */
export type AssumptionCategory =
  | 'income'
  | 'expense'
  | 'rate'
  | 'growth'
  | 'inflation'
  | 'market'
  | 'behavioral';

// ===== Evidence Types =====

/**
 * Evidence item for simulation explainability.
 */
export interface SimulationEvidenceItem {
  /** Evidence type */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

/**
 * Calculation step in simulation.
 */
export interface SimulationCalculationStep {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

/**
 * Source reference for simulation.
 */
export interface SimulationSourceReference {
  /** Source identifier */
  id: string;
  /** Source type (file, api, calculation, graph_node) */
  type: string;
  /** Source label */
  label: string;
  /** Source timestamp (ISO format) */
  timestamp: string;
}

/**
 * Evidence chain for simulation explainability.
 */
export interface SimulationEvidenceChain {
  /** Overall summary of the simulation */
  summary: string;
  /** List of evidence items */
  evidence: SimulationEvidenceItem[];
  /** Calculation chain steps */
  calculation_steps: SimulationCalculationStep[];
  /** Source references for traceability */
  source_references: SimulationSourceReference[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Simulation Result Types =====

/**
 * Result of a simulation run.
 */
export interface SimulationResult {
  /** Simulation type */
  type: SimulationType;
  /** Scenario that was simulated */
  scenario: Scenario;
  /** Timeline of projections */
  timeline: Projection[];
  /** Key outputs */
  outputs: SimulationOutput[];
  /** Evidence chain */
  evidence: SimulationEvidenceChain;
  /** Related graph node IDs */
  related_nodes: string[];
}

/**
 * Types of simulations supported.
 */
export type SimulationType =
  | 'cashflow'
  | 'net_worth'
  | 'loan'
  | 'investment'
  | 'retirement'
  | 'goal'
  | 'budget'
  | 'emergency_fund';

// ===== Simulation Context =====

/**
 * Context for running simulations.
 */
export interface SimulationContext {
  /** Graph nodes to use as input */
  nodes: Array<{
    id: string;
    type: string;
    label: string;
    value_paise?: number;
    date?: string;
    metadata: Record<string, unknown>;
    confidence?: number;
  }>;
  /** Graph edges */
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
    label: string;
    metadata: Record<string, unknown>;
  }>;
  /** Configuration */
  config: SimulationConfig;
}

/**
 * Configuration for simulations.
 */
export interface SimulationConfig {
  /** Simulation horizon in months */
  horizon_months: number;
  /** Inflation rate assumption in basis points (0-10000) */
  inflation_rate_bps: number;
  /** Default return rate for investments in basis points */
  investment_return_rate_bps: number;
  /** Enabled simulation types */
  enabled_simulations: SimulationType[];
}

/**
 * Default simulation configuration.
 */
export const DEFAULT_SIMULATION_CONFIG: SimulationConfig = {
  horizon_months: 12,
  inflation_rate_bps: 300, // 3%
  investment_return_rate_bps: 800, // 8%
  enabled_simulations: [
    'cashflow',
    'net_worth',
    'loan',
    'investment',
    'retirement',
    'goal',
    'budget',
    'emergency_fund',
  ],
};

// ===== Engine Interface =====

/**
 * Interface for simulation engines.
 */
export interface SimulationEngine {
  /** Engine name */
  readonly name: SimulationType;
  /** Compute simulation from context */
  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult;
  /** Reset engine state */
  reset(): void;
}

/**
 * Options for running simulations.
 */
export interface SimulationOptions {
  /** Override horizon months */
  horizon_months?: number;
  /** Custom assumptions */
  assumptions?: SimulationAssumption[];
  /** Specific node IDs to focus on */
  focus_node_ids?: string[];
}

// ===== Sensitivity Analysis =====

/**
 * Sensitivity analysis result.
 */
export interface SensitivityResult {
  /** Input parameter being analyzed */
  parameter: string;
  /** Base value */
  base_value: number;
  /** Impact per unit change */
  impact_per_unit_paise: number;
  /** Confidence in sensitivity (0-100) */
  confidence: number;
}

// ===== Version =====
export const SIMULATION_RUNTIME_VERSION = '1.0.0';