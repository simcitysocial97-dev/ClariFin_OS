/**
 * Intelligence Types - Stage 6 Financial Intelligence Engine
 *
 * Core type definitions for the deterministic Financial Intelligence Engine.
 * Every insight, alert, recommendation, risk score, and opportunity score
 * must include evidence, calculation, confidence, source, and related graph nodes.
 *
 * All monetary values are in paise (₹1.00 = 100 paise) for financial determinism.
 * All scores are in basis points (0-10000 for 0-100%) unless otherwise noted.
 */

// ===== Severity & Priority =====
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type Priority = 1 | 2 | 3 | 4 | 5; // 1 = highest priority

// ===== Evidence Chain =====
export interface EvidenceItem {
  /** Evidence type (transaction, pattern, score, calculation) */
  type: string;
  /** Human-readable summary */
  summary: string;
  /** Source reference (file, API, calculation) */
  source: string;
  /** Confidence score (0-100) */
  confidence?: number;
}

export interface CalculationStep {
  /** Step name */
  name: string;
  /** Step description */
  description: string;
  /** Input values for the step */
  inputs: Record<string, unknown>;
  /** Output values from the step */
  outputs: Record<string, unknown>;
}

export interface SourceReference {
  /** Source identifier */
  id: string;
  /** Source type (file, api, calculation, graph_node) */
  type: string;
  /** Source label */
  label: string;
  /** Source timestamp (ISO format) */
  timestamp: string;
}

export interface EvidenceChain {
  /** Overall summary of the analysis */
  summary: string;
  /** List of evidence items */
  evidence: EvidenceItem[];
  /** Calculation chain steps */
  calculation_steps: CalculationStep[];
  /** Source references for traceability */
  source_references: SourceReference[];
  /** Overall confidence (0-100) */
  confidence_score: number;
}

// ===== Insight Object =====
export interface Insight {
  /** Unique insight identifier */
  id: string;
  /** Insight type */
  type: InsightType;
  /** Severity level */
  severity: Severity;
  /** Priority (1-5, 1 highest) */
  priority: Priority;
  /** Confidence score (0-100) */
  confidence: number;
  /** Short human-readable summary */
  summary: string;
  /** Detailed description with numbers */
  description: string;
  /** Evidence chain for explainability */
  evidence: EvidenceChain;
  /** Calculation that produced this insight */
  calculation: string;
  /** Source of the insight (engine name) */
  source: string;
  /** Recommended actions */
  recommended_actions: string[];
  /** Related graph node IDs */
  related_nodes: string[];
  /** Deep link to source workspace */
  deep_link?: string;
  /** Monetary value in paise (if applicable) */
  value_paise?: number;
  /** Score in basis points (if applicable) */
  score_bps?: number;
}

export type InsightType =
  | 'health'
  | 'spending'
  | 'cashflow'
  | 'debt'
  | 'investment'
  | 'behaviour'
  | 'goal'
  | 'risk'
  | 'opportunity'
  | 'recommendation'
  | 'alert'
  | 'anomaly'
  | 'milestone'
  | 'trend';

// ===== Alert =====
export interface Alert {
  /** Unique alert identifier */
  id: string;
  /** Alert type */
  type: AlertType;
  /** Severity level */
  severity: Severity;
  /** Priority (1-5, 1 highest) */
  priority: Priority;
  /** Short title */
  title: string;
  /** Detailed message */
  message: string;
  /** Evidence chain */
  evidence: EvidenceChain;
  /** Source of the alert */
  source: string;
  /** Related graph node IDs */
  related_nodes: string[];
  /** Deep link */
  deep_link?: string;
  /** Whether alert requires acknowledgement */
  requires_acknowledgement: boolean;
  /** Whether alert has been acknowledged */
  acknowledged: boolean;
  /** Timestamp (ISO format) */
  timestamp: string;
  /** Expiry timestamp (ISO format) */
  expires_at?: string;
}

export type AlertType =
  | 'spending_anomaly'
  | 'cashflow_gap'
  | 'debt_risk'
  | 'low_liquidity'
  | 'high_impulsivity'
  | 'gambling_detected'
  | 'loan_app_pattern'
  | 'emi_burden'
  | 'negative_savings'
  | 'subscription_growth'
  | 'investment_risk'
  | 'goal_deviation'
  | 'reconciliation_issue';

// ===== Recommendation =====
export interface Recommendation {
  /** Unique recommendation identifier */
  id: string;
  /** Recommendation type */
  type: RecommendationType;
  /** Severity level */
  severity: Severity;
  /** Priority (1-5, 1 highest) */
  priority: Priority;
  /** Short title */
  title: string;
  /** Reason for recommendation */
  reason: string;
  /** Metric that triggered this recommendation */
  metric: string;
  /** Suggested action */
  suggested_action: string;
  /** Evidence chain */
  evidence: EvidenceChain;
  /** Source of the recommendation */
  source: string;
  /** Related graph node IDs */
  related_nodes: string[];
  /** Deep link */
  deep_link?: string;
}

