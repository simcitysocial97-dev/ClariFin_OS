/**
 * Workspace Registry - Stage 8B Workspace Integration & Surface Migration
 *
 * Canonical registry for all workspace registrations.
 * Extended with surface metadata and runtime integration.
 *
 * Architecture: WorkspaceRegistry → CommandCenter → Graph Runtime → Navigation
 */

import type { WorkspaceName } from './workspace-context';

// ===== Surface Types =====
export type SurfaceType =
  | 'GRAPH'
  | 'TABLE'
  | 'TIMELINE'
  | 'SANKEY'
  | 'MATRIX'
  | 'SIMULATION'
  | 'CONFIGURATION';

// ===== Workspace Registration =====
export interface WorkspaceRegistration {
  name: WorkspaceName;
  label: string;
  icon?: string;
  deepLink: string;
  viewModelKey: string;
  description?: string;

  // Surface metadata
  defaultSurface: SurfaceType;
  graphAdapter?: string;

  // Runtime integration
  supportedCommands: string[];
  supportedFilters: string[];
  supportedSelections: string[];
  inspectorSections: string[];

  // Keyboard shortcuts
  keyboardShortcuts: Record<string, string>;
}

// ===== Workspace Registry =====
/**
 * Singleton registry for all workspace registrations.
 * This is the canonical registry - all other systems use this.
 */
export class WorkspaceRegistry {
  private static instance: WorkspaceRegistry;
  private workspaces: Map<WorkspaceName, WorkspaceRegistration> = new Map();

  private constructor() {
    // Private constructor for singleton pattern
    this.registerDefaultWorkspaces();
  }

  /**
   * Get the singleton instance
   */
  static getInstance(): WorkspaceRegistry {
    if (!WorkspaceRegistry.instance) {
      WorkspaceRegistry.instance = new WorkspaceRegistry();
    }
    return WorkspaceRegistry.instance;
  }

  /**
   * Reset the singleton instance (useful for testing)
   */
  static resetInstance(): void {
    WorkspaceRegistry.instance = new WorkspaceRegistry();
  }

  /**
   * Register a workspace
   */
  register(registration: WorkspaceRegistration): void {
    this.workspaces.set(registration.name, registration);
  }

  /**
   * Unregister a workspace by name
   */
  unregister(name: WorkspaceName): boolean {
    return this.workspaces.delete(name);
  }

  /**
   * Get a workspace registration by name
   */
  get(name: WorkspaceName): WorkspaceRegistration | undefined {
    return this.workspaces.get(name);
  }

  /**
   * Check if a workspace is registered
   */
  has(name: WorkspaceName): boolean {
    return this.workspaces.has(name);
  }

  /**
   * Get all registered workspaces
   */
  getAll(): WorkspaceRegistration[] {
    return Array.from(this.workspaces.values());
  }

  /**
   * Get all workspace names
   */
  getNames(): WorkspaceName[] {
    return Array.from(this.workspaces.keys());
  }

  /**
   * Get the count of registered workspaces
   */
  get count(): number {
    return this.workspaces.size;
  }

