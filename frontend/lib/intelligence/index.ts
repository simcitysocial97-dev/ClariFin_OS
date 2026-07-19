/**
 * Financial Intelligence Engine - Public API
 *
 * Central export for the Stage 6 Financial Intelligence Engine.
 * Every workspace can import from here to generate deterministic
 * financial intelligence.
 *
 * Architecture: FinancialGraphRuntime → IntelligenceRuntime → Engines → Command Center
 */

// ===== Core Types =====
export type {
  Severity,
  Priority,
  EvidenceItem,
  CalculationStep,
  SourceReference,
  EvidenceChain,
  Insight,
  InsightType,
  Alert,
  AlertType,
  Recommendation,
  RecommendationType,
  RiskScore,
  RiskCategory,
  RiskFactor,
  OpportunityScore,
  OpportunityCategory,
  Goal,
  GoalCategory,
  HealthScore,
  HealthDimension,
  IntelligenceResult,
  IntelligenceConfig,
  EngineName,
  ThresholdConfig,
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
} from './types';

export {
  DEFAULT_THRESHOLDS,
  DEFAULT_INTELLIGENCE_CONFIG,
  INTELLIGENCE_RUNTIME_VERSION,
} from './types';

// ===== Intelligence Runtime =====
export {
  IntelligenceRuntime,
  intelligenceRuntime,
} from './runtime';

// ===== Insight Builder =====
export {
  InsightBuilder,
  insightBuilder,
} from './insight-builder';

// ===== Engines (register individually) =====
export { HealthEngine } from './health-engine';
export { SpendingEngine } from './spending-engine';
export { CashflowEngine } from './cashflow-engine';
export { DebtEngine } from './debt-engine';
export { InvestmentEngine } from './investment-engine';
export { BehaviourEngine } from './behaviour-engine';
export { GoalEngine } from './goal-engine';
export { RiskEngine } from './risk-engine';
export { OpportunityEngine } from './opportunity-engine';
export { RecommendationEngine } from './recommendation-engine';
export { AlertEngine } from './alert-engine';
export { AnomalyEngine } from './anomaly-engine';