export type RecommendationType =
  | 'debt_management'
  | 'savings_improvement'
  | 'spending_reduction'
  | 'emergency_fund'
  | 'investment'
  | 'subscription_review'
  | 'budget_setting'
  | 'liquidity_improvement'
  | 'foir_reduction'
  | 'goal_adjustment';

// ===== Risk Score =====
export interface RiskScore {
  /** Unique risk identifier */
  id: string;
  /** Risk category */
  category: RiskCategory;
  /** Risk score (0-100, higher = more risk) */
  score: number;
  /** Confidence (0-100) */
  confidence: number;
  /** Risk factors contributing to score */
  factors: RiskFactor[];
  /** Evidence chain */
  evidence: EvidenceChain;
  /** Related graph node IDs */
  related_nodes: string[];
  /** Deep link */
  deep_link?: string;
}

export type RiskCategory =
  | 'overall_financial'
  | 'debt'
  | 'spending'
  | 'liquidity'
  | 'investment'
  | 'behavioural'
  | 'concentration';

export interface RiskFactor {
  /** Factor name */
  name: string;
  /** Contribution to risk score (0-100) */
  contribution: number;
  /** Description of the factor */
  description: string;
  /** Current value */
  current_value: string;
  /** Threshold value */
  threshold: string;
}

// ===== Opportunity Score =====
export interface OpportunityScore {
  /** Unique opportunity identifier */
  id: string;
  /** Opportunity category */
  category: OpportunityCategory;
  /** Opportunity score (0-100, higher = more opportunity) */
  score: number;
  /** Confidence (0-100) */
  confidence: number;
  /** Potential impact description */
  potential_impact: string;
  /** Estimated benefit in paise (if applicable) */
  estimated_benefit_paise?: number;
  /** Evidence chain */
  evidence: EvidenceChain;
  /** Related graph node IDs */
  related_nodes: string[];
  /** Deep link */
  deep_link?: string;
}

export type OpportunityCategory =
  | 'savings_potential'
  | 'investment_potential'
  | 'debt_optimization'
  | 'spending_optimization'
  | 'cashflow_improvement'
  | 'tax_saving';

// ===== Goal =====
export interface Goal {
  /** Unique goal identifier */
  id: string;
  /** Goal category */
  category: GoalCategory;
  /** Goal title */
  title: string;
  /** Target value in paise */
  target_paise: number;
  /** Current value in paise */
  current_paise: number;
  /** Start date (ISO format) */
  start_date: string;
  /** Target date (ISO format) */
  target_date: string;
  /** Progress percentage (0-100) */
  progress_percentage: number;
  /** Velocity (paise per month) */
  velocity_paise_per_month: number;
  /** Required velocity to meet target (paise per month) */
  required_velocity_paise_per_month: number;
  /** Whether goal is on track */
  on_track: boolean;
  /** Evidence chain */
  evidence: EvidenceChain;
  /** Related graph node IDs */
  related_nodes: string[];
  /** Deep link */
  deep_link?: string;
}

export type GoalCategory =
  | 'emergency_fund'
  | 'savings'
  | 'debt_repayment'
  | 'investment'
  | 'large_purchase'
  | 'retirement';

// ===== Health Score =====
export interface HealthScore {
  /** Overall financial health score (0-100) */
  overall: number;
  /** Dimension scores */
  dimensions: HealthDimension[];
  /** Evidence chain */
  evidence: EvidenceChain;
  /** Related graph node IDs */
  related_nodes: string[];
}

export interface HealthDimension {
  /** Dimension name */
  name: string;
  /** Score (0-100) */
  score: number;
  /** Label (e.g., 'Healthy', 'Warning', 'Critical') */
  label: string;
  /** Factors contributing to score */
  factors: string[];
}

// ===== Intelligence Result =====
export interface IntelligenceResult {
  /** Timestamp of intelligence computation (ISO format) */
  computed_at: string;
  /** Number of insights generated */
  insight_count: number;
  /** Number of alerts generated */
  alert_count: number;
  /** Number of recommendations generated */
  recommendation_count: number;
  /** Number of risk scores generated */
  risk_score_count: number;
  /** Number of opportunity scores generated */
  opportunity_score_count: number;
  /** Number of goals tracked */
  goal_count: number;
  /** Overall health score */
  health_score: HealthScore | null;
  /** All insights */
  insights: Insight[];
  /** All alerts */
  alerts: Alert[];
  /** All recommendations */
  recommendations: Recommendation[];
  /** All risk scores */
  risk_scores: RiskScore[];
  /** All opportunity scores */
  opportunity_scores: OpportunityScore[];
  /** All goals */
  goals: Goal[];
}

// ===== Intelligence Configuration =====
export interface IntelligenceConfig {
  /** Enable/disable specific engines */
  enabled_engines: EngineName[];
  /** Thresholds for various triggers */
  thresholds: ThresholdConfig;
  /** Maximum number of insights to generate */
  max_insights: number;
  /** Maximum number of alerts to generate */
  max_alerts: number;
  /** Maximum number of recommendations to generate */
  max_recommendations: number;
}

