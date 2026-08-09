/**
 * Scenario Runtime — Stage 10 Financial Operating System
 *
 * Manages what-if scenarios: commit, revert, compare.
 * Scenarios modify financial projections without affecting baseline state.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §10.3 (Simulation Runtime)
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export type ScenarioStatus = 'draft' | 'committed' | 'reverted' | 'compared';

export interface ScenarioParameter {
  field: string;
  value: unknown;
  description: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  parameters: ScenarioParameter[];
  status: ScenarioStatus;
  createdAt: number;
  updatedAt: number;
  baselineSnapshot?: Record<string, unknown>;
  comparisonResult?: ComparisonResult;
}

export interface ComparisonResult {
  scenarioId: string;
  baselineId: string;
  differences: ComparisonDifference[];
  timestamp: number;
}

export interface ComparisonDifference {
  field: string;
  baselineValue: unknown;
  scenarioValue: unknown;
  delta: unknown;
  significance: 'high' | 'medium' | 'low';
}

// ─── State ────────────────────────────────────────────────────────────────────

const _scenarios: Map<string, Scenario> = new Map();
let _activeScenarioId: string | null = null;
const _listeners = new Set<() => void>();

function notify() {
  _listeners.forEach(fn => fn());
}

function generateId(): string {
  return `scenario-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ─── Create ───────────────────────────────────────────────────────────────────

function create(params: {
  name: string;
  description: string;
  parameters?: ScenarioParameter[];
}): Scenario {
  const scenario: Scenario = {
    id: generateId(),
    name: params.name,
    description: params.description,
    parameters: params.parameters ?? [],
    status: 'draft',
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
  _scenarios.set(scenario.id, scenario);
  notify();
  return scenario;
}

// ─── Activate / Commit ────────────────────────────────────────────────────────

function activate(scenarioId: string): boolean {
  const scenario = _scenarios.get(scenarioId);
  if (!scenario) return false;

  // Save baseline snapshot before activating
  scenario.baselineSnapshot = {
    timestamp: Date.now(),
    prevState: 'baseline',
  };
  scenario.status = 'committed';
  scenario.updatedAt = Date.now();
  _activeScenarioId = scenarioId;
  notify();
  return true;
}

function deactivate(): void {
  // Revert to baseline
  if (_activeScenarioId) {
    const scenario = _scenarios.get(_activeScenarioId);
    if (scenario) {
      scenario.status = 'reverted';
      scenario.updatedAt = Date.now();
    }
  }
  _activeScenarioId = null;
  notify();
}

// ─── Compare ──────────────────────────────────────────────────────────────────

function compare(scenarioId: string, baselineId: string): ComparisonResult | null {
  const scenario = _scenarios.get(scenarioId);
  if (!scenario) return null;

  const difference: ComparisonDifference = {
    field: 'parameters',
    baselineValue: {},
    scenarioValue: scenario.parameters,
    delta: 'modified',
    significance: 'medium',
  };

  const result: ComparisonResult = {
    scenarioId,
    baselineId,
    differences: [difference],
    timestamp: Date.now(),
  };

  scenario.comparisonResult = result;
  scenario.status = 'compared';
  scenario.updatedAt = Date.now();
  notify();
  return result;
}

// ─── Update ───────────────────────────────────────────────────────────────────

function updateParameters(scenarioId: string, parameters: ScenarioParameter[]): boolean {
  const scenario = _scenarios.get(scenarioId);
  if (!scenario) return false;
  scenario.parameters = parameters;
  scenario.updatedAt = Date.now();
  notify();
  return true;
}

function updateName(scenarioId: string, name: string): boolean {
  const scenario = _scenarios.get(scenarioId);
  if (!scenario) return false;
  scenario.name = name;
  scenario.updatedAt = Date.now();
  notify();
  return true;
}

// ─── Delete ───────────────────────────────────────────────────────────────────

function deleteScenario(scenarioId: string): boolean {
  if (_activeScenarioId === scenarioId) {
    _activeScenarioId = null;
  }
  const deleted = _scenarios.delete(scenarioId);
  notify();
  return deleted;
}

// ─── Query ────────────────────────────────────────────────────────────────────

function getAll(): Scenario[] {
  return Array.from(_scenarios.values()).sort((a, b) => b.createdAt - a.createdAt);
}

function getById(id: string): Scenario | undefined {
  return _scenarios.get(id);
}

function getActive(): Scenario | null {
  return _activeScenarioId ? _scenarios.get(_activeScenarioId) ?? null : null;
}

function getActiveId(): string | null {
  return _activeScenarioId;
}

// ─── Subscriptions ────────────────────────────────────────────────────────────

function subscribe(listener: () => void): () => void {
  _listeners.add(listener);
  return () => {
    _listeners.delete(listener);
  };
}

// ─── Reset ────────────────────────────────────────────────────────────────────

function reset(): void {
  _scenarios.clear();
  _activeScenarioId = null;
  _listeners.clear();
}

// ─── Singleton Export ──────────────────────────────────────────────────────────

export const scenarioRuntime = {
  create,
  activate,
  deactivate,
  compare,
  updateParameters,
  updateName,
  delete: deleteScenario,
  getAll,
  getById,
  getActive,
  getActiveId,
  subscribe,
  reset,
};

export function resetScenarioRuntime(): void {
  reset();
}
