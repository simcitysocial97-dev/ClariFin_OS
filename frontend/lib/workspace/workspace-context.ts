/**
 * Workspace Context - Stage 7.5 Runtime Consolidation
 *
 * Single global workspace state.
 * Owns only global UI/runtime state, not workspace-specific data.
 *
 * Architecture: WorkspaceContext → All Workspaces
 */

import { useState, useCallback, createContext, useContext } from 'react';
import type { GraphSelection } from '../graph';

// ===== Workspace Types =====
export type WorkspaceName =
  | 'dashboard'
  | 'transactions'
  | 'accounts'
  | 'cards'
  | 'loans'
  | 'investments'
  | 'net-worth'
  | 'cashflow'
  | 'behaviour'
  | 'forecast'
  | 'reconciliation'
  | 'settings';

// ===== Workspace State =====
export interface WorkspaceState {
  // Current workspace
  currentWorkspace: WorkspaceName;

  // Active entity (selected item in any workspace)
  activeEntity: {
    workspace: WorkspaceName;
    entityId: string | null;
  } | null;

  // Global date range (shared across workspaces)
  globalDateRange: {
    from: string | null;
    to: string | null;
  };

  // Selected items (cross-workspace selection)
  selectedAccount: string | null;
  selectedTransaction: string | null;
  selectedLoan: string | null;
  selectedCard: string | null;
  selectedInvestment: string | null;

  // Graph selection state
  graphSelection: GraphSelection | null;

  // Timeline position
  timelinePosition: {
    date: string | null;
    workspace: WorkspaceName | null;
  };

  // Layout state
  layout: {
    sidebarCollapsed: boolean;
    commandPaletteOpen: boolean;
  };
}

// ===== Workspace Context =====
export interface WorkspaceContextValue {
  state: WorkspaceState;
  actions: {
    // Workspace navigation
    navigateToWorkspace: (workspace: WorkspaceName) => void;

    // Entity selection
    setActiveEntity: (workspace: WorkspaceName, entityId: string | null) => void;

    // Date range
    setGlobalDateRange: (from: string | null, to: string | null) => void;

    // Selection
    selectAccount: (accountId: string | null) => void;
    selectTransaction: (transactionId: string | null) => void;
    selectLoan: (loanId: string | null) => void;
    selectCard: (cardId: string | null) => void;
    selectInvestment: (investmentId: string | null) => void;
    setGraphSelection: (selection: GraphSelection | null) => void;

    // Timeline
    setTimelinePosition: (date: string | null, workspace: WorkspaceName | null) => void;

    // Layout
    toggleSidebar: () => void;
    setSidebarCollapsed: (collapsed: boolean) => void;
    toggleCommandPalette: () => void;
    setCommandPaletteOpen: (open: boolean) => void;

    // Reset
    reset: () => void;
  };
}

// ===== Default State =====
const defaultState: WorkspaceState = {
  currentWorkspace: 'dashboard',
  activeEntity: null,
  globalDateRange: { from: null, to: null },
  selectedAccount: null,
  selectedTransaction: null,
  selectedLoan: null,
  selectedCard: null,
  selectedInvestment: null,
  graphSelection: null,
  timelinePosition: { date: null, workspace: null },
  layout: {
    sidebarCollapsed: false,
    commandPaletteOpen: false,
  },
};

// ===== Workspace Context Hook =====
export function useWorkspaceContext(): WorkspaceContextValue {
  const [state, setState] = useState<WorkspaceState>(() => {
    // Load from localStorage if available
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('workspace-context');
        if (stored) {
          return JSON.parse(stored);
        }
      } catch {
        // Ignore parse errors
      }
    }
    return defaultState;
  });

  // Save to localStorage on change
  const saveState = useCallback((newState: WorkspaceState) => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('workspace-context', JSON.stringify(newState));
      } catch {
        // Ignore storage errors
      }
    }
  }, []);

  // Workspace navigation
  const navigateToWorkspace = useCallback((workspace: WorkspaceName) => {
    setState(prev => {
      const newState = { ...prev, currentWorkspace: workspace };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  // Entity selection
  const setActiveEntity = useCallback((workspace: WorkspaceName, entityId: string | null) => {
    setState(prev => {
      const newState = {
        ...prev,
        activeEntity: entityId ? { workspace, entityId } : null,
      };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  // Date range
  const setGlobalDateRange = useCallback((from: string | null, to: string | null) => {
    setState(prev => {
      const newState = {
        ...prev,
        globalDateRange: { from, to },
      };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  // Selection
  const selectAccount = useCallback((accountId: string | null) => {
    setState(prev => {
      const newState = { ...prev, selectedAccount: accountId };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const selectTransaction = useCallback((transactionId: string | null) => {
    setState(prev => {
      const newState = { ...prev, selectedTransaction: transactionId };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const selectLoan = useCallback((loanId: string | null) => {
    setState(prev => {
      const newState = { ...prev, selectedLoan: loanId };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const selectCard = useCallback((cardId: string | null) => {
    setState(prev => {
      const newState = { ...prev, selectedCard: cardId };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const selectInvestment = useCallback((investmentId: string | null) => {
    setState(prev => {
      const newState = { ...prev, selectedInvestment: investmentId };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const setGraphSelection = useCallback((selection: GraphSelection | null) => {
    setState(prev => {
      const newState = { ...prev, graphSelection: selection };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  // Timeline
  const setTimelinePosition = useCallback((date: string | null, workspace: WorkspaceName | null) => {
    setState(prev => {
      const newState = {
        ...prev,
        timelinePosition: { date, workspace },
      };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  // Layout
  const toggleSidebar = useCallback(() => {
    setState(prev => {
      const newState = {
        ...prev,
        layout: { ...prev.layout, sidebarCollapsed: !prev.layout.sidebarCollapsed },
      };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const setSidebarCollapsed = useCallback((collapsed: boolean) => {
    setState(prev => {
      const newState = {
        ...prev,
        layout: { ...prev.layout, sidebarCollapsed: collapsed },
      };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const toggleCommandPalette = useCallback(() => {
    setState(prev => {
      const newState = {
        ...prev,
        layout: { ...prev.layout, commandPaletteOpen: !prev.layout.commandPaletteOpen },
      };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  const setCommandPaletteOpen = useCallback((open: boolean) => {
    setState(prev => {
      const newState = {
        ...prev,
        layout: { ...prev.layout, commandPaletteOpen: open },
      };
      saveState(newState);
      return newState;
    });
  }, [saveState]);

  // Reset
  const reset = useCallback(() => {
    setState(defaultState);
    saveState(defaultState);
  }, [saveState]);

  return {
    state,
    actions: {
      navigateToWorkspace,
      setActiveEntity,
      setGlobalDateRange,
      selectAccount,
      selectTransaction,
      selectLoan,
      selectCard,
      selectInvestment,
      setGraphSelection,
      setTimelinePosition,
      toggleSidebar,
      setSidebarCollapsed,
      toggleCommandPalette,
      setCommandPaletteOpen,
      reset,
    },
  };
}

// ===== React Context Export =====
export const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function useWorkspace(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within WorkspaceContext.Provider');
  }
  return context;
}