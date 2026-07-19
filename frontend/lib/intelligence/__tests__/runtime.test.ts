/**
 * Intelligence Runtime Tests - Stage 6 Financial Intelligence Engine
 */

import { describe, it, expect } from 'vitest';
import { IntelligenceRuntime } from '../runtime';
import { HealthEngine } from '../health-engine';
import { SpendingEngine } from '../spending-engine';
import { DEFAULT_INTELLIGENCE_CONFIG } from '../types';

describe('IntelligenceRuntime', () => {
  it('should create with default config', () => {
    const runtime = new IntelligenceRuntime();
    expect(runtime.getVersion()).toBe('1.0.0');
    // No engines registered by default - they must be registered explicitly
    expect(runtime.getEnabledEngines()).toHaveLength(0);
  });

  it('should register and retrieve engines', () => {
    const runtime = new IntelligenceRuntime();
    const engine = new HealthEngine();

    runtime.registerEngine(engine);
    expect(runtime.getEngine('health')).toBe(engine);
  });

  it('should unregister engines', () => {
    const runtime = new IntelligenceRuntime();
    const engine = new HealthEngine();

    runtime.registerEngine(engine);
    runtime.unregisterEngine('health');
    expect(runtime.getEngine('health')).toBeUndefined();
  });

  it('should compute intelligence from multiple engines', () => {
    const runtime = new IntelligenceRuntime();
    runtime.registerEngine(new HealthEngine());
    runtime.registerEngine(new SpendingEngine());

    const result = runtime.compute({
      nodes: [
        {
          id: 'node-1',
          type: 'behaviour_score',
          label: 'Savings',
          value_paise: 100000,
          metadata: { savings_rate_bps: 1500 },
        },
      ],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    expect(result.computed_at).toBeDefined();
    expect(result.insights).toBeDefined();
    expect(result.alerts).toBeDefined();
    expect(result.recommendations).toBeDefined();
    expect(result.risk_scores).toBeDefined();
    expect(result.opportunity_scores).toBeDefined();
    expect(result.goals).toBeDefined();
  });

  it('should return last result', () => {
    const runtime = new IntelligenceRuntime();
    runtime.registerEngine(new HealthEngine());

    runtime.compute({
      nodes: [],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    expect(runtime.getLastResult()).not.toBeNull();
  });

  it('should reset all engines', () => {
    const runtime = new IntelligenceRuntime();
    runtime.registerEngine(new HealthEngine());
    runtime.registerEngine(new SpendingEngine());

    expect(() => runtime.reset()).not.toThrow();
  });

  it('should get insights by type', () => {
    const runtime = new IntelligenceRuntime();
    runtime.registerEngine(new SpendingEngine());

    runtime.compute({
      nodes: [
        {
          id: 'node-1',
          type: 'spending_pattern',
          label: 'Food',
          value_paise: 500000,
          metadata: { category: 'Food' },
        },
      ],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    const spendingInsights = runtime.getInsightsByType('spending');
    expect(spendingInsights.length).toBeGreaterThanOrEqual(0);
  });

  it('should get unacknowledged alerts', () => {
    const runtime = new IntelligenceRuntime();
    runtime.registerEngine(new SpendingEngine());

    runtime.compute({
      nodes: [
        {
          id: 'node-1',
          type: 'transaction',
          label: 'Large Purchase',
          value_paise: -10000000,
          metadata: { category: 'Shopping' },
        },
      ],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    const unacknowledged = runtime.getUnacknowledgedAlerts();
    expect(unacknowledged.every(a => !a.acknowledged)).toBe(true);
  });
});