export type EngineName =
  | 'health'
  | 'spending'
  | 'cashflow'
  | 'debt'
  | 'investment'
  | 'behaviour'
  | 'goal'
  | 'risk'
  | 'opportunity'
  | 'recommendation'
  | 'alert'
  | 'anomaly';

export interface ThresholdConfig {
  /** Impulsivity threshold (0-1) */
  impulsivity_threshold: number;
  /** Financial stress threshold (0-1) */
  stress_threshold: number;
  /** Savings discipline threshold (0-1) */
  savings_threshold: number;
  /** Debt-to-income ratio threshold (0-1) */
  debt_to_income_threshold: number;
  /** Liquidity months threshold */
  liquidity_months_threshold: number;
  /** Large transaction threshold in paise */
  large_transaction_threshold_paise: number;
  /** Micro transaction threshold in paise */
  micro_transaction_threshold_paise: number;
  /** EMI ratio threshold (0-1) */
  emi_ratio_threshold: number;
  /** Subscription growth threshold (0-1) */
  subscription_growth_threshold: number;
}

export const DEFAULT_THRESHOLDS: ThresholdConfig = {
  impulsivity_threshold: 0.7,
  stress_threshold: 0.6,
  savings_threshold: 0.3,
  debt_to_income_threshold: 0.4,
  liquidity_months_threshold: 3,
  large_transaction_threshold_paise: 5000000, // ₹50,000
  micro_transaction_threshold_paise: 50000,   // ₹500
  emi_ratio_threshold: 0.4,
  subscription_growth_threshold: 0.25,
};

export const DEFAULT_INTELLIGENCE_CONFIG: IntelligenceConfig = {
  enabled_engines: [
    'health',
    'spending',
    'cashflow',
    'debt',
    'investment',
    'behaviour',
    'goal',
    'risk',
    'opportunity',
    'recommendation',
    'alert',
    'anomaly',
  ],
  thresholds: DEFAULT_THRESHOLDS,
  max_insights: 50,
  max_alerts: 20,
  max_recommendations: 20,
};

// ===== Engine Interface =====
export interface IntelligenceEngine {
  /** Engine name */
  readonly name: EngineName;
  /** Compute intelligence from graph data */
  compute(context: IntelligenceContext): EngineResult;
  /** Reset engine state */
  reset(): void;
}

export interface IntelligenceContext {
  /** Graph nodes */
  nodes: Array<{ id: string; type: string; label: string; value_paise?: number; date?: string; metadata: Record<string, unknown>; confidence?: number }>;
  /** Graph edges */
  edges: Array<{ id: string; source: string; target: string; type: string; label: string; metadata: Record<string, unknown> }>;
  /** Configuration */
  config: IntelligenceConfig;
}

export interface EngineResult {
  /** Insights generated by this engine */
  insights: Insight[];
  /** Alerts generated by this engine */
  alerts: Alert[];
  /** Recommendations generated by this engine */
  recommendations: Recommendation[];
  /** Risk scores generated by this engine */
  risk_scores: RiskScore[];
  /** Opportunity scores generated by this engine */
  opportunity_scores: OpportunityScore[];
  /** Goals tracked by this engine */
  goals: Goal[];
  /** Health score computed by this engine */
  health_score: HealthScore | null;
}

// ===== Version =====
export const INTELLIGENCE_RUNTIME_VERSION = '1.0.0';

// ===== Executive Insight Types =====
export type ExecutiveSeverity = 'warning' | 'critical';

export interface ExecutiveInsight {
  id: string;
  severity: ExecutiveSeverity;
  title: string;
  summary: string;
  requiresAction: boolean;
  actionLabel: string;
  cancelLabel: string;
  onAction?: () => void;
  onCancel?: () => void;
  auditTrail: {
    detectedAt: number;
    threshold?: number;
    actualValue?: number;
  };
  acknowledged: boolean;
  decisions: Array<{ decision: 'action' | 'cancel'; timestamp: number; details?: Record<string, unknown> }>;
}

// ===== Investigative Insight Types =====
export type InvestigativeTrigger = 'entity-selected' | 'insight-clicked' | 'command-issued';

export interface EvidenceLink {
  label: string;
  sourceType: 'transaction' | 'statement' | 'reconciliation' | 'forecast';
  sourceId: string;
  confidence: number;
}

export interface EntityReference {
  entityId: string;
  entityType: string;
  label: string;
  relationshipType: string;
}

export interface DrillDownAction {
  label: string;
  targetWorkspace?: string;
  targetRoute?: string;
  contextPayload?: Record<string, unknown>;
}

export interface InvestigativeInsight {
  id: string;
  trigger: InvestigativeTrigger;
  title: string;
  summary: string;
  evidenceTrail: EvidenceLink[];
  relatedEntities: EntityReference[];
  drillDownActions: DrillDownAction[];
  createdAt: number;
  dismissed: boolean;
}