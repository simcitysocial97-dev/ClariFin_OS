/**
 * Design System Colors - Stage 8C Financial OS Visual System
 *
 * Semantic color tokens for financial data visualization.
 * No decorative gradients - flat slate theme.
 */

// ===== Financial Semantic Colors =====
export const financialColors = {
  // Positive values (income, gains, assets)
  positive: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },

  // Negative values (expenses, losses, liabilities)
  negative: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
  },

  // Neutral values (transfers, balance)
  neutral: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },

  // Warning (high risk, attention needed)
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
  },

  // Info (insights, recommendations)
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
  },

  // Success (completed, achieved)
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
  },
} as const;

// ===== Node Type Colors =====
export const nodeTypeColors = {
  transaction: financialColors.neutral[500],
  account: financialColors.info[500],
  cashflow_month: financialColors.neutral[600],
  cashflow_category: financialColors.neutral[500],
  loan: financialColors.negative[500],
  amortization_entry: financialColors.negative[400],
  credit_card: financialColors.negative[500],
  credit_card_statement: financialColors.negative[400],
  investment: financialColors.positive[500],
  holding: financialColors.positive[400],
  behaviour_score: financialColors.info[500],
  spending_pattern: financialColors.neutral[500],
  reconciliation_statement: financialColors.neutral[500],
  discrepancy: financialColors.negative[500],
  forecast_projection: financialColors.info[500],
  forecast_scenario: financialColors.info[400],
  net_worth_snapshot: financialColors.neutral[500],
  net_worth_breakdown: financialColors.neutral[400],
  merchant: financialColors.neutral[500],
  category: financialColors.neutral[400],
  institution: financialColors.neutral[600],
} as const;

// ===== Edge Type Colors =====
export const edgeTypeColors = {
  belongs_to: financialColors.neutral[400],
  categorized_as: financialColors.neutral[400],
  from_merchant: financialColors.neutral[400],
  at_institution: financialColors.neutral[400],
  composes: financialColors.info[400],
  affects_cashflow: financialColors.neutral[400],
  amortizes: financialColors.negative[400],
  has_statement: financialColors.negative[400],
  has_holding: financialColors.positive[400],
  impacts_score: financialColors.info[400],
  reconciles: financialColors.neutral[400],
  projects: financialColors.info[400],
  scenario_of: financialColors.info[400],
  traces_to: financialColors.neutral[400],
  references: financialColors.neutral[400],
  derived_from: financialColors.neutral[400],
  related_to: financialColors.neutral[400],
} as const;

// ===== Confidence Level Colors =====
export const confidenceColors = {
  high: financialColors.success[500], // 80-100%
  medium: financialColors.warning[500], // 50-79%
  low: financialColors.negative[500], // 0-49%
} as const;

// ===== Risk Level Colors =====
export const riskColors = {
  low: financialColors.success[500],
  medium: financialColors.warning[500],
  high: financialColors.negative[500],
  critical: financialColors.negative[700],
} as const;

// ===== UI Colors (Flat Slate Theme) =====
export const uiColors = {
  background: {
    primary: '#ffffff',
    secondary: '#f8fafc',
    tertiary: '#f1f5f9',
    dark: '#0f172a',
  },
  border: {
    primary: '#e2e8f0',
    secondary: '#cbd5e1',
    focus: '#3b82f6',
    selected: '#2563eb',
  },
  text: {
    primary: '#0f172a',
    secondary: '#475569',
    tertiary: '#64748b',
    disabled: '#94a3b8',
    inverse: '#ffffff',
  },
} as const;