  /**
   * Register all default workspaces
   */
  private registerDefaultWorkspaces(): void {
    const defaultWorkspaces: WorkspaceRegistration[] = [
      {
        name: 'dashboard',
        label: 'Dashboard',
        icon: 'layout-dashboard',
        deepLink: '/dashboard',
        viewModelKey: 'dashboard',
        description: 'Financial overview and insights',
        defaultSurface: 'GRAPH',
        graphAdapter: 'dashboard',
        supportedCommands: ['refresh', 'export', 'search'],
        supportedFilters: ['date', 'search'],
        supportedSelections: [],
        inspectorSections: ['context', 'insights'],
        keyboardShortcuts: {
          'r': 'refresh',
          'e': 'export',
        },
      },
      {
        name: 'transactions',
        label: 'Transactions',
        icon: 'receipt',
        deepLink: '/transactions',
        viewModelKey: 'transactions',
        description: 'Transaction history and categorization',
        defaultSurface: 'TABLE',
        graphAdapter: 'transactions',
        supportedCommands: ['search', 'filter', 'group', 'sort', 'export', 'refresh', 'select-all', 'delete'],
        supportedFilters: ['date', 'category', 'merchant', 'amount', 'status', 'search'],
        supportedSelections: ['transaction'],
        inspectorSections: ['context', 'evidence', 'related', 'actions'],
        keyboardShortcuts: {
          'f': 'search',
          'F': 'filter',
          'g': 'group',
          's': 'sort',
          'r': 'refresh',
          'a': 'select-all',
          'Delete': 'delete',
          'Escape': 'close-evidence',
        },
      },
      {
        name: 'accounts',
        label: 'Accounts',
        icon: 'wallet',
        deepLink: '/accounts',
        viewModelKey: 'accounts',
        description: 'Bank accounts and balances',
        defaultSurface: 'TABLE',
        graphAdapter: 'accounts',
        supportedCommands: ['add', 'edit', 'delete', 'refresh'],
        supportedFilters: ['search'],
        supportedSelections: ['account'],
        inspectorSections: ['context', 'related'],
        keyboardShortcuts: {
          'a': 'add',
          'r': 'refresh',
        },
      },
      {
        name: 'cards',
        label: 'Cards',
        icon: 'credit-card',
        deepLink: '/cards',
        viewModelKey: 'cards',
        description: 'Credit cards and statements',
        defaultSurface: 'TABLE',
        graphAdapter: 'cards',
        supportedCommands: ['add', 'validate', 'refresh'],
        supportedFilters: ['search'],
        supportedSelections: ['card'],
        inspectorSections: ['context', 'evidence'],
        keyboardShortcuts: {
          'a': 'add',
          'r': 'refresh',
        },
      },
      {
        name: 'loans',
        label: 'Loans',
        icon: 'landmark',
        deepLink: '/loans',
        viewModelKey: 'loans',
        description: 'Loan management and amortization',
        defaultSurface: 'TABLE',
        graphAdapter: 'loans',
        supportedCommands: ['add', 'edit', 'delete', 'schedule', 'simulate', 'refresh'],
        supportedFilters: ['search'],
        supportedSelections: ['loan'],
        inspectorSections: ['context', 'amortization', 'simulation'],
        keyboardShortcuts: {
          'a': 'add',
          'r': 'refresh',
        },
      },
      {
        name: 'investments',
        label: 'Investments',
        icon: 'trending-up',
        deepLink: '/investments',
        viewModelKey: 'investments',
        description: 'Investment portfolio and holdings',
        defaultSurface: 'TABLE',
        graphAdapter: 'investments',
        supportedCommands: ['add', 'edit', 'delete', 'refresh'],
        supportedFilters: ['search'],
        supportedSelections: ['investment'],
        inspectorSections: ['context', 'allocation', 'related'],
        keyboardShortcuts: {
          'a': 'add',
          'r': 'refresh',
        },
      },
      {
        name: 'net-worth',
        label: 'Net Worth',
        icon: 'scale',
        deepLink: '/net-worth',
        viewModelKey: 'netWorth',
        description: 'Net worth tracking and analysis',
        defaultSurface: 'GRAPH',
        graphAdapter: 'netWorth',
        supportedCommands: ['date-range', 'period', 'export', 'refresh'],
        supportedFilters: ['date', 'account-type', 'period'],
        supportedSelections: ['account', 'investment'],
        inspectorSections: ['context', 'composition', 'trend', 'related'],
        keyboardShortcuts: {
          'd': 'date-range',
          'p': 'period',
          'r': 'refresh',
        },
      },
      {
        name: 'cashflow',
        label: 'Cashflow',
        icon: 'arrow-left-right',
        deepLink: '/cashflow',
        viewModelKey: 'cashflow',
        description: 'Cashflow analysis and trends',
        defaultSurface: 'SANKEY',
        graphAdapter: 'cashflow',
        supportedCommands: ['refresh', 'export', 'evidence'],
        supportedFilters: ['date', 'period'],
        supportedSelections: ['transaction'],
        inspectorSections: ['context', 'evidence', 'insights'],
        keyboardShortcuts: {
          'r': 'refresh',
          'e': 'evidence',
        },
      },
      {
        name: 'behaviour',
        label: 'Behaviour',
        icon: 'brain',
        deepLink: '/behaviour',
        viewModelKey: 'behaviour',
        description: 'Financial behavior analysis',
        defaultSurface: 'TIMELINE',
        graphAdapter: 'behaviour',
        supportedCommands: ['period', 'refresh', 'evidence'],
        supportedFilters: ['period'],
        supportedSelections: ['pattern'],
        inspectorSections: ['context', 'evidence', 'insights', 'patterns'],
        keyboardShortcuts: {
          'p': 'period',
          'r': 'refresh',
          'e': 'evidence',
        },
      },
      {
        name: 'forecast',
        label: 'Forecast',
        icon: 'crystal-ball',
        deepLink: '/forecast',
        viewModelKey: 'forecast',
        description: 'Financial projections and scenarios',
        defaultSurface: 'SIMULATION',
        graphAdapter: 'forecast',
        supportedCommands: ['horizon', 'scenarios', 'refresh', 'simulate'],
        supportedFilters: ['horizon', 'scenarios'],
        supportedSelections: ['projection'],
        inspectorSections: ['context', 'projections', 'scenarios', 'insights'],
        keyboardShortcuts: {
          'h': 'horizon',
          's': 'scenarios',
          'r': 'refresh',
        },
      },
      {
        name: 'reconciliation',
        label: 'Reconciliation',
        icon: 'check-square',
        deepLink: '/reconciliation',
        viewModelKey: 'reconciliation',
        description: 'Statement reconciliation',
        defaultSurface: 'TABLE',
        graphAdapter: 'reconciliation',
        supportedCommands: ['refresh', 'match', 'skip'],
        supportedFilters: ['search', 'status'],
        supportedSelections: ['reconciliation'],
        inspectorSections: ['context', 'evidence', 'actions'],
        keyboardShortcuts: {
          'r': 'refresh',
          'm': 'match',
          's': 'skip',
        },
      },
      {
        name: 'settings',
        label: 'Settings',
        icon: 'settings',
        deepLink: '/settings',
        viewModelKey: 'settings',
        description: 'Application settings',
        defaultSurface: 'CONFIGURATION',
        graphAdapter: undefined,
        supportedCommands: ['export', 'import', 'clear'],
        supportedFilters: [],
        supportedSelections: [],
        inspectorSections: ['context'],
        keyboardShortcuts: {
          'e': 'export',
          'i': 'import',
        },
      },
    ];

    for (const workspace of defaultWorkspaces) {
      this.workspaces.set(workspace.name, workspace);
    }
  }

  /**
   * Clear all workspaces
   */
  clear(): void {
    this.workspaces.clear();
  }
}

// ===== Convenience Export =====
export const workspaceRegistry = WorkspaceRegistry.getInstance();