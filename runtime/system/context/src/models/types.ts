export type ContextType =
  | 'Dashboard'
  | 'Account'
  | 'Transaction'
  | 'Loan'
  | 'Investment'
  | 'Goal'
  | 'Budget'
  | 'CashFlow'
  | 'NetWorth'
  | 'Forecast'
  | 'Investigation'
  | 'Comparison'
  | 'Simulation'
  | 'Search'
  | 'Command'
  | 'Workspace'
  | string;


export interface Context {
  id: string;
  name: string;
  type: ContextType;
  createdTime: string; // ISO 8601
  updatedTime: string; // ISO 8601
  owner: string;
  workspace: string;
  currentTimeScope: {
    start: string; // ISO 8601
    end: string;   // ISO 8601
  };
  selectedFinancialObjects: Array<{
    id: string;
    type: string;
  }>;
  focusedObject?: {
    id: string;
    type: string;
  };
  activeInvestigation?: string;
  appliedFilters: Array<{
    id: string;
    type: string;
    value: unknown;
  }>;
  navigationState: {
    path: string;
    params: Record<string, unknown>;
  };
  comparisonState?: {
    comparedContexts: string[];
    comparisonType: string;
  };
  pinnedObjects: Array<{
    id: string;
    type: string;
  }>;
  temporaryObjects: Array<{
    id: string;
    type: string;
    expiresAt: string; // ISO 8601
  }>;
  historyStack: string[];
  metadata: Record<string, unknown>;
  evidenceReferences: string[];
  explainabilityReferences: string[];
}


export interface ContextSnapshot {
  id: string;
  contextId: string;
  timestamp: string; // ISO 8601
  state: Context;
}


export interface ContextEvent {
  id: string;
  contextId: string;
  type: string;
  timestamp: string; // ISO 8601
  metadata: Record<string, unknown>;
  previousState?: Context;
  newState?: Context;
}


export interface Workspace {
  id: string;
  name: string;
  activeContexts: string[];
  inactiveContexts: string[];
  history: string[];
  preferences: Record<string, unknown>;
}