/**
 * Intelligence Runtime - Stage 6 Financial Intelligence Engine
 *
 * Main runtime that orchestrates all intelligence engines.
 * Consumes the Financial Graph Runtime and produces deterministic
 * financial intelligence (insights, alerts, recommendations, risk scores).
 *
 * Architecture: FinancialGraphRuntime → IntelligenceRuntime → Engines → Command Center
 *
 * Every insight includes: evidence, calculation, confidence, source, related graph nodes.
 */

import type {
  IntelligenceConfig,
  IntelligenceResult,
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  Insight,
  Alert,
  Recommendation,
  RiskScore,
  OpportunityScore,
  Goal,
  HealthScore,
  EngineName,
} from './types';
import { DEFAULT_INTELLIGENCE_CONFIG, INTELLIGENCE_RUNTIME_VERSION } from './types';

// ===== Intelligence Runtime =====
/**
 * Main runtime for the Financial Intelligence Engine.
 * Orchestrates all intelligence engines and produces deterministic results.
 */
export class IntelligenceRuntime {
  private config: IntelligenceConfig;
  private engines: Map<EngineName, IntelligenceEngine> = new Map();
  private lastResult: IntelligenceResult | null = null;
  private engineResults: Map<EngineName, EngineResult> = new Map();

  constructor(config: Partial<IntelligenceConfig> = {}) {
    this.config = { ...DEFAULT_INTELLIGENCE_CONFIG, ...config };
  }

  // ===== Engine Registration =====
  /**
   * Register an intelligence engine
   */
  registerEngine(engine: IntelligenceEngine): void {
    this.engines.set(engine.name, engine);
  }

  /**
   * Unregister an intelligence engine
   */
  unregisterEngine(name: EngineName): void {
    this.engines.delete(name);
  }

  /**
   * Get a registered engine
   */
  getEngine(name: EngineName): IntelligenceEngine | undefined {
    return this.engines.get(name);
  }

  /**
   * Get all registered engines
   */
  getEngines(): IntelligenceEngine[] {
    return Array.from(this.engines.values());
  }

  /**
   * Get enabled engine names
   */
  getEnabledEngines(): EngineName[] {
    return this.config.enabled_engines.filter(name => this.engines.has(name));
  }

