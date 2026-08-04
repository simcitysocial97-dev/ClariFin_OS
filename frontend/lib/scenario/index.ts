/**
 * Scenario Runtime — Public API
 *
 * Manages what-if scenarios: commit, revert, compare.
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §10.3
 */

export type {
  Scenario,
  ScenarioStatus,
  ScenarioParameter,
  ComparisonResult,
  ComparisonDifference,
} from './runtime';

export {
  scenarioRuntime,
  resetScenarioRuntime,
} from './runtime';
