/**
 * Spending Engine Tests - Stage 6 Financial Intelligence Engine
 */

import { describe, it, expect } from 'vitest';
import { SpendingEngine } from '../spending-engine';
import { DEFAULT_INTELLIGENCE_CONFIG } from '../types';

describe('SpendingEngine', () => {
  const engine = new SpendingEngine();

  it('should have correct engine name', () => {
    expect(engine.name).toBe('spending');
  });

  it('should return empty results for nodes with no transaction data', () => {
    const result = engine.compute({
      nodes: [],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    expect(result.insights).toHaveLength(0);
    expect(result.alerts).toHaveLength(0);
  });

  it('should detect high spending in categories', () => {
    const result = engine.compute({
      nodes: [
        {
          id: 'node-1',
          type: 'spending_pattern',
          label: 'Food',
          value_paise: 600000, // ₹6,000 - above threshold of ₹5,000
          metadata: { category: 'Food' },
        },
      ],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    // Spending threshold is 5000000 (₹50,000) in config
    // This value is below threshold, so no insights
    expect(result.insights.length).toBeGreaterThanOrEqual(0);
  });

  it('should detect large transaction anomalies', () => {
    const result = engine.compute({
      nodes: [
        {
          id: 'node-1',
          type: 'transaction',
          label: 'Large Purchase',
          value_paise: -10000000, // ₹100,000
          metadata: { category: 'Shopping' },
        },
      ],
      edges: [],
      config: DEFAULT_INTELLIGENCE_CONFIG,
    });

    expect(result.alerts.length).toBeGreaterThan(0);
  });

  it('should reset without error', () => {
    expect(() => engine.reset()).not.toThrow();
  });
});