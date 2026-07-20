/**
 * Scenario Comparison Tests - Stage 7 Simulation & Forecast Engine
 */

import { describe, it, expect } from 'vitest';
import { ScenarioComparisonEngine } from '../comparison';
import { simulationBuilder } from '../insight-builder';
import type { SimulationResult } from '../types';

describe('ScenarioComparisonEngine', () => {
  const engine = new ScenarioComparisonEngine();

  const createMockResult = (name: string, finalValue: number): SimulationResult => {
    const scenario = simulationBuilder.createScenario(
      `scenario-${name}`,
      name,
      `Test scenario ${name}`,
      10000,
      [
        simulationBuilder.createProjection(`proj-0`, 'cashflow', '2025-01-01', 0, 80, []),
        simulationBuilder.createProjection(`proj-1`, 'cashflow', '2025-02-01', finalValue, 80, []),
      ],
      [],
      simulationBuilder.buildEvidenceChain(
        `Test ${name}`,
        [],
        [],
        [],
        80,
      ),
    );

    return simulationBuilder.createSimulationResult(
      'cashflow',
      scenario,
      [
        simulationBuilder.createProjection(`proj-0`, 'cashflow', '2025-01-01', 0, 80, []),
        simulationBuilder.createProjection(`proj-1`, 'cashflow', '2025-02-01', finalValue, 80, []),
      ],
      [simulationBuilder.createOutput('test', 'Test output', { valuePaise: finalValue })],
      simulationBuilder.buildEvidenceChain(
        `Test ${name}`,
        [],
        [],
        [],
        80,
      ),
      [],
    );
  };

  describe('compare', () => {
    it('should compare two scenarios and find best/worst case', () => {
      const baseline = createMockResult('baseline', 100000);
      const alternative = createMockResult('alternative', 150000);

      const result = engine.compare(baseline, alternative);

      expect(result.name).toBe('Scenario Comparison');
      expect(result.scenarios).toHaveLength(2);
      expect(result.best_case).toBe(alternative.scenario);
      expect(result.worst_case).toBe(baseline.scenario);
    });

    it('should calculate differences between scenarios', () => {
      const baseline = createMockResult('baseline', 100000);
      const alternative = createMockResult('alternative', 150000);

      const result = engine.compare(baseline, alternative);

      expect(result.differences).toHaveLength(2); // final_value + test output
      const finalValueDiff = result.differences.find(d => d.metric === 'final_value');
      expect(finalValueDiff?.difference_paise).toBe(50000);
      expect(finalValueDiff?.percentage_difference).toBe(50);
    });
  });

  describe('compareMultiple', () => {
    it('should compare multiple scenarios', () => {
      const results = [
        createMockResult('low', 50000),
        createMockResult('medium', 100000),
        createMockResult('high', 150000),
      ];

      const result = engine.compareMultiple(results);

      expect(result.scenarios).toHaveLength(3);
      expect(result.best_case?.name).toBe('high');
      expect(result.worst_case?.name).toBe('low');
    });

    it('should handle single scenario', () => {
      const results = [createMockResult('only', 100000)];

      const result = engine.compareMultiple(results);

      expect(result.summary).toBe('Need at least 2 scenarios to compare');
    });
  });

  describe('findBestCase', () => {
    it('should find the scenario with highest final value', () => {
      const results = [
        createMockResult('low', 50000),
        createMockResult('high', 150000),
      ];

      const best = engine.findBestCase(results);

      expect(best?.scenario.name).toBe('high');
    });

    it('should return null for empty results', () => {
      const best = engine.findBestCase([]);
      expect(best).toBeNull();
    });
  });

  describe('findWorstCase', () => {
    it('should find the scenario with lowest final value', () => {
      const results = [
        createMockResult('low', 50000),
        createMockResult('high', 150000),
      ];

      const worst = engine.findWorstCase(results);

      expect(worst?.scenario.name).toBe('low');
    });

    it('should return null for empty results', () => {
      const worst = engine.findWorstCase([]);
      expect(worst).toBeNull();
    });
  });
});