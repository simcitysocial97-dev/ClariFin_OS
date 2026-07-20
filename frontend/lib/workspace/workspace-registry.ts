/**
 * Workspace Registry - Stage 7.5 Runtime Consolidation
 *
 * Canonical registry for all workspace registrations.
 * Extracted from CommandCenterRuntime to become the single source of truth.
 *
 * Architecture: WorkspaceRegistry → CommandCenter → Graph Runtime → Navigation
 */

import type { WorkspaceName } from './workspace-context';

// ===== Workspace Registration =====
export interface WorkspaceRegistration {
  name: WorkspaceName;
  label: string;
  icon?: string;
  deepLink: string;
  viewModelKey: string;
  description?: string;
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
      },
      {
        name: 'transactions',
        label: 'Transactions',
        icon: 'receipt',
        deepLink: '/transactions',
        viewModelKey: 'transactions',
        description: 'Transaction history and categorization',
      },
      {
        name: 'accounts',
        label: 'Accounts',
        icon: 'wallet',
        deepLink: '/accounts',
        viewModelKey: 'accounts',
        description: 'Bank accounts and balances',
      },
      {
        name: 'cards',
        label: 'Cards',
        icon: 'credit-card',
        deepLink: '/cards',
        viewModelKey: 'cards',
        description: 'Credit cards and statements',
      },
      {
        name: 'loans',
        label: 'Loans',
        icon: 'landmark',
        deepLink: '/loans',
        viewModelKey: 'loans',
        description: 'Loan management and amortization',
      },
      {
        name: 'investments',
        label: 'Investments',
        icon: 'trending-up',
        deepLink: '/investments',
        viewModelKey: 'investments',
        description: 'Investment portfolio and holdings',
      },
      {
        name: 'net-worth',
        label: 'Net Worth',
        icon: 'scale',
        deepLink: '/net-worth',
        viewModelKey: 'netWorth',
        description: 'Net worth tracking and analysis',
      },
      {
        name: 'cashflow',
        label: 'Cashflow',
        icon: 'arrow-left-right',
        deepLink: '/cashflow',
        viewModelKey: 'cashflow',
        description: 'Cashflow analysis and trends',
      },
      {
        name: 'behaviour',
        label: 'Behaviour',
        icon: 'brain',
        deepLink: '/behaviour',
        viewModelKey: 'behaviour',
        description: 'Financial behavior analysis',
      },
      {
        name: 'forecast',
        label: 'Forecast',
        icon: 'crystal-ball',
        deepLink: '/forecast',
        viewModelKey: 'forecast',
        description: 'Financial projections and scenarios',
      },
      {
        name: 'reconciliation',
        label: 'Reconciliation',
        icon: 'check-square',
        deepLink: '/reconciliation',
        viewModelKey: 'reconciliation',
        description: 'Statement reconciliation',
      },
      {
        name: 'settings',
        label: 'Settings',
        icon: 'settings',
        deepLink: '/settings',
        viewModelKey: 'settings',
        description: 'Application settings',
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