  // ===== Configuration =====
  /**
   * Update configuration
   */
  updateConfig(config: Partial<IntelligenceConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current configuration
   */
  getConfig(): IntelligenceConfig {
    return { ...this.config };
  }

  // ===== Intelligence Computation =====
  /**
   * Compute intelligence from graph data
   *
   * Runs all enabled engines and aggregates results.
   * Every result is deterministic and reproducible.
   */
  compute(context: IntelligenceContext): IntelligenceResult {
    const computedAt = new Date().toISOString();
    const enabledEngines = this.getEnabledEngines();

    // Aggregate results from all enabled engines
    const allInsights: Insight[] = [];
    const allAlerts: Alert[] = [];
    const allRecommendations: Recommendation[] = [];
    const allRiskScores: RiskScore[] = [];
    const allOpportunityScores: OpportunityScore[] = [];
    const allGoals: Goal[] = [];
    let healthScore: HealthScore | null = null;

    for (const engineName of enabledEngines) {
      const engine = this.engines.get(engineName);
      if (!engine) continue;

      const result = engine.compute(context);
      this.engineResults.set(engineName, result);

      allInsights.push(...result.insights);
      allAlerts.push(...result.alerts);
      allRecommendations.push(...result.recommendations);
      allRiskScores.push(...result.risk_scores);
      allOpportunityScores.push(...result.opportunity_scores);
      allGoals.push(...result.goals);

      // Health score from health engine takes precedence
      if (result.health_score && engineName === 'health') {
        healthScore = result.health_score;
      } else if (result.health_score && !healthScore) {
        healthScore = result.health_score;
      }
    }

    // Sort by priority (1 = highest)
    allInsights.sort((a, b) => a.priority - b.priority);
    allAlerts.sort((a, b) => a.priority - b.priority);
    allRecommendations.sort((a, b) => a.priority - b.priority);

    // Apply limits
    const result: IntelligenceResult = {
      computed_at: computedAt,
      insight_count: allInsights.length,
      alert_count: allAlerts.length,
      recommendation_count: allRecommendations.length,
      risk_score_count: allRiskScores.length,
      opportunity_score_count: allOpportunityScores.length,
      goal_count: allGoals.length,
      health_score: healthScore,
      insights: allInsights.slice(0, this.config.max_insights),
      alerts: allAlerts.slice(0, this.config.max_alerts),
      recommendations: allRecommendations.slice(0, this.config.max_recommendations),
      risk_scores: allRiskScores,
      opportunity_scores: allOpportunityScores,
      goals: allGoals,
    };

    this.lastResult = result;
    return result;
  }

  /**
   * Get the last computed result
   */
  getLastResult(): IntelligenceResult | null {
    return this.lastResult;
  }

  /**
   * Get result from a specific engine
   */
  getEngineResult(name: EngineName): EngineResult | undefined {
    return this.engineResults.get(name);
  }

  // ===== Query Methods =====
  /**
   * Get all insights
   */
  getInsights(): Insight[] {
    return this.lastResult?.insights ?? [];
  }

  /**
   * Get insights by type
   */
  getInsightsByType(type: string): Insight[] {
    return (this.lastResult?.insights ?? []).filter(i => i.type === type);
  }

  /**
   * Get insights by severity
   */
  getInsightsBySeverity(severity: string): Insight[] {
    return (this.lastResult?.insights ?? []).filter(i => i.severity === severity);
  }

  /**
   * Get all alerts
   */
  getAlerts(): Alert[] {
    return this.lastResult?.alerts ?? [];
  }

  /**
   * Get unacknowledged alerts
   */
  getUnacknowledgedAlerts(): Alert[] {
    return (this.lastResult?.alerts ?? []).filter(a => !a.acknowledged);
  }

  /**
   * Get all recommendations
   */
  getRecommendations(): Recommendation[] {
    return this.lastResult?.recommendations ?? [];
  }

  /**
   * Get all risk scores
   */
  getRiskScores(): RiskScore[] {
    return this.lastResult?.risk_scores ?? [];
  }

  /**
   * Get risk score by category
   */
  getRiskScoreByCategory(category: string): RiskScore | undefined {
    return (this.lastResult?.risk_scores ?? []).find(r => r.category === category);
  }

  /**
   * Get all opportunity scores
   */
  getOpportunityScores(): OpportunityScore[] {
    return this.lastResult?.opportunity_scores ?? [];
  }

  /**
   * Get all goals
   */
  getGoals(): Goal[] {
    return this.lastResult?.goals ?? [];
  }

  /**
   * Get health score
   */
  getHealthScore(): HealthScore | null {
    return this.lastResult?.health_score ?? null;
  }

  /**
   * Get explainability for an insight
   */
  explainInsight(insightId: string): Insight | undefined {
    return (this.lastResult?.insights ?? []).find(i => i.id === insightId);
  }

  /**
   * Get related nodes for an insight
   */
  getRelatedNodes(insightId: string): string[] {
    const insight = (this.lastResult?.insights ?? []).find(i => i.id === insightId);
    return insight?.related_nodes ?? [];
  }

  // ===== Reset =====
  /**
   * Reset all engines
   */
  reset(): void {
    for (const engine of this.engines.values()) {
      engine.reset();
    }
    this.lastResult = null;
    this.engineResults.clear();
  }

  /**
   * Reset a specific engine
   */
  resetEngine(name: EngineName): void {
    const engine = this.engines.get(name);
    if (engine) {
      engine.reset();
      this.engineResults.delete(name);
    }
  }

  // ===== Version =====
  /**
   * Get runtime version
   */
  getVersion(): string {
    return INTELLIGENCE_RUNTIME_VERSION;
  }
}

// ===== Convenience Export =====
/** Default intelligence runtime instance */
export const intelligenceRuntime = new IntelligenceRuntime();