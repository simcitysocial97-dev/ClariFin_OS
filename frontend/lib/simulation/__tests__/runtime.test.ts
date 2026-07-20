/**
 * Simulation Runtime Tests - Stage 7 Simulation & Forecast Engine
 */

import { describe, it, expect } from 'vitest';
import { SimulationRuntime } from '../runtime';
import { CashflowSimulator } from '../simulators/cashflow-simulator';
import { NetWorthSimulator } from '../simulators/net-worth-simulator';
import { DEFAULT_SIMULATION_CONFIG } from '../types';

describe('SimulationRuntime', () => {
  const runtime = new SimulationRuntime();

  it('should have correct version', () => {
    expect(runtime.getVersion()).toBe('1.0.0');
  });

  it('should register and retrieve engines', () => {
    const engine = new CashflowSimulator();
    runtime.registerEngine(engine);
    expect(runtime.getEngine('cashflow')).toBe(engine);
    runtime.unregisterEngine('cashflow');
    expect(runtime.getEngine('cashflow')).toBeUndefined();
  });

  it('should return enabled engines', () => {
    const engine = new CashflowSimulator();
    runtime.registerEngine(engine);
    const enabled = runtime.getEnabledEngines();
    expect(enabled).toContain('cashflow');
    runtime.unregisterEngine('cashflow');
  });

  it('should update configuration', () => {
    const newConfig = { horizon_months: 24 };
    runtime.updateConfig(newConfig);
    const config = runtime.getConfig();
    expect(config.horizon_months).toBe(24);
    runtime.updateConfig(DEFAULT_SIMULATION_CONFIG);
  });

  it('should compute simulations with no nodes', () => {
    const engine = new CashflowSimulator();
    runtime.registerEngine(engine);

    const result = runtime.compute({
      nodes: [],
      edges: [],
      config: DEFAULT_SIMULATION_CONFIG,
    });

    expect(result).toHaveLength(1);
    expect(result[0].type).toBe('cashflow');
    expect(result[0].timeline).toHaveLength(12); // Default horizon
    runtime.unregisterEngine('cashflow');
  });

  it('should compute simulations with transaction data', () => {
    const engine = new CashflowSimulator();
    runtime.registerEngine(engine);

    const result = runtime.compute({
      nodes: [
        {
          id: 'tx-1',
          type: 'transaction',
          label: 'Salary',
          value_paise: 500000, // ₹5000
          date: '2025-01-01',
          metadata: {},
        },
        {
          id: 'tx-2',
          type: 'transaction',
          label: 'Rent',
          value_paise: -200000, // -₹2000
          date: '2025-01-01',
          metadata: {},
        },
      ],
      edges: [],
      config: DEFAULT_SIMULATION_CONFIG,
    });

    expect(result).toHaveLength(1);
    expect(result[0].outputs).toHaveLength(3);
    runtime.unregisterEngine('cashflow');
  });

  it('should reset engines', () => {
    const engine = new CashflowSimulator();
    runtime.registerEngine(engine);
    runtime.reset();
    expect(runtime.getAllLastResults()).toHaveLength(0);
  });
});

describe('NetWorthSimulator', () => {
  const engine = new NetWorthSimulator();

  it('should have correct engine name', () => {
    expect(engine.name).toBe('net_worth');
  });

  it('should compute net worth projection', () => {
    const result = engine.compute({
      nodes: [
        {
          id: 'acc-1',
          type: 'account',
          label: 'Savings',
          value_paise: 1000000, // ₹10000
          date: '2025-01-01',
          metadata: {},
        },
      ],
      edges: [],
      config: DEFAULT_SIMULATION_CONFIG,
    });

    expect(result.type).toBe('net_worth');
    expect(result.timeline).toHaveLength(13); // 0 to 12 months
    expect(result.outputs).toHaveLength(3);
  });

  it('should reset without error', () => {
    expect(() => engine.reset()).not.toThrow();
  });
});