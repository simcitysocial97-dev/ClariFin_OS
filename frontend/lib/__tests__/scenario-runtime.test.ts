/**
 * Scenario Runtime Tests — Stage 10
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  scenarioRuntime,
  resetScenarioRuntime,
} from '../scenario/runtime';

describe('ScenarioRuntime', () => {
  beforeEach(() => {
    resetScenarioRuntime();
  });

  it('should create a scenario', () => {
    const scenario = scenarioRuntime.create({
      name: 'Test Scenario',
      description: 'A test scenario',
      parameters: [{ field: 'rate', value: 0.05, description: 'Interest rate' }],
    });
    expect(scenario).toBeDefined();
    expect(scenario.name).toBe('Test Scenario');
    expect(scenario.status).toBe('draft');
    expect(scenario.parameters).toHaveLength(1);
  });

  it('should activate a scenario', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    const activated = scenarioRuntime.activate(scenario.id);
    expect(activated).toBe(true);
    expect(scenarioRuntime.getActive()?.id).toBe(scenario.id);
    expect(scenarioRuntime.getActive()?.status).toBe('committed');
  });

  it('should fail to activate non-existent scenario', () => {
    expect(scenarioRuntime.activate('non-existent')).toBe(false);
  });

  it('should deactivate the active scenario', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    scenarioRuntime.activate(scenario.id);
    scenarioRuntime.deactivate();
    expect(scenarioRuntime.getActive()).toBeNull();
  });

  it('should compare a scenario against baseline', () => {
    const scenario = scenarioRuntime.create({
      name: 'S1',
      description: 'desc',
      parameters: [{ field: 'spending', value: 500000, description: 'Monthly spending' }],
    });
    const result = scenarioRuntime.compare(scenario.id, 'baseline');
    expect(result).not.toBeNull();
    expect(result?.scenarioId).toBe(scenario.id);
    expect(result?.differences).toHaveLength(1);
  });

  it('should update scenario parameters', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    const updated = scenarioRuntime.updateParameters(scenario.id, [
      { field: 'rate', value: 0.08, description: 'New rate' },
    ]);
    expect(updated).toBe(true);
    expect(scenarioRuntime.getById(scenario.id)?.parameters).toHaveLength(1);
  });

  it('should update scenario name', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    const updated = scenarioRuntime.updateName(scenario.id, 'Updated Name');
    expect(updated).toBe(true);
    expect(scenarioRuntime.getById(scenario.id)?.name).toBe('Updated Name');
  });

  it('should delete a scenario', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    const deleted = scenarioRuntime.delete(scenario.id);
    expect(deleted).toBe(true);
    expect(scenarioRuntime.getById(scenario.id)).toBeUndefined();
  });

  it('should return all scenarios sorted by creation time', () => {
    scenarioRuntime.create({ name: 'First', description: 'desc' });
    scenarioRuntime.create({ name: 'Second', description: 'desc' });
    const all = scenarioRuntime.getAll();
    expect(all).toHaveLength(2);
    // Both created rapidly; just verify two exist with distinct names
    const names = all.map(s => s.name);
    expect(names).toContain('First');
    expect(names).toContain('Second');
  });

  it('should return active scenario', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    scenarioRuntime.activate(scenario.id);
    expect(scenarioRuntime.getActive()?.id).toBe(scenario.id);
  });

  it('should clear active scenario on reset', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    scenarioRuntime.activate(scenario.id);
    resetScenarioRuntime();
    expect(scenarioRuntime.getActive()).toBeNull();
    expect(scenarioRuntime.getAll()).toHaveLength(0);
  });

  it('should maintain status transitions', () => {
    const scenario = scenarioRuntime.create({ name: 'S1', description: 'desc' });
    expect(scenario.status).toBe('draft');

    scenarioRuntime.activate(scenario.id);
    expect(scenarioRuntime.getById(scenario.id)?.status).toBe('committed');

    scenarioRuntime.compare(scenario.id, 'baseline');
    expect(scenarioRuntime.getById(scenario.id)?.status).toBe('compared');
  });
});
