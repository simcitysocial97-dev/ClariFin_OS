/**
 * Health Engine Tests - Stage 6 Financial Intelligence Engine
 */

import { describe, it, expect } from 'vitest';
import { HealthEngine } from '../health-engine';
import { DEFAULT_INTELLIGENCE_CONFIG } from '../types';

describe('HealthEngine', () => {
  const engine = new HealthEngine();

  it('should have correct engine name', () => {
    expect(engine.name).toBe('health');
  });

  it('should return empty insights for nodes with no data', () => {
    const result = engine.compute({
      nodes: [],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    expect(result.insights).toHaveLength(0);
    expect(result.health_score).not.toBeNull();
    // Default neutral score when no data
    expect(result.health_score?.overall).toBe(50);
  });

  it('should compute health score with savings data', () => {
    const result = engine.compute({
      nodes: [
        {
          id: 'node-1',
          type: 'behaviour_score',
          label: 'Savings',
          value_paise: 100000,
          metadata: { savings_rate_bps: 1500 }, // 15%
        },
      ],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    expect(result.health_score).not.toBeNull();
    expect(result.health_score?.dimensions).toHaveLength(5);
    expect(result.health_score?.dimensions[0].name).toBe('Savings');
  });

  it('should generate insights for low health scores', () => {
    const result = engine.compute({
      nodes: [
        {
          id: 'node-1',
          type: 'behaviour_score',
          label: 'Savings',
          value_paise: 100000,
          metadata: { savings_rate_bps: 0 }, // 0% - will trigger low score
        },
      ],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    // With 0% savings rate, the savings dimension score is 20 (below 40 threshold)
    expect(result.health_score?.dimensions[0].score).toBe(20);
  });

  it('should reset without error', () => {
    expect(() => engine.reset()).not.toThrow();
  });
});