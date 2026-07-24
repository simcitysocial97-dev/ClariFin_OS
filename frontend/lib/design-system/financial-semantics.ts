/**
 * Financial Semantics - Stage 8C Financial OS Visual System
 *
 * Visualization grammar for financial node types.
 * Single source of truth for node shapes, colors, animations, and badges.
 */

import { nodeTypeColors, edgeTypeColors, confidenceColors, riskColors, financialColors } from './colors';

// ===== Node Shape Types =====
export type NodeShape = 'circle' | 'square' | 'triangle' | 'diamond' | 'octagon' | 'hexagon' | 'rounded';

// ===== Node Grammar =====
export interface NodeGrammar {
  shape: NodeShape;
  color: string;
  size: number;
  animation?: 'none' | 'pulse' | 'flow' | 'warning';
  badge?: 'confidence' | 'risk' | 'value' | 'none';
  accessibilityLabel: string;
}

// ===== Edge Grammar =====
export interface EdgeGrammar {
  color: string;
  strokeWidth: number;
  strokeDasharray?: string;
  animation?: 'none' | 'flow' | 'dash';
}

// ===== Node Type Grammar Map =====
export const nodeGrammar: Record<string, NodeGrammar> = {
  // Transaction - circle, neutral, value badge
  transaction: {
    shape: 'circle',
    color: nodeTypeColors.transaction,
    size: 12,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Transaction node',
  },

  // Account - square, info, confidence badge
  account: {
    shape: 'square',
    color: nodeTypeColors.account,
    size: 16,
    animation: 'none',
    badge: 'confidence',
    accessibilityLabel: 'Account node',
  },

  // Cashflow month - rounded, neutral
  cashflow_month: {
    shape: 'rounded',
    color: nodeTypeColors.cashflow_month,
    size: 14,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Cashflow month node',
  },

  // Cashflow category - circle, neutral
  cashflow_category: {
    shape: 'circle',
    color: nodeTypeColors.cashflow_category,
    size: 10,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Cashflow category node',
  },

  // Loan - octagon, negative, risk badge
  loan: {
    shape: 'octagon',
    color: nodeTypeColors.loan,
    size: 18,
    animation: 'none',
    badge: 'risk',
    accessibilityLabel: 'Loan node',
  },

  // Amortization entry - diamond, negative
  amortization_entry: {
    shape: 'diamond',
    color: nodeTypeColors.amortization_entry,
    size: 10,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Amortization entry node',
  },

  // Credit card - octagon, negative
  credit_card: {
    shape: 'octagon',
    color: nodeTypeColors.credit_card,
    size: 16,
    animation: 'none',
    badge: 'confidence',
    accessibilityLabel: 'Credit card node',
  },

  // Credit card statement - square, negative
  credit_card_statement: {
    shape: 'square',
    color: nodeTypeColors.credit_card_statement,
    size: 12,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Credit card statement node',
  },

  // Investment - triangle, positive
  investment: {
    shape: 'triangle',
    color: nodeTypeColors.investment,
    size: 16,
    animation: 'none',
    badge: 'confidence',
    accessibilityLabel: 'Investment node',
  },

  // Holding - triangle, positive
  holding: {
    shape: 'triangle',
    color: nodeTypeColors.holding,
    size: 12,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Holding node',
  },

  // Behaviour score - circle, info, confidence badge
  behaviour_score: {
    shape: 'circle',
    color: nodeTypeColors.behaviour_score,
    size: 14,
    animation: 'none',
    badge: 'confidence',
    accessibilityLabel: 'Behaviour score node',
  },

  // Spending pattern - circle, neutral
  spending_pattern: {
    shape: 'circle',
    color: nodeTypeColors.spending_pattern,
    size: 10,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Spending pattern node',
  },

  // Reconciliation statement - square, neutral
  reconciliation_statement: {
    shape: 'square',
    color: nodeTypeColors.reconciliation_statement,
    size: 12,
    animation: 'none',
    badge: 'confidence',
    accessibilityLabel: 'Reconciliation statement node',
  },

  // Discrepancy - diamond, negative, warning animation
  discrepancy: {
    shape: 'diamond',
    color: nodeTypeColors.discrepancy,
    size: 12,
    animation: 'warning',
    badge: 'confidence',
    accessibilityLabel: 'Discrepancy node',
  },

  // Forecast projection - circle, info
  forecast_projection: {
    shape: 'circle',
    color: nodeTypeColors.forecast_projection,
    size: 12,
    animation: 'none',
    badge: 'confidence',
    accessibilityLabel: 'Forecast projection node',
  },

  // Forecast scenario - rounded, info
  forecast_scenario: {
    shape: 'rounded',
    color: nodeTypeColors.forecast_scenario,
    size: 14,
    animation: 'none',
    badge: 'none',
    accessibilityLabel: 'Forecast scenario node',
  },

  // Net worth snapshot - circle, neutral
  net_worth_snapshot: {
    shape: 'circle',
    color: nodeTypeColors.net_worth_snapshot,
    size: 14,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Net worth snapshot node',
  },

  // Net worth breakdown - square, neutral
  net_worth_breakdown: {
    shape: 'square',
    color: nodeTypeColors.net_worth_breakdown,
    size: 12,
    animation: 'none',
    badge: 'value',
    accessibilityLabel: 'Net worth breakdown node',
  },

  // Merchant - circle, neutral
  merchant: {
    shape: 'circle',
    color: nodeTypeColors.merchant,
    size: 10,
    animation: 'none',
    badge: 'none',
    accessibilityLabel: 'Merchant node',
  },

  // Category - square, neutral
  category: {
    shape: 'square',
    color: nodeTypeColors.category,
    size: 10,
    animation: 'none',
    badge: 'none',
    accessibilityLabel: 'Category node',
  },

  // Institution - rounded, neutral
  institution: {
    shape: 'rounded',
    color: nodeTypeColors.institution,
    size: 14,
    animation: 'none',
    badge: 'none',
    accessibilityLabel: 'Institution node',
  },
} as const;

