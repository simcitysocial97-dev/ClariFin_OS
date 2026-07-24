/**
 * Simulation Runtime - Stage 7 Simulation & Forecast Engine
 *
 * Main runtime that orchestrates all simulation engines.
 * Consumes the Financial Graph Runtime and produces deterministic
 * financial projections.
 *
 * Architecture: FinancialGraphRuntime → SimulationRuntime → Engines → Command Center
 *
 * Every projection includes: assumptions, inputs, outputs, evidence, confidence, related graph nodes.
 */

import type {
  SimulationConfig,
  SimulationContext,
  SimulationResult,
  SimulationEngine,
  SimulationType,
  SimulationOptions,
} from './types';
import { DEFAULT_SIMULATION_CONFIG, SIMULATION_RUNTIME_VERSION } from './types';

// ===== Simulation Runtime =====
/**
 * Main runtime for the Simulation & Forecast Engine.
 * Orchestrates all simulation engines and produces deterministic results.
 */
export class SimulationRuntime {
  private config: SimulationConfig;
  private engines: Map<SimulationType, SimulationEngine> = new Map();
  private lastResults: Map<SimulationType, SimulationResult> = new Map();

  constructor(config: Partial<SimulationConfig> = {}) {
    this.config = { ...DEFAULT_SIMULATION_CONFIG, ...config };
  }

  // ===== Engine Registration =====
  /**
   * Register a simulation engine.
   */
  registerEngine(engine: SimulationEngine): void {
    this.engines.set(engine.name, engine);
  }

  /**
   * Unregister a simulation engine.
   */
  unregisterEngine(name: SimulationType): void {
    this.engines.delete(name);
  }

  /**
   * Get a registered engine.
   */
  getEngine(name: SimulationType): SimulationEngine | undefined {
    return this.engines.get(name);
  }

  /**
   * Get all registered engines.
   */
  getEngines(): SimulationEngine[] {
    return Array.from(this.engines.values());
  }

  /**
   * Get enabled engine names.
   */
  getEnabledEngines(): SimulationType[] {
    return this.config.enabled_simulations.filter(name => this.engines.has(name));
  }

  // ===== Configuration =====
  /**
   * Update configuration.
   */
  updateConfig(config: Partial<SimulationConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current configuration.
   */
  getConfig(): SimulationConfig {
    return { ...this.config };
  }

  // ===== Simulation Computation =====
  /**
   * Compute simulations from graph data.
   *
   * Runs all enabled engines and returns results.
   * Every result is deterministic and reproducible.
   */
  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult[] {
    const results: SimulationResult[] = [];
    const enabledEngines = this.getEnabledEngines();

    for (const engineName of enabledEngines) {
      const engine = this.engines.get(engineName);
      if (!engine) continue;

      const result = engine.compute(context, options);
      this.lastResults.set(engineName, result);
      results.push(result);
    }

    return results;
  }

  /**
   * Get the last computed result for a specific engine.
   */
  getLastResult(name: SimulationType): SimulationResult | undefined {
    return this.lastResults.get(name);
  }

  /**
   * Get all last computed results.
   */
  getAllLastResults(): SimulationResult[] {
    return Array.from(this.lastResults.values());
  }

  // ===== Query Methods =====
  /**
   * Get all projections from a specific simulation.
   */
  getProjections(name: SimulationType): SimulationResult['timeline'] {
    const result = this.lastResults.get(name);
    return result?.timeline ?? [];
  }

  /**
   * Get all scenarios from a specific simulation.
   */
  getScenarios(name: SimulationType): SimulationResult['scenario'][] {
    const result = this.lastResults.get(name);
    return result?.scenario ? [result.scenario] : [];
  }

  // ===== Reset =====
  /**
   * Reset all engines.
   */
  reset(): void {
    for (const engine of this.engines.values()) {
      engine.reset();
    }
    this.lastResults.clear();
  }

  /**
   * Reset a specific engine.
   */
  resetEngine(name: SimulationType): void {
    const engine = this.engines.get(name);
    if (engine) {
      engine.reset();
      this.lastResults.delete(name);
    }
  }

  // ===== Version =====
  /**
   * Get runtime version.
   */
  getVersion(): string {
    return SIMULATION_RUNTIME_VERSION;
  }
}

/** Convenience export */
export const simulationRuntime = new SimulationRuntime();