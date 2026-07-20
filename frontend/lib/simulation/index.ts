/**
 * Simulation & Forecast Engine - Public API
 *
 * Central export for the Stage 7 Simulation & Forecast Engine.
 * Every workspace can import from here to run deterministic simulations.
 *
 * Architecture: FinancialGraphRuntime → IntelligenceEngine → SimulationRuntime → Engines
 */

// ===== Core Types =====
export type {
  Projection,
  ProjectionType,
  Scenario,
  SimulationInput,
  SimulationOutput,
  SimulationAssumption,
  AssumptionCategory,
  SimulationEvidenceItem,
  SimulationCalculationStep,
  SimulationSourceReference,
  SimulationEvidenceChain,
  SimulationResult,
  SimulationType,
  SimulationContext,
  SimulationConfig,
  SimulationOptions,
  SensitivityResult,
} from './types';

export {
  DEFAULT_SIMULATION_CONFIG,
  SIMULATION_RUNTIME_VERSION,
} from './types';

// ===== Simulation Runtime =====
export {
  SimulationRuntime,
  simulationRuntime,
} from './runtime';

// ===== Simulation Insight Builder =====
export {
  SimulationInsightBuilder,
  simulationBuilder,
} from './insight-builder';

// ===== Scenario Comparison =====
export {
  ScenarioComparisonEngine,
} from './comparison';

export type {
  ComparisonResult,
  ComparisonDifference,
} from './comparison';

// ===== Simulators =====
export { CashflowSimulator } from './simulators/cashflow-simulator';
export { NetWorthSimulator } from './simulators/net-worth-simulator';
export { BudgetSimulator } from './simulators/budget-simulator';
export { LoanSimulator } from './simulators/loan-simulator';
export { InvestmentSimulator } from './simulators/investment-simulator';
export { RetirementSimulator } from './simulators/retirement-simulator';
export { GoalSimulator } from './simulators/goal-simulator';
export { EmergencyFundSimulator } from './simulators/emergency-fund-simulator';