// ===== Edge Type Grammar Map =====
export const edgeGrammar: Record<string, EdgeGrammar> = {
  belongs_to: {
    color: edgeTypeColors.belongs_to,
    strokeWidth: 1,
    animation: 'none',
  },

  categorized_as: {
    color: edgeTypeColors.categorized_as,
    strokeWidth: 1,
    animation: 'none',
  },

  from_merchant: {
    color: edgeTypeColors.from_merchant,
    strokeWidth: 1,
    animation: 'none',
  },

  at_institution: {
    color: edgeTypeColors.at_institution,
    strokeWidth: 1,
    animation: 'none',
  },

  composes: {
    color: edgeTypeColors.composes,
    strokeWidth: 2,
    animation: 'none',
  },

  affects_cashflow: {
    color: edgeTypeColors.affects_cashflow,
    strokeWidth: 1,
    animation: 'none',
  },

  amortizes: {
    color: edgeTypeColors.amortizes,
    strokeWidth: 1,
    animation: 'none',
  },

  has_statement: {
    color: edgeTypeColors.has_statement,
    strokeWidth: 1,
    animation: 'none',
  },

  has_holding: {
    color: edgeTypeColors.has_holding,
    strokeWidth: 1,
    animation: 'none',
  },

  impacts_score: {
    color: edgeTypeColors.impacts_score,
    strokeWidth: 1,
    animation: 'none',
  },

  reconciles: {
    color: edgeTypeColors.reconciles,
    strokeWidth: 1,
    animation: 'none',
  },

  projects: {
    color: edgeTypeColors.projects,
    strokeWidth: 2,
    animation: 'flow',
    strokeDasharray: '5,5',
  },

  scenario_of: {
    color: edgeTypeColors.scenario_of,
    strokeWidth: 1,
    animation: 'none',
  },

  traces_to: {
    color: edgeTypeColors.traces_to,
    strokeWidth: 1,
    animation: 'none',
  },

  references: {
    color: edgeTypeColors.references,
    strokeWidth: 1,
    animation: 'none',
  },

  derived_from: {
    color: edgeTypeColors.derived_from,
    strokeWidth: 1,
    animation: 'none',
  },

  related_to: {
    color: edgeTypeColors.related_to,
    strokeWidth: 1,
    animation: 'none',
  },
} as const;

// ===== Get Node Grammar =====
export function getNodeGrammar(nodeType: string): NodeGrammar {
  return nodeGrammar[nodeType] ?? {
    shape: 'circle',
    color: financialColors.neutral[500],
    size: 12,
    animation: 'none',
    badge: 'none',
    accessibilityLabel: 'Unknown node',
  };
}

// ===== Get Edge Grammar =====
export function getEdgeGrammar(edgeType: string): EdgeGrammar {
  return edgeGrammar[edgeType] ?? {
    color: edgeTypeColors.related_to,
    strokeWidth: 1,
    animation: 'none',
  };
}

// ===== Get Confidence Color =====
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return confidenceColors.high;
  if (confidence >= 50) return confidenceColors.medium;
  return confidenceColors.low;
}

// ===== Get Risk Color =====
export function getRiskColor(risk: 'low' | 'medium' | 'high' | 'critical'): string {
  return riskColors[risk] ?? riskColors.low;
}